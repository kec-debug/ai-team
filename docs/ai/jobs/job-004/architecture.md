# job-004 — Architecture Review

## Approach

The plan (`gemini-plan.en.md`) adds a **server-driven autonomous pipeline** to the local GUI: one button runs *create-job → save input → Gemini → Claude Architect → Codex → capture diff → Claude Reviewer*, polled via `GET /api/pipeline/status`, with PR creation and merge left to the human.

The intent matches `input.ko.md`. The problem is that the plan **expands the server's execution surface dramatically** — today `web/server.js` only `execFile`s three allow-listed scripts and a few fixed `git`/`tmux` arg-vectors; the proposed pipeline either (a) shells out to `gemini` / `claude` / `codex exec` headlessly, or (b) drives them via tmux paste and watches the filesystem for completion. Both modes have safety mechanics that the plan lists as "open questions" rather than designs. That is what I need closed before the work starts.

Deviations from the plan worth flagging up front:

- **Filename drift from project conventions.** The plan calls the Gemini output `gemini-plan.en.md` (and the file in this job folder is already named that), and the Reviewer output `claude-pr-review.en.md`. The project's existing prompts (`prompts/gemini-manager.md:12`, `prompts/claude-reviewer.md:14`) and the server's allow-list (`web/server.js:18`–`web/server.js:30`) say `plan.en.md` and `review.md`. Pick one set and apply it consistently — do not silently fork.
- **"Yes to all" framing.** The plan says "ensure agents run with 'Yes to all' or non-interactive settings." That phrasing is dangerous; the agent's confirmation prompt for destructive ops *is* the safety, not a UX papercut. The architecture below replaces this with explicit sandbox + allow-list.
- **Acknowledged-but-undesigned items.** Concurrency, timeouts, restart behavior, and step-completion detection are listed as risks/open questions. For a stage that is about to write code touching `web/server.js`, these must be design decisions, not deferred questions.

## Affected files / modules

In scope (write):
- `web/server.js` — new endpoints `POST /api/pipeline/run`, `GET /api/pipeline/status`, optional `POST /api/pipeline/create-pr`; pipeline state object; per-jobId lock; step runner; expand `ARTIFACT_NAMES` (`web/server.js:18`–`web/server.js:30`) to cover any new artifact names (after the naming decision above).
- `web/public/index.html` — "전체 파이프라인 실행" button, status display region, optional "PR 생성" button. Existing four per-role "전송" buttons should remain so manual operation is still possible (good for recovery when the pipeline marks a step "Manual Intervention Required").
- `web/public/app.js` — pipeline trigger, polling loop, status rendering.
- `web/public/style.css` — styling for the status panel only.
- `README.md` — new section describing the pipeline button, the polling UX, the explicit list of what the server does *not* do (commit / push / merge / arbitrary shell), and how to use the "PR 생성" button if added.

Out of scope — read-only, do not touch:
- `scripts/*.sh` — adding a new pipeline script is OK *only* if it is `execFile`'d with a fixed arg vector; otherwise leave alone.
- `prompts/*.md` — touch only if a headless variant is genuinely required; otherwise leave alone.
- `docs/safety-rules.md` — the rules at `docs/safety-rules.md:1`–`docs/safety-rules.md:72` are the source of truth; the README change must point to them, not restate or weaken them.
- `.env`, secrets, auth, payment, DB, infra, `~/.bashrc`, `~/.config/{gh,gemini,claude,codex}/*`.

Forbidden in this job (per `input.ko.md` and `docs/safety-rules.md`):
- Any code path that runs an arbitrary string through a shell (`exec`, `spawn('sh', ['-c', …])`, backticks, `child_process.exec`). All external commands must continue to use `execFile` with an **arg vector**, never an interpolated shell string.
- Any code path that reads files outside `projectDir` or writes outside `docs/ai/jobs/{JOB_ID}/`.
- Any auto `git commit`, `git push`, `gh pr create --merge`, `gh pr merge`, `gh auth ...` mutating call.

## Risks

Ranked. Each risk has a required mitigation; the implementer must address every "*Required:*" item before the reviewer signs off.

1. **(HIGH) Headless agent execution = new code-execution surface on the server.** The plan suggests `execFile` of `gemini` / `claude` / `codex exec`. These CLIs can edit the filesystem, read secrets from the user's home directory, and (with the wrong flags) call other tools. Once the server can invoke them unattended, the server is effectively a remote-code-execution endpoint scoped to whatever the agent CLI can do.
   - *Required:* every CLI invocation uses `execFile(binary, [arg1, arg2, ...], { cwd: projectDir, env: <minimal env>, timeout: <ms> })`. **No** `shell: true`, **no** `child_process.exec`, **no** building a string command and splitting it.
   - *Required:* binary names are an explicit allow-list at the top of `server.js` (e.g. `{ gemini: 'gemini', claude: 'claude', codex: 'codex' }`); subcommands and flags are hard-coded per role, not user-supplied.
   - *Required:* `cwd` is always the validated `projectDir` resolved by the existing `resolveProjectDir()` (`web/server.js:49`); no path comes from the request body unsanitised.
   - *Required:* `env` passed to the child is a curated subset (`PATH`, `HOME`, `TERM`, plus whatever auth env the CLI needs). Do not blanket-pass `process.env`.

