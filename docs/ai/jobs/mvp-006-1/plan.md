## 1. 요청 요약

`projects/paper-trading/`에 KIS Open API **모의투자** 연결 준비 작업을 한다.
실제 HTTP 호출/실주문은 본 작업에서 만들지 않는다 — 인터페이스 골격 + 설정 구조 + 안전 가드 + 테스트까지만.

### 컨텍스트 — mvp-006 vs mvp-006-1

mvp-006 (`docs/ai/jobs/mvp-006/`)은 본 세션에서 plan/codex-task를 만들었지만 아직 구현되지 않았다. mvp-006-1은 다음 차이로 사실상 mvp-006을 **대체**한다.

| 항목 | mvp-006 | mvp-006-1 (본 작업) |
| --- | --- | --- |
| env 변수명 | `KIS_PAPER_API_BASE`, `KIS_PAPER_APP_KEY`, `KIS_PAPER_APP_SECRET`, `KIS_PAPER_ACCOUNT` | `KIS_ENV`, `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO` (+ `ALLOW_MARKET_ORDERS`) |
| paper/live 분리 | 없음(paper 전용 변수명) | `KIS_ENV=paper`/`live` 스위치, live는 Phase 1 차단 |
| 어댑터 인터페이스 | `submit/cancel/open_orders/positions`만 | `authenticate/refresh_token/get_account/get_positions/get_quote/get_open_orders/place_order/cancel_order/replace_order/healthcheck` + BrokerAdapter 호환 메서드 |
| URL | 코드에서 env 로드 | 본 단계에서 **base URL 없음**(추후 mvp). KIS 공식 endpoint 추측 금지 |
| 비밀값 repr/log | 별도 규정 없음 | `Settings`/`KisBroker` 모두 `__repr__` 마스킹 |
| `/paper/status` 확장 | `brokers` 메타 | `broker_type`, `broker_environment`, `kis_config_loaded`, `kis_secret_exposed: false` 등 |

**결론**: 본 작업이 끝나면 mvp-006의 plan/codex-task는 더 이상 실행 대상이 아니다. mvp-006 산출물 파일은 그대로 두되 구현하지 않는다.

### 사용자 `.env` 매핑 (사람이 해야 할 일)

현재 `projects/paper-trading/.env`는 이전 세션에서 `KIS_PAPER_*` 이름으로 키가 들어가 있다. mvp-006-1 구현이 끝난 뒤 사람이 다음 매핑으로 `.env`를 갱신해야 한다.

| 기존 (현재 `.env`) | mvp-006-1 표준 |
| --- | --- |
| `KIS_PAPER_API_BASE=...` | 제거(현 단계 미사용) |
| `KIS_PAPER_ACCOUNT=...` | `KIS_ACCOUNT_NO=...` |
| `KIS_PAPER_APP_KEY=...` | `KIS_APP_KEY=...` |
| `KIS_PAPER_APP_SECRET=...` | `KIS_APP_SECRET=...` |
| (없음) | `KIS_ENV=paper` |
| (없음) | `ALLOW_MARKET_ORDERS=false` |

이 매핑은 Codex가 아니라 사람이 한다(secret을 채팅에 다시 노출하지 않기 위해).

### 핵심 절대 조건 (요청 + `prompts/claude.md` + mvp-005 안전 불변식)

- live trading 코드 경로/플래그 활성화 금지. 5단 차단(`Settings` 기본 False / `load_settings` env 차단 / `RiskEngine` reject / `OMS.place` 차단 / `POST /paper/run` 503) 그대로 유지.
- `KIS_ENV=live`는 Phase 1에서 어댑터 init 단계에서 reject(fail closed).
- 시장가 주문 금지. `OrderType`에 MARKET 멤버 추가 금지. `ALLOW_MARKET_ORDERS=true`는 `load_settings()`가 reject(fail closed).
- 모든 주문은 `Strategy → RiskEngine → OMS → BrokerAdapter`. Strategy가 KIS adapter 직접 호출 금지(`app/strategy/`에서 `app.broker.kis` import 금지).
- `KisBroker`의 `place_order`/`cancel_order`/`replace_order`/`submit`/`cancel` 모두 `NotImplementedError`. 실주문 코드 경로 없음.
- KIS endpoint URL/TR ID 코드 하드코딩 금지. 본 단계에서는 URL을 env에도 두지 않는다(공식 문서 확인 전).
- 실제 KIS app key/secret/account를 **어떤 파일에도** 쓰지 않는다(`.env.example`은 placeholder만, 테스트는 가짜 값만).
- `Settings`/`KisBroker`의 `__repr__`가 key/secret/account를 노출하지 않는다(`field(repr=False)` 또는 커스텀 repr).
- `/paper/status`나 어떤 응답에서도 key/secret/account 노출 금지.
- `git commit`/`push`/`merge`/`deploy` 자동화 금지. `.env` Git 추가 금지. 신규 의존성 추가 없음.

검증:

