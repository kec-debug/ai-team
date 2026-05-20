# KIS_3 — Claude Review

## Verdict

APPROVE

## Summary

KIS_3 closes the catalog gap C1 identified by KIS_2-check audit. `uploads/6.xlsx` 의 **`해외주식 주문체결내역`** sheet 에서 32 개 sub-field 가, **`해외주식 미체결내역`** sheet 에서 29 개 sub-field 가 `Confirmed: yes` 로 추가됐다. 세 query method (`get_open_orders` / `get_fills` / `get_order_status`) 모두 BLOCKED → **PARTIALLY READY** 로 재분류 가능. `api-orders-paper-003-query` 의 request.ko.md 초안이 `next-job-request.md` 에 작성됐다. 코드 / 테스트 / `.env` / GUI 무변동. pytest 458 passed (pre-job baseline 그대로).

## Scope of changes

In-scope, intentional:

- `docs/kis/MISSING_OFFICIAL_VALUES.md` (+77 lines) — §4.7 끝에 §4.7.1 / §4.7.2 두 신규 subsection 추가. 기존 §1 / §2 / §3 / §4.1–§4.6 / §4.7 본문 (request query table 포함) / §4.8 / §4.9 / §4.10 byte-for-byte 무변동 (diff stat 확인).
- `projects/paper-trading/docs/ai/jobs/KIS_3/recommendation.md` (NEW) — 갱신된 audit decision matrix.
- `projects/paper-trading/docs/ai/jobs/KIS_3/next-job-request.md` (NEW) — `api-orders-paper-003-query` request.ko.md 초안. fenced markdown 블록.
- `projects/paper-trading/docs/ai/jobs/KIS_3/patch.md` (NEW).

