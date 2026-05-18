## 1. 요청 요약

KIS 모의투자 주문 흐름의 **내부 경계 + 변환 모델 + 안전 가드 + 응답 sanitization + idempotency hook + 세분화된 가용성 상태**를 만든다. 실제 KIS HTTP 호출/실주문은 본 작업에서도 만들지 않는다(공식 문서 미확인 상태 유지).

### 컨텍스트 — mvp-008 흡수

mvp-008(`docs/ai/jobs/mvp-008/plan.md`)이 본 세션에서 plan만 작성되고 구현되지 않았다. mvp-009는 mvp-008의 모든 scope(pre-flight 가드, KisOrderRequest, kill switch in RiskEngine, get_fills/get_order_status 메서드, /paper/status에 entry 모드 필드)를 **흡수**한다. mvp-008 plan/codex-task는 그대로 두되 deprecated — Codex는 mvp-009 단독으로 작업한다.

mvp-009가 mvp-008보다 추가로 가지는 것:

| 항목 | mvp-008 | mvp-009 |
| --- | --- | --- |
| KisOrderRequest 필드 | symbol/side/quantity/order_type/limit_price/extended_hours/account_no_masked/broker_environment | + `market`, + `idempotency_key` |
| KisOrderResponse 모델 | 없음 | 신규 — `raw_response_sanitized` 포함 |
| 응답 sanitization | 없음 | `sanitize_kis_response()` 함수 신설 |
| Idempotency | 없음 | `KisBroker._idempotency_key_for(broker_order)` deterministic 키 생성 |
| 상태 응답 가용성 | `kis_order_entry_mode` 단일 enum | 메서드별 5개 bool: `kis_order_submission_available`/`cancel`/`replace`/`open_orders`/`fills` |
| Capabilities API | 없음 | `KisBroker.capabilities() -> dict[str, bool]` |

### 핵심 절대 조건 (mvp-005/006-1/007 안전 불변식 + 본 작업 추가)

- live trading 6단 차단 그대로 + 본 작업 7단째: `validate_kis_order_request` pre-flight.
- `OrderType.MARKET` 부재 유지.
- 모든 주문 `Strategy → RiskEngine → OMS → BrokerAdapter`. KIS 주문 메서드는 외부에서 직접 호출되지 않음(OMS만 진입점).
- KIS endpoint URL / TR ID / payload 코드 하드코딩 금지. 공식 문서 확인 전에는 실주문 전송 코드 일체 미작성.
- `place_order`/`cancel_order`/`replace_order`/`get_open_orders`/`get_fills`/`get_order_status`는 pre-flight 통과 시에도 최종 `NotImplementedError` 또는 `KisOrderRejectedError`로 fail-closed.
- 외부 HTTP 라이브러리(`requests`/`httpx`/`aiohttp`) import 금지.
- 에러 메시지/sanitized response에 raw key/secret/account/access_token 미포함.
- `Settings` 비밀 필드 `repr=False` + `KisBroker`/sub-client `__repr__` 마스킹 유지.
- `/paper/status`나 어떤 응답에서도 credentials 노출 금지. 계좌번호는 마스킹.
- `git commit`/`push`/`merge`/`deploy` 자동화 금지. `.env` Git 추가 금지.
- `pip install` 실행 금지(이미 `.venv`에 의존성 설치됨).
- 공식 문서 미확인 부분은 모두 `NotImplementedError` + 명시적 TODO 메시지로 fail-closed.

### 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기존 74개(mvp-007 시점) + 신규 약 28–34개 모두 PASS.

## 2. 작업 범위

### 포함 (In scope)

`projects/paper-trading/` 아래:

- **`app/config.py`**: `kill_switch_engaged: bool = False` 필드 추가, `load_settings`이 `KILL_SWITCH_ENGAGED` env 읽음(mvp-008에서 흡수).
- **`app/risk/engine.py`**: `RiskEngine.evaluate()` 최상단 kill switch 단축 reject 추가(mvp-008 흡수).
- **`app/broker/kis.py`**: 다음 모두 추가/수정
  - 신규 예외 `KisOrderRejectedError(KisError)` (mvp-008 흡수).
  - 신규 frozen dataclass `KisOrderRequest` (필드: `symbol`, `market`, `side`, `quantity`, `order_type`, `limit_price`, `extended_hours`, `account_no_masked`, `broker_environment`, `idempotency_key`).
  - 신규 frozen dataclass `KisOrderResponse` (필드: `internal_order_id`, `broker_order_id`, `broker`, `status`, `submitted_at`, `symbol`, `side`, `quantity`, `limit_price`, `raw_response_sanitized: dict[str, Any]`).
  - 신규 함수 `sanitize_kis_response(raw: dict | None, settings: Settings) -> dict` — 입력 dict에서 key/secret/account 원문이 포함된 필드를 마스킹/제거. fallback default가 안전 dict.
  - 신규 함수 `validate_kis_order_request(settings, broker_order) -> None` — 8개 reject 사유 short reason code(mvp-008 흡수). raw 값 미포함 메시지.
  - 신규 `KisBroker._idempotency_key_for(broker_order)` — deterministic 키 생성. `broker_order.oms_id`(고유) 기반의 `idempotency_key = f"kis-paper-{oms_id}"`.
  - 신규 `KisBroker._to_kis_request(broker_order)` — pre-flight 통과 후 KisOrderRequest 빌드. `account_no_masked`는 `self._account.masked_account_no()` 사용, raw account 미사용.
  - 신규 `KisBroker.capabilities() -> dict[str, bool]` — `{"submission": False, "cancel": False, "replace": False, "open_orders": False, "fills": False, "order_status": False}` 반환. 현 단계에서는 모두 False(NotImplementedError이므로). 향후 HTTP가 wired 되면 개별 bool이 True로.
  - 수정 `place_order`: pre-flight → `_to_kis_request` 빌드 → 최종 `NotImplementedError`(공식 문서 필요 메시지).
  - 수정 `cancel_order`: settings 가드(paper/live/env/kill_switch) → `NotImplementedError`.
  - 수정 `replace_order`: pre-flight → 빌드 → `NotImplementedError`.
  - 신규 `get_fills() -> list`: `NotImplementedError` + 공식 문서 TODO.
  - 신규 `get_order_status(broker_order_id) -> dict`: `NotImplementedError` + 공식 문서 TODO.
  - 기존 `get_open_orders`는 그대로 `NotImplementedError`(mvp-007에서 이미 존재).
