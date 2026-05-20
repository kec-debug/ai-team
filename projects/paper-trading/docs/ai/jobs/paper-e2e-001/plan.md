# paper-e2e-001 — Paper trading end-to-end 검증

## 1. 요청 요약

api-orders-paper-001 까지 KIS paper 주문 본문이 구현됐다. 새 기능 추가 전에 **기존 구성요소를 그대로** 사용해서 paper trading 흐름이 처음부터 끝까지 끊기지 않는지 회귀로 고정한다. 본 작업은 신규 기능 추가가 아니라 **end-to-end 흐름의 testable assertion 추가**이며, 필요 시 read-only helper / runtime entrypoint 보강을 1-2 줄로만 허용한다.

검증할 단일 chain:

```
Quote (or StrategyInput)
 → Strategy.evaluate
 → non-executable OrderIntent
 → PaperEngine.submit_intents (or PaperRunner)
   → OMS.place (Strategy → RiskEngine → OMS 경계)
     → RiskEngine.evaluate (approve / reject)
     → BrokerOrder 생성 (OMS 단독)
     → broker.submit
       → PaperBroker.submit (open order 저장)
       또는 KisBroker.place_order (KIS_ORDER_DRY_RUN=true → dry_run ack, no HTTP)
 → PaperEngine.on_quote(matching Quote)
   → PaperBroker.tick → Fill
   → PaperAccount.apply_fill (cash update)
   → PortfolioService.apply_trade + mark_price (position + PnL update)
   → PaperJournal.record_trade (journal entry)
 → /paper/account, /paper/positions, /paper/fills, /paper/engine/status, /paper/status read-only surfaces
```

기존 코드 인벤토리에서 이 chain 의 모든 구성요소가 이미 존재함을 확인:

- `app/strategy/premarket_gap.py::PremarketGapVolumeBreakoutStrategy.evaluate` 가 `OrderIntent` 생성 (executable 아님).
- `app/risk/engine.py::RiskEngine.evaluate` 가 risk_token 또는 reject 반환.
- `app/oms/manager.py::OMS.place` 가 RiskEngine 호출 후 BrokerOrder 생성 + `broker.submit(broker_order)` 호출. live trading off 와 broker.mode == PAPER 확인 가드 있음.
- `app/broker/paper.py::PaperBroker.submit` 가 open order 저장, `PaperBroker.tick(quote)` 가 fill list 반환.
- `app/broker/kis.py::KisBroker.place_order` 가 `kis_order_dry_run=True` 분기에서 transport 호출 없이 `OrderAck(status="dry_run")` 반환 (api-orders-paper-001).
- `app/runtime/paper_engine.py::PaperEngine.submit_intents` 가 intent 리스트를 OMS 로 위임. `on_quote` 가 broker.tick → account/portfolio/journal 적용.
- `app/runtime/paper_runner.py::PaperRunner.run_once` 가 Strategy.evaluate + OMS/PaperEngine 위임.
- `app/api/routes.py` 의 `/paper/status`, `/paper/account`, `/paper/positions`, `/paper/fills`, `/paper/engine/status`, `/paper/order/simulate`, `/paper/run` 모든 read-only surface 가 PaperEngine 상태를 노출.
- `app/api/server.py` 가 `broker = PaperBroker(...)`, `oms = OMS(settings, risk, broker)`, `paper_engine = PaperEngine(settings, broker=broker, portfolio=portfolio)` 로 **broker 인스턴스 공유** — runner.run_once 가 OMS 경유로 open order 를 저장하면 paper_engine.on_quote 가 같은 broker 의 tick 으로 fill 생성 가능. 이 공유 가정도 회귀로 고정한다.

따라서 본 작업은 **테스트 1 파일 추가** 가 핵심이며, 코드 변경은 (a) 신규 production code 0 / (b) 기존 read-only API 변경 0 / (c) 테스트 helper 1 파일 신규를 원칙으로 한다.

추가 제약 (request "절대 하지 말 것" 직역):

