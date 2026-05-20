# paper-e2e-001 — Codex 구현 지시문

You are Codex, implementing the plan at `docs/ai/jobs/paper-e2e-001/plan.md` inside the `projects/paper-trading` package.

Read first (in order):

1. `docs/ai/CLAUDE_CODEX_WORKFLOW.md` (root) — workflow + safety rules.
2. `docs/ai/jobs/paper-e2e-001/request.ko.md` — original Korean request.
3. `docs/ai/jobs/paper-e2e-001/plan.md` — this task's plan. Stay within scope.
4. `projects/paper-trading/app/api/server.py` — how the pipeline is wired in production (PaperBroker shared between OMS and PaperEngine).
5. `projects/paper-trading/app/runtime/paper_engine.py`, `paper_runner.py`, `paper_journal.py`, `paper_status.py`, `dry_run.py`.
6. `projects/paper-trading/app/oms/manager.py`, `app/risk/engine.py`, `app/portfolio/account.py`, `app/portfolio/service.py`, `app/strategy/premarket_gap.py`.
7. `projects/paper-trading/app/broker/paper.py`, `app/broker/kis.py` (especially the `place_order` dry-run branch + `_order_transport` from api-orders-paper-001).
8. `projects/paper-trading/tests/conftest.py` (provides `settings` + `make_snapshot` fixtures).
9. `projects/paper-trading/tests/test_paper_e2e_api.py` — existing TestClient regression that already exercises `/paper/order/simulate`. Reuse its style.

## Absolute prohibitions (block immediately if any apply)

- Do not enable live trading. Do not call live KIS endpoints. Do not add the live base URL to any new code path.
- Do not introduce live or paper-unsupported TR_IDs (`TTTT1002U`, `TTTT1006U`, `TTTT1004U`, `TTTS1002U`, `TTTS1001U`, `TTTS0307U`, `TTTS0308U`, `TTTS0309U`, `TTTT3014U`, `TTTT3016U`, `TTTT3017U`, `TTTS3013U`, `TTTS3018R`, `TTTT3039R`, `TTTS3014R`, `TTTS6036U`, `TTTS6037U`, `TTTS6038U`, `TTTS6058R`, `TTTS6059R`). Only the existing paper TR_IDs (`VTTT1002U` / `VTTT1001U`) may be referenced indirectly via existing constants — do not type new TR_ID literals.
- Do not invent KIS endpoints, TR IDs, headers, payloads, or response fields.
- Do not import external HTTP libraries (`requests`, `httpx`, `aiohttp`, `urllib3`).
- **Do not modify any file under `app/`** (production code). This job is test-only by default. If you discover a case where the existing production code cannot satisfy the end-to-end chain, STOP. Add a `## Production change required` section to `patch.md` describing the gap, propose the narrowest possible fix, and request human approval before editing `app/`.
- Do not modify `tests/conftest.py` or any existing test file. Add only new tests in a new file.
- Do not change `OrderType.MARKET` guards, `ALLOW_MARKET_ORDERS=true` reject, kill-switch behavior, OMS contract, RiskEngine contract, or the Strategy → RiskEngine → OMS → Broker order of operations.
- Do not introduce `OrderType.STOP`, FX conversion functions, exchange rate constants, or new env variables.
- Do not read or modify `.env` / `.env.example`. Do not write actual app keys, app secrets, account numbers, access tokens, or Bearer tokens anywhere — code, tests, docstrings, patch.md.
- Do not modify `docs/kis/MISSING_OFFICIAL_VALUES.md` or any GUI file (`app/api/*`, `app/static/*`, `app/main.py`).
- Do not run `git commit`, `git push`, `git merge`, PR creation, or deployment commands.

## Allowed file changes

| Path | Action |
| --- | --- |
| `projects/paper-trading/tests/test_paper_e2e_pipeline.py` | Create per §1 below. |
| `projects/paper-trading/docs/ai/jobs/paper-e2e-001/patch.md` | Create per §4. |

No other files. If any other file must change, STOP and explain in `patch.md` instead.

## 1. New test file `tests/test_paper_e2e_pipeline.py`

