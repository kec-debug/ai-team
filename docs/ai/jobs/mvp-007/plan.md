## 1. 요청 요약

`projects/paper-trading/`의 KIS Open API 모의투자 연결을 **인증/계좌/시세 클라이언트 구조 분리 + 상태 머신 + 상태 응답 확장**까지 진행한다. 실제 HTTP 호출은 본 작업에서 만들지 않는다 — 실주문은 mvp-008, 그 외 실제 호출도 KIS 공식 문서 확인 후 별도 mvp에서 구현.

### 의존성 — mvp-006-1이 먼저 구현되어 있어야 함

mvp-006-1 (`docs/ai/jobs/mvp-006-1/plan.md`)에서 다음이 만들어진다고 가정한다.

- `projects/paper-trading/app/broker/kis.py`의 `KisBroker` 골격 + `__repr__` 마스킹
- `Settings`에 `kis_env`/`kis_account_no`/`kis_app_key`/`kis_app_secret`/`allow_market_orders` 필드 + `field(repr=False)` 보호
- `load_settings()`의 `ALLOW_MARKET_ORDERS=true` reject + KIS env 로딩
- `/paper/status`에 `broker_type`/`broker_environment`/`live_trading_enabled`/`market_orders_allowed`/`kis_config_loaded`/`kis_secret_exposed`/`configured_brokers` 필드
- `tests/test_kis_config.py`, `tests/test_broker_interface.py`, `tests/test_api_paper_status.py` 확장
- `.env.example`에 `KIS_ENV`/`KIS_ACCOUNT_NO`/`KIS_APP_KEY`/`KIS_APP_SECRET`/`ALLOW_MARKET_ORDERS` placeholder

**Codex는 mvp-007 작업 시작 시 위 파일/필드 존재를 확인한다. 누락이면 mvp-007을 멈추고 `patch.md` Remaining TODOs에 "mvp-006-1을 먼저 구현해야 함"으로 기록한다.**

### KIS 공식 문서 가드 (매우 중요)

요청은 "KIS Open API endpoint, TR ID, payload는 공식 문서 기준으로만 구현"을 요구한다. 실무적 해석:

- Codex는 웹 접근이 없고, 본 저장소에 KIS 공식 문서 사본도 없다.
- Codex가 학습 데이터에서 "기억"하는 KIS endpoint/TR ID는 (a) outdated 가능성, (b) hallucination 가능성, (c) 사용자의 "공식 문서 확인" 기준에 미치지 못함.
- 따라서 **모든 실제 HTTP 호출 코드는 본 작업에서 `NotImplementedError` + 명시적 TODO 주석으로 남긴다.**
- 실제 일은 (1) 서브 클라이언트 분리, (2) 토큰 라이프사이클 상태 머신, (3) 계좌번호 마스킹, (4) `healthcheck` 강화, (5) `last_broker_error` 추적, (6) 상태 응답 확장, (7) 테스트 — 모두 HTTP 없이 구현·검증 가능.

### 핵심 절대 조건

mvp-005 + mvp-006-1 안전 불변식 전부 유지:

- live trading 5단(+KIS 6단째) 차단 그대로.
- `OrderType`에 MARKET 멤버 추가 금지. `ALLOW_MARKET_ORDERS=true` fail closed 유지.
- 모든 주문은 `Strategy → RiskEngine → OMS → BrokerAdapter`. Strategy가 KIS adapter 직접 호출 금지(`app/strategy/`에서 `app.broker.kis*` import 금지, grep 정적 검증).
- OMS의 `_risk`/`_broker` private 유지.
- 실주문 코드 신설 금지. `place_order`/`cancel_order`/`replace_order`/`submit`/`cancel` 모두 `NotImplementedError`.
- KIS endpoint URL/TR ID/payload 코드 하드코딩 금지(공식 문서 확인 전).
- 실제 KIS key/secret/account를 어떤 파일에도 쓰지 않는다(`.env.example`은 placeholder).
- `Settings`/`KisBroker`/모든 client 클래스의 `__repr__`가 key/secret/account 미노출.
- `/paper/status`나 어떤 응답에서도 key/secret/account/access_token 원문 미노출. 계좌번호는 마스킹.
- `git commit`/`push`/`merge`/`deploy` 자동화 금지. `.env` Git 추가 금지.
- `pip install` 실행 금지(미설치는 Remaining TODOs).

### 상태 응답 필드 이름 정리

mvp-006-1에서 `kis_secret_exposed`로 명명했던 필드를 mvp-007 요청 spec(`secret_exposed`)에 맞춰 **`secret_exposed`로 통일**한다. mvp-006-1 산출물에 `kis_secret_exposed`가 들어 있다면 본 작업에서 `secret_exposed`로 일관 정리하고 그 테스트도 갱신한다.

### 검증

```bash
# projects/paper-trading 에서
python -m compileall app tests
python -m pytest -p no:cacheprovider
# 저장소 루트에서
git diff --stat
git status --short
```

mvp-005 + mvp-006-1 + mvp-007 모든 테스트가 PASS여야 한다.

## 2. 작업 범위

### 포함 (In scope)

`projects/paper-trading/` 아래:

- **신규 클라이언트 클래스**(파일 분리 방식): `app/broker/kis.py`를 단일 모듈로 유지하되, 내부에 다음 클래스를 분리하여 정의:
  - `KisAuthClient` — 인증 토큰 라이프사이클 상태 머신
  - `KisAccountClient` — 계좌/포지션/현금 조회 + 계좌번호 마스킹
  - `KisMarketDataClient` — 시세 조회 + 시장 데이터 헬스체크
  - `KisBroker` — BrokerAdapter Protocol 구현체. 위 3개 client를 들고 메서드를 위임.
  - `KisError`, `KisAuthError`, `KisConfigError`, `KisDataUnavailableError` — 예외 계층
