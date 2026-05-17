## 1. 요청 요약

KIS 모의투자 **주문 흐름 연결 준비**: `Strategy → RiskEngine → OMS → BrokerAdapter → KisBroker` 경로의 KIS 주문 메서드들에 **pre-flight 안전 가드 + 내부 도메인 변환 모델 + kill switch**를 추가한다. 실제 KIS HTTP 호출/실주문은 본 작업에서 만들지 않는다(공식 문서 미확인).

### 핵심 절대 조건 (요청 + mvp-005/006-1/007 안전 불변식)

- live trading 6단 차단 그대로 + 본 작업에서 KIS 주문 pre-flight 7단째 추가.
- `OrderType.MARKET` 부재 유지. 시장가 주문은 RiskEngine + PaperBroker + KIS pre-flight 3중 가드.
- 모든 주문 `Strategy → RiskEngine → OMS → BrokerAdapter`. KIS 주문 메서드 자체도 외부에서 직접 호출되지 않도록 OMS만 진입점.
- KIS endpoint URL / TR ID / payload 코드 하드코딩 금지. 공식 문서 확인 전에는 실주문 전송 코드 일체 미작성.
- 모든 KIS 주문 메서드(`place_order`/`cancel_order`/`replace_order`/`get_open_orders`/`get_fills`/`get_order_status`)는 pre-flight 통과 시에도 최종적으로 `NotImplementedError` 또는 `KisOrderRejectedError`로 fail-closed.
- 에러 메시지에 raw key/secret/account 미노출(masked만).
- `Settings` 비밀 필드 `repr=False` + `KisBroker`/sub-client `__repr__` 마스킹 유지.
- `/paper/status`나 어떤 응답에서도 credentials 노출 금지.
- `git commit`/`push`/`merge`/`deploy` 자동화 금지. `.env` Git 추가 금지.
- `pip install` 실행 금지(이미 `.venv`에 의존성 설치되어 있음).
- 외부 HTTP 라이브러리(`requests`/`httpx`/`aiohttp`) `app/broker/kis.py`에 import 금지.

### 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기존 74개 + 본 작업 신규 (대략 18–22개) 모두 PASS.

## 2. 작업 범위

### 포함 (In scope)

`projects/paper-trading/` 아래:

- **`app/config.py`**: `kill_switch_engaged: bool = False` 필드 추가. `load_settings()`가 `KILL_SWITCH_ENGAGED` env 읽음.
- **`app/risk/engine.py`**: `RiskDecision`/`RiskEngine.evaluate()`에 kill switch 체크 추가(최상단 단축 reject).
- **`app/broker/kis.py`**: 다음을 추가/수정
  - 신규 예외: `KisOrderRejectedError(KisError)` — pre-flight 거절용. `reason` 속성 보유, 메시지에 raw credentials 미포함.
  - 신규 frozen dataclass: `KisOrderRequest` — 내부 도메인 변환 모델 (`symbol`, `side`, `quantity`, `order_type`, `limit_price`, `extended_hours`, `account_no_masked`, `broker_environment`). **외부 직렬화 안 함.**
  - 신규 함수: `validate_kis_order_request(settings, broker_order) -> None` — pre-flight 가드. 실패 시 `KisOrderRejectedError`. 검사 항목:
    - `settings.trading_mode == PAPER`
    - `settings.live_trading_enabled is False`
    - `settings.allow_market_orders is False`
    - `settings.kis_env == "paper"`
    - `settings.kill_switch_engaged is False`
    - `broker_order.order_type in (LIMIT, STOP_LIMIT)`
    - `broker_order.quantity > 0`
    - `broker_order.limit_price > 0` (Decimal 양수)
  - 신규 메서드 (`KisBroker`):
    - `get_fills() -> list` — `NotImplementedError` + TODO 메시지.
    - `get_order_status(broker_order_id: str) -> dict` — `NotImplementedError` + TODO 메시지.
  - 기존 메서드 수정 (`KisBroker`):
    - `place_order(broker_order)` — **먼저 `validate_kis_order_request(...)` 호출**, 통과 시에도 `NotImplementedError("KIS place_order: TODO confirm endpoint+TR ID")`로 fail-closed. (pre-flight가 거절하면 `KisOrderRejectedError`; 통과해도 `NotImplementedError` — 이중 fail-closed.)
    - `cancel_order(broker_order_id)` — settings 가드(kill switch/live/env) 적용 후 `NotImplementedError`. broker_order_id 자체에 raw 값 가능하지만 메시지에는 미포함.
    - `replace_order(broker_order_id, broker_order)` — `validate_kis_order_request(...)` 호출 후 `NotImplementedError`.
  - 신규 내부 helper: `_to_kis_request(broker_order) -> KisOrderRequest` — pre-flight 통과 시 호출되어 내부 도메인 변환 객체 만든다. 본 단계에서는 이 객체를 직렬화하거나 네트워크로 보내지 않음. 단위 테스트에서 변환 정합성만 검증.
