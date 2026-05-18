# Architecture Review — MVP-001

Reviewer: Claude Architect
Plan reviewed: `docs/ai/jobs/mvp-001/plan.en.md`
Input rules: `docs/ai/jobs/mvp-001/input.ko.md`

## Approach

The plan is directionally correct: TypeScript skeleton enforcing the mandatory
pipeline `Strategy → RiskEngine → OMS → Broker`, paper-trading default, market
orders disabled, fail-closed on uncertainty. No live broker integration, no
persistence, no LLM. Scope matches `input.ko.md`.

However, several concrete decisions are still open in the plan, and acting on
them at implementation time will produce a wobbly skeleton that is hard to
correct later. They must be resolved **before** code is written. Deviations from
the plan I am asking for are explicit in the sections below.

## Affected files / modules

The plan proposes adding a TypeScript project at the **repo root**. That root
already hosts the AI Dev Team Control Center (`web/server.js`, `web/public/*`,
`scripts/*.sh`, `prompts/*`, `docs/*`). Mixing a second Node project into the
same root will collide with `web/package.json` and confuse `npm install`.

**Required change**: place the trading engine under `engine/` (its own
self-contained Node project), not at the repo root. The plan itself flagged this
as an open question — the answer is `engine/`.

Concrete file list after this change:

- `.gitignore` (NEW, **root**) — must precede everything else; see Risk 1.
- `engine/package.json` (NEW)
- `engine/tsconfig.json` (NEW)
- `engine/.env.example` (NEW; non-secret template only)
- `engine/src/types/index.ts` (NEW)
- `engine/src/core/strategy.ts` (NEW)
- `engine/src/core/risk-engine.ts` (NEW)
- `engine/src/core/oms.ts` (NEW)
- `engine/src/adapters/mock-broker.ts` (NEW)
- `engine/src/config.ts` (NEW; env loading + fail-closed defaults)
- `engine/tests/pipeline.test.ts` (NEW)
- `engine/README.md` (NEW; one short paragraph, no marketing copy)

Out of bounds for this job (do not touch):

- `web/**`, `scripts/**`, `prompts/**`, `docs/ai/jobs/**` (other jobs),
  top-level `README.md`.

## Risks

Ranked by severity. Each has a required mitigation that becomes a
non-negotiable acceptance criterion.

### R1 — No root `.gitignore` exists; `.env` may be committed by accident (HIGH)

`find` confirms there is no `.gitignore` at the repo root. The plan adds
`dotenv` and `.env`-driven config without addressing this. If a developer ever
creates `engine/.env` with broker credentials, `git add -A` will pick it up.
This is the single most likely way this project leaks secrets.

**Mitigation (required before any other file is created):** add a root
`.gitignore` containing at minimum:

```
.env
.env.*
!.env.example
node_modules/
dist/
coverage/
*.log
```

Reviewer must `BLOCK` the implementation patch if `.gitignore` is missing or
does not include `.env`.

### R2 — "OMS exclusivity" is unenforceable with TypeScript types alone (HIGH)

The plan correctly identifies that only OMS may produce `ExecutableOrder`, but
TypeScript types are erased at runtime. A simple `interface ExecutableOrder`
can be constructed by any module via an object literal cast. This silently
breaks the most important invariant in the system.

**Mitigation (required):** enforce at runtime, not just at the type level.

- `ExecutableOrder` is a **class with a private constructor** (or a frozen
  object produced behind a module-private symbol).
- The only export from `engine/src/core/oms.ts` that can produce an
  `ExecutableOrder` is `OMS.execute(approvedIntent)`.
- The `ExecutableOrder` type is exported as a **branded opaque type**
  (e.g. `type ExecutableOrder = { readonly __brand: unique symbol; ... }`) so
  callers can hold and forward it but cannot fabricate one.
- A unit test must assert that constructing `ExecutableOrder` from outside OMS
  fails (either does not compile or throws at runtime).