- 수정 `app/config.py` — `last_broker_error` 추적용 필드는 추가하지 않음(런타임 상태이므로 `Settings`에 두지 않고 `KisBroker` 인스턴스 또는 `app.state`에 둔다). 다른 KIS 설정 변경 없음.
- 수정 `app/api/server.py` — `KisBroker(settings)` 인스턴스가 성공하면 `app.state.kis_broker = KisBroker(settings)`로 보관(메서드는 모두 NotImplementedError지만 healthcheck/`is_authenticated` 같은 read-only 메서드는 호출 가능). `try/except RuntimeError`로 가드. credentials 그 자체를 `app.state`에 보관하지 않음 — broker 인스턴스만 보관(broker 인스턴스는 settings를 내부에 가짐, 외부 직접 접근 없음).
- 수정 `app/api/routes.py` — `/paper/status` 응답에 다음 필드 추가/조정:
  - `kis_authenticated`: bool — `kis_broker.auth.is_authenticated()` 결과(broker 없으면 False)
  - `kis_account_loaded`: bool — broker가 계좌 정보를 한 번이라도 성공적으로 로드했는지(현재는 항상 False)
  - `kis_market_data_available`: bool — `kis_broker.market_data.healthcheck()` 결과의 `connected` 필드
  - `last_broker_error`: str | None — `kis_broker.last_error`
  - `account_no_masked`: str — broker가 있으면 마스킹된 계좌번호(예: `***1234`), 없으면 `<unset>`
  - `secret_exposed`: false — mvp-006-1의 `kis_secret_exposed`를 이 이름으로 통일
- 수정 `.env.example` — 변경 없음(mvp-006-1에서 이미 KIS 변수 포함). 단 mvp-006-1 결과가 mvp-007에 도달하지 않은 변수 추가 필요 시 보강.
- 수정 `projects/paper-trading/README.md` — KIS Auth/Account/MarketData 클라이언트 구조 + 상태 머신 + TODO 경계를 짧게 추가.
- 신규 `tests/test_kis_auth_client.py` — 토큰 라이프사이클 상태 머신 + secret 미노출.
- 신규 `tests/test_kis_account_client.py` — 계좌번호 마스킹 + get_account fail-closed.
- 신규 `tests/test_kis_market_data_client.py` — get_quote fail-closed + healthcheck 응답 형식.
- 수정 `tests/test_broker_interface.py` (mvp-006-1에서 추가됨) — KisBroker가 새로운 client 컴포지션을 노출하는지(`broker.auth`, `broker.account`, `broker.market_data` 접근 가능) + 기존 NotImplementedError 검증 유지.
- 수정 `tests/test_api_paper_status.py` (mvp-006-1에서 추가됨) — 신규 status 필드 assertion + `secret_exposed` 이름 통일.
- 수정 `docs/ai/jobs/mvp-007/patch.md` — Codex 변경 요약.

### 제외 (Out of scope; 절대 만지지 않음)

- 실제 KIS Open API HTTP 호출(인증, 계좌, 시세, 주문 모두).
- KIS endpoint URL / TR ID / payload 하드코딩.
- 실주문 활성화(`place_order`/`cancel_order`/`replace_order` 모두 NotImplementedError 유지).
- 시장 데이터 수집 파이프라인 자체 (시세 client는 호출자가 명시적으로 호출).
- KRX 한국 종목용 새 전략. `app/strategy/` 미수정.
- mvp-005의 OMS/RiskEngine/PaperBroker/AlpacaPaperBroker/Strategy/PaperRunner 로직.
- `OrderType` enum 변경(특히 MARKET 추가 금지).
- `app/broker/base.py` Protocol 변경. KIS adapter는 새 메서드를 추가로 노출만.
- `app/broker/paper.py`, `app/broker/alpaca_paper.py` 변경.
- `app/oms/`, `app/risk/`, `app/runtime/`, `app/domain/{enums,orders,market}.py` 변경.
- mvp-001..mvp-005 산출물, mvp-006 산출물(deprecated), `web/`, `prompts/`, `scripts/`, `examples/`, 기존 `docs/`(mvp-007 job dir 제외) 변경.
- `.env`, secrets, credentials, KIS 실제 endpoint URL.
- 인증/결제/DB migration/production infra.
- `git commit`/`push`/`merge`/`deploy` 자동화.
- 임의 shell 실행 기능.
- `pip install` 실행.
- 외부 HTTP 라이브러리 import(`requests`, `httpx`, `aiohttp` 등) — TODO 단계에서 import 자체를 두지 않음(나중에 실제 HTTP mvp에서 추가).

### 안전 가드

- KIS client 3종 모두 `__repr__` 마스킹(account/key/secret/token 노출 금지).
- access token도 `KisAuthClient` 내부 비공개(`_access_token: str | None`). 외부에 노출하는 접근자는 `get_access_token() -> str | None`인데 본 단계에서는 항상 `None`(토큰 발급이 안 됨) 또는 NotImplementedError.
- `last_broker_error`에 secret/계좌/token 원문이 포함될 위험을 차단 — 에러 메시지 빌드 시 절대 `app_secret`, `app_key`, raw account_no를 포함시키지 않는다.
- `/paper/status`의 `account_no_masked`는 client가 제공하는 마스킹 함수 결과만 사용 — 직접 `settings.kis_account_no`를 참조하지 않는다.
- `app.state.kis_broker`는 broker 인스턴스만 보관. broker는 settings를 내부에 가지고 있되 그 settings 자체를 외부 attribute로 노출하지 않는다(이미 mvp-006-1의 `_settings` private 보관).

