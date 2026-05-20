# 07. Risk / Safety / Observability

본 문서는 safety guard 와 observability 를 통합 정의한다. 기준은 `00_current_state.md` §8 과 `docs/OPS_AUDIT.md` 의 안전 감사 원칙이다.

## 1. Safety guard catalog

| Guard | 트리거 조건 | 동작 | 현재 구현 여부 | 후속 job 필요 |
| --- | --- | --- | --- | --- |
| Global kill switch | engaged | 새 주문 차단 | 부분 구현 | M |
| Paper kill switch | paper scope engaged | paper order 차단 | 부분 구현 | S |
| Live kill switch | live scope engaged | live locked 유지 | 설계 필요 | M |
| Max daily loss | 일일 손실 초과 | order block | 미구현 | M |
| Max order notional | 단일 주문 금액 초과 | risk reject | 구현 | S |
| Max orders per day | 주문 수 초과 | order block | 미구현 | M |
| Max position size | position size 초과 | risk reject | 미구현 | M |
| Stale quote guard | quote age 초과 | candidate / fill 차단 | 구현 | S |
| Spread guard | spread 초과 | candidate / fill 차단 | 구현 | S |
| Volatility guard | 변동성 초과 | order block | 미구현 | M |
| Session guard | closed/unknown session | fail-closed | 부분 구현 | M |
| Duplicate idempotency guard | same key 재사용 | duplicate reject | 미구현 | M |
| Broker disconnect guard | broker unavailable | order block | 미구현 | M |
| Token expired guard | token expired | broker call block | 부분 구현 | M |
| Live arming guard | not armed | live order block | 미구현 | L |
| Manual approval guard | approval missing | arm block | 미구현 | L |
| Allowlist guard | symbol not allowed | risk reject | 구현 | S |
| Market order guard | market order attempted | reject | 구현 | S |
| Dry-run guard | dry-run required | real submit block | 구현 | S |
| Paper/live mismatch guard | mode mismatch | reject | 구현 | S |

## 2. Guard interaction

```text
Input candidate
  -> session guard
  -> stale / spread / volatility guard
  -> allowlist / notional / size / daily limits
  -> dry-run / paper-live mode guard
  -> OMS only if all passed
```

## 3. Observability catalog

| Card / Metric | 노출 위치 | 데이터 source | 새 endpoint 필요 |
| --- | --- | --- | --- |
| Safety banner | dashboard | ops preflight | no |
| Readiness checklist | dashboard/live console | `PreflightItem` | no |
| Runtime heartbeat | overview | runner heartbeat | yes |
| Paper runner status | paper training | `DryRunController.summary` | partial |
| Agent pipeline status | agent research | `AgentTrace` | yes |
| Strategy status | strategy lab | strategy registry | yes |
| Risk status | risk console | guard state | yes |
| OMS status | orders | OMS counters | yes |
| Broker status | broker card | broker healthcheck | partial |
| Reconciliation status | incident view | storage + broker | yes |
| Last error | overview | app state / audit | partial |
| Recent audit events | incident view | `AuditEvent` | yes |
| Alert skeleton | overview | guard events | yes |
| Incident view | runbook area | audit + reports | yes |
| Report export | reports | report storage | partial |

## 4. Alert severity

| Level | 의미 | 예 |
| --- | --- | --- |
| info | 정상 상태 | paper mode, dry-run true |
| warning | 운영 확인 필요 | KIS auth missing, kill switch on |
| danger | 즉시 중지 / 조사 | secret exposed, live enabled unexpectedly |

## 5. AuditEvent requirements

| Field | 의미 |
| --- | --- |
| `event_id` | event identity |
| `correlation_id` | run/tick/order 연결 |
| `event_type` | guard_triggered / state_changed / error |
| `severity` | info/warning/danger |
| `actor` | system/operator |
| `source` | runtime/API/dashboard |
| `redacted_payload` | secret-free context |
| `created_at` | event time |

## 6. Incident view

Incident view 는 아래를 한 화면에 묶는다.

- 최근 danger / warning.
- 관련 run id.
- 관련 order id.
- 관련 guard.
- operator action.
- rollback status.

> **TODO**: incident view 의 endpoint 와 storage 는 `06_api_data_storage.md` 의 audit model 도입 후 구현한다.

## 7. Safety non-negotiables

- LLM 은 hard risk block 을 해제하지 못한다.
- Strategy / Agent 는 broker 를 직접 호출하지 않는다.
- live 는 default lock 이며 manual approval 이 필요하다.
- KIS 미확인 값은 TODO / fail-closed 로 남긴다.
