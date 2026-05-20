# 작업 ID
paper-use-ready-001

# 작업명
Paper trading 실제 사용 준비 — 서버 실행 / 대시보드 / dry-run / paper order / KIS 상태 / 테스트 / git 상태 통합 점검

현재 paper trading 시스템은 여러 작업을 통해 많은 기능이 구현되었다.

현재 구현된 것으로 보는 범위는 다음과 같다.

- paper trading 기본 구조
- PaperEngine
- PaperBroker
- OMS
- RiskEngine
- PaperAccount
- PaperJournal
- Fill 모델
- Portfolio / PnL
- KIS 설정 로딩
- KIS OAuth
- KIS 시세 Quote 매핑
- KIS 계좌 / 잔고 / 포지션 조회
- KIS 모의 주문 place_order
- KIS 모의 주문 cancel / replace
- KIS query support
- dashboard UI
- dry-run runner
- dry-run report analyzer
- Korean dashboard UX
- live validation readiness dashboard
- e2e tests
- runtime soak validation

문제는 기능은 많이 만들어졌지만, 실제 사용자가 매번 명령어를 많이 입력해야 하고, 서버 실행 / 대시보드 확인 / dry-run 실행 / paper order simulation / report 확인 / git 상태 확인 흐름이 아직 복잡하다는 점이다.

이번 작업의 목표는 시스템을 “개발 중인 코드”가 아니라 “실제로 매일 켜서 paper trading 검증에 사용할 수 있는 상태”로 정리하는 것이다.

## 목표

- 서버 실행을 간단하게 만든다.
- 서버 중지 / 재시작 / 상태 확인을 간단하게 만든다.
- 대시보드 접속 주소와 사용법을 명확히 정리한다.
- dry-run 시작 / tick / 중지 / 분석 흐름을 초보자도 실행할 수 있게 만든다.
- paper order simulation을 대시보드와 스크립트 양쪽에서 확인할 수 있게 한다.
- KIS 설정 / 인증 / 시세 / 계좌 / 주문 준비 상태를 한 화면에서 확인할 수 있게 한다.
- 테스트 실행과 안전 grep 실행을 하나의 점검 명령으로 묶는다.
- git status가 clean인지 확인하고, dirty가 있으면 어떤 작업 잔재인지 분류한다.
- 사용자가 실제 paper trading 검증을 시작하기 전에 봐야 할 최종 체크리스트를 만든다.
- Codex 작업 후 Claude 검증 요청 프롬프트를 patch.md에 반드시 포함한다.
- Claude 리뷰가 REQUEST CHANGES 또는 BLOCK일 때만 사용할 follow-up Codex 수정 프롬프트 작성 규칙을 patch.md에 포함한다.

## 구현 범위

이번 작업은 운영 편의성과 점검 자동화 작업이다.

필요하면 아래 범위에서 수정하거나 추가한다.

- 서버 실행 스크립트
- 서버 중지 스크립트
- 서버 재시작 스크립트
- 서버 상태 확인 스크립트
- 전체 smoke check 스크립트
- dry-run 실행 스크립트
- report 분석 스크립트
- dashboard read-only 상태 표시 보강
- README / RUNBOOK / 사용 가이드
- ops final audit 문서
- 테스트 보강

## 사용자가 최종적으로 할 수 있어야 하는 것

작업 완료 후 사용자는 아래 명령만으로 운영할 수 있어야 한다.

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading

./scripts/server_start.sh
./scripts/server_status.sh
./scripts/smoke_use_ready.sh
./scripts/server_stop.sh

또는 이미 기존 script 구조가 있다면 그 구조에 맞춰 아래 기능을 제공한다.

./scripts/start_server.sh
./scripts/stop_server.sh
./scripts/restart_server.sh
./scripts/status.sh
./scripts/smoke_check.sh
./scripts/dry_run_tick.sh
./scripts/analyze_report.sh

스크립트 이름은 현재 프로젝트 구조에 맞춰 결정하되, README에 정확히 적는다.

서버 실행 기준

서버 실행 시 기본 운영 기준은 아래와 같다.

TRADING_MODE=paper
LIVE_TRADING_ENABLED=false
ALLOW_MARKET_ORDERS=false
KIS_ORDER_DRY_RUN=true
KIS 설정은 .env에서 읽되 값은 출력하지 않는다.
.env가 없어도 서버는 안전하게 뜨고, KIS 상태는 미설정으로 표시한다.
서버는 tmux 세션 paper-server에서 실행할 수 있어야 한다.
이미 paper-server가 떠 있으면 중복 실행하지 않거나 재시작 절차를 안내한다.
서버 상태 확인 시 /paper/status, /ops/status, /ops/preflight를 확인한다.
대시보드 확인 기준

