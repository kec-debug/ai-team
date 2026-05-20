# paper-use-ready-001 — Codex 구현 지시문

You are Codex implementing `docs/ai/jobs/paper-use-ready-001/plan.md`. **This job is tooling / docs / scripts only.** Do NOT modify any file under `projects/paper-trading/app/`. Do NOT add new endpoints. Do NOT change dashboard.html. Do NOT modify settings, OMS, RiskEngine, broker, strategy, runtime, portfolio, session, or domain code.

Read first (in order):

1. `docs/ai/CLAUDE_CODEX_WORKFLOW.md` (root) — workflow + safety rules.
2. `docs/ai/jobs/paper-use-ready-001/request.ko.md` — user request.
3. `docs/ai/jobs/paper-use-ready-001/plan.md` — this task's plan.
4. `projects/paper-trading/scripts/_common.sh` — shared bash helpers (BASE_URL, pretty_print, print_banner, safe env defaults).
5. `projects/paper-trading/scripts/start_server.sh` / `status.sh` / `smoke_check.sh` / `start_dry_run.sh` / `stop_dry_run.sh` / `tick.sh` / `analyze.sh` — existing scripts to extend or compose.
6. `projects/paper-trading/README.md` — existing operator guide (do not rewrite, append only).
7. `projects/paper-trading/app/api/routes.py` — read-only reference for endpoint URLs. **Do not modify.**
8. `projects/paper-trading/tests/test_paper_e2e_api.py` — pattern for TestClient tests.

## Absolute prohibitions

- **Do not modify any file under `projects/paper-trading/app/`.** Not routes.py, not server.py, not dashboard.html, not config.py, not the broker / OMS / risk / strategy / runtime / portfolio / session / domain / ops files.
- **Do not modify any existing test file.** `tests/test_*.py` stay as they are. Only add `tests/test_use_ready_smoke.py` (new file).
- **Do not modify `.env`, `.env.example`, or `docs/kis/MISSING_OFFICIAL_VALUES.md`.**
- Do not add new endpoints. The scripts and smoke test use only existing `/paper/*` + `/ops/*` + `/reports/*` paths.
- Do not enable live trading / live arm / dry-run disable / market allow / `OrderType.STOP` / FX conversion. (Plan §"제외".)
- Do not import external HTTP libraries in Python code. Bash scripts may use `curl` and `bash` builtins only.
- Do not echo `.env` contents, `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO`, `access_token`, or `Bearer …` values anywhere in scripts, README, RUNBOOK, OPS_AUDIT, or patch.md. Use `<redacted>` or `***xxxx` style if needed.
- Do not recommend `git add -A` in README, RUNBOOK, OPS_AUDIT, patch.md, or any new script. Always file-by-file `git add <path>`.
- Do not run `git commit`, `git push`, `git merge`, PR creation, or deployment from any script or instruction.

If you find that completing the job requires editing any forbidden file, STOP and document in `patch.md` under `## Out-of-scope discovery` instead of editing.

## Allowed file changes

| Path | Action |
| --- | --- |
| `scripts/stop_server.sh` | NEW |
| `scripts/restart_server.sh` | NEW |
| `scripts/status.sh` | MODIFY (additive only — append `/ops/status` + `/ops/preflight` curl blocks; do not change existing curl blocks). |
| `scripts/smoke_check.sh` | MODIFY (additive only — append ops endpoints, paper simulation, OK/FAIL summary). |
| `scripts/use_ready_check.sh` | NEW |
| `scripts/safety_grep.sh` | NEW |
| `docs/RUNBOOK.md` | NEW |
| `docs/OPS_AUDIT.md` | NEW |
| `README.md` | MODIFY (append only — add "운영 스크립트 명령 정리 (paper-use-ready-001)" section at end). |
| `tests/test_use_ready_smoke.py` | NEW |
| `docs/ai/jobs/paper-use-ready-001/patch.md` | NEW |
| `docs/ai/jobs/paper-use-ready-001/status.md` | NEW |

No other files. If something needs to change outside this list, STOP and document.

## 1. Scripts

### 1.1 `scripts/stop_server.sh`

Use exact code from plan §4.1. Make executable (`chmod +x`).

Key behaviors:

- `pgrep -f "uvicorn app.api.server"` to identify only this project's uvicorn (not other uvicorn processes on the host).
- SIGTERM first, wait up to 5 seconds, SIGKILL fallback.
- Idempotent: prints `"no uvicorn paper-trading server running"` and exits 0 if no match.
- No `.env` access. No raw credential output.

### 1.2 `scripts/restart_server.sh`

Use exact code from plan §4.2. Make executable. Just a wrapper: `stop_server.sh && sleep 1 && exec start_server.sh "$@"`.

### 1.3 `scripts/status.sh` (additive)

Append the two `curl` blocks from plan §4.3 to the existing file. Do NOT remove or modify the existing `/paper/status` and `/paper/dry-run/status` blocks.

### 1.4 `scripts/smoke_check.sh` (additive)

Append the three blocks from plan §4.4 (ops status, ops preflight, paper simulation example) to the existing file's end (after the existing `stop dry-run` section). Do NOT modify earlier sections.

Also add a final summary line:

```bash
echo
echo "===== smoke_check done ====="
```

(If a `===== ... =====` line already exists at the end, replace it with this. Otherwise append.)

### 1.5 `scripts/safety_grep.sh`

Use exact code from plan §4.5. Make executable.

Key behaviors:

- 9 grep checks. Each prints `[OK ]` or `[FAIL]` plus the failing lines if any.
- Exits 1 if any FAIL, 0 if all OK.
- Reads source files only. Never opens `.env`.

### 1.6 `scripts/use_ready_check.sh`

Use exact code from plan §4.6. Make executable.

Key behaviors:

- Uses `set -uo pipefail` (NOT `-e`) so it collects all results instead of bailing on first failure.
- Calls existing `smoke_check.sh` + new `safety_grep.sh` via subprocess.
- Runs `.venv/bin/python -m compileall` and `pytest -p no:cacheprovider --tb=no -q`.
- Runs `git status --short` and `git log --oneline -5` against the ai-team repo root (resolve path via `cd "$PROJECT_DIR/../.."`).
- Captures intermediate output to `/tmp/{smoke,safety,compileall,pytest}.log` for retrospect.
- Prints final `OK=N FAIL=M` + READY / NOT READY verdict. Exit code matches.

## 2. Docs

### 2.1 `docs/RUNBOOK.md`

Korean operator guide. Follow plan §4.7 structure exactly. Include all 10 troubleshooting items. Always reference scripts by `./scripts/<name>.sh` (relative to project dir).

The PuTTY section should look like:

```markdown
### PuTTY 터널 설정 (원격 접속 시)

1. PuTTY 의 Connection > SSH > Tunnels 에서:
   - Source port: `8000`
   - Destination: `127.0.0.1:8000`
   - Local 선택, Add 클릭.
2. SSH 접속 후 로컬 브라우저에서 `http://127.0.0.1:8000/dashboard` 접속.
```

The "git 운영 원칙" section MUST include:

> **`git add -A` 사용 금지.** 변경한 파일을 명시적으로 `git add <path>` 로 추가한다. 본 시스템은 `git commit / push / merge` 를 자동화하지 않는다.

### 2.2 `docs/OPS_AUDIT.md`

Korean final ops audit. Follow plan §4.8 structure. Include the 6-layer live trading block list, 3-layer market guard list, KIS safety boundaries, Strategy/Agent/LLM isolation evidence, and operator daily checklist.

The audit MUST NOT include any KIS endpoint guesses or invented TR_IDs. Only reference confirmed catalog rows by section number (e.g., "catalog §4.7.1") without quoting field names.

### 2.3 `README.md` (append)

Append the block from plan §4.10 to the end of README. Do NOT modify existing sections. Add a clear separator (`---`) between the existing last section and the new one.

## 3. Tests

### 3.1 `tests/test_use_ready_smoke.py`

Use exact 10 tests from plan §4.9. All tests use `TestClient(create_app())` — no subprocess, no bash. The dry-run lifecycle test must call `start → tick → status → stop` to leave server state clean for subsequent tests.

For `test_smoke_no_secrets_in_combined_responses`, the forbidden tokens list MUST include:
- `"KIS_APP_KEY"` (uppercase env var name — but check the actual JSON to confirm no leak; the substring would only appear if a response contains that exact label or value, which our codebase never does)
- `"KIS_APP_SECRET"`
- `"KIS_ACCOUNT_NO"`
- `"app_secret"` (lowercase)
- `"access_token"`
- `"Bearer "` (with trailing space — catches `Bearer eyJ...` etc.)

For `test_smoke_dry_run_lifecycle`, ensure the test calls stop in a `try/finally` if any step might leave state dirty. (Optional — pytest test isolation via `create_app()` per test should make this safe.)

## 4. Verification commands

After implementation, run from `projects/paper-trading`:

```bash
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
chmod +x scripts/stop_server.sh scripts/restart_server.sh scripts/use_ready_check.sh scripts/safety_grep.sh
bash scripts/safety_grep.sh
```

Expected:

- compileall PASS.
- pytest 547 baseline + 10 new = 557 passed.
- `safety_grep.sh` returns "ALL OK" with exit 0.

`scripts/use_ready_check.sh` SHOULD NOT be auto-run in this turn (it requires the server to be running, which Codex shouldn't start). Document the command in patch.md but do not execute it.

## 5. `patch.md` contents

Create `docs/ai/jobs/paper-use-ready-001/patch.md` with these sections:

1. **Files Changed** — explicit list. Verify NO `app/` files appear.
2. **Implementation Summary** — list of new scripts + docs + tests.
3. **Smoke flow walk-through** — describe what `use_ready_check.sh` does end-to-end.
4. **Safety grep summary** — paste output of `scripts/safety_grep.sh` (with any expected pre-existing patterns documented).
5. **Git status summary** — paste output of `git status --short` from ai-team root, classifying each line.
6. **Safety Confirmation** — explicit confirmations:
   - No `app/` files were modified.
   - No new endpoint was added.
   - `dashboard.html` is unchanged.
   - `live_trading_enabled=True` not introduced.
   - `OrderType.STOP` not introduced.
   - FX conversion not introduced.
   - `git add -A` is not recommended in any new doc.
   - No `commit / push / merge / deploy` performed.
   - No `.env` / `.env.example` modified.
   - No real KIS secret / token / account number written.
7. **Test Results** — compileall + pytest summary (557 expected).
8. **Remaining TODOs** — future follow-up jobs (out of scope): live-validation-002 actual arm; status-surface advertise; runbook screenshot guide; etc.
9. **Claude verification prompt** — use the exact text from request.ko.md's "Codex 작업 후 patch.md에 포함할 Claude 검증 요청 프롬프트" section, including project directory `/root/ai-dev-center/projects/ai-team`, job directory `/root/ai-dev-center/projects/ai-team/docs/ai/jobs/paper-use-ready-001`, the 12 review-focus items, and the verdict / follow-up rules.
10. **Follow-up Codex prompt rules** (used only if Claude returns REQUEST CHANGES or BLOCK):

    - Must include: `request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, `review.md` as required reads.
    - "Required Fixes 만 반영 — 원래 작업 범위 밖 확장 금지."
    - Test re-run command: `.venv/bin/python -m compileall app tests && .venv/bin/python -m pytest -p no:cacheprovider`.
    - "patch.md 갱신 (append `## Follow-up <N>` section) 또는 `review-fix.patch.md` 신규 작성."
    - "Do not commit / push / merge / deploy."
    - "Do not modify secrets / `.env` / auth / payment / production infra."

11. **Status footer**: `READY FOR REVIEW`.

## 6. `status.md` contents

Create `docs/ai/jobs/paper-use-ready-001/status.md` (short):

```markdown
# paper-use-ready-001 Status

Status: READY FOR REVIEW

Implemented operator tooling and documentation:

- `scripts/stop_server.sh` / `scripts/restart_server.sh` (NEW)
- `scripts/status.sh` / `scripts/smoke_check.sh` (additive)
- `scripts/use_ready_check.sh` / `scripts/safety_grep.sh` (NEW)
- `docs/RUNBOOK.md` / `docs/OPS_AUDIT.md` (NEW, Korean)
- `README.md` (append only)
- `tests/test_use_ready_smoke.py` (NEW, 10 tests)

Verification:

- compileall PASS.
- pytest 557 passed.
- safety_grep.sh ALL OK.

No `app/` files modified. No `.env` access. No `git add -A` recommended. No commit / push / merge / deploy.
```

Stop. Do not commit, push, merge, deploy, or modify `.env`. Hand off to the human, who will run `git diff` and invoke Claude review.