## 3. 수정해야 할 파일

### 신규

| 파일 | 목적 |
| --- | --- |
| `tests/test_kis_auth_client.py` | 토큰 상태 머신 + secret 미노출 |
| `tests/test_kis_account_client.py` | 계좌번호 마스킹 + fail-closed |
| `tests/test_kis_market_data_client.py` | 시세 fail-closed + 시장 데이터 healthcheck |
| `docs/ai/jobs/mvp-007/patch.md` | Codex 변경 요약 |

### 수정

| 파일 | 변경 내용 |
| --- | --- |
| `app/broker/kis.py` | `KisAuthClient`, `KisAccountClient`, `KisMarketDataClient` 클래스 추가; `KisBroker`가 이 3개를 컴포지션으로 보유. 예외 클래스 추가. 모든 HTTP 호출 NotImplementedError 유지. healthcheck 강화. last_error 추적 |
| `app/api/server.py` | `KisBroker(settings)` 성공 시 `app.state.kis_broker`에 보관. `try/except RuntimeError` 유지 |
| `app/api/routes.py` | `/paper/status` 응답에 신규 필드 추가, `kis_secret_exposed` → `secret_exposed` 통일 |
| `tests/test_broker_interface.py` | broker 컴포지션 접근(`broker.auth`, `broker.account`, `broker.market_data`) + NotImplementedError 검증 유지 |
| `tests/test_api_paper_status.py` | 신규 status 필드 assertion + 필드 이름 통일 |
| `projects/paper-trading/README.md` | KIS Auth/Account/MarketData client 구조 + TODO 경계 추가 |

### 절대 미수정

- `app/config.py` (mvp-006-1 결과를 그대로 두고 mvp-007에서 변경하지 않음 — 새 설정 필드 필요 없음)
- `app/domain/enums.py`, `app/domain/orders.py`, `app/domain/market.py`
- `app/broker/base.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`
- `app/risk/engine.py`, `app/oms/manager.py`, `app/runtime/paper_runner.py`
- `app/strategy/*`, `app/main.py`
- 기존 테스트: `test_config.py`, `test_models.py`, `test_risk_engine.py`, `test_oms.py`, `test_paper_broker.py`, `test_alpaca_paper_stub.py`, `test_flow.py`, `test_paper_runner.py`, `test_strategy_premarket_gap.py`
- mvp-006-1의 `test_kis_config.py` (변경 없음, 단 `secret_exposed` 이름 통일이 필요하면 거기서가 아니라 `test_api_paper_status.py`에서)
- 루트 `.gitignore`, 프로젝트 `.gitignore`
- mvp-001..mvp-006 산출물 (mvp-006은 deprecated, 그대로 둠)

## 4. Codex 구현 지시문

### 4.1 사전 점검 (Codex 첫 단계)

작업 시작 직후 다음을 확인한다. 누락 시 작업을 멈추고 `patch.md` Remaining TODOs에 명시:

- `projects/paper-trading/app/broker/kis.py` 존재 + `KisBroker` 클래스 정의
- `projects/paper-trading/app/config.py`에 `kis_env`/`kis_account_no`/`kis_app_key`/`kis_app_secret`/`allow_market_orders` 필드 존재
- `projects/paper-trading/app/api/routes.py`의 `/paper/status` 응답에 mvp-006-1의 KIS 메타 필드 존재
- `projects/paper-trading/.env.example`에 KIS_* placeholder 라인 존재

위 중 어느 하나라도 누락이면 mvp-006-1을 먼저 구현하라는 메시지를 `patch.md`에 적고 mvp-007 작업을 중단한다.

### 4.2 `app/broker/kis.py` 확장 (mvp-006-1의 기존 내용 위에)

mvp-006-1에서 만든 `KisBroker`를 다음 구조로 리팩터한다. **기존 `__init__` 검증 규칙(KIS_ENV 검사, credentials 누락 검사, `__repr__` 마스킹)은 보존한다.**

#### 4.2.1 예외 클래스 (파일 상단)

```python
class KisError(Exception):
    """Base for KIS adapter errors."""


class KisConfigError(KisError):
    """Configuration missing/invalid."""


class KisAuthError(KisError):
    """Authentication/token error."""


class KisDataUnavailableError(KisError):
    """Market data unavailable or stale."""
```

#### 4.2.2 `KisAuthClient`

```python
from datetime import datetime, timezone

class KisAuthClient:
    """KIS authentication token lifecycle (state machine).

    Network calls are NOT implemented in this phase. authenticate() and
    refresh_token() raise NotImplementedError. The state machine itself
    (token storage, expiry check, clear_token) is implemented and tested.
    """

    def __init__(self, settings: Settings) -> None:
        if not settings.kis_app_key or not settings.kis_app_secret:
            raise KisConfigError("KIS_APP_KEY / KIS_APP_SECRET missing in .env")
        self._settings = settings
        self._access_token: str | None = None
        self._expires_at: datetime | None = None
        self._last_error: str | None = None

    def __repr__(self) -> str:
        token_state = "<set>" if self._access_token else "<unset>"
        return f"KisAuthClient(env={self._settings.kis_env!r}, token={token_state})"

    def is_authenticated(self) -> bool:
        if not self._access_token or not self._expires_at:
            return False
        return datetime.now(timezone.utc) < self._expires_at

    def get_access_token(self) -> str | None:
        # Return cached token only if still valid. Do NOT trigger a network call here.
        if self.is_authenticated():
            return self._access_token
        return None

    def clear_token(self) -> None:
        self._access_token = None
        self._expires_at = None

    def authenticate(self) -> None:
        raise NotImplementedError(
            "KIS authenticate(): TODO — confirm OAuth/token endpoint, payload, and response shape "
            "from KIS Open API official documentation. Do not invent endpoints."
        )

    def refresh_token(self) -> None:
        raise NotImplementedError(
            "KIS refresh_token(): TODO — confirm refresh endpoint and payload from KIS Open API official documentation."
        )

    @property
    def last_error(self) -> str | None:
        return self._last_error
```

