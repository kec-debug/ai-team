# roadmap-implementation-plan — 남은 paper trading 작업 통합 설계

본 문서는 **docs-only 설계 / 진단** 결과다. 코드 / catalog / `.env` / GUI 변경 없음.

## 1. 요청 요약

지난 mvp-001 ~ mvp-022 + api-* / paper-* / runtime-* / KIS_* 시리즈를 거치며 `projects/paper-trading` 의 핵심 기반은 land 되었으나, 작업이 잘게 쪼개진 결과 (a) 완료/미완료 경계가 흐려졌고 (b) 같은 기능을 재설계하려는 충동이 반복되며 (c) 다음 단계 선택이 즉흥적이다. 본 작업은 코드 구현 없이 **현재 상태 ground truth 확정 + 남은 7 개 작업 분류 + 의존관계 / 묶음 / 순서 / 다음 단일 작업 추천** 만 수행한다.

## 2. Ground truth: 무엇이 실제로 land 됐는가

### 2.1 commit 으로 land 된 항목 (`git log` 검증)

`projects/paper-trading/` 에 land 된 커밋 (최신순):

```text
39395b2 catalog KIS order query official values        ← KIS_3 catalog (committed before this turn? actually still dirty — see §2.2)
96ac7f3 add paper trading e2e pipeline tests           ← paper-e2e-001 test file
14aa232 implement KIS paper order submission           ← api-orders-paper-001
b9ffe8f implement KIS paper account read models        ← api-account-001
13ee52c catalog KIS account and order official values  ← KIS_2
cc6f2cc implement KIS market data quote mapping        ← api-market-data-001 / mvp-023 unblocked
22a3849 wire paper runtime submit intents              ← runtime-002 (PaperEngine.submit_intents)
a549454 expose paper trading account dashboard         ← dashboard a/c/positions/fills/engine status
522d31e add internal paper trading engine              ← paper-001 PaperEngine + PaperAccount + PaperJournal
08987c7 paper-001: internal paper trading MVP
df5fe7f paper-trading: land mvp-014..api-auth-001 KIS + Quote scaffolding (242 PASS)
```

(commit `39395b2 catalog KIS order query official values` 는 KIS_2 의 §4 catalog 확장이지 KIS_3 가 아님. KIS_3 patch 는 **uncommitted dirty** — §2.2 참고.)

### 2.2 dirty (review APPROVE 완료, 아직 사용자 commit 대기)

| 작업 | review 결과 | 상태 |
| --- | --- | --- |
| `api-orders-paper-002-cancel-replace` | APPROVE | code (`app/broker/kis.py`) + new test + 2 narrow test edits + docs dir 모두 working tree 에. |
| `paper-e2e-001` 의 `docs/ai/jobs/paper-e2e-001/` 하위 5 파일 | APPROVE | test 파일 (`tests/test_paper_e2e_pipeline.py`) 은 이미 commit `96ac7f3` 으로 land 됨. 문서 디렉터리만 untracked. |
| `KIS_2-check` (audit) | APPROVE | 새 디렉터리 (`docs/ai/jobs/KIS_2-check/`) 5 파일 untracked. |
| `KIS_3` (catalog) | APPROVE | `docs/kis/MISSING_OFFICIAL_VALUES.md` +77 줄 modify + 새 디렉터리 (`docs/ai/jobs/KIS_3/`) 5 파일 untracked. |

추가로 conversation-start residue (이번 시리즈 외):

- `app/api/server.py`, `scripts/_common.sh`, `scripts/start_server.sh`, `docs/ai/jobs/mvp-002/request.ko.md` — 본 시리즈 작업 전부터 dirty. 본 master plan 범위 외.
- 새 untracked 디렉터리 `docs/ai/AI_TEAM_BRIEFING.md`, `docs/ai/AI_TEAM_REQUEST_GENERATOR_BRIEF.md`, `docs/ai/jobs/paper-ux-001/` — 본 master plan 범위 외 (사용자 검토 대상).

