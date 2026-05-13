# Codex Prompt: Improve README for Beginners

You are the **Codex Implementer**. Your task is to update the project's `README.md` based on the following instructions derived from the Gemini Manager's plan.

## Tasks
1. **Numbered Quick Start**: Revise the "Quick Start" section to be a clear, step-by-step guide for a brand-new user.
2. **Simplified Roles Table**: Ensure the roles table includes:
   - Gemini Manager
   - Claude Architect
   - Codex Implementer
   - Claude Reviewer
   - Git Shell
   Describe their responsibilities simply.
3. **Tmux Navigation**: Add a highly visible, easy-to-read tip on how to switch between these roles using tmux shortcuts (e.g., `Ctrl-b` followed by the window number).
4. **Pre-push Checklist**: Create a section titled "Checklist: Before You Push" that reminds users to:
   - Verify changes in the `Git Shell`.
   - Never push directly to `main`.
   - Ensure a PR is reviewed by `Claude Reviewer`.

## Constraints
- **NO Script Changes**: Do not touch anything in the `scripts/` folder.
- **NO Secrets**: Do not add `.env`, API keys, or tokens.
- **Workflow Integrity**: Keep the bilingual flavor of the document where it already exists.

## Reference
- Input: `docs/ai/jobs/job-001/input.en.md`
- Plan: `docs/ai/jobs/job-001/gemini-plan.en.md`
