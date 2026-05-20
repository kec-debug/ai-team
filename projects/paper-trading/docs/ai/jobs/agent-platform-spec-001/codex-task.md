# agent-platform-spec-001 — Codex 구현 지시문

You are Codex generating **11 Korean design documents** + `patch.md` for the paper-trading platform's Agent platform final design: **85 role modules** (40 real-time core + 10 news/event + 20 validation/learning + 15 ops/security) running as **7 execution services** (Orchestrator / Market Data / Strategy / Broker Gateway / News & Event / Validation & Learning / Ops & Security), with a **Top 15 critical + 5 Claude/Codex meta-agent** focus set as the actual entry point.

**This job is documentation-only.** Do NOT modify any application code, tests, scripts, catalog content, `.env`, or any file outside `projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/`.

Read first (in order):

1. `docs/ai/CLAUDE_CODEX_WORKFLOW.md` (root) — workflow + safety rules.
2. `projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/request.ko.md` — user request (85+7 final design).
3. `projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/plan.md` — this task's plan. Every "필수 포함" section + 7-service §3 is binding.
4. `projects/paper-trading/docs/ai/jobs/final-platform-plan/00_current_state.md` ~ `10_acceptance_criteria.md` — earlier design set; reference and extend, NEVER modify.
5. `projects/paper-trading/README.md` / `docs/RUNBOOK.md` / `docs/OPS_AUDIT.md` — operator guides (read-only).
6. `docs/ai/ROADMAP_STATUS.md` / `docs/ai/MASTER_TRADING_ROADMAP.md` (root) — roadmap principles.
7. `docs/kis/MISSING_OFFICIAL_VALUES.md` (root) — KIS catalog (only `Confirmed: yes` rows may be cited by § number; do NOT invent fields).
8. `projects/paper-trading/app/` — read-only inspection of `broker/`, `oms/`, `risk/`, `strategy/`, `runtime/`, `ops/`, `domain/`, `api/`.

## Absolute prohibitions

- **Do not modify any file outside `projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/`.** Not `app/`, not `tests/`, not `scripts/`, not `docs/kis/`, not `.env`, not `.env.example`, not `README.md`, not `docs/RUNBOOK.md`, not `docs/OPS_AUDIT.md`, not other job directories, not `final-platform-plan/`.
- Do not write Python / TypeScript / SQL / Bash code into any document. Pseudocode and ASCII diagrams are OK.
- Do not invent KIS endpoints, TR IDs, payloads, response field names, or vendor-specific values. Cite only `Confirmed: yes` rows by § number from `docs/kis/MISSING_OFFICIAL_VALUES.md`. Mark unknown values as `> **TODO**: ...`.
- Do not include profit guarantees, fake win-rate claims, or marketing copy.
- Do not include time estimates ("2 sprints", "Q1 까지", "1 주 안에"). Backlog sizing is qualitative (S/M/L) only.
- Do not write real app keys, app secrets, account numbers, access tokens, or Bearer tokens — use `<redacted>` / `***xxxx` if needed.
- Do not enable live trading or suggest bypassing the live trading lock. "실전 전환 승인 에이전트" MUST be documented as locked / future-approval-gated.
- Do not suggest Agent → broker direct call. Agent ≠ Broker. Every doc states this.
- **Do not suggest any service other than Broker Gateway Service holds KIS credentials or calls KIS API.** Broker Gateway is the sole KIS-credentialed service.
- Do not suggest exposing inter-service RPC to the public internet. Loopback / UNIX socket only.
- Do not run `git commit`, `git push`, `git merge`, PR creation, or deployment.

If completing the job requires editing any forbidden file, STOP and document in `patch.md` under `## Out-of-scope discovery`.

## Allowed file changes (exactly 12 new files)

| Path | Action |
| --- | --- |
| `docs/ai/jobs/agent-platform-spec-001/00_principles_and_boundaries.md` | NEW |
| `docs/ai/jobs/agent-platform-spec-001/01_seven_services.md` | NEW |
| `docs/ai/jobs/agent-platform-spec-001/02_realtime_core_40_agents.md` | NEW |
| `docs/ai/jobs/agent-platform-spec-001/03_news_event_10_agents.md` | NEW |
| `docs/ai/jobs/agent-platform-spec-001/04_validation_learning_20_agents.md` | NEW |
| `docs/ai/jobs/agent-platform-spec-001/05_ops_security_15_agents.md` | NEW |
| `docs/ai/jobs/agent-platform-spec-001/06_top15_focus_set.md` | NEW |
| `docs/ai/jobs/agent-platform-spec-001/07_llm_provider_design.md` | NEW |
| `docs/ai/jobs/agent-platform-spec-001/08_data_contracts.md` | NEW |
| `docs/ai/jobs/agent-platform-spec-001/09_implementation_backlog.md` | NEW |
| `docs/ai/jobs/agent-platform-spec-001/10_acceptance_criteria.md` | NEW |
| `docs/ai/jobs/agent-platform-spec-001/patch.md` | NEW |

