# final-platform-plan — Codex 구현 지시문

You are Codex generating **11 Korean design documents** for the paper-trading platform's final architecture. **This job is documentation-only.** Do NOT modify any application code, tests, scripts, catalog content, `.env`, or any file outside `projects/paper-trading/docs/ai/jobs/final-platform-plan/`.

Read first (in order):

1. `docs/ai/CLAUDE_CODEX_WORKFLOW.md` (root) — workflow + safety rules.
2. `projects/paper-trading/docs/ai/jobs/final-platform-plan/request.ko.md` — user request.
3. `projects/paper-trading/docs/ai/jobs/final-platform-plan/plan.md` — this task's plan. Every "필수 포함" section is binding.
4. `projects/paper-trading/README.md` — existing project guide.
5. `projects/paper-trading/docs/RUNBOOK.md` — Korean operator runbook (synchronize with).
6. `projects/paper-trading/docs/OPS_AUDIT.md` — Korean final ops audit (synchronize with).
7. `docs/ai/ROADMAP_STATUS.md` / `docs/ai/MASTER_TRADING_ROADMAP.md` (root) — roadmap principles.
8. `docs/kis/MISSING_OFFICIAL_VALUES.md` / `docs/kis/MISSING_MARKET_DATA_VALUES.md` (root) — KIS catalog (only `Confirmed: yes` rows may be cited).
9. `projects/paper-trading/app/` — read-only inspection of existing modules.
10. `projects/paper-trading/docs/ai/jobs/` — other job records (read for context, do NOT modify any non-`final-platform-plan` subdirectory).

## Absolute prohibitions

- **Do not modify any file outside `projects/paper-trading/docs/ai/jobs/final-platform-plan/`.** Not `app/`, not `tests/`, not `scripts/`, not `docs/kis/`, not `.env`, not `.env.example`, not `README.md`, not `docs/RUNBOOK.md`, not `docs/OPS_AUDIT.md`, not any other job directory.
- Do not write Python / TypeScript / SQL / Bash code into any document. Pseudocode and ASCII diagrams are OK. The 11 docs are prose + tables + structural lists.
- Do not invent KIS endpoints, TR IDs, request payloads, response field names, or vendor-specific values. Only cite `Confirmed: yes` rows from `docs/kis/MISSING_OFFICIAL_VALUES.md`. Unknown values stay TODO / fail-closed.
- Do not include profit guarantees, fake win-rate claims, exaggerated performance promises, or anything resembling marketing copy.
- Do not include time estimates ("2 sprints", "Q1 까지", "1 주 안에 완료" etc.). Backlog sizing is qualitative (S/M/L or dependency stage) only.
- Do not include real app keys, app secrets, account numbers, access tokens, or Bearer tokens — use placeholder text like `<redacted>` / `***xxxx` if needed.
- Do not enable live trading. Do not write any document that suggests bypassing the existing live trading lock.
- Do not run `git commit`, `git push`, `git merge`, PR creation, or deployment.
- Do not write fake / fabricated test results. If asked for a test count, cite the current `pytest -p no:cacheprovider` result from a recent log only (do NOT re-run).

If completing the job seems to require editing any forbidden file, STOP and document in `patch.md` under `## Out-of-scope discovery`.

## Allowed file changes (exactly 12 new files)

| Path | Action |
| --- | --- |
| `projects/paper-trading/docs/ai/jobs/final-platform-plan/00_current_state.md` | NEW |
| `projects/paper-trading/docs/ai/jobs/final-platform-plan/01_product_spec.md` | NEW |
| `projects/paper-trading/docs/ai/jobs/final-platform-plan/02_ui_ux_spec.md` | NEW |
| `projects/paper-trading/docs/ai/jobs/final-platform-plan/03_paper_training_runtime.md` | NEW |
| `projects/paper-trading/docs/ai/jobs/final-platform-plan/04_agent_strategy_pipeline.md` | NEW |
| `projects/paper-trading/docs/ai/jobs/final-platform-plan/05_live_validation_console.md` | NEW |
| `projects/paper-trading/docs/ai/jobs/final-platform-plan/06_api_data_storage.md` | NEW |
| `projects/paper-trading/docs/ai/jobs/final-platform-plan/07_risk_safety_observability.md` | NEW |
| `projects/paper-trading/docs/ai/jobs/final-platform-plan/08_runbook.md` | NEW |
| `projects/paper-trading/docs/ai/jobs/final-platform-plan/09_implementation_backlog.md` | NEW |
| `projects/paper-trading/docs/ai/jobs/final-platform-plan/10_acceptance_criteria.md` | NEW |
| `projects/paper-trading/docs/ai/jobs/final-platform-plan/patch.md` | NEW |

