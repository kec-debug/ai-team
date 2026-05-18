## 1. 요청 요약

미국주식 자동 페이퍼매매 시스템의 **Phase 1 스캐폴딩**을 만든다. 실제 매매 전략 구현 전에, paper trading 실행 경로가 안전하게 동작하도록 골격 코드와 테스트를 구축하는 것이 목표다.

다음 사항을 인지하고 시작한다.

- 현 `ai-team` 저장소에는 트레이딩 시스템 코드가 전혀 없다. (`app/`, broker adapter, RiskEngine, OMS, Strategy, `/paper/status` API 모두 없음.)
- 사용자가 명시적으로 선택한 진행 방식은 **ai-team 하위에 새 Python 프로젝트 스캐폴딩**이다.
- 대상 디렉터리: `projects/paper-trading/` (저장소 루트 기준 신규 생성).
- Phase 1은 골격 + 안전 가드 + 최소 API + 단위/통합 테스트까지만 만든다. 실제 Alpaca 네트워크 호출, 시장 데이터, 매매 전략 본체는 Phase 2 이후.

핵심 절대 조건(요청 + `prompts/claude.md` 안전 규칙):

- live trading 코드 경로/플래그를 활성화하지 않는다. `LIVE_TRADING_ENABLED=false`를 기본값이자 **변경 불가**한 Phase 1 상수로 둔다.
- 실계좌 주문을 만들 수 있는 코드 경로는 만들지 않는다. (Alpaca 어댑터는 stub만, 네트워크 호출 미구현.)
- 시장가(market) 주문은 RiskEngine이 무조건 거부한다.
- 모든 주문은 `Strategy → RiskEngine → OMS → BrokerAdapter` 순서를 통과해야 한다. RiskEngine 우회는 코드 경로 자체에서 막는다.
- agent / LLM이 직접 주문을 만들 수 없다. Strategy는 비실행성 `OrderIntent`만 만든다. 실행성 주문은 OMS만 만든다.
- API 키는 `.env`에서만 읽는다. `.env`는 커밋하지 않는다. 저장소에는 `.env.example`만 둔다.
- 브로커 endpoint URL은 코드에 하드코딩하지 않는다. `.env`에서 읽고, 없으면 fail closed(예외)로 멈춘다.
- `git commit`, `git push`, PR merge, deploy는 자동화하지 않는다.

## 2. 작업 범위

### 포함 (In scope)

신규 디렉터리 `projects/paper-trading/` 아래에 다음을 만든다.

- 패키지 메타데이터: `pyproject.toml`, `README.md`, `.env.example`, `.gitignore`, `pytest.ini`(또는 pyproject 설정).
- 안전 설정 모듈: `app/config.py` (paper 기본, live 차단, 환경변수 로딩).
- 도메인 데이터 모델: `app/models.py` (`OrderIntent`, `Order`, `BrokerOrder`, `OrderAck`, `OrderType`, `Side`, `TradingMode`).
- 브로커 인터페이스: `app/broker/base.py` (`BrokerAdapter` Protocol/ABC).
- Paper 브로커: `app/broker/paper.py` (in-memory 시뮬레이션, live mode 사용 시 즉시 RuntimeError).
- Alpaca Paper 어댑터 stub: `app/broker/alpaca_paper.py` (env에서 base URL 로드, 네트워크 호출은 NotImplementedError로 fail closed).
- RiskEngine: `app/risk_engine.py` (시장가 거부, 최대 주문 금액/수량 한도, paper-only 강제, fail closed).
- OMS: `app/oms.py` (RiskEngine 통과 토큰 없는 주문은 거부, broker submit의 유일한 경로).
- Strategy 베이스: `app/strategy.py` (`Strategy` 추상 + `NoopStrategy`; `OrderIntent`만 만들 수 있음).
- Paper 실행 상태 API: `app/api/server.py` (`GET /paper/status`, `GET /healthz`).
- 진입점: `app/main.py` (uvicorn 실행 진입점, 기본은 dry-run 안내만 출력하며 자동 매매를 시작하지 않음).
- 단위/통합 테스트: `tests/` 하위.