### 1.1 Imports

```python
import json
import pathlib
import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.server import create_app
from app.broker.kis import KisBroker, KisOrderRejectedError
from app.broker.paper import PaperBroker
from app.config import Settings, load_settings
from app.domain.enums import OrderType, Session, Side, TradingMode
from app.domain.market import StrategyInput
from app.domain.orders import BrokerOrder, OrderIntent
from app.domain.quote import Quote
from app.oms.manager import OMS
from app.portfolio.account import PaperAccount
from app.portfolio.service import PortfolioService
from app.risk.engine import RiskEngine
from app.runtime.paper_engine import PaperEngine
from app.runtime.paper_journal import PaperJournal
from app.runtime.paper_runner import PaperRunner
from app.strategy.premarket_gap import PremarketGapVolumeBreakoutStrategy
```

### 1.2 Local helpers

Define these inside the file (no conftest changes):

```python
def _wire_paper_pipeline(settings):
    risk = RiskEngine(settings)
    broker = PaperBroker(
        max_quote_age_seconds=settings.paper_max_quote_age_seconds,
        allowed_sessions={Session(s) for s in settings.paper_allowed_sessions},
        max_fill_ratio_of_volume=settings.paper_max_fill_ratio_of_volume,
        commission_per_share=settings.paper_commission_per_share,
        commission_per_fill=settings.paper_commission_per_fill,
    )
    oms = OMS(settings, risk, broker)
    portfolio = PortfolioService()
    starting_cash = dict(
        settings.paper_starting_cash_by_currency
        or {settings.paper_base_currency: settings.paper_starting_cash}
    )
    account = PaperAccount(cash=starting_cash)
    journal = PaperJournal()
    paper_engine = PaperEngine(
        settings,
        broker=broker,
        account=account,
        portfolio=portfolio,
        journal=journal,
        oms=oms,
    )
    strategy = PremarketGapVolumeBreakoutStrategy(settings)
    runner = PaperRunner(settings, strategy, oms=oms, paper_engine=paper_engine)
    return {
        "strategy": strategy,
        "risk": risk,
        "broker": broker,
        "account": account,
        "portfolio": portfolio,
        "journal": journal,
        "oms": oms,
        "paper_engine": paper_engine,
        "runner": runner,
    }


def _matching_quote(snapshot, *, volume=500_000):
    return Quote(
        symbol=snapshot.symbol,
        last=snapshot.ask,
        bid=snapshot.bid,
        ask=snapshot.ask,
        volume=volume,
        timestamp=datetime.now(timezone.utc),
        source="e2e_test",
        session=Session.REGULAR,
        currency="USD",
    )


def _kis_paper_settings(settings, **overrides):
    data = {
        "kis_env": "paper",
        "kis_account_no": "12345678-01",
        "kis_app_key": "fake-key-XYZ",
        "kis_app_secret": "fake-secret-XYZ",
        "kis_api_mode": "paper",
        "kis_order_dry_run": True,
    }
    data.update(overrides)
    return replace(settings, **data)


class _RaiseOnCallOrderTransport:
    """KisOrderTransport that asserts no HTTP path is ever invoked."""

    def submit_order(self, **kwargs):  # pragma: no cover — invocation is a failure
        raise AssertionError(
            "KisBroker dry-run unexpectedly invoked the order transport; kwargs="
            + ", ".join(sorted(kwargs))
        )


def _build_intent(symbol="AAPL", side=Side.BUY, quantity=10, limit=Decimal("100.50"), order_type=OrderType.LIMIT):
    return OrderIntent(
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit,
        currency="USD",
        client_tag="e2e_test",
        quote_timestamp=datetime.now(timezone.utc),
    )


def _order_payload(**overrides):
    payload = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 1,
        "order_type": "limit",
        "limit_price": "100",
        "stop_price": None,
        "mock_bid": "99",
        "mock_ask": "100",
        "mock_last": "100",
        "mock_volume": 100,
        "currency": "USD",
    }
    payload.update(overrides)
    return payload
```

`make_snapshot` and `settings` fixtures come from `tests/conftest.py` — do not redefine them.