```bash
# projects/paper-trading 에서
python -m compileall app tests
python -m pytest -p no:cacheprovider
# 저장소 루트에서
git diff --stat
git status --short
```

mvp-005 기존 19개 테스트 + 본 작업 신규 테스트 모두 PASS여야 한다.

## 2. 작업 범위

### 포함 (In scope)

`projects/paper-trading/` 아래:

- 신규 `app/broker/kis.py` — `KisBroker` 풀-인터페이스 골격(아래 §4.2). `mode = TradingMode.PAPER`. init은 fail-closed. trading 메서드는 `NotImplementedError`. `healthcheck()`는 정적 dict 반환(네트워크 호출 없음).
- 수정 `app/config.py` — `Settings`에 KIS 4필드 + `allow_market_orders` 추가. 비밀값은 `field(repr=False)`. `load_settings()`에서 env 읽음. `ALLOW_MARKET_ORDERS=true` 시 `ValueError`. KIS 키 누락은 `load_settings` 레벨에서 막지 않음(adapter init에서만 검증).
- 수정 `app/api/server.py` — `KisBroker(settings)`를 `try/except RuntimeError`로 시도, 성공 시 `app.state.configured_brokers`에 `"KisBroker"` 추가. 활성 broker는 `PaperBroker` 그대로.
- 수정 `app/api/routes.py` — `/paper/status` 응답에 다음 필드 추가:
  - `broker_type`: 활성 broker 클래스명
  - `broker_environment`: 항상 `"paper"`
  - `live_trading_enabled`: `settings.live_trading_enabled` 그대로
  - `market_orders_allowed`: `settings.allow_market_orders` 그대로
  - `kis_config_loaded`: KIS 4필드 모두 채워졌는지 bool
  - `kis_secret_exposed`: 항상 `false` (literal)
- 수정 `.env.example` — 다음 placeholder 라인 추가(빈 값 또는 명시적 placeholder). 기존 `KIS_PAPER_*` 라인(mvp-006 잔재로 추가되지 않았다면 무시) 제거.
  ```
  TRADING_MODE=paper
  LIVE_TRADING_ENABLED=false
  ALLOW_MARKET_ORDERS=false
  KIS_ENV=paper
  KIS_ACCOUNT_NO=your_kis_paper_account_no
  KIS_APP_KEY=your_kis_app_key
  KIS_APP_SECRET=your_kis_app_secret
  ```
  (기존 `TRADING_MODE`/`LIVE_TRADING_ENABLED`/Alpaca 줄과 충돌 없게 배치.)
- 수정 `projects/paper-trading/README.md` — KIS 환경변수 표 + KIS adapter의 TODO 경계 한 단락 추가. 실제 endpoint/TR ID는 추측 금지를 명시. 실제 key/secret/account 예시는 적지 않음.
- 신규 `tests/test_kis_config.py` — `.env` 기반 config 로딩, secret repr 마스킹, live/market 기본값.
- 신규 `tests/test_broker_interface.py` — `KisBroker`가 BrokerAdapter Protocol 만족 + 모든 KIS-스타일 메서드 보유 + place_order/cancel_order/replace_order/submit/cancel이 `NotImplementedError`.
- 수정 `tests/test_api_paper_status.py` — 신규 필드 assertion + secret 미노출 검증.
- (선택) 수정 `tests/conftest.py` — KIS env helper fixture(필요 시).
- 수정 `docs/ai/jobs/mvp-006-1/patch.md` — Codex 변경 요약.

### 제외 (Out of scope; 절대 만지지 않음)

- 실제 KIS Open API HTTP 호출 / TR ID / URL.
- 시장 데이터 수집 파이프라인.
- KRX 한국 종목용 새 전략. `app/strategy/` 미수정.
- mvp-005의 OMS/RiskEngine/PaperBroker/AlpacaPaperBroker/Strategy/PaperRunner 로직.
- `OrderType` enum 변경(특히 MARKET 추가 금지).
- `app/broker/base.py` Protocol 변경(기존 OMS 의존성 보호). KIS adapter는 새 메서드를 추가로 노출만 한다.
- `app/broker/paper.py`, `app/broker/alpaca_paper.py` 변경.
- `app/oms/`, `app/risk/`, `app/runtime/`, `app/domain/{enums,orders,market}.py` 변경.
- mvp-001..mvp-005 산출물, `web/`, `prompts/`, `scripts/`, `examples/`, 기존 `docs/` (mvp-006-1 job dir 제외) 변경.
- 새 `docs/runbook.md`, `docs/architecture.md` 생성 (사용자 요청은 "또는 README" — 기존 README 확장으로 충족).
- mvp-006 산출물 변경(deprecated이므로 그대로 둠).
- `.env`, secrets, credentials.
- 인증/결제/DB migration/production infra.
- `git commit`/`push`/`merge`/`deploy` 자동화.
- 임의 shell 실행 기능.
- `pip install` 실행.

### 안전 가드