- **`app/api/routes.py`**: `/paper/status` 응답에 다음 추가:
  - `kis_order_entry_ready` (bool, mvp-008 흡수)
  - `kis_order_entry_mode` (`disabled` | `paper_guarded` | `not_implemented`, mvp-008 흡수)
  - `kis_order_methods_fail_closed: True` (literal, mvp-008 흡수)
  - `kill_switch_engaged` (bool, mvp-008 흡수)
  - **신규 (mvp-009)**: `kis_order_submission_available`, `kis_cancel_available`, `kis_replace_available`, `kis_open_orders_available`, `kis_fills_available` — `kis_broker.capabilities()` 결과에서 매핑.
- **`.env.example`**: `KILL_SWITCH_ENGAGED=false` placeholder 추가(mvp-008 흡수).
- **`projects/paper-trading/README.md`**: KIS 주문 흐름 단락(mvp-008 + mvp-009 통합 설명: pre-flight, KisOrderRequest/Response, sanitization, idempotency, capabilities).
- **신규 테스트**:
  - `tests/test_kis_order_preflight.py` (mvp-008 흡수): 8개 reject 사유 + 정상 통과 후 NotImplementedError.
  - `tests/test_kis_order_request_model.py` (mvp-008 흡수 + market/idempotency_key 검증): 필드 존재, raw account 미포함, idempotency_key deterministic.
  - `tests/test_kis_order_response_model.py` (신규): `KisOrderResponse` dataclass 필드 + `sanitize_kis_response` 정상 마스킹.
  - `tests/test_kill_switch.py` (mvp-008 흡수): RiskEngine + KIS pre-flight reject.
  - `tests/test_kis_capabilities.py` (신규): `KisBroker.capabilities()`가 6개 bool dict 반환, 현 단계에서 모두 False.
- **수정 테스트**:
  - `tests/test_broker_interface.py`: `get_fills`/`get_order_status` 메서드 + `KisOrderRequest`/`KisOrderResponse`/`sanitize_kis_response` exports 확인 + `capabilities` property 확인.
  - `tests/test_api_paper_status.py`: 신규 9개 필드(mvp-008 4개 + mvp-009 5개) assertion + raw 미노출.
  - `tests/test_risk_engine.py`: kill switch reject 케이스(mvp-008 흡수).
- **`docs/ai/jobs/mvp-009/patch.md`**: Codex 변경 요약.

### 제외 (Out of scope; 절대 만지지 않음)

- 실제 KIS Open API HTTP 호출(인증/조회/주문 모두).
- KIS endpoint URL / TR ID / payload / header 하드코딩.
- 실주문 전송 코드.
- live trading 활성화.
- 시장가 주문 허용. `OrderType` enum에 MARKET 멤버 추가 금지.
- KIS broker를 OMS에 활성 broker로 연결. OMS는 여전히 `PaperBroker`만 사용. (KIS 주문 메서드는 외부에서 직접 호출되지 않으며 OMS 라우팅은 별도 mvp.)
- OMS의 idempotency 트래킹(intent ledger). 본 mvp는 KisBroker 측의 deterministic 키 생성까지만.
- mvp-005의 PaperBroker/AlpacaPaperBroker/Strategy/PaperRunner 로직 변경.
- `app/domain/{enums.py,orders.py,market.py}` 변경. (OrderIntent/Order/BrokerOrder/OrderAck/StrategyInput 그대로.)
- mvp-001..mvp-008 산출물(plan/codex-task/patch/review 문서) 변경.
- `web/`, `prompts/`, `scripts/`, `examples/`, 기존 `docs/`(mvp-009 외) 변경.
- 외부 HTTP 라이브러리 import.
- `.env`, secrets, credentials, KIS 실제 endpoint URL.
- 인증/결제/DB migration/production infra.
- `git commit`/`push`/`merge`/`deploy` 자동화.
- 임의 shell 실행 기능.
- `pip install` 실행.

