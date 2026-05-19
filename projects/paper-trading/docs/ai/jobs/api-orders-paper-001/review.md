# api-orders-paper-001 — Claude Review (final)

## Verdict

APPROVE

## Summary

api-orders-paper-001 implements the `KisBroker.place_order()` non-dry-run branch strictly against the `Confirmed: yes` paper-supported rows in `docs/kis/MISSING_OFFICIAL_VALUES.md` §4 (`VTTT1002U` US BUY + `VTTT1001U` US SELL, POST `/uapi/overseas-stock/v1/trading/order`). Dry-run behavior, every safety guard, and every `NotImplementedError` for out-of-scope endpoints are preserved. Follow-up 1 surgically updated a single stale test expectation in `tests/test_kis_http_boundaries.py`. Full pytest is clean (395 passed, 0 failed).

## Scope of changes (this job + Follow-up 1)

In-scope, intentional:

- `projects/paper-trading/app/broker/kis.py` — paper-order constants (`KIS_OVERSEAS_ORDER_PATH`, `KIS_PAPER_ORDER_TR_ID_US_BUY="VTTT1002U"`, `KIS_PAPER_ORDER_TR_ID_US_SELL="VTTT1001U"`, `KIS_PAPER_ORDER_TR_IDS`, `KIS_PAPER_ORDER_HOSTS`, `KIS_PAPER_ORDER_EXCHANGES`, `KIS_PAPER_ORDER_LIMIT_DVSN="00"`, `KIS_PAPER_ORDER_ORD_SVR_DVSN_CD="0"`, `KIS_PAPER_ORDER_SELL_TYPE="00"`), helpers (`_select_paper_order_tr_id`, `_build_paper_order_body`), transports (`KisOrderTransport` Protocol, `MockOrderTransport`, `UrllibOrderTransport`), `KisBroker.__init__` order-transport selection, `place_order` non-dry-run branch, `_last_order_response` state + `last_order_response` property.
- `projects/paper-trading/tests/test_kis_paper_order_submission.py` — 29 new tests (all of plan §5 enumerated names present).
- `projects/paper-trading/tests/test_kis_order_preflight.py` — `test_place_order_valid_input_with_dry_run_disabled_requires_auth` (1 function renamed + 1 assertion swapped to `KisOrderRejectedError("authentication_required")`).
- `projects/paper-trading/tests/test_broker_interface.py` — `test_kis_place_cancel_replace_not_implemented` (1 assertion line swapped: `broker_no_dry_run.place_order(...)` now expects `KisOrderRejectedError("authentication_required")`; cancel/replace `NotImplementedError` checks intact).
- `projects/paper-trading/tests/test_kis_http_boundaries.py` — **Follow-up 1**: `test_order_live_http_fails_closed_without_official_endpoint` (1 function, 2 assertion lines: `pytest.raises(NotImplementedError, match="order endpoint")` → `pytest.raises(KisOrderRejectedError, match="authentication_required")`; `broker.last_error == "official_kis_order_endpoint_required"` → `broker.last_error == "authentication_required"`). The earlier `test_account_parsers_return_internal_models_and_sanitize` change in this same file is from api-account-001 (already reviewed and approved).
- `projects/paper-trading/docs/ai/jobs/api-orders-paper-001/patch.md` — this job's record + Follow-up 1.

Out-of-scope, pre-existing dirty (NOT from this job — present in initial git status):

- `projects/paper-trading/app/api/server.py`
- `projects/paper-trading/scripts/_common.sh`
- `projects/paper-trading/scripts/start_server.sh`
- `docs/ai/jobs/mvp-002/request.ko.md`

