## 1. Files Changed

paper-use-ready-001 changed only scripts, docs, README, and one new test file:

- `scripts/stop_server.sh` (NEW)
- `scripts/restart_server.sh` (NEW)
- `scripts/status.sh`
- `scripts/smoke_check.sh`
- `scripts/use_ready_check.sh` (NEW)
- `scripts/safety_grep.sh` (NEW)
- `docs/RUNBOOK.md` (NEW)
- `docs/OPS_AUDIT.md` (NEW)
- `README.md` (append-only for this job)
- `tests/test_use_ready_smoke.py` (NEW)
- `docs/ai/jobs/paper-use-ready-001/patch.md` (NEW)
- `docs/ai/jobs/paper-use-ready-001/status.md` (NEW)

No `app/` file was edited for this job. The current workspace already contains pre-existing live-validation dirty entries under `app/`; those are classified in the git status summary below and were not touched by paper-use-ready-001.

## 2. Implementation Summary

Added operator tooling and documentation so the paper trading system can be checked with a repeatable daily routine:

- `stop_server.sh`: idempotent uvicorn stop with SIGTERM, 5-second wait, SIGKILL fallback.
- `restart_server.sh`: stop then exec start wrapper.
- `status.sh`: existing paper status output plus `/ops/status` and `/ops/preflight`.
- `smoke_check.sh`: existing dry-run flow plus ops status, ops preflight, paper order simulation example, and final completion line.
- `safety_grep.sh`: consolidated safety grep helper with `[OK ]` / `[FAIL]` output and nonzero exit on failure.
- `use_ready_check.sh`: master readiness check for server reachability, smoke flow, safety grep, compileall, pytest, and git status.
- `docs/RUNBOOK.md`: Korean operator guide with PuTTY tunnel setup, dashboard usage, dry-run, paper simulation, KIS status, tests, git rules, and troubleshooting.
- `docs/OPS_AUDIT.md`: Korean ops audit covering live trading guards, market order guards, KIS boundaries, Strategy/Agent/LLM isolation, and daily checklist.
- `README.md`: appended operational command summary and RUNBOOK / OPS_AUDIT links.
- `tests/test_use_ready_smoke.py`: 10 TestClient smoke tests for health, paper status, ops status/preflight, dry-run lifecycle, paper simulation, reports analyze, secret non-exposure, GET-only ops routes, and dashboard HTML.

## 3. Smoke flow walk-through

`./scripts/use_ready_check.sh` performs the full paper-use readiness flow:

1. Checks server reachability at `$BASE_URL/healthz`.
2. Checks `/paper/status`, `/ops/status`, and `/ops/preflight`.
3. Runs `./scripts/smoke_check.sh`.
4. Runs `./scripts/safety_grep.sh`.
5. Runs `.venv/bin/python -m compileall app tests`.
6. Runs `.venv/bin/python -m pytest -p no:cacheprovider --tb=no -q`.
7. Prints `git status --short` summary and last 5 commits from the repo root.
8. Prints final `OK=N FAIL=M` and exits 0 only when all checks pass.

I did not run `use_ready_check.sh` in this turn because it expects the server to be running. It is documented for the operator to run after starting the server.

## 4. Safety grep summary

Command:

```text
$ bash scripts/safety_grep.sh
```

Result:

```text
===== safety_grep =====

[OK ] external HTTP libs in app/
[OK ] Strategy 가 KIS 직접 import
[OK ] Agent / LLM 의 broker 직접 호출 (app/agent)
[OK ] live trading 활성화 코드
[OK ] market order guard 우회 (allow_market_orders=True)
[OK ] OrderType.STOP 도입
[OK ] FX 변환 함수 도입
[OK ] JWT-style secret 노출 (Bearer eyJ / access_token=eyJ)
[OK ] .env 가 git tracked 인지

===== safety_grep: ALL OK =====
```

Implementation note: the JWT-style grep excludes `docs/OPS_AUDIT.md` so the audit's expected-output template does not self-match.

## 5. Git status summary

Command:

```text
$ git status --short
```

Current output:

```text
 M projects/paper-trading/README.md
 M projects/paper-trading/app/api/routes.py
 M projects/paper-trading/app/config.py
 M projects/paper-trading/app/static/dashboard.html
 M projects/paper-trading/scripts/smoke_check.sh
 M projects/paper-trading/scripts/status.sh
?? projects/paper-trading/app/ops/
?? projects/paper-trading/docs/OPS_AUDIT.md
?? projects/paper-trading/docs/RUNBOOK.md
?? projects/paper-trading/docs/ai/jobs/live-validation-001/
?? projects/paper-trading/docs/ai/jobs/paper-use-ready-001/
?? projects/paper-trading/scripts/restart_server.sh
?? projects/paper-trading/scripts/safety_grep.sh
?? projects/paper-trading/scripts/stop_server.sh
?? projects/paper-trading/scripts/use_ready_check.sh
?? projects/paper-trading/tests/test_ops_endpoints.py
?? projects/paper-trading/tests/test_use_ready_smoke.py
```

