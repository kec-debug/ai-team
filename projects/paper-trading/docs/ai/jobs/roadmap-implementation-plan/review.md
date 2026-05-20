# roadmap-implementation-plan — Claude Review

## Verdict

APPROVE

## Summary

roadmap-implementation-plan 은 docs-only 설계 job 이었고, Codex pass 가 정확히 그 정신을 지켰다. `plan.md` 와 `codex-task.md` 는 이전 Claude turn 에서 작성된 그대로 보존됐고, Codex 의 implementer pass 는 `patch.md` 만 추가했다. `api-orders-paper-003-query` 같은 후속 작업을 실수로 선행 구현하지 않았고, 코드 / 테스트 / catalog / `.env` / GUI 일체 무변동. 또한 본 review 시점에서 이미 master plan 의 Phase 0 권고가 부분 실행됨이 git log 에서 확인된다 (`4d5e639 implement KIS paper cancel and replace`).

## Codex pass 행동 검증

Codex 의 `patch.md` 가 보고한 내용:

1. **`patch.md` 만 신규 추가** — `plan.md`, `codex-task.md`, `request.ko.md` 는 이전 turn 에 작성됨.
2. **`api-orders-paper-003-query` 미실행** — `codex-task.md` 의 seed 는 다음 job 의 입력이지 본 turn 의 작업이 아님을 정확히 식별.
3. **무변경 확인** — `git diff --name-only HEAD -- projects/paper-trading/app projects/paper-trading/tests` 결과의 `app/api/server.py` 는 본 시리즈 전부터 dirty 였다고 명시. 사실과 일치 (이전 모든 review 에서 동일 파일이 conversation-start residue 로 분류됨).
4. **테스트 베이스라인 유지** — 458 passed (compileall PASS, pytest PASS). 본 docs-only job 의 정확한 expectation.
5. **안전 grep clean** — `docs/ai/jobs/roadmap-implementation-plan` 안에 외부 HTTP / 의존성 import 0.

이 5 가지 모두 정확. Codex 가 docs-only 의도를 오해해서 코드를 만들지 않았다는 점이 가장 중요한 정직 신호다.

## Plan / codex-task 내용 재검증 (이전 turn 산출물)

`plan.md` 의 핵심 결정은 정확하다:

- **Ground truth 정정**: 15/15 완료 항목 검증, `runtime-002` already committed (commit `22a3849`), `KIS_3` / `api-orders-paper-002-cancel-replace` DONE-DIRTY 표시. 본 review 시점의 `git log` 와 일치.
- **7 개 작업 분류**: BLOCKED-BY-DOCS 0 건, READY 3 건 (`api-orders-paper-003-query` / `paper-002` / `strategy-002`), READY-after-value 1 건 (`runtime-soak-001`), HELD 1 건 (`live-validation-001`). KIS_2-check / KIS_3 review 결과와 정합.
- **의존관계**: 세 READY job 의 상호 독립성을 정확히 식별. soak / live 의 process gate 명시.
- **Phase 순서**: Phase 0 (commit dirty) → Phase 1 (api-orders-paper-003-query) → Phase 2 (paper-002) → Phase 3 (strategy-002) → Phase 4 (runtime-soak-001) → Phase 5 (live-validation-001 HELD). MASTER_TRADING_ROADMAP §1 의 안전 원칙과 정합.
- **묶음 금지 원칙**: 본 시리즈가 1-domain-per-job 으로 review APPROVE 받아온 패턴을 그대로 보존. 1000 LoC + 5 파일 미만.

`codex-task.md` 의 seed (api-orders-paper-003-query request.ko.md 초안) 검증:

- 사용 가능 catalog 행을 §4.7 / §4.7.1 로 정확히 한정.
- 사용 금지: `/inquire-nccs` paper, live TR_IDs, paper-unsupported TR_IDs, Asia 추측, OMS 확장, GUI 변경, capabilities surface 변경, 외부 HTTP libs, `OrderType.MARKET` 우회, `ALLOW_MARKET_ORDERS=true` 허용, `OrderType.STOP` 도입, FX 변환, `.env` 수정 모두 명시.
- `%` (전체 거래소) 허용 여부에서 fail-closed (US only) 로 결정 — KIS_3 review 의 F2 권고와 정합.
- `KisQueryTransport` 신규 (POST `KisOrderTransport` 재사용 금지) 명시 — `KisAccountTransport` GET 전용 패턴 재사용.
- `_order_history` 패턴 (`unknown_broker_order_id` fail-closed) 을 `get_order_status` 에 재사용 — api-orders-paper-002-cancel-replace 와 정합.
- 좁은 갱신 후보 (test_broker_interface / test_kis_http_boundaries 의 `get_open_orders` / `get_fills` / `get_order_status` 단언 갱신) 명시하면서 cancel/replace 단언은 절대 변경 금지 — api-orders-paper-002-cancel-replace 의 이미 land 된 갱신 보호.