- `Settings`의 `kis_app_key`, `kis_app_secret`, `kis_account_no` 필드는 `field(repr=False)`로 dataclass repr에서 제외. `kis_env`, `allow_market_orders`는 노출 OK(민감 정보 아님).
- `KisBroker`도 `__repr__`를 직접 정의해 `account=<set>/key=<set>/secret=<set>` 형태로만 노출.
- `app/api/server.py`의 KIS 인스턴스화 `try/except`는 `RuntimeError`만 catch(broad `Exception` 금지).
- `KisBroker` 인스턴스 자체를 `app.state`에 저장하지 않는다(credentials 보관 불필요). `configured_brokers`에 클래스명만.
- `/paper/status` 응답 생성 시 `settings`에서 secret 필드 직접 참조 금지. bool flag만 산출(`kis_config_loaded`).

## 3. 수정해야 할 파일

### 신규

| 파일 | 목적 |
| --- | --- |
| `app/broker/kis.py` | `KisBroker` 풀-인터페이스 골격 |
| `tests/test_kis_config.py` | env 로딩 + secret 마스킹 + 기본값 |
| `tests/test_broker_interface.py` | KIS adapter 인터페이스 + NotImplementedError 검증 |
| `docs/ai/jobs/mvp-006-1/patch.md` | Codex 변경 요약 |

### 수정

| 파일 | 변경 내용 |
| --- | --- |
| `app/config.py` | KIS 4필드 + `allow_market_orders` 추가(비밀값 `repr=False`), `load_settings()` 보강, `ALLOW_MARKET_ORDERS=true` fail closed |
| `app/api/server.py` | `KisBroker(settings)` try/except, `configured_brokers` 등록 |
| `app/api/routes.py` | `/paper/status`에 신규 필드 추가 |
| `.env.example` | KIS_*, ALLOW_MARKET_ORDERS placeholder 추가(실제 값 없음) |
| `projects/paper-trading/README.md` | KIS 환경변수 + adapter TODO 경계 단락 |
| `tests/test_api_paper_status.py` | 신규 필드 + secret 미노출 assertion |
| `tests/conftest.py` (선택) | KIS env helper fixture |

### 절대 미수정

- `app/domain/enums.py`, `app/domain/orders.py`, `app/domain/market.py`
- `app/broker/base.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`
- `app/risk/engine.py`, `app/oms/manager.py`, `app/runtime/paper_runner.py`
- `app/strategy/*` 전부
- `tests/test_{config,models,risk_engine,oms,paper_broker,alpaca_paper_stub,flow,paper_runner,strategy_premarket_gap}.py`
- 루트 `.gitignore`(이미 `.env`/`.env.*`/`!.env.example` 룰이 들어가 있음 — 확인됨)
- 프로젝트 `.gitignore`(이미 `.env`/`__pycache__/` 등 보유 — 확인됨)
- mvp-006 산출물(`docs/ai/jobs/mvp-006/...`)

## 4. Codex 구현 지시문

### 4.1 사전 조건

- 작업 루트: `/root/ai-dev-center/projects/ai-team`. 신규 코드는 `projects/paper-trading/` 안에만.
- mvp-006의 plan/codex-task는 무시한다(deprecated). 본 작업은 mvp-006-1의 단독 구현이다.
- `.env`는 절대 읽지 않는다(테스트는 `monkeypatch`로 env 흉내). 실제 secret을 어떤 파일에도 쓰지 않는다.
- `pip install` 실행 금지. 호스트 의존성 미설치는 `patch.md` Remaining TODOs.
- `git commit`/`push`/`merge`/`deploy` 절대 금지.

### 4.2 `app/broker/kis.py` (신규)