### 제외 (Out of scope; 절대 만지지 않음)

- 실계좌(Alpaca Live, 그 외 broker live) 어댑터.
- live trading 활성화 토글/플래그.
- 시장가(market) 주문 경로.
- 매매 전략 본체 구현(`NoopStrategy` 외).
- 실제 Alpaca 네트워크 통신, 시장 데이터 수집.
- 잔액/세금/체결 슬리피지 정밀 모델링.
- `web/` GUI 변경 (mvp-003 범위 밖).
- `prompts/`, `scripts/`, 기존 `docs/` 파일 변경.
- `.env`, secrets, credentials, API key, token 류 일체.
- 인증, 결제, 데이터베이스 마이그레이션, production infra.
- `git commit`, `git push`, PR 생성/머지, 배포 자동화.
- 임의 shell 실행 기능.

### 안전 가드 (Codex가 작업 중 항상 지켜야 할 것)

- 새 파일은 모두 `projects/paper-trading/` 아래에만 만든다.
- 신규 의존성은 `pyproject.toml`에만 선언한다. `pip install`은 실행하지 않는다(테스트 실행 시 호스트에 이미 설치된 패키지만 사용; 없으면 patch.md에 명시).
- 코드에 어떤 시크릿도 하드코딩하지 않는다. `.env.example`은 placeholder 값(`changeme-paper-key` 등)만 갖는다.
- Alpaca Paper URL은 `.env.example`에 placeholder로만 적고, 실제 어댑터는 env에서 읽는다. URL을 모를 경우 어댑터 코드의 상수로 적지 않는다.
- 어떤 코드 경로에서도 live 주문을 만들 수 없도록 OMS와 RiskEngine 양쪽에서 이중으로 차단한다.

## 3. 수정해야 할 파일

신규 파일만 생성한다. 기존 파일 수정은 없다(단, 저장소 루트 `.gitignore`에 `projects/paper-trading/.env`만 한 줄 추가 — 아래 4.13 참고).

| 파일 | 목적 |
| --- | --- |
| `projects/paper-trading/README.md` | 모듈 개요, 안전 규칙, 실행/테스트 방법, 환경변수 |
| `projects/paper-trading/pyproject.toml` | Python 패키지 메타데이터 + 의존성 |
| `projects/paper-trading/.env.example` | 환경변수 템플릿(placeholder만) |
| `projects/paper-trading/.gitignore` | `.env`, `__pycache__/`, `.pytest_cache/`, `*.egg-info/`, `.coverage` 등 |
| `projects/paper-trading/pytest.ini` | pytest 설정 (rootdir, testpaths) |
| `projects/paper-trading/app/__init__.py` | 패키지 마커 |
| `projects/paper-trading/app/config.py` | `TradingMode` 열거형, `Settings` 데이터클래스, live 차단 |
| `projects/paper-trading/app/models.py` | 도메인 모델 (`OrderIntent`, `Order`, `BrokerOrder`, `OrderAck`, `Side`, `OrderType`) |
| `projects/paper-trading/app/broker/__init__.py` | 패키지 마커 |
| `projects/paper-trading/app/broker/base.py` | `BrokerAdapter` Protocol/ABC |
| `projects/paper-trading/app/broker/paper.py` | in-memory paper broker |
| `projects/paper-trading/app/broker/alpaca_paper.py` | Alpaca Paper 어댑터 stub (네트워크 미구현) |
| `projects/paper-trading/app/risk_engine.py` | RiskEngine 규칙 + 통과 토큰 발급 |
| `projects/paper-trading/app/oms.py` | OMS, 유일한 broker submit 경로 |
| `projects/paper-trading/app/strategy.py` | `Strategy` 추상 + `NoopStrategy` |
| `projects/paper-trading/app/api/__init__.py` | 패키지 마커 |
| `projects/paper-trading/app/api/server.py` | FastAPI `GET /paper/status`, `GET /healthz` |
| `projects/paper-trading/app/main.py` | uvicorn 실행 진입점 (자동 매매 미실행) |
| `projects/paper-trading/tests/__init__.py` | 패키지 마커 |
| `projects/paper-trading/tests/test_config.py` | 기본 paper 모드 / live 차단 검증 |
| `projects/paper-trading/tests/test_models.py` | 모델 불변식 검증 |
| `projects/paper-trading/tests/test_risk_engine.py` | 시장가 거부, 한도 초과 거부, paper 강제 |
| `projects/paper-trading/tests/test_oms.py` | RiskEngine 우회 차단, live 차단 |
| `projects/paper-trading/tests/test_paper_broker.py` | paper 브로커 동작 |
| `projects/paper-trading/tests/test_alpaca_paper_stub.py` | env 미설정 fail closed, 네트워크 미구현 확인 |
| `projects/paper-trading/tests/test_flow.py` | Strategy → RiskEngine → OMS → PaperBroker 통합 |
| `projects/paper-trading/tests/test_api_paper_status.py` | `/paper/status` 응답, `live_enabled=false` |
| `.gitignore` (저장소 루트) | `projects/paper-trading/.env` 라인 한 줄 추가 |
| `docs/ai/jobs/mvp-003/patch.md` | Codex가 변경 요약 작성 |

