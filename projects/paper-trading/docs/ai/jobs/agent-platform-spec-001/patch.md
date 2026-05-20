# agent-platform-spec-001 — Codex Patch

## Files Changed

Created exactly 12 new files inside `projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/`:

1. `00_principles_and_boundaries.md`
2. `01_seven_services.md`
3. `02_realtime_core_40_agents.md`
4. `03_news_event_10_agents.md`
5. `04_validation_learning_20_agents.md`
6. `05_ops_security_15_agents.md`
7. `06_top15_focus_set.md`
8. `07_llm_provider_design.md`
9. `08_data_contracts.md`
10. `09_implementation_backlog.md`
11. `10_acceptance_criteria.md`
12. `patch.md`

No application code, tests, scripts, `.env`, KIS catalog, README/RUNBOOK/OPS_AUDIT, or other job directory files were modified for this job. Existing dirty application/test files in the working tree predate this docs-only job and were not touched.

## Scope Summary

- Produced Korean design documentation for 85 role modules grouped into 7 execution services.
- Preserved the final-platform safety boundary: Agent ≠ Broker, OMS-only executable order creation, Broker Gateway-only KIS credential custody, deterministic LLM fallback, and live default lock.
- `01_seven_services.md` includes the 7-service boundary, internal loopback/UNIX-socket communication rule, kill switch propagation, fail-closed scenarios, and the 85-module service mapping.
- `02`~`05` define the 40 real-time core, 10 news/event, 20 validation/learning, and 15 ops/security modules.
- `06_top15_focus_set.md` defines the Top 15 critical + 5 Claude/Codex meta-agent entry set with P0 priority and matching backlog IDs.
- `07_llm_provider_design.md` keeps LLM optional, schema-validated, and unable to release hard risk blocks.
- `08_data_contracts.md` defines typed contracts and preserves existing `OrderIntent` / `BrokerOrder` boundaries.
- `09_implementation_backlog.md` contains exactly 97 backlog rows: 85 modules + 7 services + 5 cross-cutting jobs.
- `10_acceptance_criteria.md` defines design and future implementation acceptance.

## Count Verification

| Check | Result |
| --- | --- |
| 85 module mapping rows in `01_seven_services.md` | 85 |
| Real-time core rows in `02_realtime_core_40_agents.md` | 40 |
| News/event rows in `03_news_event_10_agents.md` | 10 |
| Validation/learning rows in `04_validation_learning_20_agents.md` | 20 |
| Ops/security rows in `05_ops_security_15_agents.md` | 15 |
| Backlog rows in `09_implementation_backlog.md` | 97 |

## Verification Output

```text
$ ls -la projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/
total 164
drwxr-xr-x  2 root root  4096 May 20 13:34 .
drwxr-xr-x 20 root root  4096 May 20 13:03 ..
-rw-r--r--  1 root root  5106 May 20 13:27 00_principles_and_boundaries.md
-rw-r--r--  1 root root 11680 May 20 13:27 01_seven_services.md
-rw-r--r--  1 root root 10712 May 20 13:29 02_realtime_core_40_agents.md
-rw-r--r--  1 root root  4059 May 20 13:29 03_news_event_10_agents.md
-rw-r--r--  1 root root  6401 May 20 13:29 04_validation_learning_20_agents.md
-rw-r--r--  1 root root  5251 May 20 13:29 05_ops_security_15_agents.md
-rw-r--r--  1 root root  4477 May 20 13:30 06_top15_focus_set.md
-rw-r--r--  1 root root  3362 May 20 13:30 07_llm_provider_design.md
-rw-r--r--  1 root root  4540 May 20 13:30 08_data_contracts.md
-rw-r--r--  1 root root 19077 May 20 13:32 09_implementation_backlog.md
-rw-r--r--  1 root root  3313 May 20 13:32 10_acceptance_criteria.md
-rw-r--r--  1 root root 20141 May 20 13:20 codex-task.md
-rw-r--r--  1 root root  9656 May 20 13:34 patch.md
-rw-r--r--  1 root root 20340 May 20 13:18 plan.md
-rw-r--r--  1 root root  6824 May 20 13:11 request.ko.md
```

Safety grep from the task, verbatim. Matches are in pre-existing `request.ko.md`, `plan.md`, or `codex-task.md` instructions/self-references, not in the newly generated `00`~`10` design docs.

