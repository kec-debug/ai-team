# job-004 — Claude Reviewer

## Verdict

**REQUEST CHANGES.**

The intent matches `input.ko.md`. The implementer correctly **rejected** the highest-risk path the plan flirted with (headless `execFile` of `gemini` / `claude` / `codex exec` with `--yes`-style flags) and instead reused the existing fixed tmux paste flow. That single decision avoids the largest item in `architecture.md` Risk 1 and Risk 3, and is the right call.

What is not yet right: two of the architect's HIGH-severity *Required* mitigations are only **partially** implemented. The post-Codex safety check cannot see new untracked secrets, and the step-completion detector advances on any non-empty file, with no sentinel. Both are quoted directly from `architecture.md` and both can be tightened with a few lines of code. There is also one spec deviation (the "PR 생성 별도 버튼" from `input.ko.md` §4 is not in the patch and the deferral is not recorded anywhere a human will find it).

Safety envelope holds: no secrets/`.env`/credentials in the diff, no auth/payment/DB-migration/prod-infra changes, no `commit`/`push`/`merge`/`gh pr merge` wiring, server still binds 127.0.0.1, scope stays inside the architect's "In scope (write)" list, nothing has been pushed to `main`.

## Findings

### Blockers

None.

### Major

- **`web/server.js:289`–`web/server.js:299`, used at `web/server.js:396`–`web/server.js:405` — post-Codex safety check is blind to untracked files.**
  `changedFiles()` calls `git diff --name-only -- .`, which only reports **tracked** modifications. A Codex run that creates a new `.env.production`, `secrets/openai.txt`, `migrations/0042_drop_users.sql`, or `infra/foo.yaml` will leave the deny-list (`web/server.js:37`–`web/server.js:46`) with nothing to match, and the pipeline will advance past the "안전 차단" gate as if no rule were violated. `architecture.md` Risk 2 was explicit: *"server-side post-step check after Codex finishes: if `git diff --name-only` shows any path matching a deny-list ... the pipeline is halted"* — that requirement was written assuming a tracked diff was sufficient; in practice the post-step check must union `git diff --name-only -- .` with `git ls-files --others --exclude-standard` (or use `git status --porcelain -uall`) and feed every reported path through `isDeniedSafetyPath`. *Confirmed by inspection of the regex (`web/server.js:79`) and the `git diff` behaviour — git's diff only walks the tracked index.*

- **`web/server.js:266`–`web/server.js:287` — step-completion detection is racy and has no sentinel.**
  `findFirstExistingArtifact` returns a hit as soon as the expected file exists, is non-empty, and has `mtimeMs >= sinceMs`. `architecture.md` Risk 4 *Required* was: *"atomic rename **or** wait for the agent process to exit successfully ... additionally check that the expected artifact exists, is non-empty, **and ends with a sentinel** (e.g., a `Verdict:` line for the architect, a `## Verdict` section for the reviewer) before moving on."* None of the three guards (atomic rename, process-exit signal, sentinel) is present. Practical consequences: a partially flushed `architecture.md` (one byte, fsync pending) passes; the next step ("Codex 전송") then fires against an incomplete context. A separate timing edge: `stat.mtimeMs` is second-resolution on some filesystems and is being compared to a millisecond `Date.now()` — a file written in the same wall-clock second as `sinceMs` can be falsely rejected. Add per-step sentinel checks (architect → `## Verdict`; codex → `## Verdict` or `READY FOR REVIEW`; reviewer → `## Verdict`) and floor `sinceMs` to whole seconds before comparing.

- **`web/server.js:79`–`web/server.js:84` — `validateJobId` accepts `.`, `..`, and any all-dot value.**
  The regex `/^[A-Za-z0-9._-]+$/` matches `.`, `..`, and `....` (verified by running the regex). With `jobId='..'`, `path.join(projectDir, 'docs', 'ai', 'jobs', '..', 'pipeline.log.md')` resolves to `<projectDir>/docs/ai/pipeline.log.md` — still inside `projectDir`, but outside the `docs/ai/jobs/<jobId>/` envelope that the rest of the pipeline assumes. That clobbers any file at that path on every run, and the artifact endpoint's `resolveJobArtifact` guard (`web/server.js:99`–`web/server.js:107`) accepts the rewritten path too (the relative path passes its `parts[0..2]` check). Job-004 is the first job whose code consumes `jobId` for an in-memory key, a log path, and a directory creation in the server; this pre-existing weakness now has more weight. Reject `jobId === '.'`, `jobId === '..'`, and `/^\.+$/`; also reject a leading hyphen so a future migration to argv-style consumption doesn't reintroduce `--option` confusion.

