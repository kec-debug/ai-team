# Codex Summary — Job 001

## Files changed
- `README.md` — improved the beginner path while keeping the document Korean-primary.

## Implementation notes
- Updated the existing roles table instead of adding a duplicate section.
- Verified tmux window ordering against `scripts/start-ai-team.sh` and documented indices 0 through 4:
  - 0: `gemini-manager`
  - 1: `claude-architect`
  - 2: `codex-implementer`
  - 3: `claude-reviewer`
  - 4: `git-shell`
- Reworked the existing quick start into ordered first-time usage steps.
- Added a visible tmux navigation callout.
- Clarified that `examples/job-001/input.ko.md` is only a reference example, while real jobs are created under `docs/ai/jobs/<JOB_ID>/` by `./scripts/create-job.sh`.
- Added a short pre-push checklist that links to `docs/safety-rules.md` and `docs/workflow.md`.

## Verification
- `git diff --stat`
- `git diff -- README.md`
- README relative link check command from the job request

## Verdict
READY FOR REVIEW
