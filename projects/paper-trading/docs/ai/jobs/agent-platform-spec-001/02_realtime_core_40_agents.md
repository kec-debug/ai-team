# 02. 실시간 핵심 40 에이전트

본 문서는 장중 paper runtime에서 사용하는 40개 핵심 역할 모듈을 정의한다. 이 모듈들은 `final-platform-plan/03_paper_training_runtime.md`와 `04_agent_strategy_pipeline.md`를 확장하지만 broker를 직접 호출하지 않는다.

## 공통 안전 규칙

Agent는 Broker가 아니다. OMS만 executable `BrokerOrder`를 만든다. Broker Gateway Service만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태이며 이 문서는 이를 바꾸지 않는다.

## 공통 typed I/O

| 항목 | 내용 |
| --- | --- |
| Input | `AgentInput(symbol, snapshot, session, quote, event_context, paper_state, ops_state)` |
| Output | `AgentOutput(score, confidence, reasons, blockers, metadata, trace)` |
| Score / Confidence | 0.0~1.0, 없으면 null |
| Provider | 기본 rule-based, 일부 LLM optional |
| Fallback | deterministic |
| Parse status | ok / malformed / timeout |
| 안전 가드 | kill switch, stale quote, spread guard, dry-run, OMS boundary |

## 40 모듈 catalog

| # | 한국어 / alias | 소속 서비스 | 책임 | Input typed | Output typed / 다음 모듈 | Score / Confidence | Reasons / Blockers 예시 | Provider / Fallback / Parse | 안전 가드 / 의존 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 오케스트레이터 / `OrchestratorAgent` | Orchestrator | 서비스 lifecycle과 tick 순서 조율 | service_state, schedule, ops_state | lifecycle_decision -> all services | confidence only | service_down, kill_switch | rule / deterministic / ok | broker 0, kill broadcast |
| 2 | 세션 관리 / `SessionManagerAgent` | Orchestrator | market session 판단 | timestamp, exchange, calendar | session_state -> Strategy | confidence | closed_session | rule / deterministic / ok | closed면 intent 0 |
| 3 | 데이터 수집 / `DataCollectionAgent` | Market Data | quote/snapshot 수집 | symbol, source_config | raw_snapshot -> normalization | confidence | source_unavailable | rule / deterministic / timeout | read-only |
| 4 | 데이터 정규화 / `DataNormalizationAgent` | Market Data | source별 field를 `StrategyInput` 후보로 정리 | raw_snapshot | normalized_snapshot -> cache | confidence | malformed_price | rule / deterministic / malformed | KIS 미확인 field TODO |
| 5 | 데이터 캐시 / `DataCacheAgent` | Market Data | 최근 snapshot 보관 | normalized_snapshot | cached_snapshot -> scanner | confidence | cache_miss | rule / deterministic / ok | secret 0 |
| 6 | 데이터 무결성 / `DataIntegrityAgent` | Market Data | 가격/시간/volume invariant 검사 | cached_snapshot | integrity_verdict -> scanner | score | stale_quote, ask_lt_bid | rule / deterministic / ok | stale guard |
| 7 | 스캐너 / `ScannerAgent` | Market Data | watchlist 후보 추출 | universe, integrity_verdict | candidate_list -> Strategy | score | no_volume | rule / deterministic / ok | 주문 0 |
| 8 | 종목 universe / `UniverseAgent` | Market Data | 허용 종목 목록 관리 | config_allowlist, metadata | universe -> scanner | confidence | symbol_not_allowed | rule / deterministic / ok | allowlist guard |
| 9 | 종목 metadata / `SymbolMetadataAgent` | Market Data | sector, currency, exchange metadata 제공 | symbol | symbol_profile -> analysis | confidence | metadata_missing | rule / deterministic / ok | read-only |
| 10 | 호가 모니터 / `QuoteMonitorAgent` | Market Data | bid/ask quality 판단 | quote | quote_quality -> risk feed | score | wide_spread, stale | rule / deterministic / ok | spread guard |
| 11 | 거래량 모니터 / `VolumeMonitorAgent` | Market Data | volume surge 판단 | volume, avg_volume | volume_signal -> scanner | score | low_volume | rule / deterministic / ok | read-only |
| 12 | 변동성 모니터 / `VolatilityMonitorAgent` | Market Data | intraday volatility 판단 | price_series | vol_signal -> analysis | score | volatility_low/high | rule / deterministic / ok | read-only |
| 13 | VWAP/세션 통계 / `VwapSessionStatsAgent` | Market Data | VWAP, opening range, session stats 계산 | ticks, session | session_stats -> Strategy | score | insufficient_ticks | rule / deterministic / ok | read-only |
| 14 | ORB 분석 / `OpeningRangeBreakoutAgent` | Strategy | opening range breakout 조건 평가 | StrategyInput, session_stats | analysis_signal -> synthesis | score/confidence | range_not_ready | rule / deterministic / ok | Strategy boundary |
| 15 | 추세 분석 / `TrendAnalysisAgent` | Strategy | trend direction 판단 | price_series | trend_signal -> synthesis | score | trend_unclear | rule / deterministic / ok | 주문 0 |
| 16 | 모멘텀 분석 / `MomentumAnalysisAgent` | Strategy | momentum continuation 판단 | returns, volume | momentum_signal -> synthesis | score | momentum_faded | rule / deterministic / ok | 주문 0 |
| 17 | 변동성 분석 / `VolatilityAnalysisAgent` | Strategy | strategy별 volatility regime 판단 | vol_signal | regime_signal -> selector | score | regime_blocked | rule / deterministic / ok | 주문 0 |
| 18 | 평균회귀 분석 / `MeanReversionAgent` | Strategy | 과열/과매도 후보 판단 | price_deviation, vwap | mean_reversion_signal -> selector | score | no_reversion_edge | rule / deterministic / ok | 주문 0 |
| 19 | 거시지표 분석 / `MacroIndicatorAgent` | Strategy | macro blocker/weight 제공 | macro_event | macro_signal -> synthesis | confidence | macro_event_risk | rule + LLM optional / deterministic / ok | LLM hard block 해제 불가 |
| 20 | 산업/섹터 분석 / `SectorAnalysisAgent` | Strategy | sector momentum/rotation 보조 | symbol_profile, sector_data | sector_signal -> synthesis | score | sector_weak | rule + LLM optional / deterministic / ok | read-only |
| 21 | 전략 선택 / `StrategySelectorAgent` | Strategy | 사용할 strategy 후보 선택 | signals, blockers | strategy_choice -> Strategy eval | confidence | no_strategy | rule / deterministic / ok | broker 0 |
| 22 | 신호 종합 / `SignalSynthesisAgent` | Strategy | 여러 signal을 하나의 candidate로 결합 | analysis_signals | strategy_candidate -> pre-risk | score/confidence | conflicting_signals | rule / deterministic / ok | hard blocker 보존 |
| 23 | 사전 리스크 / `PreRiskAgent` | Strategy | RiskEngine 입력 전 blocker feed | candidate, ops_state | pre_risk_context -> RiskEngine | confidence | notional_risk | rule / deterministic / ok | 최종 verdict 아님 |
| 24 | 실시간 리스크 / `RealtimeRiskAgent` | Strategy | quote 변화와 포지션 변화 감시 | quote_quality, position | realtime_risk_context -> RiskEngine | confidence | spread_widened | rule / deterministic / ok | 최종 verdict 아님 |
| 25 | 포지션 사이징 / `PositionSizingAgent` | Strategy | non-executable quantity proposal | risk_context, cash | size_proposal -> limit manager | score | insufficient_cash | rule / deterministic / ok | OMS 전 proposal |
| 26 | 한도 관리 / `LimitManagerAgent` | Strategy | daily/order/position limit 보조 | limits, size_proposal | limit_verdict -> price agents | confidence | max_orders | rule / deterministic / ok | RiskEngine 우회 0 |
| 27 | 진입 가격 산정 / `EntryPriceAgent` | Strategy | limit price proposal | quote, signal | entry_price -> intent emitter | confidence | price_out_of_band | rule / deterministic / ok | market order 금지 |
| 28 | 손절가 산정 / `StopPriceAgent` | Strategy | stop reference proposal | volatility, entry | stop_reference -> intent emitter | confidence | stop_too_close | rule / deterministic / ok | 자동 주문 아님 |
| 29 | 익절가 산정 / `TakeProfitAgent` | Strategy | target reference proposal | volatility, risk_reward | target_reference -> intent emitter | confidence | target_unavailable | rule / deterministic / ok | 자동 주문 아님 |
| 30 | 거래 에이전트 / `IntentEmitterAgent` | Strategy | `OrderIntent` 생성 후 OMS 위임 | strategy_choice, price, size | non-executable `OrderIntent` -> OMS boundary | confidence | blocker_present | rule / deterministic / ok | broker 호출 0 |
| 31 | 주문 검증 / `OrderValidationAgent` | Strategy | intent shape, enum, allowlist 검증 | OrderIntent | validation_context -> OMS/Risk | confidence | malformed_intent | rule / deterministic / malformed | executable 생성 0 |
| 32 | 주문 감시 / `OrderWatcherAgent` | Strategy | OMS/Paper order 상태 관찰 | orders, fills | order_state_event -> portfolio/risk | confidence | stuck_order | rule / deterministic / ok | cancel 자동화 0 |
| 33 | 부분 체결 처리 / `PartialFillAgent` | Strategy | partial fill 상태 해석 | fills, open_order | partial_fill_event -> portfolio | confidence | partial_fill | rule / deterministic / ok | read-only |
| 34 | 미체결 관리 / `OpenOrderManagerAgent` | Strategy | open order aging 감시 | open_orders | open_order_alert -> order watcher | confidence | aging_order | rule / deterministic / ok | paper query만 |
| 35 | 슬리피지 감시 / `SlippageMonitorAgent` | Strategy | expected vs fill price 비교 | fills, quote | slippage_event -> validation | score | high_slippage | rule / deterministic / ok | read-only |
| 36 | 가격 추적 / `PriceTrackingAgent` | Strategy | candidate 이후 가격 follow-up | candidate, quote | price_followup -> reports | score | invalid_followup | rule / deterministic / ok | read-only |
| 37 | 포트폴리오 모니터 / `PortfolioMonitorAgent` | Strategy | position/cash state 감시 | portfolio_snapshot | portfolio_state -> risk | confidence | concentration | rule / deterministic / ok | read-only |
| 38 | P&L 실시간 / `RealtimePnlAgent` | Strategy | paper P&L 변화 계산 | positions, fills | pnl_event -> risk/reports | confidence | pnl_drawdown | rule / deterministic / ok | read-only |
| 39 | 리스크 이벤트 모니터 / `RiskEventMonitorAgent` | Strategy | risk event escalation | risk_context, pnl | risk_event -> Ops | confidence | hard_block | rule / deterministic / ok | LLM 해제 불가 |
| 40 | 모듈 헬스 / `ModuleHealthAgent` | Orchestrator | module heartbeat와 degraded state 관찰 | heartbeats | health_event -> Ops/Orchestrator | confidence | module_down | rule / deterministic / timeout | fail-closed |

## 특별 규칙

`IntentEmitterAgent`는 Strategy Service 내부 역할이다. broker 호출, KIS 호출, credential 접근은 0이다. #23/#24 리스크 모듈은 `RiskEngine`의 보조 feed이며 최종 `RiskVerdict` 권한을 갖지 않는다.

## 반복 확인

Agent는 Broker가 아니다. OMS만 executable order를 만든다. Broker Gateway만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.
