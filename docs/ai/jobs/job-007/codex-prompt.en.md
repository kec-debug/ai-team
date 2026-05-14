# Codex Prompt: job-007 (GUI Usability and QA)

## Role
You are the **Codex Implementer**. Your task is to implement the changes outlined in `gemini-plan.en.md` for `job-007`.

## Strict Safety Boundaries
- **DO NOT** write code for authentication, passwords, login, or session management.
- **DO NOT** automate any Git commits, pushes, or merges.
- **DO NOT** modify server infrastructure, systemd, or CI files.
- **DO NOT** add functionality to run arbitrary shell commands.
- Your changes must be restricted entirely to the frontend UI (`index.html`, `style.css`, `app.js`) and any minor, safe backend data-formatting in `server.js` required to support the UI.

## Implementation Tasks
1. **Button Cleanup:** Organize the buttons in `web/public/index.html`. Separate the main pipeline flow from advanced/system controls (like restarting servers). Remove redundancies.
2. **State Visibility:** Update `web/public/app.js` and `web/public/style.css` to make the "waiting for approval" and "current active step" states visually prominent.
3. **User Guidance:** Add a UI section indicating what the user should do after the pipeline finishes (e.g., a checklist reminding them to manually review `git diff`, create a PR, and merge via GitHub).
4. **Functional Preservation:** Ensure all existing features (tmux output, git status, git diff, artifact loading) continue to work properly with the new layout.

Please execute these changes, run the necessary tests to verify the GUI still functions, and generate the final `patch.md` and `codex-summary.en.md` as usual. Do not commit or push the changes.
