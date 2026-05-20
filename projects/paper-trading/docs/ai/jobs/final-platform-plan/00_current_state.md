# 00. 현재 상태 기준선

본 문서는 `3812144 add paper trading use-ready operations` 시점의 paper-trading 시스템을 기준으로 한다. 이 기준선은 이후 `01_product_spec.md` 부터 `10_acceptance_criteria.md` 까지의 모든 설계가 의존하는 ground truth 이며, 현재 테스트 기준은 `pytest -p no:cacheprovider` 557 passed 이다.

## 1. 핵심 운영 상태

- 기본 모드: paper trading.
- live trading: 기본 잠금 상태이며 활성화 경로 없음.
- 주문 경계: `Strategy` -> `RiskEngine` -> `OMS` -> `BrokerAdapter`.
- Agent / LLM: 현재 실행 경로에 통합되지 않았고, future design 에서도 non-executable intent 까지만 허용.
- KIS: catalog 확인 범위 안에서 paper 중심으로 fail-closed.
- 대시보드: paper / dry-run / live validation readiness 를 한국어로 표시.
- 운영 도구: `scripts/use_ready_check.sh`, `scripts/safety_grep.sh`, `docs/RUNBOOK.md`, `docs/OPS_AUDIT.md`.

## 2. Runtime / 도메인 인벤토리

| 모듈 | 현재 역할 | 안전 의미 |
| --- | --- | --- |
| `app/runtime/paper_engine.py` | `PaperEngine.submit_intents()` 와 `on_quote()` 로 paper order / fill / account / portfolio / journal 갱신 | OMS 없이는 intent 제출 불가 |
| `app/runtime/paper_runner.py` | strategy 결과를 OMS 또는 PaperEngine 으로 전달 | Strategy 가 broker 를 직접 호출하지 않도록 중간 경로 제공 |
| `app/runtime/dry_run.py` | `DryRunController` start / stop / tick / summary | KIS 직접 호출 없음, caller-driven synchronous controller |
| `app/runtime/paper_journal.py` | order / trade log | paper fill 감사 추적 |
| `app/runtime/paper_status.py` | paper engine 상태 helper | dashboard / status 응답 구성 |
| `app/runtime/dry_run_report.py` | dry-run report file persistence | local report 기반 분석 |
| `app/runtime/__init__.py` | runtime package marker | runtime import boundary |

## 3. Broker 인벤토리

| 모듈 | 현재 역할 | 현재 제한 |
| --- | --- | --- |
| `app/broker/paper.py` | `PaperBroker.tick()` 기반 partial fill, slippage, market impact, spread guard | paper-only broker |
| `app/broker/kis.py` | KIS auth/account/market/order/query adapter | paper catalog 확인 범위, live activation 없음 |
| `app/broker/kis_http.py` | OAuth 전용 safe HTTP allowlist | broker 일반 HTTP 경계와 분리 |
| `app/broker/kis_token_cache.py` | paper token persistence | secret 원문 노출 금지 |
| `app/broker/kis_quote_mapper.py` | KIS quote 를 `Quote` 로 매핑 | 미확인 field 는 fail-closed |
| `app/broker/alpaca_paper.py` | paper stub | 현재 운영 경로 핵심 아님 |
| `app/broker/base.py` | broker interface | adapter boundary |

## 4. OMS / Risk / Portfolio / Strategy

| 영역 | 현재 구현 | 설계 anchor |
| --- | --- | --- |
| OMS | `app/oms/manager.py` 의 `OMS.place(intent)` | RiskEngine 승인 후에만 `BrokerOrder` 생성 |
| Risk | `app/risk/engine.py` 의 `RiskEngine.evaluate(intent)` | live 차단, market order guard, allowlist, notional guard |
| Account | `app/portfolio/account.py` | currency별 paper cash 와 fill 적용 |
| Portfolio | `app/portfolio/service.py` | position, realized / unrealized PnL snapshot |
| Strategy | `premarket_gap`, `opening_range_breakout` | broker 직접 호출 없음 |
| Session | `app/session/__init__.py` | US session policy 기반 order allowed 판단 |

## 5. Ops / API / UI

| 영역 | 현재 구현 |
| --- | --- |
| Ops preflight | `app/ops/preflight.py` 의 read-only live validation readiness |
| API server | FastAPI lifespan 이 settings, risk, broker, OMS, strategy, paper_engine, dry_run_controller 연결 |
| API routes | `/healthz`, `/dashboard`, `/paper/*`, `/reports/*`, `/ops/status`, `/ops/preflight` |
| Dashboard | 한국어 paper UX, safety banner, Live Validation 준비 상태, Preflight Checklist |
| Main | `app/main.py` 는 app import entry |

## 6. Config / 도메인 모델

| 모델 | 현재 역할 |
| --- | --- |
| `Settings` | frozen dataclass, paper-safe default, unsafe env reject |
| `TradingMode` | paper / live enum, 현재 paper 만 지원 |
| `OrderType` | LIMIT / STOP_LIMIT / MARKET, STOP 없음 |
| `StrategyInput` | strategy 입력 snapshot |
| `OrderIntent` | non-executable strategy intent |
| `Order`, `BrokerOrder`, `OrderAck` | OMS / broker order domain |
| `Quote` | broker-agnostic quote |
| `Fill` | paper fill domain |

## 7. Tests / Scripts / Docs

- `tests/`: 557 passed baseline.
- `scripts/`: server lifecycle, dry-run, smoke, safety grep, use-ready check.
- `docs/RUNBOOK.md`: 한국어 운영 가이드.
- `docs/OPS_AUDIT.md`: 안전 감사 보고서.
- `docs/kis/MISSING_OFFICIAL_VALUES.md`: KIS catalog source of truth.
- `docs/kis/MISSING_MARKET_DATA_VALUES.md`: market data catalog gap tracking.

## 8. 현재 안전 가드

### 8.1 Live trading 차단

1. `Settings` 기본값이 paper / live disabled.
2. unsafe live env 는 `load_settings()` 에서 reject.
3. `RiskEngine.evaluate` 가 paper mode 와 live disabled 조건 확인.
4. `OMS.place` 가 live 상태를 reject.
5. 실주문 UI / endpoint 없음.
6. KIS adapter 는 paper 확인 범위 밖 동작을 fail-closed.

### 8.2 Market order guard

1. market allow env 는 설정 단계에서 reject.
2. `RiskEngine` 이 market order 를 기본 reject.
3. dashboard / scripts 에 market allow toggle 없음.

### 8.3 Dry-run / kill switch

- `KIS_ORDER_DRY_RUN=true` 가 기본 운영 기준.
- kill switch 는 주문 생성 경로를 차단하는 전역 운영 제어로 취급.
- live validation readiness 는 UX 신호이며 safety gate 를 해제하지 않음.

## 9. Known issues

1. `kis_authenticated=True` 까지 이어지는 production wiring 은 별 job 필요.
2. `live_validation_ready=READY` 가 표시되어도 실제 live 코드 경로는 없음.
3. `capabilities()` 의 submission / cancel / replace / open_orders / fills / order_status 는 보수적으로 false.
4. KIS query / order 응답 일부 sub-field 는 `<TBD>`.
5. runtime-soak 는 1회 PASS이며 더 긴 scenario 검증 필요.
6. strategy 는 두 개뿐이며 strategy lab 은 미구현.
7. LLM / Agent pipeline 은 미구현.
8. PostgreSQL / Redis 미사용.
9. `TrainingRun`, `TrainingTick`, `AgentTrace`, `AuditEvent` 미정의.
10. 24시간 service mode 미설계.
11. dashboard 는 운영용이지만 full incident console 은 아님.
12. replay / synthetic / live quote source abstraction 미완성.
13. storage rehydrate / crash recovery 전략 미구현.
14. live console 은 readiness view 까지만 있고 arm/disarm 은 future locked design.

## 10. 다음 문서 anchor

본 문서 이후의 doc 들은 본 ground truth 를 기준으로 작성한다. 미래 계획은 `09_implementation_backlog.md` 에서만 backlog 로 정리하며, 현재 구현 상태를 과장하지 않는다.
