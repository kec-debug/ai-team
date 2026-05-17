## 1. 요청 요약

미국주식 페이퍼매매 시스템의 **첫 번째 전략** "프리마켓 갭 + 거래량 돌파"를 구현한다. paper trading 전용이며 live trading은 절대 활성화하지 않는다.

### 현재 상태 — 매우 중요

mvp-003에서 paper trading 시스템 스캐폴딩이 **계획됐지만 실제로 만들어지지 않았다.** (mvp-003 review 결과: BLOCK. `projects/paper-trading/` 디렉터리 미존재.) mvp-005 요청은 `app/strategy/`, `app/runtime/paper_runner.py`, `app/api/routes.py`, `app/domain/`, `app/risk/` 같은 경로에 작업하라고 명시하지만 그 경로들도 존재하지 않는다.

요청문 자체에 "단, 실제 구조가 다르면 현재 프로젝트 구조에 맞춰 최소 수정해줘"라고 적혀 있고, 사용자가 mvp-003에서 이미 "ai-team 하위에 새 Python 프로젝트 스캐폴딩"을 선택했으므로, 본 작업은 **mvp-003의 미실행 스캐폴딩 + mvp-005의 전략 구현을 한 번에 묶어** 다음 위치에 만든다.

- 대상 루트: `projects/paper-trading/`
- 모듈 구조: mvp-005 요청의 경로 명세를 그대로 사용(`app/strategy/`, `app/runtime/`, `app/api/`, `app/domain/`, `app/risk/`, `app/oms/`, `app/broker/`). mvp-003의 단일 파일 구조(`app/oms.py`, `app/risk_engine.py`)는 사용하지 않는다.

요청문에 "승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해"가 명시되어 있으므로, 사용자 추가 확인 없이 위 통합 계획으로 진행한다.

### 핵심 절대 조건 (요청 + `prompts/claude.md` 안전 규칙)

- live trading 코드 경로/플래그 활성화 금지. `LIVE_TRADING_ENABLED=false` 기본값이자 Phase 1 상수.
- 실계좌 주문 코드 경로 신설 금지. Alpaca 어댑터는 stub만(네트워크 호출 미구현).
- 시장가(market) 주문 절대 금지. `OrderType`에 MARKET 멤버 없음. RiskEngine + PaperBroker + Strategy 모두에서 차단.
- 모든 주문은 `Strategy → RiskEngine → OMS → BrokerAdapter` 순서를 통과. 외부 호출자가 OMS·RiskEngine·BrokerAdapter를 우회할 수 있는 길 없음.
- Strategy는 비실행성 `OrderIntent`만 만든다. 실행성 `BrokerOrder`는 OMS만 만든다.
- agent/LLM이 OMS, BrokerAdapter, RiskEngine을 직접 호출하지 않는다. Strategy도 마찬가지.
- API key는 `.env`에서만 읽는다. 저장소에는 `.env.example`만(placeholder).
- broker endpoint URL은 코드에 하드코딩하지 않는다. 모르면 `.env`에서 로드, 없으면 fail closed.
- `git commit`, `git push`, PR merge, deploy 자동화 금지.

### 검증 명령

```bash
# projects/paper-trading 디렉터리에서
python -m compileall app tests
python -m pytest -p no:cacheprovider

# 저장소 루트에서
git diff --stat
git status --short
```

호스트에 `fastapi`/`pytest`/`pydantic`/`httpx`/`python-dotenv`가 없으면 Codex는 `pip install`을 직접 실행하지 말고 `patch.md` Remaining TODOs에 사람이 실행할 명령을 적는다.

## 2. 작업 범위

### 포함 (In scope)

`projects/paper-trading/` 아래 신규 생성:

- 패키지 메타: `README.md`, `pyproject.toml`, `pytest.ini`(또는 pyproject `[tool.pytest.ini_options]`), `.env.example`, `.gitignore`.
- `app/config.py` — `Settings`, `TradingMode`, `Session`, `load_settings()`(live 차단 fail closed).
- `app/domain/` 패키지
  - `enums.py` — `TradingMode`, `Side`, `OrderType`(LIMIT, STOP_LIMIT만), `Session`(PRE_MARKET, REGULAR, AFTER_HOURS, CLOSED).
  - `orders.py` — `OrderIntent`, `Order`, `BrokerOrder`, `OrderAck`.
  - `market.py` — `StrategyInput`(시장 스냅샷 스키마), 보조 dataclass.
- `app/broker/` 패키지
  - `base.py` — `BrokerAdapter` Protocol.
  - `paper.py` — `PaperBroker`(in-memory).
  - `alpaca_paper.py` — `AlpacaPaperBroker` stub(env 미설정 fail closed, 네트워크 미구현).
- `app/risk/` 패키지
  - `engine.py` — `RiskEngine` + `RiskDecision`.
- `app/oms/` 패키지
  - `manager.py` — `OMS`(내부에서만 RiskEngine 호출, broker.submit 단일 경로).
- `app/strategy/` 패키지
  - `base.py` — `Strategy` ABC + `StrategyResult` 스키마.
  - `inputs.py` — `StrategyInput` 재export 또는 추가 헬퍼.
  - `premarket_gap.py` — `PremarketGapVolumeBreakoutStrategy` 본체.
  - `__init__.py` — 등록 helper(이름→인스턴스).
- `app/runtime/` 패키지
  - `paper_runner.py` — `PaperRunner.run_once(snapshots)` — 스냅샷 리스트를 Strategy → OMS로 흘려보내고 결과 집계.
