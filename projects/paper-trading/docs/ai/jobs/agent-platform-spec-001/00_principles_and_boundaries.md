# 00. 원칙과 경계

본 문서는 85개 역할 모듈과 7개 실행 서비스를 설계할 때 절대 깨지면 안 되는 운영 경계를 정의한다. 기준은 `final-platform-plan/00_current_state.md`, `04_agent_strategy_pipeline.md`, `07_risk_safety_observability.md`이며, 본 설계는 live trading을 켜거나 KIS payload를 새로 만들지 않는다.

## 안전 invariant

1. **Agent ≠ Broker.** `app/agents/*` 역할 모듈은 `app.broker.*`를 import하지 않고 broker 호출을 하지 않는다.
2. **OMS only executable.** Agent와 Strategy는 `OrderIntent`까지만 만들 수 있고, executable `BrokerOrder`는 OMS만 생성한다.
3. **Broker Gateway Service only KIS-credentialed.** KIS 자격증명과 KIS API 호출 권한은 Broker Gateway Service에만 있다.
4. **LLM 단독 hard risk block 해제 불가.** LLM output은 Pydantic validation과 deterministic fallback을 통과해야 하며 `RiskEngine` hard block을 해제하지 못한다.
5. **live default lock.** 어떤 모듈도 `live_trading_enabled=True`를 set하거나 `KIS_ORDER_DRY_RUN=false`를 toggle하지 않는다. 실전 전환 승인 에이전트도 locked / future-approval-gated다.

## 서비스와 주문 경계

```text
Operator / Dashboard
  -> OrchestratorService
      -> MarketDataService        -> Quote / Snapshot
      -> NewsEventService         -> EventSignal
      -> ValidationLearningService -> Report / Validation
      -> OpsSecurityService       -> Guard / Alert / KillSwitch
      -> StrategyService
            AgentOutput / StrategyResult
            -> RiskEngine
            -> OMS
            -> BrokerOrder
      -> BrokerGatewayService
            -> BrokerAdapter
            -> PaperBroker 또는 KisBroker
            -> KIS API (Broker Gateway 만)
```

`StrategyService`는 전략 평가, 보조 agent, `RiskEngine`, OMS를 품는다. 그러나 KIS 자격증명은 없다. `BrokerGatewayService`는 OMS가 만든 `BrokerOrder`만 받으며, `OrderIntent`나 agent recommendation을 직접 받지 않는다.

## 도메인 관계

```text
AgentInput
  -> AgentOutput(score, confidence, reasons, blockers)
  -> StrategyInput / StrategyCandidate
  -> StrategyResult(non_executable_order_intent)
  -> RiskEngine.evaluate
  -> OMS.place
  -> BrokerOrder
  -> BrokerGatewayService
  -> BrokerAdapter(PaperBroker | KisBroker)
```

Agent는 입력 보강과 해석을 담당한다. Strategy는 `StrategyResult`를 만든다. `RiskEngine`은 hard guard를 적용한다. OMS만 executable order를 만든다. Broker adapter는 Broker Gateway 내부에만 배치한다.

## Agent input source / output sink

| Agent group | Input source | Output sink | Mutation |
| --- | --- | --- | --- |
| 실시간 핵심 | Market Data, News, Ops state, Paper state | Strategy Service, Validation Service | 주문 mutation 0 |
| 뉴스 이벤트 | read-only news/event feed | Strategy Service event signal | 주문 mutation 0 |
| 검증 학습 | paper run, journal, fills, reports | Reports, parameter proposal | 자동 적용 0 |
| 운영 보안 | config state, logs, safety grep, auth status | Alert, lock state, operator view | 비상정지 agent만 kill switch set |

## Broker Gateway 격리

Broker Gateway Service는 7개 서비스 중 유일하게 KIS 자격증명을 받을 수 있다. 다른 서비스는 masked status나 capability flag만 본다. KIS catalog를 인용할 때는 `docs/kis/MISSING_OFFICIAL_VALUES.md`의 `Confirmed: yes` row만 § 번호로 인용한다. 미확인 값은 `> **TODO**: KIS 공식 catalog 확인 필요`로 남긴다.

## 거래 에이전트와 비상정지 에이전트

`IntentEmitterAgent`는 이름 때문에 거래처럼 보이지만 broker 호출을 하지 않는다. 이 모듈은 `OrderIntent`를 만들고 Strategy Service 내부 OMS 경계로 위임한다. 반대로 비상정지 에이전트는 유일한 mutation을 가진다. mutation은 kill switch set뿐이며, Orchestrator Service가 6개 서비스에 broadcast한다.

## 위반 시 review BLOCK

다음 설계나 구현 제안은 review BLOCK이다.

| 위반 | BLOCK 이유 |
| --- | --- |
| Agent가 broker adapter 호출 | Agent ≠ Broker 위반 |
| OMS 외 모듈이 `BrokerOrder` 생성 | executable order 경계 위반 |
| Broker Gateway 외 서비스가 KIS secret 보유 | credential 격리 위반 |
| LLM output으로 hard risk block 해제 | deterministic risk guard 위반 |
| live lock 해제 또는 dry-run 해제 제안 | live default lock 위반 |

## 문서 간 참조

- `final-platform-plan/00_current_state.md`: 현재 runtime / broker / OMS / risk 기준선.
- `final-platform-plan/04_agent_strategy_pipeline.md`: 기존 7 agent 개념.
- `final-platform-plan/05_live_validation_console.md`: locked live console 원칙.
- `final-platform-plan/10_acceptance_criteria.md`: future job 공통 acceptance.

## 반복 확인

Agent는 Broker가 아니다. OMS만 executable order를 만든다. Broker Gateway만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태이며 본 설계는 이를 변경하지 않는다.
