# Codex Summary — job-006

## Files changed
- `web/server.js` — added real-time tmux output/control APIs, service status/restart APIs, richer pipeline status metadata, approval-wait detection, and artifact-based progress refresh.
- `web/public/index.html` — reorganized the GUI around primary control-center actions, added tmux output, approval controls, service restart buttons, and final next-action display.
- `web/public/app.js` — added 2-second live refresh, tmux window/output loading, approval/reject/interrupt actions, service restart calls, and richer selected-job status rendering.
- `web/public/style.css` — styled the new control panel, warning/guidance states, pipeline metadata, advanced controls, and tmux output area.
- `README.md` — documented the real-time control-center features and allow-listed approval controls.
- `docs/ai/jobs/job-006/codex-summary.en.md` — this implementation summary.

## Safety notes
- No arbitrary shell command input was added.
- No commit, push, merge, PR creation, or deployment automation was added.
- tmux key sending is limited to allow-listed windows and fixed inputs only.
- tmux output is redacted before being returned to the browser.
- Restart controls only restart the local tmux AI team or the local GUI server; they do not affect git publishing or deployment.

## Verification
- Pass: `node --check web/server.js`
- Pass: `node --check web/public/app.js`
- Pass: `git diff --stat`

## Verdict
READY FOR REVIEW
