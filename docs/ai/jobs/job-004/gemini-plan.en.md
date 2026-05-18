# Job Plan: job-004 - Implement All-in-one AI Pipeline in GUI

## Goal
Implement a "Run Entire Pipeline" feature in the Browser GUI to automate the sequential execution of AI agents (Manager, Architect, Implementer, Reviewer) with a single button click, while maintaining manual control over final PR creation and merging.

## Context
Currently, users must manually trigger each AI agent and wait for each step to finish. Automating this sequence improves efficiency and provides a better user experience for the AI development team's control center.

## In scope
- **GUI Updates**:
    - Add a "Run Entire Pipeline" button to `index.html`.
    - Add a "Create PR" button (separate from the pipeline).
    - Add a status display to show the progress of the pipeline (e.g., current step, success/failure).
    - Update `app.js` to handle pipeline initiation and status polling.
- **Backend Updates (`server.js`)**:
    - Implement `POST /api/pipeline/run` to start the sequential execution.
    - Implement `GET /api/pipeline/status` to report progress and artifacts.
    - Implement the automation logic for the following steps:
        1. Create job directory.
        2. Save `input.ko.md`.
        3. Trigger Gemini Manager (English plan).
        4. Trigger Claude Architect (Architecture review).
        5. Trigger Codex Implementer (Code implementation).
        6. Capture `git diff`.
        7. Trigger Claude Reviewer (PR review).
    - Ensure `codex-summary.en.md` and `claude-pr-review.en.md` (or `review.md`) are viewable in the GUI.
- **Execution Strategy**:
    - Use non-interactive/headless execution for agents where supported (e.g., `codex exec`).
    - Minimize interactive tmux prompts to prevent the pipeline from hanging.
- **Documentation**:
    - Update `README.md` with instructions for the new pipeline feature and a clear statement about manual PR/Merge safety policies.

## Out of scope
- Automatic `git commit`, `git push`, or `gh pr merge`.
- Adding any features for arbitrary shell command execution.
- Modifying authentication, payment, or production infrastructure code.
- Automating manual steps that require human intervention (mark as "Manual Intervention Required" instead).

## Acceptance criteria
- GUI features a "Run Entire Pipeline" button that triggers the full sequence.
- Users can see which step is currently running and whether it succeeded or failed.
- The pipeline correctly generates and displays artifacts (`gemini-plan.en.md`, `patch.md`, `review.md`, etc.).
- "Create PR" remains a separate manual action.
- Safety rules are strictly followed (no auto-merge, no sensitive file access).
- `README.md` is updated and reflects the new workflow.

## Suggested approach
1. **Research**: Identify the non-interactive flags or methods for the `gemini`, `claude`, and `codex` CLI tools.
2. **UI**: Update `index.html` and `style.css` to accommodate the new pipeline controls and status indicators.
3. **Backend Logic**:
    - Use an in-memory object in `server.js` to track active pipeline statuses.
    - Implement the sequential execution loop. Since these tasks take time, the `/run` endpoint should start the process and return immediately, while the client polls `/status`.
    - Use `execFile` for headless execution if possible; otherwise, continue using `sendToWindow` but with logic to wait for file generation.
4. **Integration**: Ensure the new `claude-pr-review.en.md` and `codex-summary.en.md` filenames are included in the allowed artifacts list.
5. **Testing**: Run a sample job through the entire pipeline and verify all steps complete correctly.

## Risks & open questions
- **Timeouts**: AI agent tasks can take several minutes. The backend must handle these long-running tasks without blocking or timing out the HTTP connection (polling is the solution).
- **Interactivity**: If an agent forces a prompt (e.g., "Do you want to continue? [Y/n]"), the pipeline might hang. We must ensure agents run with "Yes to all" or non-interactive settings.
- **Concurrency**: What happens if two users try to run a pipeline for the same job ID simultaneously? Simple locking or job-level status tracking is needed.

## Files likely to change
- `web/server.js`
- `web/public/index.html`
- `web/public/app.js`
- `web/public/style.css`
- `README.md`