No other files. `request.ko.md` / `plan.md` / `codex-task.md` already exist; do NOT modify them.

## Style rules (every doc)

1. **언어**: 한국어 우선. 기술 식별자 (`AgentInput`, `OrderIntent`, `RiskEngine`, `BrokerOrder`, `KIS_ORDER_DRY_RUN`, `OrchestratorService`, `BrokerGatewayService`) 는 inline `code` 영어.
2. **운영자 readable**: 첫 문단에 영역 목적 + 안전 원칙.
3. **개발자 specific**: implementation backlog 으로 직접 변환 가능.
4. **형식**: Markdown. H1 = doc title, H2 = 섹션, H3 = 하위.
5. **길이**: doc 별 평균 200~700 줄.
6. **Cross-reference**: 다른 doc + `final-platform-plan/` 의 doc 을 명시 인용.
7. **TODO 표시**: 미확인은 `> **TODO**: ...`. 추측 0.
8. **No coding**: 실행 가능한 `.py` / `.ts` / SQL / Bash 0. pseudocode / 표 / ASCII 만.

## Mandatory safety invariants (every doc reaffirms)

각 design doc 의 첫 또는 마지막 섹션에 다음 5 가지 명시:

1. **Agent ≠ Broker.** `app/agents/*` 어떤 모듈도 `app.broker.*` import 0. broker 호출 0.
2. **OMS only executable.** Agent 는 `OrderIntent` 까지. OMS 만 `BrokerOrder` 생성.
3. **Broker Gateway Service only KIS-credentialed.** 다른 6 서비스는 KIS 자격증명 0.
4. **LLM 단독 hard risk block 해제 불가.** Pydantic validation + deterministic fallback 강제.
5. **live default lock.** 어떤 모듈도 `live_trading_enabled=True` set / `KIS_ORDER_DRY_RUN=false` toggle 0. "실전 전환 승인 에이전트" 도 locked.

## Per-document requirements

### `00_principles_and_boundaries.md`

- 위 5 invariant 설명.
- Agent / Strategy / RiskEngine / OMS / BrokerAdapter / KisBroker / PaperBroker 관계 ASCII 도식 + 7 서비스 boundary.
- Agent input source / output sink 표.
- Broker Gateway 격리 명문화.
- "거래 에이전트" broker 호출 0 / "비상정지 에이전트" 유일 mutation.
- 위반 시 review BLOCK.

### `01_seven_services.md`

- 7 서비스 각각의 책임 / 소속 모듈 / KIS 자격증명 (Broker Gateway 만 yes) / broker 호출 (Broker Gateway 만 yes) / 통신 패턴.
- ASCII 아키텍처 도식 — 7 서비스 박스 + 내부 RPC 화살표 + KIS 외부 박스. Broker Gateway 가 유일하게 KIS 와 직접 화살표.
- 통신 프로토콜 — loopback HTTP 또는 UNIX socket 권고. 내부 토큰. 외부 노출 0.
- Strategy Service → Broker Gateway: 유일 write 채널. `BrokerOrder` payload 만. OrderIntent 직접 전달 0.
- Orchestrator → 6 서비스: kill switch broadcast.
- 장애 시나리오 — 서비스 죽으면 fail-closed.
- **85 모듈 → 7 서비스 매핑 표 — 정확히 85 row.** 각 row: `# / 한국어 명칭 / 영어 alias / 카테고리 (실시간 핵심·뉴스 이벤트·검증 학습·운영 보안) / 소속 서비스`.

### `02_realtime_core_40_agents.md`

40 모듈. 각각 다음 표:

| 항목 | 내용 |
| --- | --- |
| # / 한국어 명칭 / 영어 alias | |
| 소속 서비스 | |
| 책임 (한 줄) | 운영자 readable |
| Input (typed) | 필드 / 타입 / source |
| Output (typed) | 필드 / 타입 / 다음 모듈 |
| Score / Confidence | 적용 + 범위 |
| Reasons / Blockers | 예시 |
| Provider | rule-based / LLM optional |
| Fallback | deterministic |
| Parse status | ok / malformed / timeout |
| 안전 가드 | read-only / Strategy 경계 / kill switch / dry-run |
| 의존 모듈 | |
| 다음 모듈 | |

