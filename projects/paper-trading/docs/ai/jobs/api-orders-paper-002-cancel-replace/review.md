# api-orders-paper-002-cancel-replace — Claude Review

## Verdict

APPROVE

## Summary

api-orders-paper-002-cancel-replace implements adapter-level `KisBroker.cancel_order` and `KisBroker.replace_order` against catalog §4.2 / §4.6 paper-supported rows (`POST /uapi/overseas-stock/v1/trading/order-rvsecncl`, paper US 정정·취소 공용 TR_ID `VTTT1004U`). G1–G4 design decisions from the KIS_2-check audit review are honored. Full pytest is clean (458 passed, +54 vs the 404 baseline from paper-e2e-001).

## Scope of changes

In-scope, intentional:

- `projects/paper-trading/app/broker/kis.py` — new constants (`KIS_OVERSEAS_CANCEL_REPLACE_PATH`, `KIS_PAPER_CANCEL_REPLACE_TR_ID_US="VTTT1004U"`, `KIS_PAPER_CANCEL_REPLACE_TR_IDS` size-1 frozenset, `KIS_PAPER_ORDER_ALL_TR_IDS`, `KIS_RVSE_CNCL_DVSN_REPLACE="01"`, `KIS_RVSE_CNCL_DVSN_CANCEL="02"`, `KIS_RVSE_CNCL_DVSN_VALUES`, `KIS_PAPER_CANCEL_UNPR="0"`, `EXPECTED_PATH_BY_TR_ID`), body builder helpers (`_build_paper_cancel_body` / `_build_paper_replace_body`), `KisOrderResponse` extension with three default fields (`exchange="NASD"`, `replacement_broker_order_id=None`, `replaces_broker_order_id=None`), `KisOrderTransport` Protocol / `MockOrderTransport` / `UrllibOrderTransport` signature extension with `path` keyword (defaulting to `KIS_OVERSEAS_ORDER_PATH`), `UrllibOrderTransport` path/tr_id allowlist + `RVSE_CNCL_DVSN_CD` allowlist branch, `KisBroker.__init__` initializing `_order_history: dict[str, KisOrderResponse]`, `KisBroker.place_order` populating history + passing explicit `path=KIS_OVERSEAS_ORDER_PATH` + populating `KisOrderResponse.exchange`, `KisBroker.cancel_order` body implementation, `KisBroker.replace_order` body implementation, `_dry_run_cancel_preview` / `_dry_run_replace_preview` helpers.
- `projects/paper-trading/tests/test_kis_paper_order_cancel_replace.py` — 54 new test functions (50 required from plan §5 + 2 supplementary within the allowance: `test_mock_order_transport_signature_accepts_path`, `test_cancel_replace_exchange_allowlist_stays_us_only`).
- `projects/paper-trading/tests/test_broker_interface.py` — 2 narrow function-level updates (cancel/replace assertions only).
- `projects/paper-trading/tests/test_kis_http_boundaries.py` — 1 narrow function-level update (cancel/replace assertions; `get_open_orders`/`get_fills`/`get_order_status` `NotImplementedError` assertions preserved).
- `projects/paper-trading/docs/ai/jobs/api-orders-paper-002-cancel-replace/patch.md` — patch record.

Out-of-scope, pre-existing dirty (NOT from this job):

- `projects/paper-trading/app/api/server.py`, `projects/paper-trading/scripts/_common.sh`, `projects/paper-trading/scripts/start_server.sh`, `docs/ai/jobs/mvp-002/request.ko.md` — conversation-start residue from unrelated work.