- **Acceptance-criteria deviation: `input.ko.md` §4 "PR 생성은 별도 버튼으로 둔다" is not implemented and the deferral is not recorded anywhere.**
  `architecture.md` Risk 7 recommended deferring the PR button to a follow-up job, and that recommendation is sound (the safe-by-default semantics it would need are real work). But `codex-summary.en.md` says only *"No commit, push, PR creation, merge, or deployment automation was added"* — phrased as a safety property, not as a documented gap against the input spec. The new README section likewise tells the human the pipeline doesn't auto-create PRs, but never mentions the originally requested button or where it went. `docs/ai/jobs/job-005/` is an empty skeleton; nothing in this branch points the human there. Add one line to `codex-summary.en.md` ("PR 생성 버튼은 `architecture.md` Risk 7 권고에 따라 후속 job으로 연기됨") and a sentence to the README pipeline section telling the human PR creation still happens in the `git-shell` tmux window.

### Minor

- **`web/server.js:340`–`web/server.js:353` — `updateReviewSummary` decision-line regex returns the heading, not the verdict.**
  `find(line => /decision|verdict|approve|request changes|comment/i.test(line))` matches the **first** line containing any of those words. A `review.md` that follows `prompts/claude-reviewer.md` has `## Verdict` as a heading; the actual `APPROVE` / `REQUEST CHANGES` / `BLOCK` token sits on the next non-blank line (and is often bold, e.g. `**REQUEST CHANGES.**`). The current code returns the string `"## Verdict"` as the decision, which is unhelpful to the human. Match `^##\s*Verdict\b` first, then read the next non-blank line; or scan directly for the literal tokens `APPROVE`, `REQUEST CHANGES`, `BLOCK`.

- **`web/server.js:625`–`web/server.js:642` — `/api/send/*` endpoints ignore the pipeline lock.**
  The four per-role endpoints (`gemini`, `claude-architect`, `codex`, `claude-reviewer`) bypass `pipelineStates`. A human clicking "Codex Implementer 전송" while the in-memory pipeline is in its `waitForArtifact` poll will fire a second prompt at the same tmux window, racing the file-mtime detector and confusing both runners. Either gate these endpoints with the same 409 check used by `/api/pipeline/run`, or restrict them to terminal states (`failed` / `needs_manual` / `blocked_safety`) so the manual override is only available for recovery.

- **`web/server.js:566`–`web/server.js:602` — TOCTOU window in `/api/pipeline/run`.**
  Between `existing.status === 'running'` (line 573) and `pipelineStates.set(key, state)` (line 584) there are two `await`s (`fs.mkdir`, `fs.writeFile`). Two simultaneous POSTs to the same key can both pass the check and both spawn a runner. Node's single-threaded model doesn't save you here — the awaits explicitly yield. Move the state insert to *before* any `await`, or check-and-set within the same synchronous tick.

- **`web/server.js:20` — `pipelineStates` accumulates without eviction.**
  The same `(projectDir, jobId)` key gets overwritten on subsequent runs, but distinct keys are never freed. For a long-running local server, terminal states (`succeeded` / `failed` / …) stick around and the GUI re-renders last week's diff/review when the same job ID is opened. Either evict on terminal-state transition older than N runs, or surface `state.finishedAt` next to the summary so the human can tell historical from current.

- **`web/server.js:118`–`web/server.js:124` — redaction list is starter-only.**
  OpenAI / GitHub / Slack / Bearer is a reasonable seed, but `pipeline.log.md` is rendered through `/api/artifact` to the browser. Add at minimum AWS access keys (`AKIA[0-9A-Z]{16}`), Google API keys (`AIza[0-9A-Za-z_-]{35}`), and generic `Basic [A-Za-z0-9+/=]{20,}`. Note also that `/api/artifact` (`web/server.js:676`–`web/server.js:693`) reads the artifact verbatim — only the *write* path is redacted. That is fine *today* because `pipeline.log.md` is the sole server-written artifact that consumes child-process output, but it is a fragile invariant; a comment at the read site noting "redaction happens at write" would prevent a future regression.

- **`web/server.js:506`–`web/server.js:516` — shared tmux paste buffer, never deleted.**
  `bufferName = 'ai-team-gui-prompt'` is reused for every send. Concurrent pipelines for *different* `(projectDir, jobId)` will overwrite each other's buffer between `set-buffer` and `paste-buffer`. Add a per-call unique buffer name (e.g. `ai-team-gui-${Date.now()}-${random}`) and `tmux delete-buffer -b <name>` after the send, so neither the race nor a left-over secret in the user's clipboard happens.

- **README "브라우저 GUI v1" section — does not name `blocked_safety` or what triggers it.**
  The diff names `needs_manual` and explains its meaning, but `blocked_safety` (the state the post-Codex deny-list produces) is never mentioned. The human reading the README cannot tell when the pipeline will halt for safety reasons or which paths the server treats as forbidden. Add a single sentence pointing at `docs/safety-rules.md` and listing the deny-pattern families (`.env*`, `secrets/`, `migrations/`, `auth/`, `payment/`, `billing/`, `infra/`, `.github/workflows/`).