#### 4.2.3 `KisAccountClient`

```python
class KisAccountClient:
    """KIS account/positions/cash queries.

    All network calls raise NotImplementedError. Account number masking
    is implemented and testable without HTTP.
    """

    def __init__(self, settings: Settings, auth: KisAuthClient) -> None:
        if not settings.kis_account_no:
            raise KisConfigError("KIS_ACCOUNT_NO missing in .env")
        self._settings = settings
        self._auth = auth
        self._account_loaded = False
        self._last_error: str | None = None

    def __repr__(self) -> str:
        return f"KisAccountClient(account={self.masked_account_no()})"

    def masked_account_no(self) -> str:
        acc = self._settings.kis_account_no
        if not acc:
            return "<unset>"
        if len(acc) <= 4:
            return "***"
        return f"***{acc[-4:]}"

    def is_loaded(self) -> bool:
        return self._account_loaded

    def get_account(self):
        raise NotImplementedError(
            "KIS get_account(): TODO — confirm TR ID + endpoint + payload from KIS Open API docs."
        )

    def get_positions(self):
        raise NotImplementedError(
            "KIS get_positions(): TODO — confirm TR ID + endpoint + payload from KIS Open API docs."
        )

    def get_cash_balance(self):
        raise NotImplementedError(
            "KIS get_cash_balance(): TODO — confirm TR ID + endpoint + payload from KIS Open API docs."
        )

    @property
    def last_error(self) -> str | None:
        return self._last_error
```

#### 4.2.4 `KisMarketDataClient`

```python
class KisMarketDataClient:
    """KIS overseas/US stock market data queries.

    All network calls raise NotImplementedError. healthcheck_market_data()
    returns a static-disconnected dict suitable for /paper/status.
    """

    def __init__(self, settings: Settings, auth: KisAuthClient) -> None:
        self._settings = settings
        self._auth = auth
        self._last_error: str | None = None

    def __repr__(self) -> str:
        return "KisMarketDataClient(<disconnected>)"

    def get_quote(self, symbol: str):
        raise NotImplementedError(
            f"KIS get_quote({symbol!r}): TODO — confirm overseas-quote TR ID + endpoint from KIS Open API docs."
        )

    def get_last_price(self, symbol: str):
        raise NotImplementedError(
            f"KIS get_last_price({symbol!r}): TODO — confirm endpoint from KIS Open API docs."
        )

    def healthcheck_market_data(self) -> dict:
        return {
            "connected": False,
            "reason": "skeleton — KIS market data HTTP calls not implemented in this phase",
            "auth_required": True,
            "auth_present": self._auth.is_authenticated(),
        }

    @property
    def last_error(self) -> str | None:
        return self._last_error
```

#### 4.2.5 `KisBroker` 리팩터

기존 `KisBroker.__init__`은 mvp-006-1의 검증 로직(KIS_ENV/account/key/secret) 그대로 유지하되, 다음 컴포지션을 추가:

```python
class KisBroker:
    mode = TradingMode.PAPER

    def __init__(self, settings: Settings) -> None:
        # ... (mvp-006-1의 기존 검증 유지) ...
        self._settings = settings
        self._auth = KisAuthClient(settings)
        self._account = KisAccountClient(settings, self._auth)
        self._market_data = KisMarketDataClient(settings, self._auth)
        self._last_error: str | None = None

    def __repr__(self) -> str:
        return (
            f"KisBroker(env={self._settings.kis_env!r}, "
            f"account=<set>, app_key=<set>, app_secret=<set>)"
        )

    @property
    def auth(self) -> KisAuthClient:
        return self._auth

    @property
    def account(self) -> KisAccountClient:
        return self._account

    @property
    def market_data(self) -> KisMarketDataClient:
        return self._market_data

    @property
    def last_error(self) -> str | None:
        return self._last_error
```

기존 메서드(`authenticate`, `refresh_token`, `get_account`, `get_positions`, `get_quote`, `get_open_orders`, `place_order`, `cancel_order`, `replace_order`, `submit`, `cancel`, `open_orders`, `positions`)는 다음과 같이 위임/유지:

- `authenticate()` → `self._auth.authenticate()` (NotImplementedError 전파)
- `refresh_token()` → `self._auth.refresh_token()` (NotImplementedError 전파)
- `get_account()` → `self._account.get_account()` (NotImplementedError 전파)
- `get_positions()` → `self._account.get_positions()` (NotImplementedError 전파)
- `get_quote(symbol)` → `self._market_data.get_quote(symbol)` (NotImplementedError 전파)
- `get_open_orders()` → `NotImplementedError` (그대로)
- `place_order/cancel_order/replace_order` → `NotImplementedError` (그대로, 강한 메시지 유지)
- `submit/cancel/open_orders/positions` (BrokerAdapter 호환) → 위에 동일 위임

`healthcheck()` 강화:

```python
def healthcheck(self) -> dict:
    market = self._market_data.healthcheck_market_data()
    return {
        "broker": "KisBroker",
        "environment": self._settings.kis_env,
        "config_loaded": True,  # __init__ succeeded
        "authenticated": self._auth.is_authenticated(),
        "account_loaded": self._account.is_loaded(),
        "market_data": market,
        "last_error": self._last_error,
        "order_execution_implemented": False,
    }
```

### 4.3 `app/api/server.py` 변경

