# 01. 7 실행 서비스

본 문서는 85개 역할 모듈을 실제 운영 프로세스인 7개 서비스로 묶는 설계다. 서비스는 배포와 장애 격리 단위이고, 역할 모듈은 책임 단위다. 안전 원칙은 `00_principles_and_boundaries.md`를 따른다.

## 서비스 책임 표

| # | Service | 책임 | KIS 자격증명 | broker 호출 | 통신 패턴 |
| --- | --- | --- | --- | --- | --- |
| 1 | `OrchestratorService` | lifecycle, schedule, kill switch broadcast, operator command | no | no | loopback / UNIX socket |
| 2 | `MarketDataService` | quote, snapshot, scanner data 수집/정규화/캐시 | no | no | read-only feed |
| 3 | `StrategyService` | analysis, strategy, risk feed, OMS boundary | no | no | internal RPC to Broker Gateway |
| 4 | `BrokerGatewayService` | OMS `BrokerOrder` 수신, BrokerAdapter 호출, KIS 격리 | yes | yes | loopback private RPC |
| 5 | `NewsEventService` | news/event 수집, 분류, 신뢰도, event signal | no | no | read-only event push |
| 6 | `ValidationLearningService` | backtest, report, validation, proposal | no | no | read-only analytics |
| 7 | `OpsSecurityService` | monitoring, kill switch, secret mediation, audit, lock | no | no | alert / guard RPC |

## 아키텍처

```text
             [Operator UI / FastAPI read-only console]
                         |
                  OrchestratorService
        kill switch / lifecycle / schedule broadcast
       /        |           |            |          \
MarketData  NewsEvent  StrategyService  Validation  OpsSecurity
 Service     Service       |              Service      Service
    |           |          RiskEngine/OMS     |           |
    +---- read-only -----> Agent/Strategy <---+---- audit |
                           |
                           | BrokerOrder only
                           v
                    BrokerGatewayService
                           |
                   PaperBroker / KisBroker
                           |
                       [KIS external]
```

KIS 외부 박스로 향하는 화살표는 Broker Gateway Service에만 있다. 다른 서비스는 KIS credential, raw token, account number를 보유하지 않는다.

## 통신 프로토콜

- 서비스 간 통신은 loopback HTTP 또는 UNIX socket만 권장한다.
- 내부 토큰은 Ops & Security Service가 관리하되 raw secret은 문서와 로그에 남기지 않는다.
- 외부 인터넷에 inter-service RPC를 노출하지 않는다.
- Strategy Service -> Broker Gateway Service write channel은 OMS가 만든 `BrokerOrder` payload만 허용한다.
- Orchestrator -> 6 서비스 kill switch broadcast는 모든 write action보다 우선한다.

## fail-closed 장애 시나리오

| 장애 | 기대 동작 |
| --- | --- |
| Orchestrator down | 새 schedule 중단, 서비스는 local kill switch state 유지 |
| Market Data down | Strategy 신규 평가 중단, stale quote blocker |
| Strategy down | 신규 `OrderIntent` 0, Broker Gateway 수신 없음 |
| Broker Gateway down | broker call 0, OMS order pending/rejected |
| News Event down | 뉴스 보강 없이 deterministic fallback |
| Validation down | report 지연, trading 권한 영향 0 |
| Ops Security down | secret issuance 중단, live lock 유지 |

## 85 모듈 → 7 서비스 매핑

