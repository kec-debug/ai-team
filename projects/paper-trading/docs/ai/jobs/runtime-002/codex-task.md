# Codex 작업 지시문 — runtime-002

## 0. 너의 역할

너는 Codex 구현자다. 이 문서와 `plan.md` 만 따른다. 범위를 임의로 넓히지 않는다. 안전 규칙을 위반하지 않는다. commit / push / merge / deploy 는 절대 하지 않는다. `.env`, secret, API key, token, 계좌번호 raw 값을 읽지도 쓰지도 노출하지도 않는다.

## 1. 컨텍스트 요약

`PaperEngine.on_quote(quote)` 는 이미 `PaperBroker.tick(quote)` 결과 `Fill` 을 `PaperAccount`, `PortfolioService`, `PaperJournal` 에 적용한다. 그러나 **주문 제출** 은 외부 caller 가 `oms.place(intent)` 를 직접 호출해야 했고, dry-run controller 도 PaperRunner 를 거쳐 OMS 직접 호출 경로만 가졌다.

본 작업은 `PaperEngine` 에 `submit_intents()` 단일 진입점을 추가하여 `OrderIntent` 목록을 `RiskEngine → OMS → PaperBroker.submit` 으로 통과시키고, 결과 (accepted/rejected/blocked counts, oms_ids, rejection reasons) 를 batch 로 반환한다. `submit_intents` 후 `on_quote` 가 호출되면 동일한 broker/account/portfolio/journal 상태를 공유한다. `PaperRunner` 는 선택적 `paper_engine` 을 받아 dry-run controller 가 새 진입점을 사용할 수 있게 한다.

production wiring (`app/api/server.py`) 의 PaperEngine↔OMS 연결은 본 job 범위에서 명시적으로 미적용 (별 job 으로 분리). 기존 GUI / KIS / OMS / RiskEngine / PaperBroker / strategy / dry_run 모듈의 핵심 로직은 변동 없음.

## 2. 절대 금지

- live trading 활성화. `LIVE_TRADING_ENABLED=true` 추가.
- `ALLOW_MARKET_ORDERS=true` reject 정책 풀기. `OrderType.MARKET` 3중 가드 우회. `OrderType.STOP` 도입.
- 실 broker API 호출. KIS endpoint / TR ID / payload / header 추측. KIS HTTP 구현 추가.
- Strategy / Agent / LLM 이 broker 를 직접 호출하거나 `BrokerOrder` 를 만드는 경로 추가. OMS / RiskEngine 우회.
- OMS 미경유로 PaperBroker.submit 직접 호출. PaperBroker 가 OMS 가 만든 `BrokerOrder` 외 다른 입력을 받게 하는 변경.
- FX 변환 / 환율 상수 / base currency 통합 함수 도입.
- 외부 HTTP 라이브러리 (`requests`, `httpx`, `aiohttp`, `urllib3`) import.
- `.env` 읽기/수정. `.env.example` 에 실제 값 추가. 실제 app key / app secret / access token / Bearer / 계좌번호를 코드 / 문서 / 테스트 / patch 에 기록.
- GUI 파일 (`app/api/*`, `app/static/*`, `app/main.py`) 수정. `app/api/server.py` 의 production wiring 변경. **본 job 에서 server.py 의 `PaperEngine(...)` 생성에 `oms` 를 주입하지 않는다.**
- `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/base.py`, `app/broker/kis*.py`, `app/domain/*`, `app/strategy/*`, `app/session/*`, `app/runtime/paper_journal.py`, `app/runtime/paper_status.py`, `app/runtime/dry_run.py`, `app/runtime/dry_run_report.py`, `app/config.py`, `docs/kis/*` 변경. (단, dry-run controller 테스트에서 paper_engine 주입 PaperRunner 를 구성하는 변경은 테스트 파일 안에서만 한다 — 컨트롤러 소스는 변경 금지.)
- 자동 git commit / push / merge / deploy.

## 3. 수정·생성 파일 화이트리스트

수정 (MODIFY):

