## 1. Files Changed

- `app/broker/kis.py`
- `tests/test_kis_account_client.py`
- `tests/test_kis_http_boundaries.py`
- `docs/ai/jobs/api-account-001/patch.md`

## 2. Implementation Summary

- Implemented KIS paper read-only account and position retrieval using the confirmed overseas balance endpoint from `docs/kis/MISSING_OFFICIAL_VALUES.md` §2.2 / §2.4 / §2.5 / §2.6:
  - Path: `/uapi/overseas-stock/v1/trading/inquire-balance`
  - Paper TR ID: `VTTS3012R`
  - Method: `GET`
- Added `_split_kis_account_no()` to enforce the KIS 10-digit account shape and split it into `CANO` and `ACNT_PRDT_CD`.
- Added a dedicated `KisAccountTransport` boundary inside `app/broker/kis.py`, with:
  - `UrllibAccountTransport` using only stdlib `urllib.request`
  - paper host allowlist
  - paper TR ID allowlist
  - paper exchange/currency allowlists
  - sanitized short failure reasons
  - retry only for 5xx/transport failures
- `KisAccountClient.get_account()` now authenticates, enforces paper/live/kill-switch gates, fetches one or more balance pages up to `KIS_BALANCE_MAX_PAGES`, sanitizes raw responses, and returns aggregated `output1` rows plus the last `output2`.
- `KisAccountClient.get_positions()` now maps only confirmed catalog fields:
  - `output1[].ovrs_pdno`
  - `output1[].ovrs_cblc_qty`
  - `output1[].pchs_avg_pric`
  - `output1[].ovrs_stck_evlu_amt`
  - `output1[].tr_crcy_cd`
  - `output1[].ovrs_excg_cd`
- `KisPosition` now exposes `currency` and `exchange` with defaults, preserving existing positional construction.
- `KisAccountClient.get_cash_balance()` remains fail-closed with `KisDataUnavailableError("paper_cash_balance_not_available_official_field_missing")`.
  - Reason: `VTTS3007R` is per-symbol buying power, not account cash.
  - Reason: `VTRP6504R` paper mode exposes only `output3`, and the cash/withdrawable sub-fields remain unconfirmed.

## 3. Safety Confirmation

- No live trading was enabled.
- No order, cancel, replace, fill, open-order, or order-status endpoint was implemented.
- `place_order`, `cancel_order`, `replace_order`, `get_open_orders`, `get_fills`, and `get_order_status` behavior was not changed.
- `OrderType.MARKET` guards, `ALLOW_MARKET_ORDERS=true` rejection, kill-switch checks, and `validate_kis_order_request()` were not changed.
- `app/broker/kis_http.py` was not changed.
- `.env`, `.env.example`, `app/config.py`, `app/api/*`, `app/static/*`, `app/main.py`, Strategy, Agent, OMS, Risk, Portfolio, Runtime, Session, migrations, auth, payment, and production infra were not changed.
- No third-party HTTP client import was added.
- Account responses are sanitized before returning from `get_account()`.
- Access token, app key, app secret, Bearer header values, and raw account number are not included in exception messages or repr output added by this patch.

Safety grep results:

```text
$ grep -rnI -E "^(from|import) (requests|httpx|aiohttp|urllib3)" app/broker tests
0 lines

$ grep -rnI "TTTS3012R\|CTRP6504R\|CTRP6010R\|CTOS4001R\|TTTS3039R\|TTTC2101R" app tests
0 lines

$ grep -rnI "openapi.koreainvestment.com:9443" app tests
app/config.py:53:    kis_base_url_live: str = "https://openapi.koreainvestment.com:9443"
app/config.py:194:        kis_base_url_live=_str_env("KIS_BASE_URL_LIVE") or "https://openapi.koreainvestment.com:9443",

$ grep -rnI "ALLOW_MARKET_ORDERS=true\|allow_market_orders=True" app
app/config.py:150:            "ALLOW_MARKET_ORDERS=true is rejected in this phase (market orders disabled)"

$ grep -rnI "Bearer eyJ" app tests docs/ai/jobs/api-account-001 || true
tests/test_missing_market_data_values_doc.py:43:    assert "Bearer eyJ" not in text, "JWT-style bearer token present"
docs/ai/jobs/api-account-001/plan.md:458:- `test_get_account_sanitizes_response`: FakeAccountTransport 가 응답에 `{"appkey": "fake-key-XYZ", "access_token": "Bearer eyJ..."}` 같은 echo 를 포함. `result` 의 raw text dump 에서 sensitive 값이 `<redacted>` 로 마스킹.
docs/ai/jobs/api-account-001/plan.md:518:grep -rn "Bearer eyJ\|access_token=eyJ" app tests docs/ai/jobs/api-account-001
docs/ai/jobs/api-account-001/codex-task.md:503:21. `test_get_account_sanitizes_echoed_secrets` (FakeAccountTransport returns page with `"appkey": "fake-key-XYZ"`, `"access_token": "Bearer eyJfake"`, etc. → resulting dict serialized via `json.dumps(result)` does not contain those literals; sensitive keys redacted)
docs/ai/jobs/api-account-001/codex-task.md:512:forbidden = ("fake-key-XYZ", "fake-secret-XYZ", "12345678", "Bearer eyJ")
docs/ai/jobs/api-account-001/codex-task.md:602:grep -rn "Bearer eyJ" app tests docs/ai/jobs/api-account-001 || true

$ grep -rn "from app.broker.kis" app/strategy 2>/dev/null || true
0 lines

$ grep -rn "from app.broker.kis" app/agent 2>/dev/null || true
0 lines
```

