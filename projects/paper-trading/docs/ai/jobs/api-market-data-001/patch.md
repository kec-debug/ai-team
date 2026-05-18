# api-market-data-001 Patch

## Files Changed

- `README.md`
- `app/domain/quote.py`
- `app/broker/kis.py`
- `app/broker/kis_quote_mapper.py`
- `tests/test_broker_interface.py`
- `tests/test_kis_http_boundaries.py`
- `tests/test_kis_market_data_client.py`
- `tests/test_kis_quote_mapper.py`
- `tests/test_quote_model.py`

Pre-existing unrelated dirty files were left untouched.

## Implementation Summary

- Added `Quote.bid_ask_present` so synthetic bid/ask values can be distinguished from broker-supplied quotes.
- Implemented KIS overseas current-price response mapping for confirmed fields only: `rt_cd`, `output.last`, and `output.tvol`.
- Added a conservative KIS market data transport boundary:
  - default mock mode returns `mock_mode_no_network` without network access
  - paper mode only allows the confirmed paper host, current-price path, and current-price TR ID
  - unsupported exchanges and non-paper hosts fail closed before any network call
- Updated `KisMarketDataClient.get_quote()` to return a domain `Quote`.
- Updated `get_last_price()` to return the mapped `Decimal` last price.
- Preserved KIS order, account, OMS, RiskEngine, strategy, runtime, and GUI boundaries.

## Safety Confirmation

- No live trading was enabled.
- No order endpoint, order TR ID, order payload, or order URL was added.
- No market order behavior was changed.
- No `.env` file was read, edited, or added.
- No API credential, token, or account value was copied into code, docs, logs, or tests.
- No third-party HTTP client library was imported.
- Network remains disabled by default through `KIS_API_MODE=mock`.
- Real KIS market data HTTP is limited to confirmed paper current-price values and still requires explicit paper API mode plus authentication.

## Test Results

From `/root/ai-dev-center/projects/ai-team/projects/paper-trading`:

```text
.venv/bin/python -m compileall app tests
Result: passed
```

```text
.venv/bin/python -m pytest -p no:cacheprovider
Result: 337 passed in 0.69s
```

Safety grep:

```text
safety-grep: clean
```

Job-scoped diff stat:

```text
9 files changed, 482 insertions(+), 80 deletions(-)
```

## Remaining TODOs

- Add bid/ask and exchange timestamp mapping only if official KIS response fields are confirmed.
- Add additional exchange-specific symbol handling only from official KIS documentation.
- Keep KIS order HTTP implementation out of scope until a separate approved job confirms order endpoint values.

READY FOR REVIEW
