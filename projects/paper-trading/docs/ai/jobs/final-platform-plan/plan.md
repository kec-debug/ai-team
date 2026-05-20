# final-platform-plan — Paper trading 최종 플랫폼 설계 plan

본 plan 은 **design-documentation only** 작업. 다음 turn 에서 Codex 가 11 개 design 문서를 생성하는 데 필요한 모든 지침을 정의한다. Application 코드 / 테스트 / `.env` / catalog 본문 / runtime 무변동.

## 1. 요청 요약

`projects/paper-trading` 의 현 시점 (paper-001 ~ paper-use-ready-001, 557 passed, runtime-soak-001 PASS) 까지의 구현 위에 **최종 플랫폼 설계 문서 11 종** 을 생성한다. 시스템 비전:

> "Paper training + agent research + strategy lab + live validation console."

24 시간 운영되는 서비스 / 분석 / 모니터링 / 학습 / 리포팅 플랫폼. **24 시간 거래 ≠ 24 시간 운영.** 실 주문은 항상 session → risk → OMS → guard → broker 경로.

## 2. 작업 범위

### 2.1 포함 (본 turn 의 Claude 가 직접 작성)

- `request.ko.md` (한국어 요청 정리)
- `plan.md` (본 파일)
- `codex-task.md` (Codex 가 다음 turn 에서 따를 지시문)

### 2.2 Codex 가 다음 turn 에 생성

- 11 design 문서 (`00_current_state.md` ~ `10_acceptance_criteria.md`)
- `patch.md` (생성 결과 보고)

### 2.3 절대 제외

- `app/` / `tests/` / `scripts/` / `docs/kis/` / `.env` / `.env.example` / `README.md` / `RUNBOOK.md` / `OPS_AUDIT.md` 어떤 파일도 수정.
- 새 endpoint / 새 KIS endpoint / 새 TR ID / 새 payload / 새 response field 추측.
- live trading 활성화 계획 / live arm 실행 / `KIS_ORDER_DRY_RUN=false` 토글.
- 자동 git commit / push / merge / deploy.
- 수익 보장 / 거짓 성과 주장 / 과장된 승률 주장.
- 시간 추정 ("2 주 안에 완료" 같은 표현 금지).
- 본 turn 또는 다음 turn 에서 코딩.

## 3. 현재 시스템 인벤토리 (00_current_state.md 의 anchor)

다음 항목이 **이미 구현 + 회귀 테스트로 잠겨 있음**:

### 3.1 Runtime / 도메인

- `app/runtime/paper_engine.py` — `PaperEngine.submit_intents()` + `on_quote()` (runtime-002).
- `app/runtime/paper_runner.py` — `PaperRunner` (OMS 또는 PaperEngine 둘 다 지원).
- `app/runtime/dry_run.py` — `DryRunController` start/stop/tick/summary.
- `app/runtime/paper_journal.py` — `PaperJournal` trade / order log.
- `app/runtime/paper_status.py` — paper engine status helper.
- `app/runtime/dry_run_report.py` — report file persistence.
- `app/runtime/__init__.py`.

### 3.2 Broker

- `app/broker/paper.py` — `PaperBroker.tick()` 의 partial fill / slippage_bps / market_impact_bps_per_pct_volume / max_spread_pct_for_fill (paper-002).
- `app/broker/kis.py` — `KisAuthClient` / `KisAccountClient` / `KisMarketDataClient` / `KisBroker` (place / cancel / replace / get_open_orders / get_fills / get_order_status) — **paper TR_ID 만**. live TR_ID 추가 0.
- `app/broker/kis_http.py` — `SafeKisHttpClient` (OAuth 전용 `{/oauth2/tokenP, /oauth2/revokeP}` allowlist).
- `app/broker/kis_token_cache.py` — token persistence.
- `app/broker/kis_quote_mapper.py` — Quote 매핑.
- `app/broker/alpaca_paper.py` — 미사용 stub.
- `app/broker/base.py`.

