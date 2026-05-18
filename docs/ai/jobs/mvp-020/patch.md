## 1. Files Changed

- `projects/paper-trading/scripts/_common.sh`
  - Added shared safe environment defaults, base URL/port defaults, JSON pretty-print helper, and banner output.
- `projects/paper-trading/scripts/start_server.sh`
  - Added localhost-only uvicorn starter.
- `projects/paper-trading/scripts/status.sh`
  - Added `/paper/status` and `/paper/dry-run/status` helper.
- `projects/paper-trading/scripts/start_dry_run.sh`
  - Added dry-run start helper.
- `projects/paper-trading/scripts/tick.sh`
  - Added auto-start-if-needed dry-run tick helper.
- `projects/paper-trading/scripts/stop_dry_run.sh`
  - Added dry-run stop helper.
- `projects/paper-trading/scripts/analyze.sh`
  - Added dry-run report analyze/latest helper and local `analysis_report.md` path output.
- `projects/paper-trading/scripts/smoke_check.sh`
  - Added status -> start -> tick -> analyze -> latest -> stop smoke flow.
- `projects/paper-trading/tests/test_helper_scripts.py`
  - Added script metadata, syntax, safety, and permissions tests.
- `projects/paper-trading/README.md`
  - Added beginner-friendly execution instructions for mvp-020 scripts.
- `docs/ai/jobs/mvp-020/patch.md`
  - Added this implementation summary.

## 2. Implementation Summary

### 2.1 Shared Helper

`scripts/_common.sh` forces safe defaults at the shell level:

- `TRADING_MODE=paper`
- `LIVE_TRADING_ENABLED=false`
- `ALLOW_MARKET_ORDERS=false`
- `KIS_ORDER_DRY_RUN=true`

It also provides `BASE_URL`, `PORT`, `pretty_print()`, and `print_banner()`.

### 2.2 Server Startup

`scripts/start_server.sh` starts uvicorn with `--host 127.0.0.1` and the selected `PORT`, preventing accidental external binding.

### 2.3 Runtime Helpers

Added helper scripts for status, dry-run start, tick, stop, and analysis. `tick.sh` checks whether dry-run is running and starts it first if needed.

### 2.4 Analysis Helper

`scripts/analyze.sh` calls both `/reports/dry-run/analyze` and `/reports/dry-run/latest`, then prints the local path to the generated `analysis_report.md`.

### 2.5 Smoke Flow

`scripts/smoke_check.sh` runs the beginner flow in sequence and tolerates expected failures such as already-running or already-stopped dry-runs.

### 2.6 Tests / Docs

Added script metadata tests for existence, executable bits, shebangs, `bash -n`, safe env exports, no secret-reading/printing patterns, no git/pip automation, and localhost-only server binding. README now documents the beginner workflow and safety behavior.

## 3. Safety Confirmation

- No `.env` file was read, copied, printed, modified, or added to git.
- No real KIS app key, app secret, account number, access token, or refresh token was added.
- Scripts do not echo raw KIS credential variables.
- Scripts do not `cat` or `grep` `.env`.
- Scripts do not run `git commit`, `git push`, `git merge`, or `pip install`.
- No app code, strategy, OMS, RiskEngine, broker, settings, `.env.example`, or `.gitignore` change was made for mvp-020.
- No KIS endpoint, TR ID, URL, header, or payload was invented.
- No actual KIS HTTP implementation was added.
- Live trading remains disabled by script-level env exports.
- Market orders remain disabled by script-level env exports.
- `KIS_ORDER_DRY_RUN=true` is forced by script-level env exports.
- `start_server.sh` binds only to `127.0.0.1`.
- No commit, push, merge, deploy, auth, payment, production infra, or database migration change was performed.

## 4. Test Results

From `projects/paper-trading`:

```text
bash -n scripts/*.sh
Result: passed
```

```text
.venv/bin/python -m pytest -p no:cacheprovider -q tests/test_helper_scripts.py
Result: 9 passed in 0.02s
```

```text
.venv/bin/python -m compileall app tests
Result: passed
```

```text
.venv/bin/python -m pytest -p no:cacheprovider
Result: 181 passed in 0.39s
```

Additional checks:

- Forbidden script pattern grep against `scripts/`: no matches.
- `.env` / `projects/paper-trading/.env` git status: no matches.
- `git status --short` for mvp-020 scope shows only README plus new scripts/tests/patch files. Existing unrelated dirty work remains in the wider worktree from previous MVPs.

## 5. Remaining TODOs

- Start the server manually with `./scripts/start_server.sh` before using the helper scripts.
- Add richer sample snapshots to `tick.sh` in a separate approved MVP if beginner workflows need non-empty dry-run inputs.
- Add optional Windows PowerShell equivalents in a future MVP if needed.

READY FOR REVIEW