### 안전 가드

- 모든 신규/수정 코드는 위 명시 파일에만.
- `KisOrderRequest`에 raw `account_no` 필드 없음 — `account_no_masked`만.
- `KisOrderResponse.raw_response_sanitized`는 `sanitize_kis_response`를 통한 결과만 저장. 원본 dict 직접 저장 금지.
- `sanitize_kis_response`는 다음 패턴을 제거/마스킹:
  - 키 이름이 `app_key`, `appkey`, `app_secret`, `appsecret`, `appKey`, `appSecret`, `accountNo`, `account_no`, `cano`, `acct_no`, `access_token`, `accessToken`, `Authorization`, `tr_key`(case-insensitive) 매칭 시 → 값을 `"<redacted>"` 또는 마스킹 형태로 치환.
  - 값이 `settings.kis_app_key`/`kis_app_secret`/`kis_account_no`와 정확 일치하면 → `"<redacted>"` 치환.
- `validate_kis_order_request` 메시지에 raw 값 직접 인용 금지(reason short code만).
- `/paper/status`의 capabilities 매핑은 `kis_broker.capabilities()` 호출 결과만 사용 — 직접 메서드 attribute 검사 금지.

## 3. 수정해야 할 파일

### 신규

| 파일 | 목적 |
| --- | --- |
| `tests/test_kis_order_preflight.py` | pre-flight 8개 사유 + 통과 후 NotImplementedError |
| `tests/test_kis_order_request_model.py` | KisOrderRequest 필드/마스킹/idempotency_key deterministic |
| `tests/test_kis_order_response_model.py` | KisOrderResponse 필드 + sanitize_kis_response 마스킹 |
| `tests/test_kill_switch.py` | RiskEngine + KIS pre-flight kill switch reject |
| `tests/test_kis_capabilities.py` | capabilities() dict, 모두 False |
| `docs/ai/jobs/mvp-009/patch.md` | Codex 변경 요약 |

### 수정

| 파일 | 변경 내용 |
| --- | --- |
| `app/config.py` | `kill_switch_engaged` 필드 + `KILL_SWITCH_ENGAGED` env 로딩 |
| `app/risk/engine.py` | `RiskEngine.evaluate()` 최상단 kill switch reject |
| `app/broker/kis.py` | KisOrderRejectedError, KisOrderRequest(+market+idempotency_key), KisOrderResponse, sanitize_kis_response, validate_kis_order_request, _idempotency_key_for, _to_kis_request, get_fills, get_order_status, capabilities. place_order/cancel_order/replace_order pre-flight 적용 |
| `app/api/routes.py` | `/paper/status` 9개 신규 필드 + capabilities 매핑 |
| `.env.example` | `KILL_SWITCH_ENGAGED=false` placeholder |
| `tests/test_broker_interface.py` | 신규 메서드/타입 노출 확인 |
| `tests/test_api_paper_status.py` | 9개 신규 필드 assertion + raw 미노출 |
| `tests/test_risk_engine.py` | kill switch reject 케이스 |
| `projects/paper-trading/README.md` | KIS 주문 흐름 (pre-flight + Request/Response + sanitization + idempotency + capabilities) 단락 |

### 절대 미수정

- `app/domain/{enums.py,orders.py,market.py}`
- `app/broker/{base.py,paper.py,alpaca_paper.py}`
- `app/oms/manager.py`
- `app/runtime/paper_runner.py`
- `app/strategy/*`
- `app/api/server.py` (kis_broker 이미 보관, capabilities는 routes에서 호출)
- `app/main.py`
- 기존 테스트(mvp-005 ~ mvp-007) 중 본 작업이 다루지 않는 것
- 루트 `.gitignore`, 프로젝트 `.gitignore`
- mvp-001..mvp-008 산출물 (mvp-008 plan/codex-task는 deprecated, 그대로 둠)

## 4. Codex 구현 지시문

### 4.1 사전 점검

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
test -f app/broker/kis.py && grep -q "class KisBroker" app/broker/kis.py && echo "OK KisBroker"
grep -q "class KisAuthClient" app/broker/kis.py && echo "OK KisAuthClient"
grep -q "class KisAccountClient" app/broker/kis.py && echo "OK KisAccountClient"
grep -q "class KisMarketDataClient" app/broker/kis.py && echo "OK KisMarketDataClient"
grep -q "kis_env" app/config.py && echo "OK Settings.kis_env"
grep -q "kill_switch_engaged" app/config.py && echo "OK kill_switch_engaged"  # may be present from mvp-008 absorb
grep -q "kis_authenticated" app/api/routes.py && echo "OK routes.py KIS status"
test -d .venv && echo "OK venv"
```

(필수: 7번째는 누락 가능 — mvp-008이 미구현 상태이면 본 작업이 추가하므로. 그 외는 모두 OK여야 함.)

### 4.2 `app/config.py`

`Settings`에 한 필드 추가(없으면):

```python
kill_switch_engaged: bool = False
```

`load_settings()` 생성자에 한 줄 추가(없으면):

```python
kill_switch_engaged=_bool_env("KILL_SWITCH_ENGAGED", False),
```

이미 mvp-008 흡수로 인해 존재할 수 있음 — idempotent 추가.

### 4.3 `app/risk/engine.py`

`RiskEngine.evaluate(intent)` 최상단에:

```python
if self._settings.kill_switch_engaged:
    return RiskDecision(approved=False, reason="kill_switch_engaged", risk_token=None)