Notes on grep output:
- The live base URL and `ALLOW_MARKET_ORDERS=true` string are existing `app/config.py` guard/config literals outside the approved edit scope.
- The `Bearer eyJ` hits are existing test/assertion or job-instruction text, not runtime code or newly added secret material.

## 4. Test Results

```text
$ .venv/bin/python -m compileall app tests
PASS

$ .venv/bin/python -m pytest -p no:cacheprovider tests/test_kis_account_client.py tests/test_kis_http_boundaries.py
37 passed in 0.04s

$ .venv/bin/python -m pytest -p no:cacheprovider
365 passed, 1 failed in 0.70s
```

Full-suite blocker:

```text
FAILED tests/test_missing_official_values_doc.py::test_missing_official_values_does_not_leak_real_secrets
AssertionError: assert 'Confirmed: yes' not in text
```

The failing assertion conflicts with this job's approved premise that `docs/kis/MISSING_OFFICIAL_VALUES.md` now contains confirmed KIS catalog rows. I did not modify that test because it is outside the approved file scope.

## 5. Remaining TODOs

- BLOCKED: full pytest is not clean because of the out-of-scope catalog test noted above.
- Paper cash balance still needs official catalog work for `VTRP6504R` paper `output3` cash/withdrawable sub-fields before it can be implemented.
- Per-symbol paper buying power via `VTTS3007R` should be a separate follow-up job because it does not match `KisCashBalance`.

Claude verification prompt:

```text
Read `docs/ai/jobs/api-account-001/plan.md` and `docs/ai/jobs/api-account-001/patch.md`. Run `git diff` on the working tree. Verify: (a) only `app/broker/kis.py`, `tests/test_kis_account_client.py`, and the narrow `tests/test_kis_http_boundaries.py` change were modified for implementation; (b) only `VTTS3012R` and the paper inquire-balance path were introduced by this patch; (c) `get_account` / `get_positions` use only catalog `Confirmed: yes` fields (`output1[].ovrs_pdno` / `ovrs_cblc_qty` / `pchs_avg_pric` / `ovrs_stck_evlu_amt` / `tr_crcy_cd` / `ovrs_excg_cd`); (d) `get_cash_balance` is fail-closed; (e) `_split_kis_account_no` enforces 10-digit format; (f) `_validate_paper_account_query` blocks live/non-paper/kill-switch; (g) `app/broker/kis_http.py` and the OAuth allowlist are unchanged; (h) no third-party HTTP imports; (i) Strategy/Agent do not import `app.broker.kis`; (j) all order endpoints keep their NotImplementedError/dry-run behavior; (k) market-order guards, `ALLOW_MARKET_ORDERS=true` block, and kill-switch behavior are unchanged; (l) `.env`, `.env.example`, and `docs/kis/MISSING_OFFICIAL_VALUES.md` are unchanged; (m) focused tests pass; (n) full pytest is blocked by the out-of-scope `Confirmed: yes` catalog assertion. Output verdict `APPROVE`, `REQUEST CHANGES`, or `BLOCK`.
```

Follow-up Codex prompt rules if Claude returns REQUEST CHANGES or BLOCK:

- Quote Claude's specific findings verbatim under `## Findings`.
- For each finding, include `## Required change` with the exact edit, why it is in scope for `api-account-001`, and the safety rule that must remain intact.
- Re-state the absolute prohibitions and verification commands.
- Do not expand scope beyond `app/broker/kis.py`, `tests/test_kis_account_client.py`, `tests/test_kis_http_boundaries.py`, `patch.md`, or optional `README.md`.
- End with: `Update patch.md (do not create a new one). Append a ## Follow-up <N> section explaining what changed and re-run verification. Do not commit / push / merge.`

## Follow-up 1

Claude review verdict was `REQUEST_CHANGES` for one completion blocker:

- `tests/test_missing_official_values_doc.py::test_missing_official_values_does_not_leak_real_secrets` still reflected the pre-KIS_2 catalog assumption that `Confirmed: yes`, official KIS paths, and official KIS domains must be absent from `docs/kis/MISSING_OFFICIAL_VALUES.md`.

Required change applied:

- Updated only `tests/test_missing_official_values_doc.py::test_missing_official_values_does_not_leak_real_secrets`.
- Removed `assert "Confirmed: yes" not in text`.
- Removed official vendor path/domain forbidden entries for `/uapi/`, `/oauth2/`, `paper-api`, and `koreainvestment.com`.
- Kept `assert "<TBD>" in text`.
- Kept real credential prefix forbidden entries: `PSNFD`, `PKID`, `AKIA`, `sk-`, and `ghp_`.

Verification after Follow-up 1:

```text
$ .venv/bin/python -m compileall app tests
PASS

$ .venv/bin/python -m pytest -p no:cacheprovider
366 passed in 0.68s
```

No code, catalog, environment, auth, GUI, order, risk, OMS, production infra, or secret files were changed in this follow-up.

Verdict: READY FOR REVIEW
