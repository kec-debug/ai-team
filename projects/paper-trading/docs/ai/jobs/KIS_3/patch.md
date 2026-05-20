# KIS_3 — Patch Summary

## 1. Files Changed

- `docs/kis/MISSING_OFFICIAL_VALUES.md`
- `projects/paper-trading/docs/ai/jobs/KIS_3/recommendation.md`
- `projects/paper-trading/docs/ai/jobs/KIS_3/next-job-request.md`
- `projects/paper-trading/docs/ai/jobs/KIS_3/patch.md`

No `app/`, `tests/`, `.env`, `.env.example`, GUI, `pyproject.toml`, or `README.md` file was modified by this docs-only job.

Current worktree note: `git status` still shows pre-existing unrelated dirty files from earlier jobs, including `projects/paper-trading/app/*` and `projects/paper-trading/tests/*`. They were not edited for KIS_3 and were not reverted.

## 2. 6.xlsx extraction summary

Source of truth:

- `/root/ai-dev-center/projects/ai-team/uploads/6.xlsx`
- Read with stdlib only: `zipfile` + `xml.etree.ElementTree`
- No `openpyxl`, `pandas`, or third-party dependency was added.

Workbook sheets observed:

- `API 목록`
- `해외주식 주문`
- `해외주식 정정취소주문`
- `해외주식 예약주문접수`
- `해외주식 예약주문접수취소`
- `해외주식 매수가능금액조회`
- `해외주식 미체결내역`
- `해외주식 잔고`
- `해외주식 주문체결내역`
- `해외주식 체결기준현재잔고`
- `해외주식 예약주문조회`
- `해외주식 결제기준잔고`
- `해외주식 일별거래내역`
- `해외주식 기간손익`
- `해외증거금 통화별조회`
- `해외주식 미국주간주문`
- `해외주식 미국주간정정취소`
- `해외주식 지정가주문번호조회`
- `해외주식 지정가체결내역조회`

Consumed sheets and ranges:

- `해외주식 주문체결내역`, rows 54-85, columns B-G:
  - B = Element / field name
  - C = 한글명
  - D = Type
  - E = Required
  - F = Length
  - G = Description
- `해외주식 미체결내역`, rows 46-74, columns B-G:
  - B = Element / field name
  - C = 한글명
  - D = Type
  - E = Required
  - F = Length
  - G = Description
- `API 목록`, rows 1-19, columns A-K:
  - scanned for a separate "주문상태" / "order status" endpoint.

Extraction result:

- `해외주식 주문체결내역`: 32 `output[]` sub-fields extracted, 0 left as `<TBD>`.
- `해외주식 미체결내역`: 29 `output[]` sub-fields extracted, 0 left as `<TBD>`.
- Separate order-status endpoint: not found in `API 목록`. The only `주문상태` text found in the workbook was reservation-order status fields in the unrelated `해외주식 예약주문조회` sheet.

## 3. §4.7.1 added rows

Added 32 `Confirmed: yes` rows under:

- `### 4.7.1 주문체결내역 (VTTS3035R) Response output[] sub-fields`

Rows came from `uploads/6.xlsx` sheet `해외주식 주문체결내역`, rows 54-85.

Confirmed mapping-relevant fields include:

- order id: `output[].odno`
- original order id: `output[].orgn_odno`
- symbol: `output[].pdno`
- side: `output[].sll_buy_dvsn_cd`
- order quantity: `output[].ft_ord_qty`
- order price: `output[].ft_ord_unpr3`
- filled quantity: `output[].ft_ccld_qty`
- fill price: `output[].ft_ccld_unpr3`
- fill amount: `output[].ft_ccld_amt3`
- remaining quantity: `output[].nccs_qty`
- status text: `output[].prcs_stat_name`
- rejection reason: `output[].rjct_rson`, `output[].rjct_rson_name`
- order time: `output[].ord_tmd`
- exchange: `output[].ovrs_excg_cd`
- currency: `output[].tr_crcy_cd`

No unverified field name was marked `Confirmed: yes`.

## 4. §4.7.2 added rows

Added 29 `Confirmed: yes` rows under:

- `### 4.7.2 미체결내역 (TTTS3018R) Response output[] sub-fields (실전 only — 모의 미지원)`

Rows came from `uploads/6.xlsx` sheet `해외주식 미체결내역`, rows 46-74.

The section explicitly states:

- `TTTS3018R` is paper-unsupported.
- The repository must not call this endpoint from `KisBroker.get_open_orders()` in paper mode.
- The table is cataloged for future live-expansion completeness only.

## 5. §4.2 row addition

No §4.2 row was added.

Reason:

- `API 목록` rows 1-19 do not contain a separate "주문상태 조회" endpoint.
- KIS_2-check's decision remains valid: paper order status must be inferred from supported query data, not a separate endpoint.