### R3 — "Fail-closed" is not defined concretely (HIGH)

The plan says fail-closed but does not specify the contract. Without a
concrete contract, an unhandled exception or an undefined return in
`RiskEngine` will silently pass through OMS.

**Mitigation (required):** `RiskEngine.validate(intent)` returns a discriminated
union:

```ts
type RiskDecision =
  | { ok: true;  approved: ApprovedIntent }
  | { ok: false; reason: string };
```

- Any thrown exception inside `RiskEngine.validate` is caught at the boundary
  and converted to `{ ok: false, reason: 'risk_engine_exception' }`.
- `OMS.execute` accepts a `RiskDecision`, returns early on `ok: false`, and
  **never** constructs an `ExecutableOrder` from an `OrderIntent` directly.
- Default branch in any `switch` over order type / decision must be
  `{ ok: false, reason: 'unknown_case' }`, not `throw`.

### R4 — Market-order rejection should be an allowlist, not a denylist (MEDIUM)

The plan says "rejects market orders by default." Denylists rot — every new
order type becomes a security review. Allowlist is safer.

**Mitigation (required):** define `OrderType` as a string-literal union
(`'LIMIT' | 'MARKET' | 'STOP' | 'STOP_LIMIT'`). `RiskEngine` carries an
explicit `allowedOrderTypes: Set<OrderType>` initialized to `new Set(['LIMIT'])`.
Anything not in the set is rejected with `reason: 'order_type_not_allowed'`.
Adding a new type later is one line and one test.

### R5 — Live-trading code path must not exist yet (MEDIUM)

The plan says `PAPER_TRADING=true` is enforced "even if overridden". The
cleanest way to enforce that in MVP-001 is: **no live broker adapter exists at
all**. `MockBrokerAdapter` is the only `BrokerAdapter` implementation.

**Mitigation (required):**

- `engine/src/config.ts` reads `PAPER_TRADING` and exposes `paperTrading`.
- On startup, if `paperTrading !== true`, the process logs a structured
  rejection and exits non-zero (or the OMS factory throws). No code path
  hands an `ExecutableOrder` to anything other than `MockBrokerAdapter` in
  this job.
- Live broker work is a separate future job and must come with its own
  human-approved input.

### R6 — `dotenv` import order (LOW, but bites everyone once)

`dotenv.config()` must run before any module that reads `process.env`. If the
entry point imports `OMS` before `dotenv.config()`, env-driven safety checks
silently see `undefined`.

**Mitigation (required):** `engine/src/config.ts` calls `dotenv.config()` at
the top of the file and exports a frozen config object. Every other module
imports the config object, **never** reads `process.env` directly. Add a
lint/grep check or test that fails if `process.env` appears outside `config.ts`.

### R7 — Coexistence with `web/` GUI (LOW)

The control-center GUI server (`web/server.js`) runs unrelated logic. Placing
the engine under `engine/` keeps them physically separated, so the GUI keeps
working. No change to `web/` is in scope.

**Mitigation:** confirmed by the `engine/` layout in R0 above. Implementer
must not edit `web/**`.

### R8 — Working branch (LOW)

Current branch is `feat/job-006-control-center-upgrade` with unrelated
modifications to `web/` and `README.md`. MVP-001 must not piggy-back on that
branch.

**Mitigation (required):** human creates a fresh branch off `main`, e.g.
`feat/job-mvp-001-engine-skeleton`, before the implementer begins. Implementer
verifies `git status` is clean (other than untracked job folders under
`docs/ai/jobs/`) before writing files.

### R9 — Node / package manager version drift (LOW)

The plan does not pin a Node version. Two contributors on Node 18 vs 22 will
disagree on what works.

**Mitigation (required):** `engine/package.json` declares
`"engines": { "node": ">=20" }` and a `packageManager` field (`npm@10` is fine).

## Test strategy