대시보드는 아래 주소에서 확인 가능해야 한다.

http://127.0.0.1:8000/dashboard

대시보드에서 아래 항목을 확인할 수 있어야 한다.

1. 안전 상태
mode
live_enabled
market_orders_allowed
kis_order_dry_run
secret_exposed
kill_switch_engaged
live_validation_ready 또는 동등한 준비 상태
2. KIS 상태
kis_config_loaded
kis_authenticated
kis_account_loaded
kis_positions_loaded
kis_cash_balance_loaded
kis_market_data_available
kis_order_entry_ready
kis_order_submission_available
kis_cancel_available
kis_replace_available
kis_open_orders_available
kis_fills_available
account_no_masked
kis_last_error
3. Paper 계좌 상태
cash by currency
positions
market value
realized PnL
unrealized PnL
recent orders
recent fills
recent trades
journal 상태
paper engine 상태
4. Dry-run 상태
dry_run_running
started_at
last_tick_at
ticks_total
candidates_seen
candidates_blocked
dry_run_orders_created
dry_run_orders_rejected
errors_total
last_error
5. 운영 버튼

대시보드 버튼은 기존 safe endpoint만 호출한다.

상태 새로고침
Dry-run 시작
Tick 1회 실행
Dry-run 중지
리포트 분석
최신 리포트 보기
예시 paper simulation 실행
Dry-run 점검 흐름

아래 흐름을 스크립트 또는 smoke check에서 확인한다.

/paper/dry-run/status 확인
/paper/dry-run/start 실행
/paper/dry-run/tick 1회 실행
/paper/dry-run/status 재확인
/reports/dry-run/analyze 실행
/reports/dry-run/latest 확인
/paper/dry-run/stop 실행

점검 결과는 사람이 보기 쉽게 출력한다.

예시 출력:

[OK] server is running
[OK] paper status loaded
[OK] dry-run started
[OK] dry-run tick completed
[OK] report analyze completed
[OK] latest report found
[OK] dry-run stopped
Paper order simulation 점검 흐름

아래 흐름을 확인한다.

예시 Quote 또는 기존 dashboard demo order를 사용한다.
Strategy 또는 simulation endpoint가 non-executable intent를 만든다.
RiskEngine이 평가한다.
OMS가 승인된 intent만 paper order로 만든다.
PaperBroker가 paper fill을 만든다.
PaperEngine이 cash / position / journal을 갱신한다.
Dashboard에 결과가 표시된다.

점검 결과에는 아래를 포함한다.

accepted
filled
rejection_reason
risk_result
order
fills
cash_before
cash_after
positions
realized_pnl
safety_flags
summary_ko
KIS 상태 점검 흐름

KIS 상태 점검은 read-only로 수행한다.

확인할 값:

KIS config loaded 여부
account_no_masked 표시 여부
secret_exposed=false 여부
OAuth 인증 상태
market data availability
account / positions / cash availability
order entry readiness
order submission availability
cancel / replace availability
open orders / fills availability

KIS 상태가 false여도 시스템은 fail-closed 상태로 표시되어야 한다.

테스트 및 안전 점검

아래 명령을 실행하는 통합 점검 스크립트를 만든다.

cd /root/ai-dev-center/projects/ai-team/projects/paper-trading

.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider

추가로 아래 성격의 안전 grep을 수행한다.

외부 HTTP 라이브러리 import 여부
Strategy가 KIS를 직접 import하는지 여부
Agent/LLM이 broker를 직접 호출하는지 여부
live trading 활성화 코드 여부
market order guard 우회 여부
OrderType.STOP 도입 여부
FX 변환 함수 도입 여부
secret 문자열 노출 여부
.env가 git에 포함되는지 여부

결과는 patch.md에 요약한다.

Git 상태 점검

아래 명령을 실행하고 결과를 정리한다.

cd /root/ai-dev-center/projects/ai-team
git status --short
git log --oneline -10

결과 기준:

clean이면 clean이라고 명시한다.
dirty가 있으면 파일별로 분류한다.
어떤 파일은 커밋 대상인지, 어떤 파일은 보류인지 제안한다.
git add -A를 사용하지 않는 staging 원칙을 README 또는 patch.md에 적는다.
자동 commit / push / merge는 작업 범위에 포함하지 않는다.
README / RUNBOOK 업데이트

README 또는 별도 문서에 아래 내용을 추가한다.

초보자용 실행 순서
PuTTY 접속
서버 시작
브라우저에서 dashboard 접속
상태 확인
dry-run 시작
tick 실행
report 분석
paper simulation 실행
결과 확인
서버 중지
브라우저 접속 안내