## 4. Codex 구현 지시문

> Codex는 다음 지시를 그대로 따른다. 범위 확장 금지. 안전 규칙 우선.

### 4.1 사전 조건

- 작업 루트: `/root/ai-dev-center/projects/ai-team`.
- 신규 코드는 모두 `projects/paper-trading/` 아래에만 만든다.
- 기존 파일 수정은 저장소 루트 `.gitignore` 한 줄 추가 외에는 없다.
- `git commit`, `git push`, PR 생성/머지, 배포 절대 금지.
- `.env`, secrets, credentials, API key, token 류 절대 만지지 않는다.
- 어떤 코드에도 시크릿/실제 API 키/실제 URL 하드코딩 금지.
- `pip install`을 실행하지 않는다. 호스트에 이미 설치된 패키지(`pytest`, `fastapi`, `pydantic`, `python-dotenv` 등)가 있다면 그대로 사용하고, 없으면 `patch.md`에 `pip install`이 필요한 패키지 목록만 남긴다.

### 4.2 `projects/paper-trading/pyproject.toml`

- 빌드 시스템: `setuptools` 또는 `hatchling` 중 하나(둘 다 표준). `setuptools` 권장.
- 프로젝트명: `paper-trading`, 버전 `0.1.0`, Python 요구: `>=3.10`.
- 의존성: `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `python-dotenv`. 테스트 의존성: `pytest`, `httpx`(FastAPI TestClient 의존).
- `[tool.pytest.ini_options]`에 `testpaths = ["tests"]`, `addopts = "-p no:cacheprovider"`를 둔다.

### 4.3 `projects/paper-trading/.env.example`

다음 키만 placeholder 값으로 둔다. 실제 시크릿 금지.

```
TRADING_MODE=paper
LIVE_TRADING_ENABLED=false
ALPACA_PAPER_API_BASE=
ALPACA_PAPER_KEY_ID=
ALPACA_PAPER_SECRET_KEY=
PAPER_STARTING_CASH=100000
MAX_ORDER_NOTIONAL_USD=5000
MAX_OPEN_POSITIONS=20
SYMBOL_ALLOWLIST=AAPL,MSFT,GOOG,AMZN,NVDA
```

`ALPACA_PAPER_API_BASE`는 비워두고, 주석으로 "Alpaca Paper의 공식 paper trading base URL을 사용자가 .env에 직접 적는다. 이 저장소는 URL을 추측하지 않는다."를 둔다.

### 4.4 `projects/paper-trading/.gitignore`

`.env`, `__pycache__/`, `.pytest_cache/`, `*.egg-info/`, `.coverage`, `.venv/`, `dist/`, `build/`를 무시한다.

### 4.5 `projects/paper-trading/app/config.py`

- `class TradingMode(str, Enum): PAPER = "paper"; LIVE = "live"`.
- `@dataclass(frozen=True) class Settings`:
  - `trading_mode: TradingMode = TradingMode.PAPER`
  - `live_trading_enabled: bool = False`
  - `alpaca_paper_api_base: str | None = None`
  - `alpaca_paper_key_id: str | None = None`
  - `alpaca_paper_secret_key: str | None = None`
  - `paper_starting_cash: Decimal = Decimal("100000")`
  - `max_order_notional_usd: Decimal = Decimal("5000")`
  - `max_open_positions: int = 20`
  - `symbol_allowlist: tuple[str, ...] = ()`
- `def load_settings() -> Settings`:
  - `python-dotenv`로 `.env`를 읽는다. `.env`가 없어도 OK(기본값 사용).
  - `TRADING_MODE`가 `paper`가 아니면 `ValueError("Phase 1 only supports paper trading")`로 fail closed.
  - `LIVE_TRADING_ENABLED`이 `true`이면 `ValueError("Live trading is disabled in Phase 1")`로 fail closed.
  - `Decimal` 변환은 안전하게(`Decimal(os.environ.get(...))`).
  - `symbol_allowlist`는 콤마 분리 후 대문자 정규화.

### 4.6 `projects/paper-trading/app/models.py`

- `class Side(str, Enum): BUY = "buy"; SELL = "sell"`.
- `class OrderType(str, Enum): LIMIT = "limit"; STOP_LIMIT = "stop_limit"` (시장가 의도적으로 누락).
- `@dataclass(frozen=True) class OrderIntent`:
  - `symbol: str`, `side: Side`, `quantity: int`, `order_type: OrderType`, `limit_price: Decimal`, `stop_price: Decimal | None = None`, `client_tag: str | None = None`.
  - `__post_init__`에서 `quantity > 0`, `limit_price > 0`, `symbol == symbol.upper()` 검증, 아니면 `ValueError`.
- `@dataclass(frozen=True) class Order`:
  - `OrderIntent`의 모든 필드 + `risk_token: str`(RiskEngine 발급 토큰), `created_at: datetime`.
- `@dataclass(frozen=True) class BrokerOrder`:
  - `Order`의 모든 필드 + `oms_id: str`, `submitted_at: datetime`.
- `@dataclass(frozen=True) class OrderAck`:
  - `oms_id: str`, `broker_order_id: str | None`, `status: str`, `mode: TradingMode`.

### 4.7 `projects/paper-trading/app/broker/base.py`

- `class BrokerAdapter(Protocol)`:
  - `mode: TradingMode` (구현체 속성).
  - `def submit(self, broker_order: BrokerOrder) -> OrderAck: ...`
  - `def cancel(self, broker_order_id: str) -> None: ...`
  - `def open_orders(self) -> list[OrderAck]: ...`
  - `def positions(self) -> dict[str, int]: ...`
- 상단 docstring에 "Phase 1: only paper-mode adapters are usable. Any live adapter must explicitly raise."를 명시.

### 4.8 `projects/paper-trading/app/broker/paper.py`

- `class PaperBroker`:
  - `mode = TradingMode.PAPER`.
  - 내부 상태: `_open_orders: dict[str, OrderAck]`, `_positions: dict[str, int]`.
  - `submit(self, broker_order)`:
    - `broker_order.order_type == OrderType.LIMIT or OrderType.STOP_LIMIT`만 허용. 다른 타입은 `ValueError("market orders are disabled")`. (이중 가드 — RiskEngine이 이미 막지만 broker 단계에서도 fail closed.)
    - 새 `broker_order_id` 발급, `OrderAck`을 만든다.
    - 즉시 체결 시뮬레이션은 하지 않음(open 상태로 둠) — 단순 큐잉.
  - `cancel`, `open_orders`, `positions` 구현.
  - 호스트 환경에 따라 외부 호출 없음.

### 4.9 `projects/paper-trading/app/broker/alpaca_paper.py`

- `class AlpacaPaperBroker`:
  - `mode = TradingMode.PAPER`.
  - `__init__(self, settings: Settings)`:
    - `settings.alpaca_paper_api_base`가 비어있거나 `https://`로 시작하지 않으면 `RuntimeError("ALPACA_PAPER_API_BASE missing or invalid")` — fail closed.
    - `settings.alpaca_paper_key_id`/`secret_key`가 비어있으면 `RuntimeError("Alpaca paper credentials missing in .env")`.
  - `submit`/`cancel`/`open_orders`/`positions`: 본 단계에서는 `raise NotImplementedError("Alpaca Paper network calls are not implemented in Phase 1")`. 향후 연결 시 broker 내부에서만 HTTP 호출하도록 한다(현재는 stub).
  - 어떤 URL도 코드에 하드코딩하지 않는다.