## 6. audit decision matrix

| 기능 | KIS_2-check 결과 | KIS_3 후 결과 | 사유 |
| --- | --- | --- | --- |
| `get_open_orders` | BLOCKED-BY-DOCS | PARTIALLY READY | `/inquire-nccs` remains paper-unsupported, but `/inquire-ccnl` now has confirmed `odno`, `pdno`, `sll_buy_dvsn_cd`, `ft_ord_qty`, `ft_ccld_qty`, `nccs_qty`, `ft_ord_unpr3`, `prcs_stat_name`, `ord_tmd`, and `ovrs_excg_cd`, enabling total-query plus client-side filtering. |
| `get_fills` | PARTIALLY READY → effectively BLOCKED | PARTIALLY READY | Confirmed fields now support fill projection from `VTTS3035R`, but no separate fill id or explicit fill timestamp was found. |
| `get_order_status` | BLOCKED-BY-DOCS | PARTIALLY READY | No separate endpoint and no paper ODNO query, but total-query plus client-side lookup can use confirmed `odno`, quantities, status, and rejection fields. |

## 7. next-job-request.md decision

Created `docs/ai/jobs/KIS_3/next-job-request.md`.

Reason:

- At least one function became READY/PARTIALLY READY; in fact all three query functions are now PARTIALLY READY.
- The draft scopes the follow-up as `api-orders-paper-003-query`.
- The draft requires adapter-level only implementation, a new GET-only `KisQueryTransport`, paper request constraints from §4.7, and only §4.7.1 `Confirmed: yes` response fields.
- The draft forbids OMS extension, GUI/status-surface changes, live TR_IDs, paper-unsupported TR_IDs, `/inquire-nccs` in paper, and unconfirmed response-field guessing.

## 8. Safety confirmation

- No `app/` or `tests/` file was edited by KIS_3.
- No `.env`, `.env.example`, GUI, `pyproject.toml`, or `README.md` file was edited.
- No third-party dependency was added.
- No real app key, app secret, account number, access token, or Bearer token was added.
- `docs/kis/MISSING_OFFICIAL_VALUES.md` was changed additively only at the end of §4.7, immediately before §4.8.
- §1 / §2 / §3 / §4.1-§4.7 existing text / §4.8 / §4.9 / §4.10 remain unchanged outside the inserted §4.7.1 and §4.7.2 subsections.
- §4.2 was not changed.
- `docs/kis/MISSING_OFFICIAL_VALUES.md` diff shows 77 insertions and no deletions.

`git diff --name-only HEAD -- projects/paper-trading/app projects/paper-trading/tests` output:

```text
projects/paper-trading/app/api/server.py
projects/paper-trading/app/broker/kis.py
projects/paper-trading/tests/test_broker_interface.py
projects/paper-trading/tests/test_kis_http_boundaries.py
```

These are pre-existing unrelated dirty files from earlier work in this session. KIS_3 did not edit them. I did not revert them because reverting user/previous-job changes is outside scope.

## 9. Safety grep output

