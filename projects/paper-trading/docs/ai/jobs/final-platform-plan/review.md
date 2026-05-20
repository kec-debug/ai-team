# final-platform-plan — Claude Review

## Verdict

APPROVE

## Summary

final-platform-plan 은 design-documentation only 작업으로 **12 개 신규 파일** (`00_current_state.md` ~ `10_acceptance_criteria.md` + `patch.md`) 을 `projects/paper-trading/docs/ai/jobs/final-platform-plan/` 안에 정확히 생성했다. application 코드 / 테스트 / `.env` / catalog 본문 / 다른 job 디렉터리 무변동. KIS endpoint 추측 0 / 수익 보장 0 / 시간 추정 0 / live arming 0 / secret 노출 0. 11 design 문서 모두 한국어이며 plan §4 의 "필수 포함" 을 충족한다.

## Scope of changes

**In-scope (final-platform-plan 이 생성한 12 파일)**:

| # | 파일 | 줄 수 | 핵심 |
| --- | --- | --- | --- |
| 1 | `00_current_state.md` | 124 | 현재 commit `3812144` 시점 ground truth + pytest 557 passed + 인벤토리 + known issues |
| 2 | `01_product_spec.md` | 133 | 10 영역 product structure + 영역별 use case + 의존관계 |
| 3 | `02_ui_ux_spec.md` | 103 | 운영용 dashboard (ASCII wireframe) + 3 단 safety banner + 영역별 grid |
| 4 | `03_paper_training_runtime.md` | 112 | 24h TrainingRunner + Session Router + 3 종 DataSource + 10 안전 가드 |
| 5 | `04_agent_strategy_pipeline.md` | 126 | 7 종 Agent (typed input/output) + LLM provider + deterministic fallback + Strategy boundary |
| 6 | `05_live_validation_console.md` | 77 | locked live console + 14 항 readiness checklist + arm/disarm locked state machine |
| 7 | `06_api_data_storage.md` | 120 | API endpoint surface (기존 + 신규) + 도메인 모델 + Postgres/Redis/file 3 층 storage |
| 8 | `07_risk_safety_observability.md` | 100 | 19 종 safety guard + 13 종 observability card |
| 9 | `08_runbook.md` | 134 | 운영자 runbook (RUNBOOK.md 확장) + incident response + tmux / PuTTY 가이드 |
| 10 | `09_implementation_backlog.md` | 40 | 20 backlog item (table 형식, S/M/L size, 시간 추정 없음) |
| 11 | `10_acceptance_criteria.md` | 52 | 본 design 의 acceptance + 후속 job template |
| 12 | `patch.md` | 182 | 생성 보고 + 4 종 안전 grep 결과 + Claude review prompt + follow-up 규칙 |

**Out-of-scope, untouched (정확히 보호됨)**:

- `app/` 의 어떤 파일도 modify/create/delete 0 (git diff stat 의 `M app/config.py` / `?? app/ops/` 는 live-validation-001 의 commit 대기 잔재 — patch.md §3 정확히 분류).
- `tests/` / `scripts/` / `.env` / `.env.example` / `README.md` / `docs/RUNBOOK.md` / `docs/OPS_AUDIT.md` / `docs/kis/MISSING_OFFICIAL_VALUES.md` / `docs/kis/MISSING_MARKET_DATA_VALUES.md` 무변동.
- 다른 job 디렉터리 (`docs/ai/jobs/<other>/`) 무변동.

## Review focus 항목별 검증

### 1. 12 files exist — OK

`ls docs/ai/jobs/final-platform-plan/` 결과: `00_*.md` ~ `10_*.md` (11) + `patch.md` (1) + 기존 메타 3 개 (`request.ko.md` / `plan.md` / `codex-task.md`) = 15 total. **12 신규** 정확히 생성됨.

### 2. 11 design docs Korean — OK

모든 doc 의 H1 / H2 / H3 헤더가 한국어 (예: `# 00. 현재 상태 기준선`, `## 1. 핵심 운영 상태`, `## 2. Readiness checklist`). 기술 식별자 (`OrderIntent`, `RiskEngine`, `KIS_ORDER_DRY_RUN`) 는 inline `code` 로 영어 그대로 — codex-task §"Style rules" 정확히 준수.

### 3. plan.md 의 "필수 포함" 충족 — OK

스팟 체크:

- `00_current_state.md` — commit hash `3812144` + pytest 557 baseline + Strategy/Risk/OMS/Broker 경계 명시 + 운영 도구 (`scripts/use_ready_check.sh`, `docs/RUNBOOK.md`, `docs/OPS_AUDIT.md`) 인용.
- `02_ui_ux_spec.md` — ASCII wireframe 구현됨 (line 26-36+), 3 단 safety banner / left nav 10 영역 / status grid / selected workspace + raw JSON 영역.
- `05_live_validation_console.md` — 14 항 readiness table (line 17-30+) 이 live-validation-001 의 항목과 정합. "live default locked" / "주문 버튼 없음" / "arm/disarm 은 future job 의 locked state machine" 명시.
- `09_implementation_backlog.md` — 20 개 backlog item (plan §4.10 의 "최소 15 개" 초과). 모든 row 가 Size 컬럼에 S/M/L (시간 추정 없음). `paper-runtime-002-training-service` / `agent-001-base` / `agent-003-llm-provider` / `live-console-001-separated-page` / `storage-001-postgres-model` 등 plan §4.10 의 분류 8 영역 (Runtime / Agent / Strategy / Live / Storage / Risk / Observability / Ops) 모두 커버.