- `projects/paper-trading/app/runtime/paper_engine.py` — `IntentSubmitResult`, `SubmitIntentsBatchResult` 추가. `__init__` 에 `oms` keyword-only 파라미터 추가. `submit_intents` 메서드 추가. `_classify_rejection` 모듈 함수 추가.
- `projects/paper-trading/app/runtime/paper_runner.py` — `__init__` 의 `oms` 를 default `None`, 신규 keyword-only `paper_engine` 추가. `run_once` 에 paper_engine 경로 분기 추가.
- `projects/paper-trading/tests/test_paper_engine.py` — 기존 3 테스트 보존 + 신규 9 개 테스트.
- `projects/paper-trading/tests/test_paper_runner.py` — 기존 2 테스트 보존 + 신규 3 개 테스트.
- `projects/paper-trading/tests/test_dry_run_controller.py` — 기존 테스트 보존 + 신규 1 개 테스트.
- `projects/paper-trading/README.md` — 선택, 1-2 줄 안내.

생성 (NEW):

- `projects/paper-trading/docs/ai/jobs/runtime-002/patch.md` — 구현 후 너의 요약 + Claude 검증 요청 프롬프트 + REQUEST CHANGES/BLOCK 시 follow-up Codex 수정 프롬프트 작성 규칙.

위 목록에 없는 파일은 절대 수정/생성하지 않는다. 특히 `server.py`, `routes.py`, `dashboard.html`, `main.py`, OMS / RiskEngine / PaperBroker / Strategy / KIS 어댑터 / dry_run.py 어떤 것도 변경하지 않는다.

## 4. 단계별 작업

### 4.1 `app/runtime/paper_engine.py`

기존 파일 상단에 import 와 신규 dataclass 추가:

```python
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from app.broker.paper import PaperBroker
from app.config import Settings
from app.domain.enums import Session
from app.domain.orders import OrderIntent
from app.domain.quote import Quote
from app.oms.manager import OMS
from app.portfolio.account import PaperAccount, PaperAccountError
from app.portfolio.service import PortfolioService
from app.runtime.paper_journal import PaperJournal, TradeLogEntry
```

기존 `from app.broker.paper ...` 등은 그대로. 새 import 만 추가.

신규 dataclass:

```python
@dataclass(frozen=True)
class IntentSubmitResult:
    intent: OrderIntent
    accepted: bool
    oms_id: str | None
    broker_order_id: str | None
    status: str | None
    rejected_by: str | None      # "risk_engine" | "oms" | None
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

신규 helper:

```python
def _classify_rejection(reason: str) -> str:
    return "risk_engine" if reason.startswith("RiskEngine rejected") else "oms"
```

`PaperEngine.__init__` 시그니처:

```python
def __init__(
    self,
    settings: Settings,
    *,
    broker: PaperBroker | None = None,
    account: PaperAccount | None = None,
    portfolio: PortfolioService | None = None,
    journal: PaperJournal | None = None,
    oms: OMS | None = None,
) -> None:
    ...
    self._oms = oms
```

기존 default 객체 생성 (broker / account / portfolio / journal) 분기 그대로. 그 외 메서드 (`on_quote`, `mark_quote`, `cash_by_currency`) 본문 변경 금지.

신규 메서드:

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
    accepted_oms_ids: list[str] = []
    accepted_broker_order_ids: list[str] = []
    accepted_count = 0
    risk_rejected_count = 0
    oms_rejected_count = 0
    for intent in materialized:
        try:
            ack = self._oms.place(intent)
        except (RuntimeError, ValueError) as exc:
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
```

주의:

- `OMS.place` 는 RuntimeError 만 raise 한다 (실 코드). PaperBroker.submit 의 ValueError ("unsupported order type") 는 RiskEngine 가드를 통과한 뒤 broker 가 raise 할 수 있는 안전망 — 같은 except 절에서 처리해도 안전.
- OMS 가 raise 한 시점에서는 `PaperBroker.submit` 가 호출되지 않았으므로 `broker._open_orders` 에 등록되지 않는다. 이 안전 가드를 테스트로 검증.
- 결과 dataclass 는 frozen. 호출자가 mutate 불가.
- `submit_intents` 는 로깅 / print / file write 를 하지 않는다.