```

(`RiskDecision` 시그니처는 기존 코드와 일치하게 작성.)

### 4.4 `app/broker/kis.py`

#### 4.4.1 신규 예외

```python
class KisOrderRejectedError(KisError):
    def __init__(self, reason: str) -> None:
        super().__init__(f"KIS order rejected: {reason}")
        self.reason = reason
```

#### 4.4.2 KisOrderRequest

```python
@dataclass(frozen=True)
class KisOrderRequest:
    """Internal KIS order request domain model.

    Not serialized to network in this phase — KIS endpoint/TR ID/payload formats
    await official documentation review. Contains no raw account number.
    """
    symbol: str
    market: str
    side: Side
    quantity: int
    order_type: OrderType
    limit_price: Decimal
    extended_hours: bool
    account_no_masked: str
    broker_environment: str
    idempotency_key: str
```

#### 4.4.3 KisOrderResponse

```python
@dataclass(frozen=True)
class KisOrderResponse:
    """Internal KIS order response model.

    raw_response_sanitized must be produced via sanitize_kis_response() to
    prevent credential/account leakage.
    """
    internal_order_id: str
    broker_order_id: str | None
    broker: str
    status: str
    submitted_at: datetime
    symbol: str
    side: Side
    quantity: int
    limit_price: Decimal
    raw_response_sanitized: dict[str, Any]
```

#### 4.4.4 sanitize_kis_response

```python
_SECRET_KEYS = frozenset({
    "app_key", "appkey", "appKey",
    "app_secret", "appsecret", "appSecret",
    "account_no", "accountNo", "cano", "acct_no",
    "access_token", "accessToken",
    "authorization", "Authorization",
    "tr_key", "trKey", "secret",
})


def sanitize_kis_response(raw: dict | None, settings: Settings) -> dict[str, Any]:
    """Return a redacted copy of a KIS API response dict.

    Removes credential-like keys (case-insensitive name match) and replaces
    occurrences of the configured app_key/app_secret/account_no values with
    "<redacted>". Returns {} for None or non-dict input.
    """
    if not isinstance(raw, dict):
        return {}

    forbidden_values: set[str] = set()
    for v in (settings.kis_app_key, settings.kis_app_secret, settings.kis_account_no):
        if v:
            forbidden_values.add(v)

    def _scrub(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: ("<redacted>" if k.lower() in {s.lower() for s in _SECRET_KEYS} else _scrub(v))
                    for k, v in value.items()}
        if isinstance(value, list):
            return [_scrub(item) for item in value]
        if isinstance(value, str) and value in forbidden_values:
            return "<redacted>"
        return value

    return _scrub(raw)
```

(구현 핵심: 키 이름 case-insensitive 매칭 + 값 매칭. 중첩 dict/list 재귀 처리. None / non-dict → 빈 dict.)

#### 4.4.5 pre-flight 가드 함수

```python
def validate_kis_order_request(settings: Settings, broker_order: BrokerOrder) -> None:
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

#### 4.4.6 KisBroker 메서드 변경/추가

```python
def _idempotency_key_for(self, broker_order: BrokerOrder) -> str:
    # Deterministic — same broker_order (same oms_id) yields same key.
    return f"kis-paper-{broker_order.oms_id}"

def _to_kis_request(self, broker_order: BrokerOrder) -> KisOrderRequest:
    return KisOrderRequest(
        symbol=broker_order.symbol,
        market="US",  # paper-trading scaffold is US-focused; KIS env still "paper"
        side=broker_order.side,
        quantity=broker_order.quantity,
        order_type=broker_order.order_type,
        limit_price=broker_order.limit_price,
        extended_hours=False,
        account_no_masked=self._account.masked_account_no(),
        broker_environment=self._settings.kis_env or "paper",
        idempotency_key=self._idempotency_key_for(broker_order),
    )

def capabilities(self) -> dict[str, bool]:
    # All False in this phase — KIS HTTP not implemented.
    # Future mvps will flip individual flags as endpoints are wired with
    # official documentation reference.
    return {
        "submission": False,
        "cancel": False,
        "replace": False,
        "open_orders": False,
        "fills": False,
        "order_status": False,
    }

def place_order(self, broker_order: BrokerOrder) -> OrderAck:
    validate_kis_order_request(self._settings, broker_order)
    self._to_kis_request(broker_order)  # build internal model; not serialized
    raise NotImplementedError(
        "KIS place_order(): TODO — confirm submission endpoint, TR ID, headers, payload, "
        "and response shape from KIS Open API official paper-trading documentation. "
        "Do not invent endpoints. Do not connect live trading."
    )

def cancel_order(self, broker_order_id: str) -> None:
    if self._settings.trading_mode != TradingMode.PAPER:
        raise KisOrderRejectedError("trading_mode_not_paper")
    if self._settings.live_trading_enabled:
        raise KisOrderRejectedError("live_trading_enabled")
    if self._settings.kis_env != "paper":
        raise KisOrderRejectedError("kis_env_not_paper")
    if self._settings.kill_switch_engaged:
        raise KisOrderRejectedError("kill_switch_engaged")
    raise NotImplementedError(
        "KIS cancel_order(): TODO — confirm cancel endpoint, TR ID, headers, payload, "
        "and response shape from KIS Open API official paper-trading documentation."
    )

def replace_order(self, broker_order_id: str, broker_order: BrokerOrder) -> OrderAck:
    validate_kis_order_request(self._settings, broker_order)
    self._to_kis_request(broker_order)
    raise NotImplementedError(
        "KIS replace_order(): TODO — confirm replace endpoint, TR ID, headers, payload, "
        "and response shape from KIS Open API official paper-trading documentation."
    )

def get_fills(self) -> list[OrderAck]:
    raise NotImplementedError(
        "KIS get_fills(): TODO — confirm fills endpoint, TR ID, payload, and response shape "
        "from KIS Open API official paper-trading documentation. Do not invent endpoints."
    )

def get_order_status(self, broker_order_id: str) -> dict[str, Any]:
    raise NotImplementedError(
        "KIS get_order_status(): TODO — confirm order status endpoint, TR ID, payload, "
        "and response shape from KIS Open API official paper-trading documentation."
    )
```

