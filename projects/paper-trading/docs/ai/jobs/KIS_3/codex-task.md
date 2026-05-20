# KIS_3 — Codex 구현 지시문

You are Codex, executing the plan at `docs/ai/jobs/KIS_3/plan.md`. **This job is docs-only.** No code or test changes anywhere.

Read first (in order):

1. `docs/ai/CLAUDE_CODEX_WORKFLOW.md` (root).
2. `projects/paper-trading/docs/ai/jobs/KIS_3/request.ko.md`.
3. `projects/paper-trading/docs/ai/jobs/KIS_3/plan.md`.
4. `docs/kis/MISSING_OFFICIAL_VALUES.md` (root) — especially §4.2 (endpoint catalog), §4.7 (주문체결내역 paper constraints, ends with `<TBD>` sub-fields note), §4.8 (paper-unsupported list), §4.10 (safety policy).
5. `projects/paper-trading/docs/ai/jobs/KIS_2/patch.md` — confirms `uploads/6.xlsx` is the source of truth and was previously consumed for §2 / §4 catalog.
6. `projects/paper-trading/docs/ai/jobs/KIS_2-check/plan.md`, `recommendation.md`, `review.md` — audit that identified the C1 gap this job closes.

## Absolute prohibitions

- Do not modify any file under `projects/paper-trading/app/` or `projects/paper-trading/tests/`.
- Do not modify `pyproject.toml`, `README.md`, `.env`, `.env.example`, or any GUI file.
- Do not add `openpyxl`, `pandas`, or any third-party dependency. Read `.xlsx` via stdlib `zipfile` + `xml.etree.ElementTree` only.
- Do not invent or guess KIS sub-field names. **Every `Confirmed: yes` row added to the catalog must come from a verifiable cell in `uploads/6.xlsx`**. Anything not verifiable stays `<TBD>` with `Confirmed: no`.
- Do not record real app key / app secret / account number / access token / Bearer token in any artifact, even if `uploads/6.xlsx` happens to contain a sample value. Strip or `<redacted>` such values.
- Do not introduce live TR_IDs into the working catalog beyond what §4.2 already documents (the live TR_IDs listed there are reference-only and were placed by KIS_2 — your job does not extend them).
- Do not modify `docs/kis/MISSING_OFFICIAL_VALUES.md` outside the scope of "add §4.7.1 / §4.7.2 sub-field tables and update §4.2 / §4.8 only if a separate order-status endpoint is found." Other sections (§1 OAuth, §2 account, §3 market data, §4.1–§4.6, §4.9, §4.10, etc.) stay byte-for-byte unchanged.
- Do not run `git commit`, `git push`, `git merge`, PR creation, or deployment.

## Allowed file changes

| Path | Action |
| --- | --- |
| `docs/kis/MISSING_OFFICIAL_VALUES.md` | Modify per §3 below — additive only (new subsections §4.7.1 / §4.7.2; optional §4.2 / §4.8 row tweak if a separate order-status endpoint surfaces). |
| `projects/paper-trading/docs/ai/jobs/KIS_3/recommendation.md` | Create. |
| `projects/paper-trading/docs/ai/jobs/KIS_3/next-job-request.md` | Create **only if** at least one of `get_open_orders` / `get_fills` / `get_order_status` becomes READY or PARTIALLY READY after catalog enrichment. Otherwise skip. |
| `projects/paper-trading/docs/ai/jobs/KIS_3/patch.md` | Create. |

No other files. If a code or test change feels necessary, STOP and document in `patch.md` under `## Out-of-scope discovery` instead of editing.

## 1. Read 6.xlsx safely with stdlib only

`uploads/6.xlsx` is an OOXML zip. Use the following pattern (sketch — adapt as needed):

```python
import zipfile
import xml.etree.ElementTree as ET

NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}

with zipfile.ZipFile("/root/ai-dev-center/projects/ai-team/uploads/6.xlsx") as z:
    # workbook.xml -> sheet name → sheet relationship id → sheet*.xml path
    workbook = ET.fromstring(z.read("xl/workbook.xml"))
    sheets = {
        s.get("name"): s.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id")
        for s in workbook.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheet")
    }
    # xl/_rels/workbook.xml.rels resolves rId -> Target (e.g., worksheets/sheet5.xml)
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rel_targets = {
        r.get("Id"): r.get("Target")
        for r in rels.iter("{http://schemas.openxmlformats.org/package/2006/relationships}Relationship")
    }
    # xl/sharedStrings.xml provides indexed strings
    shared = []
    try:
        ss_root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in ss_root.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}si"):
            # concatenate all <t> elements (handles rich text)
            shared.append("".join(t.text or "" for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")))
    except KeyError:
        pass
    # read a specific sheet by name
    sheet_name_to_path = {name: f"xl/{rel_targets[rid]}" for name, rid in sheets.items()}
    # ...iterate the sheet's <row><c><v> cells, resolving shared strings when c[@t='s']
```