### 4.10 `projects/paper-trading/app/risk_engine.py`

- `@dataclass class RiskDecision`: `approved: bool`, `reason: str`, `risk_token: str | None`.
- `class RiskEngine`:
  - `__init__(self, settings: Settings)`.
  - `def evaluate(self, intent: OrderIntent) -> RiskDecision`.
  - 규칙(모두 통과해야 `approved=True`, 하나라도 실패하면 즉시 거부):
    1. `settings.trading_mode == PAPER` (그렇지 않으면 거부).
    2. `settings.live_trading_enabled is False` (true면 거부).
    3. `intent.order_type in (LIMIT, STOP_LIMIT)` — market 거부.
    4. `intent.quantity > 0`.
    5. `intent.symbol` 이 `settings.symbol_allowlist` (비어있지 않은 경우)에 포함.
    6. `intent.quantity * intent.limit_price <= settings.max_order_notional_usd`.
    7. (선택) 향후 추가 규칙은 TODO 주석.
  - 통과 시 `risk_token`은 `secrets.token_hex(16)` 같은 무작위 토큰. RiskEngine 인스턴스가 발급한 토큰만 OMS가 받아들이도록 OMS에서 검증한다.
  - 거부 시 `risk_token=None`, `reason`에 사람이 읽을 수 있는 사유.

