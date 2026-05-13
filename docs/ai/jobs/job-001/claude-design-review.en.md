# Claude Architect Design Review — Job 001

**Subject:** Improve README.md to be more beginner-friendly
**Plan reviewed:** `docs/ai/jobs/job-001/gemini-plan.en.md`
**Codex prompt reviewed:** `docs/ai/jobs/job-001/codex-prompt.en.md`
**Reviewer:** Claude Architect

---

## 1. Approach

The plan is sound for the requested scope: a docs-only edit to `README.md`. The 7-step workflow stage 3 (architecture review) is normally optional for trivial README edits, but several real risks below justify keeping it. No deviation from the stated scope is recommended — the deviations needed are *clarifications*, not redesigns.

## 2. Task clarity & safety

| Check | Result |
|---|---|
| Single-file blast radius (`README.md` only) | OK — explicitly bounded |
| No `scripts/` modifications | OK — prohibited in plan and prompt |
| No secrets / `.env` / tokens added | OK — prohibited |
| No `main`-push recommendation | OK — pre-push checklist forbids it |
| Touches auth / payments / DB migrations / prod infra | No |
| Auto-commit / auto-push / auto-merge implied | No |
| Scope expansion beyond `input.ko.md` | No |

The task is **clear** and **safe**. It is also reversible (single markdown file, easy to revert).

## 3. Affected files

- `README.md` — only file expected to change.
- *Indirect read-only references:* `docs/safety-rules.md`, `docs/workflow.md` — the new "Before You Push" section should **link to** these, not restate the rules (avoid drift).

## 4. Risks the plan missed

Ranked by severity.

### R1 — Bilingual policy is undefined (HIGH)
The current `README.md` is **predominantly Korean** with a single English tagline at the top (line 4). The plan says "preserve or improve the bilingual nature consistently" but does not pick a policy. Without one, Codex may:
- Rewrite the whole file in English (breaks current KO-primary voice), or
- Add EN sections alongside KO, doubling the length and hurting the "easy-to-scan for beginners" goal.

**Mitigation:** State explicitly that the README stays **Korean-primary**, with brief English in headings or call-outs only where it already exists. Match the existing pattern (line 2–4).

### R2 — Duplication of content that already exists (HIGH)
The current README already contains:
- A roles table at lines 8–14 (covers all 5 roles).
- A tmux navigation tip at line 38 (`Ctrl-b` + 0~4, detach `Ctrl-b` + d).
- A "Quick Start" code block at lines 16–36.

The plan says "Add ... table" / "Add ... tmux tip" / "Reorganize Quick Start." Without clarification, Codex risks **adding duplicate sections** instead of enhancing the existing ones. Acceptance criteria check "a table exists" — which is already true today — so the criteria can be technically met without improving anything.

**Mitigation:** Reword acceptance criteria as *enhancements*, not *existence checks*. E.g., "roles table includes a short example of what each role outputs," "tmux tip is in a callout/blockquote near the top, not a single sentence buried after the code block."

### R3 — Window-numbering off-by-one beginner trap (MEDIUM)
The current README table labels the windows "1." through "5." (Markdown list prefix), but the actual tmux shortcuts are `Ctrl-b` + **0–4** (`scripts/start-ai-team.sh:79–83` create windows without `base-index 1`, so they are zero-indexed). A first-time user will type `Ctrl-b 1` expecting Gemini Manager and land on Claude Architect.

This is exactly the kind of beginner-hostile detail this job is supposed to fix, and the plan does **not** mention it.

**Mitigation:** The new table must use the **actual tmux index** in a dedicated column (0, 1, 2, 3, 4) and the human-readable ordinal can be the row position. Example:

```
| Ctrl-b key | tmux window      | Role             |
|------------|------------------|------------------|
|     0      | gemini-manager   | Gemini Manager   |
|     1      | claude-architect | Claude Architect |
|     2      | codex-implementer| Codex Implementer|
|     3      | claude-reviewer  | Claude Reviewer  |
|     4      | git-shell        | Git Shell        |
```

This must be verified by reading `scripts/start-ai-team.sh`, not guessed — the plan should instruct Codex to verify.

### R4 — Pre-push checklist may drift from `docs/safety-rules.md` (MEDIUM)
The checklist content overlaps with `docs/safety-rules.md` §2 (no direct `main` push), §3 (no auto-merge), §7 (the "who does what" table). If the README restates these rules verbatim, the two documents will drift over time.

**Mitigation:** The pre-push section should be a **short checklist (5–7 bullets)** that ends with a link to `docs/safety-rules.md` and `docs/workflow.md` as the authoritative sources. Do not restate rationale.

### R5 — Two `input.ko.md` paths will confuse beginners (LOW)
The README references `examples/job-001/input.ko.md` (line 87) as the example, but the actual workflow places real jobs at `docs/ai/jobs/{JOB_ID}/input.ko.md` (`docs/workflow.md:8`, `scripts/create-job.sh`). A first-time user reading the new "step-by-step" section will not understand which path to use.

