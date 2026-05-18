# Job Request

Write a final QA and usability improvement plan for the AI Development Team GUI Control Center.

## Goal

Verify that the current Web GUI Control Center is in a usable state in practice.
For this `job-007`, dangerous infrastructure changes, auth/password implementation, CI/CD changes, and auto-merge must NOT be performed.

The purposes of this job are:

1. Verify that the current GUI features actually work.
2. Ensure users can handle most tasks via the browser.
3. Organize any missing pieces within a safe scope.
4. Separate and document future candidate tasks.

## Current Features to Verify

Check if the following features actually work:

- Run entire pipeline button
- Real-time pipeline status display
- View tmux output
- Approve / Session Approve / Reject / Abort buttons
- Restart AI Team button
- Restart GUI Server button
- View artifact list
- View `git status`
- View `git diff`
- Display Reviewer results
- Provide guidance that the final PR/merge must be performed manually by a human

## Desired GUI Usability Improvements

If possible, propose the following usability improvements within a safe scope:

- Clean up unnecessary or redundant buttons.
- Distinguish between primary and advanced buttons.
- More clearly display the current step and the target AI window.
- Make the "waiting for approval" state more prominent.
- Provide guidance on what to do next after the Reviewer finishes.
- Display a checklist of final manual tasks the user must do in the GUI.

## Forbidden in this Job

Do NOT implement or execute the following in `job-007`:

- Automate `git push`
- Automate PR merge
- Automate deployment
- Register systemd services
- Set up auto-start on server reboot
- Modify GitHub Actions / CI files
- Implement login, password, session, or token-handling code
- Read or output `.env`, tokens, secrets, or API keys
- Modify auth, payment, DB migration, or production infra
- Add arbitrary shell command execution features

## Items Requiring Direct Human Intervention

Do not automate the following items in this job; organize them only as future work that a human must manually approve and perform:

- Commit / PR / merge the latest GUI changes
- Set up auto-execution after server reboot
- Enhance GUI security
- Add CI validators
- Enhance the multi-project selection feature

## Artifacts

Create the following files:

- `docs/ai/jobs/job-007/input.en.md`
- `docs/ai/jobs/job-007/gemini-plan.en.md`
- `docs/ai/jobs/job-007/codex-prompt.en.md`

## Acceptance Criteria

- `job-007` does not execute any dangerous tasks.
- The plan for verifying current GUI features is clear.
- GUI usability items that can be safely improved are organized.
- Items for human execution and AI execution are clearly separated.
- The prompt handed over to Codex is strictly restricted to safe GUI QA/usability improvements.
