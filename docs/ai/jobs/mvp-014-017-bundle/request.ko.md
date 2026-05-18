# 작업 ID
mvp-014-017-bundle

# 작업명
KIS 공식 문서값 정리 + HTTP 인증/계좌/시세/모의투자 주문 실제 연결

토큰과 작업 단계를 줄이기 위해 아래 작업을 하나로 묶어서 진행해줘.

- mvp-014: KIS 공식 문서값 정리
- mvp-015: KIS OAuth 인증 실제 HTTP 구현
- mvp-016: KIS 계좌 / 잔고 / 포지션 / 시세 실제 조회 구현
- mvp-017: KIS 모의투자 주문 HTTP 연결

현재 목표는 실전거래가 아니라 KIS 모의투자 / paper trading 검증이다.
live trading은 절대 활성화하지 않는다.

## 현재 상태

이미 완료된 것:

- paper-trading 프로젝트 기본 구조
- KIS 설정 구조
- .env 기반 KIS 설정 로딩
- KIS Auth / Account / MarketData skeleton
- KIS 주문 dry-run / fail-closed 구조
- /paper/status KIS 상태 표시
- secret/account/token masking
- RiskEngine / OMS / BrokerAdapter 경계
- 프리마켓 갭 + 거래량 돌파 전략
- 테스트 126 passed 상태

## 이번 통합 목표

공식 KIS 문서값을 확인할 수 있는 범위에서만 실제 HTTP 연결을 구현한다.

구현 대상:

1. KIS OAuth 인증 실제 HTTP 연결
2. KIS token 저장 / 만료 / refresh 구조
3. KIS 계좌 / 잔고 / 포지션 조회
4. KIS 미국주식 또는 해외주식 시세 조회
5. KIS 모의투자 지정가 주문
6. KIS 모의투자 주문 취소
7. KIS 모의투자 주문 정정
8. KIS 모의투자 미체결 주문 조회
9. KIS 모의투자 체결 조회
10. KIS 주문 상태 조회
11. 내부 모델 변환
12. /paper/status 상태 보강
13. 테스트 추가

## 가장 중요한 원칙

KIS endpoint, path, TR ID, header, payload는 공식 문서 기준으로만 구현해야 한다.

절대 추측하지 마.

공식 문서값이 repo 안에 없거나 확인할 수 없으면:

1. 해당 HTTP 기능은 구현하지 않는다.
2. 기존 dry-run / fail-closed 상태를 유지한다.
3. docs/kis/MISSING_OFFICIAL_VALUES.md 파일을 만들어서 필요한 공식 문서값 목록을 정리한다.
4. patch.md에 “공식 KIS 문서값 부족으로 실제 HTTP 연결 보류”라고 명확히 적는다.
5. 테스트는 fail-closed 동작을 검증한다.

## 공식 문서값 확인 대상

아래 값이 공식 문서 또는 repo 내부 문서에서 확인되는 경우에만 구현해라.

### OAuth

- 모의투자 base URL
- OAuth token endpoint
- OAuth refresh endpoint, 존재하는 경우
- HTTP method
- request headers
- request body fields
- response token field
- token expires field

### 해외주식 / 미국주식 계좌

- 해외주식 잔고 endpoint
- 해외주식 잔고 TR ID
- 해외주식 포지션 TR ID
- 현금 / 예수금 조회 TR ID
- request query/body fields
- response fields

### 해외주식 / 미국주식 시세

- 해외주식 현재가 endpoint
- 해외주식 현재가 TR ID
- bid / ask / last price fields
- quote timestamp field
- stale quote 판단 가능 필드

### 모의투자 주문

- 모의투자 해외주식 주문 endpoint
- 모의투자 해외주식 주문 TR ID
- 지정가 주문 payload fields
- 주문 response broker_order_id field
- 주문 취소 endpoint / TR ID
- 주문 정정 endpoint / TR ID
- 미체결 조회 endpoint / TR ID
- 체결 조회 endpoint / TR ID
- 주문 상태 조회 endpoint / TR ID

## 구현 조건

공식 문서값이 확인된 항목만 실제 HTTP로 연결해라.

확인되지 않은 항목은 기존처럼 fail-closed 또는 dry-run 상태로 둬라.

절대 하지 말 것:

- KIS endpoint 추측
- TR ID 추측
- payload 추측
- 실전투자 endpoint 연결
- 실전 주문 연결
- market order 허용
- live trading 활성화
- app key / app secret / account number / token 출력
- .env Git 추가

## 보안 조건

KIS 실제 값은 .env에서만 읽는다.

절대 노출 금지:

- KIS_APP_KEY
- KIS_APP_SECRET
- KIS_ACCOUNT_NO 원문
- access token
- refresh token

허용:

- account_no_masked
- secret_exposed: false
- token_loaded: true/false
- token_expires_in_seconds 같은 상대값

.env.example에는 placeholder만 둔다.

## 주문 안전 조건

반드시 아래 흐름을 유지해라.

Strategy
→ RiskEngine
→ OMS
→ BrokerAdapter
→ KisBroker

금지:

- Strategy가 KIS 직접 호출
- Agent/LLM이 KIS 직접 호출
- OMS 우회
- RiskEngine 우회
- Strategy나 Agent가 executable order 직접 생성

## KIS 주문 guard

KIS 주문 전 반드시 확인한다.

- TRADING_MODE=paper
- LIVE_TRADING_ENABLED=false
- ALLOW_MARKET_ORDERS=false
- KIS_ENV=paper
- KIS_ORDER_DRY_RUN=true면 HTTP 전송 금지
- market order 거절
- quantity > 0
- limit_price 존재
- stale quote 아님
- kill switch off
- RiskEngine 승인
- OMS idempotency 통과

하나라도 실패하면 주문 거절.

## dry-run 정책

기본값은 계속 dry-run true로 둔다.

```env
KIS_ORDER_DRY_RUN=true