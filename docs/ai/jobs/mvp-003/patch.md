# Codex 패치 요약

## 1. Files Changed

- `web/server.js`
- `web/public/app.js`
- `web/public/index.html`
- `README.md`
- `docs/ai/CLAUDE_CODEX_WORKFLOW.md`
- `scripts/start-ai-team.sh`
- `docs/ai/jobs/mvp-003/patch.md`

## 2. Implementation Summary

- Removed old workflow artifacts from active pipeline stage completion so the pipeline no longer treats `gemini-plan.en.md`, `codex-summary.en.md`, or `claude-pr-review.en.md` as successful outputs for the new stages.
- Kept old artifact filenames readable only as backward-compatible artifacts.
- Confirmed active send mappings are only `claude-plan -> claude`, `codex-implement -> codex`, and `claude-review -> claude`.
- Removed the legacy `/api/send/codex` compatibility route from active send endpoints.
- Updated pipeline prompts to explicitly read/write `request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, and `review.md`.
- Switched the non-AI manual shell window to the preferred `git-shell` tmux name while keeping it labeled as Manual Shell, not an AI role.

## 3. Safety Confirmation

- No arbitrary shell command input was added.
- No auto commit, push, merge, PR merge, or deployment automation was added.
- Did not read or modify `.env`, secrets, tokens, API keys, auth, payment, database migrations, or production infrastructure.

## 4. Test Results

- PASS: `node --check web/server.js`
- PASS: `node --check web/public/app.js`
- PASS: `git diff --stat`
- PASS: active web/start files contain no `ai-team:gemini-manager`, `id: 'gemini'`, old send endpoints, or old 5-role tmux window mappings.

`git diff --stat` output:

```text
14 files changed, 723 insertions(+), 306 deletions(-)
```

## 5. Remaining TODOs

- Restart the running GUI server after deploying this patch if it is still serving the old in-memory code that calls `ai-team:gemini-manager`.

## Verdict

READY FOR REVIEW