mvp-006-1에서 `KisBroker(settings)`를 try/except로 시도해 `configured_brokers`에 등록만 했다. mvp-007에서는 **broker 인스턴스 자체를 `app.state.kis_broker`로 보관**한다:

```python
kis_broker = None
configured_brokers: list[str] = []
try:
    from app.broker.kis import KisBroker
    kis_broker = KisBroker(settings)
    configured_brokers.append("KisBroker")
except RuntimeError:
    pass
```

lifespan 안에서:

```python
app.state.configured_brokers = configured_brokers
app.state.kis_broker = kis_broker  # None or KisBroker instance
```

- `except RuntimeError`만 catch. broad `Exception` 금지.
- KIS 인스턴스를 보관하지만 settings 자체를 외부 attribute로 노출하지 않는다(broker._settings는 private 그대로).

### 4.4 `app/api/routes.py` 변경

`/paper/status` 응답을 다음으로 확장(기존 mvp-005/mvp-006-1 필드 보존). `kis_secret_exposed` → `secret_exposed`로 이름 통일:

```python
@router.get("/paper/status")
def paper_status(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    broker = request.app.state.broker
    kis = request.app.state.kis_broker  # None or KisBroker

    kis_loaded = bool(
        settings.kis_env
        and settings.kis_account_no
        and settings.kis_app_key
        and settings.kis_app_secret
    )

    if kis is not None:
        kis_authenticated = kis.auth.is_authenticated()
        kis_account_loaded = kis.account.is_loaded()
        kis_market = kis.market_data.healthcheck_market_data()
        kis_market_available = bool(kis_market.get("connected"))
        last_broker_error = kis.last_error
        account_no_masked = kis.account.masked_account_no()
    else:
        kis_authenticated = False
        kis_account_loaded = False
        kis_market_available = False
        last_broker_error = None
        account_no_masked = "<unset>"

    return {
        "ok": True,
        "mode": settings.trading_mode.value,
        "live_enabled": settings.live_trading_enabled,
        "strategies": list(STRATEGY_NAMES),
        "safety": { ... (mvp-005 그대로) ... },
        # mvp-006-1
        "broker_type": type(broker).__name__,
        "broker_environment": "paper",
        "live_trading_enabled": settings.live_trading_enabled,
        "market_orders_allowed": settings.allow_market_orders,
        "kis_config_loaded": kis_loaded,
        "configured_brokers": list(request.app.state.configured_brokers),
        # mvp-007
        "kis_authenticated": kis_authenticated,
        "kis_account_loaded": kis_account_loaded,
        "kis_market_data_available": kis_market_available,
        "last_broker_error": last_broker_error,
        "account_no_masked": account_no_masked,
        "secret_exposed": False,  # renamed from kis_secret_exposed
    }
```

- 어떤 분기에서도 `settings.kis_app_key`, `settings.kis_app_secret`, raw `settings.kis_account_no`를 응답에 포함시키지 않는다.
- `account_no_masked`는 broker가 있을 때만 client의 마스킹 함수로 산출. settings에서 직접 슬라이스하지 않는다.

`/paper/run`, `/healthz`는 손대지 않는다.

### 4.5 테스트

#### `tests/test_kis_auth_client.py` (신규)

핵심 검증:
1. `KisAuthClient(settings)`: credentials 누락 시 `KisConfigError`.
2. 초기 상태에서 `is_authenticated()` False, `get_access_token()` None.
3. `clear_token()` 호출 후에도 상태 동일.
4. `authenticate()` / `refresh_token()` → `NotImplementedError` 메시지에 "TODO" 포함.
5. `repr(client)`에 실제 key/secret 값 미노출. token 미발급 시 `token=<unset>`.
6. 토큰 만료 시뮬레이션: 내부 `_access_token`, `_expires_at`을 직접 설정(테스트에서) → `is_authenticated()`가 시간 비교로 정확히 동작.
7. `last_error`는 초기 None.

```python
from datetime import datetime, timezone, timedelta
from dataclasses import replace
import pytest

from app.broker.kis import KisAuthClient, KisConfigError


def _settings(s):
    return replace(s, kis_env="paper", kis_account_no="acc",
                   kis_app_key="k-FAKE", kis_app_secret="s-FAKE")


def test_auth_client_requires_credentials(settings):
    bad = replace(settings, kis_env="paper", kis_account_no="acc",
                  kis_app_key=None, kis_app_secret=None)
    with pytest.raises(KisConfigError):
        KisAuthClient(bad)


def test_initial_state(settings):
    c = KisAuthClient(_settings(settings))
    assert c.is_authenticated() is False
    assert c.get_access_token() is None
    assert c.last_error is None


def test_authenticate_not_implemented(settings):
    c = KisAuthClient(_settings(settings))
    with pytest.raises(NotImplementedError, match="TODO"):
        c.authenticate()
    with pytest.raises(NotImplementedError, match="TODO"):
        c.refresh_token()


def test_repr_masks_secrets(settings):
    c = KisAuthClient(_settings(settings))
    text = repr(c)
    assert "k-FAKE" not in text
    assert "s-FAKE" not in text
    assert "token=<unset>" in text


def test_token_expiry_state_machine(settings):
    c = KisAuthClient(_settings(settings))
    future = datetime.now(timezone.utc) + timedelta(minutes=5)
    past = datetime.now(timezone.utc) - timedelta(minutes=1)
    # simulate a valid token
    c._access_token = "tok-FAKE"
    c._expires_at = future
    assert c.is_authenticated() is True
    assert c.get_access_token() == "tok-FAKE"
    # simulate expired
    c._expires_at = past
    assert c.is_authenticated() is False
    assert c.get_access_token() is None
    # clear
    c._access_token = "tok-FAKE"
    c._expires_at = future
    c.clear_token()
    assert c.is_authenticated() is False
```