- **`app/api/routes.py`**: `/paper/status` 응답에 다음 필드 추가:
  - `kis_order_entry_ready: bool` — `kis_broker is not None and not kill_switch and live disabled and kis_env=="paper"` 등 모든 정적 조건 만족. (단, 메서드가 NotImplementedError이므로 실제 실행 가능성은 별도.)
  - `kis_order_entry_mode: str` — `"disabled"` | `"paper_guarded"` | `"not_implemented"` (정의는 4.6).
  - `kis_order_methods_fail_closed: True` (literal).
  - `kill_switch_engaged: bool` — `settings.kill_switch_engaged` (디버깅/투명성 위한 부가 필드, raw 아님).
  - 기존 `live_trading_enabled`/`market_orders_allowed`/`secret_exposed` 유지.
- **`app/api/server.py`**: 변경 없음 추정. `kis_broker`가 이미 `app.state`에 보관됨.
- **`app/broker/base.py`**: 변경 없음. 기존 `BrokerAdapter` Protocol 보존.
- **`app/oms/manager.py`**: 변경 없음. OMS가 `RiskEngine.evaluate(intent)`을 내부에서 호출하므로 kill switch는 RiskEngine 측에서 자동 적용됨. KIS 라우팅 추가는 mvp-008 범위 외.
- **`.env.example`**: `KILL_SWITCH_ENGAGED=false` placeholder 추가.
- **`projects/paper-trading/README.md`**: KIS 주문 흐름 단락 추가(pre-flight 가드 + KisOrderRequest + kill switch + 본 단계 fail-closed 정책).
- **신규 테스트**:
  - `tests/test_kis_order_preflight.py`: pre-flight 가드 단위 테스트(개별 reject 사유 × 7~8개).
  - `tests/test_kis_order_request_model.py`: `KisOrderRequest` 변환 및 마스킹 검증.
  - `tests/test_kill_switch.py`: kill switch reject (RiskEngine + KIS pre-flight 양쪽).
- **수정 테스트**:
  - `tests/test_broker_interface.py`: `KisBroker`가 `get_fills`/`get_order_status` 메서드 보유 확인 + `NotImplementedError`.
  - `tests/test_api_paper_status.py`: 신규 status 필드 assertion.
  - `tests/test_risk_engine.py`: kill switch reject 케이스 추가.
- **`docs/ai/jobs/mvp-008/patch.md`**: Codex 변경 요약.

### 제외 (Out of scope; 절대 만지지 않음)

- 실제 KIS Open API HTTP 호출(인증/조회/주문 모두).
- KIS endpoint URL / TR ID / payload / header 하드코딩.
- 실주문 전송 코드.
- live trading 활성화.
- 시장가 주문 허용. `OrderType` enum에 MARKET 멤버 추가 금지.
- KIS broker를 OMS에 활성 broker로 연결. OMS는 여전히 `PaperBroker`만 사용.
- mvp-005의 PaperBroker/AlpacaPaperBroker/Strategy/PaperRunner 로직 변경.
- `app/domain/orders.py` 변경(기존 OrderIntent/Order/BrokerOrder/OrderAck 그대로).
- `app/domain/enums.py` 변경(OrderType/Side/Session/TradingMode 그대로).
- `app/domain/market.py` 변경(StrategyInput 그대로).
- mvp-001..mvp-007 산출물, `web/`, `prompts/`, `scripts/`, 기존 `docs/`(mvp-008 외) 변경.
- 외부 HTTP 라이브러리 import.
- `.env`, secrets, credentials, KIS 실제 endpoint URL.
- 인증/결제/DB migration/production infra.
- `git commit`/`push`/`merge`/`deploy` 자동화.
- 임의 shell 실행 기능.
- `pip install` 실행.

### 안전 가드

- 모든 신규/수정 코드는 위에 명시된 파일에만. 그 외 파일 미변경.
- `KisOrderRequest` 필드에 raw `account_no` 포함 금지(`account_no_masked`만).
- `KisOrderRejectedError` 메시지 빌드 시 raw key/secret/account 직접 인용 금지(reason 코드만 또는 masked 값).
- `/paper/status`의 `kis_order_entry_ready` 산출 시 `settings` 비밀 필드 직접 비교 결과로 bool만 반환(raw 값 응답에 포함 안 함).

## 3. 수정해야 할 파일

### 신규