Classification:

- paper-use-ready-001 changes: `README.md`, `scripts/smoke_check.sh`, `scripts/status.sh`, `docs/OPS_AUDIT.md`, `docs/RUNBOOK.md`, `docs/ai/jobs/paper-use-ready-001/`, `scripts/restart_server.sh`, `scripts/safety_grep.sh`, `scripts/stop_server.sh`, `scripts/use_ready_check.sh`, `tests/test_use_ready_smoke.py`.
- Pre-existing live-validation-001 dirty entries: `app/api/routes.py`, `app/config.py`, `app/static/dashboard.html`, `app/ops/`, `docs/ai/jobs/live-validation-001/`, `tests/test_ops_endpoints.py`.

## 6. Safety Confirmation

- No `app/` files were modified by paper-use-ready-001.
- No new endpoint was added by paper-use-ready-001.
- `dashboard.html` was not modified by paper-use-ready-001.
- `live_trading_enabled=True` was not introduced.
- `OrderType.STOP` was not introduced.
- FX conversion was not introduced.
- `git add -A` is not recommended; docs explicitly prohibit it and require file-by-file staging.
- No commit, push, merge, PR, or deploy was performed.
- `.env` and `.env.example` were not modified.
- No real KIS secret, token, Bearer header, or account number was written.
- No auth, payment, production infra, or database migration was modified.
- Scripts use `curl` and shell utilities only; no external Python HTTP library was added.

## 7. Test Results

```text
$ .venv/bin/python -m compileall app tests
PASS
```

```text
$ .venv/bin/python -m pytest -p no:cacheprovider
557 passed in 0.97s
```

```text
$ bash scripts/safety_grep.sh
ALL OK
```

## 8. Remaining TODOs

- Future live-validation-002 actual arming workflow remains out of scope and requires explicit approval.
- Status-surface advertising for newly implemented capabilities remains a separate job.
- Screenshot-based RUNBOOK guide could be added later.
- Operator may run `./scripts/use_ready_check.sh` after starting the server.

## 9. Claude verification prompt

```text
Use prompts/claude.md.

Project directory: /root/ai-dev-center/projects/ai-team
Job ID: paper-use-ready-001
Job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/paper-use-ready-001

Review the paper-use-ready-001 implementation.

Read:
- docs/ai/jobs/paper-use-ready-001/request.ko.md
- docs/ai/jobs/paper-use-ready-001/plan.md
- docs/ai/jobs/paper-use-ready-001/codex-task.md
- docs/ai/jobs/paper-use-ready-001/patch.md

Review the current diff for:
- projects/paper-trading/scripts/
- projects/paper-trading/README.md
- projects/paper-trading/docs/
- projects/paper-trading/app/api/routes.py
- projects/paper-trading/app/static/dashboard.html
- projects/paper-trading/tests/

Review focus:
1. Server start/stop/status workflow is beginner friendly.
2. Dashboard access instructions are correct.
3. Dry-run smoke flow works.
4. Paper order simulation check works.
5. KIS status is shown safely.
6. No app key, app secret, account number, token, Bearer token, or .env contents are exposed.
7. Live trading remains disabled.
8. Market order guard remains intact.
9. No real broker order is sent by smoke checks.
10. Tests pass.
11. Git status guidance is safe and does not recommend git add -A.
12. Scope stayed within paper-use-ready-001.

Verdict must be one of:
APPROVE
REQUEST CHANGES
BLOCK.

If verdict is REQUEST CHANGES or BLOCK, write a Follow-up Codex Prompt that fixes only the required issues.
Do not expand scope.

Do not commit, push, merge, deploy, or run arbitrary shell commands.
```

## 10. Follow-up Codex prompt rules

Use only if Claude returns REQUEST CHANGES or BLOCK.

Required follow-up prompt contents:

- Read `request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, and `review.md`.
- Apply Required Fixes only.
- Do not expand beyond the original paper-use-ready-001 scope.
- Re-run:
  ```bash
  .venv/bin/python -m compileall app tests
  .venv/bin/python -m pytest -p no:cacheprovider
  ```
- Re-run `bash scripts/safety_grep.sh` if scripts/docs are touched.
- Update `patch.md` by appending `## Follow-up <N>` or create `review-fix.patch.md`.
- Do not commit, push, merge, deploy, or create a PR.
- Do not modify secrets, `.env`, auth, payment, production infra, or migrations.

READY FOR REVIEW
