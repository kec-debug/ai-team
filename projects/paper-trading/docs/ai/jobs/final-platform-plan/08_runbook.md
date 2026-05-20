# 08. Final Platform Runbook

본 문서는 `docs/RUNBOOK.md` 를 대체하지 않고 확장한다. 현재 RUNBOOK 은 paper-use-ready 운영 절차이고, 본 문서는 final platform 단계의 procedure / incident response 설계다.

## 1. Paper training start / stop

| 항목 | 내용 |
| --- | --- |
| 사전 조건 | server reachable, paper mode, live disabled |
| 단계 | start command 참조, status 확인, dashboard 확인 |
| 검증 | runner state running, heartbeat 갱신 |
| 실패 시 fallback | stop 후 status 재확인 |
| rollback | run state stopped, open paper order 확인 |

## 2. Strategy 추가

| 항목 | 내용 |
| --- | --- |
| 사전 조건 | strategy boundary 이해, broker 직접 호출 금지 |
| 단계 | strategy class 추가, registry 연결, tests 추가 |
| 검증 | StrategyResult, blockers, non-executable intent |
| 실패 시 fallback | registry 에서 strategy 제거 |
| rollback | 관련 파일 revert 는 사용자 수동 |

## 3. Universe / watchlist 변경

| 항목 | 내용 |
| --- | --- |
| 사전 조건 | symbol allowlist 정책 확인 |
| 단계 | watchlist config 변경, status 확인 |
| 검증 | universe snapshot 에 symbol 반영 |
| 실패 시 fallback | 이전 watchlist 로 복구 |
| rollback | 변경 파일 단위로 수동 처리 |

## 4. Agent provider 변경

| 항목 | 내용 |
| --- | --- |
| 사전 조건 | deterministic fallback 활성 |
| 단계 | provider setting 변경, trace 확인 |
| 검증 | `provider_used`, `fallback_used`, `parse_status` |
| 실패 시 fallback | rule-based provider |
| rollback | provider 설정 원복 |

## 5. LLM fallback handling

- malformed output: validation block.
- timeout: deterministic fallback.
- missing evidence: recommendation block.
- hard risk blocker: LLM output 무시.

## 6. Stale quote handling

| 항목 | 내용 |
| --- | --- |
| 사전 조건 | quote timestamp 존재 |
| 단계 | quote age 확인 |
| 검증 | stale blocker 또는 정상 tick |
| 실패 시 fallback | source unavailable 로 표시 |
| rollback | 해당 tick order 생성 금지 |

## 7. Broker disconnect handling

- broker healthcheck 확인.
- disconnect guard 를 warning/danger 로 표시.
- open order reconciliation 은 read-only 부터 수행.
- unknown broker state 는 fail-closed.

## 8. Token expiration handling

- token status 는 redacted / relative 로만 표시.
- expired 상태에서는 broker 호출 차단.
- 재인증은 broker adapter 내부 경계에서만 처리.
- token 원문을 로그나 문서에 쓰지 않는다.

## 9. Order rejection handling

| 항목 | 내용 |
| --- | --- |
| 사전 조건 | order id / correlation id 확인 |
| 단계 | strategy blocker, risk verdict, OMS error, broker ack 순서로 확인 |
| 검증 | rejection reason 이 journal / report 에 남음 |
| 실패 시 fallback | unknown rejection 은 incident 로 기록 |
| rollback | paper position / cash snapshot 확인 |

## 10. Kill switch 사용

- kill switch 상태는 dashboard 와 risk status 에 표시.
- engaged 면 새 order 생성 금지.
- disengage 는 manual audit event 가 필요하다.
- live scope 는 future console 에서 별도 관리한다.

## 11. Live checklist

- live console locked 상태 확인.
- readiness checklist 확인.
- recent paper soak 와 tests 확인.
- manual approval 없이는 arm 금지.
- 실 주문 전환은 본 design 범위 밖.

## 12. Live validation 절차

1. paper evidence 검토.
2. risk limits 확인.
3. KIS status read-only 확인.
4. manual approval pending 상태 기록.
5. future job 의 arm guard 통과 전까지 locked 유지.

## 13. Rollback 절차

- kill switch engage.
- runner stop.
- status snapshot 저장.
- audit event 기록.
- 관련 report export.
- logical change 단위로 수동 rollback.

## 14. Dashboard troubleshooting

- dashboard not reachable: server status 확인.
- JSON only: `/dashboard` URL 확인.
- readiness warning: `/ops/preflight` detail 확인.
- paper order no fill: quote, spread, volume, session 확인.
- report missing: dry-run run directory 확인.

## 15. tmux 서버 관리

- tmux 는 server process 를 장시간 유지하기 위한 운영 도구다.
- 세션 이름, log path, restart 절차는 RUNBOOK 과 동기화한다.
- tmux 종료 전 server stop 을 먼저 확인한다.

## 16. PuTTY 터널

현재 `docs/RUNBOOK.md` 와 동일하게 Source port `8000`, Destination `127.0.0.1:8000`, Local tunnel 을 사용한다.