| 파일 | 목적 |
| --- | --- |
| `tests/test_kis_order_preflight.py` | pre-flight 가드 8개 reject 사유 단위 검증 |
| `tests/test_kis_order_request_model.py` | `KisOrderRequest` 변환 + 마스킹 |
| `tests/test_kill_switch.py` | kill switch RiskEngine + KIS pre-flight reject |
| `docs/ai/jobs/mvp-008/patch.md` | Codex 변경 요약 |

### 수정

| 파일 | 변경 내용 |
| --- | --- |
| `app/config.py` | `kill_switch_engaged: bool = False` 필드 + `KILL_SWITCH_ENGAGED` env 로딩 |
| `app/risk/engine.py` | `RiskEngine.evaluate()`에 kill switch 체크 추가(최상단) |
| `app/broker/kis.py` | `KisOrderRejectedError`, `KisOrderRequest`, `validate_kis_order_request`, `_to_kis_request`, `get_fills`, `get_order_status` 추가. `place_order`/`cancel_order`/`replace_order` 수정(pre-flight + NotImplementedError 이중 fail-closed) |
| `app/api/routes.py` | `/paper/status` 응답에 `kis_order_entry_ready`/`kis_order_entry_mode`/`kis_order_methods_fail_closed`/`kill_switch_engaged` 추가 |
| `.env.example` | `KILL_SWITCH_ENGAGED=false` placeholder 추가 |
| `tests/test_broker_interface.py` | `get_fills`/`get_order_status` 보유 + NotImplementedError, `KisOrderRequest` 보유 확인 |
| `tests/test_api_paper_status.py` | 신규 4개 필드 assertion + raw 미노출 |
| `tests/test_risk_engine.py` | kill switch reject 케이스 추가 |
| `projects/paper-trading/README.md` | KIS 주문 흐름 + pre-flight + kill switch 단락 |

### 절대 미수정

- `app/domain/{enums.py,orders.py,market.py}`
- `app/broker/{base.py,paper.py,alpaca_paper.py}`
- `app/oms/manager.py` (kill switch는 RiskEngine 측에서 적용되므로 OMS 변경 불필요)
- `app/runtime/paper_runner.py`
- `app/strategy/*`
- `app/api/server.py`(kis_broker 이미 보관됨, 변경 없음)
- `app/main.py`
- 기존 테스트: `test_alpaca_paper_stub.py`, `test_config.py`, `test_models.py`, `test_oms.py`, `test_paper_broker.py`, `test_flow.py`, `test_paper_runner.py`, `test_strategy_premarket_gap.py`, `test_kis_config.py`, `test_kis_auth_client.py`, `test_kis_account_client.py`, `test_kis_market_data_client.py`
- 루트 `.gitignore`, 프로젝트 `.gitignore`
- mvp-001..mvp-007 산출물

## 4. Codex 구현 지시문

### 4.1 사전 점검 (Codex 첫 단계)

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
test -f app/broker/kis.py && grep -q "class KisBroker" app/broker/kis.py && echo "OK kis.py"
grep -q "class KisAuthClient" app/broker/kis.py && echo "OK KisAuthClient"
grep -q "kis_env" app/config.py && echo "OK Settings.kis_env"
.venv/bin/python -c "import sys; sys.path.insert(0,'.'); from app.broker.kis import KisBroker; print('importable')"
```

위가 모두 OK여야 mvp-006-1/007이 정상 land된 것. 누락되면 `patch.md` Remaining TODOs에 적고 작업 중단.

### 4.2 `app/config.py` 변경

`Settings` 클래스 끝쪽에 한 필드 추가:

```python
kill_switch_engaged: bool = False
```

`load_settings()` 의 `Settings(...)` 생성자 호출에 한 줄 추가:

```python
kill_switch_engaged=_bool_env("KILL_SWITCH_ENGAGED", False),
```

(`_bool_env`는 mvp-006-1에서 추가됨, 그대로 사용.)

기존 paper/live/market-order 가드 변경 없음. KIS 필드 변경 없음.

### 4.3 `app/risk/engine.py` 변경

`RiskEngine.evaluate(intent)` 함수의 **최상단**(다른 모든 검사 전)에 다음 분기 추가:

```python
if self._settings.kill_switch_engaged:
    return RiskDecision(approved=False, reason="kill_switch_engaged", risk_token=None)
