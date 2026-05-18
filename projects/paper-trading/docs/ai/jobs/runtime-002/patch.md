# runtime-002 — Codex 구현 요약

## 1. Files Changed

- `app/runtime/paper_engine.py`
- `app/runtime/paper_runner.py`
- `tests/test_paper_engine.py`
- `tests/test_paper_runner.py`
- `tests/test_dry_run_controller.py`
- `README.md`
- `docs/ai/jobs/runtime-002/patch.md`

Pre-existing unrelated dirty files were left untouched.

## 2. Implementation Summary

`PaperEngine.submit_intents(intents)` was added as the runtime entrypoint for non-executable `OrderIntent` batches.

Flow:

1. Caller passes only `OrderIntent` objects to `paper_engine.submit_intents([...])`.
2. `submit_intents` materializes and type-checks the batch. `Order`, `BrokerOrder`, dicts, and other objects raise `TypeError`.
3. Each intent is submitted through `OMS.place(intent)`.
4. OMS still owns the `RiskEngine.evaluate` call and executable `BrokerOrder` creation.
5. Accepted intents return `IntentSubmitResult(accepted=True)` with `oms_id`, optional `broker_order_id`, status, and submission time.
6. Rejected intents return `IntentSubmitResult(accepted=False)` with `rejected_by` set to `risk_engine` for `RiskEngine rejected: ...` messages, otherwise `oms`.
7. `SubmitIntentsBatchResult` summarizes submitted, accepted, rejected, risk-rejected, and OMS-rejected counts.
8. A later `PaperEngine.on_quote(quote)` call uses the same broker/account/portfolio/journal state, so the existing `PaperBroker.tick -> Fill -> PaperAccount -> PortfolioService -> PaperJournal` flow is preserved.

`PaperRunner` now accepts optional `paper_engine`. If present, `run_once` routes passed strategy intents through `paper_engine.submit_intents([intent])` and maps the first batch result back into the existing `PaperRunResult` shape. If absent, the old `oms.place(intent)` path remains.

`DryRunController` source was not changed. A new test wires it with a `PaperRunner(..., paper_engine=engine)` and verifies dry-run counters plus shared paper engine state.

## 3. Safety Confirmation

- Live trading remains disabled by default; no live trading flag was enabled.
- Market order policy was not loosened. Default `OrderType.MARKET` submission remains rejected by the existing paper-market guard.
- `OrderType.STOP` was not introduced.
- No KIS HTTP code, KIS endpoint, TR ID, header, or payload was added.
- No external HTTP client library was imported.
- No `.env`, auth, payment, production infra, migration, GUI, KIS adapter, OMS, RiskEngine, PaperBroker, strategy, session, config, or dry-run controller source was modified.
- `submit_intents` accepts only `OrderIntent`; executable `Order` / `BrokerOrder` input is rejected before OMS.
- RiskEngine and OMS rejection tests verify no rejected intent reaches `broker.open_orders()`.
- No raw secret, app key, app secret, account number, access token, or bearer token was added.
- No commit, push, merge, or deploy was run.

Safety grep:

```text
grep -rn "ALLOW_MARKET_ORDERS=true" app tests
Result: existing app/config.py startup rejection message only; not introduced by runtime-002.

grep -rn "LIVE_TRADING_ENABLED=true" app tests
Result: clean

grep -rn "Bearer eyJ" app tests
Result: existing negative assertion test only; no token value added by runtime-002.

grep -rn "OrderType.STOP" app tests
Result: existing STOP_LIMIT references only; no OrderType.STOP enum/value introduced.

grep -rEn "import (requests|httpx|aiohttp|urllib3)" app tests
Result: existing negative assertion tests only; no app import added.

git diff -- app/runtime/paper_engine.py app/runtime/paper_runner.py tests/test_paper_engine.py tests/test_paper_runner.py tests/test_dry_run_controller.py README.md | grep -E "ALLOW_MARKET_ORDERS=true|LIVE_TRADING_ENABLED=true|Bearer eyJ|OrderType.STOP\b|import (requests|httpx|aiohttp|urllib3)" || echo "runtime-002-diff-safety-grep: clean"
Result: runtime-002-diff-safety-grep: clean
```

## 4. Test Results

From `/root/ai-dev-center/projects/ai-team/projects/paper-trading`:

```text
.venv/bin/python -m compileall app tests
Result: passed
```

```text
.venv/bin/python -m pytest -p no:cacheprovider
Result: 350 passed in 0.69s
```

New / updated tests:

