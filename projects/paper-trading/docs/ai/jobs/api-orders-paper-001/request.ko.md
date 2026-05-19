# 작업 ID
api-orders-paper-001

# 작업명
KIS 모의투자 주문 본문 구현

KIS_2에서 계좌 및 주문 관련 공식 문서값 catalog가 정리되었고, api-account-001에서 KIS 모의 계좌 / 잔고 / 포지션 조회 구현이 완료되었다.

다음 단계는 `KisBroker.place_order()`의 모의투자 주문 본문을 구현하는 것이다.

이번 작업은 실전거래가 아니라 KIS 모의투자 주문 검증이다. live trading은 계속 비활성이다. 주문은 반드시 Strategy → RiskEngine → OMS → BrokerAdapter 경로를 통과해야 하며, Strategy/Agent/LLM이 직접 주문을 만들거나 broker를 호출하면 안 된다.

## 목표

- `KisBroker.place_order()` 모의투자 주문 본문을 구현한다.
- KIS_2에서 `Confirmed: yes`로 정리된 모의투자 주문 endpoint, TR ID, headers, request fields, response fields만 사용한다.
- stdlib `urllib.request` 기반 기존 HTTP 경계를 사용한다.
- 외부 HTTP 라이브러리는 추가하지 않는다.
- `KIS_ORDER_DRY_RUN=true` 기본값을 유지한다.
- dry-run true이면 실제 HTTP 주문을 전송하지 않고 sanitized order preview만 반환한다.
- dry-run false인 경우에도 `TRADING_MODE=paper`, `LIVE_TRADING_ENABLED=false`, `KIS_ENV=paper` 조건을 모두 만족해야만 모의투자 주문 전송이 가능하다.
- 시장가 주문은 허용하지 않는다.
- 지정가 주문만 허용한다.
- quantity, limit_price, symbol, side를 검증한다.
- 주문 응답을 내부 broker order result / ack 모델로 안전하게 변환한다.
- raw response는 sanitized 형태로만 보관한다.
- app key, app secret, access token, 계좌번호 원문, Bearer token은 절대 노출하지 않는다.
- 테스트를 추가한다.

## 절대 하지 말 것

- live trading 활성화 금지.
- 실전 주문 endpoint 사용 금지.
- 실계좌 주문 기능 구현 금지.
- KIS endpoint, TR ID, payload, header 추측 금지.
- KIS_2 또는 공식 catalog에서 확인되지 않은 값을 사용하지 말 것.
- `cancel_order()`, `replace_order()`, `get_open_orders()`, `get_fills()`, `get_order_status()` 본문 구현은 이번 작업 범위가 아니다. 필요한 경우 fail-closed 유지.
- 외부 HTTP 라이브러리(`requests`, `httpx`, `aiohttp`, `urllib3`) import 금지.
- Strategy, Agent, LLM이 broker를 직접 호출하는 경로 추가 금지.
- executable order를 Agent나 LLM이 생성하게 만들지 말 것.
- 모든 주문은 Strategy → RiskEngine → OMS → PaperBroker/KisBroker 경로를 통과해야 한다.
- OMS 우회 금지.
- RiskEngine 우회 금지.
- `ALLOW_MARKET_ORDERS=true` 허용 금지. `load_settings()`의 reject 정책을 풀지 않는다.
- `OrderType.MARKET` 3중 가드 우회 금지.
- `OrderType.STOP` 도입 금지. LIMIT / STOP_LIMIT / MARKET 3개만 유지.
- FX 변환 함수나 환율 상수 도입 금지.
- `.env` 읽기/수정 금지.
- `.env.example`에 실제 값 추가 금지.
- 실제 app key, app secret, access token, Bearer token, 계좌번호를 코드/문서/테스트/patch에 기록 금지.
- GUI 파일(`app/api/`, `app/static/`, `app/main.py`) 수정 금지.
- 자동 git commit / push / merge / production deploy 금지.

## 완료 기준

- `KisBroker.place_order()`가 KIS_2의 공식 catalog 기반으로 구현된다.
- dry-run true에서는 실제 HTTP 주문이 전송되지 않는다.
- dry-run true에서는 sanitized preview와 dry-run ack만 반환한다.
- dry-run false에서는 모의투자 환경과 모든 안전 조건을 만족할 때만 주문 전송 경계에 도달한다.
- `TRADING_MODE=paper`가 아니면 주문이 거절된다.
- `LIVE_TRADING_ENABLED=true`이면 주문이 거절된다.
- `KIS_ENV=paper`가 아니면 주문이 거절된다.
- 시장가 주문은 거절된다.
- limit_price 없는 주문은 거절된다.
- quantity <= 0 주문은 거절된다.
- KIS 공식 catalog에 없는 값은 사용하지 않는다.
- 주문 응답 parser는 공식 response field만 사용한다.
- raw response는 sanitized 처리된다.
- app key, app secret, access token, Bearer token, 계좌번호 원문은 status, log, test output, patch 어디에도 노출되지 않는다.
- Strategy 패키지에서 KIS 직접 import가 없어야 한다.
- Agent/LLM 경로에서 KIS 직접 호출이 없어야 한다.
- OMS/RiskEngine 경계가 약화되지 않아야 한다.
- `cancel_order()`, `replace_order()`, `get_open_orders()`, `get_fills()`, `get_order_status()`는 이번 작업에서 fail-closed 상태를 유지한다.
- 전체 pytest 회귀 0건.
- 안전 grep이 clean이어야 한다.
- patch.md에 다음 항목을 포함한다.
  - 수정 파일 목록
  - 사용한 공식 주문 endpoint / TR ID 출처
  - dry-run 동작 방식
  - 실제 모의투자 주문 전송 조건
  - fail-closed로 남긴 항목
  - secret/account/token 노출 없음 확인
  - live trading 비활성 유지 확인
  - market order guard 유지 확인
  - 테스트 결과
  - Claude 검증 요청 프롬프트
  - Claude 리뷰가 REQUEST CHANGES/BLOCK일 때만 사용할 follow-up Codex 수정 프롬프트 작성 규칙