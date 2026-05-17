# Codex Task — mvp-003: Paper Trading 시스템 Phase 1 스캐폴딩

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-003/plan.md` and `docs/ai/jobs/mvp-003/request.ko.md` first. 그 후 이 파일의 지시에 따라 신규 디렉터리 `projects/paper-trading/`을 만든다.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-003`
- Job directory: `/root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-003`
- 대상 신규 디렉터리: `projects/paper-trading/` (저장소 루트 기준 신규 생성)
- 워크플로 문서: `docs/ai/CLAUDE_CODEX_WORKFLOW.md`
- 본 작업은 **Phase 1 스캐폴딩**만 한다. 실제 매매 전략, 시장 데이터 연결, Alpaca 네트워크 호출은 모두 Phase 2 이후의 별도 작업이다.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, API key, token 류 일체 변경/생성 금지(`.env.example`은 placeholder만).
- 시크릿, 실제 API 키, 실제 broker URL을 어떤 파일에도 하드코딩 금지.
- live trading 코드 경로/플래그 활성화 금지. `LIVE_TRADING_ENABLED=true`로 만들 수 있는 코드 경로 신설 금지.
- 실계좌(Alpaca Live 등) 어댑터 작성 금지. Alpaca Paper 어댑터도 네트워크 호출은 stub(`NotImplementedError`)만.
- 시장가(market) 주문 경로 신설 금지. `OrderType`에 MARKET 멤버 추가 금지.
- RiskEngine 우회 코드 경로 신설 금지. 외부 호출자가 RiskEngine을 건너뛰고 broker를 호출할 수 있는 길이 있으면 안 됨.
- Strategy/agent/LLM이 BrokerAdapter나 OMS를 직접 호출하는 코드 경로 신설 금지.
- 임의 shell 명령 입력 UI/API 신설 금지.
- 본 작업 범위 외 파일 변경 금지(저장소 루트 `.gitignore` 한 줄 추가는 허용).
- `pip install` 실행 금지. 호스트에 없는 패키지는 `patch.md`의 Remaining TODOs에 적어 사람에게 넘긴다.

## 수정 허용 위치

- 신규 디렉터리/파일: `projects/paper-trading/` 아래 전체.
- 기존 파일 수정 허용: 저장소 루트 `.gitignore`에 `projects/paper-trading/.env` 한 줄 추가만(이미 광범위한 `.env` 무시 규칙이 있으면 추가하지 않는다).
- 본 작업의 산출물: `docs/ai/jobs/mvp-003/patch.md`.

그 외 파일(예: `web/`, `prompts/`, `scripts/`, `docs/` 기타 파일, README.md, mvp-001/mvp-01/mvp-002 산출물)은 손대지 않는다.

## 디렉터리 구조 (신규 생성 대상)

```
projects/paper-trading/
├── README.md
├── pyproject.toml
├── pytest.ini                 # 또는 pyproject [tool.pytest.ini_options]만 사용해도 됨
├── .env.example
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── models.py
│   ├── risk_engine.py
│   ├── oms.py
│   ├── strategy.py
│   ├── main.py
│   ├── broker/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── paper.py
│   │   └── alpaca_paper.py
│   └── api/
│       ├── __init__.py
│       └── server.py
└── tests/
    ├── __init__.py
    ├── test_config.py
    ├── test_models.py
    ├── test_risk_engine.py
    ├── test_oms.py
    ├── test_paper_broker.py
    ├── test_alpaca_paper_stub.py
    ├── test_flow.py
    └── test_api_paper_status.py
```

## 구현 작업

### 1) `pyproject.toml`

