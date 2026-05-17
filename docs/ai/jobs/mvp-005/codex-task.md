# Codex Task — mvp-005: 프리마켓 갭 + 거래량 돌파 전략 (paper trading scaffold + strategy)

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-005/plan.md` and `docs/ai/jobs/mvp-005/request.ko.md` first.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-005`
- 대상 신규 디렉터리: `projects/paper-trading/` (저장소 루트 기준 신규 생성)
- mvp-003에서 계획됐던 paper trading 스캐폴딩이 실제로 만들어지지 않았다. mvp-005에서는 **스캐폴딩 + premarket gap 전략을 한 번에** 만든다.
- 모듈 구조는 `app/strategy/`, `app/runtime/`, `app/api/`, `app/domain/`, `app/risk/`, `app/oms/`, `app/broker/` 패키지 체계를 사용한다(mvp-005 요청 명세).

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, API key, token 류 일체 변경/생성 금지(`.env.example`는 placeholder만).
- 시크릿, 실제 API 키, 실제 broker URL을 어떤 파일에도 하드코딩 금지.
- live trading 코드 경로/플래그 활성화 금지. `LIVE_TRADING_ENABLED=true`로 만들 수 있는 코드 경로 신설 금지.
- 실계좌(Alpaca Live 등) 어댑터 작성 금지. Alpaca Paper 어댑터도 네트워크 호출은 stub(`NotImplementedError`)만.
- 시장가(market) 주문 경로 신설 금지. `OrderType`에 MARKET 멤버 추가 금지. 어떤 코드도 market order를 만들지 않는다.
- RiskEngine 우회 코드 경로 신설 금지. OMS 외부에서 RiskEngine 또는 BrokerAdapter를 직접 호출할 수 있는 길이 있으면 안 됨.
- Strategy 패키지가 `app.oms`, `app.risk`, `app.broker`를 import하면 안 됨. Strategy는 OrderIntent까지만 만든다.
- agent/LLM이 OMS/Broker/RiskEngine을 직접 호출하는 코드 경로 신설 금지.
- 임의 shell 명령 입력 UI/API 신설 금지.
- 본 작업 범위 외 파일 변경 금지(저장소 루트 `.gitignore` 한 줄 추가는 허용).
- `pip install` 실행 금지. 호스트에 없는 패키지는 `patch.md` Remaining TODOs에 사람이 실행할 명령으로 적는다.
- `web/`, `prompts/`, `scripts/`, `examples/`, `docs/`(mvp-005 job dir 제외), `docs/ai/jobs/mvp-001..mvp-004/` 변경 금지.

## 수정 허용 위치

- 신규: `projects/paper-trading/` 아래 전체.
- 기존 파일 수정: 저장소 루트 `.gitignore`에 `projects/paper-trading/.env` 한 줄만(중복 룰이 이미 있으면 추가 안 함).
- 산출물: `docs/ai/jobs/mvp-005/patch.md`.

## 디렉터리 구조 (신규 생성 대상)

```
projects/paper-trading/
├── README.md
├── pyproject.toml
├── pytest.ini          # 또는 pyproject [tool.pytest.ini_options]만 사용
├── .env.example
├── .gitignore
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── main.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── enums.py
│   │   ├── orders.py
│   │   └── market.py
│   ├── broker/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── paper.py
│   │   └── alpaca_paper.py
│   ├── risk/
│   │   ├── __init__.py
│   │   └── engine.py
│   ├── oms/
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── strategy/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── inputs.py
│   │   └── premarket_gap.py
│   ├── runtime/
│   │   ├── __init__.py
│   │   └── paper_runner.py
│   └── api/
│       ├── __init__.py
│       ├── server.py
│       └── routes.py
└── tests/
    ├── __init__.py
    ├── test_config.py
    ├── test_models.py
    ├── test_risk_engine.py
    ├── test_oms.py
    ├── test_paper_broker.py
    ├── test_alpaca_paper_stub.py
    ├── test_flow.py
    ├── test_api_paper_status.py
    ├── test_strategy_premarket_gap.py
    └── test_paper_runner.py
```