### 2.3 사용자가 요청한 "완료된 작업 15 개" 항목별 검증

| 항목 | 상태 | 출처 |
| --- | --- | --- |
| paper-trading 기본 구조 | DONE (committed) | mvp-005, paper-001 (commit `08987c7` / `522d31e`) |
| dashboard UI | DONE (committed) | mvp-021 + `a549454 expose paper trading account dashboard` |
| KIS 설정 로딩 | DONE (committed) | mvp-006-1, mvp-022 |
| KIS OAuth | DONE (committed) | api-auth-001 (commit `df5fe7f` 안에 포함) |
| KIS 시세 Quote 매핑 | DONE (committed) | api-market-data-001 / mvp-023 (commit `cc6f2cc`) |
| KIS 계좌 / 잔고 / 포지션 조회 | DONE (committed) | api-account-001 (commit `b9ffe8f`) |
| KIS 모의 주문 `place_order` | DONE (committed) | api-orders-paper-001 (commit `14aa232`) |
| KIS 모의 주문 `cancel_order` / `replace_order` | DONE-DIRTY | api-orders-paper-002-cancel-replace APPROVE, **사용자 commit 대기** |
| 내부 `PaperEngine` | DONE (committed) | paper-001 (commit `522d31e`) |
| `PaperAccount` | DONE (committed) | paper-001 (commit `522d31e`) |
| `PaperJournal` | DONE (committed) | paper-001 (commit `522d31e`) |
| `Fill` 모델 | DONE (committed) | paper-001 (commit `522d31e`) |
| 통화별 cash / PnL | DONE (committed) | paper-001 |
| e2e 테스트 | DONE (committed) | paper-e2e-001 test 파일 (commit `96ac7f3`). 단 doc 디렉터리만 untracked. |
| dashboard 에 cash / PnL / fill / journal 노출 | DONE (committed) | `a549454` + `paper-001` 후속 |

**15/15 모두 DONE.** 단 항목 8 (cancel/replace) 은 review APPROVE 후 commit 대기. 항목 14 의 doc dir 도 untracked.

### 2.4 ROADMAP_STATUS.md 의 stale 정도

`docs/ai/ROADMAP_STATUS.md` 의 "마지막 갱신: 2026-05-15" 이후 11+ 커밋이 land 됨. 본 문서는 다음 항목이 모두 stale:

- mvp-023 `BLOCKED-BY-DOCS` → 실제로 `cc6f2cc implement KIS market data quote mapping` 으로 **unblocked + land**.
- mvp-024 ~ mvp-029 "⏸️ 미시작" → 사실상 api-* / paper-* / runtime-* / KIS_2 / KIS_3 시리즈가 mvp-024 ~ mvp-026 영역을 흡수했음. 본 master plan §3 의 새 분류로 갈음.
- pytest 누적 결과 "214 passed" → 실제 현재 458 passed.
- "📜 새 mvp 번호 생성 금지 원칙" 절은 그대로 유효.
- "BLOCKED 상세" 의 mvp-023 항 전체가 outdated.

**ROADMAP_STATUS.md 갱신 제안** (본 plan 은 직접 수정하지 않음 — §10 참고):

1. mvp-023 → "✅ 완료 (api-market-data-001 / cc6f2cc)" 로 변경. BLOCKED 절 제거.
2. mvp-024 ~ mvp-029 행 전체를 본 master plan §4 의 새 분류 (`api-orders-paper-003-query`, `paper-002`, `strategy-002`, `runtime-soak-001`, `live-validation-001`) 로 대체. 이전 mvp 번호는 historical record 로 별도 절에 보존.
3. "Phase 0 누적 결과 pytest 214 passed" → 현재 458 passed 갱신.
4. "Next single action" 을 본 plan §8 의 권고로 갱신.
5. "새 mvp 번호 생성 금지 원칙" 유지. 본 master plan 이 그 원칙의 연장선.

## 3. 남은 7 개 작업 분류

본 분류는 KIS_2-check / KIS_3 / paper-e2e-001 review APPROVE 결과를 모두 반영한 최신 ground truth 다.

