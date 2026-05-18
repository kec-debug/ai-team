# Codex Task — mvp-006-1: KIS Open API 모의투자 연결 준비

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-006-1/plan.md` and `docs/ai/jobs/mvp-006-1/request.ko.md` first.
>
> **중요**: mvp-006 (`docs/ai/jobs/mvp-006/plan.md`)은 deprecated. 본 작업은 mvp-006-1만 구현한다.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-006-1`
- 대상 디렉터리: `projects/paper-trading/` (mvp-005에서 생성, 기존 구조 유지)
- 본 작업은 KIS Open API 모의투자 **연결 준비**(인터페이스 골격 + 설정 구조 + 안전 가드 + 테스트)까지만. 실제 HTTP 호출, 실주문, KIS endpoint URL/TR ID는 본 작업에 포함하지 않는다.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, API key, token, account number 류 일체 변경/생성/읽기 금지(테스트는 `monkeypatch`로 흉내).
- 실제 KIS app key/secret/account/URL을 **어떤 파일에도** 쓰지 않는다. `.env.example`은 `your_kis_*` 같은 placeholder만.
- KIS endpoint URL, TR ID, payload 형식을 코드/문서에 하드코딩 금지. 공식 KIS Open API 문서 확인 없이 추측 금지.
- 실주문 코드 신설 금지. `place_order`/`cancel_order`/`replace_order`/`submit`/`cancel` 모두 `NotImplementedError`.
- live trading 활성화 금지. `Settings.live_trading_enabled` 기본 False, `load_settings()` env 차단 유지.
- `KIS_ENV=live`는 `KisBroker.__init__`에서 `RuntimeError`(fail closed).
- 시장가 주문 금지. `OrderType`에 MARKET 멤버 추가 금지. `ALLOW_MARKET_ORDERS=true`는 `load_settings()`가 `ValueError`.
- RiskEngine/OMS 우회 코드 경로 신설 금지.
- Strategy 패키지가 `app.broker.kis`를 import하면 안 됨.
- OMS의 `_risk`/`_broker` private 유지. getter 추가 금지.
- 외부 HTTP 라이브러리(`requests`, `httpx`, `aiohttp` 등) `KisBroker`에 import 금지.
- `KisBroker`에서 실제 네트워크 호출/소켓 연결 시도 금지.
- `/paper/status`나 어떤 응답에서도 KIS 실제 key/secret/account 값 노출 금지.
- 임의 shell 명령 입력 UI/API 신설 금지.
- 본 작업 범위 외 파일 변경 금지. 특히 mvp-001..mvp-005 산출물, mvp-006 산출물, `web/`, `prompts/`, `scripts/`, `examples/`, 기존 `docs/`(mvp-006-1 job dir 제외) 미변경.
- `pip install` 실행 금지. 의존성 미설치는 `patch.md` Remaining TODOs.

## 수정 허용 위치

### 신규 파일

- `projects/paper-trading/app/broker/kis.py`
- `projects/paper-trading/tests/test_kis_config.py`
- `projects/paper-trading/tests/test_broker_interface.py`
- `docs/ai/jobs/mvp-006-1/patch.md`

### 수정 가능 파일

- `projects/paper-trading/app/config.py` (KIS 4필드 + `allow_market_orders` + repr 마스킹 + `load_settings` 보강)
- `projects/paper-trading/app/api/server.py` (`KisBroker(settings)` try/except + `configured_brokers`)
- `projects/paper-trading/app/api/routes.py` (`/paper/status` 신규 필드)
- `projects/paper-trading/.env.example` (KIS_*, ALLOW_MARKET_ORDERS placeholder)
- `projects/paper-trading/README.md` (KIS 환경변수 + TODO 경계 단락)
- `projects/paper-trading/tests/test_api_paper_status.py` (신규 필드 + credentials 미노출 assertion)
- `projects/paper-trading/tests/conftest.py` (필요 시 helper fixture)

### 절대 수정 금지 파일

- `projects/paper-trading/app/domain/enums.py` (특히 `OrderType`에 MARKET 추가 금지)
- `projects/paper-trading/app/domain/orders.py`
- `projects/paper-trading/app/domain/market.py`
- `projects/paper-trading/app/broker/base.py`
- `projects/paper-trading/app/broker/paper.py`
- `projects/paper-trading/app/broker/alpaca_paper.py`
- `projects/paper-trading/app/risk/engine.py`
- `projects/paper-trading/app/oms/manager.py`
- `projects/paper-trading/app/strategy/*` 전부
- `projects/paper-trading/app/runtime/paper_runner.py`
- `projects/paper-trading/app/main.py`
- 기존 테스트 파일들 — `test_config.py`, `test_models.py`, `test_risk_engine.py`, `test_oms.py`, `test_paper_broker.py`, `test_alpaca_paper_stub.py`, `test_flow.py`, `test_paper_runner.py`, `test_strategy_premarket_gap.py`
- 루트 `.gitignore`(이미 보호 룰 있음)
- 프로젝트 `.gitignore`(이미 `.env` ignore 보유)
- mvp-006 산출물(`docs/ai/jobs/mvp-006/...`) — deprecated, 그대로 둠