- 빌드 시스템은 `setuptools` 또는 `hatchling` 중 표준 하나.
- `name = "paper-trading"`, `version = "0.1.0"`, `requires-python = ">=3.10"`.
- 기본 의존성: `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `python-dotenv`.
- 옵션 의존성 `[project.optional-dependencies] dev = ["pytest", "httpx"]`.
- `[tool.pytest.ini_options]`에 `testpaths = ["tests"]`, `addopts = "-p no:cacheprovider"`를 둔다(또는 `pytest.ini`에 동일 내용).
- 패키지 경로: `packages = ["app"]` 또는 setuptools auto-discovery.

### 2) `.env.example`

```
TRADING_MODE=paper
LIVE_TRADING_ENABLED=false
# Alpaca Paper trading의 공식 base URL을 사용자가 직접 .env에 적는다. 이 저장소는 URL을 추측하지 않는다.
ALPACA_PAPER_API_BASE=
ALPACA_PAPER_KEY_ID=
ALPACA_PAPER_SECRET_KEY=
PAPER_STARTING_CASH=100000
MAX_ORDER_NOTIONAL_USD=5000
MAX_OPEN_POSITIONS=20
SYMBOL_ALLOWLIST=AAPL,MSFT,GOOG,AMZN,NVDA
```

### 3) `.gitignore`

```
.env
__pycache__/
.pytest_cache/
*.egg-info/
.coverage
.venv/
dist/
build/
```

### 4) `app/config.py`

- `TradingMode(str, Enum)`: `PAPER = "paper"`, `LIVE = "live"`.
- `Settings` (frozen dataclass):
  - `trading_mode: TradingMode = TradingMode.PAPER`
  - `live_trading_enabled: bool = False`
  - `alpaca_paper_api_base: str | None = None`
  - `alpaca_paper_key_id: str | None = None`
  - `alpaca_paper_secret_key: str | None = None`
  - `paper_starting_cash: Decimal = Decimal("100000")`
  - `max_order_notional_usd: Decimal = Decimal("5000")`
  - `max_open_positions: int = 20`
  - `symbol_allowlist: tuple[str, ...] = ()`
- `load_settings() -> Settings`:
  - `dotenv.load_dotenv()` 호출. 파일 없어도 OK.
  - env에서 위 값을 읽어 정규화.
  - `TRADING_MODE`가 `paper`가 아니면 `ValueError("Phase 1 only supports paper trading")`.
  - `LIVE_TRADING_ENABLED`가 `"true"`/`"1"`/`"yes"`(대소문자 무시)이면 `ValueError("Live trading is disabled in Phase 1")`.
  - `symbol_allowlist`는 콤마 split + strip + upper → tuple.

### 5) `app/models.py`

- `Side(str, Enum)`: `BUY = "buy"`, `SELL = "sell"`.
- `OrderType(str, Enum)`: `LIMIT = "limit"`, `STOP_LIMIT = "stop_limit"`. **MARKET 멤버 추가 금지.**
- frozen dataclass:
  - `OrderIntent`: `symbol: str`, `side: Side`, `quantity: int`, `order_type: OrderType`, `limit_price: Decimal`, `stop_price: Decimal | None = None`, `client_tag: str | None = None`. `__post_init__`에서 `quantity > 0`, `limit_price > 0`, `symbol == symbol.upper()` 검증.
  - `Order`: `OrderIntent` 필드 + `risk_token: str`, `created_at: datetime`.
  - `BrokerOrder`: `Order` 필드 + `oms_id: str`, `submitted_at: datetime`.
  - `OrderAck`: `oms_id: str`, `broker_order_id: str | None`, `status: str`, `mode: TradingMode`.

### 6) `app/broker/base.py`

- `class BrokerAdapter(Protocol)` (혹은 ABC):
  - `mode: TradingMode`
  - `def submit(self, broker_order: BrokerOrder) -> OrderAck: ...`
  - `def cancel(self, broker_order_id: str) -> None: ...`
  - `def open_orders(self) -> list[OrderAck]: ...`
  - `def positions(self) -> dict[str, int]: ...`
- 상단 docstring: "Phase 1: only paper-mode adapters are usable. Any live adapter MUST raise."

### 7) `app/broker/paper.py`

- `class PaperBroker`:
  - `mode = TradingMode.PAPER`.
  - 내부 상태: `self._open_orders: dict[str, OrderAck] = {}`, `self._positions: dict[str, int] = {}`.
  - `submit(self, broker_order)`:
    - `if broker_order.order_type not in (OrderType.LIMIT, OrderType.STOP_LIMIT): raise ValueError("market orders are disabled")` — 이중 가드.
    - `broker_order_id = secrets.token_hex(8)` 발급.
    - `OrderAck(oms_id=..., broker_order_id=..., status="accepted", mode=TradingMode.PAPER)` 생성, `self._open_orders[broker_order_id] = ack`.
    - 자동 체결/포지션 변동 모사는 하지 않는다(open 상태로 유지).
  - `cancel`, `open_orders()`, `positions()` 단순 구현.
- 네트워크 호출 없음.

### 8) `app/broker/alpaca_paper.py`

- `class AlpacaPaperBroker`:
  - `mode = TradingMode.PAPER`.
  - `__init__(self, settings: Settings)`:
    - `base = settings.alpaca_paper_api_base`. `base`가 빈 값이거나 `https://`로 시작하지 않으면 `RuntimeError("ALPACA_PAPER_API_BASE missing or invalid; set it in .env")`.
    - `settings.alpaca_paper_key_id`/`secret_key` 둘 중 하나라도 빈 값이면 `RuntimeError("Alpaca paper credentials missing in .env")`.
  - `submit`/`cancel`/`open_orders`/`positions`: 본 단계에서 `raise NotImplementedError("Alpaca Paper network calls are not implemented in Phase 1")`.