### 4.11 `projects/paper-trading/app/oms.py`

- `class OMS`:
  - `__init__(self, settings: Settings, risk: RiskEngine, broker: BrokerAdapter)`.
  - 내부에 `_issued_tokens: set[str]` — RiskEngine에서 받은 토큰을 등록하는 방식 대신, **OMS가 직접 RiskEngine을 호출**하는 흐름으로 단순화한다. 즉 외부에서 `oms.place(intent)`만 호출하면, OMS가 내부에서 `risk.evaluate(intent)`를 부르고 결과에 따라 broker로 보낸다. 이렇게 하면 외부 호출자가 RiskEngine을 우회할 코드 경로가 없다.
  - `def place(self, intent: OrderIntent) -> OrderAck`:
    1. `settings.live_trading_enabled is True`이면 `RuntimeError("OMS refuses live trading in Phase 1")`.
    2. `broker.mode != TradingMode.PAPER`이면 `RuntimeError("OMS rejects non-paper broker")`.
    3. `decision = risk.evaluate(intent)`.
    4. `decision.approved`가 False면 `RuntimeError(f"RiskEngine rejected: {decision.reason}")`.
    5. `Order`를 만들고 `BrokerOrder`로 승격한 뒤 `broker.submit(...)` 결과를 반환.
  - 어떤 다른 클래스도 `broker.submit`을 직접 부르지 않는다. (테스트에서만 broker 내부 동작을 검증.)

### 4.12 `projects/paper-trading/app/strategy.py`

- `class Strategy(ABC)`:
  - `@abstractmethod def generate_intents(self, market_snapshot) -> list[OrderIntent]: ...`
  - docstring에 "Strategies may only return OrderIntent. They must NEVER call OMS, BrokerAdapter, or RiskEngine directly. LLM/agent-driven strategies must also obey this contract."를 명시.
- `class NoopStrategy(Strategy)`:
  - `generate_intents` 항상 `[]` 반환.
  - Phase 2에서 실제 전략을 추가할 때 이 클래스를 참고.

### 4.13 `projects/paper-trading/app/api/server.py`