| Job ID | 상태 | 사유 |
| --- | --- | --- |
| `KIS_3` | **DONE-DIRTY** | `docs/kis/MISSING_OFFICIAL_VALUES.md` §4.7.1 (32 rows) + §4.7.2 (29 rows) 추가됨. review APPROVE. 사용자 commit 대기. 본 plan 의 "남은 7 개" 라는 사용자 가정 자체가 stale — 본 job 은 더 이상 미완료가 아님. |
| `api-orders-paper-003-query` | **READY** | KIS_3 의 §4.7.1 으로 `get_open_orders` / `get_fills` / `get_order_status` 모두 PARTIALLY READY 가 됨. `docs/ai/jobs/KIS_3/next-job-request.md` 에 request.ko.md 초안이 이미 작성됐고 sound. 본 master plan 의 §8 첫 번째 Codex 추천 대상. |
| `runtime-002` | **DONE (committed)** | `22a3849 wire paper runtime submit intents` 로 land 됨. `PaperEngine.submit_intents` 가 존재 (`app/runtime/paper_engine.py:72`), `PaperRunner` 가 `paper_engine` 인자 시 위임 (`paper_runner.py:42-43`), paper-e2e-001 의 `test_e2e_happy_path_strategy_to_fill_through_oms_paper_engine` 으로 회귀 잠금. 사용자의 master pack 에 적힌 "submit_intents 가 없다" 는 stale premise. **재실행 금지**. |
| `paper-002` | **READY** | partial fill 시퀀스 / 슬리피지 / market impact. catalog 의존성 없음. `PaperBroker.tick` / `PaperEngine.on_quote` 기반 시뮬레이션 강화. 다른 모든 남은 작업과 독립. |
| `strategy-002` | **READY** | Opening Range Breakout. 기존 `PremarketGapVolumeBreakout` 패턴 재사용. catalog 의존성 없음. broker / KIS 의존성 없음. 다른 모든 남은 작업과 독립. |
| `runtime-soak-001` | **READY (after value)** | 코드 측면에서는 즉시 가능. 단, 의미 있는 soak run 을 위해서는 paper-002 의 fill realism + strategy-002 의 두 번째 전략 후에 진행하는 것이 검증 가치가 높음. catalog 의존성 없음. |
| `live-validation-001` | **HELD-BY-PROCESS** | 코드 가능성과 별개로 "충분한 paper soak 검증 데이터" 라는 process gate. runtime-soak-001 의 결과가 의미 있는 통계 (승률 / 손익비 / 슬리피지 / 오류율) 를 모은 후에만 진행. 본 시리즈에서는 **착수 금지** (`docs/ai/MASTER_TRADING_ROADMAP.md` §1 의 안전 원칙). |

요약:

- DONE-DIRTY: `KIS_3`, `api-orders-paper-002-cancel-replace` (사용자가 master pack 에 안 적었지만 actually pending commit)
- DONE-COMMITTED: `runtime-002` (master pack 의 stale premise 정정)
- READY 즉시 가능: `api-orders-paper-003-query`, `paper-002`, `strategy-002`
- READY 가치 시점 조정: `runtime-soak-001` (paper-002 + strategy-002 후 권고)
- HELD: `live-validation-001`

BLOCKED-BY-DOCS 는 0 건. KIS_3 이후 모든 남은 catalog 의존 작업은 unblock 되었음.

## 4. 의존관계

```
api-orders-paper-003-query
    ├─ requires: KIS_3 catalog (DONE-DIRTY; commit 권고)
    └─ depends only on: §4.7 + §4.7.1 의 confirmed 필드. paper-002 / strategy-002 / runtime-soak-001 와 무관.

paper-002
    ├─ requires: PaperBroker / PaperEngine (DONE-committed)
    └─ depends only on: app/broker/paper.py + app/runtime/paper_engine.py. catalog 무관.

strategy-002
    ├─ requires: Strategy / RiskEngine / OMS (DONE-committed)
    └─ depends only on: app/strategy/*. catalog 무관. broker 무관 (Strategy 는 broker import 금지 원칙).

runtime-soak-001
    ├─ requires: DryRunController (DONE-committed)
    └─ benefits from: paper-002 + strategy-002 (의미 있는 soak data 를 만들기 위해).

live-validation-001
    ├─ requires: runtime-soak-001 의 누적 결과 + 명시적 사용자 승인.
    └─ HELD until 충분한 paper soak data + 사용자 승인.
```

