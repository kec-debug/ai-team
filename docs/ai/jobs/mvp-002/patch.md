# Codex 패치 요약

## 1. Files Changed

- `web/server.js`
- `web/public/index.html`
- `web/public/app.js`
- `web/public/style.css`
- `scripts/start-ai-team.sh`
- `README.md`
- `docs/ai/CLAUDE_CODEX_WORKFLOW.md`
- `docs/ai/jobs/mvp-002/patch.md`

## 2. Implementation Summary

- Updated the GUI from the deprecated 5-role workflow to the Claude + Codex workflow.
- Replaced old visible role actions with `Claude 계획 생성`, `Codex 구현 실행`, and `Claude 리뷰 실행`.
- Renamed the full pipeline action to `Claude → Codex → Claude 전체 실행`.
- Mapped Claude plan/review to the `claude` tmux window and Codex implementation to the `codex` tmux window.
- Added a non-AI `manual-shell` tmux window for human git/test commands and exposed it as Manual Shell in tmux output selection.
- Restricted approval/interrupt controls to Claude and Codex AI windows.
- Changed saved request input to `request.ko.md` and prioritized the new artifact list: `request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, `review.md`, `status.md`.
- Updated pipeline states to the new names: `claude_planning`, `codex_implementing`, `claude_reviewing`, `manual_review_required`, `succeeded`, `failed`, `blocked`, and `approval_required`.
- Kept `git status` and `git diff` as manual utility buttons, separate from AI role buttons.
- Documented Manual Shell as a non-AI utility window, not a `git-shell` AI role.
- Updated README GUI usage for the new two-role workflow.

## 3. Safety Confirmation

- Did not add arbitrary shell command input.
- Did not add auto commit, push, merge, PR merge, or deployment.
- Did not read or edit `.env`, tokens, secrets, API keys, auth, payment, database migrations, or production infrastructure.

## 4. Test Results

- PASS: `node --check web/server.js`
- PASS: `node --check web/public/app.js`
- PASS: `bash -n scripts/start-ai-team.sh`
- PASS: `git diff --stat`
- PASS: no old 5-role tmux window names found in GUI/server/start script files

`git diff --stat` reported broader pre-existing repository changes in addition to this job's files:

```text
14 files changed, 727 insertions(+), 309 deletions(-)
```

## 5. Remaining TODOs

- None at this stage.

## Verdict

READY FOR REVIEW