```text
$ grep -rnE "^(from|import) (requests|httpx|aiohttp|urllib3|openpyxl|pandas)" docs/ai/jobs/KIS_3
<no output>

$ grep -rn "Bearer eyJ\|access_token=eyJ\|appkey=eyJ" docs/ai/jobs/KIS_3 /root/ai-dev-center/projects/ai-team/docs/kis/MISSING_OFFICIAL_VALUES.md
docs/ai/jobs/KIS_3/patch.md:167:$ grep -rn "Bearer eyJ\|access_token=eyJ\|appkey=eyJ" docs/ai/jobs/KIS_3 /root/ai-dev-center/projects/ai-team/docs/kis/MISSING_OFFICIAL_VALUES.md
docs/ai/jobs/KIS_3/patch.md:168:docs/ai/jobs/KIS_3/plan.md:127:- `grep -rn "Bearer eyJ\|access_token=eyJ\|appkey=eyJ" docs/ai/jobs/KIS_3 docs/kis/MISSING_OFFICIAL_VALUES.md` → 0 lines (forbidden literal grep, 단 본 plan / codex-task / patch 의 instruction 텍스트 인용은 예외).
docs/ai/jobs/KIS_3/patch.md:169:docs/ai/jobs/KIS_3/codex-task.md:227:grep -rn "Bearer eyJ\|access_token=eyJ\|appkey=eyJ" docs/ai/jobs/KIS_3 docs/kis/MISSING_OFFICIAL_VALUES.md || true
docs/ai/jobs/KIS_3/patch.md:179:The grep hits for `Bearer eyJ`, `12345678`, and `fake-key` are instruction self-references in KIS_3 docs, not catalog or generated secret content.
docs/ai/jobs/KIS_3/plan.md:127:- `grep -rn "Bearer eyJ\|access_token=eyJ\|appkey=eyJ" docs/ai/jobs/KIS_3 docs/kis/MISSING_OFFICIAL_VALUES.md` → 0 lines (forbidden literal grep, 단 본 plan / codex-task / patch 의 instruction 텍스트 인용은 예외).
docs/ai/jobs/KIS_3/codex-task.md:227:grep -rn "Bearer eyJ\|access_token=eyJ\|appkey=eyJ" docs/ai/jobs/KIS_3 docs/kis/MISSING_OFFICIAL_VALUES.md || true

$ grep -rn "12345678\|fake-account\|fake-key" docs/ai/jobs/KIS_3 /root/ai-dev-center/projects/ai-team/docs/kis/MISSING_OFFICIAL_VALUES.md
docs/ai/jobs/KIS_3/patch.md:171:$ grep -rn "12345678\|fake-account\|fake-key" docs/ai/jobs/KIS_3 /root/ai-dev-center/projects/ai-team/docs/kis/MISSING_OFFICIAL_VALUES.md
docs/ai/jobs/KIS_3/patch.md:172:docs/ai/jobs/KIS_3/plan.md:128:- `grep -rn "12345678\|fake-account\|fake-key" docs/ai/jobs/KIS_3 docs/kis/MISSING_OFFICIAL_VALUES.md` → 0 lines.
docs/ai/jobs/KIS_3/patch.md:173:docs/ai/jobs/KIS_3/codex-task.md:228:grep -rn "12345678\|fake-account\|fake-key" docs/ai/jobs/KIS_3 docs/kis/MISSING_OFFICIAL_VALUES.md || true
docs/ai/jobs/KIS_3/patch.md:179:The grep hits for `Bearer eyJ`, `12345678`, and `fake-key` are instruction self-references in KIS_3 docs, not catalog or generated secret content.
docs/ai/jobs/KIS_3/plan.md:128:- `grep -rn "12345678\|fake-account\|fake-key" docs/ai/jobs/KIS_3 docs/kis/MISSING_OFFICIAL_VALUES.md` → 0 lines.
docs/ai/jobs/KIS_3/codex-task.md:228:grep -rn "12345678\|fake-account\|fake-key" docs/ai/jobs/KIS_3 docs/kis/MISSING_OFFICIAL_VALUES.md || true

$ grep -rn "^Result: yes" /root/ai-dev-center/projects/ai-team/docs/kis/MISSING_OFFICIAL_VALUES.md
<no output>
```

The grep hits for `Bearer eyJ`, `12345678`, and `fake-key` are instruction self-references in KIS_3 docs, not catalog or generated secret content.

## 10. Test Results

Commands run from `/root/ai-dev-center/projects/ai-team/projects/paper-trading`:

```text
$ .venv/bin/python -m compileall app tests
Result: passed, exit code 0

$ .venv/bin/python -m pytest -p no:cacheprovider
Result: 458 passed in 0.73s
```

The pytest count matches the pre-job baseline of 458 tests.

## 11. Claude verification prompt

> Read `docs/ai/jobs/KIS_3/plan.md`, `recommendation.md`, `next-job-request.md` (if present), and `patch.md`. Run `git diff` and `git diff --name-only HEAD`. Verify: (a) only catalog + KIS_3 docs were modified; no `app/` / `tests/` / `.env` / GUI / `pyproject.toml` / `README.md` changes; (b) every `Confirmed: yes` row added to §4.7.1 / §4.7.2 cites a 6.xlsx cell in `patch.md`; (c) §4.7.2 explicitly marks paper-unsupported; (d) §1 / §2 / §3 / §4.1–§4.10 outside the new subsections are unchanged byte-for-byte; (e) no third-party dependency was added; (f) no real app key / app secret / account number / Bearer token / access token appears in any file; (g) audit decision matrix in `recommendation.md` matches the actual sub-field coverage; (h) `next-job-request.md` (if present) only covers methods classified as READY or PARTIALLY READY, and forbids implementation of BLOCKED methods; (i) the optional §4.2 row addition (if any) is faithfully cited from 6.xlsx; (j) pytest count matches the pre-job baseline. Output verdict `APPROVE`, `REQUEST CHANGES`, or `BLOCK`.

## 12. Follow-up Codex prompt rules

Only if Claude returns REQUEST CHANGES or BLOCK:

- Quote findings verbatim under `## Findings`.
- For each finding, write `## Required change` stating the exact catalog edit, why it is in scope of KIS_3, and the safety rule preserved.
- Re-state absolute prohibitions and verification commands.
- Do not expand scope: any change to `app/`, `tests/`, `.env`, GUI, or non-§4.7 catalog sections requires human approval.
- End with: "Update `patch.md` (do not create a new one). Append a `## Follow-up <N>` section explaining what changed and re-run verification. Do not commit / push / merge."

## 13. Status

READY FOR REVIEW