기존 `get_open_orders`(mvp-007에서 NotImplementedError로 정의됨)는 그대로 둔다.

`healthcheck()`에 한 줄 추가(선택, capabilities 일관성):

```python
"capabilities": self.capabilities(),
```

### 4.5 `app/api/routes.py`

`/paper/status` 핸들러 안에 mvp-008 흡수 + mvp-009 신규 필드:

```python
# mvp-008 absorbed
kis_order_entry_mode = "disabled"
if kis_broker is not None:
    settings_safe = (
        settings.trading_mode.value == "paper"
        and settings.live_trading_enabled is False
        and settings.allow_market_orders is False
        and settings.kis_env == "paper"
        and settings.kill_switch_engaged is False
    )
    kis_order_entry_mode = "not_implemented" if settings_safe else "disabled"

kis_order_entry_ready = (kis_broker is not None) and (kis_order_entry_mode != "disabled")
capabilities = kis_broker.capabilities() if kis_broker else {
    "submission": False, "cancel": False, "replace": False,
    "open_orders": False, "fills": False, "order_status": False,
}
```

응답 dict에 추가(mvp-008 4개 + mvp-009 5개 = 9개):

```python
# mvp-008
"kis_order_entry_ready": kis_order_entry_ready,
"kis_order_entry_mode": kis_order_entry_mode,
"kis_order_methods_fail_closed": True,
"kill_switch_engaged": bool(settings.kill_switch_engaged),
# mvp-009 (capability bools)
"kis_order_submission_available": bool(capabilities.get("submission", False)),
"kis_cancel_available": bool(capabilities.get("cancel", False)),
"kis_replace_available": bool(capabilities.get("replace", False)),
"kis_open_orders_available": bool(capabilities.get("open_orders", False)),
"kis_fills_available": bool(capabilities.get("fills", False)),
```

기존 mvp-005/006-1/007 필드 모두 보존.

### 4.6 `.env.example`

`ALLOW_MARKET_ORDERS=false` 다음에 한 줄(없으면):

```
KILL_SWITCH_ENGAGED=false
```

다른 라인 변경 금지. 실제 secret 금지.

### 4.7 `projects/paper-trading/README.md`

KIS 섹션 안에 mvp-009 단락 추가:

```markdown
### 주문 흐름 안전 가드 (mvp-009)

`KisBroker.place_order` / `cancel_order` / `replace_order` 호출 시 pre-flight 가드(`validate_kis_order_request`)가 다음을 검사합니다:

- `trading_mode == paper`
- `live_trading_enabled is False`
- `allow_market_orders is False`
- `kis_env == "paper"`
- `kill_switch_engaged is False`
- `order_type in (LIMIT, STOP_LIMIT)`
- `quantity > 0`
- `limit_price > 0`

실패 시 `KisOrderRejectedError(reason)`로 즉시 거절. raw 값 미포함.

가드 통과 후에도 KIS HTTP 전송은 본 단계에서 구현되지 않습니다(공식 문서 확인 후 별도 mvp). 모든 KIS 주문 메서드는 최종적으로 `NotImplementedError`로 fail-closed 합니다.

### 내부 변환 모델 (mvp-009)

- `KisOrderRequest`: BrokerOrder → KIS 도메인 변환. 필드에 raw `account_no` 없음(`account_no_masked`만). `idempotency_key`는 `oms_id` 기반 deterministic.
- `KisOrderResponse`: KIS 응답 → 내부 모델. `raw_response_sanitized`는 `sanitize_kis_response()`로 정제된 dict만 보유.
- `sanitize_kis_response(raw, settings)`: key 이름(case-insensitive) 또는 값이 settings의 KIS credential과 일치하면 `"<redacted>"`로 치환. 중첩 dict/list 재귀.

### Kill switch

`KILL_SWITCH_ENGAGED=true`로 설정하면 RiskEngine이 모든 주문을 즉시 거절하고 KIS pre-flight도 동일하게 거절합니다.

### Capabilities

`KisBroker.capabilities()`는 6개 메서드별 가용 bool dict를 반환합니다. 현 단계에서는 모두 False — HTTP가 wired 되면 개별 bool이 True로. `/paper/status`가 다음을 표면화합니다:

- `kis_order_submission_available`, `kis_cancel_available`, `kis_replace_available`
- `kis_open_orders_available`, `kis_fills_available`
- `kis_order_methods_fail_closed: true` (항상)
- `kis_order_entry_mode`: `disabled` / `paper_guarded` / `not_implemented`
```

