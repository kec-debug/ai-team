## 1. Files Changed

Created 12 files inside `projects/paper-trading/docs/ai/jobs/final-platform-plan/`:

- `00_current_state.md`
- `01_product_spec.md`
- `02_ui_ux_spec.md`
- `03_paper_training_runtime.md`
- `04_agent_strategy_pipeline.md`
- `05_live_validation_console.md`
- `06_api_data_storage.md`
- `07_risk_safety_observability.md`
- `08_runbook.md`
- `09_implementation_backlog.md`
- `10_acceptance_criteria.md`
- `patch.md`

No file outside `final-platform-plan/` was created or modified by this job.

## 2. Per-document summary

`00_current_state.md` establishes the ground truth at commit `3812144 add paper trading use-ready operations`, including 557 passed baseline, app/runtime/broker/OMS/risk/portfolio/strategy/API/config inventories, scripts/docs inventory, 14 known issues, and current safety guard summary. It anchors all later docs.

`01_product_spec.md` defines the ten product areas: Overview Dashboard, Paper Training, Agent Research, Strategy Lab, Orders/Fills, Portfolio, Reports/Analytics, Live Validation Console, Risk/Ops/Settings, and Runbook/Incident View. Each area includes definition, user use cases, implemented state, missing scope, and dependencies.

`02_ui_ux_spec.md` describes the operator dashboard UX, including safety banner escalation, paper/live status visibility, live locked area, paper training controls, Agent evidence/confidence/blockers, Strategy candidate visibility, Risk/session/stale/spread guard visibility, and orders/fills/journal/PnL cards.

`03_paper_training_runtime.md` designs the 24h paper training service mode without implying 24h trading. It covers TrainingRunner structure, universe/watchlist, session-aware behavior, replay/synthetic/live quote sources, TrainingRun aggregation, closed-market behavior, and ten safety guards.

`04_agent_strategy_pipeline.md` defines the Agent + Strategy pipeline, seven Agent types, typed output contract, optional LLM provider with deterministic fallback, malformed-output validation block, and the Strategy boundary that prevents direct broker calls.

`05_live_validation_console.md` designs a separate locked live console. It covers readiness checklist extension, state machine, `live_validation_ready` as UX signal only, lock sections, forbidden live UI controls, and future approval boundary.

`06_api_data_storage.md` specifies existing and future API surfaces, data models, state machines, PostgreSQL tables, Redis keys, file/JSON fallback, replay, rehydrate, and crash recovery. Future endpoints are marked as design backlog, not current implementation.

`07_risk_safety_observability.md` catalogs safety guards and observability cards/metrics. It covers global/paper/live kill switch, daily loss, notional, order count, stale quote, spread, volatility, session, idempotency, broker disconnect, token expiry, live arming, manual approval, allowlist, market order, dry-run, and mode mismatch guards.

`08_runbook.md` extends the current `docs/RUNBOOK.md` with final-platform procedures: paper training, strategy addition, universe/watchlist changes, Agent provider change, LLM fallback, stale quote, broker disconnect, token expiration, rejection handling, kill switch, live checklist, rollback, dashboard troubleshooting, tmux, and PuTTY tunnel.

`09_implementation_backlog.md` translates the design into future Codex-ready backlog items using qualitative S/M/L sizing only. It includes runtime, domain, source adapter, session, Agent, Strategy Lab, Live Console, Storage, Risk, Observability, Reports, Ops, Soak, and staging-profile jobs.

`10_acceptance_criteria.md` defines acceptance for this design set and a common future-job acceptance template covering pytest, safety grep, protected areas, secret handling, git automation, Strategy/Agent boundaries, OMS/RiskEngine boundary, `OrderType`, FX, Korean docs, KIS catalog, and live locked principles.

## 3. Verification output

Directory listing after creating the 11 design docs:

```text
$ ls -la projects/paper-trading/docs/ai/jobs/final-platform-plan/
total 140
drwxr-xr-x  2 root root  4096 May 20 11:58 .
drwxr-xr-x 19 root root  4096 May 20 11:47 ..
-rw-r--r--  1 root root  6837 May 20 11:57 00_current_state.md
-rw-r--r--  1 root root  5633 May 20 11:57 01_product_spec.md
-rw-r--r--  1 root root  5222 May 20 11:57 02_ui_ux_spec.md
-rw-r--r--  1 root root  4243 May 20 11:57 03_paper_training_runtime.md
-rw-r--r--  1 root root  4287 May 20 11:57 04_agent_strategy_pipeline.md
-rw-r--r--  1 root root  2948 May 20 11:57 05_live_validation_console.md
-rw-r--r--  1 root root  7295 May 20 11:57 06_api_data_storage.md
-rw-r--r--  1 root root  4331 May 20 11:58 07_risk_safety_observability.md
-rw-r--r--  1 root root  4449 May 20 11:58 08_runbook.md
-rw-r--r--  1 root root  4581 May 20 11:58 09_implementation_backlog.md
-rw-r--r--  1 root root  2291 May 20 11:58 10_acceptance_criteria.md
-rw-r--r--  1 root root 17621 May 20 11:52 codex-task.md
-rw-r--r--  1 root root 23220 May 20 11:50 plan.md
-rw-r--r--  1 root root  4098 May 20 11:47 request.ko.md
```

Safety grep 1:

```text
$ grep -rnE "수익 보장|profit guarantee|승률 100|fake" projects/paper-trading/docs/ai/jobs/final-platform-plan/ || true
projects/paper-trading/docs/ai/jobs/final-platform-plan/plan.md:32:- 수익 보장 / 거짓 성과 주장 / 과장된 승률 주장.
projects/paper-trading/docs/ai/jobs/final-platform-plan/plan.md:486:### 5.2 No fake claims
projects/paper-trading/docs/ai/jobs/final-platform-plan/plan.md:488:- 수익 보장 / 거짓 성과 / 과장된 승률 표현 0.
projects/paper-trading/docs/ai/jobs/final-platform-plan/plan.md:490:- 백테스트 / paper 결과는 "검증 데이터" 로만 기술. "수익 보장" 으로 기술 금지.
projects/paper-trading/docs/ai/jobs/final-platform-plan/plan.md:528:7. 수익 보장 / 시간 추정 / 거짓 성과 0.
projects/paper-trading/docs/ai/jobs/final-platform-plan/plan.md:538:- 수익 보장 / 시간 추정 / KIS endpoint 추측 / live arming 0.
projects/paper-trading/docs/ai/jobs/final-platform-plan/codex-task.md:23:- Do not include profit guarantees, fake win-rate claims, exaggerated performance promises, or anything resembling marketing copy.
projects/paper-trading/docs/ai/jobs/final-platform-plan/codex-task.md:28:- Do not write fake / fabricated test results. If asked for a test count, cite the current `pytest -p no:cacheprovider` result from a recent log only (do NOT re-run).
projects/paper-trading/docs/ai/jobs/final-platform-plan/codex-task.md:264:- 보안 원칙 준수 (수익 보장 / 시간 추정 / KIS 추측 / live arming 0).
projects/paper-trading/docs/ai/jobs/final-platform-plan/codex-task.md:298:grep -rnE "수익 보장|profit guarantee|승률 100|fake" projects/paper-trading/docs/ai/jobs/final-platform-plan/ || true
projects/paper-trading/docs/ai/jobs/final-platform-plan/codex-task.md:349:   > 7. No profit guarantee / win-rate / time-estimate claims.
projects/paper-trading/docs/ai/jobs/final-platform-plan/request.ko.md:29:- 수익 보장 / 거짓 성과 주장 / 과장된 승률 주장 0.
projects/paper-trading/docs/ai/jobs/final-platform-plan/request.ko.md:69:- 수익 보장 / 거짓 성과 주장.
```

These matches are only in existing `request.ko.md`, `plan.md`, and `codex-task.md` where the forbidden patterns are quoted as prohibitions or grep commands. The generated 00-10 docs avoid those exact claims.

Safety grep 2:

```text
$ grep -rnE "Bearer eyJ|access_token=eyJ|appkey=PS" projects/paper-trading/docs/ai/jobs/final-platform-plan/ || true
projects/paper-trading/docs/ai/jobs/final-platform-plan/codex-task.md:299:grep -rnE "Bearer eyJ|access_token=eyJ|appkey=PS" projects/paper-trading/docs/ai/jobs/final-platform-plan/ || true
```

This match is the existing verification command in `codex-task.md`; no generated design doc includes a token or credential.

Safety grep 3:

```text
$ grep -rn "TTTS3035R\|TTTS3018R\|TTTT3039R\|TTTT1002U\|TTTS1003U" projects/paper-trading/docs/ai/jobs/final-platform-plan/ || true
projects/paper-trading/docs/ai/jobs/final-platform-plan/codex-task.md:300:grep -rn "TTTS3035R\|TTTS3018R\|TTTT3039R\|TTTT1002U\|TTTS1003U" projects/paper-trading/docs/ai/jobs/final-platform-plan/ || true
```