- FastAPI 인스턴스 생성, `GET /healthz` → `{"ok": true}`.
- `GET /paper/status` → 다음 JSON을 반환:

  ```json
  {
    "trading_mode": "paper",
    "live_enabled": false,
    "broker": "<adapter class name>",
    "broker_mode": "paper",
    "open_orders": <int>,
    "positions": <dict[str, int]>,
    "limits": {
      "max_order_notional_usd": <number>,
      "max_open_positions": <int>,
      "symbol_allowlist": [...]
    },
    "safety": {
      "market_orders_disabled": true,
      "risk_engine_required": true,
      "oms_only_execution": true
    }
  }
  ```

- API는 in-process로 OMS/PaperBroker 인스턴스를 들고 있는다. 시작 시 `load_settings()`를 호출하여 fail closed가 동작하도록 한다.
- 절대 주문을 받는 POST 엔드포인트를 만들지 않는다. (Phase 1은 read-only.)

### 4.14 `projects/paper-trading/app/main.py`

- `if __name__ == "__main__":`에서 uvicorn을 띄울 수 있는 진입점만 둔다.
- 자동 매매 루프는 시작하지 않는다. CLI 인자/실행 시 로그로 "Phase 1: read-only paper status only. No trading loop." 출력.

### 4.15 저장소 루트 `.gitignore`

- `projects/paper-trading/.env` 한 줄 추가. 이미 `.env`가 무시되도록 광범위한 룰이 있으면 중복 추가 불필요(확인 후 결정).

### 4.16 `projects/paper-trading/README.md`

- 모듈 개요(목표가 paper 자동매매 골격이라는 점).
- 디렉터리 구조 트리.
- 안전 규칙 요약(live 차단, 시장가 차단, RiskEngine 필수, OMS 단일 경로, agent 직접 주문 금지, `.env`에서만 키 로드, broker URL 추측 금지).
- 실행 방법: `python -m app.main`(자동 매매 없음), `uvicorn app.api.server:app --reload`(개발용).
- 테스트 방법: `python -m compileall app tests`, `python -m pytest -p no:cacheprovider`.
- Phase 2에서 할 일(시장 데이터 연결, 실제 Alpaca paper HTTP 호출, 매매 전략 구현, 알림). 단 모두 별도 작업으로.

### 4.17 테스트

각 테스트는 `pytest`로 실행 가능해야 하며 외부 네트워크를 호출하지 않는다.

- `tests/test_config.py`:
  - 기본 `Settings()`가 paper 모드, live=False여야 한다.
  - `TRADING_MODE=live`로 env를 흉내내면 `load_settings()`가 `ValueError`를 던진다 (monkeypatch).
  - `LIVE_TRADING_ENABLED=true`도 `ValueError`.

- `tests/test_models.py`:
  - `OrderIntent`에 quantity<=0, limit_price<=0, 소문자 symbol 넣으면 `ValueError`.

- `tests/test_risk_engine.py`:
  - 시장가는 거부 (LIMIT/STOP_LIMIT만 통과).
  - notional이 한도 초과면 거부.
  - allowlist에 없는 심볼 거부.
  - 통과 시 `risk_token`이 문자열이고 비어있지 않다.

- `tests/test_oms.py`:
  - live=True인 settings로 OMS를 만들면 `place`가 즉시 `RuntimeError`.
  - broker.mode가 LIVE인 가짜 어댑터를 주면 `place`가 `RuntimeError`.
  - RiskEngine이 거부하는 intent를 주면 `place`가 `RuntimeError`.
  - 정상 intent는 `OrderAck`을 반환하고 broker의 `_open_orders`에 들어간다.

- `tests/test_paper_broker.py`:
  - 시장가 BrokerOrder를 강제로 만들어 `submit`을 호출하면 `ValueError` (이중 가드).
  - 정상 LIMIT BrokerOrder는 ack를 만들고 open_orders에 들어간다.

- `tests/test_alpaca_paper_stub.py`:
  - `ALPACA_PAPER_API_BASE`가 비어있는 Settings로 `AlpacaPaperBroker(settings)` 호출 시 `RuntimeError`.
  - 임의 URL 값을 넣어 인스턴스화 후 `submit`을 호출하면 `NotImplementedError`.