### 4.2 `app/runtime/paper_runner.py`

기존 import 위에 추가:

```python
from app.domain.enums import TradingMode
from app.domain.orders import OrderAck
from app.runtime.paper_engine import PaperEngine
```

`PaperRunner.__init__` 시그니처:

```python
def __init__(
    self,
    settings,
    strategy: Strategy,
    oms=None,
    *,
    paper_engine: PaperEngine | None = None,
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
        ack: OrderAck | None = None
        error: str | None = None
        if strategy_result.passed and strategy_result.non_executable_order_intent is not None:
            intent = strategy_result.non_executable_order_intent
            if self._paper_engine is not None:
                batch = self._paper_engine.submit_intents([intent])
                first = batch.results[0]
                if first.accepted and first.oms_id is not None:
                    ack = OrderAck(
                        oms_id=first.oms_id,
                        broker_order_id=first.broker_order_id,
                        status=first.status or "accepted",
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

`PaperRunResult` 의 dataclass 정의는 변경하지 않는다. dry_run controller 의 `_classify_oms_error` 등 기존 처리가 동일하게 동작하도록 reason 문자열을 그대로 전달.

### 4.3 `app/api/server.py` 는 변경 금지

production wiring 은 그대로 유지: `paper_engine = PaperEngine(settings, broker=broker, portfolio=portfolio)`. `oms` 미주입 상태이므로 `paper_engine.submit_intents` 는 production HTTP 경로에서 호출되지 않는다. `/paper/order/simulate` 는 기존 `request.app.state.oms.place(intent)` + `engine.on_quote(quote)` 경로 그대로 (routes.py 변경 금지).

### 4.4 `tests/test_paper_engine.py`

기존 3 테스트는 그대로 유지. 다음 신규 테스트를 추가한다.

```python
from dataclasses import FrozenInstanceError, replace

from app.domain.enums import OrderType, Session, Side, TradingMode
from app.domain.orders import BrokerOrder, Order, OrderIntent
from app.oms.manager import OMS
from app.risk.engine import RiskEngine
from app.runtime.paper_engine import (
    IntentSubmitResult,
    PaperEngine,
    SubmitIntentsBatchResult,
)


def _intent(symbol="AAPL", quantity=2, limit=Decimal("10"), order_type=OrderType.LIMIT, currency="USD"):
    return OrderIntent(
        symbol=symbol,
        side=Side.BUY,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit,
        currency=currency,
    )


def _wire(settings, *, allowlist=None, **overrides):
    s = settings
    if allowlist is not None:
        s = replace(s, symbol_allowlist=allowlist)
    for key, value in overrides.items():
        s = replace(s, **{key: value})
    broker = PaperBroker(max_fill_ratio_of_volume=Decimal("1"))
    risk = RiskEngine(s)
    oms = OMS(s, risk, broker)
    account = PaperAccount(cash={"USD": Decimal("100")})
    journal = PaperJournal()
    engine = PaperEngine(s, broker=broker, account=account, journal=journal, oms=oms)
    return engine, broker, account, journal