## 실제 Phase 0 진행 상황 (本 review 시점)

`git log --since="1 hour ago"` 결과:

```text
4d5e639 implement KIS paper cancel and replace
```

→ master plan Phase 0 의 `api-orders-paper-002-cancel-replace` 커밋이 land 됨. 추가로 `docs/kis/MISSING_OFFICIAL_VALUES.md` 가 `git status` 의 modify 목록에서 사라진 점으로 보아 **KIS_3 catalog 도 동일 커밋 또는 다른 커밋으로 land 됨** (정확히 어느 커밋에 통합됐는지는 본 review 에서 확인 불필요).

남은 untracked dirs:

- `projects/paper-trading/docs/ai/jobs/KIS_2-check/` (audit doc — 사용자가 commit 여부 결정 중)
- `projects/paper-trading/docs/ai/jobs/paper-e2e-001/` (test 는 이미 committed, doc dir 만 남음)
- `projects/paper-trading/docs/ai/jobs/roadmap-implementation-plan/` (본 master plan 자체)
- `docs/ai/jobs/api-orders-paper-003-query/` — **사용자가 이미 `codex-task.md` seed 를 새 job 디렉터리로 옮겼음**. master plan §8 의 권고대로 Phase 1 진입 준비 완료.

Pre-existing residue (본 master plan 전부터 dirty, master plan 권고 영향 외):

- `app/api/server.py`, `scripts/_common.sh`, `scripts/start_server.sh`, `docs/ai/jobs/mvp-002/request.ko.md`, `docs/ai/AI_TEAM_BRIEFING.md`, `docs/ai/AI_TEAM_REQUEST_GENERATOR_BRIEF.md`, `docs/ai/jobs/paper-ux-001/` — 본 시리즈 외 / 사용자 결정 영역.

master plan §8 의 권고대로 Phase 0 가 부분 실행되어 가장 큰 dirty (cancel/replace + KIS_3 catalog) 가 commit 됐고, Phase 1 의 새 job 디렉터리가 user 가 직접 준비함. 본 review 의 권고와 정확히 일치.

## Safety regression

| 항목 | 결과 |
| --- | --- |
| docs-only (코드 / 테스트 / catalog 본문 / `.env` / GUI 무변동) | OK |
| pytest 458 passed (pre-job baseline 그대로) | OK |
| compileall PASS | OK |
| 외부 의존성 추가 없음 (`requests` / `httpx` / `aiohttp` / `urllib3` / `openpyxl` / `pandas`) | OK |
| 실 secret / 계좌번호 / token / Bearer leak 없음 | OK — plan / codex-task / patch 모두 `fake-key-XYZ` 형식 또는 placeholder 만 사용 |
| KIS endpoint / TR_ID / payload / header / response field 추측 없음 | OK — 모든 인용이 `Confirmed: yes` catalog 행에서 |
| live trading 활성화 권고 없음 | OK — live-validation-001 명시적 HELD |
| Strategy / Agent / LLM 의 broker 직접 호출 경로 권고 없음 | OK |
| OMS / RiskEngine 우회 경로 권고 없음 | OK |
| `OrderType.MARKET` 가드 / `ALLOW_MARKET_ORDERS=true` reject 변경 권고 없음 | OK |
| `OrderType.STOP` 도입 권고 없음 | OK |
| FX 변환 함수 / 환율 상수 도입 권고 없음 | OK |
| GUI / backend mix Codex job 권고 없음 | OK — Phase 별 1-domain-per-job 유지 |
| 동시 2 개 이상 Codex 구현 지시 작성 없음 | OK — codex-task.md 는 단 1 개 (api-orders-paper-003-query) 만 seed |
| 자동 git commit / push / merge / deploy 수행 없음 | 수행 안 됨 |
| `docs/ai/ROADMAP_STATUS.md` 직접 수정 없음 (갱신 제안만 plan §7 에 기록) | OK |