- `app/api/` 패키지
  - `routes.py` — `GET /paper/status`, `GET /healthz`, `POST /paper/run`.
  - `server.py` — FastAPI app + lifespan에서 `load_settings()` 호출 및 인스턴스 와이어링.
- `app/main.py` — uvicorn 진입점(자동 매매 루프 시작하지 않음, 안내만 출력).
- `tests/` 패키지 — 기반 테스트(config/models/risk/oms/paper_broker/alpaca_stub/flow/api_status) + 전략 테스트(premarket_gap) + 러너 테스트(paper_runner) + `/paper/run` 엔드포인트 테스트.
- 저장소 루트 `.gitignore`에 `projects/paper-trading/.env` 한 줄 추가(이미 광범위한 `.env` 무시 룰이 있으면 추가하지 않음).
- `docs/ai/jobs/mvp-005/patch.md` 작성.

### 제외 (Out of scope; 절대 만지지 않음)

- 실계좌(Alpaca Live 등) 어댑터.
- live trading 활성화 토글/플래그.
- 시장가(market) 주문 경로.
- 실제 Alpaca/외부 broker 네트워크 호출(stub만).
- 실시간 시장 데이터 수집 파이프라인(스냅샷은 호출자가 제공).
- 잔액/세금/체결 슬리피지 정밀 모델링.
- 매매 전략 추가(이번 작업은 premarket gap 한 가지만).
- 알림/Slack/이메일 통합.
- `web/` GUI 변경 (mvp-005 범위 밖).
- `prompts/`, `scripts/`, 기존 `docs/` 파일 변경(`docs/ai/jobs/mvp-005/`만 예외).
- `.env`, secrets, credentials, API key, token.
- auth/login/session, payment/billing, database migration, production infra.
- `.github/workflows/` 변경, CI/CD 파이프라인 신설.
- `git commit`, `git push`, PR 생성/머지, 배포 자동화.
- 임의 shell 실행 기능.
- mvp-001/mvp-01/mvp-002/mvp-003/mvp-004 산출물 변경.

### 안전 가드 (Codex가 작업 중 항상 지켜야 할 것)

- 모든 신규 파일은 `projects/paper-trading/` 아래에만 만든다. 기존 파일 수정은 저장소 루트 `.gitignore` 한 줄 추가만.
- 신규 의존성은 `pyproject.toml`에만 선언한다. `pip install` 실행 금지.
- 어떤 코드에도 시크릿/실제 API 키/실제 URL 하드코딩 금지.
- live 주문을 만들 수 있는 코드 경로 신설 금지.
- Strategy 클래스가 OMS·BrokerAdapter·RiskEngine을 직접 호출/임포트하면 검토에서 reject. Strategy는 `app/domain/`의 모델과 자기 자신만 의존.
- OMS 외부 인터페이스에서 RiskEngine 인스턴스가 노출되지 않는다(getter 만들지 않음, `_risk` 비공개).
- `POST /paper/run`은 **caller-provided OrderIntent를 받지 않는다.** 스냅샷만 받고, 내부 Strategy → OMS로 흘린다.

## 3. 수정해야 할 파일

신규 생성(전부 `projects/paper-trading/` 아래):

| 파일 | 목적 |
| --- | --- |
| `README.md` | 모듈 개요, 안전 규칙, 실행/테스트, 환경변수, 전략 설명 |
| `pyproject.toml` | 패키지 메타 + 의존성(`fastapi`, `uvicorn[standard]`, `pydantic>=2`, `python-dotenv`) + dev(`pytest`, `httpx`) |
| `pytest.ini` 또는 pyproject 설정 | testpaths, `-p no:cacheprovider` |
| `.env.example` | 환경변수 템플릿(placeholder만) |
| `.gitignore` | `.env`, `__pycache__/`, `.pytest_cache/` 등 |
| `app/__init__.py` | 패키지 마커 |
| `app/config.py` | `Settings`, `load_settings`, `TradingMode`/`Session` re-export 가능 |
| `app/main.py` | 자동 매매 미시작, 안내만 |
| `app/domain/__init__.py` | 마커 |
| `app/domain/enums.py` | `TradingMode`, `Side`, `OrderType`, `Session` |
| `app/domain/orders.py` | `OrderIntent`, `Order`, `BrokerOrder`, `OrderAck` |
| `app/domain/market.py` | `StrategyInput` |
| `app/broker/__init__.py` | 마커 |
| `app/broker/base.py` | `BrokerAdapter` Protocol |
| `app/broker/paper.py` | `PaperBroker` |
| `app/broker/alpaca_paper.py` | `AlpacaPaperBroker` stub |
| `app/risk/__init__.py` | 마커 |
| `app/risk/engine.py` | `RiskEngine`, `RiskDecision` |
| `app/oms/__init__.py` | 마커 |
| `app/oms/manager.py` | `OMS` |
| `app/strategy/__init__.py` | `Strategy` re-export + registry helper |
| `app/strategy/base.py` | `Strategy` ABC + `StrategyResult` |
| `app/strategy/inputs.py` | `StrategyInput` re-export |
| `app/strategy/premarket_gap.py` | `PremarketGapVolumeBreakoutStrategy` |
| `app/runtime/__init__.py` | 마커 |
| `app/runtime/paper_runner.py` | `PaperRunner.run_once(snapshots)` |
| `app/api/__init__.py` | 마커 |
| `app/api/server.py` | FastAPI app + lifespan + 라우터 마운트 |
| `app/api/routes.py` | `/healthz`, `/paper/status`, `/paper/run` |
| `tests/__init__.py` | 마커 |
| `tests/test_config.py` | paper 강제, live 차단 |
| `tests/test_models.py` | 모델 불변식 |
| `tests/test_risk_engine.py` | market reject, notional, allowlist, paper 강제 |
| `tests/test_oms.py` | live 차단, non-paper broker 차단, risk reject, 정상 흐름 |
| `tests/test_paper_broker.py` | 시장가 거부 이중 가드, LIMIT 정상 |
| `tests/test_alpaca_paper_stub.py` | env 미설정 fail closed, 네트워크 미구현 |
| `tests/test_flow.py` | Strategy → OMS → PaperBroker 통합 |
| `tests/test_api_paper_status.py` | `/paper/status` 안전 플래그, `/healthz` |
| `tests/test_strategy_premarket_gap.py` | **10개 전략 테스트** |
| `tests/test_paper_runner.py` | blocked candidate가 OMS로 가지 않음 등 |

