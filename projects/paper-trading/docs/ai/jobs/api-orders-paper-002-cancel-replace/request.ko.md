# 작업 ID
api-orders-paper-002-cancel-replace

# 작업명
KIS 모의투자 주문 취소 / 정정 구현

KIS_2-check 결과, KIS 모의투자 주문 후속 기능 중 `cancel_order()`와 `replace_order()`만 READY 상태로 확인되었다.

확인된 내용:
- cancel_order: READY
- replace_order: READY
- get_open_orders: BLOCKED-BY-DOCS
- get_fills: BLOCKED-BY-DOCS
- get_order_status: BLOCKED-BY-DOCS

이번 작업은 KIS 모의투자 주문 취소/정정만 구현한다.
미체결 조회, 체결 조회, 주문상태 조회는 공식 response output 필드가 부족하므로 구현하지 않는다.

## 목표

- `KisBroker.cancel_order()` 본문을 구현한다.
- `KisBroker.replace_order()` 본문을 구현한다.
- KIS_2 catalog에서 Confirmed: yes인 공식값만 사용한다.
- 취소/정정 endpoint는 KIS_2에서 확인된 값만 사용한다.
- 취소/정정 TR ID는 KIS_2에서 확인된 모의투자 미국주식용 값만 사용한다.
- 실전 TR ID는 사용하지 않는다.
- 아시아/기타 거래소 취소/정정 TR ID는 이번 작업 범위에서 제외한다.
- get_open_orders / get_fills / get_order_status는 계속 fail-closed 상태로 둔다.
- dry-run 모드에서는 실제 HTTP 전송 없이 sanitized preview만 반환한다.
- dry-run false에서도 paper mode + live disabled + KIS_ENV=paper + 인증 통과 조건을 모두 만족해야만 모의투자 취소/정정 전송 경계에 도달한다.
- 테스트를 추가한다.

## 설계상 반드시 결정할 사항

KIS_2-check 리뷰에서 지적된 G1~G4를 이번 계획에서 반드시 해결해야 한다.

### G1. 취소/정정에 필요한 exchange 저장 방식

`/order-rvsecncl` body에는 `OVRS_EXCG_CD`가 필요하다.

현재 `KisOrderResponse`에 exchange 필드가 없다.

이번 작업에서는 아래 중 하나를 명확히 선택하고 구현한다.

- 선택 A: `KisOrderResponse`에 exchange 필드를 추가한다.
- 선택 B: 별도 `KisOrderHistoryEntry`를 추가한다.
- 선택 C: 미국주식 기본값 `NASD`를 사용한다.

단, 선택 C를 쓰는 경우 patch.md에 "이번 작업은 미국주식/NASD만 대상으로 한다"고 명시해야 한다.

### G2. cancel/replace 호출 경로

현재 OMS에 cancel/replace 메서드가 없다.

이번 작업에서는 아래 중 하나를 명확히 선택한다.

- 선택 A: KisBroker adapter level까지만 구현하고 OMS 연결은 후속 작업으로 분리한다.
- 선택 B: OMS에 cancel/replace entrypoint를 추가한다.
- 선택 C: runtime helper를 추가한다.

이번 작업에서는 범위를 줄이기 위해 기본 선택은 A로 한다.
즉, KIS adapter의 cancel/replace 본문만 구현하고 OMS 연결은 후속 runtime 작업으로 남긴다.

### G3. replace 후 새 ODNO 처리

KIS 정정 응답은 새 `output.ODNO`를 반환할 수 있다.

이번 작업에서는 아래 정책을 명확히 한다.

- 기존 order id는 유지한다.
- 새 broker order id는 `replacement_broker_order_id` 또는 동등한 필드로 보존한다.
- 기존 이력과 새 이력을 모두 추적할 수 있게 한다.
- 기존 order id를 조용히 덮어쓰지 않는다.

### G4. 아시아 거래소 제외