```python
from typing import Any

from app.config import Settings
from app.domain.enums import TradingMode
from app.domain.orders import BrokerOrder, OrderAck


class KisBroker:
    """KIS Open API broker adapter — skeleton only.

    Phase: 모의투자(paper) 환경 연결 준비. 본 단계에서는 인증/시세/주문 모두
    NotImplementedError로 막혀 있다. 실제 KIS Open API HTTP 호출, TR ID, URL은
    공식 문서 확인 후 별도 mvp에서 구현한다. URL을 추측해서 코드에 적지 않는다.
    """

    mode = TradingMode.PAPER

    def __init__(self, settings: Settings) -> None:
        env = settings.kis_env
        if env is None:
            raise RuntimeError("KIS_ENV missing in .env")
        if env != "paper":
            raise RuntimeError(
                f"KIS_ENV={env!r}: only 'paper' allowed in this phase; live env is disabled"
            )
        if not settings.kis_account_no:
            raise RuntimeError("KIS_ACCOUNT_NO missing in .env")
        if not settings.kis_app_key:
            raise RuntimeError("KIS_APP_KEY missing in .env")
        if not settings.kis_app_secret:
            raise RuntimeError("KIS_APP_SECRET missing in .env")
        self._settings = settings

    def __repr__(self) -> str:
        return (
            f"KisBroker(env={self._settings.kis_env!r}, "
            f"account=<set>, app_key=<set>, app_secret=<set>)"
        )

    # --- KIS-style interface (skeleton; no network calls) -----------------

    def authenticate(self) -> None:
        raise NotImplementedError(
            "KIS authenticate(): TODO — confirm endpoint+payload from KIS Open API docs"
        )

    def refresh_token(self) -> None:
        raise NotImplementedError(
            "KIS refresh_token(): TODO — confirm endpoint+payload from KIS Open API docs"
        )

    def get_account(self) -> dict[str, Any]:
        raise NotImplementedError(
            "KIS get_account(): TODO — confirm TR ID + endpoint from KIS Open API docs"
        )

    def get_positions(self) -> dict[str, int]:
        raise NotImplementedError(
            "KIS get_positions(): TODO — confirm TR ID + endpoint from KIS Open API docs"
        )

    def get_quote(self, symbol: str) -> dict[str, Any]:
        raise NotImplementedError(
            "KIS get_quote(): TODO — confirm TR ID + endpoint from KIS Open API docs"
        )

    def get_open_orders(self) -> list[OrderAck]:
        raise NotImplementedError(
            "KIS get_open_orders(): TODO — confirm TR ID + endpoint from KIS Open API docs"
        )

    def place_order(self, broker_order: BrokerOrder) -> OrderAck:
        raise NotImplementedError(
            "KIS place_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard"
        )

    def cancel_order(self, broker_order_id: str) -> None:
        raise NotImplementedError("KIS cancel_order(): TODO")

    def replace_order(self, broker_order_id: str, broker_order: BrokerOrder) -> OrderAck:
        raise NotImplementedError("KIS replace_order(): TODO")

    def healthcheck(self) -> dict[str, Any]:
        return {
            "broker": "KisBroker",
            "environment": self._settings.kis_env,
            "connected": False,
            "reason": "skeleton — KIS Open API HTTP calls not implemented in this phase",
            "config_loaded": True,
        }

    # --- BrokerAdapter Protocol compatibility (OMS uses these names) -----

    def submit(self, broker_order: BrokerOrder) -> OrderAck:
        return self.place_order(broker_order)

    def cancel(self, broker_order_id: str) -> None:
        return self.cancel_order(broker_order_id)

    def open_orders(self) -> list[OrderAck]:
        return self.get_open_orders()

    def positions(self) -> dict[str, int]:
        return self.get_positions()
```

- 추가 import 금지. 특히 `app.oms`, `app.risk`, `app.strategy`, `app.runtime`, `app.api`, 외부 HTTP 라이브러리(`requests`, `httpx` 등) import 금지.

### 4.3 `app/config.py` 변경

기존 `Settings` 클래스에 다음 필드를 추가(필드 순서는 기존 dataclass의 끝쪽, default 있음):

```python
kis_env: str | None = None
kis_account_no: str | None = field(default=None, repr=False)
kis_app_key: str | None = field(default=None, repr=False)
kis_app_secret: str | None = field(default=None, repr=False)
allow_market_orders: bool = False
```

(`field` import 필요: `from dataclasses import dataclass, field`.)

`load_settings()`에서:

```python
allow_mo = _bool_env("ALLOW_MARKET_ORDERS", False)
if allow_mo:
    raise ValueError("ALLOW_MARKET_ORDERS=true is rejected in this phase (market orders disabled)")
```

그리고 새 필드를 채운다:

```python
kis_env=_str_env("KIS_ENV"),  # or None if missing
kis_account_no=_str_env("KIS_ACCOUNT_NO"),
kis_app_key=_str_env("KIS_APP_KEY"),
kis_app_secret=_str_env("KIS_APP_SECRET"),
allow_market_orders=False,
```

`_str_env`가 없으면 다음 helper를 추가:

```python
def _str_env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None
```

`_bool_env`가 없으면:

```python
def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("true", "1", "yes", "on")
```

기존 paper/live 차단 로직(`TRADING_MODE != paper` → ValueError, `LIVE_TRADING_ENABLED` truthy → ValueError)은 변경 없음.

KIS 필드가 누락(None)이어도 `load_settings()`는 에러를 내지 않는다(US-only 사용자를 깨뜨리지 않기 위해).

### 4.4 `app/api/server.py` 변경

기존 `create_app()` 와이어링 뒤(broker/risk/oms/strategy/runner 만든 후)에 추가:

```python
configured_brokers: list[str] = []
try:
    from app.broker.kis import KisBroker
    KisBroker(settings)  # discard instance — we only want to know it's configurable
    configured_brokers.append("KisBroker")
except RuntimeError:
    pass
```

`lifespan` 컨텍스트 안에서 `app.state.configured_brokers = configured_brokers`. KIS 인스턴스 자체는 저장하지 않는다.

- `except RuntimeError`만 catch. `Exception` broad catch 금지.

### 4.5 `app/api/routes.py` 변경

기존 `/paper/status` 응답에 다음 필드를 추가(기존 `mode`/`live_enabled`/`strategies`/`safety` 키는 유지):