### 3.3 OMS / Risk / Portfolio / Strategy

- `app/oms/manager.py` — `OMS.place(intent)` — RiskEngine + paper-only mode 검증 + BrokerOrder 생성.
- `app/risk/engine.py` — `RiskEngine.evaluate(intent)` — 6 단 live trading 차단 + 3 중 market order guard + symbol allowlist + session policy.
- `app/portfolio/account.py` — `PaperAccount` cash by currency + apply_fill.
- `app/portfolio/service.py` — `PortfolioService` apply_trade + mark_price + snapshots.
- `app/strategy/premarket_gap.py` — `PremarketGapVolumeBreakoutStrategy`.
- `app/strategy/opening_range_breakout.py` — `OpeningRangeBreakoutStrategy` (strategy-002).
- `app/strategy/base.py` — `Strategy` ABC + `StrategyResult`.
- `app/session/__init__.py` — `SessionRouter`.

### 3.4 Ops / API / UI

- `app/ops/preflight.py` — `compute_live_validation_status()` (live-validation-001).
- `app/api/server.py` — FastAPI lifespan + state wiring.
- `app/api/routes.py` — 기존 endpoint:
  - `/healthz`, `/dashboard`
  - `/paper/status`, `/paper/account`, `/paper/positions`, `/paper/fills`, `/paper/orders`, `/paper/engine/status`
  - `/paper/order/simulate`
  - `/paper/run`, `/paper/report/summary`
  - `/paper/dry-run/start`, `/paper/dry-run/stop`, `/paper/dry-run/tick`, `/paper/dry-run/status`
  - `/reports/dry-run/analyze`, `/reports/dry-run/latest`
  - `/ops/status`, `/ops/preflight`
- `app/static/dashboard.html` — Korean UX (paper-ux-001) + safety banner + Live Validation 준비 상태 + Preflight Checklist (live-validation-001).
- `app/main.py`.

### 3.5 Config / 도메인 모델

- `app/config.py` — Settings (frozen dataclass) + `load_settings()` + 안전 가드 (`ALLOW_MARKET_ORDERS=true` reject, `LIVE_TRADING_ENABLED=true` reject in Phase 1).
- `app/domain/enums.py` — `Side`, `OrderType` (LIMIT / STOP_LIMIT / MARKET), `Session`, `TradingMode`.
- `app/domain/market.py` — `StrategyInput`.
- `app/domain/orders.py` — `OrderIntent`, `Order`, `BrokerOrder`, `OrderAck`.
- `app/domain/quote.py` — `Quote`.
- `app/domain/fills.py` — `Fill`.

### 3.6 Tests / Scripts / Docs

- `tests/` — 557 passed (paper-use-ready-001 시점).
- `scripts/` — `start_server.sh` / `stop_server.sh` / `restart_server.sh` / `status.sh` / `smoke_check.sh` / `safety_grep.sh` / `use_ready_check.sh` / `_common.sh`.
- `docs/RUNBOOK.md` — 한국어 운영 가이드.
- `docs/OPS_AUDIT.md` — 한국어 최종 ops 안전 감사.
- `docs/kis/MISSING_OFFICIAL_VALUES.md` — KIS catalog (`Confirmed: yes` paper 만 사용).
- `docs/kis/MISSING_MARKET_DATA_VALUES.md` — 시세 catalog.

### 3.7 미구현 / Known issues (14_known_issues 가 아니라 각 doc 에 분산)

