# paper-001 Patch

## Files Changed

- `projects/paper-trading/app/domain/enums.py`
- `projects/paper-trading/app/domain/orders.py`
- `projects/paper-trading/app/domain/quote.py`
- `projects/paper-trading/app/domain/fills.py`
- `projects/paper-trading/app/portfolio/service.py`
- `projects/paper-trading/app/portfolio/account.py`
- `projects/paper-trading/app/broker/paper.py`
- `projects/paper-trading/app/risk/engine.py`
- `projects/paper-trading/app/runtime/paper_journal.py`
- `projects/paper-trading/app/runtime/paper_engine.py`
- `projects/paper-trading/app/config.py`
- `projects/paper-trading/.env.example`
- `projects/paper-trading/README.md`
- `projects/paper-trading/tests/test_models.py`
- `projects/paper-trading/tests/test_paper_broker.py`
- `projects/paper-trading/tests/test_risk_engine.py`
- `projects/paper-trading/tests/test_portfolio_service.py`
- `projects/paper-trading/tests/test_kis_order_preflight.py`
- `projects/paper-trading/tests/test_strategy_premarket_gap.py`
- `projects/paper-trading/tests/test_paper_account.py`
- `projects/paper-trading/tests/test_paper_engine.py`
- `projects/paper-trading/tests/test_paper_fills.py`
- `projects/paper-trading/tests/test_paper_journal.py`
- `projects/paper-trading/tests/test_paper_001_simulation_matrix.py`

## Implementation Summary

- Review v2 Finding #1: Restored mandatory `OrderIntent.limit_price`, required `limit_price > 0` for MARKET too, inverted the market intent model test, updated market risk helper to pass an explicit limit price, and added MARKET max-notional rejection coverage.
- Review v2 Finding #2: `PaperBroker.tick()` now treats `quote.session is None` as backward-compatible legacy quote input and allows it through session filtering; added a regression test.
- Review v2 Finding #3: Kept `PaperAccount` separated from `PortfolioService` and added a docstring explaining that account owns cash settlement only while portfolio owns positions/PnL.
- Phase 1: Added `OrderType.MARKET`, order currency fields, quote `session`/`currency`, and the new `Fill` domain model.
- Phase 2: Extended `PortfolioService` for per-currency realized PnL, market value, and unrealized PnL while preserving legacy aggregate Decimal fields.
- Phase 3: Added `PaperAccount` with currency-separated cash buckets and insufficient-cash rejection.
- Phase 4: Added `PaperBroker.tick()` and `cancel_all()`, quote staleness/session checks, LIMIT/STOP_LIMIT/MARKET simulation, volume-capped partial fills, residual open quantity, and per-fill commission calculation.
- Phase 5: Added `RiskEngine` paper MARKET branch with the required triple guard.
- Phase 6: Added `PaperJournal` and `PaperEngine` for safe fill application, trade logging, rejected-order logging, and portfolio/account updates.
- Phase 7: Added paper simulation settings, `.env.example` comment-only variable descriptions, and README documentation.
- Phase 8: Added and updated tests for models, broker fills, partial fills, stale/session handling, account cash, journal, engine, portfolio multi-currency reporting, config/risk guard behavior, and existing boundary expectations.

## Safety Confirmation

- ✓ `ALLOW_MARKET_ORDERS=true` startup rejection remains unchanged.
- ✓ `ALLOW_PAPER_MARKET_ORDERS` is separate and defaults to false.
- ✓ MARKET approval requires `ALLOW_PAPER_MARKET_ORDERS=true`, `TradingMode.PAPER`, and `live_trading_enabled=False`.
- ✓ No live trading enablement was added.
- ✓ No real order placement was added.
- ✓ No RiskEngine or OMS bypass was added.
- ✓ Strategy still emits LIMIT order intents and does not call a broker directly.
- ✓ LLM/agent broker access was not added.
- ✓ No external HTTP library import was added.
- ✓ No exchange-rate conversion or base-currency conversion helper was added.
- ✓ `.env` was not read, modified, copied, or printed.
- ✓ No real app key, app secret, access token, refresh token, or account number was added.
- ✓ Forbidden GUI, dry-run runtime, KIS, Alpaca, broker base, strategy body, and OMS manager files were not modified.

## Test Results

- `cd /root/ai-dev-center/projects/ai-team/projects/paper-trading`
- `.venv/bin/python -m compileall app tests` passed.
- `.venv/bin/python -m pytest -p no:cacheprovider` passed: `303 passed in 0.48s`.
- Baseline was 242 tests; this patch results in 303 total tests.

## Remaining TODOs

- `paper-001-gui`: expose the new paper account/portfolio details in GUI/API later without touching this job's forbidden GUI files.
- Add longer multi-tick partial-fill scenarios with persistent order lifecycle assertions.
- Add richer paper journal persistence tests for file output rotation/retention if a future job defines retention rules.
- Add portfolio short-position scenarios if paper trading later supports shorting policy explicitly.

## Phase별 적용 요약

- Phase 1: enum/orders/quote/fills 확장.
- Phase 2: portfolio service 시그니처와 snapshot 통화별 필드 확장.
- Phase 3: `PaperAccount`와 `PaperAccountError` 추가.
- Phase 4: `PaperBroker.tick()` / `cancel_all()` 추가.
- Phase 5: `RiskEngine` MARKET 분기 추가.
- Phase 6: `PaperJournal` / `PaperEngine` 추가.
- Phase 7: config / env example / README 업데이트.
- Phase 8: 신규 및 기존 테스트 업데이트.

## 신규 도메인/클래스/메서드 명단

- `OrderType.MARKET`
- `Fill`
- `PaperAccount`
- `PaperAccountError`
- `PaperJournal`
- `OrderLogEntry`
- `TradeLogEntry`
- `PaperEngine`
- `PaperBroker.tick`
- `PaperBroker.cancel_all`
- `PortfolioSnapshot.realized_pnl_by_currency`
- `PortfolioSnapshot.market_value_by_currency`
- `PortfolioSnapshot.unrealized_pnl_by_currency`

## 안전 grep 결과

```text
fx-grep: clean
http-lib-grep: clean
secret-grep: clean
gui-grep: clean
dry-run-grep: clean
kis-grep: clean
```

## Commit / Push / Merge / Deploy

- `git commit` not run.
- `git push` not run.
- `git merge` not run.
- Deploy not run.

READY FOR REVIEW v2
