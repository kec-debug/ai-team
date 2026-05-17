## 1. Files Changed

- `web/server.js`
- `web/public/app.js`
- `web/public/index.html`
- `web/public/style.css`
- `docs/ai/jobs/mvp-004/patch.md`

## 2. Implementation Summary

- Fixed pipeline stage advancement so approval actions only send keys to the selected Claude/Codex tmux window and do not advance stages.
- Added artifact gates: Claude planning requires both `plan.md` and `codex-task.md`; Codex implementation requires `patch.md`; Claude review requires `review.md`.
- Added review-loop states and actions: `review_changes_requested`, `codex_fixing_review`, `claude_re_reviewing`, `manual_final_approval_required`, and buttons for Codex review fixes and Claude re-review.
- Added review decision parsing for `APPROVE`, `REQUEST_CHANGES`, `BLOCK`, plus Korean variants.
- Added approval inspector context extraction from the active AI tmux pane with request type, command/target, working directory, raw block, risk, and recommended action.
- Risk-gated approval popup buttons so high/unknown risk does not offer unsafe approval options.
- Tightened approval detection to ignore source code, diffs, grep/search output, quoted state names, and code blocks; approval popups now require a strong interactive approval prompt block.

## 3. Safety Confirmation

- No arbitrary shell command input was added.
- Approval endpoints remain key-send only for `claude` or `codex`.
- No auto commit, push, merge, PR merge, or deployment automation was added.
- No `.env`, secret, token, API key, auth, payment, DB migration, or production infra files were read or modified.
- Manual Shell remains a non-AI utility window.

## 4. Test Results

- `node --check web/server.js`: PASS
- `node --check web/public/app.js`: PASS
- `git diff --stat`: PASS, output captured in final response.

## 5. Remaining TODOs

- None.

## Verdict

READY FOR REVIEW
