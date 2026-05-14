# 작업 ID
mvp-008

# 작업명
KIS 모의투자 주문 흐름 연결 준비

미국주식 자동 페이퍼매매 시스템에서 KIS 모의투자 주문 흐름을 연결할 준비를 해줘.

현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 주문 흐름 검증이다.
live trading은 절대 활성화하지 않는다.

## 현재 상태

mvp-006-1과 mvp-007에서 아래 작업이 완료되었다.

- paper-trading 프로젝트 기본 구조 생성
- KIS 설정 구조 준비
- `.env` 기반 KIS 설정 로딩
- KIS Broker Adapter 골격
- KIS Auth / Account / MarketData Client 골격
- `/paper/status`에 KIS 상태 표시
- secret/account masking 테스트
- 74개 테스트 통과

이번 mvp-008에서는 실제 실계좌 주문이 아니라,
KIS 모의투자 주문 흐름을 안전하게 연결할 준비를 한다.

## 핵심 목표

Strategy → RiskEngine → OMS → BrokerAdapter → KIS Broker 경로가 유지되도록 하면서,
KIS 모의투자 주문 메서드의 안전한 경계를 만든다.

단, 공식 문서가 확인되지 않은 endpoint, TR ID, payload는 절대 추측해서 구현하지 않는다.

## 구현할 내용

### 1. KIS 주문 메서드 경계 정리

`KisBroker` 또는 현재 구조에 맞는 KIS adapter에 아래 주문 관련 메서드를 정리해줘.

- place_order()
- cancel_order()
- replace_order()
- get_open_orders()
- get_fills()
- get_order_status()

조건:
- 실제 endpoint/TR ID/payload를 추측해서 만들지 마.
- 공식 문서가 없으면 TODO + fail-closed로 둬.
- 메서드는 존재하되, 실주문 전송은 아직 하지 마.
- NotImplementedError 또는 안전한 Rejected 상태를 반환하게 해.
- 에러 메시지는 secret/account를 노출하지 않아야 한다.

### 2. OMS → KIS Broker 연결 준비

OMS가 broker adapter를 통해 주문을 보낼 수 있는 구조인지 점검하고,
필요하면 interface를 정리해줘.

중요:
- Strategy가 KIS를 직접 호출하면 안 된다.
- Agent/LLM이 KIS를 직접 호출하면 안 된다.
- OMS를 우회해서 주문하면 안 된다.
- 모든 주문은 반드시 RiskEngine을 통과해야 한다.
- OMS만 executable order를 만들 수 있다.

### 3. KIS 모의투자 주문 요청 모델 준비

실제 전송은 하지 말고, 내부 도메인 모델 기준으로 KIS 주문 요청 변환 경계를 만들어줘.

예:
- symbol
- side
- quantity
- order_type
- limit_price
- extended_hours
- account_no_masked
- broker_environment

조건:
- 시장가 주문은 금지
- 지정가 주문만 허용
- live trading이면 차단
- KIS_ENV가 paper가 아니면 차단
- 계좌번호 원문은 출력하지 말고 마스킹만 사용

### 4. 주문 안전 guard 추가

KIS 주문 흐름에 아래 guard를 적용해줘.

- TRADING_MODE=paper만 허용
- LIVE_TRADING_ENABLED=false 확인
- ALLOW_MARKET_ORDERS=false 확인
- KIS_ENV=paper 확인
- order_type이 market이면 거절
- quantity가 0 이하이면 거절
- limit_price가 없으면 거절
- stale quote면 거절
- kill switch가 켜져 있으면 거절

### 5. `/paper/status` 또는 status에 주문 준비 상태 추가

가능하면 아래 상태를 추가해줘.

- kis_order_entry_ready
- kis_order_entry_mode: disabled | paper_guarded | not_implemented
- kis_order_methods_fail_closed: true
- live_trading_enabled: false
- allow_market_orders: false
- secret_exposed: false

실제 app key, app secret, 계좌번호 원문은 절대 출력하지 마.

### 6. 테스트 추가

아래 테스트를 추가해줘.

1. KIS place_order가 실주문을 보내지 않고 fail-closed 되는지
2. KIS cancel_order가 실취소를 보내지 않고 fail-closed 되는지
3. KIS replace_order가 실정정을 보내지 않고 fail-closed 되는지
4. market order가 거절되는지
5. limit_price 없는 주문이 거절되는지
6. live trading true이면 거절되는지
7. KIS_ENV가 paper가 아니면 거절되는지
8. Strategy가 KIS adapter를 직접 호출하지 않는지
9. OMS 경로를 우회하지 않는지
10. status에 secret/account 원문이 노출되지 않는지
11. 기존 74개 테스트가 계속 통과하는지

## 수정 가능 파일

필요하면 아래 파일을 수정해도 된다.

- projects/paper-trading/app/broker/kis.py
- projects/paper-trading/app/broker/base.py
- projects/paper-trading/app/oms/*
- projects/paper-trading/app/risk/*
- projects/paper-trading/app/api/routes.py
- projects/paper-trading/app/api/server.py
- projects/paper-trading/app/config/*
- projects/paper-trading/app/models/*
- projects/paper-trading/tests/*
- projects/paper-trading/README.md
- docs/ai/jobs/mvp-008/patch.md

프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.

## 금지 사항

- 실제 KIS endpoint를 추측해서 만들지 마.
- TR ID를 추측해서 넣지 마.
- 실제 주문 전송 코드를 만들지 마.
- live trading을 활성화하지 마.
- 시장가 주문을 허용하지 마.
- app key, app secret, 계좌번호 원문을 코드/문서/로그/test output에 쓰지 마.
- `.env` 파일을 Git에 추가하지 마.
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