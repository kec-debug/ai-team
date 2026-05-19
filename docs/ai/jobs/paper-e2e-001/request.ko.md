# 작업 요청

내부 모의거래를 실제로 브라우저에서 진행할 수 있게 만든다.

## 최종 목표

현재 Paper Trading Dashboard는 dry-run 상태 확인과 tick 실행은 가능하지만, 사용자가 직접 가상 주문을 넣고 체결 결과를 보는 화면이 부족하다.

이번 작업에서는 브라우저에서 아래 흐름이 가능해야 한다.

1. Paper Trading Dashboard 접속
2. 현재 현금 / 포지션 / 체결내역 / 손익 확인
3. 종목, 매수/매도, 수량, 주문유형, 가격 입력
4. 가상 주문 실행
5. RiskEngine 검사
6. PaperBroker / PaperEngine으로 가상 체결
7. 결과를 즉시 대시보드에 표시
8. 실거래 / 실제 주문 / 실제 브로커 호출은 절대 하지 않음

## 요구사항

### 1. 대시보드 개선

기존 `/dashboard` 화면을 확장한다.

표시해야 할 것:
- 현재 모드: paper
- live_enabled: false
- market_orders_allowed: false
- cash balance
- positions
- open orders
- fills / trades
- realized PnL
- unrealized PnL 가능하면 표시
- last error
- safety status

### 2. 수동 가상 주문 입력 폼

대시보드에 입력 폼을 추가한다.

입력값:
- symbol
- side: BUY / SELL
- quantity
- order_type: LIMIT / MARKET / STOP_LIMIT 중 가능한 것만
- limit_price
- stop_price optional
- mock bid
- mock ask
- mock last
- mock volume
- currency 기본 KRW 또는 USD 선택 가능하면 추가

버튼:
- 가상 주문 실행
- 상태 새로고침
- 체결내역 초기화는 위험하지 않은 범위에서만 가능하면 추가

### 3. API 추가 또는 기존 API 확장

필요하면 다음 엔드포인트를 추가한다.

- GET /paper/account
- GET /paper/positions
- GET /paper/fills
- GET /paper/orders
- POST /paper/order/simulate

POST /paper/order/simulate 는 실제 브로커 API를 호출하지 않는다.

처리 흐름:
- request validation
- Paper order 생성
- RiskEngine 검사
- PaperBroker / PaperEngine에 mock quote 주입
- Fill 생성
- PaperAccount / Portfolio 반영
- Journal 기록
- 결과 JSON 반환

### 4. 안전 규칙

절대 금지:
- 실제 증권사 주문 API 호출
- KIS 실주문 호출
- live trading 활성화
- .env 읽기 또는 출력
- API key / secret / token 출력
- 계좌번호 출력
- LLM이 직접 executable order 생성
- RiskEngine 우회
- OMS 우회
- git commit / push / merge 자동 실행

반드시 유지:
- paper mode 기본값
- live_enabled false
- market orders disabled by default 또는 기존 안전 정책 유지
- 주문은 Strategy/RiskEngine/OMS/PaperBroker 흐름을 해치지 않기
- 실패 시 fail closed

### 5. 테스트

추가 또는 수정할 테스트:
- 수동 paper order simulate 성공
- 현금 부족 매수 거절
- 보유 수량 부족 매도 거절
- LIMIT BUY 체결
- LIMIT SELL 체결
- MARKET 주문 안전 정책 확인
- Fill 생성 후 position/cash 반영
- API가 secret을 노출하지 않음
- live trading이 켜지지 않음

### 6. 산출물

- docs/ai/jobs/paper-e2e-001/patch.md
- docs/ai/jobs/paper-e2e-001/status.md
- 필요한 app/api, app/runtime, app/portfolio, app/broker, tests 변경
- dashboard HTML/JS 변경

## 완료 기준

- `/dashboard`에서 사람이 직접 가상 주문을 넣을 수 있다.
- 주문 실행 후 cash / positions / fills / PnL이 화면에 반영된다.
- 실제 주문은 절대 발생하지 않는다.
- pytest 통과.
- compileall 통과.