- `kis_authenticated=True` 까지 trigger 되는 production wiring 부재 (별 job).
- `live_validation_ready=READY` 가 표시되더라도 실제 live 코드 경로 0 (의도된 상태).
- `capabilities()` 의 `submission` / `cancel` / `replace` / `open_orders` / `fills` / `order_status` 플래그 모두 `False` (보수적 advertise — UI status-surface job 으로 분리).
- KIS query / order 응답 일부 sub-field `<TBD>` (별 catalog job 필요 시).
- runtime-soak 의 검증은 1 회 PASS — 더 긴 / 다양한 시장 시나리오 필요.
- Strategy 가 두 개 (Premarket Gap + Opening Range Breakout). 더 다양한 전략 / Agent pipeline 미통합.
- LLM / Agent pipeline 미구현 (본 plan 의 doc 04 가 처음 정의).
- PostgreSQL / Redis 미사용 — paper journal 은 in-memory + 파일 (별 storage job 필요 시).
- TrainingRun / TrainingTick / AgentTrace / AuditEvent 도메인 모델 미정의 — doc 06 가 처음 정의.
- 24 시간 운영 service 모드 미설계 — doc 03 가 처음 정의.

## 4. 11 design 문서 — design intent + 필수 포함 항목

각 문서는 **한국어**, **운영자 (non-developer) 가 읽을 수 있는 수준** + **개발자가 implementation backlog 로 직접 변환 가능한 수준** 양쪽 모두 충족.

### 4.1 `00_current_state.md`

**Intent**: 현재 무엇이 land 되어 있고 무엇이 미구현인지 ground truth.

**필수 포함**:

- §3.1 ~ §3.5 의 인벤토리를 한국어로 풀어쓰기.
- §3.6 의 테스트 / 스크립트 / 문서 인벤토리.
- §3.7 의 known issues 14 개.
- "현재 commit (`3812144 add paper trading use-ready operations`) 시점" 명시.
- pytest 557 passed 베이스라인.
- safety guard 의 현재 상태 (6 단 live trading 차단 / 3 중 market guard / dry-run default / kill switch 등).
- 다음 doc 들이 어디서 시작하는지 anchor.

**제외**: 미래 작업 계획 (그건 09_implementation_backlog 에서).

### 4.2 `01_product_spec.md`

**Intent**: 플랫폼 전체 영역의 product structure.

**필수 포함 영역** (요청 §"Overall Product Structure" 그대로):

1. Overview Dashboard
2. Paper Training
3. Agent Research
4. Strategy Lab
5. Orders / Fills
6. Portfolio
7. Reports / Analytics
8. Live Validation Console
9. Risk / Ops / Settings
10. Runbook / Incident View

**각 영역마다**:

- 한 줄 정의.
- 사용자 (운영자 / 분석가 / 개발자) 의 use case.
- 이미 구현된 부분 (anchor: `00_current_state.md`).
- 아직 미구현인 부분.
- 다른 영역과의 의존관계.

**제외**: API endpoint 상세 (06 으로 분리), UI HTML (02 로 분리).

### 4.3 `02_ui_ux_spec.md`

**Intent**: 운영용 (marketing 아님) dashboard 디자인.

**필수 포함**:

- 항상 보이는 safety banner (info / warning / danger 3 단 escalation — live-validation-001 의 기존 동작 인용).
- 명확한 paper / live 상태 표시.
- 색상 + 문구 기반 안전 상태.
- 초보자용 한국어 설명.
- Paper-only / dry-run-only indicator.
- Live area 는 default lock 상태.
- Paper training start / stop / status / history.
- Agent 분석 결과: evidence / confidence / blockers / trace.
- Strategy 결과: candidate / block reason / mock order.
- Risk block reason 가시성.
- Session block 가시성.
- Stale quote 가시성.
- Spread guard 가시성.
- Kill switch 가시성.
- Order / fill / journal / PnL 가시성.

**Layout**: ASCII wireframe 또는 영역별 Markdown 표 사용. 실제 HTML 코드 작성 금지.

### 4.4 `03_paper_training_runtime.md`

**Intent**: paper training 의 24 시간 service 모드 + replay / synthetic / live quote source / 보안 가드.

**필수 포함**:

- Paper runner 가 24 시간 service 로 동작 가능한 구조.
- Universe / watchlist 관리.
- KRX / US session 인식 simulation.
- 시장 닫혀 있을 때 동작: analysis / replay / preparation 가능, 주문 실행은 valid session 안에서만.
- 교체 가능한 data source:
  - replay source
  - synthetic source
  - live quote source
- Paper order / fill / position / journal / event log 저장.
- Strategy 레벨 tick 결과 저장.
- TrainingRun-level aggregation.
- 안전 가드 (모두 적용):
  - kill switch
  - stale quote guard
  - spread guard
  - volatility guard
  - max notional
  - max daily loss
  - max position size
  - max orders per day
  - session guard
  - duplicate idempotency guard

**제외**: storage schema 상세 (06 으로 분리).

### 4.5 `04_agent_strategy_pipeline.md`

**Intent**: Agent + Strategy 의 합쳐진 runtime pipeline + LLM provider.

**필수 포함**:

- 7 종 Agent (각각 typed input / output / score / confidence / reasons / blockers / metadata / execution trace / provider_used / fallback_used / parse_status):
  - MarketResearchAgent
  - CompanyOverviewAgent
  - FinancialAnalysisAgent
  - IndustryModelAgent
  - NewsAgent
  - RiskAnalysisAgent
  - InvestmentRecommendationAgent
- Agent flow:
  1. universe / watchlist candidate 생성.
  2. company / financial / industry / news context enrichment.
  3. Risk hard block 적용.
  4. Recommendation agent 가 trade idea + non-executable order intent 생성.
  5. Strategy engine 이 context → entry / exit candidate.
  6. RiskEngine 의 pre-trade verdict.
  7. OMS 가 승인된 intent 만 order request 생성.
- LLM provider design:
  - default = rule-based / deterministic.
  - LLM 은 optional.
  - LLM failure → deterministic fallback.
  - malformed LLM output → Pydantic validation block.
  - LLM 단독으로 hard risk block 을 풀 수 없음.
- Strategy boundary (현재와 동일):
  - broker 직접 호출 0.
  - candidate / non-executable intent 까지만 생성.

**제외**: Agent 별 구체 prompt template (별 future job).

### 4.6 `05_live_validation_console.md`

**Intent**: live console — paper dashboard 와 분리된 페이지. **default lock 상태**.

**필수 포함**:

- Live default locked.
- Readiness checklist (live-validation-001 의 14 항 재인용 + 확장):
  - KIS config loaded
  - KIS auth status (현재 false 가 정상)
  - Token status
  - Account loaded
  - Positions loaded
  - Market data available
  - Order entry capability (현재 보수적 false)
  - Cancel / replace capability
  - Daily loss limit configured
  - Max order count configured
  - Symbol whitelist configured
  - Manual approval required
  - Kill switch status
  - Recent paper soak result
  - Recent test result
  - Operator acknowledgment
- 중요 명시:
  - `live_validation_ready` 가 14 항 전체 checklist 를 반영.
  - `kis_order_entry_ready` 가 actual capability 반영, placeholder 0.
  - `not_implemented` 가 ready 로 표시되지 않음.
  - live console 은 safety gate + status check 중심. 주문 버튼 0.
  - arm / disarm 개념 설계 (실제 arm 실행은 별 future job).
- 실 live 주문 실행은 본 doc 의 범위 밖 — 별 future approval step 이라고 명시.

### 4.7 `06_api_data_storage.md`

**Intent**: API surface + data model + storage 종합 설계.

**필수 포함**:

#### API (기존 보존 + 신규):

