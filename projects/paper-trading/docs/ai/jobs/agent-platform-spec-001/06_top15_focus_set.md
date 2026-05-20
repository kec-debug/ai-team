# 06. Top 15 + 5 Focus Set

본 문서는 85개 역할 모듈 중 실제 시작점인 Top 15 critical agents와 5개 Claude/Codex meta-agent를 정의한다. 목적은 위험이 낮은 순서로 안전망, 관찰, 분석, 검증을 먼저 land하는 것이다.

## 안전 invariant

Agent는 Broker가 아니다. OMS만 executable `BrokerOrder`를 만든다. Broker Gateway Service만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.

## 진입 순서 DAG

```text
Orchestrator -> Session Manager
  ├─ E-Stop Agent
  ├─ Data Agent
  │    └─ Scanner -> News/Event -> Analyst -> Strategy Selector
  │         └─ Risk -> Position Sizer -> Trader(IntentEmitter) -> Order Watcher
  ├─ Journal Agent
  ├─ Validation Agent
  └─ Learning/Report Agent

LLM Output Validator -> Codex Test Agent -> Claude Review Agent
  -> Claude Design Agent -> Codex Implementation Agent
```

## Top 15 critical

| # | 한국어 명칭 | English alias | 서비스 | 카테고리 참조 | 우선순위 | 의존 모듈 | Backlog ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 오케스트레이터 | `OrchestratorAgent` | Orchestrator | `02` #1 | P0 | 없음 | `agent-rt-01` |
| 2 | 세션 관리 | `SessionManagerAgent` | Orchestrator | `02` #2 | P0 | `agent-rt-01` | `agent-rt-02` |
| 3 | 데이터 에이전트 | `DataCollectionAgent` | Market Data | `02` #3 | P0 | `agent-rt-01` | `agent-rt-03` |
| 4 | 스캐너 | `ScannerAgent` | Market Data | `02` #7 | P0 | `agent-rt-03`, `agent-rt-06` | `agent-rt-07` |
| 5 | 뉴스/이벤트 | `EventAlertEmitterAgent` | News & Event | `03` #50 | P0 | `agent-news-01`~`agent-news-09` | `agent-news-10` |
| 6 | 분석 에이전트 | `SignalSynthesisAgent` | Strategy | `02` #22 | P0 | scanner, news | `agent-rt-22` |
| 7 | 전략 선택 | `StrategySelectorAgent` | Strategy | `02` #21 | P0 | `agent-rt-22` | `agent-rt-21` |
| 8 | 리스크 에이전트 | `PreRiskAgent` | Strategy | `02` #23 | P0 | `agent-rt-21` | `agent-rt-23` |
| 9 | 포지션 사이징 | `PositionSizingAgent` | Strategy | `02` #25 | P0 | `agent-rt-23` | `agent-rt-25` |
| 10 | 거래 에이전트 | `IntentEmitterAgent` | Strategy | `02` #30 | P0 | `agent-rt-25`, price agents | `agent-rt-30` |
| 11 | 주문 감시 | `OrderWatcherAgent` | Strategy | `02` #32 | P0 | OMS event source | `agent-rt-32` |
| 12 | 비상정지 | `EmergencyStopAgent` | Ops & Security | `05` #72 | P0 | `agent-rt-01` | `agent-ops-02` |
| 13 | 거래 로그 | `JournalAnalysisAgent` | Validation & Learning | `04` #56 | P0 | paper journal | `agent-val-06` |
| 14 | 검증 | `ValidationAgent` | Validation & Learning | `04` #51 | P0 | reports, journal | `agent-val-01` |
| 15 | 학습/리포트 | `LearningAgent` + `DailyReportAgent` | Validation & Learning | `04` #66/#57 | P0 | validation | `agent-val-16` |

`IntentEmitterAgent`는 `OrderIntent`까지만 만든다. `OrderWatcherAgent`는 read-only 관찰자다. `EmergencyStopAgent`만 kill switch set mutation을 수행한다.

## 5 meta-agent

| # | 명칭 | English alias | 서비스 | 우선순위 | 의존 | Backlog ID |
| --- | --- | --- | --- | --- | --- | --- |
| M1 | LLM 결과 검증 | `LlmOutputValidationAgent` | Validation & Learning | P0 | contracts | `agent-val-15` |
| M2 | Codex 테스트 | `CodexTestAgent` | Ops & Security | P0 | test base | `meta-codex-test-001` |
| M3 | Claude 리뷰 | `ClaudeReviewAgent` | Ops & Security | P0 | patch summary | `meta-claude-review-001` |
| M4 | Claude 설계 | `ClaudeDesignAgent` | Ops & Security | P0 | request scope | `meta-claude-design-001` |
| M5 | Codex 구현 | `CodexImplementationAgent` | Ops & Security | P0 | approved plan | `meta-codex-implement-001` |

## P0 착수 논리

1. Orchestrator와 Session Manager로 lifecycle과 session guard를 만든다.
2. E-Stop을 먼저 넣어 모든 후속 모듈이 fail-closed 신호를 받게 한다.
3. Data, Scanner, News/Event는 read-only라 위험이 낮다.
4. Analyst, Strategy Selector, Risk, Position Sizer는 Strategy Service 내부에서만 동작한다.
5. Trader는 마지막에 두며 `OrderIntent` 생성만 허용한다.
6. Validation과 Learning은 report/proposal만 생성한다.

## 반복 확인

Top 15와 meta-agent 모두 Agent ≠ Broker 원칙을 따른다. OMS만 executable order를 만든다. Broker Gateway만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.
