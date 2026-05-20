# 작업 ID
KIS_2-check

# 작업명
KIS_2 catalog 확인 및 다음 주문 API 작업 가능 여부 판단

KIS_2에서 `docs/kis/MISSING_OFFICIAL_VALUES.md`에 계좌 / 주문 관련 공식 문서값을 정리했다.

다음 작업 후보는 `api-orders-paper-002`이며, 목적은 아래 KIS 모의투자 주문 후속 기능 구현이다.

- cancel_order()
- replace_order()
- get_open_orders()
- get_fills()
- get_order_status()

하지만 실제 구현 전에 KIS_2 catalog에 필요한 공식값이 충분히 채워져 있는지 확인해야 한다.

이번 작업은 코드 구현이 아니라 문서 검토 및 다음 작업 가능 여부 판단이다.

## 목표

- `docs/kis/MISSING_OFFICIAL_VALUES.md`를 확인한다.
- KIS 모의투자 주문 후속 기능에 필요한 공식값이 있는지 판단한다.
- 취소 / 정정 / 미체결 / 체결조회 / 주문상태 조회별로 구현 가능 여부를 분류한다.
- 각 기능별로 필요한 endpoint, TR ID, method, headers, request fields, response fields가 `Confirmed: yes`인지 확인한다.
- 부족한 값은 `<TBD>` 또는 `Confirmed: no`로 남아 있는지 확인한다.
- 구현 가능한 기능과 아직 BLOCKED-BY-DOCS인 기능을 분리한다.
- 다음 Codex 작업을 하나로 할지, 기능별로 나눌지 판단한다.
- 코드 구현은 하지 않는다.

## 확인할 기능

아래 기능별로 catalog 상태를 확인한다.

### 1. cancel_order()

확인할 값:

- 모의투자 취소 endpoint
- 모의투자 취소 TR ID
- HTTP method
- required headers
- required request fields
- order id / original order id field
- response success field
- response error field

### 2. replace_order()

확인할 값:

- 모의투자 정정 endpoint
- 모의투자 정정 TR ID
- HTTP method
- required headers
- required request fields
- original order id field
- new quantity field
- new price field
- response success field
- response error field

### 3. get_open_orders()

확인할 값:

- 모의투자 미체결 조회 endpoint
- 모의투자 미체결 조회 TR ID
- HTTP method
- required headers
- required query/body fields
- response order id field
- response symbol field
- response side field
- response quantity field
- response remaining quantity field
- response price field
- response status field

### 4. get_fills()

확인할 값:

- 모의투자 체결 조회 endpoint
- 모의투자 체결 조회 TR ID
- HTTP method
- required headers
- required query/body fields
- response fill id 또는 order id field
- response symbol field
- response side field
- response filled quantity field
- response fill price field
- response fill time field

### 5. get_order_status()

확인할 값:

- 주문상태 조회 endpoint가 별도로 있는지
- 별도 endpoint가 없다면 미체결/체결 조회를 조합해야 하는지
- 주문번호 기준 조회 가능 여부
- response status mapping 가능 여부

## 절대 하지 말 것

- 코드 구현 금지.
- KIS endpoint, TR ID, payload, header 추측 금지.
- 공식 catalog에 없는 값을 새로 지어내지 말 것.
- 실전 주문 endpoint 사용 금지.
- live trading 활성화 금지.
- 실 broker API 호출 금지.
- `.env` 읽기/수정 금지.
- 실제 app key, app secret, access token, Bearer token, 계좌번호를 코드/문서/테스트/patch에 기록 금지.
- Strategy, Agent, LLM이 broker를 직접 호출하는 경로 추가 금지.
- 자동 git commit / push / merge / production deploy 금지.
- GUI 파일 수정 금지.

## 완료 기준

- 기능별 구현 가능 여부가 명확히 정리된다.
- 각 기능이 아래 상태 중 하나로 분류된다.
  - READY
  - PARTIALLY READY
  - BLOCKED-BY-DOCS
- READY 기능은 어떤 공식 endpoint / TR ID / fields를 사용할지 정리한다.
- BLOCKED 기능은 어떤 공식값이 부족한지 정리한다.
- 다음 작업 추천을 하나로 제시한다.
  - 예: `api-orders-paper-002`
  - 또는 `api-orders-paper-002-cancel-replace`
  - 또는 `api-orders-paper-002-query-only`
- 다음 Codex 구현용 request.ko.md 초안을 작성할지 여부를 판단한다.
- `docs/ai/jobs/KIS_2-check/plan.md` 또는 동등한 결과 문서에 정리한다.
- 코드 파일은 수정하지 않는다.

## 산출물

아래 파일을 작성한다.

- `docs/ai/jobs/KIS_2-check/plan.md`

가능하면 다음 파일도 작성한다.

- `docs/ai/jobs/KIS_2-check/recommendation.md`

내용:

1. KIS_2 catalog 요약
2. cancel_order 가능 여부
3. replace_order 가능 여부
4. get_open_orders 가능 여부
5. get_fills 가능 여부
6. get_order_status 가능 여부
7. 부족한 공식값 목록
8. 다음 작업 추천
9. 다음 작업이 가능한 경우 request.ko.md 초안

## 추가 조건

- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 검토를 시작해.
- 필요한 경우에만 최소한의 질문을 해.