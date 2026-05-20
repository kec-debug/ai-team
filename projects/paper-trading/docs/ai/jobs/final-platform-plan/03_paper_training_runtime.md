# 03. Paper Training Runtime

본 문서는 paper training 을 24시간 운영 서비스로 확장할 때의 runtime 설계를 정의한다. 24시간 운영은 계속 관찰하고 분석한다는 뜻이며, 24시간 주문을 넣는다는 뜻이 아니다. 주문 생성은 session guard, risk, OMS, broker boundary 를 통과해야 한다.

## 1. Runtime architecture

```text
TrainingRunner (24h loop)
  ├─ Session Router (KRX / US)
  │    ├─ valid window -> 주문 허용 가능
  │    └─ closed -> analysis / replay / preparation
  ├─ DataSource adapter (replay / synthetic / live quote)
  ├─ Strategy 평가
  ├─ RiskEngine
  ├─ OMS
  ├─ PaperBroker (tick)
  └─ Journal / Position / Cash 갱신
```

현재 구현 anchor 는 `00_current_state.md` §2, §3, §4 이다.

## 2. Service mode

| 요소 | 설계 |
| --- | --- |
| runner lifecycle | start / stop / heartbeat / graceful shutdown |
| tick cadence | source별로 조정 가능한 policy |
| run identity | `TrainingRun` id 와 correlation id |
| state output | dashboard, report, audit event |
| crash handling | 마지막 checkpoint 기준 rehydrate |

## 3. Universe / watchlist

- Universe 는 전체 후보 집합이다.
- Watchlist 는 운영자가 집중 관찰하는 subset 이다.
- symbol allowlist 는 safety guard 로 유지한다.
- Agent 는 watchlist candidate 를 제안할 수 있지만 실행 권한은 없다.

## 4. Session 인식

| 상태 | 허용 동작 |
| --- | --- |
| market open | quote ingestion, strategy eval, paper order 가능 |
| pre/after hours | policy 가 허용한 strategy 만 가능 |
| closed | replay, report, agent enrichment, preparation |
| unknown | fail-closed, order 생성 금지 |

## 5. Data source

| Source | 목적 | 안전 조건 |
| --- | --- | --- |
| replay source | 과거 event log 재생 | live broker 호출 없음 |
| synthetic source | deterministic scenario 검증 | 인위적 성과 주장 금지 |
| live quote source | 실제 quote 기반 paper decision | stale / spread guard 필수 |

> **TODO**: source adapter interface 와 persistence target 은 storage job 에서 확정한다.

## 6. 저장 대상

- Paper order.
- Fill.
- Position snapshot.
- Cash snapshot.
- Journal event.
- Strategy tick result.
- Risk verdict.
- TrainingRun aggregation.
- Audit event.

## 7. TrainingRun aggregation

| Metric | 의미 |
| --- | --- |
| ticks_total | 실행 tick 수 |
| candidates_seen | 전략 후보 수 |
| candidates_blocked | strategy / risk 차단 수 |
| orders_created | OMS 가 만든 paper order 수 |
| fills_count | paper fill 수 |
| errors_total | runtime error 수 |
| block_reasons | stale, spread, session, risk 등 |

## 8. 안전 가드 표

| Guard | 의미 | 트리거 조건 | 동작 | 현재 구현 여부 |
| --- | --- | --- | --- | --- |
| kill switch | 전역 정지 | engaged | 새 주문 차단 | 부분 구현 |
| stale quote | 오래된 quote 차단 | quote age 초과 | 후보 / fill 차단 | 구현 |
| spread guard | 넓은 spread 차단 | threshold 초과 | 후보 / fill 차단 | 구현 |
| volatility guard | 급변동 차단 | threshold 초과 | 주문 금지 | 미구현 |
| max notional | 주문 금액 제한 | per-order 초과 | risk reject | 구현 |
| max daily loss | 일일 손실 제한 | limit 초과 | order block | 미구현 |
| max position size | position size 제한 | threshold 초과 | risk reject | 미구현 |
| max orders per day | 주문 수 제한 | count 초과 | order block | 미구현 |
| session guard | session 외 주문 금지 | closed/unknown | fail-closed | 부분 구현 |
| duplicate idempotency | 중복 주문 방지 | same key 재사용 | duplicate reject | 미구현 |

## 9. Closed market behavior

시장이 닫혀 있을 때 runtime 은 멈추지 않는다. 단, 주문 실행은 금지하고 아래 작업만 허용한다.

- replay.
- report generation.
- agent research cache warmup.
- strategy parameter review.
- operator checklist.

## 10. Failure handling

- source unavailable: stale state 로 표시하고 주문 금지.
- broker unavailable: paper order 생성 중지, report event 기록.
- storage unavailable: in-memory safe mode 또는 local file fallback.
- unknown state: fail-closed.
