## 1. Files Changed

- `web/public/index.html`
- `web/public/app.js`
- `web/public/style.css`
- `README.md`
- `docs/ai/CLAUDE_CODEX_WORKFLOW.md`
- `docs/ai/jobs/mvp-01/patch.md`

## 2. Implementation Summary

- Moved the three single-step action buttons into the main setup panel under `Claude → Codex → Claude 전체 실행`.
- Removed the `Manual Shell` card from the core role display and replaced it with a smaller helper note that marks `git-shell` as a non-AI support window.
- Removed duplicated `Claude 계획 생성`, `Codex 구현 실행`, and `Claude 리뷰 실행` buttons from the advanced panel.
- Changed the GUI default job ID from `job-002` to `mvp-001`.
- Updated role and action layout CSS for a two-role display and a three-button main action grid.
- Updated README usage notes with the four main GUI actions, eight pipeline states, manual `git status`/`git diff` utilities, and automation prohibitions.
- Added a `브라우저 GUI` section to `docs/ai/CLAUDE_CODEX_WORKFLOW.md` documenting button-to-API mappings, states, tmux targets, manual utilities, and safety limits.
- Checked `web/server.js` constants against the approved scope; no mvp-01 server edit was needed.
- Added a centered approval modal for `approval_required` with clean Korean summary text, target-window details, safety warning, and approval/reject/interrupt buttons.
- Kept the page-level approval state concise with `승인 대기 중 — 팝업에서 처리하세요.` plus a `승인 팝업 열기` button.
- Added client-side anti-spam tracking with `lastApprovalKey` so polling does not reopen the same approval popup repeatedly.
- Approval modal actions send only to detected `claude` or `codex` windows and refresh pipeline status after sending.

## 3. Safety Confirmation

- No secrets, `.env`, auth, payment, database migration, or production infra files were read or modified.
- No `commit`, `push`, `merge`, PR creation/merge, or deployment automation was added.
- No arbitrary shell command input UI/API was added.
- GUI automation remains scoped to Claude/Codex role actions; `git-shell` is documented as a human-only support window.
- Approval popup actions reuse fixed tmux approval endpoints and never target `git-shell`.

## 4. Test Results

- `node --check web/server.js`: PASS, exit code 0, no output.
- `node --check web/public/app.js`: PASS, exit code 0, no output.
- `git diff --stat`:

```text
README.md                    |  86 ++++++---
docs/safety-rules.md         |   4 +-
docs/setup.md                |   7 +-
docs/workflow.md             |   3 +
prompts/claude-architect.md  |   2 +
prompts/claude-reviewer.md   |   2 +
prompts/codex-implementer.md | 117 ++++++++----
prompts/gemini-manager.md    |   2 +
scripts/create-job.sh        | 148 +++++++---------
scripts/start-ai-team.sh     |  55 +++---
web/public/app.js            | 202 +++++++++++++++++++--
web/public/index.html        |  67 ++++++-
web/public/style.css         | 227 +++++++++++++++++++++++-
web/server.js                | 412 ++++++++++++++++++++++++++++++++-----------
14 files changed, 1025 insertions(+), 309 deletions(-)
```

The stat includes pre-existing dirty worktree changes outside the mvp-01 files. For this mvp-01 implementation, I edited only the files listed in section 1.

## 5. Remaining TODOs

- None.

## Verdict

READY FOR REVIEW