```
/status                              GET
/ops/status                          GET (live-validation-001)
/ops/preflight                       GET (live-validation-001)
/paper/status                        GET (기존)
/paper/training/start                POST (NEW)
/paper/training/stop                 POST (NEW)
/paper/training/tick                 POST (NEW)
/paper/training/runs                 GET  (NEW)
/paper/orders                        GET (기존)
/paper/fills                         GET (기존)
/paper/positions                     GET (기존)
/agents/run                          POST (NEW)
/agents/status                       GET (NEW)
/agents/traces                       GET (NEW)
/strategies                          GET (NEW)
/strategies/{strategy_id}            GET (NEW)
/strategies/{strategy_id}/backtest   POST (NEW)
/reports                             GET (NEW)
/reports/{run_id}                    GET (NEW)
/live/status                         GET (NEW, locked)
/live/preflight                      GET (NEW, locked)
/live/account                        GET (NEW, locked)
/live/positions                      GET (NEW, locked)
/live/arm                            POST (NEW, locked + manual approval)
/live/disarm                         POST (NEW, locked)
/risk/status                         GET (NEW)
/risk/kill-switch                    GET / POST (NEW)
```

각 endpoint 별: purpose / request / response / authority+safety conditions / side effects / paper-live 분리.

#### Data Model (도메인 dataclass 정의):

- `TrainingRun` — 24h paper 학습 세션
- `TrainingTick` — 개별 tick 결과
- `UniverseSnapshot` — universe 시점 스냅샷
- `WatchlistCandidate` — agent 가 추천한 후보
- `AgentTrace` — agent 호출 trace
- `AgentOutput` — agent 결과 (score / confidence / reasons / blockers / metadata)
- `StrategyCandidate` — strategy 후보
- `StrategyDecision` — strategy 결정
- `RiskVerdict` — RiskEngine 결과
- `OrderIntent` (기존)
- `OrderRequest` — OMS 가 만든 executable
- `BrokerOrder` (기존)
- `OrderState` — 상태 transition
- `Fill` (기존)
- `PositionSnapshot`
- `PortfolioSnapshot`
- `Report`
- `LiveReadinessStatus` (live-validation-001 와 통합)
- `PreflightItem` (live-validation-001 와 통합)
- `AuditEvent`

각 모델별: required fields / status transition / idempotency key / timestamp / correlation_id / source/provider / persistence target.

#### Storage:

- PostgreSQL: orders / fills / portfolio snapshots / audit events / training runs / agent traces / strategy decisions / reports.
- Redis: idempotency / kill switch / latest quote / latest status / runner heartbeat / locks.
- File / JSON fallback: local paper reports (현재 사용 중인 dry_run report 와 정합).
- Replayable event log structure.
- Startup rehydrate strategy.
- Crash recovery strategy.

**제외**: 구체 ALTER TABLE 문 (별 storage migration job).

### 4.8 `07_risk_safety_observability.md`

**Intent**: Risk + Safety + Observability 통합.

**필수 포함**:

#### Risk / Safety:

- Global kill switch.
- Paper / live separate kill switch.
- Max daily loss.
- Max order notional.
- Max orders per day.
- Max position size.
- Stale quote guard.
- Spread guard.
- Volatility guard.
- Session guard.
- Duplicate idempotency guard.
- Broker disconnect guard.
- Token expired guard.
- Live arming guard.
- Manual approval guard.
- Allowlist guard.
- Market order guard.
- Dry-run guard.
- Paper / live mode mismatch guard.

#### Observability:

- Dashboard status cards (live-validation-001 의 banner / readiness / checklist 인용 + 확장).
- Runtime heartbeat.
- Paper runner status.
- Agent pipeline status.
- Strategy status.
- Risk status.
- OMS status.
- Broker status.
- Reconciliation status.
- Last error.
- Recent audit events.
- Alert skeleton.
- Incident view.
- Report export.

### 4.9 `08_runbook.md`

**Intent**: 운영자 / 개발자용 runbook. RUNBOOK.md 의 확장판.

**필수 포함**:

- Paper training start / stop.
- Strategy 추가.
- Universe / watchlist 변경.
- Agent provider 변경.
- LLM fallback handling.
- Stale quote handling.
- Broker disconnect handling.
- Token expiration handling.
- Order rejection handling.
- Kill switch 사용.
- Live checklist.
- Live validation 절차.
- Rollback 절차.
- Dashboard troubleshooting.
- tmux 서버 관리.
- PuTTY 터널 가이드 (현재 RUNBOOK.md 와 정합).

### 4.10 `09_implementation_backlog.md`

**Intent**: 위 doc 들에서 도출된 implementation backlog. Claude / Codex job 으로 직접 변환 가능한 형태.

**필수 포함 (각 backlog item)**:

- job 이름 (예: `paper-runtime-002-training-service`, `agent-001-market-research`, etc.)
- purpose.
- 수정 파일 / 신규 파일.
- 완료 기준 (acceptance criteria).
- 테스트 plan.
- Risk notes.
- Rollback notes.

**Backlog item 예시 (Codex 가 채울 것)**:

- TrainingRun / TrainingTick 도메인 모델 + 저장소 추가.
- Agent base abstract + 7 종 Agent 구현 (LLM optional + deterministic fallback).
- Strategy Lab UI + backtest endpoint.
- Live console 분리 페이지 + arm/disarm endpoint (locked).
- PostgreSQL 도입 + 마이그레이션 (별 job).
- Redis 도입 (별 job).
- 추가 안전 가드 (volatility / broker disconnect / token expired) 도입.
- Observability dashboard + heartbeat / alert skeleton.
- runbook 확장 (`08_runbook.md` 와 RUNBOOK.md 동기화).
- runtime-soak 확장 (longer / more scenarios).

**제외**: 시간 추정. 각 backlog 의 size 는 "S/M/L" 같은 정성적 label 만 (요청 §"No time estimate" 준수).

### 4.11 `10_acceptance_criteria.md`

**Intent**: 본 design 이 "완성" 되었다고 볼 수 있는 조건 + 각 후속 job 의 검수 기준 template.

**필수 포함**:

- 본 design 자체의 acceptance (11 doc 존재 + 한국어 + 운영자/개발자 양쪽 readable + 보안 원칙 준수 + 코드 0 line).
- 각 후속 job 이 따라야 할 일반 acceptance template:
  - pytest 전체 PASS.
  - safety grep clean.
  - `app/broker/kis_http.py` 같은 보호 영역 무변동.
  - secret / 계좌번호 / token 노출 0.
  - `commit / push / merge / deploy` 자동화 0.
  - Strategy / Agent / LLM 의 broker 직접 호출 0.
  - OMS / RiskEngine 우회 0.
  - `OrderType.STOP` 미도입.
  - FX 변환 미도입.
  - Korean docs (필요 시).
- "정의 끝" 의 명확한 marker — 본 design 의 다음 단계가 `09_implementation_backlog` 에서 시작.

## 5. 횡단 원칙 (모든 doc 적용)

### 5.1 언어

- **한국어 우선**. 기술 용어는 영어 그대로 사용 (예: `OrderIntent`, `RiskEngine`).
- 운영자가 읽을 수 있도록 짧은 문장 + 예시.
- 개발자 친화: code identifier 는 inline `code` 로 명시.

### 5.2 No fake claims

- 수익 보장 / 거짓 성과 / 과장된 승률 표현 0.
- "이 시스템으로 $X 벌 수 있다" 류 표현 금지.
- 백테스트 / paper 결과는 "검증 데이터" 로만 기술. "수익 보장" 으로 기술 금지.

### 5.3 No time estimate

- "1주 내", "2 sprint", "Q1 까지" 같은 시간 표현 0.
- Backlog size 는 정성적 (S/M/L 또는 별 단계 — design 의 dependency 만 기술).

### 5.4 Safety boundary (모든 doc 반복 명시)

- Strategy → RiskEngine → OMS → BrokerAdapter 경계.
- Agent 는 non-executable intent 까지만.
- LLM 단독 risk block 해제 불가.
- KIS 미확인 값은 TODO / fail-closed.
- live 는 default lock + 별도 manual approval.
- paper 와 live 분리.

### 5.5 Existing reference

- 새 catalog 값 추측 0. `docs/kis/MISSING_OFFICIAL_VALUES.md` 의 `Confirmed: yes` 행만 인용.
- `docs/ai/MASTER_TRADING_ROADMAP.md` / `ROADMAP_STATUS.md` 의 원칙과 정합.
- 기존 `RUNBOOK.md` / `OPS_AUDIT.md` 와 동기화.

### 5.6 No coding

- 본 plan + codex-task + 11 doc 어디에도 production code 추가 0.
- Pseudocode / 도식은 OK.
- 실제 `.py` 파일에 코드 작성 금지.

## 6. Codex task 의 절대 제약 (codex-task.md 에 명시)

본 plan 의 doc 4 의 "필수 포함" 모두 + 다음 메타-제약:

1. **`app/` / `tests/` / `scripts/` / `docs/kis/` / `.env` / `.env.example` / `README.md` / `docs/RUNBOOK.md` / `docs/OPS_AUDIT.md` 어떤 파일도 modify/create/delete 금지**.
2. 다른 job 디렉터리 (`docs/ai/jobs/<other>/`) 무변동.
3. 신규 파일은 `docs/ai/jobs/final-platform-plan/` 디렉터리 안에만 — 11 design doc + patch.md 까지 12 개 신규.
4. KIS endpoint / TR ID / payload / header / response field 새로 만들지 않음. 인용은 `docs/kis/MISSING_OFFICIAL_VALUES.md` 에서.
5. 외부 web fetch 없이 작성. 기존 repo 의 코드 / docs 만 참조.
6. Korean writing. 개발자 / 운영자 양측 readable.
7. 수익 보장 / 시간 추정 / 거짓 성과 0.
8. 자동 git commit / push / merge / deploy 0.

## 7. 검증 기준

본 plan + codex-task 의 review 시 확인:

- 11 design doc + patch.md 가 정확히 12 파일 생성됨.
- 어떤 doc 도 application 코드 / 테스트 / `.env` / catalog 본문을 추가하지 않음.
- 각 doc 이 한국어이며, §4 의 "필수 포함" 항목을 모두 다룸.
- 수익 보장 / 시간 추정 / KIS endpoint 추측 / live arming 0.
- `docs/ai/jobs/final-platform-plan/` 외 디렉터리 어떤 파일도 modify 되지 않음.
- patch.md 가 다음 모두 포함:
  - 생성 파일 목록 (12 개).
  - 각 doc 의 짧은 요약.
  - 안전 grep 결과.
  - Claude 검증 요청 프롬프트.
  - REQUEST CHANGES / BLOCK 시 follow-up Codex prompt 규칙.

## 8. 리뷰 체크리스트 (본 plan 자체)

- [ ] §3 의 인벤토리가 실제 `app/` / `tests/` 구조와 일치.
- [ ] §4 의 11 doc 의 design intent 가 요청 §1 ~ §14 의 모든 항목을 다룸.
- [ ] §5 의 횡단 원칙이 일관되게 모든 doc 에 적용됨.
- [ ] §6 의 Codex 제약이 codex-task.md 에 그대로 들어감.
- [ ] §7 의 검증 기준이 Claude review prompt 와 정합.
- [ ] 본 plan 자체가 production 코드 / 테스트 / `.env` / catalog 본문을 추가하지 않음.

## 9. 본 turn 의 산출물

- [x] `request.ko.md` (이미 작성).
- [x] `plan.md` (본 파일).
- [ ] `codex-task.md` (다음 step).

**본 turn 의 Claude 는 11 design doc 을 직접 작성하지 않는다.** Codex 가 다음 turn 에서 작성. 본 turn 은 plan + codex-task 까지만.