```

- `test_submit_intents_requires_oms` — `PaperEngine(settings)` (oms 미주입) 에서 `submit_intents([_intent()])` 시 `RuntimeError("PaperEngine.submit_intents requires an OMS")`.
- `test_submit_intents_rejects_non_intent_input` — wire 후 broker_order (BrokerOrder 인스턴스), Order 인스턴스, dict 각각에 대해 `TypeError("submit_intents accepts OrderIntent only ...")`.
- `test_submit_intents_happy_path_passes_through_risk_and_oms` — wire 후 `submit_intents([_intent()])`. result.accepted_count == 1, rejected_count == 0, results[0].accepted is True, results[0].rejected_by is None, results[0].reason is None, results[0].oms_id is truthy, results[0].broker_order_id is truthy, len(broker.open_orders()) == 1.
- `test_submit_intents_risk_rejected_does_not_reach_broker` — `_wire(allowlist=("AAPL",))` + `_intent(symbol="TSLA")`. result.risk_rejected_count == 1, accepted_count == 0, results[0].rejected_by == "risk_engine", results[0].reason.startswith("RiskEngine rejected"), broker.open_orders() == []. broker._open_orders 사이즈 0.
- `test_submit_intents_oms_rejected_does_not_reach_broker` — `_wire(live_trading_enabled=True)` + `_intent()`. result.oms_rejected_count == 1, accepted_count == 0, results[0].rejected_by == "oms", results[0].reason == "OMS refuses live trading in Phase 1", broker.open_orders() == [].
- `test_submit_intents_market_order_blocked_by_default_guard` — `_wire()` + `_intent(order_type=OrderType.MARKET)`. result.risk_rejected_count == 1, results[0].reason.contains "paper_market_orders_disabled" (RiskEngine 메시지: "RiskEngine rejected: paper_market_orders_disabled").
- `test_submit_intents_then_on_quote_flows_fill_through_engine` — `_wire()`. `submit_intents([_intent(quantity=2, limit=Decimal("10"))])`. 이어 `engine.on_quote(Quote("AAPL", Decimal("10"), Decimal("10"), Decimal("10"), 100, datetime.now(timezone.utc), "test", Session.REGULAR, "USD"))`. 결과 trades 길이 1, account.cash_balance("USD") == Decimal("80") (100 - 2*10), engine.portfolio.get_snapshot().positions["AAPL"].quantity == 2, journal.trades 길이 1.
- `test_submit_intents_partial_fill_preserved` — broker 의 `max_fill_ratio_of_volume=Decimal("0.5")` 로 wire. submit_intents 로 qty=10 LIMIT 10 매수, quote volume=10 (max fill = 5). on_quote → trades 1 건, fill quantity 5, broker.open_orders() 의 남은 order quantity 5.
- `test_submit_intents_results_immutable_and_secret_free` — `_wire()` + accepted 결과. `SubmitIntentsBatchResult` 와 `IntentSubmitResult` 가 frozen. `result.accepted_count = 99` 시 `FrozenInstanceError`. `repr(result)` 에 `fake-key`, `fake-secret`, `Bearer `, `12345678` 미등장.

각 테스트는 한 함수에 하나의 단일 assertion 묶음으로 작성.

### 4.5 `tests/test_paper_runner.py`

기존 2 테스트 유지. 신규:

```python
from datetime import datetime, timezone
from unittest.mock import Mock

from app.domain.enums import TradingMode
from app.runtime.paper_engine import IntentSubmitResult, SubmitIntentsBatchResult


def _ok_batch(intent):
    return SubmitIntentsBatchResult(
        submitted_count=1,
        accepted_count=1,
        rejected_count=0,
        risk_rejected_count=0,
        oms_rejected_count=0,
        results=(
            IntentSubmitResult(
                intent=intent,
                accepted=True,
                oms_id="oms-x",
                broker_order_id="br-y",
                status="accepted",
                rejected_by=None,
                reason=None,
                submitted_at=datetime.now(timezone.utc),
            ),
        ),
        accepted_oms_ids=("oms-x",),
        accepted_broker_order_ids=("br-y",),
    )


def _reject_batch(intent, reason="RiskEngine rejected: symbol_not_allowed", by="risk_engine"):
    return SubmitIntentsBatchResult(
        submitted_count=1,
        accepted_count=0,
        rejected_count=1,
        risk_rejected_count=1 if by == "risk_engine" else 0,
        oms_rejected_count=0 if by == "risk_engine" else 1,
        results=(
            IntentSubmitResult(
                intent=intent,
                accepted=False,
                oms_id=None,
                broker_order_id=None,
                status=None,
                rejected_by=by,
                reason=reason,
                submitted_at=None,
            ),
        ),
        accepted_oms_ids=(),
        accepted_broker_order_ids=(),
    )