- live trading 활성화 금지. 실전 endpoint / TR_ID 추가 금지. KIS catalog 미확인 값 사용 금지.
- 외부 HTTP 라이브러리 추가 금지.
- Strategy / Agent / LLM 이 broker 를 직접 호출하거나 executable order 를 생성하는 경로 추가 금지.
- OMS / RiskEngine 우회 금지.
- `ALLOW_MARKET_ORDERS=true` 허용 변경 금지. `OrderType.MARKET` 3중 가드 / `OrderType.STOP` 도입 / FX 변환 / 환율 상수 도입 금지.
- `.env` / `.env.example` 읽기·수정 금지. 실 secret / 계좌번호 / token 노출 금지.
- GUI 파일 (`app/api/`, `app/static/`, `app/main.py`) 불필요한 수정 금지. 기존 status helper 가 노출하는 정보만 활용.
- 자동 git commit / push / merge / deploy 금지.

## 2. 작업 범위

포함하는 것:

- 신규 테스트 파일 `tests/test_paper_e2e_pipeline.py`:
  - end-to-end happy path (Strategy → RiskEngine → OMS → PaperBroker.submit → PaperEngine.on_quote → fill → cash / position / journal update).
  - Strategy 가 blocker 로 거절한 snapshot 은 OMS / broker 까지 도달하지 않음 (OMS.place 호출 횟수 0).
  - RiskEngine 이 거절한 intent 는 broker.submit 까지 도달하지 않음 (broker.open_orders() 그대로 비어 있음).
  - KIS dry-run 경로 (OMS + KisBroker(kis_order_dry_run=True)) 에서 OrderAck.status == "dry_run", _last_order_preview 채워지고 _last_order_response is None (HTTP 미발생). `KisBroker._order_transport` 가 호출되지 않음을 raise-on-call Fake 로 회귀.
  - 시장가 OrderIntent 는 (a) OMS.place 시 `validate_kis_order_request` 를 거치는 KIS 경로에서 거절, (b) PaperBroker 경로에서도 `paper_market_orders_disabled` 또는 동등 가드로 거절 (기존 `/paper/order/simulate` 가 이미 검증; e2e pipeline 안에서도 회귀 보장).
  - shared-broker 가정 회귀: server.py 처럼 같은 broker 인스턴스를 OMS / PaperEngine 가 공유했을 때 runner.run_once → paper_engine.on_quote 가 같은 open order 를 fill 한다는 단언.
  - TestClient 기반 dashboard/status surface 회귀: fill 발생 후 `/paper/account` `cash` 감소, `/paper/positions` `quantity > 0`, `/paper/fills` 첫 trade 의 symbol/side/price, `/paper/engine/status` journal / portfolio / account snapshot 갱신, `/paper/status` `kis_account_loaded=False` / `kis_order_methods_fail_closed=True` / `kis_order_dry_run=True` 등 안전 플래그가 그대로 유지됨.
  - secret leak 회귀: e2e response text 어디에도 `KIS_APP_KEY` / `KIS_APP_SECRET` / `KIS_ACCOUNT_NO` / `app_secret` / `access_token` / `Bearer` 토큰 원문 등장 안 함.
  - Strategy / Agent 패키지가 broker 를 직접 import 하지 않음을 본 파일에서도 grep 회귀 (기존 `test_strategy_package_does_not_import_kis` 와 보완).
- `tests/test_paper_e2e_pipeline.py` 의 helper 는 conftest 의 `settings` / `make_snapshot` fixture 를 재사용. 추가 fixture 가 필요하면 본 파일 안에 local 로 정의.
- `docs/ai/jobs/paper-e2e-001/patch.md` (Codex 가 작성).

제외 (절대 안 하는 것):

