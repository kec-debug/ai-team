# 작업 ID
mvp-006-1

# 작업명
KIS Open API 모의투자 연결 준비

미국주식 자동 페이퍼매매 시스템에 KIS Open API 모의투자 연결을 준비해줘.

현재 목표는 실전매매가 아니라 paper trading / 모의투자 자동화다.
live trading은 절대 활성화하지 않는다.

## 현재 상황

KIS 모의투자 계좌, app key, app secret은 `.env`에 저장할 예정이다.

중요:
- 실제 계좌번호, app key, app secret 값을 코드나 문서에 절대 쓰지 마.
- `.env`에서만 읽게 해.
- `.env.example`에는 placeholder만 넣어.
- `.env`는 Git에 올라가면 안 된다.
- `.gitignore`에 `.env`, `.env.*`, `!.env.example` 규칙이 있는지 확인해.

## 이번 작업 목표

이번 mvp-006에서는 KIS Open API를 바로 실주문까지 연결하지 않는다.

우선 아래만 구현해줘.

1. KIS 모의투자 환경 설정 구조 만들기
2. `.env`에서 KIS 설정값을 읽는 구조 만들기
3. KIS Broker Adapter 골격 만들기
4. KIS 모의투자 / 실전투자 환경 분리 구조 만들기
5. 인증 토큰 관리 인터페이스 준비
6. 계좌 조회 인터페이스 준비
7. 해외주식 시세 조회 인터페이스 준비
8. 주문 / 취소 / 정정 인터페이스는 아직 실제 실행하지 말고 TODO boundary만 만들기
9. live trading 차단 guard 유지
10. paper trading 경로가 깨지지 않는지 테스트 추가

## KIS 설정값

실제 값은 `.env`에 있다고 가정해.

필요한 환경변수 이름은 아래처럼 사용해줘.

```env
TRADING_MODE=paper
LIVE_TRADING_ENABLED=false
ALLOW_MARKET_ORDERS=false

KIS_ENV=paper
KIS_ACCOUNT_NO=your_kis_paper_account_no
KIS_APP_KEY=your_kis_app_key
KIS_APP_SECRET=your_kis_app_secret

주의:

위 값은 예시다.
실제 key/secret/account 값은 출력하지 마.
patch.md, review.md, 로그에도 실제 값이 나오면 안 된다.
구현 조건

반드시 지켜줘.

KIS 실제 endpoint를 추측해서 만들지 마.
공식 문서 확인 없이 임의 URL이나 TR ID를 하드코딩하지 마.
아직 실제 주문 전송 코드는 만들지 마.
주문 관련 메서드는 interface / TODO / fail-closed 형태로 둬.
실계좌 주문 가능성이 있는 코드는 만들지 마.
live trading은 계속 비활성 상태로 유지해.
시장가 주문은 금지 상태를 유지해.
모든 주문은 Strategy → RiskEngine → OMS → Broker Adapter 흐름을 유지해야 해.
Strategy가 KIS adapter를 직접 호출하면 안 된다.
Agent 또는 LLM이 직접 주문하면 안 된다.
구현 범위

가능하면 아래 파일 또는 현재 프로젝트 구조에 맞는 파일을 수정/생성해줘.

broker/kis_paper.py 또는 app/adapters/brokers/kis.py
broker/broker_interface.py 또는 app/adapters/brokers/base.py
config/settings.py 또는 app/core/config.py
.env.example
README.md
docs/runbook.md 또는 docs/architecture.md
tests/test_kis_config.py
tests/test_broker_interface.py

실제 프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.

KIS Adapter에 필요한 메서드

아래 메서드 골격을 준비해줘.

authenticate()
refresh_token()
get_account()
get_positions()
get_quote(symbol)
get_open_orders()
place_order()
cancel_order()
replace_order()
healthcheck()

단:

place_order(), cancel_order(), replace_order()는 아직 실제 주문 전송하지 마.
paper mode 또는 not implemented / fail-closed 방식으로 둬.
실제 endpoint, TR ID, payload는 TODO로 남겨.
보안 체크

아래를 반드시 확인해줘.

.env는 Git에 올라가지 않는다.
.env.example에는 placeholder만 있다.
실제 KIS key/secret/account가 코드에 없다.
patch.md 또는 로그에 secret이 출력되지 않는다.
settings/config 객체가 secret을 그대로 repr/logging하지 않는다.
git diff에 실제 secret이 포함되지 않는다.
API 또는 상태 확인

가능하면 /paper/status 또는 기존 status endpoint에 아래 정보를 추가해줘.

broker type: kis 또는 paper_stub
broker environment: paper
live trading enabled: false
market orders allowed: false
kis config loaded: true/false
kis secret exposed: false

단, app key/app secret 값 자체는 절대 출력하지 마.

테스트 요구사항

테스트를 추가해줘.

.env 기반 KIS config 로딩 테스트
.env.example에 실제 secret이 없는지 확인
live trading 기본값 false 확인
market order 기본 금지 확인
KIS adapter가 BrokerInterface를 만족하는지 확인
place_order가 아직 실주문을 실행하지 않는지 확인
config/status 출력에 app secret이 노출되지 않는지 확인
paper trading 기존 테스트가 깨지지 않는지 확인
검증

가능하면 아래를 실행해줘.

python -m compileall app tests
python -m pytest -p no:cacheprovider

만약 현재 프로젝트가 Python 구조가 아니거나 다른 테스트 명령을 사용한다면,
현재 repo 구조에 맞는 안전한 검증 명령을 실행하고 patch.md에 이유를 적어줘.

완료 후 patch.md에 정리할 내용
어떤 파일을 수정했는지
KIS 설정 구조가 어떻게 되었는지
.env와 .env.example 사용 방식
실제 key/secret/account가 노출되지 않는지
KIS adapter에서 무엇이 TODO인지
live trading이 계속 차단되어 있는지
어떤 테스트를 실행했는지
다음 mvp에서 무엇을 하면 되는지
금지 사항
실제 KIS app key, app secret, 계좌번호를 코드에 쓰지 마.
실계좌 주문 기능을 만들지 마.
live trading을 true로 바꾸지 마.
시장가 주문을 허용하지 마.
KIS endpoint나 TR ID를 추측해서 만들지 마.
브로커 API를 Strategy에서 직접 호출하게 만들지 마.
.env 파일을 Git에 추가하지 마.
auth, payment, production infra, database migrations는 건드리지 마.
git commit, push, merge는 자동화하지 마.
추가 조건
승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
필요한 경우에만 최소한의 질문을 해.