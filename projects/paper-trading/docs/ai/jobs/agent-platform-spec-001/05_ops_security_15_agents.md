# 05. 운영/보안 15 에이전트

본 문서는 운영, 보안, 잠금, 감사, 권한 관련 15개 역할 모듈을 정의한다. 대부분 read-only이며, 비상정지 모듈만 kill switch set mutation을 갖는다.

## 공통 안전 규칙

Agent는 Broker가 아니다. OMS만 executable `BrokerOrder`를 만든다. Broker Gateway Service만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.

## 공통 typed I/O

| 항목 | 내용 |
| --- | --- |
| Input | `OpsInput(config_state, service_state, logs, audit_events, operator_command)` |
| Output | `OpsOutput(alerts, lock_state, audit_record, command_result, trace)` |
| Provider | deterministic rule-based |
| Fallback | fail-closed |
| Parse status | ok / malformed / timeout |
| Mutation | 비상정지 kill switch set만 허용 |

## 15 모듈 catalog

| # | 한국어 / alias | 소속 서비스 | 책임 | Input typed | Output typed / 다음 모듈 | Score / Confidence | Reasons / Blockers 예시 | Provider / Fallback / Parse | 안전 가드 / 의존 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 71 | 모니터링 / `MonitoringAgent` | Ops & Security | service health와 runtime 상태 수집 | health_events | ops_status -> dashboard | confidence | degraded_service | rule / fail-closed / ok | read-only |
| 72 | 비상정지 / `EmergencyStopAgent` | Ops & Security | kill switch set 및 Orchestrator broadcast 요청 | operator_command, risk_event | kill_switch_command -> Orchestrator | confidence | emergency_stop | rule / fail-closed / ok | 유일 mutation |
| 73 | 보안 grep / `SecretLeakScanAgent` | Ops & Security | secret-like text scan | repo_text, logs | leak_scan_report -> alert | score | credential_pattern | rule / fail-closed / ok | secret 출력 0 |
| 74 | 시크릿 관리 / `SecretManagementAgent` | Ops & Security | secret issuance mediation | service_identity | secret_grant_policy -> Broker Gateway | confidence | unauthorized_service | rule / fail-closed / ok | Broker Gateway만 수신 |
| 75 | 실계좌 잠금 / `LiveAccountLockAgent` | Ops & Security | live account lock state 강제 | config_state | lock_state -> Orchestrator | confidence | live_enabled_detected | rule / fail-closed / ok | locked 유지 |
| 76 | 규정 체크 / `ComplianceCheckAgent` | Ops & Security | 운영 정책 위반 탐지 | audit_events | compliance_alert -> operator | confidence | policy_violation | rule / fail-closed / ok | 주문 0 |
| 77 | 세금 기록 / `TaxRecordAgent` | Ops & Security | fill/journal 기반 세무 기록 보조 | fills, account_events | tax_record -> reports | confidence | missing_fill | rule / deterministic / ok | read-only |
| 78 | 계좌 보호 / `AccountProtectionAgent` | Ops & Security | 계좌 상태 노출/사용 제한 감시 | account_status | account_guard -> live console | confidence | account_unavailable | rule / fail-closed / ok | masked only |
| 79 | 주문 감사 / `OrderAuditAgent` | Ops & Security | order lifecycle audit | OrderIntent, BrokerOrder, ack | audit_event -> storage | confidence | oms_bypass_attempt | rule / fail-closed / ok | BrokerOrder는 관찰만 |
| 80 | 장애 복구 / `RecoveryAgent` | Ops & Security | service restart/recovery 절차 제안 | incidents | recovery_plan -> operator | confidence | unsafe_restart | rule / fail-closed / ok | 자동 live unlock 0 |
| 81 | 실전 전환 승인 / `LiveApprovalAgent` | Ops & Security | live validation approval 상태 모델 | preflight, operator_ack | approval_state -> console | confidence | not_approved | rule / fail-closed / ok | locked / future-approval-gated |
| 82 | 로그 회전/보관 / `LogRetentionAgent` | Ops & Security | log retention과 scrub 상태 확인 | logs, policy | retention_report -> Ops | confidence | retention_gap | rule / deterministic / ok | secret scrub |
| 83 | 알림 라우팅 / `AlertRoutingAgent` | Ops & Security | alert severity별 routing | alerts, policy | routed_alert -> operator | confidence | route_missing | rule / deterministic / ok | 외부 secret 0 |
| 84 | 운영자 명령 처리 / `OperatorCommandAgent` | Ops & Security | 허용된 read-only 명령과 e-stop 명령 처리 | command | command_result -> Orchestrator/Ops | confidence | command_denied | rule / fail-closed / malformed | live enable 명령 거부 |
| 85 | 운영자 권한 관리 / `OperatorAccessAgent` | Ops & Security | operator role과 permission 확인 | identity, command | access_verdict -> command handler | confidence | unauthorized | rule / fail-closed / ok | least privilege |

## 특수 모듈 설명

- `EmergencyStopAgent`: kill switch set만 수행한다. 해제는 별도 수동 절차이며 자동 해제는 없다.
- `LiveAccountLockAgent`: `live_trading_enabled=False` 상태를 강제하고 위반을 alert로 올린다.
- `LiveApprovalAgent`: locked / future-approval-gated 설계이며 live 활성화를 권고하지 않는다.
- `SecretManagementAgent`: Broker Gateway Service만 credential grant 대상이다.

## 반복 확인

운영/보안 Agent도 Broker가 아니다. OMS만 executable order를 만든다. Broker Gateway만 KIS 자격증명을 가진다. LLM은 hard risk block을 풀 수 없다. live는 기본 locked 상태다.