### 1.3 Required test functions

Implement these test functions with the exact names below.

#### `test_e2e_happy_path_strategy_to_fill_through_oms_paper_engine`

```python
def test_e2e_happy_path_strategy_to_fill_through_oms_paper_engine(settings, make_snapshot):
    components = _wire_paper_pipeline(settings)
    runner = components["runner"]
    broker = components["broker"]
    paper_engine = components["paper_engine"]
    account = components["account"]
    portfolio = components["portfolio"]
    journal = components["journal"]

    snapshot = make_snapshot(
        symbol="AAPL",
        previous_close=Decimal("100"),
        current_price=Decimal("106"),
        premarket_high=Decimal("106"),
        premarket_volume=200_000,
        bid=Decimal("105.90"),
        ask=Decimal("106.00"),
    )

    results = runner.run_once([snapshot])
    assert len(results) == 1
    assert results[0].strategy.passed is True
    assert results[0].oms_ack is not None
    assert results[0].oms_error is None

    open_orders = broker.open_orders()
    assert len(open_orders) == 1
    assert open_orders[0].symbol == "AAPL"
    assert open_orders[0].side is Side.BUY
    assert open_orders[0].order_type is OrderType.LIMIT
    assert open_orders[0].risk_token  # populated by RiskEngine.evaluate

    starting_cash = dict(account.cash)
    trades = paper_engine.on_quote(_matching_quote(snapshot))
    assert len(trades) >= 1
    assert trades[0].symbol == "AAPL"
    assert trades[0].oms_id == results[0].oms_ack.oms_id

    assert account.cash["USD"] < starting_cash["USD"]
    snapshot_portfolio = portfolio.get_snapshot()
    assert "AAPL" in snapshot_portfolio.positions
    assert snapshot_portfolio.positions["AAPL"].quantity > 0
    assert len(journal.trades) >= 1
    assert journal.trades[0].symbol == "AAPL"
```

#### `test_e2e_strategy_blocker_does_not_reach_oms_or_broker`

Use `premarket_volume=10` to trigger `volume_below_threshold`. Spy on OMS.place with a Mock wrapping it OR assert `broker.open_orders()` is empty. Then call `paper_engine.on_quote(...)` and assert no trades.

#### `test_e2e_risk_engine_reject_does_not_reach_broker`

Use `replace(settings, symbol_allowlist=("MSFT",))` to force RiskEngine to reject the AAPL intent. Drive the full pipeline twice: (a) via `runner.run_once([snapshot])` — assert `results[0].oms_error` contains `"RiskEngine rejected"`; (b) via `paper_engine.submit_intents([_build_intent()])` — assert `batch.results[0].accepted is False` and `batch.results[0].rejected_by == "risk_engine"`. In both cases assert `broker.open_orders()` is empty.

#### `test_e2e_oms_rejects_non_paper_broker_mode`

Construct a minimal stand-in broker with `mode != TradingMode.PAPER`:

```python
class _NonPaperBroker:
    mode = TradingMode.LIVE  # value object only; never actually used to place orders

oms = OMS(settings, RiskEngine(settings), _NonPaperBroker())
with pytest.raises(RuntimeError, match="OMS rejects non-paper broker"):
    oms.place(_build_intent())
```

#### `test_e2e_oms_rejects_live_trading_enabled`

```python
bad_settings = replace(settings, live_trading_enabled=True)
components = _wire_paper_pipeline(bad_settings)
with pytest.raises(RuntimeError, match="OMS refuses live trading"):
    components["oms"].place(_build_intent())
```

#### `test_e2e_kis_dry_run_returns_dry_run_ack_without_http`