```python
settings = request.app.state.settings
active = type(request.app.state.broker).__name__
kis_loaded = all([
    settings.kis_env,
    settings.kis_account_no,
    settings.kis_app_key,
    settings.kis_app_secret,
])
# inside the response dict:
"broker_type": active,
"broker_environment": "paper",
"live_trading_enabled": settings.live_trading_enabled,
"market_orders_allowed": settings.allow_market_orders,
"kis_config_loaded": kis_loaded,
"kis_secret_exposed": False,
"configured_brokers": list(request.app.state.configured_brokers),
```

`/paper/run`는 손대지 않는다. `/healthz`도 손대지 않는다.

### 4.6 `.env.example` 변경

기존 내용을 유지하면서, 만약 mvp-006 잔재로 `KIS_PAPER_*` 라인이 들어가 있다면 그것들을 제거하고, 다음을 깔끔하게 둔다(중복 키 금지):

```
TRADING_MODE=paper
LIVE_TRADING_ENABLED=false
ALLOW_MARKET_ORDERS=false

# KIS Open API (Korea Investment & Securities). Live env is disabled in this phase.
# Real key/secret/account values MUST go in .env (gitignored), never here.
KIS_ENV=paper
KIS_ACCOUNT_NO=your_kis_paper_account_no
KIS_APP_KEY=your_kis_app_key
KIS_APP_SECRET=your_kis_app_secret
```

기존 Alpaca placeholder 줄과 strategy 임계값은 그대로 유지. 실제 KIS 키/계좌번호 절대 금지.

### 4.7 `projects/paper-trading/README.md` 변경

기존 내용 끝쪽에 다음 단락을 추가(또는 적절한 위치에 삽입):

```markdown
## KIS Open API (모의투자) 연결 준비

`app/broker/kis.py`의 `KisBroker`는 KIS Open API 모의투자 연결을 위한 **골격**입니다. 본 단계에서는 실제 HTTP 호출이 구현되지 않았습니다 — 다음 메서드는 모두 `NotImplementedError`입니다.

- `authenticate()`, `refresh_token()`
- `get_account()`, `get_positions()`, `get_quote(symbol)`, `get_open_orders()`
- `place_order()`, `cancel_order()`, `replace_order()`
- BrokerAdapter 호환 메서드(`submit`/`cancel`/`open_orders`/`positions`)는 위 KIS-스타일 메서드로 위임만 합니다.

`healthcheck()`만 정적 dict를 반환(네트워크 호출 없음).

### 환경변수

| 키 | 의미 | 비고 |
| --- | --- | --- |
| `KIS_ENV` | `paper` 만 허용 | live는 본 단계에서 차단 |
| `KIS_ACCOUNT_NO` | 모의투자 계좌번호 | `.env`에서만 |
| `KIS_APP_KEY` | KIS app key | `.env`에서만 |
| `KIS_APP_SECRET` | KIS app secret | `.env`에서만 |
| `ALLOW_MARKET_ORDERS` | 항상 `false` | `true`이면 `load_settings()` 거부 |

`.env`는 Git에 올라가지 않습니다(루트 `.gitignore` + 프로젝트 `.gitignore` 양쪽에서 ignore). `.env.example`은 placeholder만 보관합니다.

### 안전 가드

- live trading 5단 차단(Settings 기본 False / load_settings / RiskEngine / OMS / `/paper/run`) 유지.
- `OrderType`에 MARKET 없음.
- `Strategy` 패키지는 `app.broker.kis`를 import하지 않는다.
- `Settings`/`KisBroker`의 `__repr__`가 key/secret/account를 노출하지 않는다.
- KIS endpoint URL, TR ID는 코드에 하드코딩하지 않는다. 추후 mvp에서 KIS 공식 문서 기반으로 구현한다.
```

기존 README의 다른 절은 손대지 않는다.

### 4.8 테스트

#### `tests/test_kis_config.py` (신규)