- **어떤 URL/엔드포인트도 코드에 상수로 적지 않는다.** 항상 `settings.alpaca_paper_api_base`에서 읽는다.

### 9) `app/risk_engine.py`

- `@dataclass class RiskDecision`: `approved: bool`, `reason: str`, `risk_token: str | None`.
- `class RiskEngine`:
  - `__init__(self, settings: Settings)`.
  - `evaluate(self, intent: OrderIntent) -> RiskDecision`:
    1. `settings.trading_mode != TradingMode.PAPER` → reject.
    2. `settings.live_trading_enabled` → reject.
    3. `intent.order_type not in (OrderType.LIMIT, OrderType.STOP_LIMIT)` → reject.
    4. `intent.quantity <= 0` → reject.
    5. `settings.symbol_allowlist` (비어있지 않으면) `intent.symbol not in allowlist` → reject.
    6. `intent.quantity * intent.limit_price > settings.max_order_notional_usd` → reject.
    7. 모두 통과 시 `risk_token = secrets.token_hex(16)`, `RiskDecision(approved=True, reason="ok", risk_token=token)` 반환.
  - 거부 시 `reason`은 사람이 읽을 수 있는 문구.

### 10) `app/oms.py`

- `class OMS`:
  - `__init__(self, settings: Settings, risk: RiskEngine, broker: BrokerAdapter)`.
  - `place(self, intent: OrderIntent) -> OrderAck`:
    1. `if self._settings.live_trading_enabled: raise RuntimeError("OMS refuses live trading in Phase 1")`.
    2. `if self._broker.mode != TradingMode.PAPER: raise RuntimeError("OMS rejects non-paper broker")`.
    3. `decision = self._risk.evaluate(intent)`.
    4. `if not decision.approved: raise RuntimeError(f"RiskEngine rejected: {decision.reason}")`.
    5. `order = Order(... risk_token=decision.risk_token, created_at=datetime.utcnow())`.
    6. `oms_id = secrets.token_hex(8)`.
    7. `broker_order = BrokerOrder(..., oms_id=oms_id, submitted_at=datetime.utcnow())`.
    8. `return self._broker.submit(broker_order)`.
  - 외부 호출자에게 `risk`/`broker` 인스턴스를 노출하지 않는다(getter 만들지 않음). RiskEngine 우회 경로 차단.

### 11) `app/strategy.py`

- `class Strategy(ABC)`:
  - `@abstractmethod def generate_intents(self, market_snapshot: Any) -> list[OrderIntent]: ...`
  - docstring: "Strategies MUST only return OrderIntent. They MUST NEVER call OMS, BrokerAdapter, or RiskEngine directly. This applies equally to LLM/agent-driven strategies."
- `class NoopStrategy(Strategy)`:
  - `generate_intents(self, _market_snapshot)` → `[]`.

### 12) `app/api/server.py`