### 4. application code / tests / `.env` / catalog 본문 무변동 — OK

`git status --short` (root):

```text
 M projects/paper-trading/app/config.py     ← live-validation-001 잔재
?? projects/paper-trading/app/ops/           ← live-validation-001 잔재
?? projects/paper-trading/docs/ai/jobs/final-platform-plan/   ← 본 job
```

final-platform-plan 은 `docs/ai/jobs/final-platform-plan/` 디렉터리만 untracked 로 생성. `app/config.py` / `app/ops/` 는 commit `ebeb635` 이전의 live-validation-001 작업 잔재로 patch.md §3 정확히 분류. final-platform-plan 자체가 추가한 application 파일 0.

### 5. KIS endpoint / TR ID / payload / response field 추측 0 — OK

`grep -rn "TTTS3035R\|TTTS3018R\|TTTT3039R\|TTTT1002U\|TTTS1003U" docs/ai/jobs/final-platform-plan/`:

- `patch.md:103` — safety grep 명령 자체의 인용 (forbidden pattern 정의).
- `codex-task.md:300` — Codex 지시문의 forbidden pattern 정의.

11 design 문서 본문 (`00_*.md` ~ `10_*.md`) 안에는 0 lines. KIS 인용은 모두 catalog 의 `Confirmed: yes` 행 reference (필드 명시 없이 §번호만).

### 6. live trading activation 0 — OK

- `05_live_validation_console.md` 가 "현재 시스템은 live locked 상태이며, `live_validation_ready` 는 UX 신호일 뿐 코드 게이트를 해제하지 않는다." 명시.
- `09_implementation_backlog.md` 의 `live-console-002-arm-state-locked` item 이 "no order path" acceptance + "accidental arm" risk note 로 잠금.
- backlog table 의 prioritization logic §"Live console remains locked until paper evidence and observability improve" 명시.
- 본문 어디에도 `LIVE_TRADING_ENABLED=true` / `kis_order_dry_run=false` / `ALLOW_MARKET_ORDERS=true` 활성화 권고 0.

### 7. 수익 보장 / 승률 / 시간 추정 0 — OK

`grep -rnE "수익 보장|profit guarantee|승률 100|fake"` 결과: `patch.md` + `plan.md` 의 forbidden pattern 정의 / 안전 grep 명령 인용만. 11 design 문서 본문 0 lines.

`grep -rnE "1 주 안에|2 주 안에|sprint|Q1 까지|Q2 까지"` 결과: 동일하게 `patch.md` + `plan.md` + `codex-task.md` 의 forbidden pattern 정의만. 11 design 문서 본문 0 lines.

### 8. secret / 계좌번호 / token / Bearer 0 — OK

`grep -rnE "Bearer eyJ|access_token=eyJ|appkey=PS"` 결과: `patch.md:94` (안전 grep 명령 인용) + `codex-task.md:299` (forbidden pattern) 만. 11 design 문서 본문 0 lines.

### 9. Strategy → RiskEngine → OMS → BrokerAdapter 경계 보존 — OK

- `00_current_state.md:7` — "주문 경계: `Strategy` -> `RiskEngine` -> `OMS` -> `BrokerAdapter`".
- `04_agent_strategy_pipeline.md` — pipeline flow 가 동일 경계 명시 + "broker 직접 호출 0" / "candidate / non-executable intent 까지만" 재확인.
- `09_implementation_backlog.md:40` — "Every backlog job must preserve Strategy -> RiskEngine -> OMS -> BrokerAdapter."

### 10. Agent / LLM 의 broker 직접 호출 0 — OK

`04_agent_strategy_pipeline.md` 가 다음 모두 명시:

- LLM 단독 risk block 해제 불가.
- malformed LLM output → Pydantic validation block.
- LLM failure → deterministic fallback.
- Agent 가 broker 직접 호출 0.
- non-executable intent 까지만.

### 11. live default lock + manual approval 보존 — OK

- `05_live_validation_console.md §1` 의 6 가지 핵심 원칙 — "Live 는 default locked" / "manual approval 없이는 armed 상태가 될 수 없다" / "주문 버튼 없음".
- `06_api_data_storage.md` 의 `/live/arm` endpoint 가 "locked + manual approval" authority 명시 (기대).
- `09_implementation_backlog.md` 의 `live-console-002-arm-state-locked` 가 "no order path" acceptance.

### 12. `commit / push / merge / deploy` 자동화 0 — OK

- 어떤 doc 도 자동 git ops 권고 0.
- `08_runbook.md` 는 RUNBOOK.md 의 git 운영 원칙 (`git add -A` 금지) 와 정합.
- `10_acceptance_criteria.md` 의 후속 job template 이 "commit / push / merge / deploy 자동화 0" 강제.