```python
from dataclasses import fields
import os
import pytest

from app.config import Settings, load_settings


def test_load_settings_default_paper_and_live_disabled(monkeypatch):
    for k in ("TRADING_MODE","LIVE_TRADING_ENABLED","ALLOW_MARKET_ORDERS",
              "KIS_ENV","KIS_ACCOUNT_NO","KIS_APP_KEY","KIS_APP_SECRET"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("TRADING_MODE", "paper")
    s = load_settings()
    assert s.live_trading_enabled is False
    assert s.allow_market_orders is False
    assert s.kis_env is None
    assert s.kis_account_no is None
    assert s.kis_app_key is None
    assert s.kis_app_secret is None


def test_load_settings_reads_kis_env_vars(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "false")
    monkeypatch.setenv("ALLOW_MARKET_ORDERS", "false")
    monkeypatch.setenv("KIS_ENV", "paper")
    monkeypatch.setenv("KIS_ACCOUNT_NO", "fake-account-1")
    monkeypatch.setenv("KIS_APP_KEY", "fake-app-key")
    monkeypatch.setenv("KIS_APP_SECRET", "fake-app-secret")
    s = load_settings()
    assert s.kis_env == "paper"
    assert s.kis_account_no == "fake-account-1"
    assert s.kis_app_key == "fake-app-key"
    assert s.kis_app_secret == "fake-app-secret"


def test_settings_repr_does_not_expose_secrets(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("KIS_ENV", "paper")
    monkeypatch.setenv("KIS_ACCOUNT_NO", "fake-account-XYZ")
    monkeypatch.setenv("KIS_APP_KEY", "fake-app-key-XYZ")
    monkeypatch.setenv("KIS_APP_SECRET", "fake-app-secret-XYZ")
    s = load_settings()
    text = repr(s)
    assert "fake-app-secret-XYZ" not in text
    assert "fake-app-key-XYZ" not in text
    assert "fake-account-XYZ" not in text


def test_allow_market_orders_true_is_rejected(monkeypatch):
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("ALLOW_MARKET_ORDERS", "true")
    with pytest.raises(ValueError, match="ALLOW_MARKET_ORDERS"):
        load_settings()


def test_env_example_contains_no_real_secrets():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, ".env.example"), "r", encoding="utf-8") as f:
        content = f.read()
    # placeholders only — no base64-like long strings, no obvious key prefixes
    for forbidden in ("PSNFD", "PKID", "AKIA", "sk-", "ghp_"):
        assert forbidden not in content
    # known placeholder pattern is expected
    assert "your_kis_app_key" in content
    assert "your_kis_app_secret" in content
```

#### `tests/test_broker_interface.py` (신규)

```python
from dataclasses import replace
import pytest

from app.broker.kis import KisBroker
from app.domain.enums import TradingMode


REQUIRED_METHODS = (
    # KIS-style
    "authenticate", "refresh_token",
    "get_account", "get_positions", "get_quote", "get_open_orders",
    "place_order", "cancel_order", "replace_order", "healthcheck",
    # BrokerAdapter Protocol compatibility
    "submit", "cancel", "open_orders", "positions",
)


def _configured(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_account_no="fake-acc",
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
    )


def test_kis_broker_has_all_required_methods(settings):
    broker = KisBroker(_configured(settings))
    for name in REQUIRED_METHODS:
        assert callable(getattr(broker, name)), f"missing or non-callable: {name}"


def test_kis_broker_mode_is_paper(settings):
    broker = KisBroker(_configured(settings))
    assert broker.mode == TradingMode.PAPER


def test_kis_broker_missing_env_fails_closed(settings):
    with pytest.raises(RuntimeError, match="KIS_ENV"):
        KisBroker(settings)


def test_kis_broker_live_env_rejected(settings):
    bad = replace(_configured(settings), kis_env="live")
    with pytest.raises(RuntimeError, match="live"):
        KisBroker(bad)


def test_kis_broker_missing_credentials_fails_closed(settings):
    for missing in ("kis_account_no", "kis_app_key", "kis_app_secret"):
        bad = replace(_configured(settings), **{missing: None})
        with pytest.raises(RuntimeError):
            KisBroker(bad)


def test_kis_place_cancel_replace_not_implemented(settings):
    broker = KisBroker(_configured(settings))
    with pytest.raises(NotImplementedError):
        broker.place_order(None)  # type: ignore[arg-type]
    with pytest.raises(NotImplementedError):
        broker.cancel_order("x")
    with pytest.raises(NotImplementedError):
        broker.replace_order("x", None)  # type: ignore[arg-type]


def test_kis_protocol_methods_delegate_to_not_implemented(settings):
    broker = KisBroker(_configured(settings))
    for method in ("submit", "cancel", "open_orders", "positions"):
        with pytest.raises(NotImplementedError):
            getattr(broker, method)("x") if method in ("cancel",) else getattr(broker, method)() if method in ("open_orders","positions") else getattr(broker, method)(None)


def test_kis_healthcheck_returns_disconnected_dict(settings):
    broker = KisBroker(_configured(settings))
    h = broker.healthcheck()
    assert h["broker"] == "KisBroker"
    assert h["environment"] == "paper"
    assert h["connected"] is False
    assert "not implemented" in h["reason"].lower() or "skeleton" in h["reason"].lower()


def test_kis_broker_repr_masks_secrets(settings):
    broker = KisBroker(_configured(settings))
    text = repr(broker)
    assert "fake-key" not in text
    assert "fake-secret" not in text
    assert "fake-acc" not in text


def test_strategy_package_does_not_import_kis():
    import pathlib, re
    root = pathlib.Path(__file__).parent.parent / "app" / "strategy"
    pattern = re.compile(r"\bapp\.broker\.kis\b")
    for p in root.rglob("*.py"):
        text = p.read_text(encoding="utf-8")
        assert not pattern.search(text), f"{p} imports app.broker.kis"
```

#### `tests/test_api_paper_status.py` 보정

기존 assertion은 유지. 다음을 추가:

```python
assert body["broker_type"] == "PaperBroker"
assert body["broker_environment"] == "paper"
assert body["live_trading_enabled"] is False
assert body["market_orders_allowed"] is False
assert isinstance(body["kis_config_loaded"], bool)
assert body["kis_secret_exposed"] is False

body_text = response.text
for needle in ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_NO"):
    assert needle not in body_text
```

기존 `safety`/`strategies` assertion은 그대로.

#### `tests/conftest.py` (선택)

기존 `settings` fixture를 그대로 사용. KIS 필드는 기본 None이므로 추가 fixture 없이도 OK.

### 4.9 검증 명령

`projects/paper-trading`에서:

```bash
python -m compileall app tests
python -m pytest -p no:cacheprovider
```

저장소 루트에서:

```bash
git diff --stat
git status --short
```

`compileall`과 `pytest`는 종료코드 0. mvp-005 기존 19개 + 신규 (대략 17개) 모두 PASS여야 한다.

호스트에 `pytest` 등이 미설치라 실패한 경우 작업을 멈추고 `patch.md` Remaining TODOs에 사람이 실행할 명령(`python3 -m pip install fastapi 'uvicorn[standard]' 'pydantic>=2' python-dotenv pytest httpx`)을 적은 뒤 종료한다.

### 4.10 `docs/ai/jobs/mvp-006-1/patch.md`

요청의 "완료 후 patch.md에 정리할 내용" 8개 항목과 1:1 대응하도록 다음 구조로 작성한다.

```markdown
## 1. Files Changed
(신규/수정 파일 전체)

## 2. Implementation Summary

### 2.1 변경 파일
(목록 + 한 줄 설명)

### 2.2 KIS 설정 구조
- Settings에 kis_env / kis_account_no / kis_app_key / kis_app_secret / allow_market_orders 필드 추가
- 비밀 3필드는 field(repr=False)로 dataclass repr에서 제외
- load_settings()가 .env(또는 환경변수)에서 읽고, ALLOW_MARKET_ORDERS=true이면 ValueError

### 2.3 .env와 .env.example 사용 방식
- 실제 키/계좌번호는 .env에만 존재(.env는 루트 및 프로젝트 .gitignore로 무시).
- .env.example는 placeholder만(`your_kis_app_key` 등).
- 사람은 .env의 기존 KIS_PAPER_* 키를 KIS_ENV / KIS_ACCOUNT_NO / KIS_APP_KEY / KIS_APP_SECRET 로 직접 변경해야 함(SSH 셸에서, 채팅 외부).

### 2.4 실제 key/secret/account 노출 여부
- Settings.__repr__: 비밀 필드 제외(field repr=False).
- KisBroker.__repr__: account/key/secret 모두 <set>로 마스킹.
- /paper/status 응답: kis_config_loaded(bool)와 kis_secret_exposed(false) 플래그만, 값은 미노출.
- 테스트가 응답 본문에 키 이름 문자열 미노출 확인.
- 본 patch.md / review.md / 로그에도 실제 값 미인용.

### 2.5 KIS adapter의 TODO 경계
- authenticate, refresh_token, get_account, get_positions, get_quote, get_open_orders → NotImplementedError(TODO: KIS 공식 문서로 endpoint+TR ID+payload 확인).
- place_order, cancel_order, replace_order → NotImplementedError(실주문 차단; OMS-only + RiskEngine을 거치는 흐름은 별도 mvp에서 구현).
- healthcheck()만 정적 dict 반환(네트워크 호출 없음).
- BrokerAdapter Protocol 호환 메서드(submit/cancel/open_orders/positions)는 위 KIS-스타일로 위임.

### 2.6 live trading 차단 유지
- Settings.live_trading_enabled 기본 False.
- load_settings()가 LIVE_TRADING_ENABLED=true에서 ValueError(기존).
- RiskEngine, OMS.place, /paper/run 503 — 모두 mvp-005에서 그대로 유지.
- KisBroker.__init__가 KIS_ENV != "paper"인 경우 RuntimeError(추가 차단 6단째).

### 2.7 실행한 테스트
- python -m compileall app tests: <결과>
- python -m pytest -p no:cacheprovider: <결과>
- mvp-005 기존 19개 회귀 PASS / 신규 약 17개 PASS / (미설치 시 사유 명시)

### 2.8 다음 mvp 후보
- KIS Open API base URL 환경변수 추가 + 어댑터에서 URL 검증.
- KIS Open API 실제 HTTP 호출 구현(인증 → 토큰 캐싱 → get_account/get_quote → place_order 순서로 단계 분리).
- KIS_ENV=live 활성화 절차(arming/preflight/guard, 별도 명시적 사용자 승인).
- KRX 한국 시장 전략(premarket gap의 한국형 변형 등).
- 또는 Alpaca Paper HTTP 호출 실제 구현.

## 3. Safety Confirmation
- live trading 5단(+KIS 6단째) 차단 유지.
- 실계좌(KIS 실전, Alpaca Live 등) 어댑터 없음.
- 시장가 주문 차단 유지 (OrderType MARKET 없음, ALLOW_MARKET_ORDERS=true fail closed).
- mvp-005의 Strategy/OMS/Risk/Broker 격리 불변식 그대로.
- KIS endpoint URL, TR ID 코드 하드코딩 없음. .env에도 base URL 두지 않음.
- 실제 KIS key/secret/account 코드/문서/.env.example/응답/log/patch/review 어디에도 없음.
- /paper/status 응답에서 secret 미노출.
- .env staged/committed 없음. .gitignore 보호 확인됨.
- commit/push/merge/deploy 자동화 없음.

## 4. Test Results
(2.7과 동일)

## 5. Remaining TODOs
- 사용자가 .env의 KIS_PAPER_* → KIS_* 키 이름 매핑을 직접 수행.
- 의존성 미설치 시 pip install 명령(필요 시).
```