| # | 한국어 명칭 | English alias | 카테고리 | 소속 서비스 |
| --- | --- | --- | --- | --- |
| 1 | 오케스트레이터 | `OrchestratorAgent` | 실시간 핵심 | Orchestrator Service |
| 2 | 세션 관리 | `SessionManagerAgent` | 실시간 핵심 | Orchestrator Service |
| 3 | 데이터 수집 | `DataCollectionAgent` | 실시간 핵심 | Market Data Service |
| 4 | 데이터 정규화 | `DataNormalizationAgent` | 실시간 핵심 | Market Data Service |
| 5 | 데이터 캐시 | `DataCacheAgent` | 실시간 핵심 | Market Data Service |
| 6 | 데이터 무결성 | `DataIntegrityAgent` | 실시간 핵심 | Market Data Service |
| 7 | 스캐너 | `ScannerAgent` | 실시간 핵심 | Market Data Service |
| 8 | 종목 universe | `UniverseAgent` | 실시간 핵심 | Market Data Service |
| 9 | 종목 metadata | `SymbolMetadataAgent` | 실시간 핵심 | Market Data Service |
| 10 | 호가 모니터 | `QuoteMonitorAgent` | 실시간 핵심 | Market Data Service |
| 11 | 거래량 모니터 | `VolumeMonitorAgent` | 실시간 핵심 | Market Data Service |
| 12 | 변동성 모니터 | `VolatilityMonitorAgent` | 실시간 핵심 | Market Data Service |
| 13 | VWAP/세션 통계 | `VwapSessionStatsAgent` | 실시간 핵심 | Market Data Service |
| 14 | ORB 분석 | `OpeningRangeBreakoutAgent` | 실시간 핵심 | Strategy Service |
| 15 | 추세 분석 | `TrendAnalysisAgent` | 실시간 핵심 | Strategy Service |
| 16 | 모멘텀 분석 | `MomentumAnalysisAgent` | 실시간 핵심 | Strategy Service |
| 17 | 변동성 분석 | `VolatilityAnalysisAgent` | 실시간 핵심 | Strategy Service |
| 18 | 평균회귀 분석 | `MeanReversionAgent` | 실시간 핵심 | Strategy Service |
| 19 | 거시지표 분석 | `MacroIndicatorAgent` | 실시간 핵심 | Strategy Service |
| 20 | 산업/섹터 분석 | `SectorAnalysisAgent` | 실시간 핵심 | Strategy Service |
| 21 | 전략 선택 | `StrategySelectorAgent` | 실시간 핵심 | Strategy Service |
| 22 | 신호 종합 | `SignalSynthesisAgent` | 실시간 핵심 | Strategy Service |
| 23 | 사전 리스크 | `PreRiskAgent` | 실시간 핵심 | Strategy Service |
| 24 | 실시간 리스크 | `RealtimeRiskAgent` | 실시간 핵심 | Strategy Service |
| 25 | 포지션 사이징 | `PositionSizingAgent` | 실시간 핵심 | Strategy Service |
| 26 | 한도 관리 | `LimitManagerAgent` | 실시간 핵심 | Strategy Service |
| 27 | 진입 가격 산정 | `EntryPriceAgent` | 실시간 핵심 | Strategy Service |
| 28 | 손절가 산정 | `StopPriceAgent` | 실시간 핵심 | Strategy Service |
| 29 | 익절가 산정 | `TakeProfitAgent` | 실시간 핵심 | Strategy Service |
| 30 | 거래 에이전트 | `IntentEmitterAgent` | 실시간 핵심 | Strategy Service |
| 31 | 주문 검증 | `OrderValidationAgent` | 실시간 핵심 | Strategy Service |
| 32 | 주문 감시 | `OrderWatcherAgent` | 실시간 핵심 | Strategy Service |
| 33 | 부분 체결 처리 | `PartialFillAgent` | 실시간 핵심 | Strategy Service |
| 34 | 미체결 관리 | `OpenOrderManagerAgent` | 실시간 핵심 | Strategy Service |
| 35 | 슬리피지 감시 | `SlippageMonitorAgent` | 실시간 핵심 | Strategy Service |
| 36 | 가격 추적 | `PriceTrackingAgent` | 실시간 핵심 | Strategy Service |
| 37 | 포트폴리오 모니터 | `PortfolioMonitorAgent` | 실시간 핵심 | Strategy Service |
| 38 | P&L 실시간 | `RealtimePnlAgent` | 실시간 핵심 | Strategy Service |
| 39 | 리스크 이벤트 모니터 | `RiskEventMonitorAgent` | 실시간 핵심 | Strategy Service |
| 40 | 모듈 헬스 | `ModuleHealthAgent` | 실시간 핵심 | Orchestrator Service |
| 41 | 뉴스 수집 | `NewsCollectorAgent` | 뉴스 이벤트 | News & Event Service |
| 42 | 뉴스 분류 | `NewsClassifierAgent` | 뉴스 이벤트 | News & Event Service |
| 43 | 뉴스 신뢰도 평가 | `NewsCredibilityAgent` | 뉴스 이벤트 | News & Event Service |
| 44 | 공시 모니터 | `DisclosureMonitorAgent` | 뉴스 이벤트 | News & Event Service |
| 45 | 실적 발표 모니터 | `EarningsMonitorAgent` | 뉴스 이벤트 | News & Event Service |
| 46 | 거시 이벤트 | `MacroEventAgent` | 뉴스 이벤트 | News & Event Service |
| 47 | 정정/구속력 이벤트 | `BindingEventAgent` | 뉴스 이벤트 | News & Event Service |
| 48 | 가격 충격 추정 | `EventImpactAgent` | 뉴스 이벤트 | News & Event Service |
| 49 | 뉴스 종목 매핑 | `NewsSymbolMapperAgent` | 뉴스 이벤트 | News & Event Service |
| 50 | 이벤트 알림 emit | `EventAlertEmitterAgent` | 뉴스 이벤트 | News & Event Service |
| 51 | 검증 | `ValidationAgent` | 검증 학습 | Validation & Learning Service |
| 52 | 백테스트 | `BacktestAgent` | 검증 학습 | Validation & Learning Service |
| 53 | 슬리피지 검증 | `SlippageValidationAgent` | 검증 학습 | Validation & Learning Service |
| 54 | 스프레드 검증 | `SpreadValidationAgent` | 검증 학습 | Validation & Learning Service |
| 55 | 체결 현실성 검증 | `FillRealismValidationAgent` | 검증 학습 | Validation & Learning Service |
| 56 | 매매일지 분석 | `JournalAnalysisAgent` | 검증 학습 | Validation & Learning Service |
| 57 | 일일 리포트 | `DailyReportAgent` | 검증 학습 | Validation & Learning Service |
| 58 | 주간 리포트 | `WeeklyReportAgent` | 검증 학습 | Validation & Learning Service |
| 59 | 전략 비교 | `StrategyComparisonAgent` | 검증 학습 | Validation & Learning Service |
| 60 | 전략 성과 분해 | `PerformanceAttributionAgent` | 검증 학습 | Validation & Learning Service |
| 61 | 실패 원인 분류 | `FailureClassifierAgent` | 검증 학습 | Validation & Learning Service |
| 62 | 회귀 비교 | `RegressionComparisonAgent` | 검증 학습 | Validation & Learning Service |
| 63 | 데이터 품질 검증 | `DataQualityValidationAgent` | 검증 학습 | Validation & Learning Service |
| 64 | 신호 노이즈 분석 | `SignalNoiseAgent` | 검증 학습 | Validation & Learning Service |
| 65 | LLM 결과 검증 보조 | `LlmOutputValidationAgent` | 검증 학습 | Validation & Learning Service |
| 66 | 학습 | `LearningAgent` | 검증 학습 | Validation & Learning Service |
| 67 | 파라미터 튜닝 추천 | `ParameterTuningAgent` | 검증 학습 | Validation & Learning Service |
| 68 | 결정 트리 추출 | `DecisionTreeExtractionAgent` | 검증 학습 | Validation & Learning Service |
| 69 | 가설 검증 | `HypothesisValidationAgent` | 검증 학습 | Validation & Learning Service |
| 70 | 결과 시각화 | `ResultVisualizationAgent` | 검증 학습 | Validation & Learning Service |
| 71 | 모니터링 | `MonitoringAgent` | 운영 보안 | Ops & Security Service |
| 72 | 비상정지 | `EmergencyStopAgent` | 운영 보안 | Ops & Security Service |
| 73 | 보안 grep | `SecretLeakScanAgent` | 운영 보안 | Ops & Security Service |
| 74 | 시크릿 관리 | `SecretManagementAgent` | 운영 보안 | Ops & Security Service |
| 75 | 실계좌 잠금 | `LiveAccountLockAgent` | 운영 보안 | Ops & Security Service |
| 76 | 규정 체크 | `ComplianceCheckAgent` | 운영 보안 | Ops & Security Service |
| 77 | 세금 기록 | `TaxRecordAgent` | 운영 보안 | Ops & Security Service |
| 78 | 계좌 보호 | `AccountProtectionAgent` | 운영 보안 | Ops & Security Service |
| 79 | 주문 감사 | `OrderAuditAgent` | 운영 보안 | Ops & Security Service |
| 80 | 장애 복구 | `RecoveryAgent` | 운영 보안 | Ops & Security Service |
| 81 | 실전 전환 승인 | `LiveApprovalAgent` | 운영 보안 | Ops & Security Service |
| 82 | 로그 회전/보관 | `LogRetentionAgent` | 운영 보안 | Ops & Security Service |
| 83 | 알림 라우팅 | `AlertRoutingAgent` | 운영 보안 | Ops & Security Service |
| 84 | 운영자 명령 처리 | `OperatorCommandAgent` | 운영 보안 | Ops & Security Service |
| 85 | 운영자 권한 관리 | `OperatorAccessAgent` | 운영 보안 | Ops & Security Service |

## 배포 topology 메모

Docker Compose, systemd, supervisor 중 무엇을 사용할지는 후속 implementation job에서 결정한다. 본 문서는 process boundary만 정의한다.

## 반복 확인

Agent는 Broker가 아니다. OMS만 executable order를 만든다. Broker Gateway만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.