## 구현 작업

### 1) `app/broker/kis.py` (신규)

`plan.md` §4.2의 코드를 그대로 따른다. 핵심:

- `class KisBroker:` `mode = TradingMode.PAPER`.
- `__init__(self, settings)`:
  - `settings.kis_env is None` → `RuntimeError("KIS_ENV missing in .env")`
  - `settings.kis_env != "paper"` → `RuntimeError(... only 'paper' allowed in this phase; live env is disabled)`
  - `kis_account_no` / `kis_app_key` / `kis_app_secret` 누락 시 각각 `RuntimeError`
  - `self._settings = settings` (private 보관)
- `__repr__`: `KisBroker(env={self._settings.kis_env!r}, account=<set>, app_key=<set>, app_secret=<set>)`
- `authenticate`, `refresh_token`, `get_account`, `get_positions`, `get_quote(symbol)`, `get_open_orders`, `place_order(broker_order)`, `cancel_order(broker_order_id)`, `replace_order(broker_order_id, broker_order)` — 모두 `NotImplementedError`(TODO 메시지 포함).
- `healthcheck() -> dict`: 다음 정적 dict 반환(네트워크 호출 없음):
  ```python
  {
      "broker": "KisBroker",
      "environment": self._settings.kis_env,
      "connected": False,
      "reason": "skeleton — KIS Open API HTTP calls not implemented in this phase",
      "config_loaded": True,
  }
  ```
- BrokerAdapter 호환: `submit`/`cancel`/`open_orders`/`positions`는 각각 `place_order`/`cancel_order`/`get_open_orders`/`get_positions`로 위임.

import는 다음만 허용:
- `from typing import Any`
- `from app.config import Settings`
- `from app.domain.enums import TradingMode`
- `from app.domain.orders import BrokerOrder, OrderAck`

다른 import(`app.oms`, `app.risk`, `app.strategy`, `app.runtime`, `app.api`, `requests`, `httpx`, `aiohttp` 등) 금지.

### 2) `app/config.py` 변경

`Settings` 클래스에 필드 추가(필드 순서는 기존 dataclass의 끝쪽, default 있음). `field(repr=False)`를 쓰려면 import에 `from dataclasses import dataclass, field` 보장.

```python
kis_env: str | None = None
kis_account_no: str | None = field(default=None, repr=False)
kis_app_key: str | None = field(default=None, repr=False)
kis_app_secret: str | None = field(default=None, repr=False)
allow_market_orders: bool = False
```

`load_settings()`에:

1. `ALLOW_MARKET_ORDERS` 검증 — `_bool_env("ALLOW_MARKET_ORDERS", False)` 결과가 True이면 `ValueError("ALLOW_MARKET_ORDERS=true is rejected in this phase (market orders disabled)")`.
2. 새 필드 채움:
   ```python
   kis_env=_str_env("KIS_ENV"),
   kis_account_no=_str_env("KIS_ACCOUNT_NO"),
   kis_app_key=_str_env("KIS_APP_KEY"),
   kis_app_secret=_str_env("KIS_APP_SECRET"),
   allow_market_orders=False,  # gated above
   ```

`_str_env`가 없으면 다음 helper를 추가:

```python
def _str_env(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None
```

`_bool_env`가 없으면 (대소문자 무시, `true`/`1`/`yes`/`on`):

```python
def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in ("true", "1", "yes", "on")
```

기존 paper/live 차단 로직(`TRADING_MODE != paper` → ValueError, `LIVE_TRADING_ENABLED` truthy → ValueError)은 변경 없음.

KIS 필드 누락(None)은 `load_settings()` 레벨에서 에러를 내지 않는다.

### 3) `app/api/server.py` 변경

기존 `create_app()` 와이어링 뒤에 추가:

```python
configured_brokers: list[str] = []
try:
    from app.broker.kis import KisBroker
    KisBroker(settings)  # discard instance — credentials must not be retained
    configured_brokers.append("KisBroker")
except RuntimeError:
    pass
```

`lifespan` 컨텍스트 안에서 `app.state.configured_brokers = configured_brokers`. KIS 인스턴스 자체는 저장하지 않는다.

`except RuntimeError`만. broad `Exception` catch 금지.

### 4) `app/api/routes.py` 변경

`/paper/status` 응답 dict에 다음 키를 추가(기존 `mode`/`live_enabled`/`strategies`/`safety` 유지):

```python
settings = request.app.state.settings
active = type(request.app.state.broker).__name__
kis_loaded = bool(
    settings.kis_env
    and settings.kis_account_no
    and settings.kis_app_key
    and settings.kis_app_secret
)
# in response dict:
"broker_type": active,
"broker_environment": "paper",
"live_trading_enabled": settings.live_trading_enabled,
"market_orders_allowed": settings.allow_market_orders,
"kis_config_loaded": kis_loaded,
"kis_secret_exposed": False,
"configured_brokers": list(request.app.state.configured_brokers),
```

