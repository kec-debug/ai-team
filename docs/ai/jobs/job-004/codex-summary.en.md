# Codex Summary — job-004

## Files changed
- `web/server.js` — added pipeline run/status endpoints, in-memory state tracking, safe tmux-driven step execution, artifact polling, local diff capture, redacted pipeline logging, safety deny-list checks, JSON-only `/api/*` 404 handling, and the required idle status JSON shape.
- `web/public/index.html` — added the "전체 파이프라인 실행" button, pipeline status panel, and result summary panel.
- `web/public/app.js` — added pipeline start handling, status polling, step rendering, result summary rendering, and defensive non-JSON response handling.
- `web/public/style.css` — added styles for the pipeline button, status badges, step list, and summary area.
- `README.md` — documented the one-button pipeline flow, polling behavior, manual final approval, and safety boundaries.
- `docs/ai/jobs/job-004/codex-summary.en.md` — this implementation summary.

## Design notes
- The pipeline does not run arbitrary shell commands and does not launch headless agent CLIs with auto-approval flags.
- Agent steps reuse the existing fixed tmux windows and prompts.
- The server waits for expected job artifacts before advancing. If an artifact does not appear before the timeout, the pipeline becomes `needs_manual`.
- `git diff` is saved to `docs/ai/jobs/job-004/local-diff.patch` when changes exist.
- The server blocks after Codex if changed paths match the safety deny-list for secrets, migrations, auth, payment, billing, infra, or GitHub workflow paths.
- Unknown `/api/*` routes return `{ "ok": false, "error": "Unknown API endpoint" }` with status 404 instead of Express HTML.
- The frontend checks `content-type` before parsing JSON and shows a Korean error if the server returns HTML or another non-JSON response.
- No commit, push, PR creation, merge, or deployment automation was added.

## Verification
- Pass: `node --check web/server.js`
- Pass: `node --check web/public/app.js`
- Pass: `curl -sS "http://127.0.0.1:3100/api/pipeline/status?projectDir=/root/ai-dev-center/projects/ai-team&jobId=job-004"` returned `{"ok":true,"status":{"state":"idle","message":"아직 실행되지 않았습니다.","step":null,"artifacts":[],"gitDiff":"-","reviewStatus":"-"}}`
- Pass: `git diff --stat`
- Pass: `git diff -- web README.md`

## Verdict
READY FOR REVIEW