핵심:

- `api-orders-paper-003-query` ↔ `paper-002` ↔ `strategy-002` 는 **상호 독립**. 어느 순서든 가능.
- `runtime-soak-001` 은 위 셋 중 최소 paper-002 + strategy-002 가 land 된 뒤가 가치 높음.
- `live-validation-001` 은 process gate 가 풀릴 때까지 보류.

## 5. 묶음 가능성

본 시리즈가 좁은-scope 1-fn / 1-class 패턴으로 일관되게 review APPROVE 받아왔다는 점을 고려할 때, **하나의 Codex job 이 1000 LoC + 다섯 파일 미만으로 끝나는 묶음**만 권장한다.

### Bundle 후보

| Bundle | 포함 | 예상 규모 | 권고 |
| --- | --- | --- | --- |
| **A — commit dirty** | `KIS_2-check` doc dir + `api-orders-paper-002-cancel-replace` 전부 + `KIS_3` 전부 + `paper-e2e-001` doc dir | 수동 git add/commit (사람 작업, Codex 0) | **강력 권고**. 다음 Codex job 진입 전에 4 개 PR 분리 또는 1 개 통합 commit. |
| **B — KIS query (single)** | `api-orders-paper-003-query` 만 | ~500 LoC + ~40 tests. `app/broker/kis.py` 의 query transport + 3 메서드 + 신규 test 파일. | **READY**. Bundle A 직후 권고. KIS_3 의 `next-job-request.md` 가 seed. |
| **C — paper realism (single)** | `paper-002` 만 | ~300 LoC + tests. `app/broker/paper.py` + 신규 config field + 신규 test. | READY 즉시. Bundle B 와 무관해 병렬 또는 직후 가능. |
| **D — strategy expansion (single)** | `strategy-002` 만 | ~200 LoC + tests. `app/strategy/opening_range_breakout.py` 신규. | READY 즉시. Bundle B / C 와 무관. |
| **E — soak loop (single)** | `runtime-soak-001` 만 | ~400 LoC + tests. `app/runtime/soak.py` 신규 + dashboard read-only 노출. | READY 즉시이지만 Bundle C / D 직후 권고. |
| **F — live validation prep (HELD)** | `live-validation-001` 만 | ~500 LoC + tests + 다중 가드. | **현 시점 진입 금지**. Bundle E 결과 후 명시적 사용자 승인 시 진입. |

### 묶지 말 것 (왜)

