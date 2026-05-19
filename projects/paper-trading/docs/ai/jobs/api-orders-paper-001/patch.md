## 1. Files Changed

- `app/broker/kis.py`
- `tests/test_kis_paper_order_submission.py`
- `tests/test_kis_order_preflight.py`
- `tests/test_broker_interface.py`
- `docs/ai/jobs/api-orders-paper-001/patch.md`

## 2. Implementation Summary

Implemented the KIS paper overseas stock order submission branch in `KisBroker.place_order()` for `kis_order_dry_run=False`, while preserving the existing dry-run behavior for the default `kis_order_dry_run=True` path.

Official catalog values used:

- Endpoint: `POST /uapi/overseas-stock/v1/trading/order`
- Paper BUY TR ID: `VTTT1002U`
- Paper SELL TR ID: `VTTT1001U`
- Body fields: `CANO`, `ACNT_PRDT_CD`, `OVRS_EXCG_CD`, `PDNO`, `ORD_QTY`, `OVRS_ORD_UNPR`, `ORD_DVSN="00"`, `ORD_SVR_DVSN_CD="0"`, plus `SLL_TYPE="00"` on SELL only.
- Response fields parsed: `rt_cd`, `msg_cd`, `msg1`, `output.ODNO`, with the full sanitized response retained on `KisOrderResponse.raw_response_sanitized`.

Implementation details:

- Added paper order constants, `_select_paper_order_tr_id()`, and `_build_paper_order_body()`.
- Added `KisOrderTransport`, `MockOrderTransport`, and `UrllibOrderTransport`.
- `UrllibOrderTransport` enforces paper host, paper TR ID, paper exchange, and limit-order allowlists before POST.
- `KisBroker.__init__` now selects a mock or urllib order transport based on `kis_api_mode`.
- `place_order()` now runs preflight, preserves dry-run short-circuit behavior, requires an authenticated token for non-dry-run submission, splits the 10-digit KIS account, submits through the order transport, sanitizes the response, rejects missing `rt_cd` as `malformed_response`, rejects non-zero `rt_cd` as `kis_error:<code>`, stores `last_order_response`, and returns `OrderAck(status="submitted")`.
- `capabilities()["submission"]` remains `False`.
- `healthcheck()["order_execution_implemented"]` remains `False`.

## 3. Safety Confirmation

- No live trading was enabled.
- No live endpoint path or live order transport was added.
- No cancel, replace, fills, open-order, or order-status endpoint was implemented.
- `cancel_order`, `replace_order`, `get_open_orders`, `get_fills`, and `get_order_status` remain fail-closed.
- `validate_kis_order_request()`, `_to_kis_request()`, `_dry_run_preview()`, `_idempotency_key_for()`, `_split_kis_account_no()`, `KisAuthClient`, `KisAccountClient`, and `KisMarketDataClient` were not changed.
- `OrderType.MARKET` guards and `ALLOW_MARKET_ORDERS=true` rejection remain intact.
- `OrderType.STOP` was not introduced.
- No external HTTP library was added.
- `app/broker/kis_http.py`, `app/api/*`, `app/static/*`, `app/main.py`, `app/config.py`, `.env`, `.env.example`, and `docs/kis/MISSING_OFFICIAL_VALUES.md` were not changed.
- Strategy and Agent paths do not import `app.broker.kis`.
- Response storage uses `sanitize_kis_response()` before writing `KisOrderResponse.raw_response_sanitized`.
- Added tests for secret/account/token redaction in response storage, reprs, and exception text.

Safety grep output:

