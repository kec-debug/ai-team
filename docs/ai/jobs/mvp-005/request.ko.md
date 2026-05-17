# 작업 ID
mvp-005

# 작업명
프리마켓 갭 + 거래량 돌파 전략 구현

미국주식 자동 페이퍼매매 시스템에서 첫 번째 전략을 구현해줘.

이번 목표는 실전매매가 아니라 paper trading 전략 검증이다.
live trading은 절대 활성화하지 않는다.

## 구현할 전략

전략명:
프리마켓 갭 + 거래량 돌파 전략

목표:
프리마켓에서 전일 종가 대비 크게 상승하고, 거래량이 증가하며, 스프레드가 허용 범위 안에 있는 종목을 paper trading 진입 후보로 만든다.

## 전략 조건

진입 후보 조건:
1. 미국주식 종목이어야 한다.
2. 프리마켓 세션에서만 동작한다.
3. 전일 종가 대비 갭 상승률이 일정 기준 이상이어야 한다.
   - 기본값: 5% 이상
4. 프리마켓 거래량이 일정 기준 이상이어야 한다.
   - 기본값: 100,000주 이상
5. 상대 거래량 또는 거래량 증가 조건을 만족해야 한다.
   - 데이터가 없으면 기본 거래량 조건만 사용해도 된다.
6. 현재가가 단기 고점 또는 premarket high 근처를 돌파하는 후보여야 한다.
7. 스프레드가 너무 넓으면 제외한다.
   - 기본값: 0.3% 이하
8. 시장가 주문은 절대 만들지 않는다.
9. 생성되는 주문 후보는 지정가 주문 기반이어야 한다.
10. 전략은 직접 주문하지 않고 candidate 또는 non-executable order intent까지만 만든다.

## 제외 조건

아래 조건이면 진입 후보에서 제외해줘.

1. 스프레드가 0.3% 초과
2. stale quote
3. 거래량 부족
4. 가격 데이터 부족
5. 프리마켓 세션이 아님
6. live trading 모드
7. RiskEngine 제한에 걸리는 경우
8. 시장가 주문이 필요한 경우

## 주문 안전 조건

반드시 기존 흐름을 유지해줘.

Agent 또는 Strategy
→ RiskEngine
→ OMS
→ Broker Adapter

중요:
- 전략이 Broker Adapter를 직접 호출하면 안 된다.
- 전략이 OMS를 우회하면 안 된다.
- 전략이 executable order를 직접 만들면 안 된다.
- 모든 주문 후보는 RiskEngine을 통과해야 한다.
- OMS만 최종 paper order를 만들 수 있다.
- live trading은 계속 비활성 상태여야 한다.

## 구현 범위

아래를 구현하거나 점검해줘.

1. 프리마켓 갭 + 거래량 돌파 전략 파일 추가 또는 기존 strategy 구조에 연결
2. 전략 입력 schema 정의
   - symbol
   - market
   - session
   - previous_close
   - current_price
   - premarket_high
   - premarket_volume
   - bid
   - ask
   - timestamp
3. 전략 출력 schema 정의
   - symbol
   - passed
   - score
   - reasons
   - blockers
   - suggested_limit_price
   - non_executable_order_intent
4. /paper/run 또는 기존 paper runner에서 이 전략을 사용할 수 있게 연결
5. 전략이 blocked candidate를 주문으로 넘기지 않게 처리
6. RiskEngine과 OMS 경계를 유지
7. 테스트 추가

## 테스트 요구사항

아래 테스트를 추가해줘.

1. 갭 상승률이 기준 이상이면 candidate 통과
2. 갭 상승률이 부족하면 차단
3. 거래량이 부족하면 차단
4. 스프레드가 0.3% 초과면 차단
5. 프리마켓 세션이 아니면 차단
6. stale quote면 차단
7. 전략 결과는 executable order가 아니어야 함
8. 시장가 주문이 생성되지 않아야 함
9. blocked candidate는 OMS로 넘어가지 않아야 함
10. /paper/run 또는 paper runner에서 전략 경로가 깨지지 않아야 함

## 수정 가능 파일

필요한 경우 아래 파일을 수정해도 된다.

- app/strategy/*
- app/runtime/paper_runner.py
- app/api/routes.py
- app/domain/*
- app/risk/*
- tests/*
- README.md
- docs/architecture.md
- docs/runbook.md

단, 실제 구조가 다르면 현재 프로젝트 구조에 맞춰 최소 수정해줘.

## 금지 사항

- 실계좌 주문 기능을 만들지 마.
- live trading을 true로 바꾸지 마.
- 시장가 주문을 허용하지 마.
- 브로커 endpoint를 추측해서 만들지 마.
- API key나 secret을 코드에 넣지 마.
- .env, auth, payment, production infra, database migrations는 건드리지 마.
- git commit, push, merge는 자동화하지 마.
- agent나 LLM이 직접 주문하게 만들지 마.

## 검증

가능하면 아래를 실행해줘.

- python -m compileall app tests
- python -m pytest -p no:cacheprovider

만약 현재 프로젝트가 Python 구조가 아니거나 다른 테스트 명령을 사용한다면, 현재 repo 구조에 맞는 안전한 검증 명령을 사용하고 patch.md에 이유를 적어줘.

## 완료 후 정리

완료 후 patch.md에 아래를 정리해줘.

1. 어떤 파일을 수정했는지
2. 전략 조건이 어떻게 구현됐는지
3. paper trading 경로와 어떻게 연결됐는지
4. live trading이 계속 차단되어 있는지
5. 시장가 주문이 생성되지 않는지
6. 어떤 테스트를 실행했는지
7. 다음 단계로 무엇을 하면 좋은지

## 추가 조건

- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
- 필요한 경우에만 최소한의 질문을 해.