### 4.8 테스트

#### `tests/test_kis_order_preflight.py` (신규)

8개 reject 사유 + 정상 통과 후 NotImplementedError 케이스. helper에서 fake 값(`kis_account_no="12345678"`, `kis_app_key="fake-key"`, `kis_app_secret="fake-secret"`) 사용.

#### `tests/test_kis_order_request_model.py` (신규)

```python
def test_kis_order_request_contains_market_and_idempotency_key():
    fields_set = {f.name for f in KisOrderRequest.__dataclass_fields__.values()}
    assert "market" in fields_set
    assert "idempotency_key" in fields_set
    assert "account_no" not in fields_set
    assert "account_no_masked" in fields_set


def test_idempotency_key_is_deterministic(settings):
    broker = KisBroker(_configured(settings))
    bo = _broker_order(oms_id="oms-42")
    assert broker._idempotency_key_for(bo) == broker._idempotency_key_for(bo)


def test_idempotency_key_differs_for_different_orders(settings):
    broker = KisBroker(_configured(settings))
    a = _broker_order(oms_id="oms-1")
    b = _broker_order(oms_id="oms-2")
    assert broker._idempotency_key_for(a) != broker._idempotency_key_for(b)


def test_to_kis_request_uses_masked_account(settings):
    broker = KisBroker(_configured(settings))
    req = broker._to_kis_request(_broker_order())
    assert req.account_no_masked.startswith("***")
    assert "12345678" not in repr(req)
    assert req.idempotency_key.startswith("kis-paper-")
```

#### `tests/test_kis_order_response_model.py` (신규)

```python
from app.broker.kis import KisOrderResponse, sanitize_kis_response


def test_sanitize_drops_secret_keys(settings):
    raw = {
        "app_key": "actual-key", "app_secret": "actual-secret",
        "appKey": "actual-key", "appSecret": "actual-secret",
        "access_token": "tok", "Authorization": "Bearer tok",
        "ok": True, "order_id": "abc",
    }
    sanitized = sanitize_kis_response(raw, settings)
    for k in ("app_key", "app_secret", "appKey", "appSecret",
              "access_token", "Authorization"):
        assert sanitized[k] == "<redacted>"
    assert sanitized["ok"] is True
    assert sanitized["order_id"] == "abc"


def test_sanitize_redacts_settings_values(settings):
    s = replace(settings,
                kis_env="paper", kis_account_no="12345678",
                kis_app_key="fake-key", kis_app_secret="fake-secret")
    raw = {"echo": "fake-key", "other": "fake-secret", "acct": "12345678", "ok": True}
    sanitized = sanitize_kis_response(raw, s)
    assert sanitized["echo"] == "<redacted>"
    assert sanitized["other"] == "<redacted>"
    assert sanitized["acct"] == "<redacted>"
    assert sanitized["ok"] is True


def test_sanitize_handles_nested_dicts(settings):
    raw = {"data": {"app_key": "k", "inner": {"app_secret": "s", "ok": 1}}}
    sanitized = sanitize_kis_response(raw, settings)
    assert sanitized["data"]["app_key"] == "<redacted>"
    assert sanitized["data"]["inner"]["app_secret"] == "<redacted>"
    assert sanitized["data"]["inner"]["ok"] == 1


def test_sanitize_handles_none_and_empty(settings):
    assert sanitize_kis_response(None, settings) == {}
    assert sanitize_kis_response({}, settings) == {}


def test_kis_order_response_has_required_fields():
    fields_set = {f.name for f in KisOrderResponse.__dataclass_fields__.values()}
    for required in (
        "internal_order_id", "broker_order_id", "broker", "status",
        "submitted_at", "symbol", "side", "quantity", "limit_price",
        "raw_response_sanitized",
    ):
        assert required in fields_set
```

#### `tests/test_kill_switch.py` (신규)

mvp-008 plan §4.8과 동일한 3 테스트:

```python
def test_risk_engine_rejects_when_kill_switch_engaged(settings)
def test_kis_preflight_rejects_when_kill_switch_engaged(settings)
def test_kill_switch_default_off(settings)
```

#### `tests/test_kis_capabilities.py` (신규)

