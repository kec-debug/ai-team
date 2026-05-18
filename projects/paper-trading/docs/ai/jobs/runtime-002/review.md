# runtime-002 — Claude 리뷰

## 최종 판정

APPROVE

`PaperEngine.submit_intents(intents)` 가 plan / codex-task 그대로 구현됐다. `OrderIntent` 만 허용 (`Order`/`BrokerOrder`/`dict` 입력은 `TypeError`), OMS 미주입 시 `RuntimeError`, RiskEngine 거절·OMS 인프라 거절 intent 는 `PaperBroker._open_orders` 에 등록되지 않으며, 승인된 intent 만 broker 에 등록되고 동일한 broker/account/portfolio/journal 인스턴스를 통해 이후 `on_quote(quote)` 가 fill / cash / position / journal 을 갱신한다. `OrderType.MARKET` 3중 가드 (`paper_market_orders_disabled`) 와 LIMIT / STOP_LIMIT 분기 변동 없음. `OrderType.STOP` 미도입. KIS HTTP / endpoint / TR ID / payload / FX / 외부 HTTP 라이브러리 / `.env` / secret · 계좌번호 · access token · Bearer 변동 없음. GUI (`app/api/*`, `app/static/*`, `app/main.py`) 와 `app/api/server.py` production wiring 도 변경되지 않았다. patch.md 의 `350 passed` 와 일치. commit / push / merge / deploy 가 수행되지 않았다.

dry-run controller 통합은 `DryRunController` 소스 변경 없이 `PaperRunner(..., paper_engine=engine)` 주입 방식으로 이루어졌고 (`test_controller_routes_through_paper_engine_when_runner_wired_with_paper_engine`), 같은 broker 상태에서 `on_quote` fill flow 가 그대로 작동함을 검증한다.

## Findings (severity 순)

### Critical / Major

없음.

### Minor / 관찰사항

1. **PaperBroker.submit 의 `ValueError` 도 OMS 인프라 거절로 분류** — `submit_intents` 의 `except (RuntimeError, ValueError)` (`app/runtime/paper_engine.py:84`) 가 `PaperBroker.submit("unsupported order type")` 의 ValueError 까지 흡수하고 `_classify_rejection` 에서 "oms" 로 분류한다. plan §4.2 가 권장한 보수적 처리와 일치하며 RiskEngine 의 unsupported_order_type 가드를 OMS 가 먼저 막아주므로 실제 도달 가능성은 거의 없다. 후속에서 더 세분화 (예: `"broker"` 분류) 가 필요하면 별 job 으로.

2. **`PaperRunner` 의 `first.status or "accepted"` fallback** (`app/runtime/paper_runner.py:50`) — `PaperBroker.submit` 가 항상 `status="accepted"` 를 채우므로 fallback 은 죽은 코드지만, 외부 OMS/broker 구현이 status 를 비울 경우의 방어 코드로 합리적. 비-블로커.

3. **`test_paper_runner_requires_oms_or_paper_engine` 가 `try/except/else`** (`tests/test_paper_runner.py:113-118`) — 동일 파일의 다른 테스트는 `pytest.raises` 를 사용한다. 스타일 차이일 뿐 기능은 동일. 후속 cleanup 후보.

4. **`test_submit_intents_results_immutable_and_secret_free` 의 KIS 설정 wire 가 명목상** (`tests/test_paper_engine.py:217-225`) — `kis_app_key`/`kis_app_secret`/`kis_account_no` 가 `submit_intents` 경로에서 실제로 사용되지 않지만, 회귀 안전망으로 secret 패턴이 결과 dataclass 에 흘러나오지 않음을 검증한다. 의도된 방어 테스트.

## 안전 / 정책 회귀 체크리스트

