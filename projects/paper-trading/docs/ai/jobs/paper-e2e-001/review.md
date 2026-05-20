# paper-e2e-001 — Claude Review

## Verdict

APPROVE

## Summary

paper-e2e-001 adds 9 regression tests in `tests/test_paper_e2e_pipeline.py` that lock in the existing `Quote → Strategy → RiskEngine → OMS → PaperBroker/KisBroker dry-run → PaperEngine → Fill → PaperAccount/Portfolio/Journal → status surface` chain. Zero production changes. Full pytest is clean (404 passed, +9 vs the 395 baseline from api-orders-paper-001).

## Scope of changes

In-scope, intentional:

- `projects/paper-trading/tests/test_paper_e2e_pipeline.py` — new file, 9 test functions matching plan §5 names verbatim.
- `projects/paper-trading/docs/ai/jobs/paper-e2e-001/patch.md` — patch record.

Out-of-scope, pre-existing dirty (NOT from this job — conversation-start residue):

- `projects/paper-trading/app/api/server.py`
- `projects/paper-trading/scripts/_common.sh`
- `projects/paper-trading/scripts/start_server.sh`
- `docs/ai/jobs/mvp-002/request.ko.md`

Verified unchanged: `app/broker/*`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/agent*` (none exists), `app/config.py`, `app/api/*` (server.py is pre-job dirt), `app/static/*`, `app/main.py`, `app/domain/*`, `tests/conftest.py`, every prior test file, `docs/kis/MISSING_OFFICIAL_VALUES.md`, `.env`, `.env.example`. Codex correctly honored "test-only by default" — no production change required and none made.

## Test function inventory

| Plan §5 name | File line | Status |
| --- | --- | --- |
| `test_e2e_happy_path_strategy_to_fill_through_oms_paper_engine` | :143 | OK |
| `test_e2e_strategy_blocker_does_not_reach_oms_or_broker` | :189 | OK |
| `test_e2e_risk_engine_reject_does_not_reach_broker` | :205 | OK |
| `test_e2e_oms_rejects_non_paper_broker_mode` | :221 | OK |
| `test_e2e_oms_rejects_live_trading_enabled` | :230 | OK |
| `test_e2e_kis_dry_run_returns_dry_run_ack_without_http` | :237 | OK |
| `test_e2e_market_order_intent_is_blocked_before_broker` | :259 | OK |
| `test_e2e_dashboard_status_reflects_paper_engine_state_after_fill` | :274 | OK |
| `test_e2e_strategy_and_agent_packages_do_not_import_broker_modules` | :326 | OK |

All 9 required tests present; no supplementary functions added (optional).

## Pipeline-leg verification (Codex's claims vs. test source)

- **Happy path** (`:143-186`): runner.run_once → result.strategy.passed True / oms_ack present / `broker.open_orders()[0]` carries `risk_token`. Then `paper_engine.on_quote(matching quote)` produces `trades` with `trades[0].oms_id == results[0].oms_ack.oms_id` — proves the same logical order flowed through Strategy → RiskEngine (token attached) → OMS (oms_id assigned) → PaperBroker (open order) → PaperEngine.on_quote (fill) → PaperJournal (entry) end-to-end. Cash↓, position↑, journal entry all asserted.

- **Strategy blocker** (`:189-202`): wraps `oms.place` with `Mock(wraps=oms.place)` so call count can be measured. With `premarket_volume=10`, `oms.place.call_count == 0`, `broker.open_orders() == []`, `paper_engine.on_quote(...) == []`, cash unchanged. Confirms strategy.blockers gate stops the chain before any broker contact.

- **RiskEngine reject** (`:205-218`): `symbol_allowlist=("MSFT",)` makes AAPL fail. Two entry points (`runner.run_once` and `paper_engine.submit_intents`) both produce empty `broker.open_orders()`; `rejected_by == "risk_engine"`.

- **OMS non-paper broker** (`:221-227`): stub broker with `mode = TradingMode.LIVE` causes `OMS.place` to raise `RuntimeError("OMS rejects non-paper broker")`.

- **OMS live trading reject** (`:230-234`): `live_trading_enabled=True` causes `OMS.place` to raise `RuntimeError("OMS refuses live trading...")`.

- **KIS dry-run no-HTTP** (`:237-256`): `KisBroker._order_transport` is replaced with `_RaiseOnCallOrderTransport`. Its `submit_order` raises `AssertionError("KisBroker dry-run unexpectedly invoked the order transport; ...")` if invoked. Because `KIS_ORDER_DRY_RUN=true`, `place_order` short-circuits to `OrderAck(status="dry_run")` before reaching the transport — test passes without the AssertionError ever firing. Additional asserts: `last_order_preview is not None`, `last_order_response is None`, `healthcheck()["order_dry_run"] is True`, `order_execution_implemented is False`, `order_methods_fail_closed is True`.

- **Market order blocked before broker** (`:259-271`): `OrderIntent(order_type=OrderType.MARKET, ...)` → `oms.place` raises `RuntimeError("RiskEngine rejected ...")`; `broker.open_orders() == []`. Second half: `monkeypatch.setenv("ALLOW_MARKET_ORDERS", "true")` → `load_settings()` raises `ValueError("ALLOW_MARKET_ORDERS=true is rejected ...")`. Both layers regressed.

- **Dashboard / status surface** (`:274-323`): `TestClient(create_app())` → POST `/paper/order/simulate` → cash↓, position quantity ≥ 1, fill recorded, engine status mirrors account/portfolio/journal, `/paper/status` flags `mode="paper"` / `live_enabled=False` / `safety.market_orders_disabled=True` / `kis_order_methods_fail_closed=True` / `kis_order_dry_run=True` / `secret_exposed=False`. `combined_text` over all response JSONs contains no `KIS_APP_KEY` / `KIS_APP_SECRET` / `KIS_ACCOUNT_NO` / `app_secret` / `access_token` / `Bearer ` literal.

- **Strategy/Agent isolation** (`:326-335`): regex `^\s*(from|import)\s+app\.broker\.(kis|paper)\b` scanned over `app/strategy/*.py` (and `app/agent/*.py` if present). Tests fail loudly if Strategy or Agent ever imports a broker module.

## Safety regression

- live trading off — `test_e2e_oms_rejects_live_trading_enabled` + every `/paper/status` assertion.
- market orders blocked — `test_e2e_market_order_intent_is_blocked_before_broker` (two layers) + `safety.market_orders_disabled is True` on `/paper/status`.
- `OrderType.STOP` not introduced — domain enums untouched.
- OMS / RiskEngine boundary intact — non-paper broker, live trading, risk reject, strategy blocker all regressed individually.
- KIS dry-run no-HTTP — `_RaiseOnCallOrderTransport` injection guarantees any HTTP attempt would fail the test loudly.
- No KIS endpoint / TR_ID / header / payload invented — no transport class added; no new constants.
- No external HTTP library — verified by safety grep (0 lines in `app/broker tests`).
- No secret / account / token / Bearer literal — explicit `forbidden_text_tokens` regression + only `fake-key-XYZ` / `fake-secret-XYZ` / `12345678-01` / `fake-access-token` fixtures.
- `.env` / `.env.example` / `app/config.py` / `docs/kis/MISSING_OFFICIAL_VALUES.md` untouched.
- Strategy / Agent KIS-import regression test added on top of existing one.

Safety grep output (from patch.md, re-checked):
- External HTTP imports: 0 lines.
- Strategy/Agent broker imports: 0 lines.
- Live / paper-unsupported TR_IDs: 0 lines.
- Live base URL: only pre-existing `app/config.py:53` and `:194` (default + load_settings line) — pre-job guard infrastructure, correctly untouched.
- `ALLOW_MARKET_ORDERS=true` literal: only pre-existing `app/config.py:150` reject message — correctly untouched.
- `Bearer eyJ`: only existing `tests/test_missing_market_data_values_doc.py` regression literal + plan/codex-task instruction text. No runtime secret.

## Test verification (재실행 결과)

```text
$ .venv/bin/python -m pytest -p no:cacheprovider --tb=no -q tests/test_paper_e2e_pipeline.py
9 passed in 0.19s

$ .venv/bin/python -m pytest -p no:cacheprovider --tb=no -q
404 passed in 0.71s
```

+9 new tests, 0 regressions on the prior 395-test baseline. `compileall app tests` PASS per patch.md.

## Final Checklist

| 항목 | 결과 |
| --- | --- |
| 9 required test functions present (plan §5) | OK |
| Happy path proves cash↓ + position↑ + journal entry + oms_id chained | OK |
| Strategy blocker keeps `broker.open_orders()` empty and `oms.place` uncalled | OK |
| RiskEngine reject keeps `broker.open_orders()` empty | OK |
| OMS rejects non-paper broker and live_trading_enabled | OK |
| KIS dry-run returns "dry_run" ack with `_RaiseOnCallOrderTransport` guard | OK |
| `OrderType.MARKET` blocked before broker; `ALLOW_MARKET_ORDERS=true` rejected by `load_settings` | OK |
| `/paper/status` reflects safety flags + no secret leak | OK |
| Strategy / Agent do not import broker modules | OK |
| `app/` untouched (test-only) | OK |
| pytest 404 passed | OK |
| commit / push / merge / deploy 수행 안 됨 | 수행 안 됨 |

## Follow-up Codex prompt

없음. APPROVE.

다음 단계는 사람이 직접 `git diff` 와 `git status` 로 변경 범위를 확인 (`tests/test_paper_e2e_pipeline.py` 신규 + `docs/ai/jobs/paper-e2e-001/` 신규만 본 job 변경분) 한 뒤 `git add` → `git commit` 을 수동 실행하는 것이다. 본 review 는 commit / push / merge / deploy 를 수행하지 않는다.