```

테스트:

- `test_paper_runner_routes_through_paper_engine_when_provided` — Mock paper_engine, oms None. `paper_engine.submit_intents.side_effect = lambda intents: _ok_batch(intents[0])`. runner.run_once → result.oms_ack.status == "accepted", result.oms_ack.oms_id == "oms-x", result.oms_ack.broker_order_id == "br-y", result.oms_error is None. paper_engine.submit_intents.call_count == 1 — `oms` 가 None 이므로 oms.place 미호출 (이미 None 이라 검증 불필요, 호출되면 AttributeError).
- `test_paper_runner_paper_engine_rejection_captured_in_oms_error` — Mock paper_engine 가 _reject_batch 반환. result.oms_ack is None, result.oms_error == "RiskEngine rejected: symbol_not_allowed".
- `test_paper_runner_requires_oms_or_paper_engine` — `PaperRunner(settings, strategy)` 시 `ValueError("PaperRunner requires oms or paper_engine")`.

### 4.6 `tests/test_dry_run_controller.py`

기존 테스트 전부 유지. 신규 1 개 추가:

- `test_controller_routes_through_paper_engine_when_runner_wired_with_paper_engine` — 실 RiskEngine + PaperBroker + OMS + PaperEngine (oms 주입) 으로 PaperRunner 구성. controller.start → controller.tick([make_snapshot()]) 후 summary["counters"]["dry_run_orders_created"] == 1, summary["counters"]["candidates_passed_risk"] == 1, len(broker.open_orders()) == 1. 이어 engine.on_quote(quote) 호출 시 journal.trades 가 갱신되어 같은 broker/account/portfolio/journal 상태를 공유함을 검증.

### 4.7 README (선택)

`projects/paper-trading/README.md` 에 paper engine 또는 runtime 안내 위치에 1-2 줄 추가:

> `PaperEngine.submit_intents(intents)` 는 `OrderIntent` 목록만 받아 `RiskEngine → OMS → PaperBroker.submit` 경로로 보내고 accepted/rejected 결과 batch 를 반환한다. 이어 `engine.on_quote(quote)` 가 호출되면 같은 broker/account/portfolio/journal 상태로 fill, cash, position, journal 이 갱신된다.

live trading / market order / KIS HTTP 관련 안내는 추가하지 않는다.

### 4.8 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

전체 PASS 여야 한다. 회귀 0 건.

추가로 다음 안전 grep 도 수행해 0 줄임을 확인:

```bash
grep -rn "ALLOW_MARKET_ORDERS=true" app tests
grep -rn "LIVE_TRADING_ENABLED=true" app tests
grep -rn "Bearer eyJ" app tests
grep -rn "OrderType.STOP" app tests
grep -rEn "import (requests|httpx|aiohttp|urllib3)" app tests
```

### 4.9 patch.md 작성 (필수)

`projects/paper-trading/docs/ai/jobs/runtime-002/patch.md` 를 다음 구조로 작성한다.

```markdown
# runtime-002 — Codex 구현 요약

## 변경된 파일
- app/runtime/paper_engine.py
- app/runtime/paper_runner.py
- tests/test_paper_engine.py
- tests/test_paper_runner.py
- tests/test_dry_run_controller.py
- README.md (선택)
- docs/ai/jobs/runtime-002/patch.md (본 파일)

## submit_intents 흐름

1. caller (test / dry-run controller / 미래의 GUI route) 가 `paper_engine.submit_intents([OrderIntent, ...])` 호출.
2. 각 intent 에 대해 `OMS.place(intent)` 호출. OMS 가 내부에서 `RiskEngine.evaluate` → 통과 시 `PaperBroker.submit(broker_order)`.
3. OMS 가 raise 한 경우 `IntentSubmitResult.accepted=False`, `rejected_by` 가 "risk_engine" / "oms" 로 분류, `reason` 에 raw 메시지. broker.submit 미호출이므로 broker._open_orders 에 등록되지 않음.
4. OMS 가 ack 반환 시 broker._open_orders 에 등록되고 `IntentSubmitResult.accepted=True`, `oms_id` / `broker_order_id` 포함.
5. caller 가 이어 `paper_engine.on_quote(quote)` 호출 시 PaperBroker.tick → Fill → PaperAccount.apply_fill → PortfolioService.apply_trade → PaperJournal 기존 흐름 그대로.