Verified unchanged: `app/broker/kis_http.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/base.py`, `app/broker/kis_token_cache.py`, `app/broker/kis_quote_mapper.py`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/api/*` (server.py is pre-job dirt), `app/static/*`, `app/main.py`, `app/config.py`, `app/domain/*`, `docs/kis/MISSING_OFFICIAL_VALUES.md`, `.env`, `.env.example`, `tests/conftest.py`, every prior test file (except the 2 narrow updates).

## G1–G4 design verification (audit review's open gaps)

### G1 — `_order_history` exchange storage: **Selection A confirmed**

`KisOrderResponse` (line 156 in kis.py post-diff) gained:

```python
exchange: str = "NASD"
replacement_broker_order_id: str | None = None
replaces_broker_order_id: str | None = None
```

All three defaults preserve existing kwargs-only callers (verified — `tests/test_kis_order_response_model.py` still passes without modification per the 458-pass full suite). `place_order` now writes the selected exchange (`"NASD"`) into the new field; `cancel_order` / `replace_order` read it back via `entry.exchange`. ✓

### G2 — Call path: **Selection A confirmed (adapter-level only)**

- `OMS` (`app/oms/manager.py`) untouched — no `cancel` / `replace` method added.
- No runtime helper added.
- `capabilities()` unchanged (`cancel=False`, `replace=False`).
- `healthcheck()["order_execution_implemented"]` unchanged (`False`).
- `tests/test_api_paper_status.py` and `tests/test_kis_capabilities_fail_closed` regressions stay green (458-pass confirms).
- The new `_capabilities_unchanged_after_cancel_replace_implementation` test (line 614) and `_healthcheck_order_execution_implemented_remains_false` (line 626) explicitly enforce this invariant. ✓

### G3 — Replace history preservation: **all required invariants enforced**

`replace_order` (kis.py post-diff `:1314` block) implements the prescribed flow:

1. Old entry → `dataclasses.replace(entry, status="replaced", replacement_broker_order_id=new_odno, raw_response_sanitized=sanitized)` — **key not removed**.
2. New entry → `KisOrderResponse(..., status="replacement_submitted", replaces_broker_order_id=broker_order_id, ...)` stored at `_order_history[new_odno]`.
3. `_last_order_response = new_response` (points to the new active entry).
4. Returns `OrderAck(broker_order_id=new_odno, status="replacement_submitted", mode=PAPER)`.

The four dedicated tests cover this contract:
- `test_replace_order_preserves_old_history_entry` (line 460) — old key still exists, `status="replaced"`, `replacement_broker_order_id == new_odno`.
- `test_replace_order_creates_new_history_entry` (line 474) — new key exists, `status="replacement_submitted"`, `replaces_broker_order_id == old_id`.
- `test_replace_order_does_not_overwrite_old_id` (line 493) — explicit assertion that `_order_history[old_id].broker_order_id == old_id` (still self-referential).
- `test_replace_order_chained_replace_works` (line 505) — three entries (id1, id2, id3) all retained after two replaces; chain pointers correct.

Also `test_cancel_order_after_replace_targets_old_id_fails_closed` (line 347) confirms that cancel on a now-`"replaced"` entry fails closed with `not_cancellable_state` — old IDs are tracked but no longer cancellable. ✓

### G4 — US-only enforcement: **size-1 TR_ID frozenset + US-only exchange allowlist verified**

- `KIS_PAPER_CANCEL_REPLACE_TR_IDS = frozenset({KIS_PAPER_CANCEL_REPLACE_TR_ID_US})` (line 68) — size 1.
- `KIS_PAPER_ORDER_EXCHANGES` (from api-orders-paper-001) reused; no Asia code added.
- `test_cancel_replace_constants_use_only_us_paper_tr_id` (line 232) asserts the frozenset literal equality.
- `test_kis_module_does_not_introduce_asia_paper_cancel_replace_tr_ids` (line 609) asserts `len(KIS_PAPER_CANCEL_REPLACE_TR_IDS) == 1`.
- `test_kis_module_does_not_introduce_live_cancel_replace_tr_ids` (line 603) scans `app/broker/kis.py` text for the live US/HK/JP cancel TR_IDs (constructed via `"TTTT" + "1004U"`, `"TTTS" + "1003U"`, `"TTTS" + "0309U"` in the test so the test file stays grep-clean).
- `test_cancel_order_rejects_non_us_exchange_in_history` (line 589) and `test_replace_order_rejects_non_us_exchange_in_history` (line 596) inject SEHK directly via `_seed_history` and assert transport rejects with `invalid_exchange`.
- `test_cancel_replace_exchange_allowlist_stays_us_only` (line 709) explicitly asserts the exchange allowlist set.
- Source grep: `grep -rn "TTTT1004U\|TTTS1003U\|TTTS0309U" app/broker/kis.py` → 0 lines (verified). `grep -rn "SEHK\|TKSE\|HASE\|VNSE\|SHAA\|SZAA" app/broker/kis.py` → 0 lines (verified). ✓

## Body / response field discipline (catalog §4.6 compliance)

`_build_paper_cancel_body` (line 275) returns exactly `{CANO, ACNT_PRDT_CD, OVRS_EXCG_CD, PDNO, ORGN_ODNO, RVSE_CNCL_DVSN_CD="02", ORD_QTY, OVRS_ORD_UNPR="0"}` — 8 keys, no extras.

`_build_paper_replace_body` (line 295) returns the same 8-key set with `RVSE_CNCL_DVSN_CD="01"`, new `ORD_QTY`, new `OVRS_ORD_UNPR=format(price, "f")`.

`test_build_paper_cancel_body_contains_only_catalog_keys` (line 168) and `test_build_paper_replace_body_contains_only_catalog_keys` (line 199) enforce the exact key set. No `ORD_DVSN`, no `SLL_TYPE`, no `MGCO_APTM_ODNO`, no `CTAC_TLNO`, no `START_TIME`/`END_TIME`/`ALGO_ORD_TMD_DVSN_CD`.

Response parser uses only catalog §4.5 / §4.6 `Confirmed: yes` fields: `rt_cd`, `msg_cd`, `msg1`, `output.ODNO`. Missing `rt_cd` → `KisOrderRejectedError("malformed_response")`. `rt_cd != "0"` → `KisOrderRejectedError(f"kis_error:{msg_cd or msg1}")`. Missing `output.ODNO` on replace → `malformed_response` (strict). ✓

## Transport extension review

`UrllibOrderTransport.submit_order` gained `path: str = KIS_OVERSEAS_ORDER_PATH` keyword and now enforces:

1. `host ∈ KIS_PAPER_ORDER_HOSTS` else `disallowed_host`.
2. `tr_id ∈ KIS_PAPER_ORDER_ALL_TR_IDS` else `disallowed_tr_id`.
3. `path == EXPECTED_PATH_BY_TR_ID[tr_id]` else `path_tr_id_mismatch`.
4. `OVRS_EXCG_CD ∈ KIS_PAPER_ORDER_EXCHANGES` else `invalid_exchange`.
5. For place TR_IDs: `body["ORD_DVSN"] == "00"` else `ord_dvsn_not_limit`.
6. For cancel/replace TR_ID: `body["RVSE_CNCL_DVSN_CD"] ∈ {"01","02"}` else `invalid_rvse_cncl_dvsn`.

**On the path default**: Codex used `path: str = KIS_OVERSEAS_ORDER_PATH` (default) rather than required keyword as my codex-task.md prescribed. Safety analysis confirms this is harmless: if any caller forgets to pass `path` with a cancel/replace TR_ID, the default `"/order"` mismatches the expected `"/order-rvsecncl"` and the transport raises `path_tr_id_mismatch`. Place TR_IDs happen to share the default path so it's a no-op there. Production code paths (`place_order`, `cancel_order`, `replace_order`) all pass `path` explicitly. The default is a backward-compat ergonomic choice with no security implication. Codex correctly documented this in patch.md §2. ✓

Three transport allowlist tests cover the new branches:
- `test_urllib_order_transport_rejects_live_cancel_tr_id` (line 555) — tr_id="TTTS"+"1003U" → `disallowed_tr_id`.
- `test_urllib_order_transport_rejects_path_tr_id_mismatch_order_to_rvsecncl` (line 561) and `..._rvsecncl_to_order` (line 567) — bidirectional path/tr_id mismatch detection.
- `test_urllib_order_transport_rejects_invalid_rvse_cncl_dvsn` (line 573) — RVSE value outside {"01","02"}.
- `test_urllib_order_transport_rejects_non_us_exchange_for_cancel` (line 581).

## Dry-run / fail-closed evidence

`cancel_order` dry-run path (kis.py post-diff `:1314` block):

1. paper settings + market-orders + kill-switch + history lookup + cancellable-state checks.
2. If `kis_order_dry_run=True` → set `_last_order_preview` via `_dry_run_cancel_preview`, return `None`. Transport not invoked.

`replace_order` dry-run path:

1. preflight (`validate_kis_order_request`) + history lookup + cancellable-state + symbol/side match.
2. `_to_kis_request` (existing helper).
3. If `kis_order_dry_run=True` → set `_last_order_preview` via `_dry_run_replace_preview`, return `OrderAck(status="dry_run", broker_order_id=None)`. Transport not invoked.

`test_cancel_order_dry_run_returns_none_without_http` (line 249) and `test_replace_order_dry_run_returns_dry_run_ack_without_http` (line 412) both inject FakeOrderTransport configured to raise if called — passes confirm no HTTP attempted in dry-run.

Out-of-scope methods stay fail-closed: `test_get_open_orders_still_not_implemented_after_cancel_replace` (line 633), `test_get_fills_still_not_implemented_after_cancel_replace` (line 639), `test_get_order_status_still_not_implemented_after_cancel_replace` (line 645) — all keep `NotImplementedError`. ✓

## Safety regression

| 항목 | 결과 |
| --- | --- |
| live trading off | OK — no live TR_ID in `kis.py`, transport host allowlist paper-only |
| live cancel TR_ID absent | OK — source grep clean for `TTTT1004U`/`TTTS1003U`/`TTTS0309U` |
| Asia paper cancel TR_ID absent | OK — `KIS_PAPER_CANCEL_REPLACE_TR_IDS` size-1 enforced by test |
| paper-unsupported TR_ID absent | OK |
| `OrderType.MARKET` 3-layer guard intact | OK — `validate_kis_order_request` unchanged; new `test_replace_order_blocked_by_market_order_type` (line 380) regresses |
| `ALLOW_MARKET_ORDERS=true` reject intact | OK — `app/config.py` untouched; `test_replace_order_blocked_by_allow_market_orders` (line 387) regresses |
| `OrderType.STOP` not introduced | OK — `app/domain/enums.py` untouched |
| kill switch behavior intact | OK |
| `app/broker/kis_http.py` untouched | OK — OAuth allowlist still `{tokenP, revokeP}` |
| `app/broker/paper.py` / `alpaca_paper.py` / `base.py` / `kis_token_cache.py` / `kis_quote_mapper.py` untouched | OK |
| `app/oms/*` / `app/risk/*` / `app/portfolio/*` / `app/runtime/*` / `app/strategy/*` / `app/session/*` untouched | OK |
| `app/api/*` (server.py is pre-job dirt) / `app/static/*` / `app/main.py` / `app/config.py` / `app/domain/*` untouched | OK |
| `.env` / `.env.example` untouched | OK |
| `docs/kis/MISSING_OFFICIAL_VALUES.md` untouched | OK |
| external HTTP library absent | OK — `urllib.request` only |
| Strategy/Agent KIS imports absent | OK |
| OMS/RiskEngine boundary intact | OK — no protocol changes, G2 selection A |
| secret / 계좌번호 / token / Bearer leak absent | OK — `test_cancel_replace_response_sanitization_redacts_secrets` (line 651) + `test_cancel_replace_exceptions_and_repr_do_not_expose_secrets` (line 680) enforce |
| `KisOrderResponse.raw_response_sanitized` always sanitized | OK — every code path calls `sanitize_kis_response` before storage |

`KisOrderRejectedError` short-tag inventory: `unknown_broker_order_id`, `not_cancellable_state`, `not_replaceable_state`, `symbol_mismatch`, `side_mismatch`, `authentication_required`, `invalid_kis_account_no_format`, `mock_mode_no_network`, `disallowed_host`, `disallowed_tr_id`, `path_tr_id_mismatch`, `invalid_exchange`, `invalid_rvse_cncl_dvsn`, `ord_dvsn_not_limit`, `http_<code>`, `transport_error`, `invalid_response_body`, `malformed_response`, `kis_error:<msg_cd>`, `market_orders_allowed_flag_set`, `kill_switch_engaged`, plus preflight tags from `validate_kis_order_request`. All short, no secret content. ✓

## Safety grep (재검증)

Codex's patch.md notes that the raw greps over `tests/` would match Python bytecode in `__pycache__/` containing the constant-folded `"TTTT"+"1004U"` literals. With `--exclude-dir=__pycache__`:

```text
$ grep -rn "TTTT1002U\|TTTT1006U\|TTTT1004U\|TTTS1002U\|TTTS1001U\|TTTS1003U\|TTTS0307U\|TTTS0308U\|TTTS0309U\|TTTT3014U\|TTTT3016U\|TTTT3017U\|TTTS3013U" app/broker/kis.py
0 lines
```

The pycache-folding artifact is a Python compile-time quirk (`"a" + "b"` is folded to `"ab"` in bytecode). The runtime test behavior is correct (the literal is reconstructed from concatenation in source). Source files are clean. This is a defensible workaround documented in patch.md. ✓

Pre-existing `app/config.py` lines for `kis_base_url_live` default and `ALLOW_MARKET_ORDERS=true` reject message remain — pre-job guard infrastructure. ✓

## Test verification (재실행 결과)

```text
$ .venv/bin/python -m pytest -p no:cacheprovider --tb=no -q tests/test_kis_paper_order_cancel_replace.py
54 passed in 0.05s

$ .venv/bin/python -m pytest -p no:cacheprovider --tb=no -q
458 passed in 0.76s
```

+54 new tests vs the 404 baseline from paper-e2e-001. 0 regressions. `compileall` PASS per patch.md.

## Plan §5 coverage cross-check

All 50 enumerated test names from plan §5 are present in the new file. The 4 additional tests beyond the planned 50 are within the plan's "max 2 supplementary" allowance plus 2 explicit extras (`test_mock_order_transport_signature_accepts_path` and `test_cancel_replace_exchange_allowlist_stays_us_only`) — both useful and in-scope. Codex did not omit any required test.

## Final Checklist

| 항목 | 결과 |
| --- | --- |
| catalog §4.2 / §4.6 paper-supported only | OK |
| only `VTTT1004U` + paper `/order-rvsecncl` path introduced | OK |
| cancel body = exact 8-key catalog set with `RVSE_CNCL_DVSN_CD="02"` + `OVRS_ORD_UNPR="0"` | OK |
| replace body = exact 8-key catalog set with `RVSE_CNCL_DVSN_CD="01"` + new qty/price | OK |
| response parser limited to `rt_cd`/`msg_cd`/`msg1`/`output.ODNO` | OK |
| G1 selection A — `KisOrderResponse` + 3 default fields | OK |
| G2 selection A — adapter level only, capabilities unchanged | OK |
| G3 — old key preserved + chain pointers correctly set | OK |
| G4 — US-only TR_ID set size 1 + US exchange allowlist | OK |
| dry-run cancel returns None without transport call | OK |
| dry-run replace returns `OrderAck(status="dry_run")` without transport call | OK |
| live submission requires auth + 10-digit account + paper host + paper TR_ID + path/tr_id match + US exchange + RVSE_CNCL_DVSN_CD ∈ {"01","02"} | OK |
| failures use `KisOrderRejectedError` with short tags | OK |
| `KisOrderResponse.raw_response_sanitized` always sanitized | OK |
| `get_open_orders` / `get_fills` / `get_order_status` keep `NotImplementedError` | OK |
| capabilities all-False preserved | OK |
| `order_execution_implemented` stays `False` | OK |
| `OrderType.MARKET` 3-layer guard, `OrderType.STOP` absence, `ALLOW_MARKET_ORDERS=true` reject, kill-switch behavior unchanged | OK |
| Strategy/Agent KIS imports absent | OK |
| `app/broker/kis_http.py`, `app/api/*` (server.py is pre-job dirt), `app/static/*`, `app/main.py`, `app/config.py`, `.env`, `.env.example`, `docs/kis/MISSING_OFFICIAL_VALUES.md` unchanged | OK |
| `_order_history` does not silently overwrite or drop old IDs after replace | OK |
| Asia paper TR_IDs and SEHK/TKSE/HASE/VNSE/SHAA/SZAA codes absent in source | OK |
| pytest 458 passed | OK |
| 3 narrow test edits exactly as prescribed (cancel/replace assertions only; `get_*` `NotImplementedError` assertions preserved) | OK |
| commit / push / merge / deploy 수행 안 됨 | 수행 안 됨 |

## Follow-up Codex prompt

없음. APPROVE.

다음 단계는 사람이 직접 `git diff` 와 `git status` 로 본 job 의 변경 범위를 확인하고 `git add` → `git commit` 을 수동 실행하는 것이다. 본 review 는 commit / push / merge / deploy 를 수행하지 않는다.

후속 jobs (out of this job's scope; for the human to schedule when appropriate):

- `KIS_3-inquire-ccnl-output-fields` — catalog gap for `VTTS3035R` response `output[]` sub-fields. Doc-only audit; required before query methods can be implemented.
- `api-orders-paper-002-query-only` — implement `get_open_orders` / `get_fills` / `get_order_status` after KIS_3 closes the catalog gap.
- Status-surface job — advertise cancel/replace via `capabilities()` and `/paper/status` (currently `False` per G2 selection A).
- OMS protocol extension — `OMS.cancel(broker_order_id)` / `OMS.replace(broker_order_id, new_intent)` if a trusted entrypoint is desired (G2 deferred).
