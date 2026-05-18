# runtime-002 — PaperEngine.submit_intents 통합

## 1. 요청 요약

paper-001 v2 에서 `PaperEngine.on_quote(quote)` → `PaperBroker.tick(quote)` → `PaperAccount.apply_fill` → `PortfolioService.apply_trade` → `PaperJournal` 흐름은 구축됐지만, **주문 제출** 쪽은 외부 caller 가 `oms.place(intent)` 를 직접 호출해야 하는 패턴이 남아 있다. 그래서 "전략 후보가 paper trading engine 까지 들어가는 end-to-end 경로" 가 단일 runtime entrypoint 로 잡혀 있지 않고, dry-run controller 도 `PaperRunner` 를 거쳐 OMS 를 직접 호출하는 형태다.

본 작업은 `PaperEngine` 에 `submit_intents()` runtime 진입점을 추가하여 다음을 만족하는 단일 경로를 만든다.

1. 입력은 non-executable `OrderIntent` 목록만 허용. `Order`/`BrokerOrder` 직접 입력은 거부.
2. `OrderIntent` 는 반드시 `RiskEngine` (`OMS` 내부 호출) → `OMS` → `PaperBroker.submit` 경로를 거친다.
3. 호출자는 batch 결과 (accepted / risk_rejected / oms_rejected count, oms_ids, broker_order_ids, per-intent rejection reason) 를 받는다.
4. rejected/blocked intent 는 `PaperBroker._open_orders` 로 들어가지 않는다 (OMS 가 raise 시 `broker.submit` 미호출).
5. 이후 `PaperEngine.on_quote(quote)` 가 호출되면 기존처럼 partial fill / staleness / session / commission / journal 흐름이 그대로 동작.
6. `dry-run controller` 가 OMS/PaperBroker 를 직접 우회하지 않고 새 진입점을 통과해 같은 runtime 상태를 공유할 수 있다.

본 작업은 GUI / KIS HTTP / live trading / 시장가 가드 / OMS / RiskEngine / PaperBroker 핵심 로직 어디에도 의미론적 변동을 주지 않는다.

## 2. 작업 범위

포함하는 것:

- `PaperEngine.submit_intents(intents: Iterable[OrderIntent]) -> SubmitIntentsBatchResult` 신규 메서드.
- 보조 dataclass `IntentSubmitResult`, `SubmitIntentsBatchResult` (`app/runtime/paper_engine.py` 또는 신규 module).
- `PaperEngine.__init__` 에 선택적 `oms: OMS | None = None` 파라미터 추가. 기존 호출 (`PaperEngine(settings, broker=..., portfolio=..., journal=...)`) 은 모두 후방 호환.
- `submit_intents` 입력 타입 가드: `isinstance(item, OrderIntent)` 가 아니면 `TypeError` (Order/BrokerOrder 입력 차단).
- `PaperRunner` 에 선택적 `paper_engine: PaperEngine | None = None` 파라미터 추가. `paper_engine` 이 주어지면 `paper_engine.submit_intents([intent])` 경유, 아니면 기존 `oms.place(intent)` 경로 유지 (후방 호환).
- `DryRunController` 는 변경 없음. 기존 `PaperRunner` 를 그대로 받는다. dry-run 의 paper_engine 경유 옵션은 PaperRunner 의 paper_engine 주입을 통해서만 동작 (production wiring 전환은 본 job 범위 밖, 사용자가 별 job 으로 처리).
- 단위 테스트: `submit_intents` 의 happy / risk-reject / oms-reject / 타입 가드 / end-to-end (`submit_intents` → `on_quote` 통합) 시나리오.
- runner 단위 테스트: paper_engine 경유 분기와 기존 oms 직접 경유 분기 둘 다 검증.
- dry-run controller 단위 테스트: paper_engine 경유 분기에서 ticks_total, candidates_passed, oms_acks 가 기존과 동일하게 집계됨을 검증.
- README 한 줄 안내 (있다면).
- `patch.md` 에 Claude 검증 요청 프롬프트 + REQUEST CHANGES/BLOCK 시 follow-up Codex 수정 프롬프트 규칙 포함.