This match is the existing verification command in `codex-task.md`; no generated design doc invents or cites these values.

Safety grep 4:

```text
$ grep -rn "1 주 안에\|2 주 안에\|sprint\|Q1 까지\|Q2 까지" projects/paper-trading/docs/ai/jobs/final-platform-plan/ || true
projects/paper-trading/docs/ai/jobs/final-platform-plan/plan.md:33:- 시간 추정 ("2 주 안에 완료" 같은 표현 금지).
projects/paper-trading/docs/ai/jobs/final-platform-plan/plan.md:494:- "1주 내", "2 sprint", "Q1 까지" 같은 시간 표현 0.
projects/paper-trading/docs/ai/jobs/final-platform-plan/codex-task.md:24:- Do not include time estimates ("2 sprints", "Q1 까지", "1 주 안에 완료" etc.). Backlog sizing is qualitative (S/M/L or dependency stage) only.
projects/paper-trading/docs/ai/jobs/final-platform-plan/codex-task.md:301:grep -rn "1 주 안에\|2 주 안에\|sprint\|Q1 까지\|Q2 까지" projects/paper-trading/docs/ai/jobs/final-platform-plan/ || true
```

These matches are only in existing `plan.md` and `codex-task.md` as prohibited examples or verification commands. The generated 00-10 docs use only qualitative S/M/L sizing and no date/time promises.

## 4. Safety confirmation

- No `app/`, `tests/`, `scripts/`, `.env`, `.env.example`, catalog body, `README.md`, `docs/RUNBOOK.md`, or `docs/OPS_AUDIT.md` file was modified.
- No file outside `projects/paper-trading/docs/ai/jobs/final-platform-plan/` was created or modified.
- No KIS endpoint, TR ID, request payload, header, or response field was invented.
- No profit guarantee, fabricated performance claim, or time estimate was added to generated 00-10 docs.
- No live arming or activation was suggested as current functionality.
- No real app key, app secret, account number, access token, or Bearer token was written.
- No `commit`, `push`, `merge`, PR, or deploy was performed.

## 5. Remaining TODOs

- Claude review should verify coverage of every `plan.md` "필수 포함" item.
- If approved, the next implementation step starts by selecting one item from `09_implementation_backlog.md`.
- The design intentionally leaves storage schema DDL, Agent prompts, live arm implementation, and KIS unknown catalog values as future jobs.

## 6. Claude verification prompt

Use prompts/claude.md.

Project directory: /root/ai-dev-center/projects/ai-team/projects/paper-trading
Job ID: final-platform-plan
Job directory: /root/ai-dev-center/projects/ai-team/projects/paper-trading/docs/ai/jobs/final-platform-plan

Review the final-platform-plan design output.

Read:
- request.ko.md
- plan.md
- codex-task.md
- patch.md
- 00_current_state.md ~ 10_acceptance_criteria.md

Review focus:
1. 11 design docs + patch.md exist (12 files total).
2. All 11 design docs are in Korean.
3. Each doc covers the plan.md "필수 포함" items.
4. No application code / tests / `.env` / catalog content modified.
5. No KIS endpoint / TR ID / payload / response field invented.
6. No live trading activation suggested.
7. No profit guarantee / win-rate / time-estimate claims.
8. No real secret / app key / app secret / account number / Bearer token written.
9. Strategy → RiskEngine → OMS → BrokerAdapter boundary preserved in all docs.
10. Agent / LLM 의 broker 직접 호출 0.
11. live default lock + manual approval principle preserved.
12. No `commit / push / merge / deploy` automation suggested.

Verdict must be one of: APPROVE / REQUEST CHANGES / BLOCK.

If REQUEST CHANGES or BLOCK, write a Follow-up Codex Prompt that fixes only the required issues. Do not expand scope.

## 7. Conditional follow-up Codex prompt rule

Use only if Claude returns REQUEST CHANGES or BLOCK:

- Codex must read `request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, and `review.md`.
- Apply Required Fixes only.
- Do not expand beyond `final-platform-plan/`.
- Update `patch.md` with `## Follow-up <N>`.
- Do not modify `app/`, `tests/`, `scripts/`, `.env`, `.env.example`, catalog body, README, RUNBOOK, OPS_AUDIT, or other job directories.
- Do not commit, push, merge, deploy, or modify secrets.

READY FOR REVIEW