## 경계 유지 확인

- `OrderIntent` 외 입력 차단: `submit_intents` 가 `isinstance(item, OrderIntent)` 가 아니면 `TypeError`. Strategy/Agent 가 BrokerOrder 를 만들어 직접 넘길 수 없음.
- RiskEngine 거절 intent → broker._open_orders 비어 있음 (회귀 테스트 검증).
- OMS 인프라 거절 intent (live_enabled, non_paper_broker) → broker._open_orders 비어 있음.
- 승인된 intent 만 broker 에 등록.

## dry-run controller 통합 방식

- `PaperRunner.__init__(... , paper_engine=None)` 로 선택적 주입. paper_engine 이 있으면 `paper_engine.submit_intents([intent])` 경유, 없으면 기존 `oms.place(intent)` 경유 (후방 호환).
- `DryRunController` 자체 소스 변경 없음. 컨트롤러는 PaperRunner 결과 (`PaperRunResult`) 만 사용하며 PaperRunResult 모양 보존.
- production wiring (`app/api/server.py`) 은 변경 없음 — `paper_engine` 가 `oms` 없이 생성되어 본 job 에서는 production HTTP 경로에서 submit_intents 가 호출되지 않는다. 후속 job 에서 production wiring 전환.

## live trading 비활성 / 시장가 가드 유지

- `LIVE_TRADING_ENABLED=true` 추가 없음. RiskEngine.live_trading_disabled 가드 그대로.
- `ALLOW_MARKET_ORDERS=true` 도입 없음. `OrderType.MARKET` 3중 가드 (`allow_paper_market_orders` + `TradingMode.PAPER` + `live_trading_enabled=False`) 그대로. `OrderType.STOP` 미도입.
- 회귀 grep: `ALLOW_MARKET_ORDERS=true`, `LIVE_TRADING_ENABLED=true`, `OrderType.STOP`, `Bearer eyJ`, 외부 HTTP 라이브러리 import 모두 0 줄.

## secret / account / token 노출 없음

- `submit_intents` 입출력 어디에도 raw secret / 계좌번호 / access token 없음. `OrderAck.broker_order_id` 는 PaperBroker 가 `secrets.token_hex(8)` 로 생성한 무작위 ID (secret 아님).
- `repr(SubmitIntentsBatchResult)` / `repr(IntentSubmitResult)` 에 fixture 의 `fake-key`, `fake-secret`, `12345678`, `Bearer ` 미등장.
- 코드 / 테스트 / patch / docstring 어디에도 실 키 / 토큰 / 계좌번호 미기록.

## 테스트 결과

- compileall: OK
- pytest: N passed, 0 regressions
- 신규 / 갱신된 테스트 함수 목록: (Codex 가 채워 넣는다)

## Claude 검증 요청 프롬프트

다음 프롬프트를 그대로 Claude 에게 전달하면 본 작업 리뷰가 시작된다.