권고 40 (Codex 가 보정 가능, 중복 금지):

오케스트레이터, 세션 관리, 데이터 수집, 데이터 정규화, 데이터 캐시, 데이터 무결성, 스캐너, 종목 universe, 종목 metadata, 호가 모니터, 거래량 모니터, 변동성 모니터, VWAP/세션 통계, ORB 분석, 추세 분석, 모멘텀 분석, 변동성 분석, 평균회귀 분석, 거시지표 분석, 산업/섹터 분석, 전략 선택, 신호 종합, 사전 리스크, 실시간 리스크, 포지션 사이징, 한도 관리, 진입 가격 산정, 손절가 산정, 익절가 산정, 거래 에이전트 (`IntentEmitterAgent`), 주문 검증, 주문 감시, 부분 체결 처리, 미체결 관리, 슬리피지 감시, 가격 추적, 포트폴리오 모니터, P&L 실시간, 리스크 이벤트 모니터, 모듈 헬스.

특히:

- **거래 에이전트 (#30)** — alias `IntentEmitterAgent`. broker 호출 0. `OrderIntent` → OMS 위임. Strategy Service 안.
- **사전/실시간 리스크 모듈 (#23,24)** — `RiskEngine` 의 input feed 또는 보조. 최종 `RiskVerdict` 는 RiskEngine 만.

### `03_news_event_10_agents.md`

10 모듈. 모두 read-only. 주문 0. 같은 표 형식.

권고: 뉴스 수집, 뉴스 분류, 뉴스 신뢰도 평가, 공시 모니터, 실적 발표 모니터, 거시 이벤트, 정정/구속력 이벤트, 가격 충격 추정, 뉴스 → 종목 매핑, 이벤트 알림 emit.

### `04_validation_learning_20_agents.md`

20 모듈. 모두 read-only. 주문 0. 같은 표 형식.

권고: 검증, 백테스트, 슬리피지 검증, 스프레드 검증, 체결 현실성 검증, 매매일지 분석, 일일 리포트, 주간 리포트, 전략 비교, 전략 성과 분해, 실패 원인 분류, 회귀 비교, 데이터 품질 검증, 신호 노이즈 분석, LLM 결과 검증 보조, 학습, 파라미터 튜닝 추천, 결정 트리 추출, 가설 검증, 결과 시각화.

**학습 모듈은 추천 (proposal) 만, 자동 적용 0** 명시.

### `05_ops_security_15_agents.md`

15 모듈. 같은 표 형식.

권고: 모니터링, 비상정지, 보안 (시크릿 leak grep), 시크릿 관리, 실계좌 잠금, 규정 체크, 세금 기록, 계좌 보호, 주문 감사, 장애 복구, 실전 전환 승인 (locked), 로그 회전/보관, 알림 라우팅, 운영자 명령 처리, 운영자 권한 관리.

특히:

- **비상정지** — kill switch set 유일 mutation. Orchestrator broadcast.
- **실계좌 잠금** — `live_trading_enabled=False` 강제.
- **실전 전환 승인** — locked / future-approval-gated. design 에서 활성화 권고 0.
- **시크릿 관리** — Broker Gateway 만 자격증명 수신.

### `06_top15_focus_set.md`

15 critical + 5 meta-agent.

각 모듈:

- 영어 alias.
- 소속 서비스.
- 위 02~05 doc 의 참조 (어느 카테고리).
- 우선순위 P0/P1/P2.
- 의존 모듈.
- 진입 순서 ASCII DAG.
- backlog item ID (`09_implementation_backlog.md` 와 1:1).

권고 진입 순서 (P0):

```
Orchestrator → Session Manager
  ├─ E-Stop Agent (가장 먼저 안전망)
  ├─ Data Agent
  │    └─ Scanner → News/Event → Analyst → Strategy Selector
  │         └─ Risk → Position Sizer → Trader (IntentEmitter) → Order Watcher
  ├─ Journal Agent
  ├─ Validation Agent
  └─ Learning/Report Agent
```

5 meta-agent P0 (위험 낮은 순): LLM 결과 검증 → Codex 테스트 → Claude 리뷰 → Claude 설계 → Codex 구현.

### `07_llm_provider_design.md`

- `LLMProvider` Protocol (pseudocode).
- Default: `DeterministicProvider`.
- Optional: `OpenAIProvider` / `AnthropicProvider` 추상 정의만. SDK import 0.
- Fallback chain: LLM A → LLM B (옵션) → deterministic.
- Pydantic validation 강제. malformed → 재시도 1 회 → deterministic fallback.
- Retry / timeout / cost-rate.
- 시크릿 격리 — 시크릿 매니저 (Ops & Security Service) 만 중개.
- LLM 출력은 hard risk block 풀 수 없음.
- `AgentTrace.provider_used` / `fallback_used` / `parse_status` 기록.

### `08_data_contracts.md`

Typed contracts 표:

- `AgentInput`.
- `AgentOutput` (score / confidence / reasons / blockers / metadata / trace).
- `AgentTrace` (provider_used / fallback_used / parse_status / duration / cost).
- `AgentLifecycleState` (enum).
- `KillSwitchCommand`.
- `AlertEvent`.
- `ServiceMessage` (7 서비스 간 RPC base).
- `OrderIntent` (기존 인용).
- `BrokerOrder` (기존 인용, Broker Gateway 수신 payload).

각 contract 의 필수/옵션 필드 + 기본값 + source + sink.

### `09_implementation_backlog.md`

표 형식. 정확히 **97 backlog item**:

- 85 모듈 (각 1 row).
- 7 서비스 (각 1 row — 서비스 골격 / 통신 / health check).
- 5 cross-cutting:
  - `agents-base-001` — `AgentBase` abstract + contracts.
  - `agents-llm-provider-001` — `LLMProvider` Protocol + deterministic.
  - `services-rpc-base-001` — 서비스 간 RPC base + auth.
  - `kill-switch-broadcast-001` — Orchestrator → 6 서비스 broadcast.
  - `agents-test-base-001` — agent / service 회귀 인프라.

| Job ID | Phase / 카테고리 | 소속 서비스 | Size | Purpose | 수정 파일 | 신규 파일 | 의존 backlog | Acceptance | Test plan | Risk | Rollback |

Size S/M/L. 시간 추정 0. Job ID 는 `agent-rt-XX`, `agent-news-XX`, `agent-val-XX`, `agent-ops-XX`, `service-XX`, `cross-XX` 같은 네임스페이스 권고.

마지막 섹션: prioritization logic (Top 15 + 5 = P0).

### `10_acceptance_criteria.md`

- 본 design acceptance — 12 파일 + 한국어 + invariant + 코드 0.
- 각 implementation job 공통 template:
  - `app/agents/<agent>/` 또는 `app/services/<service>/` 안에만 신규 코드.
  - `app.broker.*` import 0 (Broker Gateway 서비스 외).
  - `app.oms.*` 호출 단방향 (Strategy Service 안에서만).
  - typed I/O 테스트.
  - `AgentTrace` 회귀.
  - secret leak 0.
  - LLM optional + fallback 회귀.
  - kill switch 가드 회귀.
  - 서비스 간 통신 loopback 한정 회귀.
  - `commit / push / merge / deploy` 자동화 0.

## Verification steps

After writing the 11 docs, run:

```bash
ls -la projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/
# Expect 15 files: request.ko.md, plan.md, codex-task.md, 00_*.md ~ 10_*.md, patch.md
```

Safety grep (Codex pastes verbatim into patch.md):

```bash
grep -rnE "수익 보장|profit guarantee|승률 100|fake" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true
grep -rnE "Bearer eyJ|access_token=eyJ|appkey=PS" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true
grep -rnE "TTTT1002U|TTTT1006U|TTTS3035R|TTTS3018R" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true
grep -rnE "1 주 안에|2 주 안에|sprint|Q[1-4] 까지" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true
grep -rnE "^\s*(from|import)\s+app\.broker" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true
```

Expected: 1~4 번 grep 은 0 lines (또는 forbidden pattern 정의 자체 인용만). 5 번 grep 은 doc 본문에서 "사용하자" 권고 0.

Also count verification:

```bash
grep -c "^| [0-9]" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/02_realtime_core_40_agents.md  # ~40
grep -c "^| [0-9]" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/03_news_event_10_agents.md     # ~10
grep -c "^| [0-9]" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/04_validation_learning_20_agents.md  # ~20
grep -c "^| [0-9]" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/05_ops_security_15_agents.md  # ~15
```

Codex confirms counts in patch.md.

Do NOT run `pytest` / `compileall` / any `git` mutation.

## `patch.md` contents

Create `docs/ai/jobs/agent-platform-spec-001/patch.md` with these sections:

1. **Files Changed** — 12 신규 파일. `agent-platform-spec-001/` 외 0.
2. **Per-document summary** — doc 마다 1 단락 (purpose / key sections / 길이 / cross-references).
3. **Module count verification** — 각 카테고리 doc 의 모듈 수 (40 / 10 / 20 / 15 = 85). 합계 명시.
4. **7-service summary** — 7 서비스의 한 줄 책임 + 각 서비스의 KIS 자격증명 / broker 호출 여부.
5. **85 → 7 mapping check** — `01_seven_services.md` 매핑 표가 85 row 임을 확인.
6. **Top 15 + 5 focus set summary** — 우선순위 + 의존.
7. **Verification output** — `ls -la` + safety grep 5 종 + count grep 4 종 결과 (verbatim).
8. **Safety confirmation**:
   - `app/` / `tests/` / `scripts/` / `.env` / catalog 본문 modified 0.
   - 다른 job 디렉터리 (`final-platform-plan/` 포함) modified 0.
   - KIS endpoint / TR_ID / payload 추측 0.
   - 수익 보장 / 시간 추정 0.
   - live arming / activation 권고 0.
   - Agent → broker 직접 호출 권고 0.
   - Broker Gateway 외 다른 서비스 KIS 자격증명 권고 0.
   - 7 서비스 외부 노출 권고 0.
   - 실 secret / 계좌번호 / token 0.
   - `commit / push / merge / deploy` 수행 0.
9. **Remaining TODOs** — agent backlog 다음 진입 후보 + 본 design known gaps.
10. **Claude verification prompt** — paste this exact text:

    > Use prompts/claude.md.
    >
    > Project directory: /root/ai-dev-center/projects/ai-team/projects/paper-trading
    > Job ID: agent-platform-spec-001
    > Job directory: /root/ai-dev-center/projects/ai-team/projects/paper-trading/docs/ai/jobs/agent-platform-spec-001
    >
    > Review the agent-platform-spec-001 final design output (85 role modules + 7 execution services + Top 15+5 focus set).
    >
    > Read:
    > - request.ko.md
    > - plan.md
    > - codex-task.md
    > - patch.md
    > - 00_principles_and_boundaries.md ~ 10_acceptance_criteria.md
    >
    > Review focus:
    > 1. 11 design docs + patch.md exist (12 files total). Only `agent-platform-spec-001/` modified.
    > 2. All 11 docs are in Korean.
    > 3. Each doc covers plan.md "필수 포함" items.
    > 4. Every doc reaffirms 5 safety invariants (Agent ≠ Broker, OMS only executable, Broker Gateway only KIS-credentialed, LLM not in hard risk block, live default lock).
    > 5. 02 (40 modules), 03 (10), 04 (20), 05 (15) categories sum to exactly 85 modules.
    > 6. 01_seven_services.md has exactly 85 module-to-service mapping rows + 7 service definitions.
    > 7. 06 covers exactly 15 critical + 5 meta-agent.
    > 8. 09 has 97 backlog items (85 + 7 + 5).
    > 9. No application code / tests / `.env` / catalog content / other job dir modified.
    > 10. No KIS endpoint / TR ID / payload / response field invented.
    > 11. No live trading activation suggested. "실전 전환 승인 에이전트" locked / future-approval-gated.
    > 12. No profit guarantee / win-rate / time-estimate claims.
    > 13. No real secret / app key / account number / Bearer token written.
    > 14. "거래 에이전트" documented as broker-call-free (`IntentEmitterAgent`).
    > 15. "비상정지 에이전트" documented as only mutation-permitted (kill_switch_engaged set).
    > 16. Broker Gateway Service is documented as the sole KIS-credentialed service. No other service holds credentials or calls KIS API.
    > 17. 7 services communicate via loopback / UNIX socket only. No external public endpoint added.
    > 18. Strategy → Risk → OMS → BrokerAdapter boundary preserved.
    > 19. `commit / push / merge / deploy` automation 0.
    >
    > Verdict must be one of: APPROVE / REQUEST CHANGES / BLOCK.
    >
    > If REQUEST CHANGES or BLOCK, write a Follow-up Codex Prompt that fixes only the required issues. Do not expand scope.

11. **Follow-up Codex prompt rules** (only if Claude returns REQUEST CHANGES or BLOCK):

    - Codex reads: `request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, `review.md`.
    - Apply Required Fixes only.
    - Do not expand beyond `agent-platform-spec-001/`.
    - Update `patch.md` with `## Follow-up <N>` section.
    - Do not modify `app/` / `tests/` / `scripts/` / `.env` / catalog / other job dirs.
    - Do not commit / push / merge / deploy.
    - Do not modify secrets.

12. **Status footer**: `READY FOR REVIEW`.

Stop. Do not commit, push, merge, deploy, or modify any file outside `docs/ai/jobs/agent-platform-spec-001/`. Hand off to the human.
