# 작업 ID
agent-platform-spec-001

# 작업명
Agent 플랫폼 최종 설계 — 85 역할 모듈 + 7 실행 서비스 + Top 15+5 focus set 설계 문서 생성을 위한 plan + Codex task 작성

`final-platform-plan/04_agent_strategy_pipeline.md` 가 7 종 agent (Market / Company / Financial / Industry / News / Risk / InvestmentRecommendation) 만 정의했다. 본 작업은 그 위에 **최종 설계 — 85 역할 모듈 / 7 실행 서비스 / Top 15+5 focus set** 을 한국어 design 문서로 정리한다.

본 작업은 docs-only. **application code / tests / `.env` / KIS catalog / runtime 일체 수정 0.**

## 최종 설계 — 85 역할 모듈

| 카테고리 | 개수 |
| --- | --- |
| 실시간 핵심 에이전트 | 40 |
| 보조 뉴스/이벤트 에이전트 | 10 |
| 검증/학습 에이전트 | 20 |
| 운영/보안 에이전트 | 15 |
| **총 역할 모듈** | **85** |

## 실제 실행 서비스 — 7개

85 역할 모듈은 **7 실행 서비스** 안에 묶여 배포된다. 역할 모듈은 책임 단위 (논리), 서비스는 프로세스 단위 (배포). 한 서비스 안에 여러 역할 모듈이 cooperative 하게 동작.

권고 7 서비스 (plan §3.2 에서 상세화, Codex 가 `01_seven_services.md` 에서 design 완성):

1. **Orchestrator Service** — 모든 서비스/모듈의 lifecycle, 스케줄링, kill switch broadcast, 운영자 명령 수신.
2. **Market Data Service** — KIS / 외부 시세 read-only 수집, 정규화, 캐시. 주문 0.
3. **Strategy Service** — 실시간 핵심 40 + Top 15 critical 의 다수. `Strategy → RiskEngine → OMS` 격리 boundary 보존. broker 호출은 Broker Gateway Service 만.
4. **Broker Gateway Service** — 유일하게 KIS 자격증명을 보유. OMS 의 executable `BrokerOrder` 만 받아 KIS API 호출 (`KIS_ORDER_DRY_RUN` 게이트 + paper TR ID 만). 모든 외부 모듈은 RPC 로만 접근.
5. **News & Event Service** — 보조 뉴스/이벤트 10 모듈. 데이터 수집 / 분류 / 신뢰도 평가 / Strategy Service 에 알림 emit. 주문 0.
6. **Validation & Learning Service** — 검증/학습 20 모듈. 백테스트, 슬리피지/스프레드 검증, 일일 리포트, 전략 비교, 학습. 모두 read-only. 주문 0.
7. **Ops & Security Service** — 운영/보안 15 모듈. 모니터링, 비상정지, 보안, 시크릿, 실계좌 잠금, 주문 감사, 장애 복구, 실전 전환 승인 (locked).

> Codex 가 `01_seven_services.md` 에서 이 7 서비스의 process boundary, 통신 프로토콜 (loopback HTTP / IPC), kill switch propagation, 서비스 간 인증, 데이터 흐름을 design.

## 실제 시작점 — Top 15 + 5 Claude/Codex Meta

85 모듈 중 P0 우선 land 시작점.

### Top 15 Critical Agents (85 중 P0)

1. 오케스트레이터 에이전트
2. 세션 관리 에이전트
3. 데이터 에이전트
4. 스캐너 에이전트
5. 뉴스/이벤트 에이전트
6. 분석 에이전트
7. 전략 선택 에이전트
8. 리스크 에이전트
9. 포지션 사이징 에이전트
10. 거래 에이전트
11. 주문 감시 에이전트
12. 비상정지 에이전트
13. 거래 로그 에이전트
14. 검증 에이전트
15. 학습/리포트 에이전트

### Claude / Codex Meta-Agent (5)

1. Claude 설계 에이전트
2. Claude 리뷰 에이전트
3. Codex 구현 에이전트
4. Codex 테스트 에이전트
5. LLM 결과 검증 에이전트