- 신규 production code 추가. 기존 동작이 e2e 흐름을 이미 만족하므로 **app/ 디렉터리 안 어떤 파일도 수정하지 않는다**. 단 (a) e2e 회귀를 통과시키기 위해 정말로 read-only helper 가 필요한 경우 `app/runtime/paper_status.py` 의 read-only 함수에 1-2 줄 추가는 허용 — 단 (i) 기존 surface 의 의미를 바꾸지 않고 (ii) 새 env 변수 / 새 settings 필드 추가 없이 (iii) 같은 PR 안에서 그 helper 가 새 테스트로 회귀되어야 한다. (b) `app/runtime/paper_runner.py` 또는 `app/runtime/paper_engine.py` 의 시그니처 / 동작 변경 금지. 본 plan 의 §4 / §5 시점 코드 검토 결과 어떤 production 변경도 필요하지 않다고 결론. **production 변경 0 이 default — 정말 막힐 때만 좁게 보강하고 patch.md 에 명시.**
- 신규 endpoint / GUI 페이지 / dashboard 컴포넌트 추가.
- live trading 활성화 / `LIVE_TRADING_ENABLED=true` / live broker API / 실주문 endpoint.
- 실전 base URL / 실전 TR_ID / 모의 미지원 TR_ID 추가.
- `OrderType.STOP` 도입. `OrderType.MARKET` 3중 가드 / `ALLOW_MARKET_ORDERS=true` reject 정책 변경. kill switch 동작 변경.
- 외부 HTTP 라이브러리 (`requests`, `httpx`, `aiohttp`, `urllib3`) import.
- KIS endpoint / TR ID / header / payload / response field 추측. KIS 관련 신규 transport 클래스 추가.
- `app/broker/*` / `app/oms/*` / `app/risk/*` / `app/portfolio/*` / `app/strategy/*` / `app/session/*` / `app/agent/*` / `app/config.py` / `app/domain/*` 변경.
- Strategy / Agent / LLM 이 broker 또는 KIS adapter 를 직접 import / 호출.
- executable order 를 Agent / LLM 이 생성하게 변경.
- OMS / RiskEngine 경계 약화.
- FX 변환 함수 / 환율 상수 / base currency 통합 함수 도입.
- `.env` / `.env.example` 변경. 새 env 변수 추가.
- 실제 app key, app secret, access token, Bearer token, 계좌번호 원문 코드/문서/테스트/patch 기록.
- `docs/kis/MISSING_OFFICIAL_VALUES.md` 수정.
- 자동 git commit / push / merge / deploy.

## 3. 수정해야 할 파일

| 경로 | 변경 종류 | 요약 |
| --- | --- | --- |
| `projects/paper-trading/tests/test_paper_e2e_pipeline.py` | NEW | end-to-end 흐름 회귀 (§5 의 9 개 함수). |
| `projects/paper-trading/docs/ai/jobs/paper-e2e-001/patch.md` | NEW (Codex 가 작성) | 수정 파일 / 검증 흐름 / broker 경계 유지 근거 / dry-run no-HTTP 근거 / Account·Portfolio·Journal 갱신 확인 / safety 회귀 / 테스트 결과 / 안전 grep / Claude 검증 프롬프트 / follow-up Codex 프롬프트 규칙. |

손대지 않는 파일:

- `app/` 전체 디렉터리 (production 코드). 본 작업은 **production 변경 0** 이 default.
- `app/broker/kis.py` / `app/broker/kis_http.py` / `app/broker/kis_token_cache.py` / `app/broker/kis_quote_mapper.py` / `app/broker/paper.py` / `app/broker/alpaca_paper.py` / `app/broker/base.py`.
- `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*` (단 §2 의 좁은 read-only helper 예외 — 본 plan 시점에서는 불필요).
- `app/strategy/*`, `app/session/*`, `app/agent/*` (있다면).
- `app/api/*`, `app/static/*`, `app/main.py`, `app/config.py`, `app/domain/*`.
- `tests/test_paper_e2e_api.py` 와 기타 기존 테스트 (수정 금지). 본 작업은 추가만 한다.
- `.env`, `.env.example`, `docs/kis/MISSING_OFFICIAL_VALUES.md`.

**범위 확장 사유**: 없음. 본 plan 시점에서 production 변경이 필요하다고 판단되는 케이스 0. Codex 가 구현 중에 정말로 막히는 케이스를 발견하면 (a) 변경 없이 우회할 수 있는 fixture / monkeypatch 방법을 먼저 시도하고, (b) 그래도 불가하면 patch.md 에 "production change required" 섹션을 명시하고 좁은 변경 사유 + 회귀 영향 분석을 함께 보고한다.

## 4. Codex 구현 지시문

자세한 단계는 `codex-task.md` 에 기록한다. 요지:

### 4.1 테스트 구조