2. **(HIGH) Codex autonomous edits can violate the safety-rules envelope.** `docs/safety-rules.md` forbids unattended changes to auth, payment, DB migrations, and infra. A headless `codex exec` with no sandbox can touch any of those.
   - *Required:* `codex exec` is invoked with the most restrictive sandbox mode the CLI supports (workspace-write only, no network, no auto-approve of destructive ops). The implementer must name the exact flag set in `patch.md` and the reviewer must verify it.
   - *Required:* server-side post-step check after Codex finishes: if `git diff --name-only` shows any path matching a deny-list (`.env*`, `**/secrets/**`, `**/migrations/**`, `**/auth/**`, `**/payment/**`, `**/billing/**`, `infra/**`, `.github/workflows/**`), the pipeline is halted, status set to `BLOCKED_SAFETY`, and the human is shown the offending paths. No automatic revert; the human decides.
   - *Required:* the deny-list above is defined once, in code, and re-used by the Reviewer step.

3. **(HIGH) "Yes to all" bypasses the very confirmations that protect the user.** Treat any agent that needs `--yes`-style flags to run headlessly as a step that cannot be auto-run.
   - *Required:* if a CLI's only headless mode is "approve everything", that step must instead be marked **"Manual Intervention Required"** in the UI and the pipeline must pause there. The button to resume must require an explicit click.

4. **(MED) Step-completion detection by "file appeared" is racy.** Partial writes, editor swap files, and CLIs that create the output file before populating it will all trick a `fs.stat`-polling runner into advancing prematurely.
   - *Required:* each step writes its artifact via temp-file + atomic rename (or the runner waits for the agent process to *exit successfully*, not for the file to appear). If the runner uses tmux paste, it must additionally check that the expected artifact exists, is non-empty, and ends with a sentinel (e.g., a `Verdict:` line for the architect, a `## Verdict` section for the reviewer) before moving on.
   - *Required:* per-step timeout (suggest 15 min) with explicit failure state, not silent hang.

5. **(MED) Concurrency: two clicks on the same job race the filesystem and the tmux buffer.** The plan flags this but proposes nothing.
   - *Required:* in-memory `Map<jobId, PipelineState>` keyed by `${projectDir}::${jobId}`. `POST /api/pipeline/run` returns HTTP 409 if a pipeline is already `running` for that key. Status transitions are: `idle → running → (succeeded | failed | blocked_safety | needs_manual)`. Terminal states unlock the key.
   - *Required:* explicit note that state is in-memory only; a server restart loses status. Any child processes started before the restart keep running but are orphaned from the GUI — document this in the README so the human knows to `ps`/`tmux` to clean up.

6. **(MED) `POST /api/pipeline/run` must not block an HTTP worker for 15 minutes.** Plan acknowledges this — solution must be the standard one.
   - *Required:* `/run` validates inputs, registers state, spawns the runner async, returns `{ ok: true, jobKey, startedAt }` immediately. The runner updates the in-memory state as it progresses. The client polls `/status`.

7. **(MED) PR creation button is a hard-to-reverse, externally-visible action.** Even though it's a separate button, once it's there, it will get clicked.
   - *Required:* if the "PR 생성" button is implemented in this job, the server endpoint must: (a) refuse if the current branch is `main` or `master`; (b) push to a branch named with a stable pattern (e.g. `ai/job-${jobId}`) that is not `main`; (c) call `gh pr create --base <default-branch> --head <branch> --draft` with a fixed body template; (d) **never** call `gh pr merge`, `gh pr merge --auto`, `--admin`, or `gh auth`. If any of (a)–(d) cannot be guaranteed in this job, **defer the PR button to a follow-up job** and keep PR creation in the `git-shell` tmux window for now.
   - *Required:* the button must require a confirmation modal in the UI showing the exact branch name and base it will use.

8. **(LOW-MED) Auth/secret exposure via the spawned CLI.** The CLIs read API keys from env or `~/.config/...`. Logging their stdout/stderr to the GUI can leak tokens if a CLI ever echoes its config.
   - *Required:* CLI stdout/stderr captured to `docs/ai/jobs/{JOB_ID}/pipeline.log.md` (append-only, per-step sections), redacted with a simple regex pass for obvious patterns (`sk-…`, `ghp_…`, `xoxb-…`, `Bearer …`). GUI shows the log via the existing `/api/artifact` allow-list path, not a new "stream child stdout to browser" endpoint.

9. **(LOW) Naming inconsistency between plan and existing project conventions.** Already mentioned above. Implementer either renames the new artifacts to match `plan.en.md` / `review.md` (preferred — minimal churn, matches `prompts/*.md`) or updates the prompts and `ARTIFACT_NAMES` in lockstep with a one-line note in `patch.md`.