`/paper/run`, `/healthz`는 손대지 않는다. 실제 key/secret/account 값은 응답에 절대 포함시키지 않는다.

### 5) `.env.example` 변경

기존 파일을 열어:
- `KIS_PAPER_*` 라인이 있다면 모두 제거(mvp-006 잔재).
- 다음 라인을 깔끔하게 추가/유지(중복 키 금지):

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

### 6) `projects/paper-trading/README.md` 변경

기존 내용은 보존. 끝쪽(또는 적절한 위치)에 `plan.md` §4.7에 명시된 `## KIS Open API (모의투자) 연결 준비` 섹션을 추가.

### 7) 테스트

#### `tests/test_kis_config.py` (신규)

`plan.md` §4.8의 5 테스트를 그대로 구현. 핵심:
- 기본값(paper, live=false, allow_market=false, KIS 필드 None).
- env 로딩(fake 값으로 KIS 4필드 채움).
- `repr(settings)`에 fake 값 미노출.
- `ALLOW_MARKET_ORDERS=true` → `ValueError`.
- `.env.example`에 알려진 실 키 prefix(`PSNFD`, `PKID`, `AKIA`, `sk-`, `ghp_`) 미존재 + placeholder `your_kis_app_key` / `your_kis_app_secret` 존재.

#### `tests/test_broker_interface.py` (신규)

`plan.md` §4.8의 10여 개 테스트:
- `KisBroker`가 `REQUIRED_METHODS` 모두 보유(callable).
- `mode == TradingMode.PAPER`.
- env/credentials 누락 → `RuntimeError`.
- `kis_env="live"` → `RuntimeError`.
- `place_order`/`cancel_order`/`replace_order` → `NotImplementedError`.
- BrokerAdapter Protocol 메서드(`submit`/`cancel`/`open_orders`/`positions`) → `NotImplementedError` (위임).
- `healthcheck()` 반환 dict 검증(connected=False).
- `repr(broker)`에 fake 값 미노출.
- `app/strategy/` 안의 파일이 `app.broker.kis`를 import하지 않음(grep 기반 정적 검사).

#### `tests/test_api_paper_status.py` 보정

기존 assertion 유지. 다음을 추가:

```python
assert body["broker_type"] == "PaperBroker"
assert body["broker_environment"] == "paper"
assert body["live_trading_enabled"] is False
assert body["market_orders_allowed"] is False
assert isinstance(body["kis_config_loaded"], bool)
assert body["kis_secret_exposed"] is False
assert isinstance(body["configured_brokers"], list)

body_text = response.text
for needle in ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_NO"):
    assert needle not in body_text
```

기존 `safety`/`strategies` assertion은 그대로 유지.

### 8) 검증

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

`compileall`과 `pytest`는 종료코드 0. mvp-005 기존 19개 + 신규 약 17개 모두 PASS여야 한다.

호스트에 `pytest` 등이 미설치라 실패하면 작업을 멈추고 `patch.md` Remaining TODOs에 사람이 실행할 명령(`python3 -m pip install fastapi 'uvicorn[standard]' 'pydantic>=2' python-dotenv pytest httpx`)을 적은 뒤 종료한다. `pip install`을 Codex가 직접 실행하지 않는다.

### 9) `docs/ai/jobs/mvp-006-1/patch.md`

`plan.md` §4.10의 템플릿(섹션 1–5 + Implementation Summary 8단락)을 그대로 채운다.
patch.md에 실제 KIS key/secret/account 값을 절대 인용하지 않는다.

## 완료 정의 (Done)

- `app/broker/kis.py`, `tests/test_kis_config.py`, `tests/test_broker_interface.py`, `docs/ai/jobs/mvp-006-1/patch.md` 신규 생성.
- `app/config.py`, `app/api/server.py`, `app/api/routes.py`, `.env.example`, `projects/paper-trading/README.md`, `tests/test_api_paper_status.py` 수정.
- 그 외 `projects/paper-trading/` 파일 모두 미변경. mvp-001..mvp-005, mvp-006 산출물 미변경. `web/`/`prompts/`/`scripts/`/기존 `docs/` 미변경.
- `OrderType`에 MARKET 멤버 없음.
- Strategy 패키지가 `app.broker.kis` import 0건(grep).
- `KisBroker`가 fail-closed로 동작하며 네트워크 호출/소켓 시도 없음.
- `Settings.__repr__`/`KisBroker.__repr__`에 실제 key/secret/account 값 미노출.
- `/paper/status` 응답에 신규 필드 추가, credentials 미노출.
- `ALLOW_MARKET_ORDERS=true` → `ValueError`.
- `KIS_ENV=live` → `RuntimeError`(KisBroker init).
- `python -m compileall` PASS, `pytest`는 PASS 또는 미설치 Remaining TODOs.
- `git diff --stat`에 mvp-006-1 외 변경 없음.
- `.env` staged/committed 없음.
- `patch.md` 5섹션 + Implementation Summary 8단락 작성.
- commit/push/merge/deploy 자동화 없음.