## 구현 작업

`plan.md` §4를 그대로 따른다. 아래는 Codex가 자주 빠뜨릴 만한 핵심 불변식을 다시 정리한 것이다.

### A. 패키지 설정

- `pyproject.toml`: setuptools build, name `paper-trading`, version `0.1.0`, python `>=3.10`. deps: `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `python-dotenv`. dev: `pytest`, `httpx`. `[tool.pytest.ini_options]`: `testpaths=["tests"]`, `addopts="-p no:cacheprovider"`.
- `.env.example`: placeholder 값만. `ALPACA_PAPER_API_BASE`는 비워두고 주석으로 "사용자가 .env에 직접 적음" 명시. URL 추측 금지.
- `.gitignore`: `.env`, `__pycache__/`, `.pytest_cache/`, `*.egg-info/`, `.coverage`, `.venv/`, `dist/`, `build/`.

### B. `app/config.py`

- `TradingMode(str, Enum)`: PAPER, LIVE.
- `Session(str, Enum)`: PRE_MARKET, REGULAR, AFTER_HOURS, CLOSED.
- `Settings` frozen dataclass — `plan.md` §4.3의 모든 필드 포함(전략 임계값 포함).
- `load_settings() -> Settings`:
  - `dotenv.load_dotenv()` 호출. 파일 없어도 OK.
  - `TRADING_MODE != "paper"` → `ValueError("Phase 1 only supports paper trading")`.
  - `LIVE_TRADING_ENABLED ∈ {"true","1","yes","on"}` (lower) → `ValueError("Live trading is disabled in Phase 1")`.
  - 잘못된 Decimal/int 형식이면 `ValueError`.

### C. `app/domain/`

- `enums.py`: `TradingMode`, `Side(BUY,SELL)`, `OrderType(LIMIT, STOP_LIMIT)`, `Session`. **MARKET 멤버 추가 금지.**
- `orders.py`: `OrderIntent`, `Order`, `BrokerOrder`, `OrderAck` frozen dataclass. `OrderIntent.__post_init__`에서 `quantity>0`, `limit_price>0`, `symbol==symbol.upper()` 검증.
- `market.py`: `StrategyInput` (pydantic v2 BaseModel) — `plan.md` §4.4 필드. validator로 symbol 대문자.

### D. `app/broker/`

- `base.py`: `BrokerAdapter` Protocol.
- `paper.py`: `PaperBroker.mode=PAPER`. `submit`에서 `order_type not in (LIMIT, STOP_LIMIT)` → `ValueError("market orders are disabled")`. `broker_order_id=secrets.token_hex(8)`. open_orders/positions dict. 체결 시뮬레이션 없음.
- `alpaca_paper.py`: `AlpacaPaperBroker(settings)`. base URL 빈 값/`https://` 미시작 → `RuntimeError`. credentials 누락 → `RuntimeError`. `submit/cancel/open_orders/positions` 모두 `NotImplementedError`. URL 하드코딩 금지.

### E. `app/risk/engine.py`

- `RiskDecision`(approved, reason, risk_token).
- `RiskEngine.evaluate(intent)`: paper 강제, live 차단, MARKET 거부, quantity>0, allowlist(비어있지 않으면), notional 한도. 통과 시 `risk_token = secrets.token_hex(16)`.

### F. `app/oms/manager.py`

- `OMS(settings, risk, broker)`. 인스턴스 변수는 `_settings`, `_risk`, `_broker`(private). **getter 만들지 않는다.**
- `place(intent)`:
  1. live 차단
  2. non-paper broker 차단
  3. `_risk.evaluate(intent)` 내부 호출, 거부면 `RuntimeError`
  4. `Order` → `BrokerOrder` → `broker.submit` 반환