No other files. `request.ko.md` and `plan.md` already exist; do not modify them.

## Style rules (every doc)

1. **언어**: 한국어 우선. 기술 식별자 (e.g., `OrderIntent`, `RiskEngine`, `KIS_ORDER_DRY_RUN`) 는 inline `code` 로 영어 그대로.
2. **운영자 readable**: 비개발자도 각 doc 의 첫 문단을 보고 영역의 목적 + 안전 원칙을 이해할 수 있어야 함.
3. **개발자 specific**: 각 doc 의 본문은 implementation backlog 으로 직접 변환 가능한 명세 (필드 / 상태 transition / 의존관계 등).
4. **형식**: Markdown. H1 = doc title, H2 = 섹션, H3 = 하위 섹션. Code 블록은 ASCII diagram / 도메인 모델 필드 정의에만 사용.
5. **한 doc 의 최대 길이**: 자연스럽게. 강제 줄 수 제한 없음. 단 doc 마다 평균 200~600 줄 권장.
6. **반복 가능한 cross-reference**: 각 doc 은 자신이 의존하는 다른 doc 을 명시적으로 인용 (예: "본 doc 은 `00_current_state.md` §3.2 의 broker 인벤토리를 anchor 로 한다").
7. **TODO 표시**: 미확인 / 미설계 / 추후 결정 항목은 `> **TODO**: ...` blockquote 로 명시. 추측 금지.
8. **No coding**: 어떤 doc 도 실행 가능한 코드 블록을 포함하지 않음. 도메인 모델 정의는 pseudocode-style 표 (필드 / 타입 / 의미 / source) 권장.

## Per-document requirements

### `00_current_state.md`

Anchor for everything else. Must include:

- 현재 commit `3812144 add paper trading use-ready operations` 시점 명시.
- pytest 557 passed 베이스라인.
- `app/` 모든 모듈의 한국어 인벤토리 (plan §3.1 ~ §3.5).
- `tests/` / `scripts/` / `docs/` 인벤토리 (plan §3.6).
- Known issues 14 개 (plan §3.7).
- 6 단 live trading 차단 가드 + 3 중 market guard + dry-run default + kill switch 등 현재 안전 상태 요약 (`OPS_AUDIT.md` 와 정합).
- 마지막 섹션: "본 문서 이후의 doc 들은 본 ground truth 를 기준으로 작성한다."

### `01_product_spec.md`

10 영역 (plan §4.2). 각 영역마다:

- 한 줄 정의.
- 사용자 use case (운영자 / 분석가 / 개발자).
- 이미 구현된 부분 (00_current_state 인용).
- 미구현 부분.
- 다른 영역과의 의존관계.

마지막 섹션: 전체 platform navigation 의 mermaid-style 아닌 ASCII 도식 (영역 간 화살표).

### `02_ui_ux_spec.md`

운영용 dashboard 설계. plan §4.3 의 "필수 포함" 모두. ASCII wireframe / 영역별 표. 실제 HTML 금지.

다음 wireframe 권고:

- Header: safety banner (3 단 escalation).
- Left nav: 10 영역 (01_product_spec 의 영역과 1:1 대응).
- Main area: 영역별 status card grid.
- Footer: 시스템 buildinfo + 마지막 갱신 시각.

### `03_paper_training_runtime.md`