```python
def test_capabilities_returns_six_bool_keys(settings):
    broker = KisBroker(_configured(settings))
    caps = broker.capabilities()
    for k in ("submission", "cancel", "replace", "open_orders", "fills", "order_status"):
        assert k in caps
        assert isinstance(caps[k], bool)


def test_capabilities_all_false_in_this_phase(settings):
    broker = KisBroker(_configured(settings))
    caps = broker.capabilities()
    assert all(v is False for v in caps.values())
```

#### `tests/test_broker_interface.py` 보정

추가:

```python
def test_kis_exports_order_models_and_helpers():
    from app.broker.kis import (
        KisOrderRequest, KisOrderResponse, KisOrderRejectedError,
        sanitize_kis_response, validate_kis_order_request,
    )
    assert KisOrderRequest is not None
    assert KisOrderResponse is not None
    assert KisOrderRejectedError is not None
    assert callable(sanitize_kis_response)
    assert callable(validate_kis_order_request)


def test_kis_broker_has_get_fills_and_order_status(settings):
    b = KisBroker(_configured(settings))
    with pytest.raises(NotImplementedError, match="TODO"):
        b.get_fills()
    with pytest.raises(NotImplementedError, match="TODO"):
        b.get_order_status("oms-1")


def test_kis_broker_capabilities_method(settings):
    b = KisBroker(_configured(settings))
    assert callable(b.capabilities)
    assert isinstance(b.capabilities(), dict)
```

#### `tests/test_api_paper_status.py` 보정

기존 두 시나리오에 다음 추가:

```python
# mvp-008 fields
assert body["kis_order_methods_fail_closed"] is True
assert body["kis_order_entry_mode"] in ("disabled", "paper_guarded", "not_implemented")
assert isinstance(body["kis_order_entry_ready"], bool)
assert isinstance(body["kill_switch_engaged"], bool)
# mvp-009 capability fields
for cap in (
    "kis_order_submission_available",
    "kis_cancel_available",
    "kis_replace_available",
    "kis_open_orders_available",
    "kis_fills_available",
):
    assert body[cap] is False  # all False in this phase
```

KIS configured 케이스: `kis_order_entry_mode == "not_implemented"`.
KIS 미configured 케이스: `kis_order_entry_mode == "disabled"`.

#### `tests/test_risk_engine.py` 보정

추가:

```python
def test_risk_engine_kill_switch_short_circuit(settings):
    s = replace(settings, kill_switch_engaged=True, symbol_allowlist=("AAPL",))
    decision = RiskEngine(s).evaluate(_intent())
    assert decision.approved is False
    assert decision.reason == "kill_switch_engaged"
```

### 4.9 검증 명령

`projects/paper-trading`에서:

```bash
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

저장소 루트:

```bash
git diff --stat
git status --short
```

종료코드 0. mvp-007 시점 74개 + 신규 약 28–34개 PASS.

### 4.10 `docs/ai/jobs/mvp-009/patch.md`

```markdown
## 1. Files Changed

## 2. Implementation Summary

### 2.1 KIS 주문 메서드 경계
- pre-flight 8개 reject + NotImplementedError 이중 fail-closed.
- get_fills, get_order_status 신규 (NotImplementedError + TODO).

### 2.2 OMS → KIS 연결 준비
- OMS는 PaperBroker 그대로(KIS 미연결).
- KisBroker.capabilities()로 메서드별 가용성 노출.
- RiskEngine kill switch 단축 reject 추가.

### 2.3 KisOrderRequest 모델 (mvp-009)
- 필드: symbol, market, side, quantity, order_type, limit_price, extended_hours, account_no_masked, broker_environment, idempotency_key.
- account_no raw 없음. idempotency_key는 oms_id 기반 deterministic.

### 2.4 KisOrderResponse 모델 + sanitize_kis_response
- raw_response_sanitized는 sanitize_kis_response 결과만 저장.
- 마스킹 패턴: key 이름 case-insensitive 매칭(app_key/app_secret/access_token 등) + 값 매칭(settings.kis_* 일치).
- 중첩 dict/list 재귀 처리.

### 2.5 주문 안전 guard
- validate_kis_order_request 8개 reject 사유 short code, raw 미포함.
- RiskEngine kill_switch_engaged 최상단 reject.

### 2.6 /paper/status 신규 필드 (9개)
mvp-008 흡수 4개:
- kis_order_entry_ready, kis_order_entry_mode, kis_order_methods_fail_closed, kill_switch_engaged
mvp-009 신규 5개:
- kis_order_submission_available, kis_cancel_available, kis_replace_available, kis_open_orders_available, kis_fills_available
모두 현 단계 False (HTTP 미구현).

### 2.7 실행한 테스트
- compileall: PASS
- pytest: 74 + 신규 N PASS, 회귀 없음
- 신규 테스트 파일 5개

### 2.8 공식 문서 필요 (TODO 보존)
- KIS 모의투자 주문 전송 endpoint, TR ID, headers, payload, 응답 shape
- KIS 모의투자 취소/정정 endpoint, payload
- KIS 모의투자 체결/주문 상태/미체결 조회 endpoint, TR ID, payload
- 본 작업에서는 모두 NotImplementedError + 명시적 TODO 메시지로 fail-closed

