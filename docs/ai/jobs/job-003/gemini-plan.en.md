# Job Plan: job-003 - Enhance GUI usage instructions in README.md

## Goal
Improve the "Browser GUI v1" section in `README.md` to provide clearer, step-by-step instructions for users.

## Context
New users may find the current GUI instructions too brief. Providing a numbered list of steps will improve onboarding and reduce confusion about the workflow.

## In scope
- Update the `README.md` file's "브라우저 GUI v1" section.
- Add a step-by-step guide for using the GUI:
    1. Access via browser.
    2. Input project path.
    3. Input Job ID.
    4. Create job.
    5. Save input (`input.ko.md`).
    6. Execute AI buttons (Manager, Architect, Implementer, Reviewer).
    7. Verify results.
- Explicitly state that automatic commit, push, and merge are not performed.

## Out of scope
- Changing the actual GUI code in `web/`.
- Modifying other sections of `README.md` unless necessary for consistency.
- Automating any git operations.

## Acceptance criteria
- `README.md` contains the new step-by-step guide in the specified order.
- The instructions are easy to follow in Korean (matching the rest of the file's primary language for descriptions).
- The warning about no auto-commit/push/merge is clearly visible.

## Suggested approach
- Locate the "브라우저 GUI v1" section in `README.md`.
- Replace or append the detailed steps after the basic setup instructions.
- Ensure the tone matches the existing documentation (informative and direct).

## Risks & open questions
- None identified. The task is straightforward documentation improvement.

## Files likely to change
- `README.md`