24h service 모드. plan §4.4 의 "필수 포함" 모두. 다음 도식 권고:

```
TrainingRunner (24h loop)
  ├─ Session Router (KRX / US)
  │    └─ valid window → 주문 허용
  │    └─ closed → analysis / replay / preparation
  ├─ DataSource adapter (replay / synthetic / live quote)
  ├─ Strategy 평가
  ├─ RiskEngine
  ├─ OMS
  ├─ PaperBroker (tick)
  └─ Journal / Position / Cash 갱신
```

10 종 안전 가드 모두 표로 정리 (가드명 / 의미 / 트리거 조건 / 동작 / 현재 구현 여부).

### `04_agent_strategy_pipeline.md`

7 종 Agent + LLM provider. plan §4.5 의 "필수 포함" 모두.

각 Agent 의 표 권고:

| 항목 | 내용 |
| --- | --- |
| Input | typed input (필드 / 타입 / 의미) |
| Output | typed output (score / confidence / reasons / blockers / metadata) |
| Provider | rule-based default + optional LLM |
| Fallback | LLM 실패 시 deterministic provider |
| Validation | Pydantic 검증 + malformed block |
| Risk block authority | LLM 단독 해제 불가 |

Pipeline flow 도식:

```
Universe → 7 Agent enrichment → RiskAnalysis hard block → Recommendation
   → Strategy candidate → RiskEngine verdict → OMS order request
   → BrokerAdapter (paper or locked live)
```

Strategy boundary 재확인: broker 직접 호출 0, candidate / non-executable intent 까지만.

### `05_live_validation_console.md`

분리된 live console. plan §4.6 의 "필수 포함" 모두.

- 14 항 readiness checklist 표 (live-validation-001 의 14 항 그대로 + arm/disarm 개념 추가).
- arm/disarm flow 도식 (current state machine: locked → preflight_ok → manual_approval_pending → armed (별 future job) → disarmed).
- `live_validation_ready` 의 의미 명확화 (UX 신호일 뿐 코드 게이트 풀기 0 — 현재 동작 그대로).
- 주문 버튼 0, status check 중심.
- 실 live 주문 활성화는 본 doc 범위 밖.

### `06_api_data_storage.md`

API + Data model + Storage 종합. plan §4.7 의 "필수 포함" 모두.

#### API 섹션

각 endpoint 마다 표:

| 항목 | 내용 |
| --- | --- |
| Method | GET / POST |
| Purpose | 한국어 한 줄 |
| Request | path / query / body 필드 |
| Response | 필드 / 타입 |
| Authority | 누가 호출 가능 (운영자 / 분석가 / 시스템 자동) |
| Safety conditions | 호출 가능 사전 조건 (예: kill switch off, paper mode 등) |
| Side effects | 부수효과 (예: order 생성, kill switch toggle) |
| Paper/Live separation | 어느 쪽 |

신규 endpoint 마다 "Existing? — No, NEW" 표기.

#### Data Model 섹션

각 모델별 필드 표:

| Field | Type | Required | Default | 의미 / Source |
| --- | --- | --- | --- | --- |

상태 transition 이 있는 모델 (`OrderState`, `TrainingRun`, `LiveReadinessStatus`, `AuditEvent`) 은 ASCII state machine 추가.

#### Storage 섹션

PostgreSQL 테이블별 표:

| Table | Purpose | Key columns | Indexes | Retention |

Redis key 별 표:

| Key pattern | Type | TTL | Purpose |

File / JSON fallback section: 현재 `reports/` 의 구조 인용.

Replay + rehydrate + crash recovery 각각 별도 섹션.

### `07_risk_safety_observability.md`

19 종 safety guard + 13 종 observability. plan §4.8 의 "필수 포함" 모두.

각 guard 표:

| Guard | 트리거 조건 | 동작 | 현재 구현 여부 | 후속 job 필요 여부 |

각 observability 표:

| Card / Metric | 노출 위치 | 데이터 source | 새 endpoint 필요 여부 |

### `08_runbook.md`

운영자 runbook. plan §4.9 의 "필수 포함" 모두.