You do not need to commit this script — run it as a one-shot ad-hoc tool to extract the table content, then write the resulting Markdown rows into `docs/kis/MISSING_OFFICIAL_VALUES.md`. Record the exact sheet name(s) consumed and a representative cell-range coordinate (e.g., "sheet `주문체결내역` rows 12–46, column B = field name, column D = 의미, column F = type, column H = 모의 제약") in `patch.md` for reproducibility.

If `uploads/6.xlsx` is missing or unreadable, STOP and report in `patch.md`.

## 2. Sheets to extract

Identify and read these sheets (use the Korean names you find in workbook.xml):

1. **주문체결내역 sheet** (corresponds to catalog §4.7, `VTTS3035R` paper / `TTTS3035R` live). Extract the response sub-field table. This is the **primary** target.
2. **미체결내역 sheet** (corresponds to `TTTS3018R` live, paper-unsupported per §4.8). Extract the response sub-field table for catalog completeness. Mark every confirmed row with an explicit "모의 미지원" note.
3. **API 목록 sheet** (top-level endpoint inventory). Scan for any separate "주문상태" or "order status" row that was missed in §4.2. If found, add a new row to §4.2 with its endpoint / method / TR_ID and Confirmed: yes (cite the cell). If not found, record this null result in `recommendation.md` so KIS_2-check's "no separate endpoint" decision is reconfirmed by KIS_3 directly.

If a sheet is missing or has fewer rows than KIS_2's patch.md implied, report in `patch.md` under "Discrepancies".

## 3. Catalog updates to `docs/kis/MISSING_OFFICIAL_VALUES.md`

### 3.1 Add §4.7.1

Append after the current §4.7 closing paragraph (which currently ends with the `<TBD>` note about sub-fields):

```markdown
### 4.7.1 주문체결내역 (`VTTS3035R`) Response `output[]` sub-fields

본 표는 `uploads/6.xlsx` 의 **`<sheet name>`** sheet 에서 직접 추출한 응답 sub-field 정의이다. `Confirmed: yes` 행은 6.xlsx 셀 본문에 명시된 값에 한정한다. 모의 제약은 sheet 에 명시된 경우에만 별도 표기한다. 본 catalog 는 paper (`VTTS3035R`) 와 실전 (`TTTS3035R`) 공통 응답을 다루며, 모의 제약은 §4.7 의 request 측 제약과 함께 해석한다.

| Field | Type | 의미 | 모의 제약 | Confirmed |
| --- | --- | --- | --- | --- |
| `output[].<field_1>` | <type> | <의미> | <— or 제약> | yes |
| ... | ... | ... | ... | ... |

본 sub-field 표만으로 다음 기능이 가능 / 불가능한지 § <recommendation 위치> 에 정리한다.
```

Fill the table from extracted cells. If a particular sub-field's type or 모의 제약 cell is empty in 6.xlsx, leave that column as `—` (not `<TBD>`) — the row's `Confirmed` is still `yes` for the fields that 6.xlsx defines. Only mark `Confirmed: <TBD>` if the entire row is absent from 6.xlsx.

### 3.2 Add §4.7.2

```markdown
### 4.7.2 미체결내역 (`TTTS3018R`) Response `output[]` sub-fields (실전 only — 모의 미지원)

본 표는 `uploads/6.xlsx` 의 **`<sheet name>`** sheet 에서 추출한 미체결내역 응답 sub-field 정의이다. **§4.8 에 명시된 대로 모의투자에서 사용 불가하며, 본 저장소의 `KisBroker.get_open_orders()` 는 paper 환경에서 호출하지 않는다**. 실전 라이브 확장의 완전성을 위해 catalog 화만 한다.

| Field | Type | 의미 | Confirmed |
| --- | --- | --- | --- |
| `output[].<field_1>` | <type> | <의미> | yes |
| ... | ... | ... | ... |
```

(No "모의 제약" column since this endpoint is wholly paper-unsupported.)

### 3.3 Optional §4.2 row addition

Only if API 목록 sheet contains a separate "주문상태 조회" endpoint not already in §4.2: append a new row to §4.2's table with `Confirmed: yes`, citing the cell in `patch.md`. Otherwise, do not touch §4.2.

### 3.4 Sections that MUST NOT change

