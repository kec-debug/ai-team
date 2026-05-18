# Project Rules

## Project Goal
Build a US stock automated paper-trading system.
The system may later support live validation, but paper trading is the default and primary mode.

## Safety Rules
- Paper trading is the default.
- Live trading is disabled by default.
- Live trading requires explicit validation, preflight, arming, and guard checks.
- LLMs must never place orders directly.
- Recommendation agents may only create non-executable order intents.
- Executable orders may only be created by the OMS.
- All orders must pass Strategy -> Risk Engine -> OMS.
- Broker-specific API calls must stay inside broker adapters.
- API keys must only come from `.env`.
- Do not hardcode secrets.
- Do not invent vendor endpoints.
- Market orders are disabled by default.
- Fail closed on uncertainty.

## AI Tool Roles
- Gemini Manager: Convert Korean user requests into English implementation plans.
- Claude Architect: Review architecture, risks, and test strategy.
- Codex Implementer: Modify files, add tests, run checks, summarize changes.
- Claude Reviewer: Review diffs and enforce safety rules.
- Git Shell: Human-operated Git, test, commit, and push commands.

## Standard Workflow
1. Gemini Manager writes `plan.en.md`.
2. Claude Architect writes `architecture.md` or design review.
3. Codex Implementer modifies code and writes `patch.md`.
4. Claude Reviewer writes `review.md`.
5. Human runs tests and Git commands.