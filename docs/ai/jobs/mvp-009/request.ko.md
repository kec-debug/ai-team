# 작업 ID
mvp-009

# 작업명
KIS 모의투자 주문 흐름 연결

미국주식 자동 페이퍼매매 시스템에서 KIS Open API 모의투자 주문 흐름을 연결해줘.

현재 목표는 실전거래가 아니라 KIS 모의투자 주문 검증이다.
live trading은 절대 활성화하지 않는다.

## 현재 상태

이미 완료된 것:
- paper-trading 프로젝트 기본 구조
- KIS 설정 구조
- `.env` 기반 KIS 설정 로딩
- KIS Auth / Account / MarketData 골격
- `/paper/status`에 KIS 상태 표시
- secret/account masking
- 프리마켓 갭 + 거래량 돌파 전략
- RiskEngine / OMS / BrokerAdapter 기본 경계
- 테스트 통과 상태

이번 목표는 KIS 모의투자 주문 흐름을 아래 경로로 연결하는 것이다.

Strategy
→ RiskEngine
→ OMS
→ BrokerAdapter
→ KisBroker
→ KIS 모의투자 주문 API

## 매우 중요한 원칙

실전 주문은 절대 연결하지 마.

이번 작업은 KIS 모의투자 주문만 대상으로 한다.

반드시 유지:
- TRADING_MODE=paper
- LIVE_TRADING_ENABLED=false
- ALLOW_MARKET_ORDERS=false
- KIS_ENV=paper
- 시장가 주문 금지
- 지정가 주문만 허용
- live trading 기본 비활성
- 실계좌 주문 차단
- Strategy가 KIS를 직접 호출 금지
- Agent/LLM이 직접 주문 금지
- OMS 우회 금지
- RiskEngine 우회 금지

## 공식 문서 조건

KIS endpoint, TR ID, header, payload는 공식 문서 기준으로만 구현해.

중요:
- 공식 문서 또는 현재 repo 안의 명확한 문서에서 확인되지 않은 endpoint/TR ID/payload는 절대 추측하지 마.
- 확실하지 않으면 TODO + fail-closed로 남겨.
- fake endpoint를 만들지 마.
- 실전투자 endpoint는 절대 연결하지 마.
- 모의투자 endpoint와 실전투자 endpoint를 혼동하지 마.

공식 문서 정보가 부족하면:
1. 구현 가능한 내부 경계와 테스트만 만들고
2. 실제 HTTP 전송부는 fail-closed로 둔 뒤
3. patch.md에 “공식 문서 필요”라고 명확히 적어.

## 구현할 기능

### 1. KIS 모의투자 주문 요청 모델

내부 주문 객체를 KIS 모의투자 주문 요청으로 변환하는 경계를 만들어줘.

필드 예시:
- symbol
- market
- side
- quantity
- order_type
- limit_price
- extended_hours
- account_no_masked
- broker_environment
- idempotency_key

조건:
- 시장가 주문이면 거절
- quantity <= 0이면 거절
- limit_price 없으면 거절
- KIS_ENV가 paper가 아니면 거절
- live trading이면 거절
- 계좌번호 원문은 출력하지 않음

### 2. KisBroker 주문 메서드

아래 메서드를 정리해줘.

- place_order()
- cancel_order()
- replace_order()
- get_open_orders()
- get_order_status()
- get_fills()

구현 기준:
- 공식 문서 기준으로 확실한 KIS 모의투자 주문 API만 연결
- 확실하지 않은 부분은 fail-closed / TODO
- 실전 주문은 구현하지 않음
- secret/account 원문은 절대 출력하지 않음
- app key, app secret은 `.env`에서만 읽음

### 3. OMS와 연결

OMS가 KisBroker를 통해 주문을 제출할 수 있도록 연결 준비를 해줘.

조건:
- OMS가 executable order를 생성한다.
- Strategy는 non-executable intent까지만 만든다.
- RiskEngine 승인 없이는 OMS가 주문 제출하지 않는다.
- BrokerAdapter는 OMS에서만 호출된다.
- 중복 주문 방지를 위한 idempotency 흐름을 유지한다.