- 파일: `tests/test_paper_e2e_pipeline.py`.
- import: `pytest`, `dataclasses.replace`, `datetime.datetime`, `datetime.timezone`, `datetime.timedelta`, `decimal.Decimal`, `unittest.mock.Mock`, `fastapi.testclient.TestClient`, 그리고 `app.api.server.create_app`, `app.broker.kis.KisBroker`, `app.broker.kis.KisOrderRejectedError`, `app.broker.paper.PaperBroker`, `app.config.Settings`, `app.domain.enums.OrderType`, `app.domain.enums.Side`, `app.domain.enums.Session`, `app.domain.enums.TradingMode`, `app.domain.market.StrategyInput`, `app.domain.orders.OrderIntent`, `app.domain.orders.BrokerOrder`, `app.domain.quote.Quote`, `app.oms.manager.OMS`, `app.portfolio.account.PaperAccount`, `app.portfolio.service.PortfolioService`, `app.risk.engine.RiskEngine`, `app.runtime.paper_engine.PaperEngine`, `app.runtime.paper_journal.PaperJournal`, `app.runtime.paper_runner.PaperRunner`, `app.strategy.premarket_gap.PremarketGapVolumeBreakoutStrategy`.
- conftest 의 `settings` 와 `make_snapshot` fixture 재사용.

### 4.2 로컬 헬퍼

```python
def _wire_paper_pipeline(settings):
    """Build the production-shape paper pipeline used by server.py.

    Returns: (strategy, risk, broker, account, portfolio, journal, oms, paper_engine, runner)
    All components share the SAME PaperBroker instance, mirroring server.py.
    """
    risk = RiskEngine(settings)
    broker = PaperBroker(
        max_quote_age_seconds=settings.paper_max_quote_age_seconds,
        allowed_sessions={Session(s) for s in settings.paper_allowed_sessions},
        max_fill_ratio_of_volume=settings.paper_max_fill_ratio_of_volume,
        commission_per_share=settings.paper_commission_per_share,
        commission_per_fill=settings.paper_commission_per_fill,
    )
    oms = OMS(settings, risk, broker)
    portfolio = PortfolioService()
    starting_cash = dict(
        settings.paper_starting_cash_by_currency
        or {settings.paper_base_currency: settings.paper_starting_cash}
    )
    account = PaperAccount(cash=starting_cash)
    journal = PaperJournal()
    paper_engine = PaperEngine(
        settings, broker=broker, account=account, portfolio=portfolio, journal=journal, oms=oms,
    )
    strategy = PremarketGapVolumeBreakoutStrategy(settings)
    runner = PaperRunner(settings, strategy, oms=oms, paper_engine=paper_engine)
    return strategy, risk, broker, account, portfolio, journal, oms, paper_engine, runner


def _fill_matching_quote_for(snapshot, *, last=None, bid=None, ask=None, volume=None):
    """Build a Quote that PaperBroker.tick will match against the snapshot's intent."""
    return Quote(
        symbol=snapshot.symbol,
        last=last if last is not None else snapshot.ask,
        bid=bid if bid is not None else snapshot.bid,
        ask=ask if ask is not None else snapshot.ask,
        volume=volume if volume is not None else max(snapshot.premarket_volume, 100000),
        timestamp=datetime.now(timezone.utc),
        source="e2e_test",
        session=Session.REGULAR,
        currency="USD",
    )


def _kis_paper_settings(settings, **overrides):
    """Return settings with KIS paper config wired and KIS_ORDER_DRY_RUN=True default."""
    data = {
        "kis_env": "paper",
        "kis_account_no": "12345678-01",
        "kis_app_key": "fake-key-XYZ",
        "kis_app_secret": "fake-secret-XYZ",
        "kis_api_mode": "paper",
        "kis_order_dry_run": True,
    }
    data.update(overrides)
    return replace(settings, **data)


class _RaiseOnCallOrderTransport:
    """Fake KisOrderTransport that raises if any HTTP path is attempted."""
    def submit_order(self, **kwargs):  # pragma: no cover — invoked means we lost dry-run
        raise AssertionError("KisBroker dry-run sent HTTP: " + ", ".join(sorted(kwargs)))
```

### 4.3 시나리오별 테스트

요구되는 단언 (정확 함수명은 §5 에 기재).

1. **happy path**:
   - `make_snapshot(premarket_volume=200_000, current_price=Decimal("106"), premarket_high=Decimal("106"), ask=Decimal("106"), bid=Decimal("105.90"), previous_close=Decimal("100"))` (gap_pct = 0.06 ≥ default 0.05).
   - `runner.run_once([snapshot])` → result[0].strategy.passed True / oms_ack 존재 / oms_error None / accepted_count==1.
   - 같은 broker 인스턴스의 `broker.open_orders()` 가 1 개. order.symbol == "AAPL", side == BUY, order_type == LIMIT.
   - `paper_engine.on_quote(_fill_matching_quote_for(snapshot, last=Decimal("106"), bid=Decimal("105"), ask=Decimal("106"), volume=500_000))` → trade list non-empty. account.cash["USD"] < starting_cash. portfolio snapshot positions["AAPL"].quantity > 0. journal.trades 첫 entry 의 symbol == "AAPL".
   - 또한 같은 fill 이 RiskEngine 의 risk_token 을 가진 BrokerOrder 에서 유래했음을 확인: trade entry oms_id == runner result oms_ack.oms_id.

2. **strategy blocked**:
   - `make_snapshot(premarket_volume=10)` → strategy result passed=False, blockers 에 `volume_below_threshold`.
   - `runner.run_once` 시 OMS.place 호출 0 (mock OMS 로 spy 하거나 `broker.open_orders()` 가 그대로 0 인 것으로 회귀).
   - 같은 broker 에 open_orders 가 변동 없음, account.cash 변동 없음.

3. **risk reject**:
   - settings 의 `symbol_allowlist=("MSFT",)` 로 좁히고 snapshot.symbol="AAPL" 사용 → RiskEngine 이 `symbol_not_allowed` 거절.
   - `runner.run_once([snapshot])` → oms_error contains `RiskEngine rejected`. broker.open_orders() 0.
   - `paper_engine.submit_intents([intent])` 직접 호출 시 result.results[0].accepted False / rejected_by == "risk_engine" / broker.open_orders() 0.

4. **OMS rejects non-paper broker mode**: synthetic broker with mode != PAPER → OMS.place raises `RuntimeError("OMS rejects non-paper broker")`. (좁은 회귀; OMS 경계 약화 방지.)

5. **OMS rejects live_trading_enabled**: settings.live_trading_enabled=True → OMS.place raises `RuntimeError("OMS refuses live trading in Phase 1")` 이전에 RiskEngine 거절 가능 — 본 테스트는 `settings.live_trading_enabled=True` 에서 OMS.place 가 거절됨만 확인.

6. **KIS dry-run leg**:
   - `_kis_paper_settings(settings)` (kis_order_dry_run=True).
   - 새 risk/OMS/KisBroker 구성: `risk = RiskEngine(settings_with_kis_in_allowlist)`, `kis_broker = KisBroker(settings_with_kis)`, `kis_broker._order_transport = _RaiseOnCallOrderTransport()` (HTTP 시도 시 즉시 AssertionError).
   - 안전상 별도 fresh OMS: `oms_kis = OMS(settings_with_kis, risk, kis_broker)`.
   - intent = OrderIntent(...LIMIT BUY...) 직접 작성 (Strategy 와 별개로, dry-run 전송 자체를 검증).
   - `oms_kis.place(intent)` → ack.status == "dry_run", ack.broker_order_id None.
   - `kis_broker.last_order_preview is not None`. `kis_broker.last_order_response is None`. `kis_broker.last_error is None`.
   - `_RaiseOnCallOrderTransport` 가 호출되지 않음 (테스트가 통과한다는 사실 자체가 보증).
   - 회귀: `kis_broker.healthcheck()["order_dry_run"] is True`. `kis_broker.healthcheck()["order_execution_implemented"] is False`. `kis_broker.healthcheck()["order_methods_fail_closed"] is True`.

7. **market order blocked by RiskEngine / OMS**:
   - `OrderIntent(order_type=OrderType.MARKET, ...)` 직접 작성.
   - `oms.place(intent)` 가 RiskEngine 또는 paper market order guard 에서 거절 (`RuntimeError` 또는 `RiskEngineDecision.approved=False`). broker.open_orders() 0.
   - 별 회귀: `app/config.py::load_settings` 가 `ALLOW_MARKET_ORDERS=true` 를 reject 하는 정책이 그대로 유효함을 단언 (monkeypatch env + load_settings 호출 시 ValueError).

8. **dashboard / status surface after fill**:
   - `TestClient(create_app())` 로 startup.
   - `POST /paper/order/simulate` 로 LIMIT BUY fill 발생 (기존 _order_payload).
   - `GET /paper/account` → cash["USD"] 감소.
   - `GET /paper/positions` → positions list 첫 entry quantity > 0, unrealized_pnl 필드 존재.
   - `GET /paper/fills` → fills list 첫 entry symbol == "AAPL".
   - `GET /paper/engine/status` → `account.cash["USD"]`, `portfolio.positions[0].quantity`, `journal.trades` 의 entry count 가 갱신됨.
   - `GET /paper/status` → `mode == "paper"`, `live_enabled is False`, `safety.market_orders_disabled is True`, `kis_order_methods_fail_closed is True`, `kis_order_dry_run is True`, `secret_exposed is False`.
   - response.text 어디에도 `KIS_APP_KEY` / `KIS_APP_SECRET` / `KIS_ACCOUNT_NO` / `app_secret` / `access_token` / `Bearer ` 등장 안 함.

9. **strategy / agent package isolation**:
   - `app/strategy/` 디렉터리 `.py` 파일 전부에 대해 `app.broker.kis` 또는 `app.broker.paper` 의 직접 import (regex `^\s*(from|import)\s+app\.broker\.(kis|paper)`) 가 0 회.
   - `app/agent/` 존재 시 동일.
   - 기존 회귀와 중복되지만 e2e 의 contract 회귀로 별도 단언.

## 5. 테스트 기준

신규 `tests/test_paper_e2e_pipeline.py` 의 함수명 (정확):

1. `test_e2e_happy_path_strategy_to_fill_through_oms_paper_engine`
2. `test_e2e_strategy_blocker_does_not_reach_oms_or_broker`
3. `test_e2e_risk_engine_reject_does_not_reach_broker`
4. `test_e2e_oms_rejects_non_paper_broker_mode`
5. `test_e2e_oms_rejects_live_trading_enabled`
6. `test_e2e_kis_dry_run_returns_dry_run_ack_without_http`
7. `test_e2e_market_order_intent_is_blocked_before_broker`
8. `test_e2e_dashboard_status_reflects_paper_engine_state_after_fill`
9. `test_e2e_strategy_and_agent_packages_do_not_import_broker_modules`

선택적 보강 함수 (Codex 재량으로 추가 가능, 단 1-2 개만):

- `test_e2e_dry_run_controller_can_be_started_stopped_without_http` — `DryRunController.start()/stop()` 가 HTTP / broker 호출 없이 idempotent 함을 회귀 (request 의 "기존 dry-run controller 연결 점검" 항).
- `test_e2e_no_secret_leak_in_pipeline_responses` — TestClient 응답 + 직접 호출 결과 모두에서 secret 회귀 (function 8 의 secret 단언과 중복이면 생략).

회귀 / 안전 회귀 (기존 테스트):

- 기존 `tests/test_paper_e2e_api.py`, `tests/test_paper_engine.py`, `tests/test_paper_runner.py`, `tests/test_oms.py`, `tests/test_risk_engine.py`, `tests/test_portfolio_service.py`, `tests/test_paper_journal.py`, `tests/test_dashboard.py`, `tests/test_status_modules.py`, `tests/test_api_paper_status.py`, `tests/test_kis_*`, `tests/test_strategy_premarket_gap.py` 모두 **변경 없음**. 본 작업이 production 코드를 건드리지 않으므로 회귀 깨질 가능성 0.
- 만약 회귀가 발생하면 Codex 는 production 변경을 즉시 중단하고 patch.md 에 사유 + 영향 분석을 보고. 회귀를 강제로 통과시키기 위해 테스트를 수정하지 말 것.

검증 명령:

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

전체 PASS 가 완료 조건.

안전 grep (Codex 가 patch.md 에 결과 첨부):

```bash
grep -rnE "^(from|import) (requests|httpx|aiohttp|urllib3)" app/broker tests
grep -rnE "^\s*(from|import)\s+app\.broker\.(kis|paper)" app/strategy app/agent 2>/dev/null
grep -rn "TTTT1002U\|TTTT1006U\|TTTT1004U\|TTTS1002U\|TTTS1001U\|TTTS0307U\|TTTS0308U\|TTTS0309U\|TTTT3014U\|TTTT3016U\|TTTT3017U\|TTTS3013U" app tests
grep -rn "TTTS3018R\|TTTT3039R\|TTTS3014R\|TTTS6036U\|TTTS6037U\|TTTS6038U\|TTTS6058R\|TTTS6059R" app tests
grep -rn "openapi.koreainvestment.com:9443" app tests
grep -rn "ALLOW_MARKET_ORDERS=true\|allow_market_orders=True" app
grep -rn "Bearer eyJ" app tests docs/ai/jobs/paper-e2e-001 || true
```

기대 결과: 외부 HTTP / live TR_ID / 모의 미지원 TR_ID / 실전 base URL / market order 활성화 / 실토큰 / Strategy·Agent 의 broker 직접 import 모두 0 lines (단 `app/config.py` 의 기존 `kis_base_url_live` default 와 `ALLOW_MARKET_ORDERS=true` reject 메시지 같은 기존 가드 라인은 잔존 가능 — patch.md 에서 명시).

## 6. 리뷰 체크리스트

안전 회귀:

- [ ] live trading 활성화 코드 / live broker API / 실주문 endpoint 추가 없음.
- [ ] 실전 base URL / 실전 TR_ID / 모의 미지원 TR_ID 코드/테스트/문서 추가 없음.
- [ ] `OrderType.MARKET` 3중 가드 / `ALLOW_MARKET_ORDERS=true` reject / kill switch / `validate_kis_order_request` 변경 없음.
- [ ] `OrderType.STOP` 도입 없음. enum 변경 없음.
- [ ] `app/broker/kis_http.py`, `app/broker/kis.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/base.py`, `app/broker/kis_token_cache.py`, `app/broker/kis_quote_mapper.py` 변경 없음.
- [ ] `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/agent/*` 변경 없음. 단 §2 의 좁은 read-only helper 예외가 발생했다면 patch.md 에 명시 + 영향 분석 포함.
- [ ] `app/config.py` / `app/api/*` / `app/static/*` / `app/main.py` / `app/domain/*` 변경 없음.
- [ ] 외부 HTTP 라이브러리 import 없음.
- [ ] secret / 계좌번호 / token / Bearer 원문 코드 / repr / exception / 로그 / pytest capture 노출 없음.
- [ ] `.env` / `.env.example` 수정 없음. 새 env 변수 추가 없음.
- [ ] Strategy / Agent / LLM 이 `app.broker.kis` 또는 `app.broker.paper` 또는 KisBroker / PaperBroker 직접 import / 호출 추가 없음.
- [ ] OMS / RiskEngine 경계 약화 없음. Strategy → RiskEngine → OMS → Broker 순서 그대로.

스코프 / 동작:

- [ ] 신규 production code 0. (정말로 막혀서 좁게 보강했다면 patch.md 의 "production change required" 섹션 + 회귀 영향 분석.)
- [ ] 신규 테스트 9 개 (선택 보강 포함 최대 11 개) 가 §5 의 함수명/시나리오와 정확히 일치.
- [ ] happy path 테스트가 cash 감소, position 증가, journal trade entry 갱신 세 가지를 모두 단언.
- [ ] KIS dry-run 테스트가 `_RaiseOnCallOrderTransport` 를 주입해서 HTTP 미발생을 회귀로 보장.
- [ ] Strategy blocker / RiskEngine reject 경로에서 `broker.open_orders()` 가 0 임을 단언.
- [ ] OMS non-paper / live-on 분기가 직접 회귀.
- [ ] TestClient 기반 dashboard / status surface 가 fill 이후 cash / position / journal / safety flag / secret 부재를 모두 단언.

테스트 / 문서:

- [ ] `python -m compileall app tests` 통과.
- [ ] `python -m pytest -p no:cacheprovider` 전체 PASS. 기존 테스트 회귀 0.
- [ ] `docs/ai/jobs/paper-e2e-001/patch.md` 에 수정 파일 / 검증 흐름 / broker 경계 유지 근거 / dry-run no-HTTP 근거 / Account·Portfolio·Journal 갱신 확인 / live trading off 회귀 / market order guard 회귀 / 테스트 결과 / 안전 grep 결과 / Claude 검증 요청 프롬프트 / follow-up Codex 프롬프트 규칙 모두 포함.

자동화 금지:

- [ ] commit / push / merge / PR / deploy 수행 없음.
- [ ] `.env` / secret / credential / API key / token 수정/노출 없음.
- [ ] `docs/kis/MISSING_OFFICIAL_VALUES.md` 변경 없음.