기존 파일 변경:

| 파일 | 변경 내용 |
| --- | --- |
| `.gitignore` (저장소 루트) | `projects/paper-trading/.env` 1줄 추가(필요 시) |
| `docs/ai/jobs/mvp-005/patch.md` | Codex 변경 요약 |

## 4. Codex 구현 지시문

> Codex는 다음 지시를 그대로 따른다. 범위 확장 금지. 안전 규칙 우선.

### 4.1 사전 조건

- 작업 루트: `/root/ai-dev-center/projects/ai-team`.
- 신규 코드는 모두 `projects/paper-trading/` 아래에만 만든다.
- 기존 파일 수정은 저장소 루트 `.gitignore` 1줄 추가 외에는 없다.
- `web/`, `prompts/`, `scripts/`, `examples/`, `docs/` (mvp-005 job dir 제외), `docs/ai/jobs/mvp-001..mvp-004/`는 손대지 않는다.
- `git commit`, `git push`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, API key, token, auth, payment, DB migration, production infra 절대 금지.
- `pip install` 실행 금지.

### 4.2 패키지 메타 (`pyproject.toml`, `.env.example`, `.gitignore`, `pytest.ini`)

- `pyproject.toml`: `setuptools` 빌드, `name = "paper-trading"`, `version = "0.1.0"`, `requires-python = ">=3.10"`. 의존성 `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `python-dotenv`. dev `pytest`, `httpx`. `[tool.pytest.ini_options]`에 `testpaths = ["tests"]`, `addopts = "-p no:cacheprovider"`.
- `.env.example` (placeholder만, 실제 키 금지):

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
  STRATEGY_PREMARKET_GAP_MIN_PCT=0.05
  STRATEGY_PREMARKET_MIN_VOLUME=100000
  STRATEGY_PREMARKET_MAX_SPREAD_PCT=0.003
  STRATEGY_PREMARKET_MAX_QUOTE_AGE_SECONDS=60
  STRATEGY_PREMARKET_MIN_RELATIVE_VOLUME=1.5
  STRATEGY_PREMARKET_BREAKOUT_TOLERANCE_PCT=0.001
  ```

- `.gitignore`(프로젝트): `.env`, `__pycache__/`, `.pytest_cache/`, `*.egg-info/`, `.coverage`, `.venv/`, `dist/`, `build/`.

### 4.3 `app/config.py`

- `class TradingMode(str, Enum): PAPER="paper"; LIVE="live"`.
- `class Session(str, Enum): PRE_MARKET="pre_market"; REGULAR="regular"; AFTER_HOURS="after_hours"; CLOSED="closed"`.
- frozen dataclass `Settings`:
  - `trading_mode: TradingMode = TradingMode.PAPER`
  - `live_trading_enabled: bool = False`
  - `alpaca_paper_api_base: str | None = None`
  - `alpaca_paper_key_id: str | None = None`
  - `alpaca_paper_secret_key: str | None = None`
  - `paper_starting_cash: Decimal = Decimal("100000")`
  - `max_order_notional_usd: Decimal = Decimal("5000")`
  - `max_open_positions: int = 20`
  - `symbol_allowlist: tuple[str, ...] = ()`
  - `premarket_gap_min_pct: Decimal = Decimal("0.05")`
  - `premarket_min_volume: int = 100_000`
  - `premarket_max_spread_pct: Decimal = Decimal("0.003")`
  - `premarket_max_quote_age_seconds: int = 60`
  - `premarket_min_relative_volume: Decimal = Decimal("1.5")`
  - `premarket_breakout_tolerance_pct: Decimal = Decimal("0.001")`
- `load_settings() -> Settings`:
  - `dotenv.load_dotenv()` 호출.
  - `TRADING_MODE != "paper"` → `ValueError("Phase 1 only supports paper trading")`.
  - `LIVE_TRADING_ENABLED ∈ {"true","1","yes","on"}` (대소문자 무시) → `ValueError("Live trading is disabled in Phase 1")`.
  - 모든 Decimal 환경변수는 안전 변환. 잘못된 형식이면 `ValueError`.

### 4.4 `app/domain/enums.py`, `app/domain/orders.py`, `app/domain/market.py`

`enums.py`: `TradingMode`, `Side(BUY,SELL)`, `OrderType(LIMIT, STOP_LIMIT)` — **MARKET 멤버 추가 금지**.

`orders.py` frozen dataclasses:

