# Codex Summary — job-008

## Files changed
- `web/server.js` — added allow-listed recent tmux output capture and issue classification for blocked, approval-required, failed, and manual-required states; `/api/pipeline/status` now includes `status.detectedIssue`.
- `web/public/index.html` — added a dedicated detected-issue alert area in the pipeline status panel.
- `web/public/app.js` — renders detected issues with Korean guidance and handles blocked as a terminal polling state.
- `web/public/style.css` — styled prominent issue alerts and blocked status states.
- `docs/ai/jobs/job-008/codex-summary.en.md` — this implementation summary.

## Behavior notes
- The detector only reads recent output from allow-listed tmux windows.
- If blocked or failed output is detected for the current pipeline stage, the status no longer remains plain `running`.
- Blocked and failed detections stop automatic stage advancement and require manual action.
- No arbitrary shell input, commit, push, merge, deployment automation, or secret/.env reading was added.

## Verification
- Pass: `node --check web/server.js`
- Pass: `node --check web/public/app.js`
- Pass: `git diff --stat`

## Verdict
READY FOR REVIEW
