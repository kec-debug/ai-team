# 08. Data Contracts

본 문서는 7 서비스와 85 역할 모듈 사이에서 사용하는 typed contract를 정의한다. 기존 domain model인 `OrderIntent`와 `BrokerOrder`는 재정의하지 않고 현재 코드의 의미를 인용한다.

## 안전 invariant

Agent는 Broker가 아니다. OMS만 executable `BrokerOrder`를 만든다. Broker Gateway Service만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.

## Contract catalog

| Contract | 필수 필드 | 옵션 필드 / 기본값 | Source | Sink | 비고 |
| --- | --- | --- | --- | --- | --- |
| `AgentInput` | `agent_id`, `correlation_id`, `symbol`, `timestamp`, `source` | `snapshot=null`, `event_context={}`, `paper_state={}`, `ops_state={}` | service dispatcher | agent module | raw secret 금지 |
| `AgentOutput` | `agent_id`, `correlation_id`, `status`, `reasons`, `blockers`, `trace` | `score=null`, `confidence=null`, `metadata={}` | agent module | next module / service | executable order 금지 |
| `AgentTrace` | `provider_used`, `fallback_used`, `parse_status`, `duration_ms` | `cost_units=0`, `validation_errors=[]`, `retry_count=0` | provider wrapper | audit/report | LLM 관찰성 |
| `AgentLifecycleState` | `agent_id`, `state` | `last_started_at=null`, `last_error=null`, `degraded=false` | Orchestrator | Ops | enum: idle/running/paused/error/stopped |
| `KillSwitchCommand` | `command_id`, `engaged`, `reason`, `issued_by`, `issued_at` | `scope=global`, `expires_at=null` | Ops / operator | Orchestrator / all services | 해제 자동화 없음 |
| `AlertEvent` | `severity`, `source`, `message`, `created_at` | `symbol=null`, `run_id=null`, `metadata={}` | any service | Ops / dashboard | secret scrub |
| `ServiceMessage` | `message_id`, `from_service`, `to_service`, `type`, `correlation_id` | `payload={}`, `deadline_ms=null` | service RPC | service RPC | loopback only |
| `OrderIntent` | 기존 domain fields | 기존 기본값 | Strategy Service | RiskEngine / OMS | non-executable intent |
| `BrokerOrder` | 기존 domain fields + `risk_token`, `oms_id` | 기존 기본값 | OMS | Broker Gateway Service | executable, OMS only |

## `AgentInput`

`AgentInput`은 모든 역할 모듈의 공통 입력 envelope다. Market Data Service에서 온 snapshot, News & Event Service에서 온 event, Ops state, paper state를 하나로 묶는다. KIS credential, token, raw account number는 포함하지 않는다.

## `AgentOutput`

`AgentOutput`은 score, confidence, reasons, blockers, metadata, trace를 포함한다. blockers는 삭제가 아니라 누적 방식으로 전달한다. Strategy Service는 이 값을 `StrategyResult`나 `RiskEngine` input feed로 변환할 수 있지만 broker로 보내지 않는다.

## `AgentTrace`

`AgentTrace`는 provider 관찰성의 핵심이다. `provider_used`, `fallback_used`, `parse_status`는 dashboard와 report에서 볼 수 있어야 한다. malformed output은 fallback으로 기록한다.

## `KillSwitchCommand`

비상정지 에이전트가 만드는 유일한 mutation command다. Orchestrator Service가 이 command를 받아 6개 서비스에 broadcast한다. 모든 서비스는 새 action을 중단해야 한다.

## `ServiceMessage`

서비스 간 RPC base envelope다. 외부 공개 endpoint로 쓰지 않는다. loopback HTTP 또는 UNIX socket 위에서만 사용한다. Strategy Service에서 Broker Gateway Service로 가는 write message는 `BrokerOrder` payload만 허용한다.

## `OrderIntent`

현재 `app/domain/orders.py`의 `OrderIntent` 의미를 따른다. symbol, side, quantity, order_type, limit_price 등을 담지만 executable broker order가 아니다. Agent와 Strategy는 이 수준까지만 생성할 수 있다.

## `BrokerOrder`

현재 `app/domain/orders.py`의 `BrokerOrder` 의미를 따른다. OMS가 `risk_token`과 `oms_id`를 부여한 뒤 Broker Gateway Service로 전달하는 executable payload다. Agent, LLM, Strategy module은 이를 직접 만들지 않는다.

## Contract별 secret policy

| Contract | Secret 허용 |
| --- | --- |
| `AgentInput` | no |
| `AgentOutput` | no |
| `AgentTrace` | no |
| `ServiceMessage` | no, Broker Gateway 내부 credential reference만 |
| `BrokerOrder` | raw account no 금지, masked/account reference only |

## 반복 확인

Data contract가 늘어나도 Agent는 Broker가 아니다. OMS만 executable order를 만든다. Broker Gateway만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.