- `tests/test_flow.py`:
  - `NoopStrategy`는 빈 리스트 반환 → OMS 호출 없음.
  - 수동으로 만든 intent를 OMS → PaperBroker로 흘려보내고 `/paper/status` 응답 형태에 맞는 in-memory 상태로 누적되는지 확인.

- `tests/test_api_paper_status.py`:
  - FastAPI `TestClient`로 `GET /paper/status` 호출, `trading_mode == "paper"`, `live_enabled is False`, `safety.market_orders_disabled is True`, `safety.risk_engine_required is True`, `safety.oms_only_execution is True`.
  - `GET /healthz` → 200 + `{"ok": true}`.

### 4.18 검증 명령

작업 디렉터리 `/root/ai-dev-center/projects/ai-team/projects/paper-trading`에서 다음을 실행한다.

```bash
python -m compileall app tests
python -m pytest -p no:cacheprovider
```

저장소 루트 `/root/ai-dev-center/projects/ai-team`에서:

```bash
git diff --stat
git status --short
```

세 명령 결과를 `docs/ai/jobs/mvp-003/patch.md`의 "Test Results"에 그대로 인용한다. `compileall`과 `pytest`는 종료코드 0이어야 한다. 만약 `fastapi`/`pytest`/`pydantic`/`httpx`가 미설치라 실패하면, 작업을 중단하고 `patch.md`의 "Remaining TODOs"에 "사람이 `pip install -e projects/paper-trading[dev]` 또는 `pip install fastapi uvicorn pydantic httpx pytest python-dotenv`를 직접 실행해야 함"으로 명시한다. `pip install`을 Codex가 직접 실행하지 않는다.

### 4.19 `docs/ai/jobs/mvp-003/patch.md`

`prompts/codex-implementer.md`의 출력 형식을 따른다.

```
## 1. Files Changed
## 2. Implementation Summary
## 3. Safety Confirmation
## 4. Test Results
## 5. Remaining TODOs
```

Safety Confirmation에는 다음 항목을 명시한다.

- live trading 코드 경로/플래그 활성화 없음.
- 실계좌 주문 코드 경로 없음 (Alpaca Paper는 stub).
- 시장가 주문 차단 (RiskEngine + PaperBroker 이중 가드).
- 모든 주문은 OMS만 broker.submit 호출.
- 모든 주문은 OMS가 내부에서 RiskEngine.evaluate를 호출 (외부 경로에서 우회 불가).
- Strategy는 OrderIntent만 반환. OMS/Broker/RiskEngine 직접 호출 없음.
- secrets/.env/auth/payment/migration/infra 미변경.
- broker endpoint URL 하드코딩 없음. `.env`에서만 로드.
- `git commit/push/merge/deploy` 자동화 없음.

Implementation Summary에는 다음 4가지를 별도 단락으로 정리한다(요청의 "완료 후" 항목과 일치).

1. 수정/추가된 파일 목록.
2. paper trading 경로(어떤 순서로 흐르는지 한 문장 흐름도): `Strategy → OrderIntent → OMS.place() → RiskEngine.evaluate() → BrokerAdapter.submit() (PaperBroker)`.
3. live trading 차단 메커니즘: `Settings.live_trading_enabled` 기본 False + `load_settings()` env 차단 + `OMS.place` 시작부 차단 + `RiskEngine.evaluate` 규칙 1·2번 + Alpaca live 어댑터 없음.
4. 실행한 테스트 목록과 결과 요약.

Remaining TODOs에는 Phase 2 후보를 명시한다(아래 §6 참고).

## 5. 테스트 기준