- `test_submit_intents_requires_oms`
- `test_submit_intents_rejects_non_intent_input`
- `test_submit_intents_happy_path_passes_through_risk_and_oms`
- `test_submit_intents_risk_rejected_does_not_reach_broker`
- `test_submit_intents_oms_rejected_does_not_reach_broker`
- `test_submit_intents_market_order_blocked_by_default_guard`
- `test_submit_intents_then_on_quote_flows_fill_through_engine`
- `test_submit_intents_partial_fill_preserved`
- `test_submit_intents_results_immutable_and_secret_free`
- `test_paper_runner_routes_through_paper_engine_when_provided`
- `test_paper_runner_paper_engine_rejection_captured_in_oms_error`
- `test_paper_runner_requires_oms_or_paper_engine`
- `test_controller_routes_through_paper_engine_when_runner_wired_with_paper_engine`

## 5. Remaining TODOs

- Production wiring of `PaperEngine(oms=...)` remains out of scope for this job and should be handled in a separate approved job.
- GUI/API usage of `submit_intents` remains out of scope for this job.

## Claude 검증 요청 프롬프트

```text
Use prompts/claude.md.
Project directory: /root/ai-dev-center/projects/ai-team/projects/paper-trading
Job ID: runtime-002
Job directory: /root/ai-dev-center/projects/ai-team/projects/paper-trading/docs/ai/jobs/runtime-002

Review the runtime-002 implementation.

Read:
- projects/paper-trading/docs/ai/jobs/runtime-002/request.ko.md
- projects/paper-trading/docs/ai/jobs/runtime-002/plan.md
- projects/paper-trading/docs/ai/jobs/runtime-002/codex-task.md
- projects/paper-trading/docs/ai/jobs/runtime-002/patch.md

Also review the current diff for:
- projects/paper-trading/app/runtime/paper_engine.py
- projects/paper-trading/app/runtime/paper_runner.py
- projects/paper-trading/tests/test_paper_engine.py
- projects/paper-trading/tests/test_paper_runner.py
- projects/paper-trading/tests/test_dry_run_controller.py
- projects/paper-trading/README.md

Write the review into:
projects/paper-trading/docs/ai/jobs/runtime-002/review.md

Review focus:
1. PaperEngine.submit_intents accepts only OrderIntent (Order/BrokerOrder rejected as TypeError).
2. RiskEngine and OMS gates are not bypassed; rejected/blocked intents never reach PaperBroker._open_orders.
3. Accepted intents reach PaperBroker.submit and the resulting state is shared with on_quote.
4. on_quote flow (PaperBroker.tick -> Fill -> PaperAccount -> PortfolioService -> PaperJournal) still passes.
5. LIMIT / STOP_LIMIT / MARKET behavior preserved; MARKET still blocked by the 3-guard default.
6. OrderType.STOP was not introduced.
7. No FX conversion / rate constant introduced.
8. No KIS HTTP, KIS endpoint, TR ID, payload added.
9. No third-party HTTP client imported.
10. .env, app key, app secret, account number, token, Bearer are not exposed.
11. Strategy/Agent/LLM cannot create BrokerOrder or call broker directly through this entrypoint.
12. dry-run controller integration uses submit_intents through PaperRunner without bypassing OMS.
13. GUI files (app/api/*, app/static/*, app/main.py) were not modified.
14. server.py production wiring was not modified.
15. Tests passed: 350 passed.
16. Scope stayed within runtime-002.

Verdict must be one of:
APPROVE
REQUEST CHANGES
BLOCK

Do not commit, push, merge, deploy, or run arbitrary shell commands.
```

## Claude 리뷰가 REQUEST CHANGES / BLOCK 일 때 follow-up Codex 수정 프롬프트 작성 규칙

Claude 리뷰 결과가 `APPROVE` 가 아닐 때에만 다음 절차에 따라 사용자가 Codex 에게 보낼 수정 프롬프트를 작성한다. `APPROVE` 라면 별도 프롬프트가 필요 없다.

1. 프롬프트 첫 줄은 `Use prompts/codex-implementer.md.` 로 시작한다.
2. Project directory, Job ID, Job directory, 원래 `plan.md`, `codex-task.md`, `patch.md`, `review.md` 경로를 명시한다.
3. 본문 첫 줄에 Claude review verdict 와 `review.md` 경로를 명시한다.
4. review.md 의 Critical / Major 항목과 사용자가 반영하기로 결정한 Minor 항목만 포함한다. 각 finding 은 `file_path:line_number` 를 인용한다.
5. 수정 범위는 runtime-002 `codex-task.md` 의 화이트리스트를 유지한다.
6. live trading, market order guard 완화, KIS HTTP, OMS/RiskEngine 우회, GUI 변경, `.env`/secret 변경, 외부 HTTP 라이브러리, git 자동화는 금지한다.
7. 각 finding 에 대응하는 회귀 테스트를 추가하고 전체 테스트 통과 count 를 갱신한다.
8. `patch.md` 에 finding 별 해결 방식, 변경 파일, 안전 회귀, 테스트 결과, 새 Claude 검증 요청 프롬프트를 갱신한다.
9. 말미에 `Do not commit, push, merge, deploy, or run arbitrary shell commands.` 를 둔다.

READY FOR REVIEW