## 5. 테스트 기준

1. `python -m compileall app tests` 종료코드 0.
2. `python -m pytest -p no:cacheprovider` 종료코드 0(또는 미설치 사유 Remaining TODOs).
3. mvp-005 기존 19개 테스트 그대로 PASS(회귀 없음).
4. `tests/test_kis_config.py`의 5개, `tests/test_broker_interface.py`의 10개 안팎, `tests/test_api_paper_status.py` 보정분 모두 PASS.
5. `grep -RIn "MARKET" projects/paper-trading/app` 결과 변경 없음(`OrderType.MARKET` 없음).
6. `grep -RIn "from app\.(oms|risk|strategy)" projects/paper-trading/app/broker/kis.py` 결과 0건.
7. `grep -RIn "from app\.broker\.kis\b" projects/paper-trading/app/strategy` 결과 0건.
8. `grep -RIn "https://" projects/paper-trading/app/broker/kis.py` 결과 0건(KIS URL 코드 하드코딩 없음).
9. `projects/paper-trading/.env.example`에 KIS 실제 키/계좌 0건(placeholder만).
10. `git status --short`에 `.env` 미등장.
11. `git diff --stat`에 mvp-006-1 외 변경 없음.

## 6. 리뷰 체크리스트

- [ ] `app/broker/kis.py` 신규. `mode == TradingMode.PAPER`. fail-closed init(KIS_ENV/account/app_key/app_secret 검증).
- [ ] `place_order`/`cancel_order`/`replace_order`/`submit`/`cancel` 모두 `NotImplementedError`.
- [ ] `authenticate`/`refresh_token`/`get_account`/`get_positions`/`get_quote`/`get_open_orders` 모두 `NotImplementedError` (TODO 명시).
- [ ] `healthcheck()`만 정적 dict 반환. 네트워크 호출 없음.
- [ ] `Settings`에 KIS 4필드 + `allow_market_orders` 추가. 비밀 3필드 `repr=False`.
- [ ] `Settings.__repr__`에 실제 key/secret/account 값 미노출.
- [ ] `KisBroker.__repr__`에 실제 key/secret/account 값 미노출(`<set>`).
- [ ] `load_settings()`가 `ALLOW_MARKET_ORDERS=true`에서 `ValueError`.
- [ ] `load_settings()`가 KIS 키 누락에서 에러 내지 않음(Alpaca-only 시나리오 보호).
- [ ] `app/api/server.py`가 `KisBroker(settings)`를 `try/except RuntimeError`로 시도, 성공 시 `configured_brokers`에 등록. KIS 인스턴스 자체 미저장.
- [ ] `/paper/status` 응답에 `broker_type`, `broker_environment`, `live_trading_enabled`, `market_orders_allowed`, `kis_config_loaded`, `kis_secret_exposed`, `configured_brokers` 필드 추가. credentials 미노출.
- [ ] `.env.example`에 KIS_ENV/KIS_ACCOUNT_NO/KIS_APP_KEY/KIS_APP_SECRET/ALLOW_MARKET_ORDERS placeholder. 실제 키 없음.
- [ ] `projects/paper-trading/README.md`에 KIS 환경변수 + TODO 경계 단락.
- [ ] `tests/test_kis_config.py`(5) + `tests/test_broker_interface.py`(10) + `tests/test_api_paper_status.py` 보정 모두 PASS.
- [ ] mvp-005 19개 회귀 PASS.
- [ ] `app/broker/base.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/oms/`, `app/risk/`, `app/strategy/`, `app/runtime/`, `app/domain/{enums,orders,market}.py` 미변경.
- [ ] mvp-001..mvp-005 산출물, mvp-006 산출물, `web/`, `prompts/`, `scripts/`, 기존 `docs/` 미변경.
- [ ] `OrderType`에 MARKET 멤버 미추가.
- [ ] Strategy 패키지가 KIS adapter import 0건(grep).
- [ ] KIS URL/TR ID 코드 하드코딩 0건.
- [ ] `.env` staged/committed 없음.
- [ ] commit/push/merge/deploy 자동화 없음.
- [ ] `patch.md` 5섹션 + Implementation Summary 8단락 모두 채움.