10. **(LOW) Scope creep into `prompts/`, `scripts/`, `docs/safety-rules.md`.** Tempting "while we're here" edits. *Required:* `git diff --name-only` after implementation must be limited to the files in the **In scope (write)** list above. Anything else is a scope violation and the reviewer must `REQUEST CHANGES`.

11. **(LOW) Server is bound to `127.0.0.1` (`web/server.js:7`).** Good. *Required:* do not introduce a `HOST=0.0.0.0` default, do not add CORS, do not add any auth-less endpoint that can be hit cross-origin. The README must continue to say this is local-only.

## Test strategy

What to test, at which layer, with what fixtures. There are no unit tests in this repo today (`package.json` only has `start`), so the bar is "manual + a thin smoke script", not a full unit-test suite — but the manual checks are mandatory and must be recorded in `patch.md`.

**Unit-ish (Node, no network):**
- `resolveProjectDir`, `validateJobId`, `resolveInside`, `resolveJobArtifact` already exist; reuse them, do not re-implement. New helpers (the deny-list matcher, the redaction regex) should be small pure functions; the implementer should include a 10-line test harness in `patch.md`'s notes section showing inputs/outputs they verified by hand. No new test framework needed for this job.

**Integration (local, real filesystem, mocked agents):**
- Replace the agent CLI binary names with shell scripts that simulate each step (a stub `gemini` that writes a canned `plan.en.md` and exits 0; same for `claude`, `codex`). Run the pipeline end-to-end against a throwaway job ID under a scratch project. Verify:
  - state transitions: `idle → running → succeeded`
  - all expected artifacts appear and are listed by `/api/artifacts`
  - `pipeline.log.md` is written and is readable via `/api/artifact`
  - no `git commit` / `git push` was invoked (`git log -1` and `git status` unchanged on the working branch)
- Concurrency test: hit `/api/pipeline/run` twice for the same `(projectDir, jobId)`; the second must return 409.
- Safety test: stub `codex` to touch `.env` or `infra/foo.yaml`; pipeline must terminate with `blocked_safety` and surface the offending path.
- Timeout test: stub one step to `sleep 9999`; pipeline must mark that step `failed` after the configured timeout, not hang the HTTP worker.

**Manual end-to-end (required, single pass):**
- With real CLIs installed, run one real job (small, docs-only) through the GUI button. Confirm:
  - each agent's artifact is generated and visible in the 산출물 panel
  - the Reviewer's verdict is rendered in the status display
  - no commit, push, or PR happened automatically
  - `git status` shows only the files the agents were supposed to touch

**Fixtures:**
- A `web/test/stub-bin/` directory containing the stub `gemini` / `claude` / `codex` shell scripts used in the integration test. Not loaded in production — controlled by an env var like `AI_TEAM_STUB_BIN=1` that prepends `web/test/stub-bin` to `PATH` only when set. The README must not advertise this; it is for local verification.

**No fixtures needed for:**
- README change (visual render in any Markdown viewer).
- CSS additions (visual check in the running GUI).

## Open questions for the human

Blocking — please answer before implementation:

1. **Artifact filenames.** Are we standardising on the project's existing names (`plan.en.md`, `architecture.md`, `patch.md`, `review.md`) and renaming the plan file currently saved as `gemini-plan.en.md`? Or keeping the plan's new names (`gemini-plan.en.md`, `claude-pr-review.en.md`) and updating `prompts/*.md` + `ARTIFACT_NAMES` everywhere? **Recommendation: standardise on the existing names** — minimal churn, matches `prompts/*.md`, matches what `web/server.js:18`–`web/server.js:30` already accepts.
2. **PR creation in this job — yes or defer?** Implementing a safe "PR 생성" button (Risk 7) is real work and can absolutely fit in a follow-up `job-005`. **Recommendation: defer** unless you specifically want it now. The pipeline button alone is already a sizable change.
3. **Headless mode reality check.** Do `gemini`, `claude`, and `codex` on this machine actually support non-interactive operation with sandbox flags that satisfy Risk 2 and Risk 3? If not, the corresponding steps default to **"Manual Intervention Required"** and the pipeline button only chains the steps it can safely automate. Please confirm this is acceptable rather than requiring "automate everything or nothing".

Non-blocking:

4. Should the existing four per-role 전송 buttons stay visible? **Recommendation: yes**, as a manual override / recovery path when the pipeline pauses at a "Manual Intervention Required" step.

## Verdict

**REQUEST CHANGES.**

The underlying goal is legitimate and consistent with `input.ko.md`. The proposed solution, however, would noticeably enlarge the server's blast radius and currently defers several safety-critical mechanics (sandboxing, concurrency, completion detection, timeouts, restart behavior, naming) to "open questions". Revise `gemini-plan.en.md` (or address inline in `patch.md` planning) so that each *"Required:"* item under **Risks** is a concrete design decision before any code is written. In particular, answer the three blocking questions above.

Re-submit and I will re-review.