```text
$ grep -rnI -E "^(from|import) (requests|httpx|aiohttp|urllib3)" app/broker tests
0 lines

$ grep -rnI "TTTT1002U\|TTTT1006U\|TTTT1004U\|TTTS1002U\|TTTS1001U\|TTTS0307U\|TTTS0308U\|TTTS0309U\|TTTT3014U\|TTTT3016U\|TTTT3017U\|TTTS3013U" app tests
0 lines

$ grep -rnI "TTTS3018R\|TTTT3039R\|TTTS3014R\|TTTS6036U\|TTTS6037U\|TTTS6038U\|TTTS6058R\|TTTS6059R" app tests
0 lines

$ grep -rnI "openapi.koreainvestment.com:9443" app tests
app/config.py:53:    kis_base_url_live: str = "https://openapi.koreainvestment.com:9443"
app/config.py:194:        kis_base_url_live=_str_env("KIS_BASE_URL_LIVE") or "https://openapi.koreainvestment.com:9443",

$ grep -rnI "ALLOW_MARKET_ORDERS=true\|allow_market_orders=True" app
app/config.py:150:            "ALLOW_MARKET_ORDERS=true is rejected in this phase (market orders disabled)"

$ grep -rnI "Bearer eyJ" app tests docs/ai/jobs/api-orders-paper-001 || true
tests/test_missing_market_data_values_doc.py:43:    assert "Bearer eyJ" not in text, "JWT-style bearer token present"
docs/ai/jobs/api-orders-paper-001/plan.md:495:grep -rn "Bearer eyJ\|access_token=eyJ" app tests docs/ai/jobs/api-orders-paper-001
docs/ai/jobs/api-orders-paper-001/codex-task.md:536:grep -rn "Bearer eyJ" app tests docs/ai/jobs/api-orders-paper-001 || true
docs/ai/jobs/api-orders-paper-001/codex-task.md:546:- Real `Bearer eyJ` JWT tokens: 0 (matches in plan/codex-task instruction text are OK).

$ grep -rn "from app.broker.kis" app/strategy 2>/dev/null || true
0 lines

$ grep -rn "from app.broker.kis" app/agent 2>/dev/null || true
0 lines
```

Notes:

- The live base URL and `ALLOW_MARKET_ORDERS=true` lines are pre-existing `app/config.py` guard/config literals.
- The `Bearer eyJ` hits are test/job-instruction literals, not runtime secrets or newly added order code.

## 4. Test Results

```text
$ .venv/bin/python -m compileall app tests
PASS

$ .venv/bin/python -m pytest -p no:cacheprovider tests/test_kis_paper_order_submission.py tests/test_kis_order_preflight.py tests/test_broker_interface.py
63 passed in 0.09s

$ .venv/bin/python -m pytest -p no:cacheprovider
394 passed, 1 failed in 0.72s
```

Full-suite blocker:

```text
FAILED tests/test_kis_http_boundaries.py::test_order_live_http_fails_closed_without_official_endpoint
Expected: NotImplementedError matching "order endpoint"
Actual: KisOrderRejectedError("authentication_required")
```

This failure is a stale expectation for the old `dry_run=False` path. The approved implementation now correctly fails closed at `authentication_required` before any KIS order transport call. I did not modify `tests/test_kis_http_boundaries.py` because it is outside the allowed file changes for this job.

## 5. Remaining TODOs

- BLOCKED: full pytest is not clean until `tests/test_kis_http_boundaries.py::test_order_live_http_fails_closed_without_official_endpoint` is updated or explicitly approved for modification.
- Follow-up job: KIS paper order cancel/modify endpoint support.
- Follow-up job: KIS paper order fills/executions inquiry.
- Follow-up job: status/API surface update for exposing dry-run vs submitted order entry mode.

Claude verification prompt:

```text
Read `docs/ai/jobs/api-orders-paper-001/plan.md` and `docs/ai/jobs/api-orders-paper-001/patch.md`. Run `git diff` on the working tree. Verify: (a) only `app/broker/kis.py`, `tests/test_kis_paper_order_submission.py`, the narrow `tests/test_kis_order_preflight.py` change, and the narrow `tests/test_broker_interface.py` change were modified; (b) only `VTTT1002U` and `VTTT1001U` and the paper `/uapi/overseas-stock/v1/trading/order` POST path were introduced; (c) body fields are exactly `CANO`, `ACNT_PRDT_CD`, `OVRS_EXCG_CD`, `PDNO`, `ORD_QTY`, `OVRS_ORD_UNPR`, `ORD_DVSN="00"`, `ORD_SVR_DVSN_CD="0"`, plus `SLL_TYPE="00"` on SELL only; (d) response parser uses only `rt_cd`/`msg_cd`/`msg1`/`output.ODNO`; (e) `kis_order_dry_run=True` returns `OrderAck(status="dry_run")` with no transport call; (f) `kis_order_dry_run=False` requires authentication, valid 10-digit account, paper host, paper TR_ID, paper exchange, ORD_DVSN="00"; (g) all order failures use `KisOrderRejectedError` with short tags; (h) `KisOrderResponse.raw_response_sanitized` is always passed through `sanitize_kis_response`; (i) cancel/replace/open-orders/fills/order-status stay NotImplementedError; (j) `capabilities()["submission"]` stays `False` and `healthcheck()["order_execution_implemented"]` stays `False`; (k) no live TR_ID, no paper-unsupported TR_ID, no live base URL, no external HTTP library; (l) no app key, app secret, access token, Bearer token, or raw account number appears in code, repr, exceptions, or test capture; (m) `OrderType.MARKET` guard, `OrderType.STOP` absence, `ALLOW_MARKET_ORDERS=true` reject, and kill-switch behavior are unchanged; (n) Strategy / Agent do not import `app.broker.kis`; (o) OMS → RiskEngine → KisBroker chain still routes orders correctly; (p) `app/broker/kis_http.py`, `app/api/*`, `app/static/*`, `app/main.py`, `app/config.py`, `.env`, `.env.example`, and `docs/kis/MISSING_OFFICIAL_VALUES.md` are unchanged; (q) focused tests pass; (r) full pytest is blocked only by stale `tests/test_kis_http_boundaries.py` expectation outside this job's allowed edit set. Output verdict `APPROVE`, `REQUEST CHANGES`, or `BLOCK`.
```

Follow-up Codex prompt rules if Claude returns REQUEST CHANGES or BLOCK:

- Quote Claude's specific findings verbatim under `## Findings`.
- For each finding, include `## Required change` with the exact edit, why it is in scope for `api-orders-paper-001`, and the safety rule that must remain intact.
- Re-state the absolute prohibitions and verification commands.
- Do not expand scope beyond `app/broker/kis.py`, `tests/test_kis_paper_order_submission.py`, `tests/test_kis_order_preflight.py`, `tests/test_broker_interface.py`, `patch.md`, or optional `README.md` unless the human explicitly approves a scope correction.
- End with: `Update patch.md (do not create a new one). Append a ## Follow-up <N> section explaining what changed and re-run verification. Do not commit / push / merge.`

## Follow-up 1

Changed test file:

- `tests/test_kis_http_boundaries.py`

Exact expectation updated:

- `test_order_live_http_fails_closed_without_official_endpoint` now expects `KisOrderRejectedError("authentication_required")` for `kis_order_dry_run=False` without authentication.
- The same test's `broker.last_error` assertion was updated from the old `official_kis_order_endpoint_required` value to `authentication_required`, matching the new fail-closed behavior.

Why the expectation changed:

- `KisBroker.place_order()` no longer reaches the old unimplemented order endpoint branch for unauthenticated `dry_run=False` orders.
- The approved paper-order implementation fails closed earlier at the authentication gate, before account splitting, body construction, or any transport call.

Verification after Follow-up 1:

```text
$ .venv/bin/python -m compileall app tests
PASS

$ .venv/bin/python -m pytest -p no:cacheprovider
395 passed in 0.71s
```

Safety confirmation:

- No production code was changed in this follow-up.
- No KIS endpoint, TR ID, payload, header, or transport logic was changed.
- Live trading remains disabled.
- Market orders remain disabled.
- No `.env`, secrets, auth settings, payment, production infra, migrations, or GUI files were touched.

Verdict: READY FOR REVIEW