```

(필드 이름/생성자 시그니처는 기존 `RiskDecision`을 따라 정확히 맞춤. 기존 mvp-005 RiskEngine 패턴 그대로 유지.)

### 4.4 `app/broker/kis.py` 변경

기존 코드 보존 + 다음 추가:

#### 4.4.1 신규 예외 클래스 (`KisError` 계층에 추가)

```python
class KisOrderRejectedError(KisError):
    """Order rejected by KIS adapter pre-flight guard.

    `reason` is a short code (e.g. 'market_order_disabled', 'kill_switch_engaged');
    raw credentials/account values MUST NOT appear in the message.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(f"KIS order rejected: {reason}")
        self.reason = reason
```

#### 4.4.2 `KisOrderRequest` frozen dataclass (모듈 상단 가까이)

```python
from dataclasses import dataclass as _dc_for_request
from decimal import Decimal as _Decimal_for_request
from app.domain.enums import OrderType, Side

@dataclass(frozen=True)
class KisOrderRequest:
    """Internal KIS order request domain model.

    Built locally inside KisBroker. Not serialized to network in this phase
    — KIS endpoint/TR ID/payload formats await official documentation review.
    Contains no raw account number (use account_no_masked only).
    """
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType
    limit_price: Decimal
    extended_hours: bool
    account_no_masked: str
    broker_environment: str
```

(또는 기존 import에 `dataclass`/`Decimal`/`Side`/`OrderType`이 이미 있으면 재사용. 별칭 import 불필요.)

#### 4.4.3 pre-flight 가드 함수

```python
def validate_kis_order_request(settings: Settings, broker_order: BrokerOrder) -> None:
    """Pre-flight guards for KIS order paths.

    Raises KisOrderRejectedError on the first failure with a short reason code.
    Never includes raw credentials/account in the message.
    """
    if settings.trading_mode != TradingMode.PAPER:
        raise KisOrderRejectedError("trading_mode_not_paper")
    if settings.live_trading_enabled:
        raise KisOrderRejectedError("live_trading_enabled")
    if settings.allow_market_orders:
        raise KisOrderRejectedError("market_orders_allowed_flag_set")
    if settings.kis_env != "paper":
        raise KisOrderRejectedError("kis_env_not_paper")
    if settings.kill_switch_engaged:
        raise KisOrderRejectedError("kill_switch_engaged")
    if broker_order.order_type not in (OrderType.LIMIT, OrderType.STOP_LIMIT):
        raise KisOrderRejectedError("order_type_not_limit")
    if broker_order.quantity is None or broker_order.quantity <= 0:
        raise KisOrderRejectedError("quantity_invalid")
    if broker_order.limit_price is None or broker_order.limit_price <= 0:
        raise KisOrderRejectedError("limit_price_invalid")
```

#### 4.4.4 `KisBroker` 메서드 수정

**`place_order`** (기존 NotImplementedError 메시지 보존):

```python
def place_order(self, broker_order: BrokerOrder) -> OrderAck:
    validate_kis_order_request(self._settings, broker_order)
    self._to_kis_request(broker_order)  # build but don't serialize
    raise NotImplementedError(
        "KIS place_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard. "
        "Pre-flight passed but HTTP transmission is intentionally not implemented "
        "until KIS Open API endpoints/TR IDs/payloads are confirmed from official documentation."
    )
```

**`cancel_order`**:

```python
def cancel_order(self, broker_order_id: str) -> None:
    # broker_order_id is opaque; only settings-level guards apply here.
    if self._settings.trading_mode != TradingMode.PAPER:
        raise KisOrderRejectedError("trading_mode_not_paper")
    if self._settings.live_trading_enabled:
        raise KisOrderRejectedError("live_trading_enabled")
    if self._settings.kis_env != "paper":
        raise KisOrderRejectedError("kis_env_not_paper")
    if self._settings.kill_switch_engaged:
        raise KisOrderRejectedError("kill_switch_engaged")
    raise NotImplementedError(
        "KIS cancel_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard."
    )
```

**`replace_order`**:

```python
def replace_order(self, broker_order_id: str, broker_order: BrokerOrder) -> OrderAck:
    validate_kis_order_request(self._settings, broker_order)
    raise NotImplementedError(
        "KIS replace_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard."
    )
```

**신규 메서드 `get_fills`**:

```python
def get_fills(self) -> list[OrderAck]:
    raise NotImplementedError(
        "KIS get_fills(): TODO — confirm fills endpoint, TR ID, payload, and response shape "
        "from KIS Open API official documentation. Do not invent endpoints."
    )
```

**신규 메서드 `get_order_status`**:

```python
def get_order_status(self, broker_order_id: str) -> dict[str, Any]:
    raise NotImplementedError(
        "KIS get_order_status(): TODO — confirm order status endpoint, TR ID, payload, and response shape "
        "from KIS Open API official documentation. Do not invent endpoints."
    )
```

#### 4.4.5 내부 변환 helper

```python
def _to_kis_request(self, broker_order: BrokerOrder) -> KisOrderRequest:
    return KisOrderRequest(
        symbol=broker_order.symbol,
        side=broker_order.side,
        quantity=broker_order.quantity,
        order_type=broker_order.order_type,
        limit_price=broker_order.limit_price,
        extended_hours=False,  # default; KIS overseas extended-hours handling deferred
    account_no_masked=self._account.masked_account_no(),
        broker_environment=self._settings.kis_env or "paper",
    )
```

(필드 정렬은 BrokerOrder의 실제 attribute에 맞춰 보정. 만약 BrokerOrder에 `extended_hours`가 이미 있다면 그것을 사용; 없으면 기본 False.)

#### 4.4.6 `healthcheck()` 확장 (선택, 최소)

기존 dict에 다음 한 줄 추가 가능:

```python
"order_methods_fail_closed": True,
```

이 항목은 `/paper/status`의 `kis_order_methods_fail_closed`로 직접 surface되므로 healthcheck에서 같이 노출하면 일관성 있음.

### 4.5 `app/api/routes.py` 변경

`/paper/status` 응답 산출 부분에:

```python
# mvp-008: order-entry guard metadata
kis_order_entry_mode = "disabled"
if kis_broker is not None:
    # All settings-level guards must hold for "paper_guarded" to apply.
    settings_safe = (
        settings.trading_mode.value == "paper"
        and settings.live_trading_enabled is False
        and settings.allow_market_orders is False
        and settings.kis_env == "paper"
        and settings.kill_switch_engaged is False
    )
    # In this phase, HTTP transmission is not implemented; even if guards
    # would pass, the mode is "not_implemented". Once HTTP is wired and
    # paper-only execution is verified in a later mvp, this becomes
    # "paper_guarded".
    kis_order_entry_mode = "not_implemented" if settings_safe else "disabled"

kis_order_entry_ready = (kis_broker is not None) and (kis_order_entry_mode != "disabled")
```

응답 dict에 추가:

```python
"kis_order_entry_ready": kis_order_entry_ready,
"kis_order_entry_mode": kis_order_entry_mode,
"kis_order_methods_fail_closed": True,
"kill_switch_engaged": bool(settings.kill_switch_engaged),
```

기존 `live_trading_enabled`/`market_orders_allowed`/`secret_exposed`/`kis_*` 필드는 그대로 유지.

### 4.6 `.env.example` 변경

기존 `ALLOW_MARKET_ORDERS=false` 부근에 한 줄 추가:

```
KILL_SWITCH_ENGAGED=false
```

기존 다른 라인은 변경 없음. 실제 secret 포함 금지.

### 4.7 `projects/paper-trading/README.md` 변경

`## KIS Open API (모의투자) 연결 준비` 섹션 아래에 단락 추가:

```markdown
### 주문 흐름 안전 가드 (mvp-008)

`KisBroker.place_order` / `cancel_order` / `replace_order` 호출 시 다음 pre-flight 가드를 통과해야 합니다(`validate_kis_order_request`):

- `trading_mode == paper`
- `live_trading_enabled is False`
- `allow_market_orders is False`
- `kis_env == "paper"`
- `kill_switch_engaged is False`
- `order_type in (LIMIT, STOP_LIMIT)`
- `quantity > 0`
- `limit_price > 0`

가드 실패 시 `KisOrderRejectedError(reason)`로 즉시 거절합니다. 메시지에는 사유 코드만 들어가며 raw credentials/계좌번호는 포함되지 않습니다.

가드를 통과하더라도 KIS HTTP 전송은 본 단계에서 구현되지 않습니다 — 다음 메서드는 항상 `NotImplementedError`로 fail-closed 합니다: `place_order`, `cancel_order`, `replace_order`, `get_open_orders`, `get_fills`, `get_order_status`.

`KisOrderRequest`는 내부 도메인 변환 모델로, KIS HTTP payload로 직렬화되지 않고 단위 테스트 및 향후 mvp 연결 시 입력 모델로만 사용됩니다. 계좌번호는 `account_no_masked`로만 보유합니다.

`kill_switch_engaged=true`로 설정하면 RiskEngine이 모든 주문을 즉시 거절하고, KIS pre-flight도 동일하게 거절합니다. `.env`의 `KILL_SWITCH_ENGAGED=true`로 활성화하거나 운영자가 수동으로 켤 수 있습니다.

`/paper/status`는 `kis_order_entry_ready`, `kis_order_entry_mode`(`disabled | paper_guarded | not_implemented`), `kis_order_methods_fail_closed`, `kill_switch_engaged`를 노출합니다.
```

기타 기존 단락은 변경 없음.

### 4.8 테스트

#### `tests/test_kis_order_preflight.py` (신규)

```python
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.broker.kis import (
    KisBroker,
    KisOrderRejectedError,
    KisOrderRequest,
    validate_kis_order_request,
)
from app.config import Settings
from app.domain.enums import OrderType, Side, TradingMode
from app.domain.orders import BrokerOrder


def _settings(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_account_no="12345678",
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
    )


def _broker_order(**overrides) -> BrokerOrder:
    data = dict(
        symbol="AAPL",
        side=Side.BUY,
        quantity=10,
        order_type=OrderType.LIMIT,
        limit_price=Decimal("100"),
        risk_token="rt",
        created_at=datetime.now(timezone.utc),
        oms_id="oms-1",
        submitted_at=datetime.now(timezone.utc),
    )
    data.update(overrides)
    return BrokerOrder(**data)


# ... 8 tests, one per reject condition + 1 happy-path-then-NotImplemented ...
```

핵심 케이스 (요청 6번의 4–7번과 일치):
1. `test_preflight_passes_for_valid_paper_limit_order` → `validate_kis_order_request` 정상 반환(None).
2. `test_preflight_rejects_live_trading_enabled` → reason `"live_trading_enabled"`.
3. `test_preflight_rejects_allow_market_orders_flag` → reason `"market_orders_allowed_flag_set"`.
4. `test_preflight_rejects_kis_env_not_paper` → reason `"kis_env_not_paper"`.
5. `test_preflight_rejects_kill_switch_engaged` → reason `"kill_switch_engaged"`.
6. `test_preflight_rejects_non_limit_order_type` — `OrderType.STOP_LIMIT`은 통과, 그 외(가상의 MARKET 시뮬레이션은 OrderType에 없으므로 모킹 어려움; 대신 broker_order의 `order_type`을 None으로 강제 mock한 객체로 검증; 또는 dataclass replace로 NoneType 시뮬은 불가하므로 `STOP_LIMIT`이 통과되는지만 검증하고 "MARKET 미존재"는 `assert "MARKET" not in OrderType.__members__`로 보강).
7. `test_preflight_rejects_zero_quantity` → reason `"quantity_invalid"`.
8. `test_preflight_rejects_zero_limit_price` → reason `"limit_price_invalid"` (Decimal("0") 사용).
9. `test_place_order_runs_preflight_before_notimplemented` — `KisBroker.place_order(invalid_order)`가 `KisOrderRejectedError`를 raise(NotImplementedError 아님).
10. `test_place_order_valid_input_reaches_notimplemented` — 정상 broker_order로 호출 → `NotImplementedError` (preflight 통과 후 실주문 미구현).

각 테스트는 raw `kis_app_key`/`kis_app_secret`/계좌번호 원문을 출력하지 않음(테스트 코드의 fake 값 `"12345678"`, `"fake-key"`, `"fake-secret"` 사용).

#### `tests/test_kis_order_request_model.py` (신규)

```python
def test_kis_order_request_contains_no_raw_account_field():
    fields_set = {f.name for f in KisOrderRequest.__dataclass_fields__.values()}
    assert "account_no" not in fields_set
    assert "account_no_masked" in fields_set


def test_to_kis_request_uses_masked_account(settings):
    broker = KisBroker(_settings(settings))
    req = broker._to_kis_request(_broker_order())
    assert req.account_no_masked.startswith("***")
    assert "12345678" not in repr(req)


def test_to_kis_request_preserves_order_fields(settings):
    broker = KisBroker(_settings(settings))
    bo = _broker_order(quantity=42, limit_price=Decimal("99.50"))
    req = broker._to_kis_request(bo)
    assert req.symbol == bo.symbol
    assert req.side == bo.side
    assert req.quantity == 42
    assert req.limit_price == Decimal("99.50")
    assert req.broker_environment == "paper"
```

#### `tests/test_kill_switch.py` (신규)

```python
def test_risk_engine_rejects_when_kill_switch_engaged(settings):
    s = replace(settings, kill_switch_engaged=True, symbol_allowlist=("AAPL",))
    intent = OrderIntent(
        symbol="AAPL", side=Side.BUY, quantity=10,
        order_type=OrderType.LIMIT, limit_price=Decimal("100"),
    )
    decision = RiskEngine(s).evaluate(intent)
    assert decision.approved is False
    assert decision.reason == "kill_switch_engaged"


def test_kis_preflight_rejects_when_kill_switch_engaged(settings):
    s = replace(_settings(settings), kill_switch_engaged=True)
    with pytest.raises(KisOrderRejectedError, match="kill_switch_engaged"):
        validate_kis_order_request(s, _broker_order())


def test_kill_switch_default_off(settings):
    assert settings.kill_switch_engaged is False
```

#### 수정 `tests/test_broker_interface.py`

추가:

```python
def test_kis_broker_has_get_fills_and_get_order_status(settings):
    b = KisBroker(_configured(settings))
    assert callable(b.get_fills)
    assert callable(b.get_order_status)
    with pytest.raises(NotImplementedError, match="TODO"):
        b.get_fills()
    with pytest.raises(NotImplementedError, match="TODO"):
        b.get_order_status("oms-1")


def test_kis_order_request_class_is_exported():
    from app.broker.kis import KisOrderRequest, KisOrderRejectedError, validate_kis_order_request
    assert KisOrderRequest is not None
    assert KisOrderRejectedError is not None
    assert callable(validate_kis_order_request)
```

#### 수정 `tests/test_api_paper_status.py`

기존 두 status 테스트에 다음 assertion 추가(두 시나리오 모두):

```python
assert body["kis_order_methods_fail_closed"] is True
assert body["kis_order_entry_mode"] in ("disabled", "paper_guarded", "not_implemented")
assert isinstance(body["kis_order_entry_ready"], bool)
assert "kill_switch_engaged" in body
assert isinstance(body["kill_switch_engaged"], bool)
```

KIS configured 케이스: `kis_order_entry_ready is True`, `kis_order_entry_mode == "not_implemented"`.
KIS 미configured 케이스: `kis_order_entry_ready is False`, `kis_order_entry_mode == "disabled"`.

#### 수정 `tests/test_risk_engine.py`

추가:

```python
def test_risk_engine_kill_switch_at_top(settings):
    s = replace(settings, kill_switch_engaged=True, symbol_allowlist=("AAPL",))
    decision = RiskEngine(s).evaluate(_intent())
    assert decision.approved is False
    assert decision.reason == "kill_switch_engaged"
```

(`_intent()`은 기존 테스트의 helper 패턴 재사용.)

### 4.9 검증 명령

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기존 74개 + 신규 ~20개 모두 PASS. 종료코드 0.

저장소 루트:

```bash
git diff --stat
git status --short
```

(mvp-008 변경은 `projects/paper-trading/` 안에서 일어나므로 `git diff --stat`은 mvp-008 외 dirty만 보고; mvp-008은 `git status`에서 untracked 또는 modified로 확인.)

### 4.10 `docs/ai/jobs/mvp-008/patch.md`

요청의 검증 섹션과 안전 조건을 1:1로 반영하는 구조:

```markdown
## 1. Files Changed
(전체 목록)

## 2. Implementation Summary

### 2.1 KIS 주문 메서드 경계
- get_fills, get_order_status 추가 (모두 NotImplementedError + TODO)
- place_order/cancel_order/replace_order: pre-flight → NotImplementedError 이중 fail-closed
- 메시지에 raw credentials/account 미포함

### 2.2 OMS → KIS 연결 준비
- OMS 코드 미변경. RiskEngine에 kill switch가 들어가 OMS 경로 어디서도 자동 차단.
- KisBroker는 여전히 OMS의 활성 broker가 아님(PaperBroker 그대로).
- BrokerAdapter Protocol은 호환성 유지.

### 2.3 KisOrderRequest 모델
- 내부 도메인 변환 객체, 직렬화하지 않음.
- 계좌번호는 account_no_masked로만 보유(***xxxx).
- broker_environment는 항상 "paper".

### 2.4 주문 안전 guard
- validate_kis_order_request에서 8개 reject 사유 단축 평가.
- RiskEngine에 kill_switch_engaged 최상단 reject 추가.
- 각 사유 코드는 short string으로 raw 값 미포함.

### 2.5 /paper/status 신규 필드
- kis_order_entry_ready (bool)
- kis_order_entry_mode (disabled|paper_guarded|not_implemented)
- kis_order_methods_fail_closed (True literal)
- kill_switch_engaged (bool)

### 2.6 실행한 테스트
- compileall: PASS
- pytest: 74 + 신규 N PASS, 회귀 없음
- 신규 테스트 파일 목록

### 2.7 공식 문서 부재로 TODO 유지 항목
- KIS 주문 전송 endpoint, TR ID, payload, 응답 shape
- KIS 취소/정정 endpoint, payload
- 체결/주문 상태 조회 endpoint, TR ID
- 본 작업은 모두 NotImplementedError로 fail-closed

### 2.8 다음 mvp 후보
- mvp-009: KIS 인증 HTTP 호출 실제 구현 (KIS 공식 문서 reference 후)
- 또는 mvp-009: kill switch GUI 토글 / 운영 도구

## 3. Safety Confirmation
- 실주문 코드 없음, 모든 KIS 주문 메서드 NotImplementedError
- KIS endpoint URL/TR ID 코드 0건
- 외부 HTTP 라이브러리 import 0건
- raw key/secret/account 코드/문서/.env.example/응답/log/patch 미노출
- OrderType MARKET 부재 유지
- live trading 6단 + KIS 7단째(pre-flight) 차단 모두 작동
- OMS는 PaperBroker만 사용, KIS 미연결
- Strategy 패키지가 KIS import 0건
- commit/push/merge/deploy 자동화 없음

## 4. Test Results
(compileall + pytest 출력 그대로)

## 5. Remaining TODOs
- KIS 공식 문서 확인 후 실제 HTTP 호출 구현(별도 mvp).
- mvp-008 외 dirty 워크트리(GUI 변경) 별도 commit 분리는 사람 액션.
```

## 5. 테스트 기준

1. `.venv/bin/python -m compileall app tests` 종료코드 0.
2. `.venv/bin/python -m pytest -p no:cacheprovider` 종료코드 0. 기존 74개 + 신규 약 18–22개 모두 PASS.
3. `grep -RIn "OrderType\.MARKET" projects/paper-trading/app` 결과 0건 유지.
4. `grep -RIn "https?://" projects/paper-trading/app/broker/kis.py` 결과 0건 유지.
5. `grep -RInE "import requests|import httpx|import aiohttp" projects/paper-trading/app/broker/kis.py` 결과 0건 유지.
6. `grep -RInE "from app\.broker\.kis" projects/paper-trading/app/strategy/` 결과 0건 유지.
7. `grep -RIn "TR_ID|tr_id|/uapi/|/oauth2/" projects/paper-trading/app/broker/kis.py` 결과 0건.
8. `grep -RIn "kis_account_no\s*=\s*\"5[0-9]\{7\}\"" projects/paper-trading/` 결과 0건(실 계좌 패턴 없음 — 테스트는 `"12345678"` 사용).
9. `KisOrderRequest`에 raw `account_no` 필드 없음(`account_no_masked`만).
10. `validate_kis_order_request` 메시지에 raw key/secret/account 미포함(`reason` short code만).
11. `/paper/status` 응답에 `kis_order_entry_ready`/`kis_order_entry_mode`/`kis_order_methods_fail_closed`/`kill_switch_engaged` 모두 존재, raw 값 미노출.
12. `git diff --stat`에 mvp-008 외 변경 없음(이미 dirty인 mvp-004 잔재/GUI 변경은 그대로).
13. `.env` staged/committed 없음.

## 6. 리뷰 체크리스트

- [ ] mvp-006-1/007 사전 점검 통과.
- [ ] `Settings.kill_switch_engaged` 필드 + `KILL_SWITCH_ENGAGED` env 로딩.
- [ ] `RiskEngine.evaluate()` 최상단에 kill switch 단축 reject. reason `"kill_switch_engaged"`.
- [ ] `KisOrderRejectedError` 정의, `reason` 속성 노출, 메시지에 raw 값 미포함.
- [ ] `KisOrderRequest` frozen dataclass, raw `account_no` 필드 없음, `account_no_masked` 있음.
- [ ] `validate_kis_order_request`: 8개 reject 사유 모두 short reason code.
- [ ] `KisBroker.place_order` — pre-flight 호출 → 정상 시 `NotImplementedError`로 fail-closed.
- [ ] `KisBroker.cancel_order` — 4개 settings 가드 → `NotImplementedError`.
- [ ] `KisBroker.replace_order` — pre-flight → `NotImplementedError`.
- [ ] `KisBroker.get_fills`/`get_order_status` NotImplementedError + TODO.
- [ ] `_to_kis_request`이 raw account 미노출(`***xxxx` 사용), KisOrderRequest 반환.
- [ ] `/paper/status`에 신규 4개 필드 추가, raw credentials 미노출.
- [ ] `.env.example`에 `KILL_SWITCH_ENGAGED=false` 추가, 실제 값 없음.
- [ ] mvp-005 기존 19개 + mvp-006-1 17개 + mvp-007 38개 + mvp-008 신규 18–22개 모두 PASS.
- [ ] 외부 HTTP 라이브러리 `kis.py`에 import 0건.
- [ ] KIS endpoint URL/TR ID 코드 0건.
- [ ] `app/domain/{enums,orders,market}.py`, `app/broker/{base,paper,alpaca_paper}.py`, `app/oms/manager.py`, `app/runtime/paper_runner.py`, `app/strategy/*`, `app/api/server.py`, `app/main.py` 미변경.
- [ ] mvp-001..mvp-007 산출물, `web/`/`prompts/`/`scripts/`/기존 `docs/` 미변경.
- [ ] `OrderType`에 MARKET 미추가.
- [ ] `.env` staged/committed 없음.
- [ ] commit/push/merge/deploy 자동화 없음.
- [ ] `patch.md` 5섹션 + Implementation Summary 8단락 완성.
