# 06. API / Data / Storage

본 문서는 API surface, data model, storage 설계를 통합한다. 현재 구현 anchor 는 `00_current_state.md` §5 이며, 신규 endpoint 는 future backlog 후보일 뿐 현재 구현 지시가 아니다.

## 1. API surface

| Endpoint | Method | Purpose | Request | Response | Authority | Safety conditions | Side effects | Paper/Live |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `/status` | GET | 통합 상태 | none | summary | 운영자 | read-only | none | both |
| `/ops/status` | GET | readiness summary | none | flags | 운영자 | read-only | none | both |
| `/ops/preflight` | GET | checklist | none | items | 운영자 | read-only | none | both |
| `/paper/status` | GET | paper status | none | paper flags | 운영자 | read-only | none | paper |
| `/paper/training/start` | POST | training run 시작 | options | run id | 운영자 | paper mode | run state | paper |
| `/paper/training/stop` | POST | training run 정지 | run id | stopped | 운영자 | owner/run valid | run state | paper |
| `/paper/training/tick` | POST | tick 실행 | snapshots/source | tick result | 시스템/운영자 | paper mode | run event | paper |
| `/paper/training/runs` | GET | run 목록 | filters | runs | 분석가 | read-only | none | paper |
| `/paper/orders` | GET | paper orders | filters | orders | 운영자 | read-only | none | paper |
| `/paper/fills` | GET | paper fills | filters | fills | 운영자 | read-only | none | paper |
| `/paper/positions` | GET | paper positions | none | positions | 운영자 | read-only | none | paper |
| `/agents/run` | POST | agent 분석 실행 | candidate context | trace | 분석가 | no broker call | trace | paper/research |
| `/agents/status` | GET | agent 상태 | none | status | 운영자 | read-only | none | research |
| `/agents/traces` | GET | trace 조회 | filters | traces | 분석가 | read-only | none | research |
| `/strategies` | GET | strategy 목록 | none | strategies | 운영자 | read-only | none | paper |
| `/strategies/{strategy_id}` | GET | strategy 상세 | path | detail | 개발자 | read-only | none | paper |
| `/strategies/{strategy_id}/backtest` | POST | backtest | dataset/params | result | 분석가 | no live broker | report | paper |
| `/reports` | GET | report 목록 | filters | reports | 분석가 | read-only | none | paper |
| `/reports/{run_id}` | GET | report 상세 | path | report | 분석가 | read-only | none | paper |
| `/live/status` | GET | live locked status | none | status | 운영자 | read-only | none | live locked |
| `/live/preflight` | GET | live checklist | none | checklist | 운영자 | read-only | none | live locked |
| `/live/account` | GET | live account readiness | none | masked status | 운영자 | read-only | none | live locked |
| `/live/positions` | GET | live positions readiness | none | masked status | 운영자 | read-only | none | live locked |
| `/live/arm` | POST | future arm request | manual ack | state | 운영자 | locked + approval | audit only initially | live locked |
| `/live/disarm` | POST | disarm | reason | state | 운영자 | authorized | audit | live |
| `/risk/status` | GET | risk state | none | guards | 운영자 | read-only | none | both |
| `/risk/kill-switch` | GET/POST | kill switch status/update | state/reason | state | 운영자 | audited | guard state | both |

All "NEW" entries are design backlog items, not current implementation.

## 2. Data models

| Model | Field | Type | Required | Default | 의미 / Source |
| --- | --- | --- | --- | --- | --- |
| `TrainingRun` | `run_id` | string | yes | none | run identity |
| `TrainingRun` | `state` | enum | yes | created | created/running/stopped/failed |
| `TrainingTick` | `tick_id` | string | yes | none | tick identity |
| `TrainingTick` | `run_id` | string | yes | none | parent run |
| `UniverseSnapshot` | `symbols` | list | yes | empty | universe at time |
| `WatchlistCandidate` | `symbol` | string | yes | none | candidate |
| `AgentTrace` | `provider_used` | string | yes | deterministic | provider |
| `AgentOutput` | `score` | decimal | no | null | normalized score |
| `StrategyCandidate` | `intent` | object | no | null | non-executable candidate |
| `StrategyDecision` | `blockers` | list | yes | empty | strategy block reasons |
| `RiskVerdict` | `approved` | bool | yes | false | risk result |
| `OrderIntent` | existing fields | existing | yes | existing | current domain |
| `OrderRequest` | `risk_token` | string | yes | none | OMS executable request |
| `BrokerOrder` | existing fields | existing | yes | existing | current domain |
| `OrderState` | `state` | enum | yes | created | order state |
| `Fill` | existing fields | existing | yes | existing | fill domain |
| `PositionSnapshot` | `positions` | list | yes | empty | portfolio state |
| `PortfolioSnapshot` | existing fields | existing | yes | existing | current service |
| `Report` | `run_id` | string | yes | none | report link |
| `LiveReadinessStatus` | `items` | list | yes | empty | preflight items |
| `PreflightItem` | `passed` | bool | yes | false | checklist state |
| `AuditEvent` | `correlation_id` | string | yes | none | trace |

## 3. State machines

```text
OrderState:
created -> risk_checked -> oms_accepted -> broker_accepted -> filled
       -> rejected
       -> cancelled
```

```text
TrainingRun:
created -> running -> stopping -> stopped
       -> failed
```

```text
LiveReadinessStatus:
locked -> preflight_ok -> manual_approval_pending -> armed_future -> disarmed
```

## 4. PostgreSQL tables

| Table | Purpose | Key columns | Indexes | Retention |
| --- | --- | --- | --- | --- |
| `orders` | order state | order_id, run_id | run_id, symbol, state | policy |
| `fills` | fill records | fill_id, order_id | symbol, filled_at | policy |
| `portfolio_snapshots` | portfolio history | snapshot_id, run_id | run_id, ts | policy |
| `audit_events` | safety/audit | event_id, correlation_id | ts, event_type | long |
| `training_runs` | run metadata | run_id | state, started_at | policy |
| `agent_traces` | agent trace | trace_id, run_id | provider, symbol | policy |
| `strategy_decisions` | strategy output | decision_id, run_id | symbol, strategy | policy |
| `reports` | report index | report_id, run_id | created_at | policy |

## 5. Redis keys

| Key pattern | Type | TTL | Purpose |
| --- | --- | --- | --- |
| `idem:{key}` | string | policy | duplicate guard |
| `kill:{scope}` | string | none | kill switch |
| `quote:{symbol}` | hash | short | latest quote |
| `status:{service}` | hash | short | latest status |
| `heartbeat:{runner}` | string | short | runner heartbeat |
| `lock:{resource}` | string | short | concurrency lock |

## 6. File / JSON fallback

현재 `reports/` 기반 dry-run report 는 file fallback 의 기준이다. future storage 가 도입되어도 local report export 는 debug 와 operator handoff 용도로 유지한다.

## 7. Replay / rehydrate / crash recovery

- Replay: event log 로 tick, decision, order, fill 을 재생.
- Rehydrate: startup 시 latest run, open orders, portfolio snapshot 로 복구.
- Crash recovery: incomplete run 을 `failed` 또는 `stopped_with_error` 로 audit 처리.

> **TODO**: 실제 migration 과 schema DDL 은 별도 storage job 에서 작성한다.