- `OrderIntent`: `symbol`, `side`, `quantity`, `order_type`, `limit_price`, `stop_price=None`, `client_tag=None`. `__post_init__`에서 `quantity > 0`, `limit_price > 0`, `symbol == symbol.upper()` 검증.
- `Order`: `OrderIntent` 필드 + `risk_token: str`, `created_at: datetime`.
- `BrokerOrder`: `Order` 필드 + `oms_id: str`, `submitted_at: datetime`.
- `OrderAck`: `oms_id: str`, `broker_order_id: str | None`, `status: str`, `mode: TradingMode`.

`market.py`:

- `class StrategyInput(BaseModel)` (pydantic v2):
  - `symbol: str`, `market: str`, `session: Session`, `previous_close: Decimal`, `current_price: Decimal`, `premarket_high: Decimal`, `premarket_volume: int`, `bid: Decimal`, `ask: Decimal`, `timestamp: datetime`, `relative_volume: Decimal | None = None`.
  - validator: symbol 대문자, quantity/price 양수성 검사 등.

### 4.5 `app/broker/base.py`, `paper.py`, `alpaca_paper.py`

`base.py`: `BrokerAdapter(Protocol)` with `mode`, `submit`, `cancel`, `open_orders`, `positions`. docstring에 "Phase 1: only paper-mode adapters are usable."

`paper.py`: `PaperBroker`. `mode = TradingMode.PAPER`. `submit`에서 `order_type not in (LIMIT, STOP_LIMIT)` → `ValueError("market orders are disabled")`. `broker_order_id = secrets.token_hex(8)`. open_orders에 추가. 체결 시뮬레이션 없음.

`alpaca_paper.py`: `AlpacaPaperBroker(settings)`. base URL이 빈 값이거나 `https://`로 시작하지 않으면 `RuntimeError`. credentials 누락 시 `RuntimeError`. `submit`/`cancel`/`open_orders`/`positions` 모두 `NotImplementedError("Alpaca Paper network calls are not implemented in Phase 1")`. URL 하드코딩 금지.

### 4.6 `app/risk/engine.py`

- `@dataclass class RiskDecision`: `approved: bool`, `reason: str`, `risk_token: str | None`.
- `class RiskEngine`:
  - `__init__(self, settings)`.
  - `evaluate(self, intent: OrderIntent) -> RiskDecision`:
    1. `settings.trading_mode != PAPER` → reject.
    2. `settings.live_trading_enabled` → reject.
    3. `intent.order_type not in (LIMIT, STOP_LIMIT)` → reject.
    4. `intent.quantity <= 0` → reject.
    5. `settings.symbol_allowlist` (비어있지 않으면) `intent.symbol not in allowlist` → reject.
    6. `intent.quantity * intent.limit_price > settings.max_order_notional_usd` → reject.
  - 통과 시 `risk_token = secrets.token_hex(16)`.

### 4.7 `app/oms/manager.py`

- `class OMS`:
  - `__init__(self, settings, risk, broker)`. 인스턴스 변수는 모두 underscore-private. getter 없음.
  - `place(self, intent: OrderIntent) -> OrderAck`:
    1. `if self._settings.live_trading_enabled: raise RuntimeError("OMS refuses live trading in Phase 1")`.
    2. `if self._broker.mode != TradingMode.PAPER: raise RuntimeError("OMS rejects non-paper broker")`.
    3. `decision = self._risk.evaluate(intent)`. `if not decision.approved: raise RuntimeError(f"RiskEngine rejected: {decision.reason}")`.
    4. `Order` → `BrokerOrder` 생성, `broker.submit(...)` 결과 반환.
  - **외부 호출자가 `self._risk`나 `self._broker`에 접근할 수 없게 한다.** Strategy/Runner는 OMS의 `place`만 사용.

### 4.8 `app/strategy/base.py`

- `class StrategyResult(BaseModel)` (pydantic v2):
  - `symbol: str`
  - `passed: bool`
  - `score: float | None = None`
  - `reasons: list[str] = []`
  - `blockers: list[str] = []`
  - `suggested_limit_price: Decimal | None = None`
  - `non_executable_order_intent: OrderIntent | None = None`
- `class Strategy(ABC)`:
  - `name: str` (클래스 속성).
  - `@abstractmethod def evaluate(self, snapshot: StrategyInput) -> StrategyResult: ...`.
  - docstring에 "Strategies MUST only return StrategyResult/OrderIntent. They MUST NEVER call OMS, BrokerAdapter, or RiskEngine. They MUST NEVER produce market orders. LLM/agent-driven strategies must follow the same contract."

`app/strategy/__init__.py`: 등록 dict `STRATEGIES: dict[str, type[Strategy]] = {"premarket_gap_volume_breakout": PremarketGapVolumeBreakoutStrategy}` (런타임 import 안전을 위해 lazy import 가능). `Strategy`, `StrategyResult` re-export.

`app/strategy/inputs.py`: `from app.domain.market import StrategyInput` re-export.

### 4.9 `app/strategy/premarket_gap.py` (**핵심**)

`class PremarketGapVolumeBreakoutStrategy(Strategy)`:

- `name = "premarket_gap_volume_breakout"`.
- `__init__(self, settings)`: settings 보관, 임계값을 settings에서 읽음. import는 `app.domain.*`, `app.config.Settings`만(OMS/RiskEngine/Broker import 금지).
- `evaluate(self, snapshot: StrategyInput) -> StrategyResult`:

  ```python
  blockers, reasons = [], []
  now = datetime.now(timezone.utc)

  # 1) Market
  if snapshot.market != "US":
      blockers.append("non_us_market")
  else:
      reasons.append("us_market")

  # 2) Session
  if snapshot.session != Session.PRE_MARKET:
      blockers.append("not_premarket_session")
  else:
      reasons.append("premarket_session")

  # 3) Data sanity
  if snapshot.previous_close <= 0 or snapshot.current_price <= 0 or snapshot.premarket_high <= 0:
      blockers.append("incomplete_price_data")
  if snapshot.bid <= 0 or snapshot.ask <= 0 or snapshot.ask < snapshot.bid:
      blockers.append("invalid_bid_ask")

  # 4) Stale quote
  age = (now - snapshot.timestamp).total_seconds()
  if age < 0 or age > self._settings.premarket_max_quote_age_seconds:
      blockers.append(f"stale_quote:{age:.0f}s")
  else:
      reasons.append("fresh_quote")

  # 5) Gap
  if snapshot.previous_close > 0:
      gap_pct = (snapshot.current_price - snapshot.previous_close) / snapshot.previous_close
      if gap_pct < self._settings.premarket_gap_min_pct:
          blockers.append(f"gap_below_threshold:{gap_pct:.4f}")
      else:
          reasons.append(f"gap_above_threshold:{gap_pct:.4f}")
  else:
      gap_pct = Decimal("0")

  # 6) Volume
  if snapshot.premarket_volume < self._settings.premarket_min_volume:
      blockers.append(f"premarket_volume_below_threshold:{snapshot.premarket_volume}")
  else:
      reasons.append(f"premarket_volume_ok:{snapshot.premarket_volume}")

  # 7) Relative volume (optional)
  if snapshot.relative_volume is not None:
      if snapshot.relative_volume < self._settings.premarket_min_relative_volume:
          blockers.append(f"relative_volume_below_threshold:{snapshot.relative_volume}")
      else:
          reasons.append(f"relative_volume_ok:{snapshot.relative_volume}")

  # 8) Spread
  if snapshot.ask > 0 and snapshot.ask >= snapshot.bid:
      spread_pct = (snapshot.ask - snapshot.bid) / snapshot.ask
      if spread_pct > self._settings.premarket_max_spread_pct:
          blockers.append(f"spread_too_wide:{spread_pct:.4f}")
      else:
          reasons.append(f"spread_ok:{spread_pct:.4f}")

  # 9) Breakout near or above premarket_high
  tol = self._settings.premarket_breakout_tolerance_pct
  threshold = snapshot.premarket_high * (Decimal("1") - tol)
  if snapshot.current_price < threshold:
      blockers.append("not_near_premarket_high")
  else:
      reasons.append("near_or_above_premarket_high")

  passed = len(blockers) == 0

  suggested_limit_price = None
  intent = None
  score = None

  if passed:
      # LIMIT only, breakout buy slightly above premarket_high
      suggested_limit_price = (snapshot.premarket_high * (Decimal("1") + tol)).quantize(Decimal("0.01"))
      # Quantity respects max notional
      max_qty = int(self._settings.max_order_notional_usd / suggested_limit_price)
      qty = max(1, max_qty)
      intent = OrderIntent(
          symbol=snapshot.symbol,
          side=Side.BUY,
          quantity=qty,
          order_type=OrderType.LIMIT,
          limit_price=suggested_limit_price,
          client_tag=self.name,
      )
      # Simple composite score
      score = float(gap_pct) * (snapshot.premarket_volume / max(1, self._settings.premarket_min_volume))

  return StrategyResult(
      symbol=snapshot.symbol,
      passed=passed,
      score=score,
      reasons=reasons,
      blockers=blockers,
      suggested_limit_price=suggested_limit_price,
      non_executable_order_intent=intent,
  )
  ```

- 어떤 분기에서도 `OrderType.MARKET`을 만들지 않는다(애초에 존재하지 않음). `BrokerOrder`, `Order`, `OMS`, `RiskEngine`, `BrokerAdapter`를 import하지 않는다.

### 4.10 `app/runtime/paper_runner.py`

- `class PaperRunResult(BaseModel)` 또는 dataclass:
  - `symbol: str`, `strategy: StrategyResult`, `oms_ack: OrderAck | None = None`, `oms_error: str | None = None`.
- `class PaperRunner`:
  - `__init__(self, settings, strategy, oms)` — RiskEngine을 직접 받지 않는다. OMS만 받는다. RiskEngine은 OMS 내부에서만 호출된다.
  - `run_once(self, snapshots: list[StrategyInput]) -> list[PaperRunResult]`:

    ```python
    results = []
    for s in snapshots:
        strategy_result = self._strategy.evaluate(s)
        ack, err = None, None
        if strategy_result.passed and strategy_result.non_executable_order_intent is not None:
            try:
                ack = self._oms.place(strategy_result.non_executable_order_intent)
            except RuntimeError as e:
                err = str(e)
        # blocked candidates explicitly bypass OMS
        results.append(PaperRunResult(symbol=s.symbol, strategy=strategy_result, oms_ack=ack, oms_error=err))
    return results
    ```

  - blocked candidate(`passed=False` 또는 `intent is None`)는 OMS를 호출하지 않는다 — 테스트가 이 불변식을 검증.

### 4.11 `app/api/server.py`, `app/api/routes.py`

`server.py`:

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import load_settings
from app.risk.engine import RiskEngine
from app.broker.paper import PaperBroker
from app.oms.manager import OMS
from app.strategy.premarket_gap import PremarketGapVolumeBreakoutStrategy
from app.runtime.paper_runner import PaperRunner

