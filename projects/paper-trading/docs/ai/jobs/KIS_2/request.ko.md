# 작업 ID
KIS_2

# 작업명
KIS 계좌 / 주문 공식 문서값 catalog 채우기

api-market-data-001에서 KIS 해외주식 현재체결가 기반 시세 조회 구현이 진행되었다.

다음 단계는 실제 주문 구현이 아니라, KIS 계좌 조회와 모의투자 주문 구현에 필요한 공식 문서값을 먼저 catalog에 정리하는 것이다.

현재 `KisAccountClient`와 `KisBroker`의 계좌 / 주문 관련 메서드는 공식 endpoint, TR ID, request field, response field 값이 부족해서 fail-closed 상태다.

이번 작업은 `docs/kis/MISSING_OFFICIAL_VALUES.md`의 계좌 및 주문 관련 빈 항목을 KIS 공식 자료 기준으로 채우는 문서 전용 작업이다.

## 목표

- `docs/kis/MISSING_OFFICIAL_VALUES.md`의 계좌 관련 항목을 공식 자료 기준으로 정리한다.
- `docs/kis/MISSING_OFFICIAL_VALUES.md`의 주문 관련 항목을 공식 자료 기준으로 정리한다.
- KIS 모의투자에서 지원되는 endpoint와 실전 전용 endpoint를 구분한다.
- 계좌 / 잔고 / 포지션 조회에 필요한 endpoint, TR ID, method, headers, request fields, response fields를 정리한다.
- 모의투자 주문 / 취소 / 정정 / 미체결 / 체결조회 / 주문상태 조회에 필요한 endpoint, TR ID, method, headers, request fields, response fields를 정리한다.
- 확인된 값만 `Confirmed: yes`로 표시한다.
- 확인되지 않은 값은 `<TBD>`와 `Confirmed: no`로 유지한다.
- `uploads/6.xlsx` 등 저장소에 있는 KIS 공식 자료만 사용한다.
- 공식 자료가 부족하면 부족한 항목을 명확히 남긴다.
- 코드 구현은 하지 않는다.

## 절대 하지 말 것

- live trading 활성화 금지.
- 실 broker API 호출 금지.
- KIS endpoint, TR ID, payload, header 추측 금지.
- 공식 자료에서 확인되지 않은 값을 채우지 말 것.
- KIS 주문 HTTP 구현 금지.
- KIS 계좌 HTTP 구현 금지.
- Strategy, Agent, LLM이 broker를 직접 호출하는 경로 추가 금지.
- executable order를 Agent나 LLM이 생성하게 만들지 말 것.
- 모든 주문은 Strategy → RiskEngine → OMS → PaperBroker 경로를 통과해야 한다는 안전 원칙을 변경하지 말 것.
- `ALLOW_MARKET_ORDERS=true` 허용 금지.
- `OrderType.MARKET` 3중 가드 우회 금지.
- FX 변환 함수나 환율 상수 도입 금지.
- `.env` 읽기/수정 금지.
- `.env.example` 수정 금지.
- 실제 app key, app secret, access token, Bearer token, 계좌번호를 코드/문서/테스트/patch에 기록 금지.
- 외부 HTTP 라이브러리 추가 금지.
- GUI 파일 수정 금지.
- 자동 git commit / push / merge / production deploy 금지.

## 완료 기준

- `docs/kis/MISSING_OFFICIAL_VALUES.md`의 계좌 관련 항목이 공식 자료 기준으로 업데이트된다.
- `docs/kis/MISSING_OFFICIAL_VALUES.md`의 주문 관련 항목이 공식 자료 기준으로 업데이트된다.
- 각 항목에 `Confirmed: yes` 또는 `Confirmed: no`가 명확히 표시된다.
- 모의투자 지원 여부와 실전 전용 여부가 구분된다.
- 계좌 / 잔고 / 포지션 조회에 필요한 값이 정리된다.
- 모의투자 주문 / 취소 / 정정 / 미체결 / 체결조회 / 주문상태 조회에 필요한 값이 정리된다.
- 공식 자료에서 확인할 수 없는 값은 추측하지 않고 `<TBD>`로 남긴다.
- 코드 파일은 수정하지 않는다.
- 테스트 실행이 필요한 코드 변경은 없어야 한다.
- patch.md에 어떤 값을 채웠고 어떤 값이 아직 부족한지 정리한다.
- 다음 작업인 `api-account-001` 또는 `api-orders-paper-001` 진행 가능 여부를 명확히 판단한다.