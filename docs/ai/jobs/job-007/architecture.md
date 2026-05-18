# job-007 — Architecture Review

## Approach

The plan (`gemini-plan.en.md`) and the prepared `codex-prompt.en.md` describe a deliberately bounded job:

1. **Functional QA** of the existing GUI features (pipeline button, status, tmux view, approve/reject/abort, restarts, artifacts, git status/diff, reviewer summary).
2. **Frontend usability polish**: tidy buttons, separate primary vs. advanced controls, make the "waiting for approval" state visually obvious, add a static post-run guidance/checklist for the human's remaining manual steps (review diff → commit → PR → merge).
3. **Future-work documentation** for items the user explicitly de-scoped (commit/PR/merge automation, auto-start on boot, GUI auth, CI validators, multi-project polish).

This matches `input.ko.md` precisely. The plan's "Out of scope" / "Strictly Forbidden" list and the codex-prompt's "Strict Safety Boundaries" both faithfully echo the Korean request.

A lot of the structural work the plan calls for **already exists** in the codebase and should be recognised, not reinvented:

- `web/public/index.html:125`–`web/public/index.html:138` already has a collapsed `<details class="advanced-panel">` that groups `startTeam`, `createJob`, `saveInput`, the four `data-send=` role buttons, `gitStatus`, and `gitDiff` as "advanced". Primary vs. advanced separation is already there in skeleton form.
- `web/server.js:222` (`pipelineMessage`) and `web/server.js:244` (`nextRecommendedAction`) already compute human-facing guidance text. The frontend should consume those rather than re-deriving messages client-side.
- `web/server.js:382` (`looksLikeApprovalPrompt`) and the resulting `waitingApproval` field on the status response are how "waiting for approval" is detected. The plan's stated open question ("exact state mapping… might require careful parsing") is **already solved on the backend** — the frontend just needs to render the boolean prominently, not parse anything.

Two deviations worth flagging, neither blocking:

- **Filename drift continues.** This job's plan is named `gemini-plan.en.md`, not the `plan.en.md` defined in `prompts/gemini-manager.md:12`. By now both names appear in `ARTIFACT_NAMES` at `web/server.js:35`–`web/server.js:50`, so the train has left the station. Recommend a separate follow-up job to consolidate; do not address it in this job.
- **"Minor, safe backend data-formatting in `server.js`" in the codex-prompt** is loosely worded. Binding interpretation below under Risks #2.

## Affected files / modules

In scope (write):
- `web/public/index.html` — reorganise existing buttons; add a static "최종 수동 작업" checklist section near `web/public/index.html:103`–`web/public/index.html:123` (the `result-summary` panel); ensure the "waiting for approval" indicator currently at `web/public/index.html:69`–`web/public/index.html:72` is given visual weight (move to top of the status panel, add an icon/class, etc.).
- `web/public/style.css` — new class(es) for waiting-for-approval emphasis, current-step highlight, and the checklist; minor layout adjustments. No removal of existing classes that `app.js` toggles.
- `web/public/app.js` — render the new highlight class when the status response has `waitingApproval: true`; render the checklist; surface `state.nextActionDetails` (or whatever the server already emits via `publicPipelineState` at `web/server.js:182`). No new fetch endpoints.
- `docs/ai/jobs/job-007/` — `patch.md` and `codex-summary.en.md` as normal; **add `future-work.md`** in this folder for the de-scoped items listed in `input.ko.md` lines 60–67.

In scope (read-only, may consult but not modify behavior):
- `web/server.js` — see Risks #2 for what is and isn't permitted here.

Out of scope — do not touch:
- `scripts/*.sh`
- `prompts/*.md`
- `docs/safety-rules.md`, `docs/setup.md`, `docs/workflow.md`
- All safety primitives in `web/server.js`: `SAFE_WINDOWS` (`:12`), `ALLOWED_TMUX_WINDOWS` (`:18`), `SAFETY_DENY_PATTERNS` (`:51`), `PIPELINE_STEP_TIMEOUT_MS` (`:25`), `redactedOutput` (`:132`), `validateJobId` (`:93`), `resolveInside` (`:100`), `resolveJobArtifact` (`:113`), `looksLikeApprovalPrompt` (`:382`), `isDeniedSafetyPath` (`:431`), `runFile` (`:65`), the `127.0.0.1` bind (`:7`), the `express.json({ limit: '1mb' })` body cap (`:62`), and all existing route handlers' behavior.
- `.env`, secrets, tokens, API keys, `~/.config/{gh,gemini,claude,codex}/*`
- The list of forbidden topics in `input.ko.md` lines 44–57.

## Risks

Ranked. Each carries a *Required:* item the reviewer will check the diff against.