```
Use prompts/claude.md.
Project directory: /root/ai-dev-center/projects/ai-team/projects/paper-trading
Job ID: runtime-002
Job directory: /root/ai-dev-center/projects/ai-team/projects/paper-trading/docs/ai/jobs/runtime-002

Review the runtime-002 implementation.

Read:
- projects/paper-trading/docs/ai/jobs/runtime-002/request.ko.md
- projects/paper-trading/docs/ai/jobs/runtime-002/plan.md
- projects/paper-trading/docs/ai/jobs/runtime-002/codex-task.md
- projects/paper-trading/docs/ai/jobs/runtime-002/patch.md

Also review the current diff for:
- projects/paper-trading/app/runtime/paper_engine.py
- projects/paper-trading/app/runtime/paper_runner.py
- projects/paper-trading/tests/test_paper_engine.py
- projects/paper-trading/tests/test_paper_runner.py
- projects/paper-trading/tests/test_dry_run_controller.py
- projects/paper-trading/README.md

Write the review into:
projects/paper-trading/docs/ai/jobs/runtime-002/review.md

Review focus:
1. PaperEngine.submit_intents accepts only OrderIntent (Order/BrokerOrder rejected as TypeError).
2. RiskEngine and OMS gates are not bypassed; rejected/blocked intents never reach PaperBroker._open_orders.
3. Accepted intents reach PaperBroker.submit and the resulting state is shared with on_quote.
4. on_quote flow (PaperBroker.tick → Fill → PaperAccount → PortfolioService → PaperJournal) still passes.
5. LIMIT / STOP_LIMIT / MARKET behavior preserved; MARKET still blocked by the 3-guard default.
6. OrderType.STOP was not introduced.
7. No FX conversion / rate constant introduced.
8. No KIS HTTP, KIS endpoint, TR ID, payload added.
9. No third-party HTTP client imported.
10. .env, app key, app secret, account number, token, Bearer are not exposed.
11. Strategy/Agent/LLM cannot create BrokerOrder or call broker directly through this entrypoint.
12. dry-run controller integration uses submit_intents through PaperRunner without bypassing OMS.
13. GUI files (app/api/*, app/static/*, app/main.py) were not modified.
14. server.py production wiring was not modified.
15. Tests passed: N passed (Codex's reported count).
16. Scope stayed within runtime-002.

Verdict must be one of:
APPROVE
REQUEST CHANGES
BLOCK

Do not commit, push, merge, deploy, or run arbitrary shell commands.
```

위 프롬프트의 `N passed` 자리에 본 patch.md 의 실제 pytest passed 수를 채워 넣어 사용자에게 전달한다.

## Claude 리뷰가 REQUEST CHANGES / BLOCK 일 때 follow-up Codex 수정 프롬프트 작성 규칙

Claude 리뷰 결과가 `APPROVE` 가 아닐 때에만 다음 절차에 따라 사용자가 Codex 에게 보낼 수정 프롬프트를 작성한다. `APPROVE` 라면 별도 프롬프트가 필요 없다.

규칙:

1. 프롬프트는 한국어로 작성하고 다음 헤더를 첫 줄에 둔다.
   `Use prompts/codex-implementer.md.`
2. 두 번째 블록에 Project directory, Job ID, Job directory, 원래 plan/codex-task/patch/review 경로를 명시한다.
3. 본문 첫 줄에 Claude review verdict 와 review.md 경로를 명시한다.
4. 다음 항목을 차례로 포함한다.
   - **반영해야 할 finding 목록**: review.md 의 Critical / Major 모든 항목과 사용자가 수동으로 추가한 Minor 중 반영하기로 결정한 항목만 (Minor 모두 자동 반영 금지). 각 finding 마다 review.md 의 file_path:line_number 인용.
   - **수정 범위 화이트리스트**: 본 job 의 `수정·생성 파일 화이트리스트` 그대로 (확장 금지).
   - **절대 금지** 항목: 본 codex-task §2 와 동일한 항목을 그대로 재명시 (live trading / market order / KIS HTTP / OMS 우회 / GUI 변경 / git 자동화 등).
   - **테스트 갱신 지시**: 회귀 0 건 유지, 신규 finding 에 대응하는 회귀 테스트 추가, 기존 테스트 보존.
   - **patch.md 갱신 지시**: 변경된 파일 / 흐름 / 안전 회귀 / 테스트 결과 + 새 Claude 검증 요청 프롬프트 (review.md 의 finding 들에 대해 해결 여부를 확인하도록 보강).
5. 절대 포함 금지: 자동 git commit / push / merge / deploy 명령. `.env` 수정 지시. 실 secret. 시장가 / live trading 활성화. 새 KIS endpoint / TR ID / payload 추측.
6. 프롬프트 말미에 다음 문장 1 줄을 둔다:
   `Do not commit, push, merge, deploy, or run arbitrary shell commands.`

템플릿 예시 (review.md 가 BLOCK + finding 2 건일 경우):