- B 와 C / D 를 하나의 Codex job 으로 묶지 말 것: 서로 다른 파일군 (broker/kis.py vs broker/paper.py vs strategy/*) 을 동시에 건드리면 review 가 어려워지고, 안전 grep / 좁은 변경 원칙이 깨진다. 본 시리즈가 1-domain-per-job 으로 모두 APPROVE 받았음.
- E 를 C / D 와 묶지 말 것: soak runner 는 DryRunController 와의 통합이 핵심이고, paper-002 / strategy-002 의 변경 위에서 동작을 검증해야 의미가 있다.
- F 는 어떤 묶음에도 끼우지 말 것: live trading 활성화 가드의 검토는 별도 job 으로 분리해 사람 검토 시간을 길게 가져야 한다.

## 6. 구현 순서 (Phase)

```text
Phase 0: COMMIT DIRTY
- 목표: 4 개 APPROVED 자료를 working tree → repo 로 옮긴다.
- 포함 작업: api-orders-paper-002-cancel-replace, KIS_2-check, KIS_3, paper-e2e-001 doc dir.
- Codex job ID: (없음. 사람이 git add/commit.)
- 예상 수정 파일: working tree 의 dirty 7 + 신규 dirs.
- 테스트 기준: pytest 458 passed (현재 베이스라인 유지).
- 완료 후 다음 단계: Phase 1.

Phase 1: KIS QUERY (api-orders-paper-003-query)
- 목표: KIS 모의투자 미체결 / 체결 / 주문상태 조회를 catalog §4.7 + §4.7.1 의 confirmed 필드로 adapter-level 부분 구현.
- 포함 작업: api-orders-paper-003-query.
- Codex job ID: api-orders-paper-003-query.
- 예상 수정 파일: app/broker/kis.py (KisQueryTransport / UrllibQueryTransport / MockQueryTransport + get_open_orders / get_fills / get_order_status 본문), tests/test_kis_paper_order_query.py (NEW), tests/test_broker_interface.py (narrow), tests/test_kis_http_boundaries.py (narrow), docs/ai/jobs/api-orders-paper-003-query/patch.md.
- 테스트 기준: 458 + ~40 new tests = ~500 passed. compileall PASS. 안전 grep clean.
- 완료 후 다음 단계: Phase 2.

Phase 2: PAPER REALISM (paper-002)
- 목표: PaperBroker.tick 의 fill 시뮬레이션을 partial fill 시퀀스 / 슬리피지 / market impact / spread-aware 체결가로 강화.
- 포함 작업: paper-002.
- Codex job ID: paper-002.
- 예상 수정 파일: app/broker/paper.py, app/config.py (새 settings — 단 plan 단계에서 명시 결정), tests/test_paper_broker.py (확장), tests/test_paper_engine.py (관련 부분).
- 테스트 기준: 회귀 0 + 신규 partial fill / slippage / impact / spread 테스트.
- 완료 후 다음 단계: Phase 3 또는 Phase 4 (병렬 가능).

Phase 3: STRATEGY EXPANSION (strategy-002)
- 목표: Opening Range Breakout 전략 추가. paper-002 의 강화된 fill 모델 위에서 동작.
- 포함 작업: strategy-002.
- Codex job ID: strategy-002.
- 예상 수정 파일: app/strategy/opening_range_breakout.py (NEW), app/strategy/__init__.py (STRATEGY_NAMES 등록), tests/test_strategy_opening_range_breakout.py (NEW).
- 테스트 기준: 신규 전략 happy / blocker / non-executable intent / KIS-import-isolation 회귀.
- 완료 후 다음 단계: Phase 4.

Phase 4: SOAK VERIFICATION (runtime-soak-001)
- 목표: 장시간 paper trading 검증 runner + counter / report / kill switch / dashboard read-only 노출.
- 포함 작업: runtime-soak-001.
- Codex job ID: runtime-soak-001.
- 예상 수정 파일: app/runtime/soak.py (NEW), app/api/routes.py (read-only status 추가 — GUI 전용 micro-edit), tests/test_runtime_soak.py (NEW).
- 테스트 기준: start / stop / tick / kill switch / error threshold / event log / summary report 회귀.
- 완료 후 다음 단계: Phase 5 (HELD).

Phase 5: LIVE VALIDATION PREP (live-validation-001) — HELD
- 목표: 소액 live validation 준비. preflight / manual arm / hard limits / whitelist / kill-switch 연동.
- 포함 작업: live-validation-001.
- Codex job ID: live-validation-001.
- 진입 조건: Phase 4 의 누적 soak 결과 + 명시적 사용자 승인 + MASTER_TRADING_ROADMAP §1 의 안전 원칙 재확인.
- 본 master plan 의 권고: Phase 4 결과 검토 후 별도 plan-only audit job (mvp-029-check 같은) 으로 진입 가능 여부 먼저 평가.
```

## 7. ROADMAP_STATUS.md 갱신 제안 (직접 수정하지 않음)

본 plan §2.4 의 내용을 그대로 `docs/ai/ROADMAP_STATUS.md` 다음 갱신에 반영. 갱신 작업 자체는 별도 micro-job (`roadmap-status-fix-002` 같은) 또는 사용자 수동 수정. 본 master plan 은 catalog / GUI / 코드 변경 0 원칙을 지키기 위해 직접 수정하지 않는다.

핵심 갱신 항목:

1. mvp-023 ~ mvp-029 행 전체 → 새 분류 (Phase 1 ~ Phase 5).
2. "Next single action" → "Phase 0: commit dirty + Phase 1: api-orders-paper-003-query".
3. pytest 누적 결과 갱신 (458 passed).
4. BLOCKED 상세 절 제거 (KIS_3 가 마지막 catalog gap 해소).
5. "새 mvp 번호 생성 금지 원칙" 유지.

## 8. 다음 단일 작업 추천

**권고: Phase 0 → Phase 1.**

### Phase 0 — 사용자 수동 작업 (Codex 없음)

`git status` 의 dirty 7 + untracked 5 (이번 시리즈 분) 을 4 개의 logical commit 으로 분리해 사람이 수동 commit:

```bash
# commit 1 — api-orders-paper-002-cancel-replace
git add projects/paper-trading/app/broker/kis.py
git add projects/paper-trading/tests/test_kis_paper_order_cancel_replace.py
git add projects/paper-trading/tests/test_broker_interface.py
git add projects/paper-trading/tests/test_kis_http_boundaries.py
git add projects/paper-trading/docs/ai/jobs/api-orders-paper-002-cancel-replace/
git commit -m "implement KIS paper cancel_order / replace_order (VTTT1004U)"

# commit 2 — KIS_2-check audit
git add projects/paper-trading/docs/ai/jobs/KIS_2-check/
git commit -m "audit: KIS_2-check feasibility analysis for query methods"

# commit 3 — KIS_3 catalog
git add docs/kis/MISSING_OFFICIAL_VALUES.md
git add projects/paper-trading/docs/ai/jobs/KIS_3/
git commit -m "catalog: KIS query response output[] sub-fields (§4.7.1 / §4.7.2)"

# commit 4 — paper-e2e-001 docs
git add projects/paper-trading/docs/ai/jobs/paper-e2e-001/
git commit -m "docs: paper-e2e-001 plan / patch / review"
```

(또는 사용자가 하나의 통합 commit 으로 처리해도 무방 — 본 plan 은 logical separation 만 제안.)

`app/api/server.py` / `scripts/_common.sh` / `scripts/start_server.sh` / `docs/ai/jobs/mvp-002/request.ko.md` 의 conversation-start residue 와 `docs/ai/AI_TEAM_BRIEFING.md` / `docs/ai/AI_TEAM_REQUEST_GENERATOR_BRIEF.md` / `docs/ai/jobs/paper-ux-001/` 는 본 시리즈 외 — 별도 결정.

### Phase 1 — 다음 Codex job: `api-orders-paper-003-query`

선정 사유:

1. **catalog 가 막 unblock 되었다**. KIS_3 (`docs/ai/jobs/KIS_3/recommendation.md`) 가 세 query method 모두 PARTIALLY READY 로 재분류했다.
2. **seed request.ko.md 이미 존재**. `docs/ai/jobs/KIS_3/next-job-request.md` 의 fenced markdown 블록 (line 3-112) 이 그대로 다음 job 의 request.ko.md 로 사용 가능.
3. **scope 명확**. adapter-level only, OMS / GUI / capabilities 미변경, paper 제약 (PDNO="" / CCLD_NCCS_DVSN="00" / SORT_SQN default / ODNO="") 준수.
4. **api-orders-paper-001 / api-orders-paper-002-cancel-replace 와 같은 패턴**: 새 GET 전용 transport (`KisQueryTransport` / `UrllibQueryTransport` / `MockQueryTransport`) 를 `KisAccountTransport` 패턴 그대로 재사용.

본 plan 의 §9 (codex-task.md) 에 다음 job 의 request.ko.md 정제판을 작성. 사용자는 그 본문을 `docs/ai/jobs/api-orders-paper-003-query/request.ko.md` 로 옮긴 뒤 GUI 한국어 작업 요청 칸에 입력해 Claude plan + codex-task 단계로 진입하면 된다.

### Phase 1 권고의 risk / alternative

- **risk**: 만약 Phase 0 (commit dirty) 를 건너뛰고 Phase 1 을 진행하면, working tree 의 KIS_3 catalog 변경이 commit 되지 않은 상태에서 다음 Codex 가 동일 catalog 를 읽어 사용하게 됨. 동작상 무해하지만 PR 분리가 어려워지고 회귀 추적이 흐려진다. **Phase 0 권고**.
- **alternative**: Phase 1 대신 Phase 2 (paper-002) 를 먼저 진행하는 것도 가능. catalog 의존성이 없어 commit dirty 와 무관. 다만 본 plan 은 (a) KIS_3 의 catalog 가 막 land 된 시점이라 그 가치를 즉시 활용하는 것이 명확하고, (b) Phase 2 / 3 는 catalog 무관이라 언제든 가능하다는 점에서 Phase 1 우선을 권고.

## 9. 다음 Codex job 의 request.ko.md 초안

본 master plan 의 sister 산출물 `codex-task.md` 에 정제판을 작성한다 (KIS_3 의 `next-job-request.md` 와 본질적으로 동일하나 사용자가 master plan 의 §8 권고를 그대로 따를 수 있게 self-contained).

## 10. 절대 하지 않음 (자체 점검)

본 plan 은 다음을 수행하지 않았다:

- [x] 코드 / 테스트 / catalog 본문 / `.env` / `.env.example` / GUI 일체 수정 없음.
- [x] KIS endpoint / TR ID / payload / header / response field 추측 없음 — 모든 인용은 catalog §4.2 / §4.7 / §4.7.1 의 `Confirmed: yes` 행에서.
- [x] live trading 활성화 / 실전 endpoint / 실 broker API / 자동 git ops 계획 없음.
- [x] Strategy / Agent / LLM 이 broker 직접 호출하는 구조 권고 없음.
- [x] OMS / RiskEngine 우회 경로 권고 없음.
- [x] `ALLOW_MARKET_ORDERS=true` / `OrderType.MARKET` 가드 변경 권고 없음.
- [x] `OrderType.STOP` 도입 권고 없음.
- [x] FX 변환 함수 / 환율 상수 도입 권고 없음.
- [x] 실 secret / 계좌번호 / Bearer token 기록 없음.
- [x] GUI 작업 + backend 작업을 하나의 Codex job 으로 묶는 권고 없음.
- [x] 동시에 두 개 이상의 Codex 구현 지시 작성 없음 — codex-task.md 는 단 한 개 (Phase 1 의 api-orders-paper-003-query) 만 seed 제공.
- [x] `docs/ai/ROADMAP_STATUS.md` 직접 수정 없음 — 갱신 제안만 본 plan §2.4 / §7 에 기록.

## 11. 리뷰 체크리스트

본 master plan 자체의 review 시 확인할 항목:

- [ ] §2 의 ground truth 가 실제 `git log` / `git status` 와 일치하는가.
- [ ] §3 의 분류가 KIS_2-check / KIS_3 / paper-e2e-001 / runtime-002 의 review 결과와 정합하는가.
- [ ] §4 의 의존관계가 실제 코드 import / module boundary 와 일치하는가.
- [ ] §6 의 Phase 순서가 §4 의 의존관계와 모순되지 않는가.
- [ ] §8 의 다음 Codex job 추천이 catalog `Confirmed: yes` 행만 사용하는가.
- [ ] §9 의 request.ko.md 초안 (codex-task.md) 이 BLOCKED 기능 미포함 / paper 제약 준수 / OMS 미확장 / GUI 미변경을 모두 명시하는가.
- [ ] `<TBD>` 또는 `Confirmed: no` 행을 사용하는 plan 권고 없음.
- [ ] 본 plan 이 코드 / catalog / `.env` / GUI 변경 0 인가.
