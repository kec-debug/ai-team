# Implementation Constraints from Claude Architect

Verdict: APPROVE_WITH_CHANGES

Codex must follow these constraints:

1. Keep README.md Korean-primary.
   - Preserve any useful existing English tagline if present.
   - Do not translate Korean sections into English.

2. Do not duplicate README sections.
   - Keep one Quick Start section.
   - Keep one roles table.
   - Keep one tmux navigation block.
   - Improve existing sections instead of adding duplicate versions.

3. Verify tmux window indices against scripts/start-ai-team.sh.
   - Use the real tmux indices:
     0: gemini-manager
     1: claude-architect
     2: codex-implementer
     3: claude-reviewer
     4: git-shell

4. Keep the pre-push checklist short.
   - Use 5 to 7 bullets.
   - End with links to docs/safety-rules.md and docs/workflow.md.
   - Do not restate all safety rationale in README.md.

5. Clarify the difference between example jobs and real jobs.
   - examples/job-001/input.ko.md is only a reference example.
   - Real jobs are created under docs/ai/jobs/<JOB_ID>/ by ./scripts/create-job.sh.

6. Preserve link integrity.
   - All relative links in README.md must resolve to existing files.

7. Do not modify scripts/.
   - This job should touch only README.md and job artifact files if needed.

8. Do not introduce secrets or credential examples.
   - No API keys.
   - No tokens.
   - No passwords.
   - No .env examples.

9. Do not recommend direct push to main.
   - Recommend branch + PR workflow only.