- [x] `PaperEngine.submit_intents` 가 `OrderIntent` 만 허용. `Order`/`BrokerOrder`/`dict` 입력은 `TypeError("submit_intents accepts OrderIntent only ...")`. 검증: `test_submit_intents_rejects_non_intent_input` (3 케이스).
- [x] OMS 미주입 PaperEngine 의 `submit_intents` 호출은 `RuntimeError("PaperEngine.submit_intents requires an OMS")`. 검증: `test_submit_intents_requires_oms`.
- [x] RiskEngine 거절 intent 가 broker 에 도달하지 않음. `result.risk_rejected_count == 1`, `results[0].rejected_by == "risk_engine"`, `results[0].reason.startswith("RiskEngine rejected")`, `broker.open_orders() == []`. 검증: `test_submit_intents_risk_rejected_does_not_reach_broker`.
- [x] OMS 인프라 거절 intent (`live_trading_enabled=True` → `"OMS refuses live trading in Phase 1"`) 가 broker 에 도달하지 않음. `result.oms_rejected_count == 1`, `results[0].rejected_by == "oms"`, `broker.open_orders() == []`. 검증: `test_submit_intents_oms_rejected_does_not_reach_broker`.
- [x] 승인된 intent 만 broker 에 등록되고 `accepted_oms_ids` / `accepted_broker_order_ids` 에 포함. 검증: `test_submit_intents_happy_path_passes_through_risk_and_oms` (`len(broker.open_orders()) == 1`).
- [x] `submit_intents` 후 `on_quote` 가 같은 broker/account/portfolio/journal 인스턴스에서 fill / cash / position / journal 을 갱신. 검증: `test_submit_intents_then_on_quote_flows_fill_through_engine` (cash 100→80, position qty 2, journal trade 1).
- [x] partial fill / staleness / session / cash ledger / journal 회귀 보존. 기존 `test_paper_engine_*`, `test_paper_broker.py`, `test_paper_e2e_api.py` 변경 없이 통과 (350 passed). 추가 `test_submit_intents_partial_fill_preserved` 가 partial fill 시 broker open_orders 의 남은 quantity (10→5) 와 fill quantity 를 확인.
- [x] `OrderType.MARKET` 3중 가드 (`allow_paper_market_orders=False` 기본) 유지. `test_submit_intents_market_order_blocked_by_default_guard` 가 `reason` 에 `paper_market_orders_disabled` 포함을 검증.
- [x] `OrderType.STOP` 미도입. `grep -rn "OrderType.STOP\b" app tests` clean (patch.md 의 safety grep 결과와 일치).
- [x] FX 변환 함수 / 환율 상수 / base currency 통합 함수 미도입. 통화별 분리 보고만.
- [x] 외부 HTTP 라이브러리 미사용. `grep -rEn "import (requests|httpx|aiohttp|urllib3)"` 에서 negative-assertion 회귀 테스트만 매치 (patch.md).
- [x] `.env` / `.env.example` 미접근 / 미수정. raw app key / app secret / access token / Bearer / 계좌번호 코드 · 테스트 · patch 어디에도 등장하지 않음. `repr(SubmitIntentsBatchResult)` / `repr(IntentSubmitResult)` 에 fixture 값 (`fake-key`, `fake-secret`, `12345678`, `Bearer `) 미등장. 검증: `test_submit_intents_results_immutable_and_secret_free`.
- [x] KIS endpoint / TR ID / payload / HTTP 코드 추가 없음. `app/broker/kis*.py` 변경 없음 (runtime-002 diff 범위 0).
- [x] Strategy / Agent / LLM 이 broker 를 직접 호출하거나 `BrokerOrder` 를 생성하는 경로 추가 없음. `submit_intents` 가 `OrderIntent` 만 받음으로 caller 도 executable order 생성 불가. `test_strategy_package_does_not_import_kis` / `test_agent_package_does_not_import_kis_if_present` 통과 (전체 350 passed 에 포함).
- [x] OMS / RiskEngine / PaperBroker 핵심 로직 변경 없음. `app/oms/`, `app/risk/`, `app/broker/paper.py`, `app/portfolio/` 변경 0.
- [x] `DryRunController` 소스 변경 없음. `PaperRunner` 주입을 통해서만 새 경로 활성화. 검증: `test_controller_routes_through_paper_engine_when_runner_wired_with_paper_engine` (counters 동일 집계 + 같은 broker 상태에서 `on_quote` trade 1 건 기록).
- [x] GUI 파일 (`app/api/routes.py`, `app/static/dashboard.html`, `app/main.py`) 변경 없음.
- [x] `app/api/server.py` production wiring 변경 없음 (runtime-002 commit 의 변경 파일 7 개 중 server.py 미포함). production `PaperEngine(...)` 은 `oms` 미주입 상태 유지 — `submit_intents` 가 production HTTP 경로에서 호출되지 않으므로 의도대로 본 job 범위에서 production wiring 전환 미적용.
- [x] 테스트 통과: patch.md `350 passed`. compileall OK. safety grep clean.
- [x] 본 job 범위 내 유지: 변경 파일 7 개 (`paper_engine.py`, `paper_runner.py`, 3 test, README, patch.md) — codex-task §3 화이트리스트와 일치. pre-existing unstaged (`app/api/server.py`, `app/broker/kis.py`, `app/broker/kis_quote_mapper.py`, `app/domain/quote.py`, `app/runtime/paper_journal.py`, scripts/`, `mvp-002 request`, KIS/Quote 관련 테스트들) 는 paper-001-gui / api-market-data-001 잔여물이며 Codex 가 추가로 건드린 흔적 없음 (patch.md 의 "Pre-existing unrelated dirty files were left untouched" 와 일치).
- [x] patch.md 가 plan §1 마지막 두 bullet 충족: "Claude 검증 요청 프롬프트" 와 "Claude 리뷰가 REQUEST CHANGES / BLOCK 일 때 follow-up Codex 수정 프롬프트 작성 규칙" 모두 포함 (patch.md §"Claude 검증 요청 프롬프트", §"Claude 리뷰가 REQUEST CHANGES / BLOCK 일 때 follow-up Codex 수정 프롬프트 작성 규칙").

## 산출물 vs 계획 대조

| Plan / codex-task 항목 | 구현 위치 | 결과 |
| --- | --- | --- |
| `IntentSubmitResult` / `SubmitIntentsBatchResult` frozen dataclass | `app/runtime/paper_engine.py:14-37` | OK. 모든 필드 plan 과 일치. |
| `_classify_rejection(reason)` — "risk_engine" / "oms" 분류 | `app/runtime/paper_engine.py:40-41` | OK. `"RiskEngine rejected"` prefix 매칭. |
| `PaperEngine.__init__(..., oms=None)` keyword-only | `app/runtime/paper_engine.py:46-71` | OK. 기존 default 객체 생성 분기 보존. |
| `PaperEngine.submit_intents(intents)` 타입 가드 + OMS 경유 + batch 결과 | `app/runtime/paper_engine.py:72-139` | OK. `RuntimeError`/`TypeError` 가드, `(RuntimeError, ValueError)` except, accepted_oms_ids / accepted_broker_order_ids 집계. |
| `PaperEngine.on_quote` / `mark_quote` / `cash_by_currency` 동작 보존 | `app/runtime/paper_engine.py:141-` | OK. 본문 변경 없음. |
| `PaperRunner.__init__(... , oms=None, *, paper_engine=None)` + 양쪽 None 시 raise | `app/runtime/paper_runner.py:19-37` | OK. `ValueError("PaperRunner requires oms or paper_engine")`. |
| `PaperRunner.run_once` 의 paper_engine 분기 | `app/runtime/paper_runner.py:39-60` | OK. `paper_engine.submit_intents([intent])` → first result 매핑 → `OrderAck` 재구성 (mode=PAPER). 미주입 시 기존 `oms.place` 경로. |
| 테스트 9 개 추가 (paper_engine), 3 개 추가 (paper_runner), 1 개 추가 (dry_run_controller) | `tests/test_paper_engine.py:108-235`, `tests/test_paper_runner.py:73-118`, `tests/test_dry_run_controller.py:125-163` | OK. plan §5 의 시나리오 (requires_oms / non-intent / happy / risk-reject / oms-reject / market-guard / on_quote 통합 / partial fill / immutability+secret-free / runner paper_engine 라우팅 / runner 거절 라우팅 / runner 양쪽 None / controller 통합) 전부 커버. |
| README 1-2 줄 안내 | `README.md:24` | OK. live trading / market order 활성화 안내 없음. |
| patch.md 필수 항목 (변경 파일 / 흐름 / 경계 / dry-run 통합 / 안전 회귀 / 테스트 결과 / Claude 검증 요청 프롬프트 / follow-up Codex 프롬프트 규칙) | `docs/ai/jobs/runtime-002/patch.md` | OK. 9 개 섹션 모두 포함. follow-up 규칙은 6 개 조항 + 1 줄 말미 (자동화 금지) 명시. |
| `app/api/server.py` production wiring 미변경 | n/a | OK. runtime-002 변경 파일 목록에 server.py 미포함. production `paper_engine` 은 oms 없이 유지. |

## 후속 작업 후보 (블로커 아님)

- production wiring 전환 (`server.py` 에서 `PaperEngine(..., oms=oms)` 주입, `PaperRunner(..., paper_engine=engine)`) 을 별 job (예: `runtime-002b`).
- `submit_intents` 결과에 timestamp aggregate (예: 최초/최후 submit time) 또는 broker-level 거절 분류 ("broker") 추가.
- `test_paper_runner_requires_oms_or_paper_engine` 를 `pytest.raises` 스타일로 정리 (관찰사항 #3).
- `submit_intents` 가 large batch 일 때 일부 실패 후에도 나머지 intent 를 계속 처리하는 동작이 의도임을 docstring 1 줄로 명시 (지금 코드 동작상 그러하지만 문서화는 미흡).

## 결론

요청서의 모든 완료 기준 (단일 runtime entrypoint, OrderIntent-only 입력, RiskEngine·OMS 경계 유지, broker 등록 불변, on_quote fill 흐름 유지, MARKET 3중 가드 유지, OrderType.STOP 미도입, FX 미도입, secret 비노출, Strategy/Agent KIS 직접 import 없음, GUI 미변경, server.py production wiring 미변경, 전체 pytest 회귀 0 건, 안전 grep clean, patch.md 의 Claude 검증 요청 프롬프트 + follow-up Codex 수정 프롬프트 규칙 포함) 을 충족했다.

APPROVE. commit / push / merge 는 사람이 직접 수행한다.