1. `python -m compileall app tests` 종료코드 0 (`projects/paper-trading` 내부에서 실행).
2. `python -m pytest -p no:cacheprovider` 종료코드 0, 위 8개 테스트 파일이 모두 수집·통과되며 외부 네트워크 호출이 없다.
3. `grep -RIn "market" projects/paper-trading/app` 결과에서 시장가 주문을 허용하는 코드 경로가 존재하지 않는다. (`OrderType` 열거형에 MARKET 없음, RiskEngine에 MARKET 통과 분기 없음.)
4. `grep -RIn "LIVE_TRADING_ENABLED.*[Tt]rue\|live_trading_enabled.*=.*True" projects/paper-trading/app` 결과 0건.
5. `grep -RIn "https://" projects/paper-trading/app` 결과에 broker 실제 URL이 하드코딩되어 있지 않다. (주석/문서 외에 코드 상수 없음.)
6. `git status --short` 결과에 `.env` 또는 secrets가 staged/untracked로 나타나지 않는다.
7. `git diff --stat`에 mvp-003 외 파일이 포함되어 있지 않다. (단, 저장소 루트 `.gitignore` 한 줄 추가는 허용.)
8. `/paper/status` 응답에 `live_enabled: false`, `safety.market_orders_disabled: true`, `safety.risk_engine_required: true`, `safety.oms_only_execution: true`가 포함된다.

## 6. 리뷰 체크리스트

- [ ] 신규 파일이 모두 `projects/paper-trading/` 아래에 있다. (저장소 루트 `.gitignore` 1줄 추가 외에는 기존 파일 수정 없음.)
- [ ] `Settings.live_trading_enabled` 기본값 False, `TradingMode.PAPER` 기본값.
- [ ] `load_settings()`가 `TRADING_MODE != paper` 또는 `LIVE_TRADING_ENABLED=true`에서 fail closed.
- [ ] `OrderType` 열거형에 MARKET 없음.
- [ ] `RiskEngine.evaluate`가 (1) paper 강제, (2) live 차단, (3) 시장가 거부, (4) 한도 초과 거부, (5) allowlist 검사를 수행한다.
- [ ] `OMS.place`가 외부 호출자에게 RiskEngine을 노출하지 않고 내부에서 호출한다. 외부에서 RiskEngine 우회가 불가능하다.
- [ ] `OMS.place` 시작부에서 live 차단, non-paper broker 차단.
- [ ] `PaperBroker.submit`이 LIMIT/STOP_LIMIT만 허용 (이중 가드).
- [ ] `AlpacaPaperBroker`는 env 미설정 시 fail closed, 실제 네트워크 호출 미구현(`NotImplementedError`).
- [ ] `Strategy`는 `OrderIntent`만 반환. OMS/Broker/RiskEngine을 호출하지 않는다.
- [ ] `/paper/status`가 read-only이며 `live_enabled=false`를 반환한다. 주문 생성 POST 엔드포인트 없음.
- [ ] `.env.example`에 실제 키가 없고 placeholder만 있다. `.env`는 무시된다.
- [ ] broker URL이 코드 상수가 아닌 env에서 로드된다.
- [ ] 테스트 8개가 모두 통과한다(또는 pytest 미설치를 patch.md에 명시).
- [ ] `patch.md` Implementation Summary에 (i) 변경 파일, (ii) paper trading 경로, (iii) live 차단 메커니즘, (iv) 테스트 결과가 모두 들어 있다.
- [ ] `git diff --stat`에 mvp-003 외 변경 없음.
- [ ] commit/push/merge/deploy 자동화 없음.

## (참고) Phase 2 이후 후보 — 이번 작업에서 만들지 않음

- 시장 데이터 연결 (예: Alpaca market data, Polygon 등 — env에서 endpoint 로드).
- Alpaca Paper HTTP 호출 실제 구현 (Adapter 내부에서만, RiskEngine/OMS는 그대로).
- 매매 전략 본체 (예: SMA crossover, mean reversion). Strategy 추상 계약을 그대로 따른다.
- 체결 시뮬레이션(시장가 슬리피지, 부분 체결, 호가창 모사).
- 포트폴리오/PnL 추적 + `/paper/portfolio` API.
- 알림(예: Slack) — webhook URL은 env에서만.
- 운영용 로깅/모니터링.
- live trading 활성화는 **별도 작업 + 명시적 사용자 승인 + arming/preflight/guard 절차** 후에만 검토. Phase 2 범위 아님.