Out-of-scope, pre-existing dirty (NOT from KIS_3 — all from prior jobs that haven't been committed):

- `projects/paper-trading/app/api/server.py` / `scripts/_common.sh` / `scripts/start_server.sh` / `docs/ai/jobs/mvp-002/request.ko.md` — conversation-start residue.
- `projects/paper-trading/app/broker/kis.py` / `tests/test_broker_interface.py` / `tests/test_kis_http_boundaries.py` — from api-orders-paper-002-cancel-replace (already reviewed APPROVE).
- New untracked dirs: `docs/ai/jobs/KIS_2-check/`, `docs/ai/jobs/api-orders-paper-002-cancel-replace/`, `docs/ai/jobs/paper-e2e-001/`, `tests/test_kis_paper_order_cancel_replace.py` — prior jobs' uncommitted output.

KIS_3 의 `git diff --name-only HEAD` 에서 `app/` 와 `tests/` 영역의 modify 는 모두 본 job 이전에 발생한 변경. Codex 가 patch.md §3 에서 이를 정직하게 보고했고 revert 시도하지 않은 것은 정확한 처리.

## Catalog 검증 (catalog §4.7.1 / §4.7.2)

### §4.7.1 (`VTTS3035R` Response `output[]` sub-fields, 32 rows)

paper-supported 주문체결내역 응답 필드. 모든 행 `Confirmed: yes`. KIS 의 snake_case 한국어 약어 (`odno`, `pdno`, `ft_ord_qty`, `ft_ccld_qty`, `nccs_qty`, `prcs_stat_name`, `ovrs_excg_cd`, `tr_crcy_cd` 등) 와 type 길이 (string(8), string(10), string(60) 등) 가 §4.7 의 request 측 필드 명명 규칙 및 §2.5 의 잔고 응답 필드 (`ovrs_pdno`, `ovrs_cblc_qty`) 와 일관된다. 구체 적으로 확인된 핵심 매핑 후보:

| KisBroker 매핑 목적 | catalog §4.7.1 field | 확인 |
| --- | --- | --- |
| broker_order_id | `odno` (string 10) | yes |
| 원주문 추적 (replace) | `orgn_odno` (string 10) | yes |
| symbol | `pdno` (string 12) | yes |
| side (BUY/SELL) | `sll_buy_dvsn_cd` (`01`=매도, `02`=매수) | yes |
| 주문수량 | `ft_ord_qty` (string 10) | yes |
| 체결수량 | `ft_ccld_qty` (string 10) | yes |
| 미체결수량 (open-order client filter) | `nccs_qty` (string 10) | yes |
| 주문가격 | `ft_ord_unpr3` (string 26) | yes |
| 체결가격 | `ft_ccld_unpr3` (string 26) | yes |
| 체결금액 | `ft_ccld_amt3` (string 23) | yes |
| 통화 | `tr_crcy_cd` (string 60) | yes |
| 거래소 | `ovrs_excg_cd` (string 4) | yes |
| 처리상태 (filled / 거부 / 전송) | `prcs_stat_name` (string 60) | yes |
| 거부사유 | `rjct_rson`, `rjct_rson_name` | yes |
| 주문시각 | `ord_tmd` (string 6) | yes |

따라서 fill projection / open-order client filter / order-status lookup 의 모든 핵심 필드가 paper 응답에서 사용 가능. recommendation.md 의 PARTIALLY READY 분류가 catalog 사실과 정합.

§4.7.1 본문 마지막 단락이 "단, 모의 request 제약상 `CCLD_NCCS_DVSN="00"` 전체 조회만 가능하고 `ODNO` 단건 검색은 불가하므로, paper 구현은 전체 조회 후 client-side filtering 이 필요하다." 라고 명시 — paper-only constraint 와 sub-field 가용성을 동시에 정확히 정리.

### §4.7.2 (`TTTS3018R` Response `output[]` sub-fields, 29 rows)

미체결내역 응답 필드 (실전 only). §4.8 의 "모의투자 미지원" 상태 보존을 위해 본문 첫 줄에 "**§4.8 에 명시된 대로 모의투자에서 사용 불가하며, 본 저장소의 `KisBroker.get_open_orders()` 는 paper 환경에서 이 endpoint 를 호출하지 않는다**" 명시. 모의 미지원 정책이 catalog 차원에서 한 번 더 강화됨. 향후 라이브 확장 시점에 참조 가능.

### §4.2 / 별도 주문상태 endpoint

recommendation.md §1 마지막 줄: "별도 `주문상태 조회` endpoint 는 `API 목록` sheet rows 1-19 에서 발견되지 않았다... §4.2 는 변경하지 않았다." KIS_2-check 가 "no separate endpoint" 로 잠정 결론 내린 것을 KIS_3 가 6.xlsx API 목록 sheet 를 직접 재확인해 정식 확정. ✓

### Catalog 무변동 영역 확인

`git diff HEAD -- docs/kis/MISSING_OFFICIAL_VALUES.md` 의 시작 hunk 가 §4.7 의 closing paragraph (`...추가 catalog 화한다. (<TBD>)`) **다음 줄에서 시작**하고, 끝 hunk 가 §4.8 시작 직전에서 끝나므로, §1 / §2 / §3 / §4.1–§4.6 / §4.7 본문 / §4.8 / §4.9 / §4.10 / 다음 작업 가이드 / 보안 섹션 모두 무변동. ✓

## Recommendation / next-job 검증

`recommendation.md` 의 audit decision matrix:

| 기능 | KIS_3 후 상태 | 근거 일치 여부 |
| --- | --- | --- |
| `get_open_orders` | PARTIALLY READY | `inquire-nccs` paper 미지원 + `inquire-ccnl` 전체조회 + `nccs_qty>0` client filter — 정확. |
| `get_fills` | PARTIALLY READY | `inquire-ccnl` 전체조회 + `ft_ccld_qty>0` projection + sanitized rows — 정확. recommendation.md 가 "별도 체결번호 / 명확한 체결시각 필드 미확인" 으로 약간 conservative 한데, `odno` + `ord_tmd` 조합으로 fill 식별/시각 매핑이 사실상 가능하므로 PARTIALLY READY 분류는 안전 편 (Minor 관찰 — F1). |
| `get_order_status` | PARTIALLY READY | paper ODNO 검색 불가 + 전체조회 후 client lookup + 조회 범위 밖 fail-closed — 정확. |

`next-job-request.md` 의 초안 (1-112 줄) 검증:

- 사용 가능 catalog 행 (§4.7 / §4.7.1) 정확히 인용 — line 32-36.
- 사용 금지 항목 (line 38-44, 46-67): `/inquire-nccs`, live TR_IDs, paper-unsupported TR_IDs, Asia paper TR_ID 추측, §4.7.1 에 없는 field 추측, external HTTP libs, OMS protocol 확장, GUI / capabilities surface 변경, OrderType.MARKET 가드 우회, `.env` / secret 노출, auto git ops 등 모두 명시. ✓
- 구현 지침 (line 69-84): GET 전용 `KisQueryTransport` 신규 (기존 POST `KisOrderTransport` 재사용 금지), `KisAccountTransport` 패턴 재사용, host/path/method/TR_ID allowlist 엄격, paper 제약 7 개 정확 인용, pagination + 페이지 cap, 항상 `sanitize_kis_response`, missing rt_cd / malformed output / kis_error short tag fail-closed, 조회 범위 밖 fail-closed. ✓
- 완료 기준 (line 86-99): test coverage 항목 (transport allowlists / paper constraints / pagination cap / malformed / KIS errors / sanitization / secret-safe repr / Strategy-Agent isolation) 모두 prior job 패턴과 정합. ✓
- patch.md 요구 사항 (line 101-111) 표준 워크플로 그대로. ✓

한 가지 Minor: line 78 "exchange only: paper-supported US set (`NASD`, `NYSE`, `AMEX`) or catalog-confirmed `%` if explicitly chosen in plan" — `%` (전체) 가 paper 에서 동작하는지는 §4.7 의 "모의는 §4.4 의 거래소 제약 따름" 으로 인해 불확실. 다음 plan 단계에서 fail-closed 원칙으로 결정하면 됨 (Minor 관찰 — F2).

## Safety regression

| 항목 | 결과 |
| --- | --- |
| `app/` 무변동 (KIS_3 한정) | OK — git diff 의 app 변경은 prior jobs' 잔여 dirty |
| `tests/` 무변동 (KIS_3 한정) | OK — 동일 |
| pytest 458 passed (pre-job baseline 그대로) | OK |
| `.env` / `.env.example` / `pyproject.toml` / `README.md` / GUI 무변동 | OK |
| 외부 의존성 추가 없음 | OK — `grep -rnE "(openpyxl\|pandas\|requests\|httpx\|aiohttp\|urllib3)" docs/ai/jobs/KIS_3/` → 0 lines |
| 실 secret / 계좌번호 / token / Bearer leak 없음 | OK — `grep -nE "Bearer eyJ\|access_token=eyJ\|appkey=PS[A-Z]\|appsecret=PS[A-Z]" docs/kis/MISSING_OFFICIAL_VALUES.md` → 0 lines |
| §1 / §2 / §3 / §4.1–§4.6 / §4.7 본문 / §4.8 / §4.9 / §4.10 / "다음 작업 가이드" / "보안" 무변동 | OK |
| `<TBD>` 행이 추측으로 `Confirmed: yes` 된 항목 없음 | OK — 모든 신규 yes 행이 6.xlsx 의 두 sheet 에서 인용 가능 |
| paper-unsupported (`TTTS3018R`) 가 §4.7.2 에서 "모의 미지원" 으로 명시 | OK |
| `next-job-request.md` 가 BLOCKED 기능 포함 안 함 | OK (세 기능 모두 PARTIALLY READY 이므로 모두 다음 작업 대상) |
| 별도 주문상태 endpoint 부재 재확인 | OK — recommendation.md §1 |
| commit / push / merge / deploy 수행 없음 | OK |

## Findings (severity 순)

### F1 (MINOR / Observation) — `get_fills` PARTIALLY READY 가 다소 보수적

recommendation.md §2 의 `get_fills` 행은 "별도 체결번호와 명확한 체결시각 필드는 확인되지 않아 구현은 주문번호 기반 fill projection 또는 sanitized broker rows 로 제한해야 한다" 라고 명시했다. 하지만 §4.7.1 에 `odno` + `ord_tmd` 가 모두 confirmed 되어 있어, 주문번호 기반 식별 + 주문시각 기반 시각 매핑이 가능하다. KIS 자체가 별도 "체결번호" 와 "체결시각" 필드를 paper 응답에 분리해 두지 않은 것은 catalog 의 사실이며, 본 job 의 책임이 아니다. 따라서 분류 자체는 정확하지만, 다음 plan 이 fill projection 시 `(odno, ord_tmd)` 페어를 사용한다는 점을 명시해 주면 명확해진다. **본 audit 의 결정에는 영향 없음.**

### F2 (MINOR / Observation) — `%` 거래소 코드의 paper 허용 여부 미결정

`next-job-request.md` line 78 가 transport allowlist 에 "exchange only: paper-supported US set (`NASD`, `NYSE`, `AMEX`) or catalog-confirmed `%` if explicitly chosen in plan" 이라고 적었다. catalog §4.7 의 paper 제약 ("모의는 §4.4 의 거래소 제약 따름") 은 `%` 가 paper 에서 동작하는지 명확히 하지 않는다. 다음 plan 단계에서 둘 중 하나로 결정 필요:

- (a) `%` 도 paper allowlist 에 포함 (catalog 가 명시적으로 금지하지 않음).
- (b) 안전 편 fail-closed: `%` 차단, US 거래소만 허용 (보수적; 본 review 권고).

**본 audit 의 결정에는 영향 없음** — `next-job-request.md` 의 "if explicitly chosen in plan" 표현이 결정을 다음 plan 으로 위임하므로 무방.

### F3 (INFO) — §4.7 의 trailing `<TBD>` 단락 미갱신

§4.7 의 마지막 단락 ("본 catalog 는 array 의 sub-field full list 를 보유하지 않으며, 매핑 단계의 별 job 에서 6.xlsx 주문체결내역 sheet 의 sub-field 표를 추가 catalog 화한다. (`<TBD>`)") 이 그대로 남아 있다. 바로 다음 §4.7.1 이 그 gap 을 채웠으므로 텍스트가 이제 시간순으로 약간 어색하다. 두 가지 처리 가능:

- 위 단락을 "본 catalog 의 array sub-field 표는 §4.7.1 (paper-supported) / §4.7.2 (실전 only, 모의 미지원) 에서 확인할 수 있다." 로 한 줄 갱신.
- 또는 그대로 두기 — catalog 의 historical 기록으로 해석 가능.

본 review 의 결정에는 영향 없음. 한 줄 갱신은 다음 catalog 보강 job 또는 follow-up 에서 처리 가능. patch.md 가 §4.7.1 / §4.7.2 의 존재로 사실상 해당 단락을 무력화한다는 점을 충분히 보여주므로, 본 turn 에서는 변경 요청하지 않는다.

## Final Checklist

| 항목 | 결과 |
| --- | --- |
| docs-only 작업 (코드 / 테스트 / `.env` / GUI 무변동) | OK |
| §4.7.1 32 rows, 모든 행 6.xlsx 셀 인용 가능 | OK |
| §4.7.2 29 rows, 모의 미지원 명시 | OK |
| 별도 주문상태 endpoint 부재 재확인 (§4.2 무변동) | OK |
| 추측으로 채운 `Confirmed: yes` 없음 | OK |
| 외부 의존성 추가 없음 (`openpyxl` / `pandas` / `requests` 등) | OK |
| 실 secret / 계좌번호 / token / Bearer leak 없음 | OK |
| §1 / §2 / §3 / §4.1–§4.6 / §4.7 본문 / §4.8 / §4.9 / §4.10 byte-for-byte 무변동 | OK |
| recommendation.md 의 PARTIALLY READY 분류가 catalog 사실과 정합 | OK |
| `next-job-request.md` 가 BLOCKED 기능 포함 없이 작성 (세 기능 모두 PARTIALLY READY) | OK |
| `next-job-request.md` 가 paper 제약 / 새 query transport / OMS 미확장 / GUI 미변경 / capabilities 보존 모두 명시 | OK |
| pytest 458 passed (pre-job baseline 동일) | OK |
| compileall PASS | OK (patch.md 보고) |
| commit / push / merge / deploy 수행 없음 | OK |

## Follow-up Codex prompt

없음. APPROVE.

다음 단계는 사람이 직접:

1. `git diff` 와 `git status` 로 본 job 의 변경 범위 확인 (catalog +77 줄 + 새 KIS_3 디렉터리 5 파일).
2. `git add docs/kis/MISSING_OFFICIAL_VALUES.md docs/ai/jobs/KIS_3/` 후 manual commit.
3. 다음 job 진행 의사가 있다면, `docs/ai/jobs/KIS_3/next-job-request.md` 의 fenced markdown 블록을 `docs/ai/jobs/api-orders-paper-003-query/request.ko.md` 로 옮기고 GUI 한국어 작업 요청 칸에 입력해 Claude 의 plan + codex-task 단계로 진행.

본 review 는 commit / push / merge / deploy 를 수행하지 않는다. F1 / F2 / F3 는 다음 plan 단계에서 자연스럽게 해소되거나 catalog 의 historical 기록으로 남길 수 있다 — 본 turn 에서 follow-up Codex 작업을 강제할 사유 아님.
