# 작업 ID
mvp-007

# 작업명
KIS Open API 모의투자 인증 / 계좌 / 시세 연결

미국주식 자동 페이퍼매매 시스템에 KIS Open API 모의투자 연결을 진행해줘.

현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 연결 검증이다.
live trading은 절대 활성화하지 않는다.

## 현재 전제

mvp-006에서 KIS 설정 구조와 Broker Adapter 골격을 준비했다.

이번 mvp-007에서는 가능한 범위 안에서 아래 기능을 연결한다.

1. KIS 모의투자 인증 토큰 발급 연결
2. 토큰 refresh / 만료 처리 구조
3. KIS 모의투자 계좌 정보 조회
4. KIS 해외주식 또는 미국주식 시세 조회 구조
5. Broker healthcheck 강화
6. `/paper/status` 또는 기존 status endpoint에 KIS 연결 상태 표시
7. 실제 주문은 아직 연결하지 않음

## 보안 조건

KIS 모의투자 계좌번호, app key, app secret은 `.env`에 저장되어 있다고 가정한다.

중요:
- 실제 계좌번호, app key, app secret 값을 코드에 쓰지 마.
- patch.md, review.md, 로그, 테스트 출력에 실제 secret을 노출하지 마.
- `.env.example`에는 placeholder만 유지해.
- `.env`는 Git에 추가하지 마.
- 설정 객체 repr/logging에서 app secret이 노출되지 않게 해.
- 테스트에서도 실제 secret 값을 출력하지 마.

## 공식 문서 조건

KIS Open API endpoint, TR ID, payload는 공식 문서 기준으로만 구현해야 한다.

중요:
- 공식 문서나 프로젝트 내 명확한 문서가 없으면 endpoint를 추측해서 만들지 마.
- 확실하지 않은 endpoint, TR ID, header, payload는 TODO로 남겨.
- fake endpoint를 만들지 마.
- 실제 주문 endpoint는 이번 작업에서 구현하지 마.
- 인증 / 계좌조회 / 시세조회도 확실한 공식 정보가 없으면 fail-closed + TODO로 남겨.

## 이번 구현 범위

가능하면 아래 기능을 구현해줘.

### 1. KIS Auth Client

- `.env`에서 아래 값을 읽는다.
  - KIS_ENV
  - KIS_ACCOUNT_NO
  - KIS_APP_KEY
  - KIS_APP_SECRET
- 모의투자 환경인지 확인한다.
- 인증 토큰 발급 메서드를 만든다.
- 토큰 만료 시 refresh 또는 재발급 가능 구조를 만든다.
- 인증 실패 시 fail-closed 한다.
- secret이 로그에 찍히지 않게 한다.

필요 메서드 예시:
- authenticate()
- refresh_token()
- get_access_token()
- is_authenticated()
- clear_token()

### 2. KIS Account Client

- 계좌 정보 조회 골격 또는 실제 연결을 구현한다.
- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
- 계좌번호는 출력 시 마스킹한다.
- 실패 시 주문 가능 상태로 전환하지 않는다.

필요 메서드 예시:
- get_account()
- get_positions()
- get_cash_balance()

### 3. KIS Market Data Client

- 미국주식 시세 조회 구조를 만든다.
- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
- 최소 quote 모델을 반환한다.
- 실패 시 stale / unavailable 상태로 처리한다.

필요 메서드 예시:
- get_quote(symbol)
- get_last_price(symbol)
- healthcheck_market_data()

### 4. KIS Broker Adapter 연결

기존 BrokerAdapter 구조를 유지한다.

- authenticate()
- refresh_token()
- get_account()
- get_positions()
- get_quote()
- healthcheck()

주문 관련 메서드는 아직 실제 전송하지 않는다.

- place_order()
- cancel_order()
- replace_order()

위 주문 메서드는 이번 단계에서 fail-closed 또는 NotImplemented 상태로 둔다.

## 주문 안전 조건

반드시 유지해.