## 핵심 안전 invariant (모든 doc 반복 명시)

- **Agent 는 broker 를 직접 호출하지 않는다.** `app.broker.*` import 0. 어떤 역할 모듈도 broker 호출 0.
- **OMS 만 executable `BrokerOrder` 를 생성한다.** Agent / Strategy 는 non-executable `OrderIntent` 까지만.
- **Broker Gateway Service 만 KIS API 를 호출한다.** 다른 6 서비스는 KIS 자격증명 0. Broker Gateway 는 OMS 의 검증된 `BrokerOrder` 만 수신.
- 주문 경계: `Strategy(Strategy Service) → RiskEngine(Strategy Service) → OMS(Strategy Service) → BrokerAdapter(Broker Gateway Service)`. Agent 는 Strategy 의 input source 또는 read-only 옵저버.
- "거래 에이전트" (Top 15 #10) 도 broker 호출 0. `OrderIntent` 생성 → OMS 위임만. 역할 모듈 분류상 Strategy Service 안의 IntentEmitter role.
- "비상정지 에이전트" 는 `kill_switch_engaged=True` 만 set (read-only 외 유일 mutation). Orchestrator Service 가 broadcast.
- LLM 은 optional. default 는 rule-based / deterministic. LLM 실패 시 deterministic fallback.
- LLM 단독으로 hard risk block 해제 불가.
- 실 KIS endpoint / TR ID / payload / response field 추측 0. `Confirmed: yes` 행만 인용.
- live trading 활성화 코드 추가 0. "실전 전환 승인 에이전트" 도 locked / future-approval-gated.
- 7 서비스 간 통신은 loopback / 내부 망 한정. 외부 공개 endpoint 0 (API/UI 는 별 layer 의 read-only `/ops/*` / `/paper/*` 기존 endpoint 만).

## 산출물

### 본 turn 의 Claude 가 작성

- `request.ko.md` (이 파일)
- `plan.md`
- `codex-task.md`

### Codex 가 다음 turn 에 생성 (한국어 design 11 문서 + patch.md)

- `00_principles_and_boundaries.md` — 안전 원칙, Agent ≠ Broker, 85 모듈 / 7 서비스 경계.
- `01_seven_services.md` — 7 실행 서비스 design + 통신 프로토콜 + 데이터 흐름 + 85 모듈 → 7 서비스 매핑 표.
- `02_realtime_core_40_agents.md` — 40 실시간 핵심 에이전트.
- `03_news_event_10_agents.md` — 10 뉴스/이벤트 에이전트.
- `04_validation_learning_20_agents.md` — 20 검증/학습 에이전트.
- `05_ops_security_15_agents.md` — 15 운영/보안 에이전트.
- `06_top15_focus_set.md` — Top 15 critical + 5 meta-agent (실제 시작점, 의존 그래프, 진입 순서).
- `07_llm_provider_design.md` — LLM provider abstraction + deterministic fallback.
- `08_data_contracts.md` — typed contracts (AgentInput / AgentOutput / AgentTrace / KillSwitchCommand / AlertEvent / ServiceMessage).
- `09_implementation_backlog.md` — 85 모듈 + 7 서비스 + 5 cross-cutting backlog item (S/M/L).
- `10_acceptance_criteria.md` — design + 후속 implementation job 공통 acceptance template.

## 절대 하지 말 것

- 코드 / 테스트 / `.env` / catalog 본문 수정.
- 새 endpoint / 새 KIS TR_ID / payload / header / response field 추측.
- live trading 활성화 계획 / live arm 실행.
- 수익 보장 / 거짓 성과 / 과장된 승률 표현.
- 시간 추정 (sprint / Q / 주 / 일).
- 자동 git commit / push / merge / deploy.
- 본 turn / 다음 Codex turn 에서 application code 작성.
- `final-platform-plan/` 또는 다른 job 디렉터리의 기존 파일 수정.
- 외부 web fetch.
- 7 서비스를 외부에 공개하는 endpoint 추가 권고.
- Broker Gateway Service 외 다른 서비스가 KIS 자격증명을 보유한다는 design.
