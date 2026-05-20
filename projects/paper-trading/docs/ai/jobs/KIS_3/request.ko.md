# 작업 ID
KIS_3

# 작업명
KIS 미체결 / 체결 / 주문상태 조회 공식 응답 필드 catalog 채우기

api-orders-paper-002-cancel-replace에서 KIS 모의투자 주문 취소 / 정정 구현이 진행되었다.

이제 다음 단계는 `get_open_orders()`, `get_fills()`, `get_order_status()` 구현이다.

하지만 KIS_2-check 결과에서 아래 기능들은 아직 BLOCKED-BY-DOCS 상태로 분류되었다.

- get_open_orders: BLOCKED
- get_fills: BLOCKED
- get_order_status: BLOCKED

이유:
- KIS 미체결 / 체결 조회 endpoint 일부는 확인되었지만, 응답 `output[]` 하위 필드가 부족하다.
- 주문번호, 종목, 매수/매도, 주문수량, 미체결수량, 체결수량, 체결가격, 주문상태, 체결시각 등을 내부 모델로 매핑할 수 있는 공식 field 이름이 부족하다.
- 별도 주문상태 조회 endpoint가 있는지, 아니면 미체결/체결 조회를 조합해야 하는지도 명확히 정리되어야 한다.

이번 작업은 코드 구현이 아니라 공식 문서값 catalog 보강 작업이다.

## 목표

- `docs/kis/MISSING_OFFICIAL_VALUES.md`에서 미체결 / 체결 / 주문상태 조회 관련 항목을 보강한다.
- KIS 공식 자료에서 확인된 값만 `Confirmed: yes`로 표시한다.
- 확인되지 않은 값은 `<TBD>`와 `Confirmed: no`로 유지한다.
- get_open_orders 구현 가능 여부를 판단한다.
- get_fills 구현 가능 여부를 판단한다.
- get_order_status 구현 가능 여부를 판단한다.
- 공식 자료에서 확인 가능한 request / response field를 정리한다.
- 코드 구현은 하지 않는다.

## 확인할 대상

### 1. 미체결 주문 조회

확인할 값:

- endpoint path
- HTTP method
- TR ID
- 모의투자 지원 여부
- required headers
- required query/body fields
- response list field 이름
- response order id field
- response original order id field, 있으면
- response symbol field
- response exchange field
- response side field
- response order quantity field
- response filled quantity field
- response remaining quantity field
- response limit price field
- response order status field
- response order time field
- response message/error field

### 2. 체결 조회

확인할 값:

- endpoint path
- HTTP method
- TR ID
- 모의투자 지원 여부
- required headers
- required query/body fields
- response list field 이름
- response fill id 또는 order id field
- response symbol field
- response exchange field
- response side field
- response filled quantity field
- response fill price field
- response fill time field
- response commission/fee field, 있으면
- response currency field, 있으면
- response message/error field

### 3. 주문상태 조회

확인할 값:

- 별도 주문상태 조회 endpoint가 있는지
- 주문번호 기준 단건 조회가 가능한지
- 미체결 조회와 체결 조회를 조합해야 하는지
- 주문 상태 field가 있는지
- 주문 상태 code mapping이 있는지
- canceled / rejected / filled / partially filled / open / expired 같은 내부 상태로 매핑 가능한지

## 참고 자료

가능하면 아래 공식 자료만 사용한다.

- `docs/kis/MISSING_OFFICIAL_VALUES.md`
- `uploads/*.xlsx`
- KIS Developers 공식 문서에서 가져온 자료
- 기존 KIS_2 catalog

공식 자료가 부족하면 부족하다고 남긴다.

## 절대 하지 말 것

- 코드 구현 금지.
- KIS endpoint, TR ID, payload, header, response field 추측 금지.
- 공식 자료에서 확인되지 않은 값을 `Confirmed: yes`로 표시하지 말 것.
- 실전 주문 endpoint 사용 금지.
- live trading 활성화 금지.
- 실 broker API 호출 금지.
- `.env` 읽기/수정 금지.
- `.env.example` 수정 금지.
- 실제 app key, app secret, access token, Bearer token, 계좌번호를 코드/문서/테스트/patch에 기록 금지.
- Strategy, Agent, LLM이 broker를 직접 호출하는 경로 추가 금지.
- GUI 파일 수정 금지.
- 자동 git commit / push / merge / production deploy 금지.

## 완료 기준

- 미체결 조회 output field catalog가 정리된다.
- 체결 조회 output field catalog가 정리된다.
- 주문상태 조회 가능 여부가 정리된다.
- 각 항목이 `Confirmed: yes` 또는 `Confirmed: no`로 표시된다.
- get_open_orders 구현 가능 여부가 READY / PARTIALLY READY / BLOCKED-BY-DOCS 중 하나로 분류된다.
- get_fills 구현 가능 여부가 READY / PARTIALLY READY / BLOCKED-BY-DOCS 중 하나로 분류된다.
- get_order_status 구현 가능 여부가 READY / PARTIALLY READY / BLOCKED-BY-DOCS 중 하나로 분류된다.
- 다음 구현 작업을 하나로 추천한다.
  - 예: `api-orders-paper-003-query`
  - 또는 `KIS_3-followup`
- 코드 파일은 수정하지 않는다.
- patch.md에 아래를 정리한다.
  - 어떤 공식 자료를 확인했는지
  - 어떤 값이 Confirmed: yes인지
  - 어떤 값이 여전히 `<TBD>`인지
  - get_open_orders / get_fills / get_order_status 구현 가능 여부
  - 다음 작업 추천
  - Claude 검증 요청 프롬프트
  - Claude 리뷰가 REQUEST CHANGES/BLOCK일 때만 사용할 follow-up Codex 수정 프롬프트 작성 규칙

## 수정 가능 파일

- `docs/kis/MISSING_OFFICIAL_VALUES.md`
- `docs/ai/jobs/KIS_3/patch.md`
- `docs/ai/jobs/KIS_3/request.ko.md`
- `docs/ai/jobs/KIS_3/plan.md`
- `docs/ai/jobs/KIS_3/codex-task.md`

## 검증

코드 변경이 아니므로 pytest는 필수 아님.

다만 가능하면 아래 확인을 수행한다.

```bash
cd /root/ai-dev-center/projects/ai-team
git diff --stat