#### `tests/test_kis_account_client.py` (신규)

```python
from dataclasses import replace
import pytest

from app.broker.kis import KisAccountClient, KisAuthClient, KisConfigError


def _s(s, acc=None, key="k", sec="s"):
    return replace(s, kis_env="paper", kis_account_no=acc, kis_app_key=key, kis_app_secret=sec)


def test_account_requires_account_no(settings):
    auth = KisAuthClient(_s(settings, acc="x"))
    bad = _s(settings, acc=None)
    with pytest.raises(KisConfigError):
        KisAccountClient(bad, auth)


def test_masking_short_account(settings):
    s = _s(settings, acc="12")
    auth = KisAuthClient(s)
    acc = KisAccountClient(s, auth)
    assert acc.masked_account_no() == "***"


def test_masking_long_account(settings):
    s = _s(settings, acc="50187996")
    auth = KisAuthClient(s)
    acc = KisAccountClient(s, auth)
    assert acc.masked_account_no() == "***7996"


def test_repr_masks_account(settings):
    s = _s(settings, acc="50187996")
    auth = KisAuthClient(s)
    acc = KisAccountClient(s, auth)
    text = repr(acc)
    assert "50187996" not in text
    assert "7996" in text  # masked tail OK


def test_methods_not_implemented(settings):
    s = _s(settings, acc="x")
    auth = KisAuthClient(s)
    acc = KisAccountClient(s, auth)
    for method in ("get_account", "get_positions", "get_cash_balance"):
        with pytest.raises(NotImplementedError):
            getattr(acc, method)()


def test_initial_not_loaded(settings):
    s = _s(settings, acc="x")
    auth = KisAuthClient(s)
    acc = KisAccountClient(s, auth)
    assert acc.is_loaded() is False
```

#### `tests/test_kis_market_data_client.py` (신규)

```python
from dataclasses import replace
import pytest

from app.broker.kis import KisAuthClient, KisMarketDataClient


def _s(settings):
    return replace(settings, kis_env="paper", kis_account_no="x",
                   kis_app_key="k", kis_app_secret="s")


def test_get_quote_not_implemented(settings):
    s = _s(settings)
    md = KisMarketDataClient(s, KisAuthClient(s))
    with pytest.raises(NotImplementedError, match="TODO"):
        md.get_quote("AAPL")


def test_get_last_price_not_implemented(settings):
    s = _s(settings)
    md = KisMarketDataClient(s, KisAuthClient(s))
    with pytest.raises(NotImplementedError, match="TODO"):
        md.get_last_price("AAPL")


def test_healthcheck_returns_disconnected(settings):
    s = _s(settings)
    md = KisMarketDataClient(s, KisAuthClient(s))
    h = md.healthcheck_market_data()
    assert h["connected"] is False
    assert "skeleton" in h["reason"].lower() or "not implemented" in h["reason"].lower()
    assert h["auth_required"] is True
    assert h["auth_present"] is False
```

#### `tests/test_broker_interface.py` 보정 (mvp-006-1 기존)

기존 테스트 유지 + 추가:

```python
def test_kis_broker_exposes_sub_clients(settings):
    s = replace(settings, kis_env="paper", kis_account_no="x",
                kis_app_key="k", kis_app_secret="s")
    b = KisBroker(s)
    assert b.auth is not None
    assert b.account is not None
    assert b.market_data is not None
    assert callable(b.auth.is_authenticated)
    assert callable(b.account.masked_account_no)
    assert callable(b.market_data.healthcheck_market_data)


def test_kis_broker_healthcheck_includes_subcomponents(settings):
    s = replace(settings, kis_env="paper", kis_account_no="50187996",
                kis_app_key="k", kis_app_secret="s")
    b = KisBroker(s)
    h = b.healthcheck()
    assert h["broker"] == "KisBroker"
    assert h["environment"] == "paper"
    assert h["authenticated"] is False
    assert h["account_loaded"] is False
    assert h["market_data"]["connected"] is False
    assert h["order_execution_implemented"] is False
    text = str(h)
    assert "50187996" not in text  # raw account must not leak via healthcheck


def test_kis_broker_last_error_initially_none(settings):
    s = replace(settings, kis_env="paper", kis_account_no="x",
                kis_app_key="k", kis_app_secret="s")
    b = KisBroker(s)
    assert b.last_error is None
```

#### `tests/test_api_paper_status.py` 보정 (mvp-006-1 기존)

기존 assertion 유지. 다음을 추가/조정:

```python
# field name unified: secret_exposed (not kis_secret_exposed)
assert body["secret_exposed"] is False
# new mvp-007 fields
assert body["kis_authenticated"] is False
assert body["kis_account_loaded"] is False
assert body["kis_market_data_available"] is False
assert body["last_broker_error"] is None
assert isinstance(body["account_no_masked"], str)
# masked account no must not contain the raw account number
# (in test env, .env is not present; account_no_masked should be "<unset>" or "***xxxx")
# regardless, real account_no string must not be in response body
body_text = response.text
for forbidden in ("KIS_APP_KEY", "KIS_APP_SECRET", "kis_app_secret"):
    assert forbidden not in body_text
# 만약 kis_secret_exposed라는 옛 이름이 남아 있으면 실패 (이름 통일 확인)
assert "kis_secret_exposed" not in body_text
```

### 4.6 `projects/paper-trading/README.md` 변경

`## KIS Open API (모의투자) 연결 준비` 섹션 아래에 다음 단락을 추가:

```markdown
### 클라이언트 구조 (mvp-007)

`app/broker/kis.py`는 다음 네 클래스를 분리해서 정의합니다.

- `KisAuthClient` — 인증 토큰 라이프사이클(상태 머신). `is_authenticated()`, `get_access_token()`, `clear_token()`은 구현됨. `authenticate()`/`refresh_token()`은 KIS 공식 문서 확인 후 별도 mvp에서 HTTP 호출 구현 예정.
- `KisAccountClient` — 계좌/포지션/현금 조회. 계좌번호 마스킹(`masked_account_no()`)은 구현됨. 조회 메서드는 TODO.
- `KisMarketDataClient` — 시세 조회 및 시장 데이터 헬스체크. `healthcheck_market_data()`는 disconnected dict를 반환. 조회 메서드는 TODO.
- `KisBroker` — BrokerAdapter Protocol 구현체. 위 3개 client를 컴포지션으로 보유하고 메서드 위임.

`KisBroker.healthcheck()`는 sub-component 상태(authenticated, account_loaded, market_data, last_error, order_execution_implemented)를 함께 반환합니다. `/paper/status`가 이 정보를 표면화합니다.

### 무엇이 TODO인가

- KIS Open API의 OAuth/토큰 endpoint, 갱신 endpoint, 응답 shape — `KisAuthClient.authenticate()`/`refresh_token()`.
- KIS 계좌/포지션/현금 TR ID, endpoint, payload — `KisAccountClient.get_account()` 등.
- KIS 해외주식 시세 TR ID, endpoint, payload — `KisMarketDataClient.get_quote()` 등.
- KIS 주문/취소/정정 endpoint, payload, OMS 통합 — `KisBroker.place_order()` 등. 별도 mvp(예: mvp-008).

위 항목은 KIS Open API 공식 문서 확인 후 구현합니다. **추측해서 endpoint/TR ID를 코드에 적지 않습니다.**
```

### 4.7 검증 명령

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

mvp-005 + mvp-006-1 + mvp-007 모든 테스트 PASS. 호스트 의존성 미설치 시 `patch.md` Remaining TODOs에 `python3 -m pip install fastapi 'uvicorn[standard]' 'pydantic>=2' python-dotenv pytest httpx` 명령 명시.

### 4.8 `docs/ai/jobs/mvp-007/patch.md`

요청의 "완료 후 patch.md에 정리할 내용" 9개 항목과 1:1 대응:

```markdown
## 1. Files Changed
(신규/수정 파일 전체)

## 2. Implementation Summary

### 2.1 변경 파일
(목록 + 한 줄 설명)

### 2.2 KIS 인증 구조
- KisAuthClient 클래스 분리.
- 토큰 상태 머신: _access_token / _expires_at / is_authenticated() / get_access_token() / clear_token() — 모두 구현 + 테스트.
- authenticate() / refresh_token() — NotImplementedError(KIS 공식 문서 확인 후 별도 mvp).
- __repr__가 key/secret/token 미노출.

### 2.3 KIS 계좌 조회 구조
- KisAccountClient 클래스 분리.
- masked_account_no()로 마스킹된 계좌번호만 외부 노출 (***xxxx 패턴).
- get_account/get_positions/get_cash_balance — NotImplementedError(TODO).
- is_loaded() bool로 로드 상태 표면화.

### 2.4 KIS 시세 조회 구조
- KisMarketDataClient 클래스 분리.
- get_quote(symbol)/get_last_price(symbol) — NotImplementedError(TODO).
- healthcheck_market_data() — 정적 disconnected dict (auth_required, auth_present 포함).

### 2.5 실제 주문 기능 비활성 유지
- KisBroker.place_order / cancel_order / replace_order: NotImplementedError 그대로.
- BrokerAdapter Protocol 호환 submit/cancel: 동일.
- OrderType에 MARKET 없음.
- live trading 5단 + KIS 6단 차단 모두 유지.
- Strategy 패키지가 app.broker.kis import 0건(grep).

### 2.6 secret 미노출
- Settings의 app_key/app_secret/account_no는 field(repr=False) (mvp-006-1).
- KisAuthClient/Account/MarketData/Broker 각각 __repr__ 마스킹.
- /paper/status 응답에 raw secret/key/account 미포함.
- 계좌번호는 ***xxxx 패턴으로만 노출.
- last_broker_error 메시지에 secret 미포함(설계상 메시지 생성 시 secret 직접 인용 금지).

### 2.7 실행한 테스트
- python -m compileall app tests: <결과>
- python -m pytest -p no:cacheprovider: <결과>
- 기존 + mvp-006-1 + mvp-007 신규 테스트 모두 PASS / (미설치 사유 명시)

### 2.8 공식 문서 부재로 TODO로 남긴 부분
- KIS OAuth/토큰 발급 endpoint, payload, expires_in 응답 shape
- KIS 토큰 갱신 endpoint, payload
- KIS 계좌/포지션/현금 TR ID, endpoint, payload, 응답 shape
- KIS 해외주식 시세 TR ID, endpoint, payload, 응답 shape
- 주문/취소/정정 endpoint, payload — mvp-008 범위

### 2.9 다음 mvp 후보
- mvp-008: KIS 모의투자 주문 흐름 연결(공식 문서 확인 후, 소액 검증 전까지 실주문 금지).
- 또는 KIS 인증 HTTP 호출 실제 구현(KIS 공식 문서 reference + 사용자 명시 승인 + dotenv URL/endpoint 변수 추가).
- 또는 Alpaca Paper HTTP 호출 실제 구현.

## 3. Safety Confirmation
- live trading 5단(+KIS 6단째) 차단 유지.
- 실계좌(KIS 실전, Alpaca Live 등) 어댑터 없음.
- 시장가 주문 차단 유지 (OrderType MARKET 없음, ALLOW_MARKET_ORDERS=true fail closed).
- mvp-005의 Strategy/OMS/Risk/Broker 격리 불변식 그대로.
- KIS endpoint URL, TR ID 코드 하드코딩 없음.
- 실제 KIS key/secret/account 코드/문서/.env.example/응답/log/patch/review 어디에도 없음.
- 외부 HTTP 라이브러리(requests/httpx 등) import 없음.
- /paper/status 응답에서 secret 미노출, account_no 마스킹.
- .env staged/committed 없음.
- commit/push/merge/deploy 자동화 없음.

## 4. Test Results
(2.7과 동일)

## 5. Remaining TODOs
- KIS 공식 문서 확인 후 인증/계좌/시세 HTTP 구현.
- mvp-008: 주문 흐름.
- (필요 시) 의존성 미설치 pip install 명령.
```

