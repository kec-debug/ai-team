# Codex Summary — job-005

## Files changed
- `web/server.js` — fixed selected job pipeline state handling, added `POST /api/pipeline/reset`, switched timeout state to `manual_required`, and made stage completion artifact-based for the selected job folder.
- `web/public/index.html` — added the pipeline reset button, selected job/stage/state display, manual intervention guidance area, and input hint.
- `web/public/app.js` — added reset handling, job-specific input caching, selected-job status rendering, and `manual_required` polling behavior.
- `web/public/style.css` — styled the reset controls, pipeline metadata, input hint, and manual intervention guidance.
- `README.md` — documented selected-job reset behavior and the `manual_required` state.

## Behavior notes
- Pipeline status remains keyed by `projectDir + jobId`; idle responses now include the requested project and job.
- Stage detection uses these artifacts:
  - Gemini: `gemini-plan.en.md` or `codex-prompt.en.md`
  - Claude Architect: `claude-design-review.en.md` or `architecture.md`
  - Codex: `codex-summary.en.md`
  - Reviewer: `claude-pr-review.en.md` or `review.md`
- If a stage times out, the status becomes `manual_required` with: `AI CLI 창에서 승인 대기 중일 수 있습니다. tmux ai-team 세션을 확인하세요.`
- No commit, push, merge, deployment, or arbitrary shell command automation was added.

## Verification
- Pass: `node --check web/server.js`
- Pass: `node --check web/public/app.js`
- Pass: `git diff --stat`

## Verdict
READY FOR REVIEW