KIS_2 catalog에는 아시아 paper TR ID가 부분적으로 언급되어 있을 수 있으나,
이번 작업은 미국주식 모의투자 취소/정정만 대상으로 한다.

따라서:
- 아시아 거래소 취소/정정 TR ID 사용 금지
- 아시아 거래소 주문 취소/정정 구현 금지
- NASD/NYSE/AMEX 등 미국주식 범위만 명시
- 모호하면 fail-closed

## 절대 하지 말 것

- live trading 활성화 금지.
- 실전 주문 endpoint 사용 금지.
- 실계좌 주문 기능 구현 금지.
- KIS endpoint, TR ID, payload, header 추측 금지.
- KIS_2 또는 공식 catalog에서 확인되지 않은 값을 사용하지 말 것.
- get_open_orders 구현 금지.
- get_fills 구현 금지.
- get_order_status 구현 금지.
- 아시아 거래소 취소/정정 구현 금지.
- 외부 HTTP 라이브러리 사용 금지. stdlib `urllib.request`만 허용.
- Strategy, Agent, LLM이 broker를 직접 호출하는 경로 추가 금지.
- executable order를 Agent나 LLM이 생성하게 만들지 말 것.
- OMS 우회 금지.
- RiskEngine 우회 금지.
- `ALLOW_MARKET_ORDERS=true` 허용 금지.
- `OrderType.MARKET` 3중 가드 우회 금지.
- `OrderType.STOP` 도입 금지.
- FX 변환 함수나 환율 상수 도입 금지.
- `.env` 읽기/수정 금지.
- `.env.example`에 실제 값 추가 금지.
- 실제 app key, app secret, access token, Bearer token, 계좌번호를 코드/문서/테스트/patch에 기록 금지.
- GUI 파일 수정 금지.
- 자동 git commit / push / merge / production deploy 금지.

## 완료 기준

- `KisBroker.cancel_order()`가 KIS_2 공식 catalog 기반으로 구현된다.
- `KisBroker.replace_order()`가 KIS_2 공식 catalog 기반으로 구현된다.
- dry-run true에서는 실제 HTTP 전송 없이 sanitized preview만 반환한다.
- dry-run false에서는 paper mode + live disabled + KIS_ENV=paper + 인증 통과 조건을 만족해야만 전송 경계에 도달한다.
- 실전 endpoint/TR ID는 코드와 테스트에 들어가지 않는다.
- 아시아 거래소 TR ID는 코드와 테스트에 들어가지 않는다.
- 취소/정정 request body는 KIS_2에서 Confirmed: yes인 필드만 사용한다.
- 정정 후 새 ODNO 처리 정책이 테스트로 검증된다.
- get_open_orders / get_fills / get_order_status는 계속 fail-closed다.
- Strategy 패키지에서 KIS 직접 import가 없어야 한다.
- Agent/LLM 경로에서 KIS 직접 호출이 없어야 한다.
- OMS/RiskEngine 경계가 약화되지 않아야 한다.
- app key, app secret, token, 계좌번호 원문이 status/log/test output/patch에 노출되지 않는다.
- 전체 pytest 회귀 0건.
- 안전 grep이 clean이어야 한다.
- patch.md에 다음 항목을 포함한다.
  - 수정 파일 목록
  - 사용한 공식 취소/정정 endpoint / TR ID 출처
  - G1~G4를 어떻게 해결했는지
  - dry-run 동작 방식
  - 실제 모의투자 취소/정정 전송 조건
  - fail-closed로 남긴 항목
  - secret/account/token 노출 없음 확인
  - live trading 비활성 유지 확인
  - market order guard 유지 확인
  - 테스트 결과
  - Claude 검증 요청 프롬프트
  - Claude 리뷰가 REQUEST CHANGES/BLOCK일 때만 사용할 follow-up Codex 수정 프롬프트 작성 규칙

## 추가 조건

- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
- 필요한 경우에만 최소한의 질문을 해.