기존 `docs/RUNBOOK.md` 와 정합. **본 doc 은 RUNBOOK.md 를 대체하지 않고 확장한다** — RUNBOOK.md 는 paper-use-ready-001 의 한국어 운영 가이드. 본 doc 은 final platform 단계의 더 상세한 procedure / incident response.

각 procedure 마다:

- 사전 조건 (precondition).
- 단계별 명령 (참조용 — code 블록 OK 단 pseudocode).
- 검증 (verification).
- 실패 시 fallback.
- Rollback.

### `09_implementation_backlog.md`

Backlog. plan §4.10 의 "필수 포함" 모두.

각 backlog item 표:

| 항목 | 내용 |
| --- | --- |
| Job ID | (예: `paper-runtime-002-training-service`) |
| Purpose | 한국어 한 줄 |
| Size | S / M / L (정성적) |
| 수정 파일 | (path 목록) |
| 신규 파일 | (path 목록) |
| 의존 backlog | (Job ID 목록) |
| Acceptance | 완료 기준 |
| Test plan | 테스트 시나리오 |
| Risk notes | 위험 |
| Rollback notes | 롤백 절차 |

최소 15 개 backlog item 권고. 분류 권고:

- **Runtime**: TrainingRun 도메인 / 24h service / Session Router 통합 / data source adapter.
- **Agent**: 7 종 Agent 구현 / LLM provider / fallback.
- **Strategy**: Strategy Lab UI / backtest endpoint / 추가 전략.
- **Live**: live console 분리 + arm/disarm endpoint (locked) / preflight 확장.
- **Storage**: PostgreSQL 도입 / Redis 도입 / 마이그레이션 / replay event log.
- **Risk / Safety**: 추가 가드 (volatility / broker disconnect / token expired) / kill switch refinement.
- **Observability**: heartbeat / alert skeleton / incident view / reconciliation.
- **Ops**: runtime-soak 확장 / runbook 확장 / 다중 환경 (staging) 지원.

각 item 은 별 Codex job 으로 직접 변환 가능해야 한다. 시간 추정 금지 (S/M/L 만).

### `10_acceptance_criteria.md`

본 design 의 acceptance + 후속 job template. plan §4.11 의 "필수 포함" 모두.

#### 본 design 의 acceptance

- 11 doc + patch.md = 12 files in `final-platform-plan/`.
- 모두 한국어.
- 운영자 / 개발자 양측 readable.
- 보안 원칙 준수 (수익 보장 / 시간 추정 / KIS 추측 / live arming 0).
- application code 0 line.

#### 후속 job 일반 acceptance template (모든 future job 적용)

표:

| 항목 | 기준 |
| --- | --- |
| pytest | 전체 PASS, 회귀 0 |
| safety grep | clean (`scripts/safety_grep.sh` 또는 동등) |
| 보호 영역 | `app/broker/kis_http.py` 무변동 |
| secret | 노출 0 |
| git | commit / push / merge / deploy 자동화 0 |
| Strategy / Agent | broker 직접 호출 0 |
| OMS / RiskEngine | 우회 0 |
| `OrderType` | `STOP` 미도입, `MARKET` 3 중 가드 유지 |
| FX | 변환 미도입 |
| Korean docs | 사용자-대면 문서는 한국어 |

마지막 섹션: "본 design 이 끝났음을 선언하는 marker. 다음 단계는 `09_implementation_backlog` 의 item 선택부터." 명시.

## Verification steps Codex must run

After writing the 11 docs, run:

```bash
ls -la projects/paper-trading/docs/ai/jobs/final-platform-plan/
# Expect: request.ko.md, plan.md, codex-task.md, 00_*.md ~ 10_*.md, patch.md (after this step)
```

Safety grep (Codex runs and pastes output into patch.md):

