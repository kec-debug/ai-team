# Job Plan: job-007 - GUI Final QA and Usability Improvements

## Goal
Verify the functional completeness of the current AI Team Web GUI and implement safe usability enhancements (e.g., button organization, state visibility) while strictly excluding any infrastructure, security, or automated git operations.

## Context
The GUI Control Center has been developed to orchestrate the AI team pipeline. Before finalizing version 1, we must conduct a functional QA pass and polish the user interface. It is critical that we isolate safe usability changes from sensitive operational tasks (like authentication or server configuration) to maintain system security.

## In scope
- Functional QA of existing GUI features:
    - Entire pipeline execution.
    - Status polling and display.
    - tmux output streaming/viewing.
    - Interactive controls (Approve/Reject/Abort).
    - Restart controls (AI Team, GUI Server).
    - Artifacts, `git status`, and `git diff` rendering.
    - Reviewer output rendering.
- UI/UX enhancements on the frontend:
    - Reorganize layout to separate primary actions from advanced controls.
    - Enhance visual distinction of the current pipeline step and the active target window.
    - Highlight the "waiting for approval" state visually.
    - Add post-pipeline guidance text (e.g., "Reviewer finished. Next steps: ...").
    - Add a checklist UI for manual tasks (Commit, PR, Merge).
- Documentation of future work designated strictly for human intervention.

## Out of scope
- **Strictly Forbidden:** Any automation of `git push`, PR creation, or PR merge.
- **Strictly Forbidden:** Implementing login, authentication, passwords, or session management.
- **Strictly Forbidden:** Deployments, systemd setup, or reboot auto-start configurations.
- **Strictly Forbidden:** Modifying CI/CD pipelines (e.g., GitHub Actions).
- **Strictly Forbidden:** Reading or modifying `.env`, secrets, or API keys.
- **Strictly Forbidden:** Adding arbitrary shell command execution features.
- Any backend functionality changes outside of supporting the safe UI state updates.

## Acceptance criteria
- GUI effectively guides the user through the pipeline with clear next steps and checklists.
- Unnecessary or duplicate buttons are removed or consolidated.
- The "waiting for approval" state is immediately noticeable to the user.
- Future tasks (Auth, CI, Systemd, PR merging) are documented but not implemented.
- The frontend code reflects the usability improvements without touching any forbidden areas.

## Suggested approach
- **UI Audit:** Review `index.html` and `style.css`. Group buttons semantically (e.g., Primary Flow vs. Git Utils vs. System Controls).
- **State Highlighting:** Update `app.js` to toggle a specific CSS class when the pipeline requires user approval, making it blink or change color.
- **Checklist/Guidance:** Hardcode a static checklist section in `index.html` that outlines the manual git operations required after a successful pipeline run.
- **Testing:** Verify the UI changes locally to ensure they don't break existing endpoints.

## Risks & open questions
- The exact state mapping for "waiting for approval" might require careful parsing of the backend status endpoint. The UI must cleanly reflect this without guessing.

## Files likely to change
- `web/public/index.html`
- `web/public/app.js`
- `web/public/style.css`