```
Use prompts/codex-implementer.md.
Project directory: /root/ai-dev-center/projects/ai-team/projects/paper-trading
Job ID: runtime-002
Job directory: projects/paper-trading/docs/ai/jobs/runtime-002

Claude review verdict: BLOCK
Review file: projects/paper-trading/docs/ai/jobs/runtime-002/review.md

다음 finding 을 해결한다.

1. (Critical) <review.md 의 finding 1 인용 — file_path:line_number 포함, 해결 방향 1 줄>
2. (Major) <review.md 의 finding 2 인용 — file_path:line_number 포함, 해결 방향 1 줄>

수정 범위는 codex-task.md §3 의 화이트리스트를 그대로 유지한다.

절대 금지:
- live trading / `LIVE_TRADING_ENABLED=true` / `ALLOW_MARKET_ORDERS=true` 도입.
- `OrderType.STOP` 도입. 시장가 3중 가드 우회.
- KIS endpoint / TR ID / payload 추가, 실 broker API 호출.
- OMS / RiskEngine 우회.
- 외부 HTTP 라이브러리 import.
- `.env` 또는 secret 변경.
- GUI 파일 (`app/api/*`, `app/static/*`, `app/main.py`) 수정.
- `app/api/server.py` production wiring 변경.
- 자동 git commit / push / merge / deploy.

테스트:
- 회귀 0 건 유지.
- 각 finding 에 대응하는 회귀 테스트 1 개 이상 추가.
- 기존 테스트 전부 보존.

patch.md 갱신:
- 위 finding 별 해결 방식 요약.
- 변경 파일 / 흐름 / 안전 회귀 / 테스트 결과 (전체 pytest 통과 count).
- 새 Claude 검증 요청 프롬프트 (위 finding 들의 해결 여부를 확인하는 항목 추가).

Do not commit, push, merge, deploy, or run arbitrary shell commands.
```

`REQUEST CHANGES` 일 경우 Critical/Major 가 없을 수 있다. 그 때는 사용자가 review.md 에서 반영하기로 결정한 항목만 본문에 옮긴다. Minor 만 있고 사용자가 모두 다음 job 으로 미루면 follow-up Codex 프롬프트는 작성하지 않는다.
```

위 patch.md 의 "Claude 검증 요청 프롬프트" 와 "follow-up Codex 수정 프롬프트 작성 규칙" 두 섹션은 plan.md §1 의 마지막 두 bullet 을 충족하기 위한 필수 산출물이다. 빠뜨리지 말 것.

## 5. 자가 점검 (구현 후 PR 전)

- [ ] `submit_intents` 가 `OrderIntent` 외 입력에 대해 `TypeError`.
- [ ] OMS 미주입 PaperEngine 에서 `submit_intents` 호출 시 `RuntimeError`.
- [ ] RiskEngine / OMS 거절 intent 는 `broker.open_orders()` 에 등록되지 않는다.
- [ ] 승인된 intent 만 broker 에 등록되고 `SubmitIntentsBatchResult.accepted_oms_ids` / `accepted_broker_order_ids` 에 포함된다.
- [ ] `submit_intents` 후 `on_quote` 가 같은 broker / account / portfolio / journal 을 갱신한다.
- [ ] `OrderType.MARKET` 기본 가드 동작 회귀 OK.
- [ ] `OrderType.STOP` 등 새 enum 값 미도입.
- [ ] `app/oms/`, `app/risk/`, `app/portfolio/`, `app/broker/`, `app/domain/`, `app/strategy/`, `app/session/`, `app/main.py`, `app/api/`, `app/static/`, `app/config.py`, `app/runtime/paper_journal.py`, `app/runtime/paper_status.py`, `app/runtime/dry_run.py`, `app/runtime/dry_run_report.py` 변경 없음.
- [ ] 외부 HTTP 라이브러리 import 없음.
- [ ] `.env` / `.env.example` 변동 없음. secret / 계좌번호 / token / Bearer 코드 · 테스트 · patch 어디에도 없음.
- [ ] `python -m compileall app tests` 와 `python -m pytest -p no:cacheprovider` 가 전부 통과.
- [ ] `patch.md` 가 Claude 검증 요청 프롬프트 와 REQUEST CHANGES/BLOCK 시 follow-up Codex 수정 프롬프트 작성 규칙을 모두 포함.
- [ ] commit / push / merge / deploy 를 너가 직접 실행하지 않았다.
