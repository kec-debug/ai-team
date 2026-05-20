# 05. Live Validation Console

본 문서는 paper dashboard 와 분리된 live validation console 을 설계한다. 현재 시스템은 live locked 상태이며, `live_validation_ready` 는 UX 신호일 뿐 코드 게이트를 해제하지 않는다.

## 1. 핵심 원칙

- Live 는 default locked.
- status check 중심.
- 주문 버튼 없음.
- arm/disarm 은 future job 의 locked state machine 으로만 설계.
- manual approval 없이는 armed 상태가 될 수 없다.
- KIS 미확인 값은 TODO / fail-closed.

## 2. Readiness checklist

| 항목 | 의미 | 현재 기대 |
| --- | --- | --- |
| KIS config loaded | KIS 설정 존재 | 운영자가 확인 |
| KIS auth status | 인증 상태 | false 도 정상적으로 표시 |
| Token status | token 만료 / 부재 | redacted / relative only |
| Account loaded | 계좌 조회 가능성 | read-only |
| Positions loaded | 포지션 조회 가능성 | read-only |
| Market data available | quote source 가능성 | read-only |
| Order entry capability | 주문 진입 가능성 | 현재 보수적 false |
| Cancel / replace capability | 취소 / 정정 가능성 | 현재 보수적 false |
| Daily loss limit configured | 손실 제한 설정 | live 전 필수 |
| Max order count configured | 주문 수 제한 | live 전 필수 |
| Symbol whitelist configured | 허용 종목 제한 | live 전 필수 |
| Manual approval required | 수동 승인 | 항상 필요 |
| Kill switch status | 차단 준비 | visible |
| Recent paper soak result | paper 검증 결과 | 필요 |
| Recent test result | 회귀 테스트 결과 | 필요 |
| Operator acknowledgment | 운영자 확인 | 필요 |

## 3. State machine

```text
locked
  -> preflight_ok
  -> manual_approval_pending
  -> armed (future job only)
  -> disarmed
```

현재 구현은 locked + readiness display 까지다. `armed` 는 본 문서의 실행 범위 밖이다.

## 4. `live_validation_ready` 의미

- readiness checklist 의 요약 신호다.
- 실제 live 주문 권한이 아니다.
- code gate 를 해제하지 않는다.
- `kis_order_entry_ready` 와 실제 capability 를 혼동하지 않는다.
- `not_implemented` 는 ready 로 표시하지 않는다.

## 5. Console sections

| Section | 내용 |
| --- | --- |
| Lock banner | live locked / paper status |
| Preflight | checklist, passed/failed/detail |
| KIS status | config/auth/token/account/market |
| Paper evidence | recent soak, report, tests |
| Risk limits | loss, order count, allowlist |
| Manual approval | operator acknowledgment placeholder |
| Audit | who saw what, when |

## 6. 금지 UI

- live order button.
- enable live trading button.
- dry-run disable toggle.
- market order allow toggle.
- KIS raw secret display.

## 7. Future approval boundary

실 live 주문 실행은 본 doc 의 범위 밖이다. 별도 future job 은 manual approval, rollback, audit, account size limit, broker disconnect guard 를 다시 검토해야 한다.