## Safety regression (모두 OK)

| 항목 | 결과 |
| --- | --- |
| 12 design + patch 파일 생성 (정확) | OK |
| 모든 design doc 한국어 | OK |
| 운영자 / 개발자 양측 readable | OK |
| application 코드 0 line 추가 | OK |
| `app/` / `tests/` / `scripts/` / `.env` / catalog 본문 무변동 | OK |
| 다른 job 디렉터리 무변동 | OK |
| KIS endpoint / TR ID / payload / response field 추측 0 | OK (live TR_ID 0 lines, 본문에) |
| 수익 보장 / 승률 / 거짓 성과 표현 0 | OK |
| 시간 추정 (sprint / Q1 / 1주 등) 0 | OK |
| 실 secret / 계좌번호 / token / Bearer 노출 0 | OK |
| live trading activation / live arming 권고 0 | OK |
| Strategy → RiskEngine → OMS → BrokerAdapter 경계 명시 (다수 doc) | OK |
| Agent / LLM 단독 risk block 해제 불가 명시 | OK |
| live default lock + manual approval 원칙 보존 | OK |
| 09 의 20 backlog item ≥ plan §4.10 최소 15 | OK |
| 09 의 모든 item 이 S/M/L Size 만 (시간 추정 없음) | OK |
| `commit / push / merge / deploy` 자동화 권고 0 | OK |
| patch.md 가 Claude verification prompt + follow-up 규칙 포함 | OK |

## Findings (severity 순)

### F1 (INFO) — `app/config.py` 와 `app/ops/` 의 dirty 는 final-platform-plan 외 잔재

patch.md §3 가 정확히 분류: "Current dirty app files in git status are pre-existing: `M app/config.py`, `?? app/ops/`". 이는 live-validation-001 의 commit 대기 잔재이며 final-platform-plan 이 추가한 것 아님. 사용자가 logical commit 분리 시 두 영역을 섞지 않도록 권고.

### F2 (INFO) — 09_implementation_backlog 의 wide table 형식

09 의 줄 수가 40 으로 짧지만 단일 table 안에 20 rows × 10 columns. 시간 추정 0 / S-M-L 만 사용 / 모든 backlog 가 Strategy→Risk→OMS→Broker 경계 보호 / live 활성화 격리. 본 review 의 결정에 영향 없음.

### F3 (INFO) — pytest 미실행은 의도된 선택

patch.md §4 "No compileall/pytest run, per codex-task.md: documentation-only job with no application code changes." codex-task §"Verification steps" 가 "Do NOT run `pytest` or `compileall` — this job adds zero application code" 로 강제. 정확한 처리.

## Final Checklist

| 항목 | 결과 |
| --- | --- |
| 1. 12 files exist (11 design + patch) | OK |
| 2. All 11 docs in Korean | OK |
| 3. plan.md "필수 포함" 충족 | OK |
| 4. application code / tests / `.env` / catalog 무변동 | OK |
| 5. KIS endpoint / TR ID / payload / response field 추측 0 | OK |
| 6. live trading activation 권고 0 | OK |
| 7. 수익 보장 / 승률 / 시간 추정 0 | OK |
| 8. secret / 계좌번호 / token / Bearer 0 | OK |
| 9. Strategy → RiskEngine → OMS → BrokerAdapter 경계 다수 doc 명시 | OK |
| 10. Agent / LLM 의 broker 직접 호출 0 | OK |
| 11. live default lock + manual approval 보존 | OK |
| 12. commit / push / merge / deploy 자동화 권고 0 | OK |

## Follow-up Codex prompt

없음. APPROVE.

다음 단계는 사용자가 직접:

1. (선택) `git diff` / `git status` 로 변경 범위 검토.
2. commit 권고 (final-platform-plan 디렉터리만 single commit 으로):

   ```bash
   git add projects/paper-trading/docs/ai/jobs/final-platform-plan/
   git commit -m "docs: final platform design (00-10) + plan/codex-task/patch/review"
   ```

3. pre-existing dirty 잔재 (`M app/config.py` / `?? app/ops/`) 는 별 commit 으로 분리 (live-validation-001 잔재 — 본 review 와 무관).

4. **다음 step (개발 작업)**: `09_implementation_backlog.md` 의 20 backlog item 중 우선순위 (1. domain/runtime 모델 → 2. source adapter → 3. agent base → 4. storage → 5. live console (locked 유지)) 에 따라 선택. 각 backlog 는 별 Codex job 으로 진행.

5. **live activation 은 본 series 에 포함되지 않음.** `live-console-001/002` backlog 도 "locked" / "no order path" acceptance — 실제 활성화는 명시적 사용자 승인 + Phase 5 안전 절차 충족 후 future job 으로만.

push / PR / merge / deploy 는 명시적 사용자 승인 후 수동. 본 review 자체는 코드 / catalog / `.env` / GUI 무변동, commit / push / merge / deploy 수행 없음.