제외 (절대 안 하는 것):

- live trading 활성화 / live broker API 호출 / KIS HTTP / KIS endpoint·TR ID·payload 추측.
- `OrderType.STOP` 도입 (LIMIT / STOP_LIMIT / MARKET 3 종 유지).
- `ALLOW_MARKET_ORDERS=true` reject 정책 풀기 / `OrderType.MARKET` 3중 가드 (`allow_paper_market_orders` + `TradingMode.PAPER` + `live_trading_enabled=False`) 우회.
- FX 변환 / 환율 상수 / base currency 통합 합계 도입. 통화별 분리 보고만.
- `Strategy`/`Agent`/`LLM` 이 broker 를 직접 호출하거나 `BrokerOrder` 를 직접 만드는 경로 추가.
- OMS 우회. PaperBroker 가 OMS 가 만든 `BrokerOrder` 외 다른 입력을 받게 하는 변경.
- 외부 HTTP 라이브러리 (`requests`, `httpx`, `aiohttp`, `urllib3`) import.
- `.env` 읽기/수정, `.env.example` 에 실제 값 추가, secret/계좌번호/access token/Bearer 노출.
- GUI 파일 (`app/api/`, `app/static/`, `app/main.py`) 변경. **본 job 은 production wiring 의 PaperEngine↔OMS 연결을 server.py 에서 바꾸지 않는다.** 이는 별 job (예: `runtime-002b`) 에서 처리.
- KIS adapter 파일 수정 (HTTP 구현 추가 등).
- `app/oms/`, `app/risk/`, `app/portfolio/`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/kis*.py`, `app/domain/*`, `app/strategy/*`, `app/session/*`, `app/main.py`, `app/config.py` 의 로직 변경. (단, 본 plan 에서 명시한 PaperEngine/PaperRunner 의 후방 호환 추가 외.)
- 자동 git commit / push / merge / deploy.

## 3. 수정해야 할 파일

후방 호환 정책:

- `PaperEngine(settings, *, broker=None, account=None, portfolio=None, journal=None)` 호출은 모두 그대로 동작 (`oms` 는 신규 keyword-only, default `None`).
- `PaperRunner(settings, strategy, oms)` 호출은 그대로 동작 (`paper_engine` 은 신규 keyword-only, default `None`). `paper_engine` 가 주어지면 OMS 는 미사용으로 둘 수 있도록 OMS 도 `None` 허용 (단 둘 다 None 이면 raise).
- 새 결과 dataclass 는 frozen, JSON 직렬화 가능.

| 경로 | 변경 종류 | 요약 |
| --- | --- | --- |
| `app/runtime/paper_engine.py` | MODIFY | `IntentSubmitResult` / `SubmitIntentsBatchResult` dataclass 추가. `PaperEngine.__init__` 에 `oms` 파라미터 추가 (`OMS | None = None`). `submit_intents(intents)` 메서드 추가. 기존 `on_quote`, `mark_quote`, `cash_by_currency`, 생성자 default 객체 생성 로직 모두 그대로. |
| `app/runtime/paper_runner.py` | MODIFY | `PaperRunner.__init__` 에 `paper_engine: PaperEngine | None = None` 추가. `run_once` 가 `paper_engine` 이 있으면 `paper_engine.submit_intents([intent])` 호출, 결과의 첫 번째 ack/error 를 `PaperRunResult` 에 매핑. 없으면 기존 `self._oms.place(intent)` 경로. 기존 `PaperRunResult` 모양 그대로. |
| `tests/test_paper_engine.py` | MODIFY | 기존 3 테스트 (`on_quote` 흐름) 유지. 신규 테스트 (`submit_intents` happy / risk_reject / oms_reject / type guard / end-to-end with on_quote / partial fill) 추가. |
| `tests/test_paper_runner.py` | MODIFY | 기존 2 테스트 (mock OMS 경로) 유지. 신규 테스트 (mock paper_engine 경로 + 둘 다 None 시 raise) 추가. |
| `tests/test_dry_run_controller.py` | MODIFY (좁은 추가) | 신규 테스트 하나 추가: `PaperRunner(...paper_engine=real_paper_engine_with_oms)` 로 controller 를 구성하여 `tick` 후 `counters.dry_run_orders_created`, `counters.candidates_passed_risk` 가 OMS 직접 경로와 동일하게 집계되는지 검증. 기존 테스트 전부 보존. |
| `README.md` | MODIFY (선택) | "runtime entrypoint" 1-2 줄 안내. live trading / 시장가 활성화 안내 금지. |
| `docs/ai/jobs/runtime-002/patch.md` | NEW (Codex 가 작성) | 변경 요약 + 테스트 결과 + Claude 검증 요청 프롬프트 + REQUEST CHANGES/BLOCK 시 follow-up Codex 수정 프롬프트 규칙. |

손대지 않는 파일:

- `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/kis*.py`, `app/broker/base.py`.
- `app/oms/manager.py`, `app/risk/engine.py`, `app/portfolio/*`.
- `app/runtime/paper_journal.py`, `app/runtime/paper_status.py`, `app/runtime/dry_run.py`, `app/runtime/dry_run_report.py`.
- `app/domain/*`, `app/strategy/*`, `app/session/*`.
- `app/config.py`, `app/main.py`, `app/api/*`, `app/static/*`.
- `docs/kis/*`, `.env*`.

## 4. Codex 구현 지시문

자세한 단계별 지시는 `codex-task.md` 에 기록한다. 요지:

### 4.1 신규 dataclass (`app/runtime/paper_engine.py`)

```python
from dataclasses import dataclass, field
from datetime import datetime

from app.domain.orders import OrderAck, OrderIntent


@dataclass(frozen=True)
class IntentSubmitResult:
    intent: OrderIntent
    accepted: bool
    oms_id: str | None
    broker_order_id: str | None
    status: str | None
    rejected_by: str | None       # "risk_engine" | "oms" | None
    reason: str | None
    submitted_at: datetime | None


@dataclass(frozen=True)
class SubmitIntentsBatchResult:
    submitted_count: int
    accepted_count: int
    rejected_count: int
    risk_rejected_count: int
    oms_rejected_count: int
    results: tuple[IntentSubmitResult, ...]
    accepted_oms_ids: tuple[str, ...]
    accepted_broker_order_ids: tuple[str, ...]
```

요구:

- frozen=True. 누구도 mutate 못함.
- `secret_exposed` 키는 별도 노출하지 않는다 (이 결과는 broker 응답 raw 가 아니라 OMS Ack 만 사용하며 secret 을 담지 않음).
- `accepted_broker_order_ids` 는 `OrderAck.broker_order_id` 가 None 아닌 항목만 포함.

### 4.2 PaperEngine 변경

```python
class PaperEngine:
    def __init__(
        self,
        settings: Settings,
        *,
        broker: PaperBroker | None = None,
        account: PaperAccount | None = None,
        portfolio: PortfolioService | None = None,
        journal: PaperJournal | None = None,
        oms: "OMS | None" = None,
    ) -> None:
        ...
        self._oms = oms
```

- `oms` 는 keyword-only. 기존 default 객체 생성 (broker/account/portfolio/journal) 로직 그대로.
- `OMS` 의 import 는 type-only 가능 (`from app.oms.manager import OMS` 가 정상적으로 가능하므로 일반 import).

`submit_intents` 메서드:

```python
def submit_intents(self, intents: Iterable[OrderIntent]) -> SubmitIntentsBatchResult:
    if self._oms is None:
        raise RuntimeError("PaperEngine.submit_intents requires an OMS")
    materialized = list(intents)
    for index, item in enumerate(materialized):
        if not isinstance(item, OrderIntent):
            raise TypeError(
                f"submit_intents accepts OrderIntent only; got {type(item).__name__} at index {index}"
            )
    results: list[IntentSubmitResult] = []
    accepted_count = 0
    risk_rejected_count = 0
    oms_rejected_count = 0
    accepted_oms_ids: list[str] = []
    accepted_broker_order_ids: list[str] = []
    for intent in materialized:
        try:
            ack = self._oms.place(intent)
        except RuntimeError as exc:
            reason = str(exc)
            rejected_by = _classify_rejection(reason)
            if rejected_by == "risk_engine":
                risk_rejected_count += 1
            else:
                oms_rejected_count += 1
            results.append(
                IntentSubmitResult(
                    intent=intent,
                    accepted=False,
                    oms_id=None,
                    broker_order_id=None,
                    status=None,
                    rejected_by=rejected_by,
                    reason=reason,
                    submitted_at=None,
                )
            )
            continue
        accepted_count += 1
        accepted_oms_ids.append(ack.oms_id)
        if ack.broker_order_id is not None:
            accepted_broker_order_ids.append(ack.broker_order_id)
        results.append(
            IntentSubmitResult(
                intent=intent,
                accepted=True,
                oms_id=ack.oms_id,
                broker_order_id=ack.broker_order_id,
                status=ack.status,
                rejected_by=None,
                reason=None,
                submitted_at=datetime.now(timezone.utc),
            )
        )
    return SubmitIntentsBatchResult(
        submitted_count=len(materialized),
        accepted_count=accepted_count,
        rejected_count=len(materialized) - accepted_count,
        risk_rejected_count=risk_rejected_count,
        oms_rejected_count=oms_rejected_count,
        results=tuple(results),
        accepted_oms_ids=tuple(accepted_oms_ids),
        accepted_broker_order_ids=tuple(accepted_broker_order_ids),
    )


def _classify_rejection(reason: str) -> str:
    return "risk_engine" if reason.startswith("RiskEngine rejected") else "oms"
```

주의:

- OMS 가 raise 하는 RuntimeError 메시지는 `"RiskEngine rejected: ..."`, `"OMS refuses live trading in Phase 1"`, `"OMS rejects non-paper broker"` 등. 첫 번째 형태가 RiskEngine 거절. 그 외는 OMS 인프라 거절.
- OMS 가 `broker.submit` 단계에서 예외를 던지는 시나리오는 본 plan 범위 밖. 현재 PaperBroker.submit 은 unsupported order type 에 한해 ValueError 를 raise. `ValueError` 도 잡아서 oms_rejected 로 처리하면 안전한 확장. → except `(RuntimeError, ValueError)` 로 잡는다. message classification 은 위와 동일.

PaperBroker.submit 호출 결과 `broker._open_orders` 에 등록되는 것은 OMS 가 성공한 경우뿐이다 (OMS 가 ack 를 반환하기 직전 단계). RuntimeError raise 시 `broker.submit` 미호출 — 본 메서드의 핵심 안전 가드.

### 4.3 PaperRunner 변경

```python
class PaperRunner:
    def __init__(
        self,
        settings,
        strategy: Strategy,
        oms=None,
        *,
        paper_engine: "PaperEngine | None" = None,
    ) -> None:
        if oms is None and paper_engine is None:
            raise ValueError("PaperRunner requires oms or paper_engine")
        self._settings = settings
        self._strategy = strategy
        self._oms = oms
        self._paper_engine = paper_engine
```

`run_once`:

```python
def run_once(self, snapshots: list[StrategyInput]) -> list[PaperRunResult]:
    results: list[PaperRunResult] = []
    for snapshot in snapshots:
        strategy_result = self._strategy.evaluate(snapshot)
        ack = None
        error = None
        if strategy_result.passed and strategy_result.non_executable_order_intent is not None:
            intent = strategy_result.non_executable_order_intent
            if self._paper_engine is not None:
                batch = self._paper_engine.submit_intents([intent])
                first = batch.results[0]
                if first.accepted:
                    ack = OrderAck(
                        oms_id=first.oms_id,
                        broker_order_id=first.broker_order_id,
                        status=first.status,
                        mode=TradingMode.PAPER,
                    )
                else:
                    error = first.reason
            else:
                try:
                    ack = self._oms.place(intent)
                except RuntimeError as exc:
                    error = str(exc)
        results.append(PaperRunResult(snapshot.symbol, strategy_result, ack, error))
    return results
```

- 결과 `PaperRunResult` 모양 보존 (symbol, strategy, oms_ack, oms_error). dry_run controller 가 그대로 받는다.
- paper_engine 경로에서 첫 결과만 매핑. 한 snapshot 당 intent 1 개이므로 안전.

### 4.4 (server.py 는 변경하지 않음)

production wiring (server.py) 의 `paper_engine = PaperEngine(settings, broker=broker, portfolio=portfolio)` 는 그대로 둔다. `oms` 미주입이므로 `paper_engine.submit_intents` 는 RuntimeError 를 raise — 본 job 범위에서는 production 에서 호출되지 않는다 (HTTP `/paper/order/simulate` 는 직접 `request.app.state.oms.place(intent)` 호출 + `engine.on_quote(quote)` 호출의 기존 패턴 유지). 본 job 은 production wiring 의 PaperEngine↔OMS 결합을 명시적으로 미적용한다. 별 job (`runtime-002b` 등) 으로 분리.

### 4.5 안전 / secret / 로그

- `submit_intents` 입출력 어디에도 raw secret/account/token/Bearer 가 등장하지 않는다. `OrderIntent` 에는 secret 필드 없음. `OrderAck.broker_order_id` 는 `secrets.token_hex(8)` 로 PaperBroker 가 생성한 무작위 ID — secret 아님.
- 예외 메시지는 OMS/RiskEngine 의 기존 메시지를 그대로 통과시킨다. 이 메시지들은 catalog tag (`paper_market_orders_disabled`, `symbol_not_allowed`, `kill_switch_engaged` 등) 이며 secret 비포함.

### 4.6 LIMIT / STOP_LIMIT / MARKET 가드

- `submit_intents` 는 OMS 를 통과시키기 때문에 RiskEngine 의 기존 3 종 분기 (LIMIT/STOP_LIMIT/MARKET) + 3중 가드 (`allow_paper_market_orders=False` 기본) 가 그대로 적용된다.
- 새 enum 값 추가 없음. `OrderType.STOP` 미도입.
- MARKET 시장가는 `allow_paper_market_orders=True` 일 때만 RiskEngine 통과 — 본 작업은 이 분기를 추가/수정하지 않는다.

## 5. 테스트 기준

신규 / 갱신 테스트:

`tests/test_paper_engine.py` (기존 3 + 신규):

- 기존 3 테스트 (`on_quote` 흐름) 그대로 통과.
- `test_submit_intents_requires_oms` — `PaperEngine(settings, ...)` (oms 미주입) 에서 `submit_intents([intent])` 호출 시 `RuntimeError("PaperEngine.submit_intents requires an OMS")`.
- `test_submit_intents_rejects_non_intent_input` — `submit_intents([broker_order])` 시 `TypeError`. `submit_intents([order])` 시 `TypeError`.
- `test_submit_intents_happy_path_passes_through_risk_and_oms` — RiskEngine + OMS + PaperBroker 실 객체로 wire. AAPL LIMIT 100, qty 1. 결과 `accepted_count == 1`, `risk_rejected_count == 0`, `oms_rejected_count == 0`, `accepted_oms_ids` 비어있지 않음, `accepted_broker_order_ids` 비어있지 않음, `broker.open_orders()` 에 1 건 등록.
- `test_submit_intents_risk_rejected_does_not_reach_broker` — `symbol_allowlist=("AAPL",)` 설정 후 `OrderIntent("TSLA", ...)` 제출. `risk_rejected_count == 1`, `results[0].rejected_by == "risk_engine"`, `results[0].reason.startswith("RiskEngine rejected")`, `broker.open_orders() == []`.
- `test_submit_intents_oms_rejected_does_not_reach_broker` — `live_trading_enabled=True` 설정. 결과 `oms_rejected_count == 1`, `results[0].rejected_by == "oms"`, `results[0].reason == "OMS refuses live trading in Phase 1"`, `broker.open_orders() == []`.
- `test_submit_intents_market_order_blocked_by_default_guard` — `OrderIntent(..., order_type=OrderType.MARKET, ...)` 기본 settings 에서 제출 시 `risk_rejected_count == 1`, reason 에 `paper_market_orders_disabled` 포함.
- `test_submit_intents_then_on_quote_flows_fill_through_engine` — end-to-end: submit_intents([AAPL LIMIT 10 qty 2]) 성공 → engine.on_quote(quote(price=10, volume=100)) → trades 1 건, account.cash 가 80 (시작 100), portfolio.positions["AAPL"].quantity == 2, journal.trades 길이 1. 이로써 submit_intents → on_quote 가 같은 broker / account / portfolio / journal 상태를 공유함을 검증.
- `test_submit_intents_partial_fill_preserved` — max_fill_ratio_of_volume 을 작게 잡아 partial fill 시나리오. submit_intents 후 on_quote 호출 시 partial fill 동작. broker._open_orders 의 남은 quantity 가 줄어드는지 검증.
- `test_submit_intents_results_immutable_and_secret_free` — `SubmitIntentsBatchResult` 가 frozen (FrozenInstanceError on assignment), `repr(result)` 에 `app_key` / `app_secret` / `Bearer` / account_no fixture 값이 등장하지 않음.

`tests/test_paper_runner.py` (기존 2 + 신규):

- 기존 2 테스트 (mock OMS 경로) 그대로 통과.
- `test_paper_runner_routes_through_paper_engine_when_provided` — Mock paper_engine 주입. paper_engine.submit_intents 가 `SubmitIntentsBatchResult(accepted_count=1, results=(IntentSubmitResult(accepted=True, oms_id="x", broker_order_id="y", status="accepted", ...),))` 반환. PaperRunResult.oms_ack.status == "accepted", oms_ack.oms_id == "x", oms_error is None. 그리고 mock oms.place 가 호출되지 않음.
- `test_paper_runner_paper_engine_rejection_captured_in_oms_error` — paper_engine.submit_intents 가 rejected 결과 반환. `oms_ack is None`, `oms_error == reason`.
- `test_paper_runner_requires_oms_or_paper_engine` — `PaperRunner(settings, strategy, None)` 호출 시 `ValueError`.

`tests/test_dry_run_controller.py` (기존 + 신규 1):

- 기존 테스트 전부 보존.
- `test_controller_routes_through_paper_engine_when_runner_wired_with_paper_engine` — 실 RiskEngine + OMS + PaperBroker + PaperEngine (oms 주입) 으로 PaperRunner 구성, controller 시작 후 1 tick. `counters.dry_run_orders_created == 1`, `counters.candidates_passed_risk == 1`. broker.open_orders() 가 1 건 (paper_engine 경유로도 broker 가 동일하게 채워짐). 또한 PaperEngine.on_quote(quote) 한 번 호출 시 PaperJournal 에 trade 가 기록되어 dry-run 과 fill 시뮬레이션이 같은 broker 상태를 공유함을 검증.

회귀 / 안전 회귀:

- `test_paper_e2e_api.py`, `test_api_paper_engine_status.py`, `test_dashboard.py`, `test_dry_run_routes.py`, `test_oms.py`, `test_risk_engine.py`, `test_paper_broker.py` 전부 그대로 통과.
- `test_kis_*` (broker_interface, http_boundaries, market_data_client, quote_mapper, order_preflight, capabilities) 전부 그대로 통과 — KIS 변경 없음.
- `test_strategy_package_does_not_import_kis`, `test_agent_package_does_not_import_kis_if_present` 통과 — Strategy/Agent 는 PaperEngine 도 import 하지 않는다 (PaperEngine 은 runtime 진입점이며 Strategy 가 호출하지 않음).
- `test_kis_modules_do_not_import_third_party_http_libs`, `test_kis_module_does_not_import_http_libraries` 통과.

검증 명령:

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

전체 PASS 가 완료 조건. 회귀 0 건.

안전 grep clean: `grep -rn "ALLOW_MARKET_ORDERS=true\|LIVE_TRADING_ENABLED=true\|Bearer eyJ\|access_token=\|app_key=AKIA\|appsecret=" app tests` 결과 0 줄. (catalog 의 문자열 자체는 docs 디렉터리에만 등장하고 본 작업의 코드/테스트 변경은 새로운 secret 패턴을 도입하지 않는다.)

## 6. 리뷰 체크리스트

안전 회귀:

- [ ] live trading 활성화 코드 / `LIVE_TRADING_ENABLED=true` 추가 없음.
- [ ] `ALLOW_MARKET_ORDERS=true` 도입 / RiskEngine 의 시장가 가드 변경 없음. `OrderType.MARKET` 3중 가드 그대로.
- [ ] `OrderType.STOP` 미도입. LIMIT / STOP_LIMIT / MARKET 외 enum 변동 없음.
- [ ] OMS / RiskEngine / PaperBroker 핵심 로직 변경 없음 (`app/oms/`, `app/risk/`, `app/broker/paper.py` 변동 0).
- [ ] FX 변환 / 환율 상수 / base currency 통합 함수 도입 없음.
- [ ] 외부 HTTP 라이브러리 import 없음.
- [ ] `.env` / `.env.example` 변동 없음. 코드/문서/테스트/patch 어디에도 raw app key / app secret / access token / Bearer / 계좌번호 등장하지 않음.
- [ ] KIS adapter 파일 변경 없음. KIS endpoint / TR ID / payload 추가 없음.
- [ ] GUI 파일 (`app/api/`, `app/static/`, `app/main.py`) 변경 없음.

스코프 / 동작:

- [ ] `PaperEngine.submit_intents` 가 `OrderIntent` 외 입력 (`Order`, `BrokerOrder`, dict 등) 에 대해 `TypeError` raise.
- [ ] OMS 미주입 PaperEngine 에서 `submit_intents` 호출 시 `RuntimeError`.
- [ ] RiskEngine 거절 intent 는 `broker.open_orders()` 에 등록되지 않음 (count 0 회귀 테스트로 검증).
- [ ] OMS 인프라 거절 intent (live_enabled / non_paper_broker) 도 `broker.open_orders()` 에 등록되지 않음.
- [ ] 승인된 intent 만 broker 에 등록되고 `SubmitIntentsBatchResult.accepted_oms_ids`/`accepted_broker_order_ids` 에 포함.
- [ ] `submit_intents` 결과 후 `on_quote(quote)` 가 같은 broker/account/portfolio/journal 상태를 통해 fill / cash / position / journal 갱신.
- [ ] `PaperRunner` 가 `paper_engine` 또는 `oms` 둘 다 None 이면 raise. 둘 중 하나만 제공되면 그 경로로 동작.
- [ ] `DryRunController` 가 paper_engine 주입된 PaperRunner 와도 기존과 같은 카운터를 집계.

테스트 / 문서:

- [ ] `python -m compileall app tests` 통과.
- [ ] `python -m pytest -p no:cacheprovider` 전체 PASS.
- [ ] `test_paper_engine.py`, `test_paper_runner.py`, `test_dry_run_controller.py` 신규 테스트가 위 모든 분기를 검증.
- [ ] `patch.md` 가 변경 파일 / submit_intents 흐름 설명 / RiskEngine·OMS·PaperBroker 경계 유지 확인 / dry-run controller 통합 방식 / live trading 비활성 / market order 가드 유지 / secret 비노출 / 테스트 결과 / **Claude 검증 요청 프롬프트** / **REQUEST CHANGES·BLOCK 시 follow-up Codex 수정 프롬프트 작성 규칙** 을 모두 포함.

자동화 금지:

- [ ] commit / push / merge / PR / deploy 가 수행되지 않았다.
- [ ] `.env` / secret / credential / API key / token 이 수정/노출되지 않았다.