PuTTY 터널을 사용할 경우:

Source port: 8000
Destination: 127.0.0.1:8000

브라우저 주소:

http://127.0.0.1:8000/dashboard
문제 해결

아래 상황별 해결 방법을 적는다.

curl: Failed to connect to 127.0.0.1:8000
/dashboard가 Not Found
JSON만 보임
kis_config_loaded=false
secret_exposed=true
dry-run not running
422 body missing
409 conflict
pytest가 안 돌아감
venv가 없음
git status dirty
산출물

아래 파일을 작성 또는 업데이트한다.

docs/ai/jobs/paper-use-ready-001/patch.md
docs/ai/jobs/paper-use-ready-001/status.md
projects/paper-trading/README.md
필요한 경우 projects/paper-trading/docs/RUNBOOK.md
필요한 경우 projects/paper-trading/scripts/*.sh
필요한 경우 dashboard 관련 read-only UI 파일
필요한 경우 테스트 파일
완료 기준
서버 시작 / 중지 / 재시작 / 상태 확인 명령이 명확하다.
대시보드 접속 주소가 명확하다.
smoke check 스크립트가 동작한다.
dry-run 흐름이 한 번에 점검된다.
paper order simulation 흐름이 확인된다.
KIS 상태가 안전하게 표시된다.
테스트 전체가 통과한다.
안전 grep 결과가 정리된다.
git status가 정리된다.
README/RUNBOOK에 초보자용 실행 절차가 있다.
dashboard나 status에 secret/account/token 원문이 노출되지 않는다.
patch.md에 Claude 검증 요청 프롬프트가 포함된다.
patch.md에 Claude 리뷰가 REQUEST CHANGES/BLOCK일 때만 사용할 follow-up Codex 수정 프롬프트 작성 규칙이 포함된다.
Codex 작업 후 patch.md에 포함할 Claude 검증 요청 프롬프트

Codex는 작업 완료 후 patch.md 맨 아래에 아래 형식의 Claude 검증 요청 프롬프트를 작성한다.

Use prompts/claude.md.

Project directory: /root/ai-dev-center/projects/ai-team
Job ID: paper-use-ready-001
Job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/paper-use-ready-001

Review the paper-use-ready-001 implementation.

Read:
- docs/ai/jobs/paper-use-ready-001/request.ko.md
- docs/ai/jobs/paper-use-ready-001/plan.md
- docs/ai/jobs/paper-use-ready-001/codex-task.md
- docs/ai/jobs/paper-use-ready-001/patch.md

Review the current diff for:
- projects/paper-trading/scripts/
- projects/paper-trading/README.md
- projects/paper-trading/docs/
- projects/paper-trading/app/api/routes.py
- projects/paper-trading/app/static/dashboard.html
- projects/paper-trading/tests/

Review focus:
1. Server start/stop/status workflow is beginner friendly.
2. Dashboard access instructions are correct.
3. Dry-run smoke flow works.
4. Paper order simulation check works.
5. KIS status is shown safely.
6. No app key, app secret, account number, token, Bearer token, or .env contents are exposed.
7. Live trading remains disabled.
8. Market order guard remains intact.
9. No real broker order is sent by smoke checks.
10. Tests pass.
11. Git status guidance is safe and does not recommend git add -A.
12. Scope stayed within paper-use-ready-001.

Verdict must be one of:
APPROVE
REQUEST CHANGES
BLOCK.

If verdict is REQUEST CHANGES or BLOCK, write a Follow-up Codex Prompt that fixes only the required issues.
Do not expand scope.

Do not commit, push, merge, deploy, or run arbitrary shell commands.
Claude 리뷰 결과에 따른 follow-up 규칙

Claude 리뷰가 APPROVE이면 추가 Codex 프롬프트를 만들지 않는다.

Claude 리뷰가 REQUEST CHANGES 또는 BLOCK이면 review.md 안에 Follow-up Codex Prompt를 작성한다.

그 Follow-up Codex Prompt에는 아래가 포함되어야 한다.

읽어야 할 파일:
request.ko.md
plan.md
codex-task.md
patch.md
review.md
Required Fixes만 반영하라는 지시
원래 작업 범위 밖으로 확장하지 말라는 지시
테스트 재실행 명령
patch.md 또는 review-fix.patch.md 업데이트 지시
자동 commit / push / merge / deploy를 하지 않는다는 운영 기준
secrets / .env / auth / payment / production infra 수정 없이 진행한다는 기준
추가 조건
승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
필요한 경우에만 최소한의 질문을 해.