## 5. 테스트 기준

1. `python -m compileall app tests` 종료코드 0.
2. `python -m pytest -p no:cacheprovider` 종료코드 0(또는 의존성 미설치 Remaining TODOs).
3. mvp-005 19개 + mvp-006-1 약 17개 + mvp-007 신규 약 25개 모두 PASS(회귀 없음).
4. `grep -RIn "MARKET" projects/paper-trading/app` 결과 변경 없음(`OrderType.MARKET` 없음).
5. `grep -RIn "from app\.broker\.kis" projects/paper-trading/app/strategy` 결과 0건.
6. `grep -RIn "^import requests\|^import httpx\|^import aiohttp\|^from requests\|^from httpx\|^from aiohttp" projects/paper-trading/app/broker/kis.py` 결과 0건.
7. `grep -RIn "https://" projects/paper-trading/app/broker/kis.py` 결과 0건(URL 하드코딩 없음).
8. `grep -RIn "KIS_APP_SECRET\|KIS_APP_KEY\|KIS_ACCOUNT_NO" projects/paper-trading/app/broker/kis.py` 결과는 정의 참조(`settings.kis_app_key` 등)만, 실제 값 0건.
9. `projects/paper-trading/.env.example`에 KIS 실제 키/계좌 0건.
10. `git status --short`에 `.env` 미등장.
11. `git diff --stat`에 mvp-007 외 변경 없음.
12. `/paper/status` 응답에 신규 필드 모두 존재, raw 값 미노출.

## 6. 리뷰 체크리스트

- [ ] mvp-007 작업 시작 시 mvp-006-1 사전 점검 통과.
- [ ] `app/broker/kis.py`에 `KisAuthClient`, `KisAccountClient`, `KisMarketDataClient`, `KisBroker`, 4개 예외 클래스 정의.
- [ ] 모든 client `__repr__`가 secret/key/account/token 미노출.
- [ ] `KisAuthClient` 토큰 상태 머신(is_authenticated/get_access_token/clear_token) 구현 + 테스트 통과.
- [ ] `KisAuthClient.authenticate()`/`refresh_token()` NotImplementedError(메시지에 "TODO" + 공식 문서 reference 안내).
- [ ] `KisAccountClient.masked_account_no()` 구현 + `***xxxx` 패턴 + raw 미노출.
- [ ] `KisAccountClient.get_account()`/`get_positions()`/`get_cash_balance()` NotImplementedError.
- [ ] `KisMarketDataClient.healthcheck_market_data()` 정적 disconnected dict 반환.
- [ ] `KisMarketDataClient.get_quote()`/`get_last_price()` NotImplementedError.
- [ ] `KisBroker`가 `.auth`/`.account`/`.market_data` property로 sub-client 노출.
- [ ] `KisBroker.healthcheck()`가 sub-component 상태(authenticated/account_loaded/market_data/last_error/order_execution_implemented) 포함.
- [ ] `KisBroker.place_order`/`cancel_order`/`replace_order`/`submit`/`cancel` NotImplementedError 그대로(실주문 차단).
- [ ] `app/api/server.py`가 `KisBroker` 성공 시 `app.state.kis_broker`에 보관, 실패는 None.
- [ ] `/paper/status`에 `kis_authenticated`/`kis_account_loaded`/`kis_market_data_available`/`last_broker_error`/`account_no_masked`/`secret_exposed` 필드 추가.
- [ ] `secret_exposed`로 이름 통일(`kis_secret_exposed` 잔재 없음).
- [ ] `/paper/status` 응답에 raw key/secret/account/token 미노출(텍스트 검사).
- [ ] `app/strategy/`가 `app.broker.kis*` import 0건(grep).
- [ ] `app/broker/kis.py`에 외부 HTTP 라이브러리 import 0건.
- [ ] `app/broker/kis.py`에 KIS URL 코드 하드코딩 0건.
- [ ] `.env.example`에 실제 KIS 키/계좌 0건.
- [ ] mvp-005 + mvp-006-1 기존 테스트 모두 PASS(회귀 없음).
- [ ] mvp-007 신규 테스트(`test_kis_auth_client.py`, `test_kis_account_client.py`, `test_kis_market_data_client.py`, `test_broker_interface.py` 보정, `test_api_paper_status.py` 보정) PASS.
- [ ] `app/config.py`/`app/domain/`/`app/oms/`/`app/risk/`/`app/runtime/`/`app/strategy/`/`app/broker/{base,paper,alpaca_paper}.py` 미변경.
- [ ] mvp-001..mvp-006 산출물 미변경. `web/`/`prompts/`/`scripts/`/기존 `docs/` 미변경.
- [ ] `.env` staged/committed 없음.
- [ ] commit/push/merge/deploy 자동화 없음.
- [ ] `patch.md` 5섹션 + Implementation Summary 9단락 모두 채움.
