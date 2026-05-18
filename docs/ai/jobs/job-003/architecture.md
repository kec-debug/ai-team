# job-003 — Architecture Review

## Approach

The Korean request in `input.ko.md` asks for one thing: make the **browser GUI flow** in the top-level `README.md` easier to follow, end‑to‑end, in this exact order:

1. open the browser at the GUI URL
2. enter the project path
3. enter the job ID
4. create the job folder
5. save `input.ko.md`
6. press the AI buttons (Gemini → Claude Architect → Codex → Claude Reviewer)
7. confirm the result (artifacts / git status)

…and to **explicitly state** that the GUI does not auto-commit, auto-push, or auto-merge.

This is a documentation-only change to `README.md`. No server, script, or web/ code should be modified.

> Deviation note: the formal input to this stage is `docs/ai/jobs/job-003/plan.en.md` (from Gemini Manager). That file is **not present** in the job folder at review time — only `README.md` and `input.ko.md` exist. I cannot give a final `APPROVE` against a plan that does not exist. The guidance below is the architecture envelope the eventual plan must stay inside.

## Affected files / modules

In scope (write):
- `README.md` — extend or rewrite the existing **"브라우저 GUI v1"** section (currently `README.md:70`–`README.md:97`) with a numbered 1–7 walkthrough mirroring `input.ko.md`. The auto‑commit/push/merge prohibition belongs inside that same section (it is currently mentioned at `README.md:97` and again in the safety summary at `README.md:117`–`README.md:124`; the GUI section should restate it locally so a beginner sees it without scrolling).

Out of scope (read-only, do not touch):
- `web/server.js` — endpoints, prompts, and the `SAFE_WINDOWS` whitelist are the source of truth for what each button does; the README must describe what is actually wired up, not aspirational behavior.
- `web/public/index.html`, `web/public/app.js`, `web/public/style.css` — button labels in the docs must match the labels in `index.html:33`–`index.html:47` ("AI 팀 시작", "작업 폴더 생성", "input.ko.md 저장", "Gemini Manager 전송", "Claude Architect 전송", "Codex Implementer 전송", "Claude Reviewer 전송", "git status", "git diff", "목록 새로고침").
- `scripts/*`, `prompts/*`, `docs/setup.md`, `docs/workflow.md`, `docs/safety-rules.md` — link to them, do not duplicate or contradict them.
- `.env`, secrets, auth, payment, DB, infra — explicitly forbidden; none should appear in the diff.

## Risks

Ranked, each with a mitigation.

1. **Scope creep into code (high impact, low likelihood).** A "small README fix" is a classic vehicle for sneaking in changes to `server.js` or `app.js`. *Mitigation:* the implementer must produce a diff that touches **only `README.md`**. The reviewer must reject any patch.md that lists other paths.
2. **Documentation drift vs. real GUI behavior (medium).** If the README claims a button does something the server does not implement (e.g., "Codex 전송이 자동으로 커밋합니다"), users will trust the doc and be surprised. *Mitigation:* every documented button must be traceable to a handler in `web/server.js` (`/api/start`, `/api/create-job`, `/api/save-input`, `/api/send/{gemini,claude-architect,codex,claude-reviewer}`, `/api/git/status`, `/api/git/diff`, `/api/artifacts`). The "AI 버튼 실행" step must show the four roles in workflow order (Gemini → Claude Architect → Codex → Claude Reviewer), matching `index.html:43`–`index.html:46` and `server.js:214`–`server.js:218`.
3. **Inconsistent or weakened safety statement (medium).** Phrasing like "보통은 자동 커밋하지 않습니다" or "v1에서는" with a future-tense escape hatch undermines the rule. *Mitigation:* the new section must state, unambiguously and in present tense, that the GUI **does not** run `git commit`, `git push`, or `git merge`, and that those steps happen by hand in the `git-shell` tmux window. This matches the existing line at `README.md:97` and the safety summary at `README.md:117`–`README.md:124`; do not contradict either.
4. **Bilingual duplication divergence (low).** The README currently uses Korean for the GUI section and bilingual phrasing at the top. *Mitigation:* keep the new walkthrough in Korean (the audience is the same one that wrote `input.ko.md` in Korean). Do not introduce a parallel English copy in this job — that is a separate change.
5. **Stale port / host facts (low).** The current text hard-codes `http://127.0.0.1:3100` (`README.md:72`). Defaults live in `web/server.js:7`–`web/server.js:8`. *Mitigation:* keep the same defaults and the same `HOST=… PORT=… npm start` override note; do not invent new defaults.
6. **Step 7 ("결과 확인") ambiguity (low).** "Result" could mean tmux output, artifacts panel, or git diff. *Mitigation:* point to the **산출물** panel (`docs/ai/jobs/<JOB_ID>/` artifacts surfaced via `/api/artifacts` — see `server.js:18`–`server.js:30` for the allow-listed filenames) **and** the **git 확인** panel (`git status`, `git diff`) as the two places to verify the result. Mention that the human still does the actual commit/PR in the `git-shell` window.

## Test strategy

There is no executable test for prose. The verification plan is:

- **Manual render check (required).** Open `README.md` in a Markdown viewer (GitHub preview or VS Code preview). Confirm the seven numbered steps appear in the order listed in `input.ko.md`, that each step names a real button from `web/public/index.html`, and that the auto-commit/push/merge prohibition is in the same section.
- **Live walkthrough (required, single pass).** With the dev server running (`cd web && npm start`), follow the README's 1–7 steps for a throwaway job ID (e.g. `job-readme-smoke`). Each documented click must succeed against `web/server.js`. After step 7, confirm no commit/push/merge happened automatically (`git log -1` and `git status` are unchanged on the working branch).
- **Diff scope check (required).** `git diff --name-only` must list `README.md` and nothing else. `patch.md` must say the same. Any other file in the diff is a failed review.
- **Link check (recommended).** All in-repo links in the changed section (e.g. `docs/setup.md`, `docs/workflow.md`, `docs/safety-rules.md`, `prompts/…`) must resolve to existing files.
- **No fixtures needed.** This is a docs change; there is no unit/integration layer to extend.

## Open questions for the human

Blocking:

1. **Where is `plan.en.md`?** The architect stage's defined input is `docs/ai/jobs/job-003/plan.en.md`. It is missing. Please run the Gemini Manager step (or paste the plan manually) and re-run the architect. Until then I cannot give a final `APPROVE`.

Non-blocking (decide before implementation, but the answer does not change the verdict):

2. Should the new GUI walkthrough **replace** the current "브라우저 GUI v1" section (`README.md:70`–`README.md:97`), or **sit above it** as a "처음 사용자를 위한 7단계" subsection while the existing prose stays? My recommendation: replace, to avoid two near-duplicate descriptions drifting apart.
3. Should the README also link to `examples/job-001/input.ko.md` from step 5 ("input 저장") as a sample for first-time users? Cheap to add, useful, but strictly outside the literal `input.ko.md` request.

## Verdict

**REQUEST CHANGES.**

Reason: the required input artifact `docs/ai/jobs/job-003/plan.en.md` is not present, so there is no plan to approve. The underlying task itself (README-only docs edit) is low-risk and would be approvable once the plan exists and stays inside the envelope above: **`README.md` only, no code, no auto-commit/push/merge, button names match `web/public/index.html`, behavior claims match `web/server.js`.**

Re-submit after Gemini Manager produces `plan.en.md` in this folder.