### 2.9 다음 mvp 후보
- KIS 공식 문서 reference 후 인증 HTTP 호출 실제 구현 (먼저).
- 그 다음 주문 메서드 하나씩 capabilities() 플립.
- 또는 Alpaca Paper HTTP 실제 구현(별도 mvp).

## 3. Safety Confirmation
- 실주문 코드 0건, 모든 KIS 주문 메서드 NotImplementedError.
- KIS endpoint URL/TR ID/payload 하드코딩 0건.
- 외부 HTTP 라이브러리 import 0건.
- raw key/secret/account/access_token 코드/문서/.env.example/응답/log/patch 미노출.
- sanitize_kis_response으로 모든 응답 dict가 자동 마스킹.
- OrderType MARKET 부재 유지.
- live 6단 + KIS 7단째(pre-flight) 차단 모두 작동.
- OMS는 PaperBroker만 사용, KIS 미연결.
- Strategy 패키지가 KIS import 0건.
- /paper/status raw credentials 미노출 (텍스트 검사 테스트).
- .env 미접촉, gitignore 보호 확인.
- commit/push/merge/deploy 자동화 없음.

## 4. Test Results
- compileall ...
- pytest 74 + N passed

## 5. Remaining TODOs
- KIS Open API 공식 문서 확보 후 별도 mvp에서 실제 HTTP 호출 구현.
- 워크트리에 mvp-009 외 dirty(GUI 등) 정리는 별도 작업(mvp-010 후보).
```

## 5. 테스트 기준

1. `.venv/bin/python -m compileall app tests` 종료코드 0.
2. `.venv/bin/python -m pytest -p no:cacheprovider` 종료코드 0. 회귀 없음.
3. `grep -RIn "OrderType\.MARKET" projects/paper-trading/app` 0건.
4. `grep -RIn "https?://" projects/paper-trading/app/broker/kis.py` 0건.
5. `grep -RInE "import requests|import httpx|import aiohttp|import urllib" projects/paper-trading/app/broker/kis.py` 0건.
6. `grep -RIn "TR_ID|tr_id|/uapi/|/oauth2/|/api/v1/" projects/paper-trading/app/broker/kis.py` 0건.
7. `grep -RInE "from app\\.broker\\.kis" projects/paper-trading/app/strategy/` 0건.
8. `grep -RIn "PSNFD\|PKID\|AKIA\|sk-\|ghp_" projects/paper-trading/` 0건 (실 키 prefix 미존재).
9. `KisOrderRequest`에 raw `account_no` 필드 없음(`account_no_masked` 있음).
10. `KisOrderResponse.raw_response_sanitized`가 dict 타입이며 `sanitize_kis_response` 통과 후 저장.
11. `/paper/status`에 9개 신규 필드 모두 존재 + 모두 raw 미노출.
12. `KisBroker.capabilities()` 6개 키, 모두 False.
13. `git diff --stat`에 mvp-009 외 변경 없음.
14. `.env` staged/committed 없음.

## 6. 리뷰 체크리스트

- [ ] mvp-006-1/007 사전 점검 통과.
- [ ] `Settings.kill_switch_engaged` 필드 + env 로딩 (idempotent).
- [ ] `RiskEngine.evaluate()` 최상단 kill switch reject, reason `"kill_switch_engaged"`.
- [ ] `KisOrderRejectedError` 정의, `reason` 속성, raw 값 미포함 메시지.
- [ ] `KisOrderRequest` 필드 10개(market/idempotency_key 포함), raw account 없음.
- [ ] `KisOrderResponse` 필드 10개, `raw_response_sanitized: dict[str, Any]`.
- [ ] `sanitize_kis_response`: case-insensitive 키 매칭 + 값 매칭 + 중첩 재귀 + None/empty 안전.
- [ ] `validate_kis_order_request`: 8개 reject 사유 short code.
- [ ] `KisBroker._idempotency_key_for`: deterministic, oms_id 기반.
- [ ] `KisBroker._to_kis_request`: account_no_masked 사용, raw 미노출.
- [ ] `KisBroker.capabilities()`: 6개 키, 모두 False.
- [ ] `place_order`/`cancel_order`/`replace_order`: pre-flight → NotImplementedError 이중 fail-closed.
- [ ] `get_fills`/`get_order_status`: NotImplementedError + TODO.
- [ ] `/paper/status` 9개 신규 필드 추가, raw credentials 미노출.
- [ ] `.env.example` `KILL_SWITCH_ENGAGED=false` 추가.
- [ ] mvp-007 시점 74개 + mvp-009 신규 약 28–34개 모두 PASS.
- [ ] 외부 HTTP 라이브러리 0건, URL/TR ID 0건.
- [ ] mvp-005~mvp-008 산출물, `app/domain/`, `app/broker/{base,paper,alpaca_paper}.py`, `app/oms/`, `app/runtime/`, `app/strategy/`, `app/main.py`, `app/api/server.py` 미변경.
- [ ] OrderType MARKET 부재 유지.
- [ ] `.env` staged/committed 없음.
- [ ] commit/push/merge/deploy 자동화 없음.
- [ ] `patch.md` 5섹션 + Implementation Summary 9단락 완성.