1. **(MED) "Layout cleanup" silently breaks `app.js` handlers.** `web/public/app.js` looks up elements by ID (`#projectDir`, `#jobId`, `#inputKo`, `#refreshStatus`, `#runPipeline`, `#pipelineStatus`, `#resetPipeline`, `#approveOnce`, `#approveSession`, `#rejectAction`, `#interruptAction`, `#restartAiTeam`, `#restartGui`, `#refreshTmuxOutput`, `#loadArtifacts`, `#gitStatus`, `#gitDiff`, `#clearOutput`, and the four `[data-send]` buttons). Moving a button is fine; **deleting the ID or the element silently disables the handler**.
   - *Required:* every `id="..."` and `data-send="..."` attribute currently referenced from `app.js` must still resolve to an element after the reorganisation. If a button is genuinely redundant, demote it to the advanced `<details>` rather than removing it. The reviewer checks this by grepping `app.js` for `querySelector(`/`getElementById(` and confirming each selector still hits.

2. **(MED) "Minor, safe backend data-formatting in `server.js`" is undefined.** This phrasing in `codex-prompt.en.md:11` could be stretched.
   - *Required (binding interpretation):* the **only** server changes permitted in this job are (a) *additive* fields on the JSON returned by existing endpoints (e.g., extending `publicPipelineState` at `web/server.js:182`, or adding a `userChecklist`/`nextActionDetails` field to the status response), or (b) new *pure* helper functions referenced only by those response builders. **Forbidden in this job:** new endpoints, changes to any safety primitive listed under "Out of scope" above, changes to what files can be read or written, changes to what processes can be spawned, changes to redaction, changes to deny-list semantics, changes to the body-size cap or the 127.0.0.1 bind. If the implementer feels they need any of those, they must stop and ask — do not edit them inside this job.

3. **(MED) "Checklist UI" scope creep.** A "checklist" can mean static HTML, or it can quietly grow into per-user state, localStorage, or worse.
   - *Required:* the checklist is **static markup** in `index.html` plus optional CSS strike-through for items the user clicks. No `localStorage`, no backend persistence, no per-job state, no API call. The list content is hard-coded and matches `input.ko.md` lines 60–67 plus the standard "review diff → commit → PR → merge" suffix. Acceptable interactive behavior: a single `change` listener on checkboxes that toggles a CSS class on the `<li>`. Nothing else.

4. **(MED) Safety-text removal during "cleanup".** Two existing safety affordances must survive a redesign:
   - The Korean field hint at `web/public/index.html:33` ("쉘 설정 명령, 실행 명령, 토큰, 비밀값은 넣지 않습니다") — this is a user-facing safety rail. *Required:* the same warning text remains visible near the `inputKo` textarea after the reorganisation.
   - The warning text at `web/public/index.html:80` ("승인은 현재 AI CLI 창에 키 입력을 보내는 기능입니다. 위험한 명령은 승인하지 마세요") — *Required:* this must remain visible next to the approve buttons. Do not collapse it into a tooltip-only state.

5. **(LOW-MED) "Functional QA" with no test harness.** The codex-prompt says "run the necessary tests" but there is no test suite. The risk is an implementer inventing an auto-click harness, or skipping QA entirely.
   - *Required:* the QA result lives in `patch.md` as a **manual checklist** with one line per item in `input.ko.md` lines 21–31, each marked ✓ / ✗ / N/A with a one-line note. No new test framework, no headless browser, no Puppeteer/Playwright in this job. The concrete checklist is in **Test strategy** below.

6. **(LOW) "Future-work" file leaking actionable steps.** The de-scoped items in `input.ko.md` lines 60–67 are sensitive (auth, auto-start, CI). If `future-work.md` accidentally contains ready-to-run commands or config, a future careless run could execute them.
   - *Required:* `future-work.md` describes *what* and *why*, not *how*. No `sudo ...`, no `systemctl ...`, no `gh ...` mutating commands, no example `.env` content, no example auth code. Each item links to relevant docs (`docs/safety-rules.md`) for what human approval would require.

7. **(LOW) Reset pipeline button at primary-level visibility.** `#resetPipeline` (`web/public/index.html:44`) clears pipeline state — destructive in the small sense (loses status visibility for an in-flight pipeline).
   - *Suggested (not required):* keep `#resetPipeline` in the status panel but visually de-emphasise it (smaller, secondary styling), OR demote it to the advanced `<details>`. Implementer's call; reviewer not to block on this.

8. **(LOW) Documentation drift if README changes are smuggled in.** The plan does **not** list `README.md` in "Files likely to change" but `input.ko.md` doesn't forbid touching it. If the implementer adds README updates "while there", that is scope creep for this job.
   - *Required:* if the implementer decides README changes are needed, they must be limited to a brief pointer to the new in-GUI checklist, and they must be called out explicitly in `patch.md` so the reviewer sees them. Otherwise leave the README alone.

