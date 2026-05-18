# 작업 ID
mvp-022

# 작업명
.env 자동 로딩 및 KIS 설정 표시 확인

현재 paper trading 대시보드는 정상으로 열린다.

확인된 상태:
- /dashboard 접속 성공
- mode = paper
- live_enabled = false
- market_orders_allowed = false
- kis_order_dry_run = true
- secret_exposed = false

문제:
KIS 관련 값이 false로 표시된다.

현재 화면:
- kis_config_loaded = false
- kis_authenticated = false
- kis_account_loaded = false
- kis_market_data_available = false
- kis_order_entry_ready = false

목표:
서버 실행 시 `.env` 파일을 자동으로 읽어서 KIS 설정이 로드되게 해줘.

## 원하는 결과

`.env`에 아래 값이 있으면:

- KIS_ENV
- KIS_ACCOUNT_NO
- KIS_APP_KEY
- KIS_APP_SECRET

대시보드와 `/paper/status`에서 아래처럼 보여야 한다.

- kis_config_loaded = true
- account_no_masked = 마스킹된 계좌번호
- secret_exposed = false

단, 아직 실제 KIS 인증 HTTP가 완전히 연결되지 않았으면 아래는 false여도 된다.

- kis_authenticated = false
- kis_account_loaded = false
- kis_market_data_available = false
- kis_order_entry_ready = false

## 보안 조건

절대 노출 금지:
- KIS_APP_KEY 원문
- KIS_APP_SECRET 원문
- KIS_ACCOUNT_NO 원문
- access token
- .env 전체 내용

허용:
- account_no_masked
- kis_config_loaded true/false
- secret_exposed false

## 구현 조건

1. 서버 시작 시 `.env`를 자동 로딩해줘.
2. 현재 작업 디렉터리가 `projects/paper-trading`이면 그 안의 `.env`를 읽어줘.
3. `.env`가 없으면 기존처럼 안전하게 false로 표시해줘.
4. `.env.example`에는 placeholder만 유지해줘.
5. `.env`는 Git에 추가하지 마.
6. `.gitignore`에 `.env`, `.env.*`, `!.env.example` 규칙이 유지되는지 확인해줘.
7. secret이 repr, status, log, test output에 노출되지 않게 해줘.

## 서버 실행 편의성

가능하면 README에 아래 실행 방법을 추가해줘.

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m uvicorn app.api.server:create_app --factory --host 0.0.0.0 --port 8000

.env가 자동 로딩되므로 매번 KIS 환경변수를 export하지 않아도 된다고 설명해줘.

단, 안전 기본값은 계속 유지해야 한다.

TRADING_MODE=paper
LIVE_TRADING_ENABLED=false
ALLOW_MARKET_ORDERS=false
KIS_ORDER_DRY_RUN=true
테스트 요구사항

아래 테스트를 추가하거나 갱신해줘.

.env가 있으면 KIS config가 로드되는지
.env가 없어도 서버가 안전하게 실행되는지
app secret이 status에 노출되지 않는지
account number 원문이 status에 노출되지 않는지
account_no_masked만 표시되는지
live trading 기본값 false 유지
market orders 기본값 false 유지
KIS_ORDER_DRY_RUN 기본값 true 유지
기존 테스트 계속 통과
수정 가능 파일

필요하면 아래 파일을 수정해도 된다.

projects/paper-trading/app/config.py
projects/paper-trading/app/api/server.py
projects/paper-trading/app/api/routes.py
projects/paper-trading/tests/*
projects/paper-trading/README.md
projects/paper-trading/.env.example
projects/paper-trading/.gitignore
docs/ai/jobs/mvp-022/patch.md
금지 사항
실제 KIS app key, app secret, 계좌번호를 코드/문서/로그에 쓰지 마
.env를 Git에 추가하지 마
live trading을 활성화하지 마
시장가 주문을 허용하지 마
실전 주문 기능을 만들지 마
KIS endpoint/TR ID/payload를 추측하지 마
auth, payment, production infra, database migrations는 건드리지 마
git commit, push, merge는 자동화하지 마
검증

아래를 실행해줘.

cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider

서버 실행 후 확인:

curl http://127.0.0.1:8000/paper/status

기대:

kis_config_loaded가 true
secret_exposed가 false
계좌번호 원문 노출 없음
완료 후 patch.md에 정리
어떤 파일을 수정했는지
.env 자동 로딩 방식
KIS 설정 표시 방식
secret/account가 노출되지 않는지
live trading이 계속 비활성인지
market order가 계속 금지인지
테스트 결과
서버 실행 방법
추가 조건
승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
필요한 경우에만 최소한의 질문을 해.

이 작업 끝나면 대시보드에서:

```text
kis_config_loaded = true
account_no_masked = *******
secret_exposed = false