## Findings

### F1 (INFO) — Codex pass 의 추가 가치는 patch.md 1 개 파일

본 turn 의 Codex implementer 는 단지 `patch.md` 추가 외 작업이 없었다. 이는 docs-only job 의 올바른 처리 (이전 Claude turn 이 plan + codex-task 를 작성했고, Codex 가 그 위에 무엇도 더하지 않는 것이 정답). 추가 작업이 없었다는 점 자체가 안전 정직 신호로 해석. **본 finding 은 권고 없음** — 정상.

### F2 (INFO) — paper-e2e-001 / KIS_2-check 의 doc dir 미커밋

master plan §8 의 Phase 0 가 부분 실행됐고, 4 개 logical commit 중 2 개 (api-orders-paper-002-cancel-replace + KIS_3) 만 land 됐다. `paper-e2e-001` / `KIS_2-check` / 본 `roadmap-implementation-plan` 의 doc 디렉터리는 여전히 untracked. **이는 사용자 결정 영역**이며 본 review 가 강제할 사안 아님. 사용자가 (a) 한 번에 묶어 commit, (b) 점진 commit, (c) doc dir 만 별도 leftover commit 으로 처리 중 선택하면 됨.

### F3 (INFO) — 사용자가 이미 Phase 1 디렉터리 준비 완료

`docs/ai/jobs/api-orders-paper-003-query/` 가 master plan 권고 직후 사용자에 의해 생성되어 `request.ko.md` (codex-task.md 의 fenced 블록 그대로) 가 들어 있다. Phase 1 의 다음 turn 에서 Claude 가 plan + codex-task 단계 진입 준비 완료. **본 review 의 결정에 영향 없음** — 본 master plan 의 권고가 정확히 실행되고 있다는 증거.

## Final Checklist

| 항목 | 결과 |
| --- | --- |
| `plan.md` 의 ground truth 분석이 `git log` / `git status` 와 일치 | OK |
| 15 개 완료 항목 검증이 정확 | OK |
| 7 개 남은 작업 분류가 KIS_2-check / KIS_3 / paper-e2e-001 / runtime-002 의 review 결과와 정합 | OK |
| 의존관계가 코드 import / module boundary 와 일치 | OK |
| Phase 0 ~ Phase 5 순서가 의존관계와 모순 없음 | OK |
| 다음 단일 Codex job 추천 (api-orders-paper-003-query) 이 catalog `Confirmed: yes` 행만 사용 | OK |
| `codex-task.md` 의 seed 초안이 BLOCKED 기능 미포함 / paper 제약 준수 / OMS 미확장 / GUI 미변경 / capabilities 보존 모두 명시 | OK |
| ROADMAP_STATUS.md 직접 수정 없음 (제안만 plan §2.4 / §7 에 기록) | OK |
| 코드 / catalog 본문 / `.env` / GUI 변경 없음 | OK |
| 동시 2 개 이상 Codex 구현 지시 없음 | OK |
| pytest 458 passed (pre-job baseline 그대로) | OK |
| commit / push / merge / deploy 수행 없음 | OK |

## Follow-up Codex prompt

없음. APPROVE.

다음 단계는 사용자가 직접:

1. (선택) master plan §8 의 Phase 0 남은 부분 처리 — `paper-e2e-001` doc dir / `KIS_2-check` / `roadmap-implementation-plan` 자체의 commit 여부 결정. 본 review 가 강제하지 않음.
2. `docs/ai/jobs/api-orders-paper-003-query/request.ko.md` 가 이미 준비됐으므로, GUI 한국어 작업 요청 칸에 그 내용을 입력해 **Phase 1 의 Claude plan + codex-task 단계** 로 진입.
3. Phase 1 land 후 master plan §6 의 Phase 2 (paper-002) 또는 Phase 3 (strategy-002) 중 우선순위 선택.

본 review 는 commit / push / merge / deploy 를 수행하지 않는다. 본 master plan + codex-task.md 자체는 코드 / catalog 본문 / `.env` / GUI 어떤 파일도 수정하지 않았다.
