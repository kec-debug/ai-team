# 10. Acceptance Criteria

본 문서는 agent platform spec 자체의 완료 기준과 후속 implementation job 공통 acceptance를 정의한다. 본 설계는 문서 작업이며 application code를 만들지 않는다.

## 안전 invariant

Agent는 Broker가 아니다. OMS만 executable `BrokerOrder`를 만든다. Broker Gateway Service만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.

## 본 design acceptance

| 항목 | 기준 |
| --- | --- |
| 파일 수 | `00_*.md`~`10_*.md` 11개 + `patch.md` 1개, 총 12개 신규 |
| 위치 | `docs/ai/jobs/agent-platform-spec-001/` 내부만 |
| 언어 | 한국어 우선, 기술 식별자는 inline code |
| 코드 | 실행 가능한 Python/TypeScript/SQL/Bash 0 |
| 7 서비스 | Orchestrator, Market Data, Strategy, Broker Gateway, News & Event, Validation & Learning, Ops & Security |
| 85 모듈 | 40/10/20/15 합계 85 |
| mapping | `01_seven_services.md`에 85 row |
| backlog | `09_implementation_backlog.md`에 97 row |
| KIS | `Confirmed: yes` catalog 외 추측 0, 미확인은 TODO |
| live | live activation, arming, dry-run 해제 권고 0 |
| secrets | raw key/secret/account/token 0 |
| 성과 표현 | 과장된 결과 주장 0 |
| 시간 표현 | 날짜/기간 약속 0 |

## 후속 implementation job 공통 template

| 영역 | Acceptance |
| --- | --- |
| 파일 범위 | `app/agents/<agent>/` 또는 `app/services/<service>/` 중심으로 제한 |
| broker import | Broker Gateway Service 외 `app.broker.*` import 0 |
| OMS 호출 | Strategy Service 내부에서만 단방향 |
| typed I/O | `AgentInput`, `AgentOutput`, `AgentTrace` schema 검증 |
| trace | `provider_used`, `fallback_used`, `parse_status` 회귀 |
| secret | secret-like string 0, masked만 허용 |
| LLM | optional, deterministic fallback 필수 |
| kill switch | engaged 상태에서 새 action 0 |
| RPC | loopback 또는 UNIX socket only |
| live lock | live enable, dry-run disable 자동화 0 |
| tests | unit + boundary + safety grep |
| git | commit/push/merge/deploy 자동화 0 |

## Review template

1. 변경 파일이 승인 범위 안인지 확인한다.
2. Agent가 broker를 직접 호출하지 않는지 grep과 code review로 확인한다.
3. OMS 외 executable order 생성 경로가 없는지 확인한다.
4. Broker Gateway 외 KIS credential 접근이 없는지 확인한다.
5. LLM output이 risk hard block을 해제하지 않는지 확인한다.
6. live lock과 `KIS_ORDER_DRY_RUN` 기본값을 건드리지 않았는지 확인한다.
7. secret, token, account, vendor payload 추측이 없는지 확인한다.
8. tests와 patch.md 결과가 실제 실행 결과인지 확인한다.

## BLOCK 조건

| 조건 | 판정 |
| --- | --- |
| Agent -> broker 직접 호출 | BLOCK |
| OMS 우회 executable order | BLOCK |
| Broker Gateway 외 KIS credential | BLOCK |
| LLM이 hard blocker 해제 | BLOCK |
| live unlock 또는 dry-run 해제 | BLOCK |
| KIS endpoint/TR ID/payload 추측 | BLOCK |
| secret 노출 | BLOCK |

## 반복 확인

후속 job이 어떤 모듈을 구현하더라도 Agent는 Broker가 아니다. OMS만 executable order를 만든다. Broker Gateway만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.