- live trading은 false
- TRADING_MODE는 paper
- 시장가 주문 금지
- 실주문 전송 금지
- Strategy가 KIS Adapter를 직접 호출하지 않음
- Agent/LLM이 직접 주문하지 않음
- 모든 주문은 Strategy → RiskEngine → OMS → BrokerAdapter 경로 유지
- OMS 우회 금지
- RiskEngine 우회 금지

## 상태 API

가능하면 `/paper/status` 또는 기존 `/status`에 아래 정보를 추가해줘.

- broker_type
- broker_environment
- kis_config_loaded
- kis_authenticated
- kis_account_loaded
- kis_market_data_available
- live_trading_enabled
- allow_market_orders
- last_broker_error
- secret_exposed: false

중요:
- app key, app secret, 계좌번호 원문은 절대 출력하지 마.
- 계좌번호는 필요하면 마스킹해서 보여줘.

## 테스트 요구사항

아래 테스트를 추가해줘.

1. `.env` 기반 KIS config 로딩 테스트
2. app secret이 repr/logging/status에 노출되지 않는지 테스트
3. KIS_ENV=paper 기본 동작 테스트
4. live trading 기본 false 테스트
5. 시장가 주문 기본 금지 테스트
6. 인증 client가 secret을 직접 출력하지 않는지 테스트
7. 공식 문서 정보가 없을 때 endpoint를 추측하지 않고 TODO/fail-closed 되는지 테스트
8. 주문 메서드가 아직 실주문을 전송하지 않는지 테스트
9. BrokerAdapter 인터페이스가 깨지지 않는지 테스트
10. `/paper/status` 또는 `/status`에 KIS 상태가 안전하게 표시되는지 테스트

## 수정 가능 파일

필요한 경우 아래 파일을 수정해도 된다.

- app/adapters/brokers/kis.py
- app/adapters/brokers/base.py
- app/core/config.py
- app/api/routes.py
- app/runtime/paper_runner.py
- app/monitoring/status.py
- app/domain/*
- tests/*
- .env.example
- README.md
- docs/architecture.md
- docs/runbook.md

실제 프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.

## 금지 사항

- 실제 KIS app key, app secret, 계좌번호를 코드에 쓰지 마.
- 실제 값을 patch.md, review.md, 로그에 출력하지 마.
- `.env` 파일을 Git에 추가하지 마.
- live trading을 true로 바꾸지 마.
- 실계좌 주문 기능을 만들지 마.
- 주문 endpoint를 연결하지 마.
- KIS endpoint / TR ID / payload를 추측해서 만들지 마.
- 시장가 주문을 허용하지 마.
- 브로커 API를 Strategy에서 직접 호출하게 만들지 마.
- auth, payment, production infra, database migrations는 건드리지 마.
- git commit, push, merge는 자동화하지 마.

## 검증

가능하면 아래를 실행해줘.

- python -m compileall app tests
- python -m pytest -p no:cacheprovider

만약 현재 프로젝트 구조가 Python이 아니거나 테스트 명령이 다르면,
현재 repo 구조에 맞는 안전한 검증 명령을 실행하고 patch.md에 이유를 적어줘.

## 완료 후 patch.md에 정리할 내용

1. 어떤 파일을 수정했는지
2. KIS 인증 구조가 어떻게 되었는지
3. 계좌 조회 구조가 어떻게 되었는지
4. 시세 조회 구조가 어떻게 되었는지
5. 실제 주문 기능이 여전히 비활성인지
6. secret이 노출되지 않는지
7. 어떤 테스트를 실행했는지
8. 공식 문서가 없어 TODO로 남긴 부분
9. 다음 mvp에서 무엇을 하면 되는지

## 다음 단계 예고

mvp-008에서는 KIS 모의투자 주문 흐름을 연결할 예정이다.
단, mvp-008에서도 live trading은 비활성이고, 소액 검증 전까지 실계좌 주문은 금지한다.

## 추가 조건

- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
- 필요한 경우에만 최소한의 질문을 해.