### 4. 주문 guard

KIS 모의투자 주문 전 반드시 아래를 확인해.

- paper mode인지
- live trading disabled인지
- KIS_ENV=paper인지
- market order가 아닌지
- quantity > 0인지
- limit_price가 있는지
- stale quote가 아닌지
- kill switch가 꺼져 있는지
- RiskEngine 승인 여부
- OMS idempotency 여부

하나라도 실패하면 주문 거절.

### 5. 주문 결과 모델

KIS 모의투자 주문 결과를 내부 모델로 변환하는 구조를 만들어줘.

필드 예시:
- internal_order_id
- broker_order_id
- broker
- status
- submitted_at
- symbol
- side
- quantity
- limit_price
- raw_response_sanitized

조건:
- raw_response에 secret/account 원문이 있으면 저장하지 마.
- 계좌번호는 마스킹만 허용.
- 실패 응답도 안전하게 마스킹.

### 6. 취소 / 정정 / 조회

아래 기능도 경계 또는 실제 모의투자 연결을 준비해.

- cancel_order()
- replace_order()
- get_open_orders()
- get_order_status()
- get_fills()

공식 문서가 없으면 실제 HTTP 호출은 만들지 말고 fail-closed로 둬.

### 7. status 업데이트

`/paper/status` 또는 기존 status endpoint에 아래 필드를 추가해줘.

- kis_order_entry_ready
- kis_order_entry_mode
- kis_order_submission_available
- kis_cancel_available
- kis_replace_available
- kis_open_orders_available
- kis_fills_available
- kis_order_methods_fail_closed
- live_trading_enabled
- allow_market_orders
- secret_exposed

실제 app key, app secret, 계좌번호 원문은 절대 출력하지 마.

## 테스트 요구사항

아래 테스트를 추가해줘.

1. KIS 모의투자 주문은 RiskEngine과 OMS를 통과해야만 가능
2. Strategy가 KIS를 직접 호출하지 않음
3. Agent/LLM이 직접 주문하지 않음
4. market order 거절
5. limit_price 없는 주문 거절
6. quantity <= 0 주문 거절
7. live trading true이면 거절
8. KIS_ENV가 paper가 아니면 거절
9. secret/account 원문이 status/log/response/test output에 노출되지 않음
10. 공식 문서 정보가 없으면 fail-closed
11. 주문 성공/실패 응답이 내부 모델로 안전하게 변환됨
12. get_open_orders / get_order_status / get_fills가 안전하게 동작하거나 fail-closed
13. 기존 테스트가 계속 통과

## 수정 가능 파일

필요한 경우 아래 파일을 수정해도 된다.

- projects/paper-trading/app/broker/kis.py
- projects/paper-trading/app/broker/base.py
- projects/paper-trading/app/oms/*
- projects/paper-trading/app/risk/*
- projects/paper-trading/app/api/routes.py
- projects/paper-trading/app/api/server.py
- projects/paper-trading/app/models/*
- projects/paper-trading/app/runtime/*
- projects/paper-trading/tests/*
- projects/paper-trading/README.md
- docs/ai/jobs/mvp-009/patch.md

현재 프로젝트 구조가 다르면 그 구조에 맞춰 최소 수정해줘.

## 금지 사항

- 실제 KIS app key, app secret, 계좌번호를 코드/문서/로그에 쓰지 마.
- `.env`를 Git에 추가하지 마.
- 실전 주문 기능을 만들지 마.
- live trading을 활성화하지 마.
- 시장가 주문을 허용하지 마.
- KIS endpoint/TR ID/payload를 추측하지 마.
- Strategy가 KIS를 직접 호출하게 만들지 마.
- Agent/LLM이 직접 주문하게 만들지 마.
- auth, payment, production infra, database migrations는 건드리지 마.
- git commit, push, merge는 자동화하지 마.

## 검증

아래를 실행해줘.

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider