# 09. Implementation Backlog

본 문서는 85 역할 모듈, 7 서비스, 5 cross-cutting 작업을 후속 Codex job으로 쪼개기 위한 backlog다. Size는 S/M/L만 사용하며 시간 추정은 포함하지 않는다.

## 안전 invariant

Agent는 Broker가 아니다. OMS만 executable `BrokerOrder`를 만든다. Broker Gateway Service만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.

## 97 backlog items

| Job ID | Phase / 카테고리 | 소속 서비스 | Size | Purpose | 수정 파일 | 신규 파일 | 의존 backlog | Acceptance | Test plan | Risk | Rollback |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `agent-rt-01` | 실시간 핵심 | Orchestrator | M | 오케스트레이터 lifecycle | service package | agent module | `cross-001` | broker import 0 | lifecycle tests | schedule misuse | disable module |
| `agent-rt-02` | 실시간 핵심 | Orchestrator | S | 세션 관리 | service package | agent module | `agent-rt-01` | closed session blocks intent | session tests | calendar gap | deterministic closed |
| `agent-rt-03` | 실시간 핵심 | Market Data | M | 데이터 수집 | market data package | agent module | `service-02` | read-only source | source tests | source failure | disable source |
| `agent-rt-04` | 실시간 핵심 | Market Data | S | 데이터 정규화 | market data package | agent module | `agent-rt-03` | schema validation | malformed tests | field drift | reject snapshot |
| `agent-rt-05` | 실시간 핵심 | Market Data | S | 데이터 캐시 | market data package | agent module | `agent-rt-04` | secret 0 | cache tests | stale cache | flush cache |
| `agent-rt-06` | 실시간 핵심 | Market Data | S | 데이터 무결성 | market data package | agent module | `agent-rt-05` | stale/spread guard | invariant tests | bad quote | reject quote |
| `agent-rt-07` | 실시간 핵심 | Market Data | M | 스캐너 | market data package | agent module | `agent-rt-06` | candidates only | scanner tests | noisy candidates | empty list |
| `agent-rt-08` | 실시간 핵심 | Market Data | S | universe 관리 | market data package | agent module | `agent-rt-07` | allowlist enforced | allowlist tests | broad universe | configured list |
| `agent-rt-09` | 실시간 핵심 | Market Data | S | metadata | market data package | agent module | `agent-rt-08` | missing metadata handled | metadata tests | stale metadata | fallback metadata |
| `agent-rt-10` | 실시간 핵심 | Market Data | S | 호가 모니터 | market data package | agent module | `agent-rt-06` | spread blocker | quote tests | bad spread | block |
| `agent-rt-11` | 실시간 핵심 | Market Data | S | 거래량 모니터 | market data package | agent module | `agent-rt-06` | volume score | volume tests | volume gap | low confidence |
| `agent-rt-12` | 실시간 핵심 | Market Data | S | 변동성 모니터 | market data package | agent module | `agent-rt-06` | volatility regime | vol tests | noisy vol | neutral regime |
| `agent-rt-13` | 실시간 핵심 | Market Data | M | VWAP/세션 통계 | market data package | agent module | `agent-rt-02` | stats typed | stat tests | insufficient ticks | no signal |
| `agent-rt-14` | 실시간 핵심 | Strategy | M | ORB 분석 | strategy package | agent module | `agent-rt-13` | StrategyResult-like output | strategy tests | false breakout | blocker |
| `agent-rt-15` | 실시간 핵심 | Strategy | S | 추세 분석 | strategy package | agent module | `agent-rt-06` | trend score | trend tests | overfit | neutral |
| `agent-rt-16` | 실시간 핵심 | Strategy | S | 모멘텀 분석 | strategy package | agent module | `agent-rt-11` | momentum score | momentum tests | late signal | blocker |
| `agent-rt-17` | 실시간 핵심 | Strategy | S | 변동성 분석 | strategy package | agent module | `agent-rt-12` | regime output | regime tests | regime flip | low confidence |
| `agent-rt-18` | 실시간 핵심 | Strategy | S | 평균회귀 분석 | strategy package | agent module | `agent-rt-13` | reversion score | reversion tests | wrong regime | blocker |
| `agent-rt-19` | 실시간 핵심 | Strategy | M | 거시지표 분석 | strategy package | agent module | `agent-news-06` | hard block preserved | macro tests | event ambiguity | blocker |
| `agent-rt-20` | 실시간 핵심 | Strategy | S | 산업/섹터 분석 | strategy package | agent module | `agent-rt-09` | sector signal | sector tests | missing sector | neutral |
| `agent-rt-21` | 실시간 핵심 | Strategy | M | 전략 선택 | strategy package | agent module | `agent-rt-22` | broker 0 | selector tests | bad selection | no strategy |
| `agent-rt-22` | 실시간 핵심 | Strategy | M | 신호 종합 | strategy package | agent module | analysis agents | blocker accumulation | synthesis tests | blocker loss | fail closed |
| `agent-rt-23` | 실시간 핵심 | Strategy | M | 사전 리스크 feed | strategy package | agent module | `agent-rt-22` | final verdict 아님 | risk feed tests | risk bypass | block |
| `agent-rt-24` | 실시간 핵심 | Strategy | M | 실시간 리스크 feed | strategy package | agent module | `agent-rt-10` | RiskEngine 우회 0 | realtime risk tests | stale feed | block |
| `agent-rt-25` | 실시간 핵심 | Strategy | M | 포지션 사이징 | strategy package | agent module | `agent-rt-23` | proposal only | sizing tests | oversize | zero size |
| `agent-rt-26` | 실시간 핵심 | Strategy | S | 한도 관리 | strategy package | agent module | `agent-rt-25` | limit proposal | limit tests | loose limit | reject |
| `agent-rt-27` | 실시간 핵심 | Strategy | S | 진입 가격 산정 | strategy package | agent module | `agent-rt-10` | limit price only | price tests | market order | reject |
| `agent-rt-28` | 실시간 핵심 | Strategy | S | 손절가 산정 | strategy package | agent module | `agent-rt-17` | reference only | stop tests | unsafe stop | no stop |
| `agent-rt-29` | 실시간 핵심 | Strategy | S | 익절가 산정 | strategy package | agent module | `agent-rt-17` | reference only | target tests | bad target | no target |
| `agent-rt-30` | 실시간 핵심 | Strategy | M | IntentEmitter | strategy package | agent module | `agent-rt-25`, `agent-rt-27` | `OrderIntent` only | intent tests | broker call | disable |
| `agent-rt-31` | 실시간 핵심 | Strategy | S | 주문 검증 | strategy package | agent module | `agent-rt-30` | malformed rejected | validation tests | bad enum | reject |
| `agent-rt-32` | 실시간 핵심 | Strategy | M | 주문 감시 | strategy package | agent module | OMS events | read-only | watcher tests | auto cancel | alert only |
| `agent-rt-33` | 실시간 핵심 | Strategy | S | 부분 체결 처리 | strategy package | agent module | fills source | read-only | fill tests | fill mismatch | alert |
| `agent-rt-34` | 실시간 핵심 | Strategy | S | 미체결 관리 | strategy package | agent module | order state | read-only | open order tests | live query | paper only |
| `agent-rt-35` | 실시간 핵심 | Strategy | S | 슬리피지 감시 | strategy package | agent module | fills | read-only | slippage tests | noisy alert | threshold |
| `agent-rt-36` | 실시간 핵심 | Strategy | S | 가격 추적 | strategy package | agent module | quote feed | read-only | tracking tests | stale quote | skip |
| `agent-rt-37` | 실시간 핵심 | Strategy | S | 포트폴리오 모니터 | strategy package | agent module | portfolio | read-only | portfolio tests | stale state | alert |
| `agent-rt-38` | 실시간 핵심 | Strategy | S | P&L 실시간 | strategy package | agent module | fills/positions | read-only | pnl tests | calc drift | no output |
| `agent-rt-39` | 실시간 핵심 | Strategy | S | 리스크 이벤트 모니터 | strategy package | agent module | risk events | hard block preserved | risk event tests | missed event | block |
| `agent-rt-40` | 실시간 핵심 | Orchestrator | S | 모듈 헬스 | orchestrator package | agent module | `service-01` | degraded state | health tests | false healthy | degraded |
| `agent-news-01` | 뉴스 이벤트 | News & Event | M | 뉴스 수집 | news package | agent module | `service-05` | read-only | collector tests | feed down | empty |
| `agent-news-02` | 뉴스 이벤트 | News & Event | S | 뉴스 분류 | news package | agent module | `agent-news-01` | schema validated | classifier tests | malformed | fallback |
| `agent-news-03` | 뉴스 이벤트 | News & Event | S | 뉴스 신뢰도 | news package | agent module | `agent-news-02` | credibility score | credibility tests | bad source | low score |
| `agent-news-04` | 뉴스 이벤트 | News & Event | S | 공시 모니터 | news package | agent module | `agent-news-01` | disclosure signal | disclosure tests | unsupported | no event |
| `agent-news-05` | 뉴스 이벤트 | News & Event | S | 실적 발표 모니터 | news package | agent module | `agent-news-01` | earnings signal | earnings tests | unconfirmed | blocker |
| `agent-news-06` | 뉴스 이벤트 | News & Event | S | 거시 이벤트 | news package | agent module | `agent-news-01` | macro signal | macro tests | ambiguous | blocker |
| `agent-news-07` | 뉴스 이벤트 | News & Event | S | 정정/구속력 이벤트 | news package | agent module | `agent-news-02` | binding blocker | binding tests | false event | low conf |
| `agent-news-08` | 뉴스 이벤트 | News & Event | S | 가격 충격 추정 | news package | agent module | `agent-news-03` | impact score | impact tests | overstate | neutral |
| `agent-news-09` | 뉴스 이벤트 | News & Event | S | 뉴스 종목 매핑 | news package | agent module | `agent-news-02` | symbol mapped | mapper tests | ambiguous | no symbol |
| `agent-news-10` | 뉴스 이벤트 | News & Event | S | 이벤트 알림 emit | news package | agent module | `agent-news-09` | alert only | alert tests | order action | alert only |
| `agent-val-01` | 검증 학습 | Validation & Learning | M | 검증 | validation package | agent module | `service-06` | read-only verdict | validation tests | bad data | inconclusive |
| `agent-val-02` | 검증 학습 | Validation & Learning | M | 백테스트 | validation package | agent module | `agent-val-01` | no broker call | backtest tests | data gap | skip |
| `agent-val-03` | 검증 학습 | Validation & Learning | S | 슬리피지 검증 | validation package | agent module | fills | report only | slippage tests | calc drift | flag |
| `agent-val-04` | 검증 학습 | Validation & Learning | S | 스프레드 검증 | validation package | agent module | quotes | report only | spread tests | bad quote | flag |
| `agent-val-05` | 검증 학습 | Validation & Learning | S | 체결 현실성 | validation package | agent module | fills | report only | realism tests | unrealistic fill | flag |
| `agent-val-06` | 검증 학습 | Validation & Learning | S | 매매일지 분석 | validation package | agent module | journal | scrubbed report | journal tests | secret leak | scrub |
| `agent-val-07` | 검증 학습 | Validation & Learning | S | 일일 리포트 | validation package | agent module | `agent-val-01` | no overclaim | report tests | overclaim | deterministic |
| `agent-val-08` | 검증 학습 | Validation & Learning | S | 주간 리포트 | validation package | agent module | daily reports | no overclaim | report tests | sparse data | inconclusive |
| `agent-val-09` | 검증 학습 | Validation & Learning | S | 전략 비교 | validation package | agent module | strategy runs | proposal only | comparison tests | bad compare | no winner |
| `agent-val-10` | 검증 학습 | Validation & Learning | S | 성과 분해 | validation package | agent module | fills/signals | attribution | attribution tests | overfit | inconclusive |
| `agent-val-11` | 검증 학습 | Validation & Learning | S | 실패 원인 분류 | validation package | agent module | errors | class output | failure tests | wrong class | unknown |
| `agent-val-12` | 검증 학습 | Validation & Learning | S | 회귀 비교 | validation package | agent module | baseline/current | diff output | regression tests | false diff | manual review |
| `agent-val-13` | 검증 학습 | Validation & Learning | S | 데이터 품질 | validation package | agent module | snapshots | quality report | quality tests | noisy | flag |
| `agent-val-14` | 검증 학습 | Validation & Learning | S | 신호 노이즈 | validation package | agent module | signals | noise report | noise tests | small sample | inconclusive |
| `agent-val-15` | 검증 학습 | Validation & Learning | M | LLM 결과 검증 | validation package | agent module | `cross-002` | malformed fallback | llm tests | bad parse | deterministic |
| `agent-val-16` | 검증 학습 | Validation & Learning | M | 학습 | validation package | agent module | reports | proposal only | learning tests | auto apply | disable apply |
| `agent-val-17` | 검증 학습 | Validation & Learning | S | 파라미터 튜닝 추천 | validation package | agent module | `agent-val-16` | manual approval | tuning tests | overfit | no change |
| `agent-val-18` | 검증 학습 | Validation & Learning | S | 결정 트리 추출 | validation package | agent module | signals | explanation | tree tests | unstable | no tree |
| `agent-val-19` | 검증 학습 | Validation & Learning | S | 가설 검증 | validation package | agent module | hypothesis | result | hypothesis tests | weak sample | inconclusive |
| `agent-val-20` | 검증 학습 | Validation & Learning | S | 결과 시각화 | validation package | agent module | reports | chart spec | visualization tests | bad data | no chart |
| `agent-ops-01` | 운영 보안 | Ops & Security | M | 모니터링 | ops package | agent module | `service-07` | read-only status | ops tests | false ok | degraded |
| `agent-ops-02` | 운영 보안 | Ops & Security | M | 비상정지 | ops package | agent module | `cross-004` | kill switch set only | kill tests | accidental set | manual reset |
| `agent-ops-03` | 운영 보안 | Ops & Security | S | 보안 grep | ops package | agent module | `agent-ops-01` | secret leak 0 | grep tests | false negative | block |
| `agent-ops-04` | 운영 보안 | Ops & Security | M | 시크릿 관리 | ops package | agent module | `service-07` | Broker Gateway only | secret tests | overgrant | revoke |
| `agent-ops-05` | 운영 보안 | Ops & Security | S | 실계좌 잠금 | ops package | agent module | `agent-ops-01` | live locked | lock tests | unlock path | force lock |
| `agent-ops-06` | 운영 보안 | Ops & Security | S | 규정 체크 | ops package | agent module | audit events | alerts | compliance tests | policy drift | manual review |
| `agent-ops-07` | 운영 보안 | Ops & Security | S | 세금 기록 | ops package | agent module | fills | records | tax record tests | missing fills | incomplete |
| `agent-ops-08` | 운영 보안 | Ops & Security | S | 계좌 보호 | ops package | agent module | account status | masked only | account tests | exposure | hide |
| `agent-ops-09` | 운영 보안 | Ops & Security | S | 주문 감사 | ops package | agent module | order lifecycle | audit event | audit tests | OMS bypass | block |
| `agent-ops-10` | 운영 보안 | Ops & Security | M | 장애 복구 | ops package | agent module | incidents | recovery proposal | recovery tests | unsafe restart | no action |
| `agent-ops-11` | 운영 보안 | Ops & Security | M | 실전 전환 승인 | ops package | agent module | preflight | locked state | approval tests | live unlock | locked |
| `agent-ops-12` | 운영 보안 | Ops & Security | S | 로그 회전/보관 | ops package | agent module | logs | retention report | log tests | leak | scrub |
| `agent-ops-13` | 운영 보안 | Ops & Security | S | 알림 라우팅 | ops package | agent module | alerts | routed alerts | routing tests | missed alert | local log |
| `agent-ops-14` | 운영 보안 | Ops & Security | S | 운영자 명령 처리 | ops package | agent module | commands | command result | command tests | unsafe command | deny |
| `agent-ops-15` | 운영 보안 | Ops & Security | S | 운영자 권한 관리 | ops package | agent module | identity | access verdict | access tests | privilege creep | deny |
| `service-01` | 서비스 | Orchestrator | M | 서비스 골격/health/RPC | service package | service module | `cross-003` | loopback only | service tests | exposed RPC | disable |
| `service-02` | 서비스 | Market Data | M | market data service 골격 | service package | service module | `service-01` | read-only | service tests | source leak | disable |
| `service-03` | 서비스 | Strategy | L | strategy/risk/OMS service 골격 | service package | service module | `service-01` | OMS boundary | integration tests | OMS bypass | disable write |
| `service-04` | 서비스 | Broker Gateway | L | 유일 broker/KIS gateway | service package | service module | `service-03` | credential isolated | gateway tests | secret leak | disable gateway |
| `service-05` | 서비스 | News & Event | M | news event service 골격 | service package | service module | `service-01` | read-only | service tests | noisy events | disable |
| `service-06` | 서비스 | Validation & Learning | M | validation service 골격 | service package | service module | `service-01` | read-only | service tests | overclaim | deterministic |
| `service-07` | 서비스 | Ops & Security | L | ops/security service 골격 | service package | service module | `service-01` | lock preserved | ops tests | overpermission | deny |
| `cross-001` | cross-cutting | All | M | `AgentBase` abstract + contracts | domain/agent package | base files | none | typed I/O | contract tests | loose schema | remove package |
| `cross-002` | cross-cutting | All | M | `LLMProvider` + deterministic | provider package | provider files | `cross-001` | fallback required | provider tests | secret handling | deterministic only |
| `cross-003` | cross-cutting | All | M | 서비스 RPC base + auth | service package | rpc files | `cross-001` | loopback only | rpc tests | public exposure | disable RPC |
| `cross-004` | cross-cutting | All | M | kill switch broadcast | orchestrator/ops | broadcast files | `cross-003` | all services stop action | kill tests | missed service | global lock |
| `cross-005` | cross-cutting | All | M | agent/service 회귀 인프라 | tests only | test helpers | `cross-001` | no broker import regression | test suite | weak coverage | remove helper |

## Prioritization logic

P0는 Top 15 + 5 meta-agent다. 먼저 safety rail과 read-only 관찰을 만들고, 그 다음 Strategy Service 내부 proposal을 만든다. `IntentEmitterAgent`는 P0지만 가장 뒤에 붙인다. Broker Gateway implementation은 서비스 skeleton 단계에서도 credential 격리와 disabled-by-default를 acceptance로 둔다.

## 반복 확인

Backlog implementation은 Agent ≠ Broker, OMS only executable, Broker Gateway only KIS-credentialed, LLM hard risk block 해제 불가, live default lock을 공통 acceptance로 가진다.