```text
$ grep -rnE "수익 보장|profit guarantee|승률 100|fake" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/plan.md:59:- 수익 보장 / 거짓 성과 / 과장된 승률 / 시간 추정.
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/plan.md:295:### 5.2 No fake claims / no time estimates
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/plan.md:297:- 수익 보장 / 승률 / 시간 추정 0.
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/plan.md:327:7. 수익 보장 / 시간 추정 / 거짓 성과 0.
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/plan.md:346:- 수익 보장 / 시간 추정 / KIS endpoint 추측 / live arming 0.
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/codex-task.md:23:- Do not include profit guarantees, fake win-rate claims, or marketing copy.
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/codex-task.md:254:grep -rnE "수익 보장|profit guarantee|승률 100|fake" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/codex-task.md:291:   - 수익 보장 / 시간 추정 0.
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/codex-task.md:328:    > 12. No profit guarantee / win-rate / time-estimate claims.
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/request.ko.md:108:- 수익 보장 / 거짓 성과 / 과장된 승률 표현.

$ grep -rnE "Bearer eyJ|access_token=eyJ|appkey=PS" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/codex-task.md:255:grep -rnE "Bearer eyJ|access_token=eyJ|appkey=PS" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true

$ grep -rnE "TTTT1002U|TTTT1006U|TTTS3035R|TTTS3018R" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/codex-task.md:256:grep -rnE "TTTT1002U|TTTT1006U|TTTS3035R|TTTS3018R" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true

$ grep -rnE "1 주 안에|2 주 안에|sprint|Q[1-4] 까지" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/codex-task.md:24:- Do not include time estimates ("2 sprints", "Q1 까지", "1 주 안에"). Backlog sizing is qualitative (S/M/L) only.
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/codex-task.md:257:grep -rnE "1 주 안에|2 주 안에|sprint|Q[1-4] 까지" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true
projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/request.ko.md:109:- 시간 추정 (sprint / Q / 주 / 일).

$ grep -rnE "^\s*(from|import)\s+app\.broker" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/ || true
```

Additional check on newly generated design docs only:

```text
$ grep -rnE "수익 보장|profit guarantee|승률 100|fake" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/0*.md projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/10_acceptance_criteria.md || true

$ grep -rnE "Bearer eyJ|access_token=eyJ|appkey=PS" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/0*.md projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/10_acceptance_criteria.md || true

$ grep -rnE "TTTT1002U|TTTT1006U|TTTS3035R|TTTS3018R" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/0*.md projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/10_acceptance_criteria.md || true

$ grep -rnE "1 주 안에|2 주 안에|sprint|Q[1-4] 까지" projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/0*.md projects/paper-trading/docs/ai/jobs/agent-platform-spec-001/10_acceptance_criteria.md || true
```

All four generated-doc-only greps returned no matches.

## Out-of-scope Discovery

`prompts/codex.md` was not present under `/root/ai-dev-center/projects/ai-team/projects/paper-trading/prompts/` or `/root/ai-dev-center/projects/ai-team/prompts/`. I proceeded by following `docs/ai/jobs/agent-platform-spec-001/codex-task.md` verbatim, plus the active system/developer instructions.

## Claude Review Prompt

Use `prompts/claude.md`.

Project directory:
`/root/ai-dev-center/projects/ai-team/projects/paper-trading`

Job ID:
`agent-platform-spec-001`

Review only:
`docs/ai/jobs/agent-platform-spec-001/00_principles_and_boundaries.md`
through
`docs/ai/jobs/agent-platform-spec-001/10_acceptance_criteria.md`
and
`docs/ai/jobs/agent-platform-spec-001/patch.md`

Do not review unrelated dirty app/test/doc files from prior jobs as part of this job.

Check:
- Exactly 12 new files were created in `docs/ai/jobs/agent-platform-spec-001/`.
- No file outside this job directory was modified by this job.
- 85 modules are represented as 40 real-time core + 10 news/event + 20 validation/learning + 15 ops/security.
- `01_seven_services.md` has exactly 85 module mapping rows.
- `09_implementation_backlog.md` has exactly 97 backlog rows.
- Every design doc repeats the 5 safety invariants.
- Broker Gateway Service is the only KIS-credentialed service.
- Agent/Strategy/LLM never directly call broker.
- OMS is the only executable `BrokerOrder` creator.
- LLM output cannot release hard risk blocks.
- live remains locked; no live arming, dry-run disabling, KIS endpoint/TR ID/payload invention, secret exposure, or performance overclaim.

Verdict format: `APPROVE`, `REQUEST_CHANGES`, or `BLOCK`, with findings ordered by severity.

## Follow-up Codex Prompt Rule

Only if Claude returns `REQUEST_CHANGES` or `BLOCK`, run a follow-up Codex job limited to `docs/ai/jobs/agent-platform-spec-001/` and the exact findings. Do not modify application code, tests, scripts, `.env`, KIS catalog, README/RUNBOOK/OPS_AUDIT, or any other job directory.

READY FOR REVIEW