def create_app() -> FastAPI:
    settings = load_settings()  # fail closed if live or non-paper
    broker = PaperBroker()
    risk = RiskEngine(settings)
    oms = OMS(settings, risk, broker)
    strategy = PremarketGapVolumeBreakoutStrategy(settings)
    runner = PaperRunner(settings, strategy, oms)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.settings = settings
        app.state.broker = broker
        app.state.oms = oms
        app.state.strategy = strategy
        app.state.runner = runner
        yield

    app = FastAPI(lifespan=lifespan)
    from app.api.routes import router
    app.include_router(router)
    return app

app = create_app()
```

`routes.py`:

- `GET /healthz` → `{"ok": True}`.
- `GET /paper/status` → mvp-003 plan §4.13의 응답 그대로(트레이딩 모드, live_enabled, broker 정보, limits, safety). `strategies`도 추가:

  ```json
  {
    ...
    "strategies": ["premarket_gap_volume_breakout"],
    "safety": {
      "market_orders_disabled": true,
      "risk_engine_required": true,
      "oms_only_execution": true,
      "strategy_emits_non_executable_only": true
    }
  }
  ```

- `POST /paper/run` (pydantic body):

  ```python
  class PaperRunRequest(BaseModel):
      snapshots: list[StrategyInput]
      strategy: str = "premarket_gap_volume_breakout"  # 화이트리스트 검증

  class PaperRunSummary(BaseModel):
      snapshots: int
      passed: int
      blocked: int
      submitted_to_oms: int
      rejected_by_oms: int

  class PaperRunResponse(BaseModel):
      results: list[PaperRunResult]
      summary: PaperRunSummary
  ```

  핸들러:

  ```python
  if payload.strategy not in app.state.strategies_allow:  # {"premarket_gap_volume_breakout"}
      raise HTTPException(400, "Unknown strategy")
  if app.state.settings.live_trading_enabled:
      raise HTTPException(503, "Live trading disabled in Phase 1")
  results = app.state.runner.run_once(payload.snapshots)
  return PaperRunResponse(results=results, summary=summarize(results))
  ```

- **`POST /paper/run`은 caller-provided OrderIntent를 받지 않는다.** snapshots만 받고 내부에서 Strategy → OMS로 흘려보낸다. order endpoint(예: `POST /paper/order`)는 만들지 않는다.

### 4.12 `app/main.py`

```python
def main() -> None:
    print("Phase 1: paper trading runtime. No autonomous trading loop will start.")
    print("Run the read-only API with: uvicorn app.api.server:app --reload")

if __name__ == "__main__":
    main()
```

### 4.13 저장소 루트 `.gitignore`

`projects/paper-trading/.env` 한 줄 추가(중복 룰 있으면 추가 안 함).

### 4.14 `README.md`

- 모듈 목적, 디렉터리 트리.
- 안전 규칙(live 차단, 시장가 차단, RiskEngine 필수, OMS 단일 경로, Strategy는 OrderIntent만, agent 직접 주문 금지, `.env`에서만 키 로드, broker URL 추측 금지).
- 실행 방법(`python -m app.main`, `uvicorn app.api.server:app --reload`).
- 테스트(`python -m compileall app tests`, `python -m pytest -p no:cacheprovider`).
- 전략 설명: `PremarketGapVolumeBreakoutStrategy`의 입력/출력 스키마, 차단 사유 목록, 통과 조건, 한도값(환경변수로 조정 가능).
- `/paper/run` 사용 예시(curl + sample JSON).
- Phase 2 후보: 시장 데이터 연결, Alpaca HTTP 구현, 두 번째 전략, 체결 시뮬레이션, 알림 등.

### 4.15 테스트 (`tests/`)

#### 기반 테스트(mvp-003 계승)

- `test_config.py`: 기본 paper/False; `TRADING_MODE=live` 또는 `LIVE_TRADING_ENABLED=true`이면 `load_settings()`가 `ValueError`.
- `test_models.py`: `OrderIntent`의 잘못된 quantity/price/symbol에 `ValueError`.
- `test_risk_engine.py`: MARKET 거부, notional 초과 거부, allowlist 외 거부, paper 강제, 통과 시 risk_token 비어있지 않음.
- `test_oms.py`: live=True → `RuntimeError`, non-paper broker → `RuntimeError`, RiskEngine 거부 → `RuntimeError`, 정상 시 `OrderAck` + `_open_orders` 증가.
- `test_paper_broker.py`: 강제 MARKET BrokerOrder(테스트가 직접 만들어도) → `ValueError`. LIMIT은 정상.
- `test_alpaca_paper_stub.py`: env 미설정 → `RuntimeError`. 유효 URL/키 채운 뒤 `submit` → `NotImplementedError`.
- `test_flow.py`: 수동 `OrderIntent` → OMS → PaperBroker → ack 반환. positions/open_orders 일관성.
- `test_api_paper_status.py`: `/healthz` 200; `/paper/status`에 `live_enabled=False`, `safety.market_orders_disabled=True`, `safety.risk_engine_required=True`, `safety.oms_only_execution=True`, `safety.strategy_emits_non_executable_only=True`, `strategies`에 `premarket_gap_volume_breakout` 포함.

#### 전략 테스트 (`tests/test_strategy_premarket_gap.py`) — 요청의 10개 항목

1. `test_gap_above_threshold_passes` — gap 7%, volume 200k, premarket session, 정상 spread, premarket_high 근처 → `passed=True`.
2. `test_gap_below_threshold_blocked` — gap 2% → `passed=False`, `"gap_below_threshold"` blocker.
3. `test_volume_below_threshold_blocked` — premarket_volume 50k → blocker.
4. `test_spread_above_threshold_blocked` — bid/ask spread 1% → blocker.
5. `test_not_premarket_session_blocked` — `session=REGULAR` → blocker.
6. `test_stale_quote_blocked` — timestamp 5분 전 → blocker.
7. `test_strategy_result_is_not_executable_order` — passed 통과 케이스에서 `result.non_executable_order_intent`는 `OrderIntent` 타입이고 `BrokerOrder`/`Order` 타입이 아니다(`isinstance` 검증).
8. `test_no_market_order_generated` — passed 케이스에서 `intent.order_type == OrderType.LIMIT`. `OrderType` 열거형 자체에 `MARKET`이 없는지도 별도 assertion(`assert "MARKET" not in OrderType.__members__`).
9. `test_blocked_candidate_does_not_reach_oms` — Mock `oms.place` 사용, blocked snapshot으로 PaperRunner.run_once 실행 → `oms.place.call_count == 0`.
10. `test_paper_run_endpoint_works` — FastAPI TestClient로 `/paper/run`에 통과 1개 + 차단 1개 snapshot 전송 → 응답의 summary `{passed:1, blocked:1, submitted_to_oms:1}`. `results[0].oms_ack.mode == "paper"`. `results[1].oms_ack is None`.

추가로:

- `test_paper_runner.py`: PaperRunner가 blocked candidate에 대해 OMS를 호출하지 않는지, passed candidate가 OMS error를 잡는지(RiskEngine reject 등) 검증.

### 4.16 검증 명령

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

`compileall`과 `pytest`는 종료코드 0이어야 한다. 의존성 미설치로 실패하면 Codex는 작업을 멈추고 `patch.md` Remaining TODOs에 "사람이 `pip install fastapi 'uvicorn[standard]' 'pydantic>=2' python-dotenv pytest httpx` 실행해야 함"으로 명시한다. `pip install`을 Codex가 직접 실행하지 않는다.

### 4.17 `docs/ai/jobs/mvp-005/patch.md`

`prompts/codex-implementer.md` 형식. Implementation Summary는 요청 "완료 후 정리" 7개 항목과 1:1 대응하도록 단락 분리:

```markdown
## 1. Files Changed
(전체 신규 파일 + 루트 .gitignore 추가 여부)