All tests live under `engine/tests/` and run with `jest` (or `vitest`; either
is acceptable, pick one and stick with it).

### Unit tests (required, in this job)

| # | Test                                              | Asserts                                              |
|---|---------------------------------------------------|------------------------------------------------------|
| 1 | Strategy produces an `OrderIntent`                | Shape matches the type; never produces `ExecutableOrder` |
| 2 | RiskEngine rejects MARKET                         | `{ ok: false, reason: 'order_type_not_allowed' }`    |
| 3 | RiskEngine accepts LIMIT                          | `{ ok: true, approved: ... }`                        |
| 4 | RiskEngine catches internal exception             | Returns `{ ok: false, reason: 'risk_engine_exception' }`; does not throw |
| 5 | OMS rejects an unvalidated `OrderIntent`          | No `ExecutableOrder` produced; broker not called     |
| 6 | OMS produces `ExecutableOrder` only via `execute` | Direct construction fails to compile / throws        |
| 7 | MockBroker logs the executed order                | Captured via spy on logger; no real network calls    |
| 8 | Config: `PAPER_TRADING` defaults to `true`        | When env var absent, `config.paperTrading === true`  |
| 9 | Config: non-paper start refuses to boot           | When `PAPER_TRADING=false`, factory throws / exits   |

### Integration test (required, in this job)

| # | Test                                              | Asserts                                              |
|---|---------------------------------------------------|------------------------------------------------------|
| I1| End-to-end happy path                             | `MarketData → Strategy → RiskEngine → OMS → MockBroker` produces one logged execution |
| I2| End-to-end MARKET path                            | Same inputs but order type MARKET → broker receives nothing, RiskEngine rejection is logged |

### Fixtures

- A single hard-coded `MarketData` snapshot (one symbol, one bar) lives in
  `engine/tests/fixtures/market-data.ts`. Do **not** fetch from any real
  data source in tests.
- The logger is injected, so tests can pass a spy / array-collector. No
  `console.log` assertions.

### Manual check (one-time, by the human)

After the implementer reports done:

1. `cd engine && npm install && npm test` — all green.
2. `git status` shows only files listed in §"Affected files / modules" plus
   the new `.gitignore` at the repo root. Nothing under `web/`.
3. `grep -R "process.env" engine/src` returns only `engine/src/config.ts`.
4. `grep -R "new ExecutableOrder" engine/src` returns only
   `engine/src/core/oms.ts`.

## Open questions for the human

None blocking — but please confirm before the implementer starts:

1. **`engine/` subfolder is acceptable** (vs root). I am proceeding on the
   assumption that it is. If you would rather use npm workspaces, say so now;
   it changes `package.json` layout.
2. **`jest` vs `vitest`** — either is fine; I have no preference. Implementer
   should pick one and not mix.

Neither blocks the verdict below; both are easy to lock in before code.

## Verdict

**REQUEST CHANGES.**

The plan's intent and scope are correct, but it is missing concrete decisions
on five high/medium risks (R1–R5) that, if left to the implementer, will
produce a skeleton that does not actually enforce the safety rules it claims
to. Cheap to fix in the plan; expensive to fix after code is written.

The implementer may proceed **only after** the plan (or this architecture
document, used as the authoritative spec) is updated to include:

- Root `.gitignore` as the first file created.
- `engine/` subfolder layout (not repo root).
- Runtime-enforced `ExecutableOrder` exclusivity (branded type + private
  constructor in OMS).
- Discriminated-union `RiskDecision`, exceptions caught at the boundary.
- Allowlist of order types, default `['LIMIT']`.
- No live broker adapter in this job; refuse to boot when
  `PAPER_TRADING !== true`.
- `engines.node >= 20` and a pinned package manager.
- A fresh branch off `main`; no edits under `web/`.
- The 11 tests listed above (9 unit + 2 integration).

Once these are folded in, this becomes **APPROVE** without further review.