### G. `app/strategy/`

- `base.py`:
  - `class StrategyResult(BaseModel)` pydantic v2. 필드: `symbol`, `passed`, `score: float|None`, `reasons: list[str]`, `blockers: list[str]`, `suggested_limit_price: Decimal|None`, `non_executable_order_intent: OrderIntent|None`. (pydantic이 dataclass `OrderIntent`를 직렬화하도록 `model_config = ConfigDict(arbitrary_types_allowed=True)` 등 필요 시 설정.)
  - `class Strategy(ABC)` with `name: str` and `@abstractmethod def evaluate(snapshot) -> StrategyResult`.
- `inputs.py`: `from app.domain.market import StrategyInput` re-export.
- `__init__.py`: `STRATEGIES = {"premarket_gap_volume_breakout": PremarketGapVolumeBreakoutStrategy}`. (lazy import 권장.)
- `premarket_gap.py`: `plan.md` §4.9의 알고리즘 그대로 구현. `app.oms`, `app.risk`, `app.broker` import 금지. 통과 시 `OrderType.LIMIT`만 사용. quantity는 `max(1, int(max_order_notional_usd / limit_price))`.

### H. `app/runtime/paper_runner.py`

- `PaperRunResult` dataclass/BaseModel: `symbol`, `strategy: StrategyResult`, `oms_ack: OrderAck|None`, `oms_error: str|None`.
- `PaperRunner(settings, strategy, oms)` — RiskEngine을 직접 받지 않는다.
- `run_once(snapshots: list[StrategyInput]) -> list[PaperRunResult]`:
  - 각 snapshot마다 `strategy.evaluate` 호출.
  - `passed`이고 `non_executable_order_intent is not None`이면 `oms.place(intent)` 호출 시도, RuntimeError는 `oms_error`로 잡음.
  - blocked는 OMS 호출하지 않음.

### I. `app/api/`

- `server.py`: `create_app()`에서 settings/broker/risk/oms/strategy/runner를 만들고 `app.state`에 보관. lifespan에서 yield. `app.include_router(router)`.
- `routes.py`:
  - `GET /healthz` → `{"ok": True}`.
  - `GET /paper/status` → `plan.md` §4.11의 응답 + `"strategies": ["premarket_gap_volume_breakout"]` + safety 플래그에 `"strategy_emits_non_executable_only": True` 포함.
  - `POST /paper/run`:
    - body `PaperRunRequest{snapshots: list[StrategyInput], strategy: str = "premarket_gap_volume_breakout"}`.
    - strategy 이름은 화이트리스트 검증, 일치 안 하면 400.
    - `settings.live_trading_enabled`면 503.
    - `runner.run_once(snapshots)` 호출 후 `PaperRunResponse{results, summary}` 반환.
    - **caller-provided OrderIntent를 받지 않는다.** snapshots만.

### J. `app/main.py`

```python
def main() -> None:
    print("Phase 1: paper trading runtime. No autonomous trading loop will start.")
    print("Run the read-only API with: uvicorn app.api.server:app --reload")

if __name__ == "__main__":
    main()
```

### K. 저장소 루트 `.gitignore`

`projects/paper-trading/.env` 한 줄 추가(중복 룰 있으면 추가 안 함).

### L. `README.md`

- 모듈 목적, 디렉터리 트리, 안전 규칙, 실행/테스트 명령, 전략 설명(입력/출력 스키마, 차단 사유 목록, 통과 조건, 환경변수로 조정 가능한 임계값), `/paper/run` curl 예시, Phase 2 후보.

### M. 테스트 (`tests/`) — 외부 네트워크 호출 금지, pytest로 수집 가능

- 기반 테스트 8개 (`plan.md` §4.15의 mvp-003 계승 그룹):
  `test_config.py`, `test_models.py`, `test_risk_engine.py`, `test_oms.py`, `test_paper_broker.py`, `test_alpaca_paper_stub.py`, `test_flow.py`, `test_api_paper_status.py`.
