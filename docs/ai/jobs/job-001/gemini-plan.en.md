# Work Plan — Job 001: Improve README for Beginners

## Goal
Enhance `README.md` to be more accessible to new users by providing a clear step-by-step guide, simplifying tmux navigation instructions, and clarifying team roles.

## Context
The current README is functional but could be better structured for someone using the AI Dev Team setup for the first time. Clarity on how to move between roles and what each role does is essential for efficient workflow.

## In scope
- Reorganizing the "Quick Start" section into a numbered step-by-step guide.
- Adding or clarifying the table of roles (Gemini, Claude-A, Codex, Claude-R, Git Shell).
- Simplifying tmux window navigation instructions.
- Adding a "Pre-push Checklist" section to enforce safety rules.

## Out of scope
- Modifying any logic or code within the `scripts/` directory.
- Adding instructions or placeholders for secrets, credentials, or `.env` files.
- Changing the fundamental workflow (Manager -> Architect -> Implementer -> Reviewer).

## Acceptance criteria
- [ ] `README.md` has a "First-Time Setup & Usage" section with ordered steps.
- [ ] A table exists that lists all 5 roles with their respective responsibilities.
- [ ] Tmux window switching (`Ctrl-b` + `0-4`) is explained in a way that is easy to find and understand.
- [ ] A "Before You Push" section exists, advising against direct `main` pushes and mentioning review steps.
- [ ] No security-sensitive information or script modifications are included.

## Suggested approach
- Move "Quick Start" higher or refine it to be the primary path for new users.
- Use a clean Markdown table for roles.
- Use a blockquote or a distinct sub-header for the tmux navigation tips.
- Ensure the pre-push checklist aligns with `docs/safety-rules.md`.

## Risks & open questions
- **Consistency**: Ensure the bilingual (KO/EN) nature of the README is preserved or improved consistently.

## Files likely to change
- `README.md`