## 2. Implementation Summary

### 2.1 전략 조건 구현 (premarket gap + 거래량 돌파)
- session=PRE_MARKET 강제
- gap ≥ premarket_gap_min_pct (기본 5%)
- premarket_volume ≥ premarket_min_volume (기본 100k)
- relative_volume 값이 있을 경우 ≥ premarket_min_relative_volume (기본 1.5)
- spread ≤ premarket_max_spread_pct (기본 0.3%)
- current_price ≥ premarket_high * (1 - tolerance) (기본 tolerance 0.1%)
- quote age ≤ premarket_max_quote_age_seconds (기본 60s)
- 데이터 결함 시(가격 0 이하, ask<bid 등) 자동 차단
- 통과 시 LIMIT OrderIntent만 생성, 시장가 분기 없음

### 2.2 paper trading 경로 연결
Strategy.evaluate(snapshot) → StrategyResult{non_executable_order_intent: OrderIntent}
  → PaperRunner.run_once → OMS.place(intent)
  → RiskEngine.evaluate (내부 호출)
  → BrokerOrder → PaperBroker.submit → OrderAck
- /paper/run POST 엔드포인트가 snapshots 리스트를 받아 위 경로로 처리. caller-provided OrderIntent는 받지 않음.

### 2.3 live trading 차단 메커니즘
- Settings.live_trading_enabled 기본 False
- load_settings()가 TRADING_MODE!=paper 또는 LIVE_TRADING_ENABLED=true에서 ValueError(fail closed)
- OMS.place 시작부에서 live 차단, non-paper broker 차단
- RiskEngine.evaluate가 trading_mode!=PAPER, live_trading_enabled에서 reject
- /paper/run 핸들러도 live_trading_enabled 진입 시 503
- Alpaca Live 어댑터 미존재. AlpacaPaperBroker 네트워크 NotImplementedError

### 2.4 시장가 주문 차단 메커니즘
- OrderType 열거형에 MARKET 없음 (assert "MARKET" not in OrderType.__members__)
- Strategy: 통과 케이스에서 LIMIT만 생성
- RiskEngine: order_type not in (LIMIT, STOP_LIMIT) reject
- PaperBroker: 동일 가드 (이중 가드)

### 2.5 실행한 테스트 목록
- 기반 테스트 8개
- 전략 테스트 10개 (요청의 1–10 항목과 1:1)
- 러너 테스트
- 결과: <pytest 출력>

### 2.6 다음 단계
- 시장 데이터 수집(Alpaca/Polygon 등 base URL은 .env에서만)
- Alpaca Paper HTTP 호출 실제 구현(adapter 내부에서만)
- 두 번째 전략(예: VWAP 회귀, ORB) 추가
- 체결 시뮬레이션(부분 체결, 슬리피지)
- 포트폴리오/PnL 추적과 /paper/portfolio
- 외부 알림(webhook URL은 .env)
- live trading은 별도 작업 + 명시적 사용자 승인 + arming/preflight/guard 절차 이후에만 검토