- **전략 테스트 (`test_strategy_premarket_gap.py`) — 요청의 10개 항목과 1:1 대응:**
  1. `test_gap_above_threshold_passes`
  2. `test_gap_below_threshold_blocked` (blocker에 `gap_below_threshold` 포함)
  3. `test_volume_below_threshold_blocked`
  4. `test_spread_above_threshold_blocked`
  5. `test_not_premarket_session_blocked`
  6. `test_stale_quote_blocked` (timestamp 5분 전)
  7. `test_strategy_result_is_not_executable_order` — `isinstance(result.non_executable_order_intent, OrderIntent)` 그리고 `not isinstance(..., BrokerOrder)`, `not isinstance(..., Order)`.
  8. `test_no_market_order_generated` — 통과 케이스에서 `intent.order_type == OrderType.LIMIT`. 추가로 `assert "MARKET" not in OrderType.__members__`.
  9. `test_blocked_candidate_does_not_reach_oms` — Mock OMS, blocked snapshot 1개 + runner.run_once → `oms.place.call_count == 0`.
  10. `test_paper_run_endpoint_works` — FastAPI `TestClient`로 `/paper/run` POST, body는 passed 1 + blocked 1 snapshot. 응답 검증.
- `test_paper_runner.py`: PaperRunner가 blocked candidate에서 OMS 호출 안 함, passed에서 OMS error를 잡음.

### N. 검증

`projects/paper-trading` 에서:

```bash
python -m compileall app tests
python -m pytest -p no:cacheprovider
```

저장소 루트에서:

```bash
git diff --stat
git status --short
```

네 명령 결과를 `patch.md`의 Test Results에 그대로 인용한다. `compileall`과 `pytest`는 종료코드 0이어야 한다. 의존성 미설치로 실패한 경우 작업을 멈추고 `patch.md` Remaining TODOs에 사람이 실행할 명령(`pip install fastapi 'uvicorn[standard]' 'pydantic>=2' python-dotenv pytest httpx`)을 적은 뒤 종료한다. `pip install`을 Codex가 직접 실행하지 않는다.

### O. `docs/ai/jobs/mvp-005/patch.md`

`plan.md` §4.17 형식을 그대로 채운다(7개 Implementation Summary 단락 포함). 각 단락의 첫 줄에는 어떤 요청 항목과 매핑되는지 명시한다.

## 완료 정의 (Done)

- `projects/paper-trading/` 디렉터리가 생성되어 `app/`, `tests/`, 설정 파일이 모두 존재한다.
- `app/strategy/premarket_gap.py`의 `PremarketGapVolumeBreakoutStrategy`가 요청의 9개 조건 + 8개 제외 조건을 모두 평가한다.
- `OrderType`에 MARKET 없음 (`assert "MARKET" not in OrderType.__members__` 통과).
- `Strategy` 패키지가 `app.oms`, `app.risk`, `app.broker`를 import하지 않는다.
- OMS가 외부 호출자에게 `_risk`/`_broker`를 노출하지 않는다.
- `/paper/status`에 `live_enabled=False`, safety 플래그 + `strategies` 목록 포함.
- `/paper/run`이 snapshots만 받고 caller-provided OrderIntent를 받지 않는다.
- `/paper/run`이 live 활성 시 503.
- 요청의 10개 전략 테스트가 1:1로 존재하고 통과.
- `python -m compileall app tests`와 `python -m pytest -p no:cacheprovider`가 모두 종료코드 0(또는 의존성 미설치 사유를 Remaining TODOs에 명시).
- `git diff --stat`에 mvp-005 외 변경 없음(루트 `.gitignore` 한 줄 추가 외).
- `.env`가 staged/committed되지 않음.
- `patch.md`가 7섹션으로 채워져 있다.
- commit/push/merge/deploy 자동화 없음.