- FastAPI 인스턴스 + 두 라우트.
- 앱 시작 시 `settings = load_settings()`. `RiskEngine(settings)`, `PaperBroker()`, `OMS(settings, risk, broker)`를 module-level 또는 dependency로 만든다.
- `GET /healthz` → `{"ok": True}`.
- `GET /paper/status`:

  ```python
  {
      "trading_mode": settings.trading_mode.value,
      "live_enabled": settings.live_trading_enabled,
      "broker": type(broker).__name__,
      "broker_mode": broker.mode.value,
      "open_orders": len(broker.open_orders()),
      "positions": broker.positions(),
      "limits": {
          "max_order_notional_usd": float(settings.max_order_notional_usd),
          "max_open_positions": settings.max_open_positions,
          "symbol_allowlist": list(settings.symbol_allowlist),
      },
      "safety": {
          "market_orders_disabled": True,
          "risk_engine_required": True,
          "oms_only_execution": True,
      },
  }
  ```

- POST 엔드포인트(주문 생성/취소)는 만들지 않는다. Phase 1은 read-only.

### 13) `app/main.py`

```python
def main() -> None:
    print("Phase 1: read-only paper status only. No trading loop will be started.")
    print("Run the read-only API with: uvicorn app.api.server:app --reload")

if __name__ == "__main__":
    main()
```

자동 매매 루프는 시작하지 않는다.

### 14) `README.md`

다음을 포함한다.

- 모듈 목적(paper trading 골격, Phase 1).
- 디렉터리 트리.
- 안전 규칙 요약(live 차단, 시장가 차단, RiskEngine 필수, OMS 단일 경로, agent 직접 주문 금지, `.env`에서만 키 로드, broker URL 추측 금지).
- 실행 방법: `python -m app.main` (자동 매매 없음 안내), `uvicorn app.api.server:app --reload --port 8001` (개발용 read-only API).
- 테스트 방법: `python -m compileall app tests`, `python -m pytest -p no:cacheprovider`.
- Phase 2 후보(시장 데이터, Alpaca HTTP 실제 구현, 매매 전략, 체결 시뮬레이션, 포트폴리오/PnL, 알림). 모두 별도 작업.

### 15) 저장소 루트 `.gitignore`

- 기존 파일에 이미 `.env`를 광범위하게 무시하면 변경하지 않는다.
- 없으면 `projects/paper-trading/.env` 한 줄만 추가한다.

### 16) 테스트 (`tests/`)

`plan.md` §4.17의 8개 테스트 파일을 모두 만든다. 외부 네트워크 호출 없음. `pytest`로 수집 가능해야 한다.

요약:

- `test_config.py`: 기본값 paper/false, env로 live 시도 시 `ValueError`.
- `test_models.py`: 잘못된 quantity/price/symbol에 `ValueError`.
- `test_risk_engine.py`: market reject, notional over reject, allowlist 외 reject, 정상 시 risk_token 발급.
- `test_oms.py`: live=True인 settings → `RuntimeError`, non-paper broker → `RuntimeError`, RiskEngine 거부 시 `RuntimeError`, 정상 시 `OrderAck` 반환 + `_open_orders`에 등록.
- `test_paper_broker.py`: 강제로 만든 market BrokerOrder → `ValueError` (이중 가드). LIMIT는 정상.
- `test_alpaca_paper_stub.py`: env 미설정 → `RuntimeError`. 임의 https URL/키 채우고 인스턴스화한 뒤 `submit` 호출 → `NotImplementedError`.
- `test_flow.py`: `NoopStrategy.generate_intents()` → `[]`. 수동 intent를 OMS에 흘려보내고 PaperBroker `open_orders`에 누적 확인.
- `test_api_paper_status.py`: FastAPI `TestClient`로 `/healthz`, `/paper/status` 검증. `live_enabled=False`, `safety.market_orders_disabled=True`, `safety.risk_engine_required=True`, `safety.oms_only_execution=True`.

### 17) `docs/ai/jobs/mvp-003/patch.md`