```bash
grep -rnE "수익 보장|profit guarantee|승률 100|fake" projects/paper-trading/docs/ai/jobs/final-platform-plan/ || true
grep -rnE "Bearer eyJ|access_token=eyJ|appkey=PS" projects/paper-trading/docs/ai/jobs/final-platform-plan/ || true
grep -rn "TTTS3035R\|TTTS3018R\|TTTT3039R\|TTTT1002U\|TTTS1003U" projects/paper-trading/docs/ai/jobs/final-platform-plan/ || true
grep -rn "1 주 안에\|2 주 안에\|sprint\|Q1 까지\|Q2 까지" projects/paper-trading/docs/ai/jobs/final-platform-plan/ || true
```

Expected: all 4 greps return 0 lines (or only comments inside this codex-task.md / plan.md / request.ko.md that quote them as forbidden patterns — those are OK).

Do NOT run `pytest` or `compileall` — this job adds zero application code, baseline is unchanged.

Do NOT run any `git` mutation command.

## `patch.md` contents

Create `docs/ai/jobs/final-platform-plan/patch.md` with these sections:

1. **Files Changed** — explicit list of 12 new files. Verify NO file outside `final-platform-plan/` appears.
2. **Per-document summary** — one paragraph per doc (00 ~ 10) covering: purpose, key sections, length, cross-references.
3. **Verification output** — `ls -la final-platform-plan/` listing + 4 safety grep results (verbatim).
4. **Safety confirmation** — explicit:
   - No `app/` / `tests/` / `scripts/` / `.env` / catalog 본문 modified.
   - No KIS endpoint / TR_ID guessed.
   - No profit / win-rate / time-estimate claims.
   - No live arming / activation suggested.
   - No real secret / 계좌번호 / token written.
   - `commit / push / merge / deploy` 수행 0.
5. **Remaining TODOs** — backlog items 의 다음 진입 후보 + 본 design 의 알려진 한계.
6. **Claude verification prompt** — paste this exact text:

   > Use prompts/claude.md.
   >
   > Project directory: /root/ai-dev-center/projects/ai-team/projects/paper-trading
   > Job ID: final-platform-plan
   > Job directory: /root/ai-dev-center/projects/ai-team/projects/paper-trading/docs/ai/jobs/final-platform-plan
   >
   > Review the final-platform-plan design output.
   >
   > Read:
   > - request.ko.md
   > - plan.md
   > - codex-task.md
   > - patch.md
   > - 00_current_state.md ~ 10_acceptance_criteria.md
   >
   > Review focus:
   > 1. 11 design docs + patch.md exist (12 files total).
   > 2. All 11 design docs are in Korean.
   > 3. Each doc covers the plan.md "필수 포함" items.
   > 4. No application code / tests / `.env` / catalog content modified.
   > 5. No KIS endpoint / TR ID / payload / response field invented.
   > 6. No live trading activation suggested.
   > 7. No profit guarantee / win-rate / time-estimate claims.
   > 8. No real secret / app key / app secret / account number / Bearer token written.
   > 9. Strategy → RiskEngine → OMS → BrokerAdapter boundary preserved in all docs.
   > 10. Agent / LLM 의 broker 직접 호출 0.
   > 11. live default lock + manual approval principle preserved.
   > 12. No `commit / push / merge / deploy` automation suggested.
   >
   > Verdict must be one of: APPROVE / REQUEST CHANGES / BLOCK.
   >
   > If REQUEST CHANGES or BLOCK, write a Follow-up Codex Prompt that fixes only the required issues. Do not expand scope.

7. **Follow-up Codex prompt rules** (only if Claude returns REQUEST CHANGES or BLOCK):

   - Codex must read: `request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, `review.md`.
   - Apply Required Fixes only.
   - Do not expand beyond `final-platform-plan/` directory.
   - Update `patch.md` with `## Follow-up <N>` section (do not create new patch file).
   - Do not modify `app/` / `tests/` / `scripts/` / `.env` / catalog 본문.
   - Do not commit / push / merge / deploy.
   - Do not modify secrets.

8. **Status footer**: `READY FOR REVIEW`.

Stop. Do not commit, push, merge, deploy, or modify any file outside `docs/ai/jobs/final-platform-plan/`. Hand off to the human.