- §1 OAuth, §2 account (all subsections), §3 market data.
- §4.1 base URL.
- §4.2 (unless §3.3 above applies).
- §4.3 (헤더), §4.4 (place_order body), §4.5 (place_order response), §4.6 (정정취소 body), §4.7 (existing request query table and paragraph immediately before the new §4.7.1).
- §4.8 (paper-unsupported list).
- §4.9 (모의 제약 요약).
- §4.10 (안전 정책 재확인).
- "다음 작업 가이드", "보안" sections at the end.

## 4. `recommendation.md` contents

```markdown
# KIS_3 — Recommendation

## 1. catalog 갱신 요약

- §4.7.1: 주문체결내역 (`VTTS3035R`) Response `output[]` sub-fields 가 6.xlsx의 `<sheet>` sheet 에서 추출되어 `Confirmed: yes` 로 채워짐. 총 `<N>` 개 sub-field.
- §4.7.2: 미체결내역 (`TTTS3018R`) Response `output[]` sub-fields 가 catalog 화됨. 모의 미지원 명시.
- §4.2 (optional): 별도 주문상태 조회 endpoint 존재 여부 — <found / not found, 출처 cell>.

## 2. audit decision matrix 갱신

| 기능 | KIS_2-check 결과 | KIS_3 후 결과 | 사유 |
| --- | --- | --- | --- |
| `get_open_orders` | BLOCKED-BY-DOCS | <READY / PARTIALLY READY / BLOCKED> | 근거 |
| `get_fills` | PARTIALLY READY → 사실상 BLOCKED | <상태> | 근거 |
| `get_order_status` | BLOCKED-BY-DOCS | <상태> | 근거 |

## 3. 다음 작업

<one of:>
- 옵션 A: `api-orders-paper-003-query` (전체 3 기능). `next-job-request.md` 초안 작성.
- 옵션 B: `api-orders-paper-003-fills-only` (`get_fills` 만). `next-job-request.md` 초안 작성.
- 옵션 C: 여전히 BLOCKED. 추가 KIS 측 정책 변경 또는 catalog 확장 필요. `next-job-request.md` 작성 안 함.

선택 사유:

## 4. 차단점 (있다면)

```

## 5. `next-job-request.md` contents (conditional)

If at least one of the three methods is READY or PARTIALLY READY, write a complete `request.ko.md` draft inside a fenced `markdown` block (same pattern as `docs/ai/jobs/KIS_2-check/codex-task.md`):

````markdown
```markdown
# 작업 ID
api-orders-paper-003-query

# 작업명
KIS 모의투자 미체결 / 체결 / 주문상태 조회 구현

KIS_3 에서 `docs/kis/MISSING_OFFICIAL_VALUES.md` §4.7.1 (주문체결내역 sub-fields) 가 보강되었다. ...

## 목표

- `KisBroker.get_fills()` 본문을 catalog §4.7 + §4.7.1 의 `Confirmed: yes` 필드만 사용해 구현한다.
- `KisBroker.get_order_status(broker_order_id)` 는 ... (READY 인 경우만)
- `KisBroker.get_open_orders()` 는 ... (BLOCKED 라면 NotImplementedError 유지)

## 절대 하지 말 것

(전부 KIS_3 plan / 마스터 팩 §1 의 안전 규칙 그대로 인용)

## 완료 기준

...
```
````

The draft must:

- Cover ONLY the methods that became READY or PARTIALLY READY in `recommendation.md`.
- Explicitly preserve `NotImplementedError` for any method that remained BLOCKED.
- Mandate use of catalog §4.7 + §4.7.1 fields with `Confirmed: yes` only.
- Mandate paper constraints from §4.7 (PDNO="", CCLD_NCCS_DVSN="00", SLL_BUY_DVSN="00", SORT_SQN default, ODNO=""). Do not invent new constraint values.
- Mandate new `KisQueryTransport` Protocol (or equivalent) following the `KisAccountClient.UrllibAccountTransport` GET-only pattern from `app/broker/kis.py`, not the existing `KisOrderTransport` (which is POST-only).
- Forbid all live TR_IDs, all paper-unsupported TR_IDs, all Asia paper TR_IDs (the same forbidden lists from prior jobs).
- Forbid extending OMS protocol (this job is adapter-level only, mirroring api-orders-paper-002-cancel-replace's G2 selection A).
- Forbid GUI / status-surface changes (capabilities()["fills"] etc. stay False; status-surface advertise is a separate follow-up).
- End with the standard "patch.md must include" list per `docs/ai/CLAUDE_CODEX_WORKFLOW.md`.

## 6. Verification commands

Run from `projects/paper-trading`:

```bash
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

Both must PASS unchanged (this job adds no code or tests). Confirm the test count matches the pre-job baseline (458 from api-orders-paper-002-cancel-replace).

Also run safety greps and include in `patch.md`:

```bash
grep -rnE "^(from|import) (requests|httpx|aiohttp|urllib3|openpyxl|pandas)" docs/ai/jobs/KIS_3
grep -rn "Bearer eyJ\|access_token=eyJ\|appkey=eyJ" docs/ai/jobs/KIS_3 docs/kis/MISSING_OFFICIAL_VALUES.md || true
grep -rn "12345678\|fake-account\|fake-key" docs/ai/jobs/KIS_3 docs/kis/MISSING_OFFICIAL_VALUES.md || true
grep -rn "^Result: yes" docs/kis/MISSING_OFFICIAL_VALUES.md || true
# Confirm no app/tests changes:
git diff --name-only HEAD -- projects/paper-trading/app projects/paper-trading/tests
```

Expected:
- External / non-stdlib imports in KIS_3 artifacts: 0 lines.
- Bearer JWT / real secret literals: 0 lines.
- Fake credential literals leaking from prior plans: 0 lines outside grep-target self-references.
- `git diff` over `app/` and `tests/`: 0 lines.

## 7. `patch.md` contents

Create `projects/paper-trading/docs/ai/jobs/KIS_3/patch.md` with these sections in order:

1. **Files Changed** — list every modified/created file. Should be exactly: `docs/kis/MISSING_OFFICIAL_VALUES.md`, `docs/ai/jobs/KIS_3/recommendation.md`, conditionally `docs/ai/jobs/KIS_3/next-job-request.md`, `docs/ai/jobs/KIS_3/patch.md`. NO `app/` or `tests/` entries.
2. **6.xlsx extraction summary** —
   - sheet names consumed (Korean names from workbook.xml).
   - row / column coordinates for each sub-field table.
   - total row counts extracted vs left as `<TBD>`.
3. **§4.7.1 added rows** — count of new `Confirmed: yes` rows.
4. **§4.7.2 added rows** — count.
5. **§4.2 row addition** — yes/no + cell coordinate if yes.
6. **audit decision matrix** — copy from recommendation.md.
7. **next-job-request.md decision** — created or skipped, with reason.
8. **Safety confirmation** —
   - no `app/` or `tests/` files changed (cite `git diff --name-only HEAD`).
   - no `.env` / `.env.example` / GUI files changed.
   - no third-party dependency added.
   - no real secret / app key / account number / token / Bearer literal added.
   - §1 / §2 / §3 / §4.1–§4.10 (except the additive subsections) byte-for-byte unchanged.
9. **Safety grep output** — verbatim output for each grep in §6.
10. **Test Results** — compileall + pytest summary (must match pre-job baseline since no code/test changed).
11. **Claude verification prompt** — paste this exact text:

    > Read `docs/ai/jobs/KIS_3/plan.md`, `recommendation.md`, `next-job-request.md` (if present), and `patch.md`. Run `git diff` and `git diff --name-only HEAD`. Verify: (a) only catalog + KIS_3 docs were modified; no `app/` / `tests/` / `.env` / GUI / `pyproject.toml` / `README.md` changes; (b) every `Confirmed: yes` row added to §4.7.1 / §4.7.2 cites a 6.xlsx cell in `patch.md`; (c) §4.7.2 explicitly marks paper-unsupported; (d) §1 / §2 / §3 / §4.1–§4.10 outside the new subsections are unchanged byte-for-byte; (e) no third-party dependency was added; (f) no real app key / app secret / account number / Bearer token / access token appears in any file; (g) audit decision matrix in `recommendation.md` matches the actual sub-field coverage; (h) `next-job-request.md` (if present) only covers methods classified as READY or PARTIALLY READY, and forbids implementation of BLOCKED methods; (i) the optional §4.2 row addition (if any) is faithfully cited from 6.xlsx; (j) pytest count matches the pre-job baseline. Output verdict `APPROVE`, `REQUEST CHANGES`, or `BLOCK`.

12. **Follow-up Codex prompt rules** (only if Claude returns REQUEST CHANGES or BLOCK):

    - Quote findings verbatim under `## Findings`.
    - For each finding, write `## Required change` stating the exact catalog edit, why it is in scope of KIS_3, and the safety rule preserved.
    - Re-state absolute prohibitions and verification commands.
    - Do not expand scope: any change to `app/`, `tests/`, `.env`, GUI, or non-§4.7 catalog sections requires human approval.
    - End with: "Update `patch.md` (do not create a new one). Append a `## Follow-up <N>` section explaining what changed and re-run verification. Do not commit / push / merge."

13. **Status footer**: `READY FOR REVIEW`.

Stop. Do not commit, push, merge, deploy, or modify `.env`. Hand off to the human, who will run `git diff` and invoke Claude review.