`prompts/codex-implementer.md`의 형식을 따르되, Implementation Summary는 다음 4개 단락을 분리해서 적는다(요청의 "완료 후" 항목과 1:1 대응).

```markdown
## 1. Files Changed

(생성/수정한 파일 목록. projects/paper-trading/ 하위 + 저장소 루트 .gitignore 추가 여부)

## 2. Implementation Summary

### 2.1 수정/추가된 파일

(목록 + 한 줄 설명)

### 2.2 paper trading 경로

Strategy.generate_intents() → OrderIntent → OMS.place(intent) → RiskEngine.evaluate(intent) → BrokerOrder → PaperBroker.submit() → OrderAck
- 외부 호출자는 OMS만 호출 가능. RiskEngine은 OMS 내부에서 호출. BrokerAdapter는 OMS만 호출.
- Strategy는 OrderIntent만 반환하며 OMS/Risk/Broker를 직접 호출하지 않는다.

### 2.3 live trading 차단 메커니즘

- Settings.live_trading_enabled 기본 False.
- load_settings()가 TRADING_MODE!=paper 또는 LIVE_TRADING_ENABLED=true에서 ValueError(fail closed).
- OMS.place 시작부에서 live_trading_enabled True면 RuntimeError.
- OMS.place에서 broker.mode!=PAPER면 RuntimeError.
- RiskEngine.evaluate가 (trading_mode!=PAPER) 또는 (live_trading_enabled)에서 reject.
- Alpaca Live 어댑터 미존재. AlpacaPaperBroker는 네트워크 NotImplementedError.

### 2.4 실행한 테스트

- python -m compileall app tests : 결과
- python -m pytest -p no:cacheprovider : 결과(통과 테스트 수, 실패 시 사유)

## 3. Safety Confirmation

(plan.md §4.19의 9개 체크 항목을 그대로 확인)

## 4. Test Results

- python -m compileall app tests: <결과>
- python -m pytest -p no:cacheprovider: <결과>
- git diff --stat: <결과>
- git status --short: <결과>

## 5. Remaining TODOs

(Phase 2 후보 + 호스트에 패키지가 없어 직접 pip install이 필요했던 경우 명시)
```

## 검증 명령

신규 프로젝트 디렉터리 `projects/paper-trading/`에서 실행:

```bash
python -m compileall app tests
python -m pytest -p no:cacheprovider
```

저장소 루트 `/root/ai-dev-center/projects/ai-team`에서 실행:

```bash
git diff --stat
git status --short
```

네 명령 결과를 `patch.md`의 "Test Results"에 그대로 인용한다. `compileall`과 `pytest`는 종료코드 0이어야 한다. 의존성 미설치로 실패하면 `pip install`을 Codex가 직접 실행하지 말고, 작업을 멈춘 뒤 `patch.md` Remaining TODOs에 "사람이 `pip install fastapi 'uvicorn[standard]' 'pydantic>=2' python-dotenv pytest httpx`를 실행해야 함"으로 적는다.

## 완료 정의 (Done)

- `projects/paper-trading/` 디렉터리에 `app/`, `tests/`, 설정 파일이 모두 생성됨.
- `OrderType`에 MARKET 없음(`grep -RIn "MARKET" projects/paper-trading/app` 결과 0건; 또는 주석으로만 나오고 코드 상수로는 없음).
- `LIVE_TRADING_ENABLED=true` 또는 `live_trading_enabled = True`로 만드는 코드 경로 없음(`grep` 확인).
- broker URL 코드 상수 없음(`grep -RIn "paper-api.alpaca\|https://" projects/paper-trading/app`이 빈 결과거나 주석만).
- `/paper/status` 응답에 `live_enabled: false`, `safety` 블록 포함.
- `python -m compileall app tests`와 `python -m pytest -p no:cacheprovider` 모두 종료코드 0(또는 Remaining TODOs에 사유 명시).
- `git diff --stat`에 mvp-003 외 변경 없음(루트 `.gitignore` 한 줄 추가 외).
- `.env`가 staged/committed되지 않음(`git status --short` 확인).
- `patch.md` 5섹션 완성.
- commit/push/merge/deploy 자동화 없음.