9. **(VERY LOW) Filename consolidation.** Already discussed above. Out of scope for this job; defer.

## Test strategy

No automated tests. The work is verified by a structured manual pass, recorded in `patch.md`.

**Manual functional QA (required — one line per item, recorded in `patch.md`):**

Start the GUI (`cd web && npm start`), pick a throwaway job ID, and verify each of the following. Mark each ✓ / ✗ / N/A with a one-line note.

1. `전체 파이프라인 실행` triggers `POST /api/pipeline/run`, response 200, status panel transitions `idle → running`.
2. Status panel auto-refreshes (or refresh button works) and shows current stage advancing through Gemini → Architect → Codex → Reviewer.
3. While a stage is running, `현재 단계` and `tmux 대상 창` are populated and match `PIPELINE_STAGES` at `web/server.js:29`–`web/server.js:34`.
4. When an AI CLI prompts for approval, `승인 대기 추정` flips to a truthy value and the new visual highlight is obvious.
5. The five `제어할 tmux 창` options match `ALLOWED_TMUX_WINDOWS` at `web/server.js:18`–`web/server.js:24`.
6. `승인 / 계속 진행`, `세션 승인`, `거절`, `중단` all hit their endpoints; each returns 200; the chosen tmux window receives the corresponding keystroke (verified by attaching to tmux briefly).
7. `AI팀 재시작` and `GUI 서버 재시작` work and the page recovers (server restart will drop the socket — confirm a reload reconnects).
8. `실시간 tmux 출력` populates from `GET /api/tmux/output` and the redaction at `web/server.js:132` (`redactedOutput`) is active — paste a test token like `sk-test1234567890` into a tmux window and confirm it does not appear verbatim in the GUI.
9. `목록 새로고침` lists every file in `ARTIFACT_NAMES` (`web/server.js:35`–`web/server.js:50`) that exists in the job folder; clicking one renders its content.
10. `git status` and `git diff` panels render output.
11. After the Reviewer finishes, `최종 결과` shows artifacts, diff summary, review status, and the new "다음 권장 작업" / checklist content.
12. The new checklist's items match `input.ko.md` lines 60–67 and the standard "review diff → commit → PR → merge" suffix.
13. The "do not enter shell commands" hint near `inputKo` is still visible (Risk #4).
14. The "위험한 명령은 승인하지 마세요" warning near the approve buttons is still visible (Risk #4).
15. With browser devtools open, no console errors during a full pipeline pass.

**Static checks (required, recorded in `patch.md` as a single ✓ line each):**

- `git diff --name-only` lists only files in the **In scope (write)** section above. Anything else fails the review.
- `grep -E "(querySelector|getElementById|data-send)" web/public/app.js` — every selector resolves to a present element in the updated `index.html` (Risk #1).
- `grep -nE "SAFE_WINDOWS|ALLOWED_TMUX_WINDOWS|SAFETY_DENY_PATTERNS|redactedOutput|looksLikeApprovalPrompt|isDeniedSafetyPath|validateJobId|resolveInside|resolveJobArtifact|HOST.*127\\.0\\.0\\.1|express\\.json.*limit" web/server.js` — diff vs. main shows **zero** changes to these lines (Risk #2).

**Fixtures:** none beyond an existing job folder to point the GUI at. A previously-completed `job-006` or fresh throwaway job ID is fine.

## Open questions for the human

None blocking. One non-blocking question, decide before merge:

1. The `#resetPipeline` button (Risk #7) — keep it at primary visibility, de-emphasise visually, or move into the advanced `<details>`? My weak preference: de-emphasise visually but keep where it is, because a stuck pipeline panel needs an obvious recovery affordance.

## Verdict

**APPROVE**, with the *Required:* items under **Risks** and the checklist under **Test strategy** as binding constraints. The reviewer will check the patch against this document, not against the plan alone.

Rationale: the request in `input.ko.md` is explicitly cautious and de-scopes every high-risk item; the plan and codex-prompt both honour that; the proposed changes are frontend-mostly with a narrowly-bounded server.js allowance that I've defined precisely in Risk #2. Existing safety primitives in `web/server.js` are well-factored and outside the touch surface. The only real failure modes for this job are (a) accidentally breaking `app.js` handlers by renaming/deleting button IDs, (b) over-interpreting "minor backend data-formatting", and (c) deleting the two safety-warning texts during cleanup — all three are now explicit *Required:* checks the reviewer can verify mechanically.

Codex Implementer may proceed.