```python
def test_e2e_kis_dry_run_returns_dry_run_ack_without_http(settings):
    kis_settings = _kis_paper_settings(
        settings,
        symbol_allowlist=("AAPL",),
    )
    risk = RiskEngine(kis_settings)
    kis_broker = KisBroker(kis_settings)
    kis_broker._order_transport = _RaiseOnCallOrderTransport()
    oms_kis = OMS(kis_settings, risk, kis_broker)

    intent = _build_intent()
    ack = oms_kis.place(intent)

    assert ack.status == "dry_run"
    assert ack.broker_order_id is None
    assert ack.mode is TradingMode.PAPER
    assert kis_broker.last_order_preview is not None
    assert kis_broker.last_order_response is None
    assert kis_broker.last_error is None

    health = kis_broker.healthcheck()
    assert health["order_dry_run"] is True
    assert health["order_execution_implemented"] is False
    assert health["order_methods_fail_closed"] is True
```

If `_RaiseOnCallOrderTransport.submit_order` is ever invoked, the test fails with `AssertionError("KisBroker dry-run unexpectedly invoked the order transport; ...")`.

#### `test_e2e_market_order_intent_is_blocked_before_broker`

Two parts in one function:

1. Build an OrderIntent with `order_type=OrderType.MARKET`. `OrderIntent.__post_init__` already validates positive numeric fields; ensure quantity/price are positive so construction succeeds. Call `oms.place(market_intent)` and assert it raises (RiskEngine rejects MARKET via existing policy, or OMS surfaces the rejection). Confirm `broker.open_orders()` is empty afterward.
2. Confirm the env-time guard still holds: use `monkeypatch.setenv("TRADING_MODE", "paper")`, `monkeypatch.setenv("LIVE_TRADING_ENABLED", "false")`, `monkeypatch.setenv("ALLOW_MARKET_ORDERS", "true")`, and assert `load_settings()` raises `ValueError` containing `"ALLOW_MARKET_ORDERS"` and `"rejected"`.

#### `test_e2e_dashboard_status_reflects_paper_engine_state_after_fill`

```python
def test_e2e_dashboard_status_reflects_paper_engine_state_after_fill():
    with TestClient(create_app()) as client:
        before_account = client.get("/paper/account").json()
        sim = client.post("/paper/order/simulate", json=_order_payload()).json()
        after_account = client.get("/paper/account").json()
        after_positions = client.get("/paper/positions").json()
        after_fills = client.get("/paper/fills").json()
        after_engine = client.get("/paper/engine/status").json()
        after_status = client.get("/paper/status").json()

    assert sim["accepted"] is True
    assert sim["filled"] is True
    assert Decimal(after_account["cash"]["USD"]) < Decimal(before_account["cash"]["USD"])
    assert after_positions["positions"][0]["quantity"] >= 1
    assert after_fills["fills"][0]["symbol"] == "AAPL"
    assert after_engine["account"]["cash"]["USD"] == after_account["cash"]["USD"]
    assert after_status["mode"] == "paper"
    assert after_status["live_enabled"] is False
    assert after_status["safety"]["market_orders_disabled"] is True
    assert after_status["kis_order_methods_fail_closed"] is True
    assert after_status["kis_order_dry_run"] is True
    assert after_status["secret_exposed"] is False
    forbidden_text_tokens = (
        "KIS_APP_KEY",
        "KIS_APP_SECRET",
        "KIS_ACCOUNT_NO",
        "app_secret",
        "access_token",
        "Bearer ",
    )
    combined_text = json.dumps([
        before_account,
        sim,
        after_account,
        after_positions,
        after_fills,
        after_engine,
        after_status,
    ])
    for token in forbidden_text_tokens:
        assert token not in combined_text
```

Note: the actual JSON field name `kis_account_loaded` contains the substring `KIS_ACCOUNT` (uppercase). Check the rendered values, not the JSON keys: build the assertion list from `forbidden_text_tokens` carefully — adjust if a real status field name contains `"KIS_APP_KEY"` etc. (none of the existing `/paper/status` keys contain those tokens, so the check is sound; but the existing `test_paper_e2e_responses_do_not_expose_secrets` uses the same tokens already and passes — mirror that style if in doubt).

#### `test_e2e_strategy_and_agent_packages_do_not_import_broker_modules`

```python
def test_e2e_strategy_and_agent_packages_do_not_import_broker_modules():
    project_root = pathlib.Path(__file__).resolve().parents[1] / "app"
    forbidden = re.compile(r"^\s*(from|import)\s+app\.broker\.(kis|paper)\b", re.MULTILINE)
    for package in ("strategy", "agent"):
        package_dir = project_root / package
        if not package_dir.is_dir():
            continue
        for path in package_dir.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert not forbidden.search(text), f"{path} imports a broker module directly"
```

