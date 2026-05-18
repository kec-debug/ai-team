## 1. Files Changed

- `projects/paper-trading/app/runtime/dry_run.py`
  - Added `DryRunController`, state/counter dataclasses, explicit tick execution, kill-switch blocking, and auto-stop behavior.
- `projects/paper-trading/app/runtime/dry_run_report.py`
  - Added safe report writers for `events.jsonl`, `summary.json`, and `orders.csv`.
- `projects/paper-trading/app/config.py`
  - Added dry-run report directory, max error threshold, and max tick settings.
- `projects/paper-trading/app/api/server.py`
  - Wired `DryRunController` into FastAPI lifespan as `app.state.dry_run_controller`.
- `projects/paper-trading/app/api/routes.py`
  - Added `/paper/dry-run/start`, `/paper/dry-run/stop`, `/paper/dry-run/tick`, `/paper/dry-run/status`, and `/paper/status` `dry_run_running`.
- `projects/paper-trading/.env.example`
  - Added dry-run report settings placeholders.
- `projects/paper-trading/.gitignore`
  - Added `reports/`.
- `projects/paper-trading/README.md`
  - Added the mvp-018 long-running dry-run verification section.
- `projects/paper-trading/tests/test_dry_run_controller.py`
  - Added controller state machine, counter, kill-switch, and auto-stop tests.
- `projects/paper-trading/tests/test_dry_run_reports.py`
  - Added report writer and `dump_safe` tests.
- `projects/paper-trading/tests/test_dry_run_routes.py`
  - Added API route happy/error path and secret non-exposure tests.
- `projects/paper-trading/tests/test_api_paper_status.py`
  - Added `dry_run_running` assertions.
- `docs/ai/jobs/mvp-018/patch.md`
  - Added this implementation summary.

## 2. Implementation Summary

### 2.1 DryRunController

Added a synchronous stateful controller with `idle -> running -> stopped/auto_stopped` transitions. `start()`, `stop()`, and `tick()` reject invalid lifecycle calls with `RuntimeError`, which the API maps to HTTP 409.

### 2.2 Explicit Tick Model

The controller does not create a background task or timer. `POST /paper/dry-run/tick` is the only execution trigger and delegates to the existing `PaperRunner.run_once(snapshots)` path.

### 2.3 Counters

`DryRunCounters` tracks ticks, candidates, blocked candidates, passed risk candidates, OMS rejections, risk rejections, stale quote rejections, spread rejections, market order rejections, KIS fail-closed count, errors, last error, and kill-switch blocked ticks.

### 2.4 Reports

Each run writes under `reports/dry_run/run_<timestamp>/` by default:

- `events.jsonl`
- `summary.json`
- `orders.csv`

`dump_safe()` recursively rejects credential-like key names before writing. `secret_exposed` is allowed only as the explicit false status flag required by the API summary.

### 2.5 API

Added:

- `POST /paper/dry-run/start`
- `POST /paper/dry-run/stop`
- `POST /paper/dry-run/tick`
- `GET /paper/dry-run/status`

`/paper/status` now includes `dry_run_running`.

### 2.6 Kill Switch / Auto-Stop

If `kill_switch_engaged` is true, a tick returns `blocked_kill_switch` and does not evaluate strategy snapshots. If `errors_total` reaches `DRY_RUN_MAX_ERRORS_BEFORE_AUTO_STOP`, the controller becomes `auto_stopped` with reason `error_threshold`. If `DRY_RUN_MAX_TICKS` is reached, it becomes `auto_stopped` with reason `max_ticks_reached`.

### 2.7 Safety

The controller does not call KIS directly and does not import `app.broker.kis`. It only calls `PaperRunner.run_once`, preserving Strategy -> RiskEngine -> OMS -> BrokerAdapter flow. No KIS endpoint, TR ID, URL, payload, or external HTTP library was added.

### 2.8 Worktree Note

The worktree already contained pre-existing mvp-011-013/mvp-014 changes, including diffs in `app/broker/kis.py` and older KIS tests. mvp-018 did not modify `app/broker/kis.py` or `app/runtime/paper_runner.py`.

## 3. Safety Confirmation

- No `.env` file was read, copied, printed, modified, or added to git.
- No real KIS app key, app secret, account number, access token, or refresh token was added.
- No KIS endpoint, TR ID, URL, header, or payload was invented.
- No actual KIS HTTP implementation was added.
- No external HTTP library import was added.
- Live trading remains disabled by existing settings guards.
- Market orders remain disabled.
- `KIS_ORDER_DRY_RUN=true` remains documented as the default.
- Dry-run ticks do not send HTTP orders.
- Strategy, Agent, and LLM code paths were not changed to call KIS.
- OMS/RiskEngine boundaries remain intact.
- Reports are ignored through project `.gitignore` `reports/`.
- `app/broker/kis.py` and `app/runtime/paper_runner.py` were not modified by mvp-018.
- No commit, push, merge, deploy, auth, payment, production infra, or database migration change was performed.

## 4. Test Results

From `projects/paper-trading`:

```text
.venv/bin/python -m compileall app tests
Result: passed
```

```text
.venv/bin/python -m pytest -p no:cacheprovider -q tests/test_dry_run_reports.py tests/test_dry_run_controller.py tests/test_dry_run_routes.py
Result: 26 passed in 0.23s
```

```text
.venv/bin/python -m pytest -p no:cacheprovider
Result: 155 passed in 0.33s
```

Additional checks:

- `OrderType.MARKET` grep in `projects/paper-trading/app`: no matches.
- KIS endpoint/TR ID/URL fragment grep in new mvp-018 runtime/API files: no matches.
- external HTTP import grep in `projects/paper-trading/app`: no matches.
- `.env` / `projects/paper-trading/.env` git status: no matches.

## 5. Remaining TODOs

- Add optional background auto-tick scheduling in a future MVP if needed.
- Add a report viewer or aggregation command in a future MVP.
- Keep real KIS HTTP integration blocked until official KIS values are confirmed in a separate approved job.

READY FOR REVIEW