## 3. Safety Confirmation
- live trading 코드 경로/플래그 활성화 없음
- 실계좌 주문 코드 경로 없음 (AlpacaPaperBroker는 stub)
- 시장가 주문 차단 (Strategy + RiskEngine + PaperBroker 삼중 가드, OrderType에 MARKET 없음)
- 모든 주문은 OMS만 broker.submit 호출
- OMS가 외부 호출자에게 RiskEngine 노출하지 않음 (내부 호출)
- Strategy는 OrderIntent만 반환, OMS/Broker/RiskEngine 직접 호출 없음
- /paper/run은 caller-provided OrderIntent를 받지 않음 (snapshots만)
- secrets/.env/auth/payment/migration/infra 미변경
- broker endpoint URL 하드코딩 없음 (.env에서만)
- git commit/push/merge/deploy 자동화 없음

## 4. Test Results
- python -m compileall app tests: <결과>
- python -m pytest -p no:cacheprovider: <결과>
- git diff --stat: <결과>
- git status --short: <결과>

## 5. Remaining TODOs
- 없음 (또는 pip install 필요 패키지 / Phase 2 후보 명시)
```

## 5. 테스트 기준

1. `python -m compileall app tests` 종료코드 0 (프로젝트 디렉터리 내).
2. `python -m pytest -p no:cacheprovider` 종료코드 0, 위 18개 이상 테스트가 모두 수집·통과되며 외부 네트워크 호출이 없다. 의존성 미설치로 실패한 경우 `patch.md` Remaining TODOs에 사람이 실행할 `pip install` 명령 명시.
3. `grep -RIn "MARKET" projects/paper-trading/app` 결과에 `OrderType.MARKET` 사용이 없다(주석/문자열로만 존재 OK).
4. `grep -RIn "live_trading_enabled\s*=\s*True\|LIVE_TRADING_ENABLED\s*=\s*true" projects/paper-trading/app` 결과 0건.
5. `grep -RIn "https://" projects/paper-trading/app` 결과에 broker 실제 URL 하드코딩 없음.
6. `grep -RIn "from app.oms\|from app.risk\|from app.broker" projects/paper-trading/app/strategy` 결과 0건(Strategy는 OMS/RiskEngine/Broker 미의존).
7. `git status --short`에 `.env` 또는 secrets가 staged/untracked로 나타나지 않는다.
8. `git diff --stat`에 mvp-005 외 변경 없음(루트 `.gitignore` 한 줄 + `docs/ai/jobs/mvp-005/` 외 변경 없음).
9. `/paper/status` 응답에 `live_enabled: false`, `safety.market_orders_disabled: true`, `safety.risk_engine_required: true`, `safety.oms_only_execution: true`, `safety.strategy_emits_non_executable_only: true`, `strategies`에 `premarket_gap_volume_breakout` 포함.
10. `/paper/run` 응답에서 blocked snapshot은 `oms_ack=null`이고 passed snapshot은 `oms_ack.mode=="paper"`.

## 6. 리뷰 체크리스트

- [ ] `projects/paper-trading/` 디렉터리와 `app/`, `tests/`, 설정 파일이 모두 생성됨.
- [ ] `OrderType`에 MARKET 멤버 없음.
- [ ] `Settings.live_trading_enabled` 기본 False, `TradingMode.PAPER` 기본.
- [ ] `load_settings()`가 paper 외 모드 / live 활성에서 fail closed.
- [ ] RiskEngine: paper 강제 / live 차단 / 시장가 거부 / 한도 / allowlist 모두 점검.
- [ ] OMS: live 차단 / non-paper broker 차단 / RiskEngine 내부 호출 / 외부 RiskEngine 우회 불가.
- [ ] PaperBroker: LIMIT/STOP_LIMIT만 허용 (이중 가드).
- [ ] AlpacaPaperBroker: env 미설정 fail closed, 네트워크 미구현.
- [ ] Strategy 패키지가 OMS/RiskEngine/BrokerAdapter import 없음 (grep 확인).
- [ ] PremarketGapVolumeBreakoutStrategy가 모든 차단 조건(session, gap, volume, spread, breakout, stale_quote, data sanity)을 정확히 평가.
- [ ] 통과 케이스에서 LIMIT OrderIntent만 생성. 시장가 분기 없음.
- [ ] StrategyResult의 `non_executable_order_intent`가 `OrderIntent` 타입이고 `BrokerOrder`/`Order`가 아님.
- [ ] PaperRunner: blocked candidate에서 OMS 미호출. passed에서 OMS 호출 후 ack/error 수집.
- [ ] `/paper/run`이 caller-provided OrderIntent 미수용, snapshots만 받음.
- [ ] `/paper/run` 핸들러가 live 활성 시 503.
- [ ] `/paper/status`에 strategies 목록과 safety 플래그 포함.
- [ ] `.env.example`에 실제 키 없음. `.env`는 무시됨.
- [ ] broker URL 코드 상수 없음, env에서 로드.
- [ ] 요청의 10개 전략 테스트가 1:1 대응 존재 + 통과.
- [ ] `git diff --stat`에 mvp-005 외 변경 없음.
- [ ] commit/push/merge/deploy 자동화 없음.
- [ ] `patch.md`에 (i) Files Changed, (ii) 전략 조건 구현, (iii) paper 경로 연결, (iv) live 차단, (v) 시장가 차단, (vi) 테스트 실행, (vii) 다음 단계가 모두 포함.