### 1.4 Optional supplementary functions

Codex may add up to 2 supplementary functions if they materially reinforce the e2e contract without expanding scope:

- `test_e2e_dry_run_controller_idempotent_and_no_broker_calls` — instantiate `DryRunController` via the same wiring used by server.py, run `start()` then `stop()` and assert no broker / no KIS calls. Verify `summary()` returns a dict containing `state`, `counters`, etc.

If neither adds value, omit them.

### 1.5 No conftest changes

Do not edit `tests/conftest.py`. Use `settings` and `make_snapshot` fixtures as-is. Provide any other helpers as module-private functions in the new test file.

## 2. No production code changes

This job is **test-only by default**. Do not edit any file under `app/`. If you discover a real gap (e.g., a helper is missing that prevents a clean end-to-end assertion), STOP:

1. Document the gap in `patch.md` under `## Production change required`.
2. Describe the minimal change needed (1-2 lines, read-only helper only).
3. Explain why no test-side workaround is sufficient.
4. Wait for human approval before applying.

Do not silently expand scope.

## 3. Verification commands

Run from `projects/paper-trading`:

```bash
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

Both must PASS. Also run the safety greps and include their output in `patch.md`:

```bash
grep -rnE "^(from|import) (requests|httpx|aiohttp|urllib3)" app/broker tests
grep -rnE "^\s*(from|import)\s+app\.broker\.(kis|paper)" app/strategy app/agent 2>/dev/null || true
grep -rn "TTTT1002U\|TTTT1006U\|TTTT1004U\|TTTS1002U\|TTTS1001U\|TTTS0307U\|TTTS0308U\|TTTS0309U\|TTTT3014U\|TTTT3016U\|TTTT3017U\|TTTS3013U" app tests
grep -rn "TTTS3018R\|TTTT3039R\|TTTS3014R\|TTTS6036U\|TTTS6037U\|TTTS6038U\|TTTS6058R\|TTTS6059R" app tests
grep -rn "openapi.koreainvestment.com:9443" app tests
grep -rn "ALLOW_MARKET_ORDERS=true\|allow_market_orders=True" app
grep -rn "Bearer eyJ" app tests docs/ai/jobs/paper-e2e-001 || true
```

Expected: all 0 lines except (a) the pre-existing `app/config.py` lines for `kis_base_url_live` default + `ALLOW_MARKET_ORDERS=true` reject message — these are pre-job guard infrastructure and must remain untouched.

## 4. `patch.md` contents

Create `projects/paper-trading/docs/ai/jobs/paper-e2e-001/patch.md` with these sections in order:

1. **Files Changed** — list every modified/created file. Should be exactly two entries: `tests/test_paper_e2e_pipeline.py` and `docs/ai/jobs/paper-e2e-001/patch.md`. If anything under `app/` appears here, also include §1.5 "Production change required" rationale.
2. **Verified end-to-end flow** — describe the full chain that the test file proves: Quote/StrategyInput → Strategy.evaluate → OrderIntent → PaperEngine.submit_intents / PaperRunner.run_once → OMS.place (Strategy → RiskEngine → OMS) → PaperBroker.submit (open order) → PaperEngine.on_quote → PaperBroker.tick → Fill → PaperAccount.apply_fill → PortfolioService.apply_trade/mark_price → PaperJournal.record_trade → /paper/account, /paper/positions, /paper/fills, /paper/engine/status, /paper/status.
3. **Broker boundary preservation** — cite the test functions that prove (a) Strategy does not call broker directly, (b) RiskEngine reject prevents broker.submit, (c) OMS rejects non-paper broker mode, (d) OMS rejects live_trading_enabled=True.
4. **Dry-run no-HTTP evidence** — cite `test_e2e_kis_dry_run_returns_dry_run_ack_without_http`. Explain `_RaiseOnCallOrderTransport` and how its non-invocation proves no HTTP path was taken in the dry-run branch.
5. **Account / Portfolio / Journal update evidence** — cite the cash delta, position delta, and journal entry assertions in `test_e2e_happy_path_strategy_to_fill_through_oms_paper_engine` and `test_e2e_dashboard_status_reflects_paper_engine_state_after_fill`.
6. **Live trading off / market order guard / safety regression** — cite `test_e2e_oms_rejects_live_trading_enabled`, `test_e2e_market_order_intent_is_blocked_before_broker`, and the `/paper/status` assertions in `test_e2e_dashboard_status_reflects_paper_engine_state_after_fill`. Note that `app/config.py::load_settings` still rejects `ALLOW_MARKET_ORDERS=true` (verified by the second half of the market-order test).
7. **Safety grep output** — verbatim output (or "0 lines") for each grep in §3 above. Annotate any pre-existing `app/config.py` lines as pre-job guard infrastructure.
8. **Test Results** —
   ```text
   $ .venv/bin/python -m compileall app tests
   PASS
   $ .venv/bin/python -m pytest -p no:cacheprovider
   <N> passed in <T>s
   ```
   List total test count delta (new function count vs prior baseline).
9. **Remaining TODOs** — note as follow-up jobs: extending KIS dry-run path into a runtime-wired e2e (would require server.py update to choose KisBroker as OMS broker — out of scope), end-to-end with KIS HTTP smoke test in a sandbox account (out of scope; requires live secrets and dedicated test environment), status surface update to advertise `submission_available=True` when `KIS_ORDER_DRY_RUN=false` (out of scope; tracked in api-orders-paper-001 follow-ups).
10. **Claude verification prompt** — paste this exact text:

    > Read `docs/ai/jobs/paper-e2e-001/plan.md` and `docs/ai/jobs/paper-e2e-001/patch.md`. Run `git diff` on the working tree. Verify: (a) only `tests/test_paper_e2e_pipeline.py` and `patch.md` were added; no `app/` file was modified; (b) every required test function from plan §5 is present and asserts the documented behavior; (c) the dry-run KIS test injects `_RaiseOnCallOrderTransport` and assertion-fails if HTTP is attempted; (d) the happy-path test asserts cash↓, position↑, journal entry, and that the resulting trade carries the OMS ack's `oms_id`; (e) the RiskEngine-reject test confirms `broker.open_orders()` remains empty; (f) the OMS non-paper-broker and live-trading-enabled rejections are exercised; (g) `OrderType.MARKET` is blocked before the broker; (h) `ALLOW_MARKET_ORDERS=true` reject in `load_settings` is regressed; (i) `/paper/status` shows `live_enabled=False`, `safety.market_orders_disabled=True`, `kis_order_methods_fail_closed=True`, `kis_order_dry_run=True`, `secret_exposed=False`; (j) Strategy/Agent packages do not import broker modules; (k) no live TR_ID, no paper-unsupported TR_ID, no live base URL, no external HTTP library, no real app key / secret / token / account number anywhere; (l) full pytest passes cleanly. Output verdict `APPROVE`, `REQUEST CHANGES`, or `BLOCK`.

11. **Follow-up Codex prompt rules** (used only if Claude returns REQUEST CHANGES or BLOCK):

    - Quote Claude's specific finding(s) verbatim under `## Findings`.
    - For each finding, write a `## Required change` block stating (a) the exact test edit required, (b) why this fix is in scope of paper-e2e-001 (vs requiring a new job), (c) the safety rule from `prompts/claude.md` that the fix must preserve.
    - Re-state the absolute prohibitions and verification commands.
    - Do not expand scope: this job is test-only. Any fix outside `tests/test_paper_e2e_pipeline.py` or `patch.md` requires human approval before proceeding.
    - End with: "Update `patch.md` (do not create a new one). Append a `## Follow-up <N>` section explaining what changed and re-run verification. Do not commit / push / merge."

12. **Status footer**: `READY FOR REVIEW`.

Stop. Do not commit, push, merge, deploy, or modify `.env`. Hand off to the human, who will run `git diff` and invoke Claude review.