**Mitigation:** The step-by-step section should make this explicit: "`examples/` is a reference. Your real jobs go to `docs/ai/jobs/<JOB_ID>/`, created by `./scripts/create-job.sh`."

### R6 — Broken relative links (LOW)
A docs reorganization can easily break the existing relative links to `docs/setup.md`, `docs/workflow.md`, `docs/safety-rules.md`, `prompts/*.md`, and `scripts/ai-team-aliases.sh`. Acceptance criteria do not cover link integrity.

**Mitigation:** Add an acceptance check: all relative links in the new README must resolve to existing files.

## 5. Missing requirements

What `input.ko.md` asked for but the plan did not nail down:

| Missing | What it should say |
|---|---|
| Language policy | Keep Korean-primary; do not translate existing KO sections to EN. |
| "Step-by-step" granularity | Each step must include the **tmux window** to switch to and the **artifact produced** (mirrors `docs/workflow.md`). |
| Window-index correctness | Codex must verify against `scripts/start-ai-team.sh`, not the existing table. |
| Link integrity | All relative links resolve. |
| Pre-push checklist source of truth | Short, links to `docs/safety-rules.md`. |

## 6. Test strategy

Documentation change — no unit tests. Manual + lightweight automated checks only.

### Manual checks (Git Shell window, before pushing)
1. **GitHub render** — Push to a branch and open in GitHub web UI. The rendered tables, code blocks, and callouts should be readable on mobile width.
2. **First-time-user dry run** — Read the README top-to-bottom once. Can a new user reach a running tmux session and a created job folder using only the README? If "no," the job has not met its goal even if all acceptance criteria pass.
3. **tmux index verification** — Run `./scripts/start-ai-team.sh` in a throwaway directory; confirm `Ctrl-b 0` lands on `gemini-manager` and matches the new table exactly.

### Automated / scriptable checks
1. **No `scripts/` diff:** `git diff --name-only main...HEAD -- scripts/` must be empty.
2. **No secret-shaped strings introduced:** `grep -Ein '(\.env|API[_-]?KEY|TOKEN|SECRET|PASSWORD)' README.md` returns only the *prohibition* mentions, not credential examples.
3. **Relative link resolution:** for each `](path)` in the README, `test -e path` succeeds. Can be a one-liner:
   ```bash
   grep -oE '\]\([^)]+\)' README.md | sed -E 's/^\]\(//; s/\)$//' \
     | grep -v '^https\?://' | grep -v '^#' \
     | while read p; do [ -e "$p" ] || echo "MISSING: $p"; done
   ```
4. **No `git push origin main` recommended:** `grep -E 'push +origin +main|push +main' README.md` must return nothing (or only inside an explicit "do NOT" sentence).

### Fixtures
None needed.

## 7. Review checkpoints (for Claude Reviewer in stage 6)

- Bilingual policy applied consistently (R1).
- No duplicate sections (R2) — single roles table, single tmux nav block, single Quick Start.
- Window indices match `scripts/start-ai-team.sh` (R3).
- Pre-push section links to `docs/safety-rules.md`, does not restate it (R4).
- `examples/` vs. `docs/ai/jobs/` distinction is explained (R5).
- All relative links resolve (R6).
- `git diff` touches **only** `README.md`.

## 8. Open questions for the human

None of these are blocking — defaults are reasonable — but a one-line answer per question will sharpen the implementation.

1. **Language policy** — confirm Korean-primary with current English tagline preserved? *(Default: yes.)*
2. **Add a "what each role outputs" column** to the roles table, or keep it the same shape as today? *(Default: yes, add it — directly serves the "beginner can see the flow" goal.)*
3. **Should the Pre-push Checklist live in `README.md` only, or also be promoted into `docs/safety-rules.md`** as a new "TL;DR" section? *(Default: README only, link to safety-rules.)*

## 9. Verdict

**APPROVE_WITH_CHANGES**

The task is safe and the plan's shape is correct, but the plan needs the following clarifications recorded in `gemini-plan.en.md` (or in a supplemental note) **before** Codex implements:

1. Korean-primary language policy stated explicitly.
2. Acceptance criteria reworded from "exists" to enhancement-shaped (R2).
3. Codex must verify tmux window indices against `scripts/start-ai-team.sh` and use the real 0–4 indices in the table (R3).
4. Pre-push checklist links to `docs/safety-rules.md`/`docs/workflow.md` rather than restating them (R4).
5. Step-by-step section disambiguates `examples/job-001/` (illustration) vs. `docs/ai/jobs/<ID>/` (real work) (R5).
6. Add link-integrity check to acceptance criteria (R6).

Cheap to clarify now. Expensive to re-review a duplicated, drift-prone README later.