### Nits

- **`web/server.js:454`–`web/server.js:497` — `buildPrompt` accepts `inputKo` for every role but only the `gemini` branch uses it.** Drop the parameter from the other three branches (or stop passing it from `runPipeline`). Cosmetic.
- **`web/public/app.js:3`, `web/public/index.html:27` — default `jobId` hard-coded to `job-002`.** Also pinned to `localStorage` on first run. A new operator opens the GUI staring at last month's job. Default to `""` or to a today-date pattern.
- **`web/public/app.js:22`–`web/public/app.js:32` — default `inputKo` textarea content is the job-002 brief.** Same first-run UX issue.
- **`docs/ai/jobs/job-004/pipeline.log.md`** — captures a real partial run that stopped after the `gemini` send with `(no output)`. Useful as a forensic artifact, but the file is checked into the job folder and is what `/api/artifact` will show the next operator. If you regenerate the log on a fresh run, that is fine; if you keep this one as evidence, add a one-line preamble explaining what it was.
- **`web/.gitignore`** (untracked, 14 bytes) — out of scope to inspect in detail, but worth a glance before commit so it doesn't accidentally ignore something the human will then have to chase.

## Suggested fixes (priority order)

1. **Catch untracked safety violations.** New helper `safetyChangedFiles(projectDir)` that returns the union of `git diff --name-only -- .` and `git ls-files --others --exclude-standard`. Use it (and only it) for the post-Codex check at `web/server.js:396`–`web/server.js:405`. Keep `changedFiles()` for the diff-summary use case where untracked-status doesn't matter.
2. **Sentinel-check before advancing.** After `waitForArtifact` returns a hit, read the first ~4 KB and require the per-step sentinel listed above. If absent, keep polling until the timeout, then mark `needs_manual` with a message naming the missing sentinel. Floor `sinceMs` to whole seconds.
3. **Tighten `validateJobId`** to reject `.`, `..`, all-dot, and leading-hyphen values.
4. **Fix `updateReviewSummary`** to find `## Verdict` and return the next non-blank line.
5. **Record the PR-button deferral** in `codex-summary.en.md` and add a one-line README note. Optionally update `docs/ai/jobs/job-005/input.ko.md` with the carry-over scope so it's not lost.
6. Gate `/api/send/*` with the pipeline lock, or restrict it to terminal states.
7. Per-call unique tmux buffer name + `delete-buffer` after send.

## Sign-off checklist

- [x] Scope matches `gemini-plan.en.md` — files touched (`web/server.js`, `web/public/index.html`, `web/public/app.js`, `web/public/style.css`, `README.md`) are exactly the architect's "In scope (write)" set. No scope creep into `scripts/`, `prompts/`, or `docs/safety-rules.md`.
- [ ] All acceptance criteria covered — **"PR 생성 별도 버튼"** from `input.ko.md` §4 is missing and the deferral is undocumented (Major item above).
- [ ] Tests cover the strategy from `architecture.md` — no stub `gemini` / `claude` / `codex` scripts under `web/test/stub-bin/`, no concurrency test (the 409 path), no safety test (deny-list triggering), no timeout test. `codex-summary.en.md`'s verification list is `node --check`, one curl against `/api/pipeline/status`, and `git diff --stat`. The architect explicitly accepted "manual + a thin smoke script"; even the smoke script is absent.
- [x] No secrets / `.env` / credentials added — verified by grep against the working tree: no matches for `sk-`, `ghp_`, `AKIA`, `AIza`, `BEGIN PRIVATE KEY` in the diff.
- [x] No auth / payment / DB-migration / prod-infra changes.
- [x] No push to `main` — branch is `feat/job-004-one-button-pipeline`; nothing has been committed yet (working tree only). PR creation and merge are explicitly out of this code path.
- [x] No auto-merge wiring — no `gh pr merge`, no `--auto`, no Mergify/Bulldozer config touched.

## Notes for the human

- The two Major code issues (untracked-file blindness, sentinel-less completion) are both small diffs to `web/server.js`. They are the difference between *"the safety check exists"* and *"the safety check actually works"*; please don't merge before they are addressed.
- The implementer's biggest correct decision was to **not** shell out to `codex exec --yes` headlessly. Preserve that decision when fixing the items above — do not slip into auto-approve flags as a shortcut for the sentinel check.
- The pipeline still depends on tmux paste working end-to-end against the real `gemini-manager` / `claude-architect` / `codex-implementer` / `claude-reviewer` windows. The captured `pipeline.log.md` in this job folder shows a run that got as far as the gemini paste and then produced `(no output)` — confirm one full real-job pass before sign-off; the regex/unit fixes above won't catch a tmux paste regression.
- I am not the merger. Even after a re-review brings the verdict to `APPROVE`, the human is the one who creates the branch commit, opens the PR, and presses merge.