Verified unchanged: `app/broker/kis_http.py` (OAuth allowlist intact), `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/base.py`, `app/broker/kis_token_cache.py`, `app/broker/kis_quote_mapper.py`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/api/*` (server.py outside this job), `app/static/*`, `app/main.py`, `app/config.py`, `app/domain/*`, `docs/kis/MISSING_OFFICIAL_VALUES.md`, `.env`, `.env.example`.

## Review-focus 항목별 결론

1. **Only confirmed KIS paper order endpoint/TR IDs were used.** OK. `KIS_OVERSEAS_ORDER_PATH = "/uapi/overseas-stock/v1/trading/order"` and the two paper TR_IDs are the only catalog identifiers introduced. Response parsing uses only `rt_cd` / `msg_cd` / `msg1` / `output.ODNO` (with `KRX_FWDG_ORD_ORGNO` + `ORD_TMD` preserved in `raw_response_sanitized` but not consumed) — all catalog §4.5 `Confirmed: yes` fields.

2. **Only POST `/uapi/overseas-stock/v1/trading/order` is allowed.** OK. `UrllibOrderTransport` hardcodes this path; no other path appears in code or tests. POST method only (`Request(..., method="POST")`).

3. **Only paper TR IDs `VTTT1002U` and `VTTT1001U` are allowed.** OK. `KIS_PAPER_ORDER_TR_IDS = frozenset({KIS_PAPER_ORDER_TR_ID_US_BUY, KIS_PAPER_ORDER_TR_ID_US_SELL})` enforces the 2-element allowlist; `_select_paper_order_tr_id(side)` maps BUY → `VTTT1002U`, SELL → `VTTT1001U`; transport rejects any other `tr_id` with `KisOrderRejectedError("disallowed_tr_id")`.

4. **No live order endpoint/TR ID was added.** OK. Verified via `grep -rn "TTTT1002U\|TTTT1006U\|TTTT1004U\|TTTS1002U\|TTTS1001U\|TTTS0307U\|TTTS0308U\|TTTS0309U\|TTTT3014U\|TTTT3016U\|TTTT3017U\|TTTS3013U" app tests` → 0 lines. Forbidden literals in tests 21/22/28/29 are constructed via string concatenation so grep stays clean while runtime behavior is preserved. `test_kis_module_does_not_introduce_live_tr_ids` re-enforces this as a regression.

5. **Dry-run true still sends no HTTP.** OK. `place_order` early-returns at line 1154-1161 (`OrderAck(status="dry_run")` + `_dry_run_preview`) before any auth check, account split, body build, or transport call. `test_place_order_dry_run_path_unchanged` asserts no token required, `last_order_preview` populated, `last_order_response` still `None`.

6. **Dry-run false requires authentication and paper/live/market guards.** OK. Execution order (`place_order` lines 1151-1197):
   1. `validate_kis_order_request` (paper / no-live / no-allow_market_orders / kis_env=paper / no-kill-switch / LIMIT or STOP_LIMIT / qty>0 / price>0 / fresh quote).
   2. `_to_kis_request` (existing helper, masked account).
   3. dry-run short-circuit (skipped since False).
   4. `_auth.is_authenticated()` + `_auth.get_access_token()` → fail-closed `KisOrderRejectedError("authentication_required")` if missing.
   5. `_split_kis_account_no` 10-digit format → `KisOrderRejectedError("invalid_kis_account_no_format")` if invalid.
   6. `_select_paper_order_tr_id` + `_build_paper_order_body` (exchange="NASD").
   7. `_order_transport.submit_order` (host / TR_ID / exchange / ORD_DVSN allowlists).
   Each gate has a dedicated test (`test_place_order_dry_run_disabled_*`).

7. **Market orders remain blocked.** OK. `validate_kis_order_request` rejects `OrderType.MARKET` with `KisOrderRejectedError("order_type_not_limit")` (unchanged); it also rejects `settings.allow_market_orders=True` with `KisOrderRejectedError("market_orders_allowed_flag_set")` (unchanged). `_build_paper_order_body` hardcodes `ORD_DVSN="00"`; the transport then double-checks `body["ORD_DVSN"] == "00"` and rejects otherwise with `KisOrderRejectedError("ord_dvsn_not_limit")`. `app/config.py::load_settings` still rejects `ALLOW_MARKET_ORDERS=true` at load time (untouched). Three guards in series → unchanged.

8. **LIMIT only remains enforced with `ORD_DVSN="00"`.** OK. `KIS_PAPER_ORDER_LIMIT_DVSN = "00"` is the only value written by `_build_paper_order_body`; `UrllibOrderTransport.submit_order` enforces `body.get("ORD_DVSN") != KIS_PAPER_ORDER_LIMIT_DVSN` → `ord_dvsn_not_limit`. `test_urllib_order_transport_rejects_invalid_ord_dvsn` covers this.

9. **BUY omits `SLL_TYPE` and SELL uses `SLL_TYPE="00"`.** OK. `_build_paper_order_body` only adds `body["SLL_TYPE"] = KIS_PAPER_ORDER_SELL_TYPE` when `request.side is Side.SELL`. Verified by `test_build_paper_order_body_buy_omits_sll_type`, `test_build_paper_order_body_sell_sets_sll_type_zero_zero`, `test_build_paper_order_body_contains_only_catalog_keys`, `test_place_order_happy_path_sell` (asserts transport.calls body contains `SLL_TYPE="00"`), and `test_place_order_happy_path_buy`.

10. **Cancel/replace/open_orders/fills/order_status remain out of scope or fail-closed.** OK. `KisBroker.cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` bodies all still raise `NotImplementedError` (kis.py lines 1144-1148, 1236-1259, and onward). `_validate_paper_settings` + `allow_market_orders` + `kill_switch_engaged` guards inside `cancel_order` unchanged. `capabilities()` returns `{"submission": False, "cancel": False, "replace": False, "open_orders": False, "fills": False, "order_status": False}` — preserved (intentional per plan §4.7 to keep `app/api/routes.py` and `test_api_paper_status` regressions green).

11. **No app key, app secret, account number, token, or Bearer token is exposed.** OK.
    - `KisOrderResponse.raw_response_sanitized` always populated via `sanitize_kis_response(raw, settings)` (kis.py line 1199) — the sanitizer redacts every sensitive key (`appkey` / `appsecret` / `access_token` / `account_no` / `cano` / `authorization` / `tr_key` / `secret`) and every settings-derived sensitive value.
    - Transport never includes `access_token` / `app_key` / `app_secret` / `Bearer …` in exception messages. Only short tags (`mock_mode_no_network`, `authentication_required`, `invalid_kis_account_no_format`, `disallowed_host`, `disallowed_tr_id`, `invalid_exchange`, `ord_dvsn_not_limit`, `http_<code>`, `transport_error`, `invalid_response_body`, `kis_error:<msg_cd>`, `malformed_response`).
    - `test_place_order_response_sanitization_redacts_secrets` enforces sanitization of echoed credentials.
    - `test_place_order_exceptions_and_repr_do_not_expose_secrets` enforces that `repr(broker)`, `repr(broker.last_order_response)`, and every raised exception message are free of `fake-key-XYZ` / `fake-secret-XYZ` / `12345678` / `fake-access-token` / `Bearer fake-access-token`.

12. **`.env` was not touched.** OK. `.env` / `.env.example` not in `git diff`. `app/config.py` untouched (no new env variables, transport timeouts reuse `kis_oauth_timeout_seconds` / `kis_oauth_max_retries` per plan).

13. **Strategy/Agent/LLM do not call KIS directly.** OK. `grep -rn "from app.broker.kis" app/strategy app/agent` → 0 lines. `test_strategy_package_does_not_import_kis` (existing) still passes. No new Strategy/Agent paths to KIS introduced.

14. **OMS/RiskEngine boundary remains intact.** OK. `app/oms/manager.py` and `app/risk/engine.py` unchanged. The order flow remains Strategy → RiskEngine.evaluate → OMS.place → broker.submit → KisBroker.place_order. `test_place_order_via_oms_passes_riskengine` runs the full chain end-to-end: an `OrderIntent` passes through `RiskEngine` + `OMS.place`, OMS constructs the `BrokerOrder` with a `risk_token`, and `KisBroker.place_order` (with a FakeOrderTransport) reaches the catalog `submit_order` call — confirming no Strategy/Agent bypass and that OMS is still the only producer of executable `BrokerOrder`.

15. **Follow-up 1 changed only the stale test expectation.** OK. `git diff` against pre-Follow-up state on `tests/test_kis_http_boundaries.py` shows the change is exclusively inside `test_order_live_http_fails_closed_without_official_endpoint`:
    - `pytest.raises(NotImplementedError, match="order endpoint")` → `pytest.raises(KisOrderRejectedError, match="authentication_required")`.
    - `broker.last_error == "official_kis_order_endpoint_required"` → `broker.last_error == "authentication_required"`.
    Reason recorded: the `dry_run=False + no token` path now correctly fails closed at the authentication gate before any unimplemented branch. No production code was touched in Follow-up 1; no other function in the file was modified. The earlier `test_account_parsers_return_internal_models_and_sanitize` change in the same file is from api-account-001 (already approved separately).

16. **Tests passed: 395 passed.** OK. Re-verified:
    ```text
    $ .venv/bin/python -m pytest -p no:cacheprovider --tb=no -q
    395 passed in 0.70s
    ```
    `compileall app tests` PASS as well.

17. **Scope stayed within api-orders-paper-001.** OK. In-scope diff set is exactly `app/broker/kis.py` + new `tests/test_kis_paper_order_submission.py` + narrow `tests/test_kis_order_preflight.py` (1 fn) + narrow `tests/test_broker_interface.py` (1 assertion in 1 fn) + Follow-up 1's narrow `tests/test_kis_http_boundaries.py` (1 fn) + `docs/ai/jobs/api-orders-paper-001/patch.md`. Pre-existing dirty files (`app/api/server.py`, `scripts/*`, `docs/ai/jobs/mvp-002/request.ko.md`) are conversation-start residue from unrelated work, not introduced by this job. README.md was not modified — the optional 1-2 line note was skipped, which is allowed by the plan.

## Test verification (재실행 결과)

```text
$ .venv/bin/python -m pytest -p no:cacheprovider --tb=no -q
395 passed in 0.70s
```

29 new tests in `tests/test_kis_paper_order_submission.py` cover: TR_ID mapping (BUY/SELL), body composition (only catalog keys, BUY omits SLL_TYPE, SELL sets `SLL_TYPE="00"`, quantity/price as strings), dry-run preservation, every fail-closed gate (auth / preflight / live / market type / `allow_market_orders` / kill-switch / mock-mode), happy paths (BUY + SELL with correct TR_ID), KIS rejection (`rt_cd != "0"` → `kis_error:<msg_cd>`), strict malformed response (missing `rt_cd` → `malformed_response`), HTTP 404, transport error, transport allowlist enforcement (live host built via concatenation, live TR_ID built via concatenation, bad exchange, bad ORD_DVSN), response sanitization (echoed credentials redacted), repr/exception secret-leak protection, end-to-end OMS → RiskEngine → KisBroker chain, and a static guard that scans `app/broker/kis.py` text for any live or paper-unsupported TR_ID literal (constructed in-test by concatenation so the guard itself stays grep-clean).

Narrow regression updates (3 functions across 3 files) all align with the new fail-closed behavior at the authentication gate.

## Safety grep (재실행 결과)

```text
$ grep -rnE "^(from|import) (requests|httpx|aiohttp|urllib3)" app/broker tests
0 lines

$ grep -rn "TTTT1002U\|TTTT1006U\|TTTT1004U\|TTTS1002U\|TTTS1001U\|TTTS0307U\|TTTS0308U\|TTTS0309U\|TTTT3014U\|TTTT3016U\|TTTT3017U\|TTTS3013U" app tests
0 lines

$ grep -rn "TTTS3018R\|TTTT3039R\|TTTS3014R\|TTTS6036U\|TTTS6037U\|TTTS6038U\|TTTS6058R\|TTTS6059R" app tests
0 lines

$ grep -rn "from app.broker.kis" app/strategy app/agent 2>/dev/null
0 lines
```

The pre-existing `app/config.py` literals (`https://openapi.koreainvestment.com:9443` default and `ALLOW_MARKET_ORDERS=true is rejected ...` reject message) noted by Codex in patch.md §3 are pre-job guard infrastructure and are correctly left untouched.

## Remaining TODOs (out of scope; follow-up jobs)

- `api-orders-paper-cancel-001`: paper modify/cancel endpoint (POST `/order-rvsecncl`, paper TR_ID `VTTT1004U`). Will require its own preflight + allowlist + body builder.
- `api-orders-paper-fills-001`: paper executions inquiry (`VTTS3035R` GET `/inquire-ccnl`) with the paper-only constraints in catalog §4.7.
- Status surface job (separate from api-* family) to update `app/api/routes.py` and `capabilities()` so `kis_order_submission_available` / `kis_order_entry_mode` can advertise dry-run vs submitted state. The current conservative `submission=False` and `kis_order_entry_mode="not_implemented"` are intentional under this job's "GUI 파일 수정 금지" constraint and not a defect.

## Final Checklist

| 항목 | 결과 |
| --- | --- |
| 1. confirmed paper endpoint/TR IDs only | OK |
| 2. only POST `/uapi/overseas-stock/v1/trading/order` | OK |
| 3. only `VTTT1002U` / `VTTT1001U` | OK |
| 4. no live order endpoint/TR ID | OK |
| 5. dry-run true sends no HTTP | OK |
| 6. dry-run false requires auth + paper/live/market guards | OK |
| 7. market orders blocked | OK |
| 8. LIMIT only with `ORD_DVSN="00"` | OK |
| 9. BUY omits SLL_TYPE; SELL uses `SLL_TYPE="00"` | OK |
| 10. cancel/replace/open_orders/fills/order_status fail-closed | OK |
| 11. no secret / account / token / Bearer leak | OK |
| 12. `.env` untouched | OK |
| 13. Strategy/Agent/LLM do not call KIS directly | OK |
| 14. OMS/RiskEngine boundary intact | OK |
| 15. Follow-up 1 changed only the stale test expectation | OK |
| 16. pytest 395 passed | OK |
| 17. scope inside api-orders-paper-001 | OK |
| commit / push / merge / deploy 수행 안 됨 | 수행 안 됨 |

## Follow-up Codex prompt

없음. APPROVE.

다음 단계는 사람이 직접 `git diff` 로 변경 범위 (`app/broker/kis.py` + `tests/test_kis_paper_order_submission.py` + 3 개 narrow test edits + `patch.md`) 를 확인하고 `git add` → `git commit` 을 수동 실행하는 것이다. 본 review 는 commit / push / merge / deploy 를 수행하지 않는다.
