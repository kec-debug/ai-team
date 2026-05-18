
## 2026-05-14T11:41:14.525Z — create-job

```
Ensured job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-009
```

## 2026-05-14T11:41:14.525Z — save-input

```
Saved: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-009/request.ko.md
```

## 2026-05-14T11:41:14.535Z — claude-plan

```
(no output)
```

## 2026-05-14T11:46:19.609Z — create-job

```
Ensured job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-009
```

## 2026-05-14T11:46:19.609Z — save-input

```
Saved: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-009/request.ko.md
```

## 2026-05-14T11:46:19.617Z — claude-plan

```
(no output)
```

## 2026-05-14T11:50:24.617Z — codex-implement

```
(no output)
```

## 2026-05-14T11:50:24.643Z — codex-implement

```
(no output)
```

## 2026-05-14T11:58:49.691Z — save-diff

```
diff --git a/.gitignore b/.gitignore
index 2958a59..7f7fa98 100644
--- a/.gitignore
+++ b/.gitignore
@@ -3,3 +3,6 @@ projects/paper-trading/.env
 .env
 .env.*
 !.env.example
+
+# Imported local reference code - never commit directly
+imports/
diff --git a/docs/ai/jobs/mvp-004/request.ko.md b/docs/ai/jobs/mvp-004/request.ko.md
index 7d9ecf1..dcfaa5c 100644
--- a/docs/ai/jobs/mvp-004/request.ko.md
+++ b/docs/ai/jobs/mvp-004/request.ko.md
@@ -1,10 +1,74 @@
-# 작업 요청
+# 작업 ID
+mvp-004
 
-GUI 파이프라인이 Claude 계획 완료 전에 Codex 단계로 넘어가는 문제를 수정한다.
+# 작업명
+AI 개발팀 GUI 화면 배치 개선
 
-Claude 계획 단계는 plan.md와 codex-task.md가 생성되어야 완료된 것으로 본다.
-Codex 구현 단계는 patch.md가 생성되어야 완료된 것으로 본다.
-Claude 리뷰 단계는 review.md가 생성되어야 완료된 것으로 본다.
+현재 AI 개발팀 브라우저 GUI에서 화면 배치가 불편하다.
 
-전체 파이프라인 버튼은 각 단계의 산출물 파일을 확인한 뒤 다음 단계로 넘어가야 한다.
-승인 대기, 차단, 실패 상태가 감지되면 다음 단계로 넘어가면 안 된다.
+문제점:
+1. 파이프라인 상태 영역이 너무 위에 있어서 핵심 제어 버튼과 시선 흐름이 맞지 않는다.
+2. 승인 / 서비스 제어 / 실시간 출력 영역이 아래쪽에 있어 잘 안 보인다.
+3. 작업 설정 칸이 너무 길어서 화면을 많이 차지한다.
+4. 실제 작업 중에는 승인 버튼, 서비스 제어, 실시간 출력이 더 중요하므로 위쪽에서 바로 보여야 한다.
+
+원하는 변경사항:
+
+1. “파이프라인 상태” 영역을 “Claude → Codex → Claude 전체 실행” 버튼 아래로 내려줘.
+
+2. 아래 영역들을 상단 쪽으로 올려줘.
+   - 승인 / 계속 진행
+   - 거절
+   - 중단
+   - 서비스 제어
+   - 실시간 출력
+
+3. 작업 설정 영역을 더 짧고 컴팩트하게 만들어줘.
+   - 입력칸 높이를 줄여줘.
+   - 필요하면 접기/펼치기 형태로 만들어줘.
+   - 화면에서 너무 많은 공간을 차지하지 않게 해줘.
+
+4. 화면 우선순위를 아래 순서로 재배치해줘.
+   - 상단: 작업 ID / 작업 요청 입력 / 주요 실행 버튼
+   - 그 아래: 승인 / 서비스 제어 / 실시간 출력
+   - 그 아래: 파이프라인 상태
+   - 그 아래: 작업 설정 / 고급 설정 / 산출물 목록
+
+5. Claude + Codex 2-role 구조는 유지해줘.
+   - Gemini Manager, Claude Architect, Claude Reviewer, Git Shell을 다시 노출하지 마.
+   - Claude 계획 생성
+   - Codex 구현 실행
+   - Claude 리뷰 실행
+   - Claude → Codex → Claude 전체 실행
+   이 버튼 구조는 유지해줘.
+
+6. git status와 git diff는 수동 유틸리티 버튼으로만 유지해줘.
+   - commit, push, merge는 자동화하지 마.
+
+7. 반응형 화면도 깨지지 않게 해줘.
+   - 작은 화면에서도 실시간 출력과 승인 버튼이 잘 보여야 한다.
+
+수정 대상:
+- web/public/index.html
+- web/public/app.js
+- web/public/style.css
+- 필요하면 web/server.js
+- README.md 또는 docs/ai/CLAUDE_CODEX_WORKFLOW.md는 변경 내용이 있으면 최소한만 업데이트
+
+금지:
+- 주식 페이퍼매매 로직은 건드리지 마.
+- secrets, .env, auth, payment, production infra, database migrations는 건드리지 마.
+- 임의 shell 명령 입력 기능은 만들지 마.
+- git commit, push, merge는 자동화하지 마.
+
+검증:
+- node --check web/server.js
+- node --check web/public/app.js
+- git diff --stat
+
+완료 후:
+- 어떤 UI 영역을 어디로 옮겼는지
+- 작업 설정 영역을 어떻게 줄였는지
+- Claude + Codex 구조가 유지되는지
+- 테스트 결과가 무엇인지
+patch.md에 정리해줘.
\ No newline at end of file
diff --git a/docs/ai/jobs/mvp-007/local-diff.patch b/docs/ai/jobs/mvp-007/local-diff.patch
index 559f050..ebc5221 100644
--- a/docs/ai/jobs/mvp-007/local-diff.patch
+++ b/docs/ai/jobs/mvp-007/local-diff.patch
@@ -85,6 +85,393 @@ index 7d9ecf1..dcfaa5c 100644
 +- 테스트 결과가 무엇인지
 +patch.md에 정리해줘.
 \ No newline at end of file
+diff --git a/docs/ai/jobs/mvp-007/pipeline.log.md b/docs/ai/jobs/mvp-007/pipeline.log.md
+index 75df48b..5af59ba 100644
+--- a/docs/ai/jobs/mvp-007/pipeline.log.md
++++ b/docs/ai/jobs/mvp-007/pipeline.log.md
+@@ -1477,3 +1477,27 @@ index 0ce1e5d..7d07b26 100644
+ ```
+ (no output)
+ ```
++
++## 2026-05-14T10:53:00.580Z — create-job
++
++```
++Ensured job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-007
++```
++
++## 2026-05-14T10:53:00.588Z — save-input
++
++```
++Saved: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-007/request.ko.md
++```
++
++## 2026-05-14T10:53:00.600Z — claude-plan
++
++```
++(no output)
++```
++
++## 2026-05-14T10:53:00.611Z — codex-implement
++
++```
++(no output)
++```
+diff --git a/docs/ai/jobs/mvp-007/request.ko.md b/docs/ai/jobs/mvp-007/request.ko.md
+index dfd0315..9fc2cdb 100644
+--- a/docs/ai/jobs/mvp-007/request.ko.md
++++ b/docs/ai/jobs/mvp-007/request.ko.md
+@@ -1,227 +1,170 @@
+ # 작업 ID
+-mvp-007
++mvp-008
+ 
+ # 작업명
+-KIS Open API 모의투자 인증 / 계좌 / 시세 연결
++KIS 모의투자 주문 흐름 연결 준비
+ 
+-미국주식 자동 페이퍼매매 시스템에 KIS Open API 모의투자 연결을 진행해줘.
++미국주식 자동 페이퍼매매 시스템에서 KIS 모의투자 주문 흐름을 연결할 준비를 해줘.
+ 
+-현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 연결 검증이다.
++현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 주문 흐름 검증이다.
+ live trading은 절대 활성화하지 않는다.
+ 
+-## 현재 전제
++## 현재 상태
+ 
+-mvp-006에서 KIS 설정 구조와 Broker Adapter 골격을 준비했다.
++mvp-006-1과 mvp-007에서 아래 작업이 완료되었다.
+ 
+-이번 mvp-007에서는 가능한 범위 안에서 아래 기능을 연결한다.
++- paper-trading 프로젝트 기본 구조 생성
++- KIS 설정 구조 준비
++- `.env` 기반 KIS 설정 로딩
++- KIS Broker Adapter 골격
++- KIS Auth / Account / MarketData Client 골격
++- `/paper/status`에 KIS 상태 표시
++- secret/account masking 테스트
++- 74개 테스트 통과
+ 
+-1. KIS 모의투자 인증 토큰 발급 연결
+-2. 토큰 refresh / 만료 처리 구조
+-3. KIS 모의투자 계좌 정보 조회
+-4. KIS 해외주식 또는 미국주식 시세 조회 구조
+-5. Broker healthcheck 강화
+-6. `/paper/status` 또는 기존 status endpoint에 KIS 연결 상태 표시
+-7. 실제 주문은 아직 연결하지 않음
++이번 mvp-008에서는 실제 실계좌 주문이 아니라,
++KIS 모의투자 주문 흐름을 안전하게 연결할 준비를 한다.
+ 
+-## 보안 조건
++## 핵심 목표
+ 
+-KIS 모의투자 계좌번호, app key, app secret은 `.env`에 저장되어 있다고 가정한다.
++Strategy → RiskEngine → OMS → BrokerAdapter → KIS Broker 경로가 유지되도록 하면서,
++KIS 모의투자 주문 메서드의 안전한 경계를 만든다.
+ 
+-중요:
+-- 실제 계좌번호, app key, app secret 값을 코드에 쓰지 마.
+-- patch.md, review.md, 로그, 테스트 출력에 실제 secret을 노출하지 마.
+-- `.env.example`에는 placeholder만 유지해.
+-- `.env`는 Git에 추가하지 마.
+-- 설정 객체 repr/logging에서 app secret이 노출되지 않게 해.
+-- 테스트에서도 실제 secret 값을 출력하지 마.
+-
+-## 공식 문서 조건
+-
+-KIS Open API endpoint, TR ID, payload는 공식 문서 기준으로만 구현해야 한다.
+-
+-중요:
+-- 공식 문서나 프로젝트 내 명확한 문서가 없으면 endpoint를 추측해서 만들지 마.
+-- 확실하지 않은 endpoint, TR ID, header, payload는 TODO로 남겨.
+-- fake endpoint를 만들지 마.
+-- 실제 주문 endpoint는 이번 작업에서 구현하지 마.
+-- 인증 / 계좌조회 / 시세조회도 확실한 공식 정보가 없으면 fail-closed + TODO로 남겨.
+-
+-## 이번 구현 범위
+-
+-가능하면 아래 기능을 구현해줘.
+-
+-### 1. KIS Auth Client
++단, 공식 문서가 확인되지 않은 endpoint, TR ID, payload는 절대 추측해서 구현하지 않는다.
+ 
+-- `.env`에서 아래 값을 읽는다.
+-  - KIS_ENV
+-  - KIS_ACCOUNT_NO
+-  - KIS_APP_KEY
+-  - KIS_APP_SECRET
+-- 모의투자 환경인지 확인한다.
+-- 인증 토큰 발급 메서드를 만든다.
+-- 토큰 만료 시 refresh 또는 재발급 가능 구조를 만든다.
+-- 인증 실패 시 fail-closed 한다.
+-- secret이 로그에 찍히지 않게 한다.
++## 구현할 내용
+ 
+-필요 메서드 예시:
+-- authenticate()
+-- refresh_token()
+-- get_access_token()
+-- is_authenticated()
+-- clear_token()
++### 1. KIS 주문 메서드 경계 정리
+ 
+-### 2. KIS Account Client
++`KisBroker` 또는 현재 구조에 맞는 KIS adapter에 아래 주문 관련 메서드를 정리해줘.
+ 
+-- 계좌 정보 조회 골격 또는 실제 연결을 구현한다.
+-- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
+-- 계좌번호는 출력 시 마스킹한다.
+-- 실패 시 주문 가능 상태로 전환하지 않는다.
+-
+-필요 메서드 예시:
+-- get_account()
+-- get_positions()
+-- get_cash_balance()
+-
+-### 3. KIS Market Data Client
+-
+-- 미국주식 시세 조회 구조를 만든다.
+-- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
+-- 최소 quote 모델을 반환한다.
+-- 실패 시 stale / unavailable 상태로 처리한다.
+-
+-필요 메서드 예시:
+-- get_quote(symbol)
+-- get_last_price(symbol)
+-- healthcheck_market_data()
+-
+-### 4. KIS Broker Adapter 연결
++- place_order()
++- cancel_order()
++- replace_order()
++- get_open_orders()
++- get_fills()
++- get_order_status()
+ 
+-기존 BrokerAdapter 구조를 유지한다.
++조건:
++- 실제 endpoint/TR ID/payload를 추측해서 만들지 마.
++- 공식 문서가 없으면 TODO + fail-closed로 둬.
++- 메서드는 존재하되, 실주문 전송은 아직 하지 마.
++- NotImplementedError 또는 안전한 Rejected 상태를 반환하게 해.
++- 에러 메시지는 secret/account를 노출하지 않아야 한다.
+ 
+-- authenticate()
+-- refresh_token()
+-- get_account()
+-- get_positions()
+-- get_quote()
+-- healthcheck()
++### 2. OMS → KIS Broker 연결 준비
+ 
+-주문 관련 메서드는 아직 실제 전송하지 않는다.
++OMS가 broker adapter를 통해 주문을 보낼 수 있는 구조인지 점검하고,
++필요하면 interface를 정리해줘.
+ 
+-- place_order()
+-- cancel_order()
+-- replace_order()
++중요:
++- Strategy가 KIS를 직접 호출하면 안 된다.
++- Agent/LLM이 KIS를 직접 호출하면 안 된다.
++- OMS를 우회해서 주문하면 안 된다.
++- 모든 주문은 반드시 RiskEngine을 통과해야 한다.
++- OMS만 executable order를 만들 수 있다.
++
++### 3. KIS 모의투자 주문 요청 모델 준비
++
++실제 전송은 하지 말고, 내부 도메인 모델 기준으로 KIS 주문 요청 변환 경계를 만들어줘.
++
++예:
++- symbol
++- side
++- quantity
++- order_type
++- limit_price
++- extended_hours
++- account_no_masked
++- broker_environment
+ 
+-위 주문 메서드는 이번 단계에서 fail-closed 또는 NotImplemented 상태로 둔다.
++조건:
++- 시장가 주문은 금지
++- 지정가 주문만 허용
++- live trading이면 차단
++- KIS_ENV가 paper가 아니면 차단
++- 계좌번호 원문은 출력하지 말고 마스킹만 사용
+ 
+-## 주문 안전 조건
++### 4. 주문 안전 guard 추가
+ 
+-반드시 유지해.
++KIS 주문 흐름에 아래 guard를 적용해줘.
+ 
+-- live trading은 false
+-- TRADING_MODE는 paper
+-- 시장가 주문 금지
+-- 실주문 전송 금지
+-- Strategy가 KIS Adapter를 직접 호출하지 않음
+-- Agent/LLM이 직접 주문하지 않음
+-- 모든 주문은 Strategy → RiskEngine → OMS → BrokerAdapter 경로 유지
+-- OMS 우회 금지
+-- RiskEngine 우회 금지
++- TRADING_MODE=paper만 허용
++- LIVE_TRADING_ENABLED=false 확인
++- ALLOW_MARKET_ORDERS=false 확인
++- KIS_ENV=paper 확인
++- order_type이 market이면 거절
++- quantity가 0 이하이면 거절
++- limit_price가 없으면 거절
++- stale quote면 거절
++- kill switch가 켜져 있으면 거절
+ 
+-## 상태 API
++### 5. `/paper/status` 또는 status에 주문 준비 상태 추가
+ 
+-가능하면 `/paper/status` 또는 기존 `/status`에 아래 정보를 추가해줘.
++가능하면 아래 상태를 추가해줘.
+ 
+-- broker_type
+-- broker_environment
+-- kis_config_loaded
+-- kis_authenticated
+-- kis_account_loaded
+-- kis_market_data_available
+-- live_trading_enabled
+-- allow_market_orders
+-- last_broker_error
++- kis_order_entry_ready
++- kis_order_entry_mode: disabled | paper_guarded | not_implemented
++- kis_order_methods_fail_closed: true
++- live_trading_enabled: false
++- allow_market_orders: false
+ - secret_exposed: false
+ 
+-중요:
+-- app key, app secret, 계좌번호 원문은 절대 출력하지 마.
+-- 계좌번호는 필요하면 마스킹해서 보여줘.
++실제 app key, app secret, 계좌번호 원문은 절대 출력하지 마.
+ 
+-## 테스트 요구사항
++### 6. 테스트 추가
+ 
+ 아래 테스트를 추가해줘.
+ 
+-1. `.env` 기반 KIS config 로딩 테스트
+-2. app secret이 repr/logging/status에 노출되지 않는지 테스트
+-3. KIS_ENV=paper 기본 동작 테스트
+-4. live trading 기본 false 테스트
+-5. 시장가 주문 기본 금지 테스트
+-6. 인증 client가 secret을 직접 출력하지 않는지 테스트
+-7. 공식 문서 정보가 없을 때 endpoint를 추측하지 않고 TODO/fail-closed 되는지 테스트
+-8. 주문 메서드가 아직 실주문을 전송하지 않는지 테스트
+-9. BrokerAdapter 인터페이스가 깨지지 않는지 테스트
+-10. `/paper/status` 또는 `/status`에 KIS 상태가 안전하게 표시되는지 테스트
++1. KIS place_order가 실주문을 보내지 않고 fail-closed 되는지
++2. KIS cancel_order가 실취소를 보내지 않고 fail-closed 되는지
++3. KIS replace_order가 실정정을 보내지 않고 fail-closed 되는지
++4. market order가 거절되는지
++5. limit_price 없는 주문이 거절되는지
++6. live trading true이면 거절되는지
++7. KIS_ENV가 paper가 아니면 거절되는지
++8. Strategy가 KIS adapter를 직접 호출하지 않는지
++9. OMS 경로를 우회하지 않는지
++10. status에 secret/account 원문이 노출되지 않는지
++11. 기존 74개 테스트가 계속 통과하는지
+ 
+ ## 수정 가능 파일
+ 
+-필요한 경우 아래 파일을 수정해도 된다.
++필요하면 아래 파일을 수정해도 된다.
+ 
+-- app/adapters/brokers/kis.py
+-- app/adapters/brokers/base.py
+-- app/core/config.py
+-- app/api/routes.py
+-- app/runtime/paper_runner.py
+-- app/monitoring/status.py
+-- app/domain/*
+-- tests/*
+-- .env.example
+-- README.md
+-- docs/architecture.md
+-- docs/runbook.md
++- projects/paper-trading/app/broker/kis.py
++- projects/paper-trading/app/broker/base.py
++- projects/paper-trading/app/oms/*
++- projects/paper-trading/app/risk/*
++- projects/paper-trading/app/api/routes.py
++- projects/paper-trading/app/api/server.py
++- projects/paper-trading/app/config/*
++- projects/paper-trading/app/models/*
++- projects/paper-trading/tests/*
++- projects/paper-trading/README.md
++- docs/ai/jobs/mvp-008/patch.md
+ 
+-실제 프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.
++프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.
+ 
+ ## 금지 사항
+ 
+-- 실제 KIS app key, app secret, 계좌번호를 코드에 쓰지 마.
+-- 실제 값을 patch.md, review.md, 로그에 출력하지 마.
+-- `.env` 파일을 Git에 추가하지 마.
+-- live trading을 true로 바꾸지 마.
+-- 실계좌 주문 기능을 만들지 마.
+-- 주문 endpoint를 연결하지 마.
+-- KIS endpoint / TR ID / payload를 추측해서 만들지 마.
++- 실제 KIS endpoint를 추측해서 만들지 마.
++- TR ID를 추측해서 넣지 마.
++- 실제 주문 전송 코드를 만들지 마.
++- live trading을 활성화하지 마.
+ - 시장가 주문을 허용하지 마.
+-- 브로커 API를 Strategy에서 직접 호출하게 만들지 마.
++- app key, app secret, 계좌번호 원문을 코드/문서/로그/test output에 쓰지 마.
++- `.env` 파일을 Git에 추가하지 마.
++- Strategy가 KIS를 직접 호출하게 만들지 마.
++- Agent/LLM이 직접 주문하게 만들지 마.
+ - auth, payment, production infra, database migrations는 건드리지 마.
+ - git commit, push, merge는 자동화하지 마.
+ 
+ ## 검증
+ 
+-가능하면 아래를 실행해줘.
+-
+-- python -m compileall app tests
+-- python -m pytest -p no:cacheprovider
+-
+-만약 현재 프로젝트 구조가 Python이 아니거나 테스트 명령이 다르면,
+-현재 repo 구조에 맞는 안전한 검증 명령을 실행하고 patch.md에 이유를 적어줘.
+-
+-## 완료 후 patch.md에 정리할 내용
+-
+-1. 어떤 파일을 수정했는지
+-2. KIS 인증 구조가 어떻게 되었는지
+-3. 계좌 조회 구조가 어떻게 되었는지
+-4. 시세 조회 구조가 어떻게 되었는지
+-5. 실제 주문 기능이 여전히 비활성인지
+-6. secret이 노출되지 않는지
+-7. 어떤 테스트를 실행했는지
+-8. 공식 문서가 없어 TODO로 남긴 부분
+-9. 다음 mvp에서 무엇을 하면 되는지
+-
+-## 다음 단계 예고
+-
+-mvp-008에서는 KIS 모의투자 주문 흐름을 연결할 예정이다.
+-단, mvp-008에서도 live trading은 비활성이고, 소액 검증 전까지 실계좌 주문은 금지한다.
+-
+-## 추가 조건
++아래를 실행해줘.
+ 
+-- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
+-- 필요한 경우에만 최소한의 질문을 해.
+\ No newline at end of file
++```bash
++cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
++.venv/bin/python -m compileall app tests
++.venv/bin/python -m pytest -p no:cacheprovider
+\ No newline at end of file
 diff --git a/web/public/app.js b/web/public/app.js
 index f27f460..d9fc2c2 100644
 --- a/web/public/app.js
diff --git a/docs/ai/jobs/mvp-007/pipeline.log.md b/docs/ai/jobs/mvp-007/pipeline.log.md
index 75df48b..88ef2c1 100644
--- a/docs/ai/jobs/mvp-007/pipeline.log.md
+++ b/docs/ai/jobs/mvp-007/pipeline.log.md
@@ -1477,3 +1477,1869 @@ index 0ce1e5d..7d07b26 100644
 ```
 (no output)
 ```
+
+## 2026-05-14T10:53:00.580Z — create-job
+
+```
+Ensured job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-007
+```
+
+## 2026-05-14T10:53:00.588Z — save-input
+
+```
+Saved: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-007/request.ko.md
+```
+
+## 2026-05-14T10:53:00.600Z — claude-plan
+
+```
+(no output)
+```
+
+## 2026-05-14T10:53:00.611Z — codex-implement
+
+```
+(no output)
+```
+
+## 2026-05-14T10:53:00.621Z — save-diff
+
+```
+diff --git a/docs/ai/jobs/mvp-004/request.ko.md b/docs/ai/jobs/mvp-004/request.ko.md
+index 7d9ecf1..dcfaa5c 100644
+--- a/docs/ai/jobs/mvp-004/request.ko.md
++++ b/docs/ai/jobs/mvp-004/request.ko.md
+@@ -1,10 +1,74 @@
+-# 작업 요청
++# 작업 ID
++mvp-004
+ 
+-GUI 파이프라인이 Claude 계획 완료 전에 Codex 단계로 넘어가는 문제를 수정한다.
++# 작업명
++AI 개발팀 GUI 화면 배치 개선
+ 
+-Claude 계획 단계는 plan.md와 codex-task.md가 생성되어야 완료된 것으로 본다.
+-Codex 구현 단계는 patch.md가 생성되어야 완료된 것으로 본다.
+-Claude 리뷰 단계는 review.md가 생성되어야 완료된 것으로 본다.
++현재 AI 개발팀 브라우저 GUI에서 화면 배치가 불편하다.
+ 
+-전체 파이프라인 버튼은 각 단계의 산출물 파일을 확인한 뒤 다음 단계로 넘어가야 한다.
+-승인 대기, 차단, 실패 상태가 감지되면 다음 단계로 넘어가면 안 된다.
++문제점:
++1. 파이프라인 상태 영역이 너무 위에 있어서 핵심 제어 버튼과 시선 흐름이 맞지 않는다.
++2. 승인 / 서비스 제어 / 실시간 출력 영역이 아래쪽에 있어 잘 안 보인다.
++3. 작업 설정 칸이 너무 길어서 화면을 많이 차지한다.
++4. 실제 작업 중에는 승인 버튼, 서비스 제어, 실시간 출력이 더 중요하므로 위쪽에서 바로 보여야 한다.
++
++원하는 변경사항:
++
++1. “파이프라인 상태” 영역을 “Claude → Codex → Claude 전체 실행” 버튼 아래로 내려줘.
++
++2. 아래 영역들을 상단 쪽으로 올려줘.
++   - 승인 / 계속 진행
++   - 거절
++   - 중단
++   - 서비스 제어
++   - 실시간 출력
++
++3. 작업 설정 영역을 더 짧고 컴팩트하게 만들어줘.
++   - 입력칸 높이를 줄여줘.
++   - 필요하면 접기/펼치기 형태로 만들어줘.
++   - 화면에서 너무 많은 공간을 차지하지 않게 해줘.
++
++4. 화면 우선순위를 아래 순서로 재배치해줘.
++   - 상단: 작업 ID / 작업 요청 입력 / 주요 실행 버튼
++   - 그 아래: 승인 / 서비스 제어 / 실시간 출력
++   - 그 아래: 파이프라인 상태
++   - 그 아래: 작업 설정 / 고급 설정 / 산출물 목록
++
++5. Claude + Codex 2-role 구조는 유지해줘.
++   - Gemini Manager, Claude Architect, Claude Reviewer, Git Shell을 다시 노출하지 마.
++   - Claude 계획 생성
++   - Codex 구현 실행
++   - Claude 리뷰 실행
++   - Claude → Codex → Claude 전체 실행
++   이 버튼 구조는 유지해줘.
++
++6. git status와 git diff는 수동 유틸리티 버튼으로만 유지해줘.
++   - commit, push, merge는 자동화하지 마.
++
++7. 반응형 화면도 깨지지 않게 해줘.
++   - 작은 화면에서도 실시간 출력과 승인 버튼이 잘 보여야 한다.
++
++수정 대상:
++- web/public/index.html
++- web/public/app.js
++- web/public/style.css
++- 필요하면 web/server.js
++- README.md 또는 docs/ai/CLAUDE_CODEX_WORKFLOW.md는 변경 내용이 있으면 최소한만 업데이트
++
++금지:
++- 주식 페이퍼매매 로직은 건드리지 마.
++- secrets, .env, auth, payment, production infra, database migrations는 건드리지 마.
++- 임의 shell 명령 입력 기능은 만들지 마.
++- git commit, push, merge는 자동화하지 마.
++
++검증:
++- node --check web/server.js
++- node --check web/public/app.js
++- git diff --stat
++
++완료 후:
++- 어떤 UI 영역을 어디로 옮겼는지
++- 작업 설정 영역을 어떻게 줄였는지
++- Claude + Codex 구조가 유지되는지
++- 테스트 결과가 무엇인지
++patch.md에 정리해줘.
+\ No newline at end of file
+diff --git a/docs/ai/jobs/mvp-007/pipeline.log.md b/docs/ai/jobs/mvp-007/pipeline.log.md
+index 75df48b..5af59ba 100644
+--- a/docs/ai/jobs/mvp-007/pipeline.log.md
++++ b/docs/ai/jobs/mvp-007/pipeline.log.md
+@@ -1477,3 +1477,27 @@ index 0ce1e5d..7d07b26 100644
+ ```
+ (no output)
+ ```
++
++## 2026-05-14T10:53:00.580Z — create-job
++
++```
++Ensured job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-007
++```
++
++## 2026-05-14T10:53:00.588Z — save-input
++
++```
++Saved: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-007/request.ko.md
++```
++
++## 2026-05-14T10:53:00.600Z — claude-plan
++
++```
++(no output)
++```
++
++## 2026-05-14T10:53:00.611Z — codex-implement
++
++```
++(no output)
++```
+diff --git a/docs/ai/jobs/mvp-007/request.ko.md b/docs/ai/jobs/mvp-007/request.ko.md
+index dfd0315..9fc2cdb 100644
+--- a/docs/ai/jobs/mvp-007/request.ko.md
++++ b/docs/ai/jobs/mvp-007/request.ko.md
+@@ -1,227 +1,170 @@
+ # 작업 ID
+-mvp-007
++mvp-008
+ 
+ # 작업명
+-KIS Open API 모의투자 인증 / 계좌 / 시세 연결
++KIS 모의투자 주문 흐름 연결 준비
+ 
+-미국주식 자동 페이퍼매매 시스템에 KIS Open API 모의투자 연결을 진행해줘.
++미국주식 자동 페이퍼매매 시스템에서 KIS 모의투자 주문 흐름을 연결할 준비를 해줘.
+ 
+-현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 연결 검증이다.
++현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 주문 흐름 검증이다.
+ live trading은 절대 활성화하지 않는다.
+ 
+-## 현재 전제
++## 현재 상태
+ 
+-mvp-006에서 KIS 설정 구조와 Broker Adapter 골격을 준비했다.
++mvp-006-1과 mvp-007에서 아래 작업이 완료되었다.
+ 
+-이번 mvp-007에서는 가능한 범위 안에서 아래 기능을 연결한다.
++- paper-trading 프로젝트 기본 구조 생성
++- KIS 설정 구조 준비
++- `.env` 기반 KIS 설정 로딩
++- KIS Broker Adapter 골격
++- KIS Auth / Account / MarketData Client 골격
++- `/paper/status`에 KIS 상태 표시
++- secret/account masking 테스트
++- 74개 테스트 통과
+ 
+-1. KIS 모의투자 인증 토큰 발급 연결
+-2. 토큰 refresh / 만료 처리 구조
+-3. KIS 모의투자 계좌 정보 조회
+-4. KIS 해외주식 또는 미국주식 시세 조회 구조
+-5. Broker healthcheck 강화
+-6. `/paper/status` 또는 기존 status endpoint에 KIS 연결 상태 표시
+-7. 실제 주문은 아직 연결하지 않음
++이번 mvp-008에서는 실제 실계좌 주문이 아니라,
++KIS 모의투자 주문 흐름을 안전하게 연결할 준비를 한다.
+ 
+-## 보안 조건
++## 핵심 목표
+ 
+-KIS 모의투자 계좌번호, app key, app secret은 `.env`에 저장되어 있다고 가정한다.
++Strategy → RiskEngine → OMS → BrokerAdapter → KIS Broker 경로가 유지되도록 하면서,
++KIS 모의투자 주문 메서드의 안전한 경계를 만든다.
+ 
+-중요:
+-- 실제 계좌번호, app key, app secret 값을 코드에 쓰지 마.
+-- patch.md, review.md, 로그, 테스트 출력에 실제 secret을 노출하지 마.
+-- `.env.example`에는 placeholder만 유지해.
+-- `.env`는 Git에 추가하지 마.
+-- 설정 객체 repr/logging에서 app secret이 노출되지 않게 해.
+-- 테스트에서도 실제 secret 값을 출력하지 마.
+-
+-## 공식 문서 조건
+-
+-KIS Open API endpoint, TR ID, payload는 공식 문서 기준으로만 구현해야 한다.
+-
+-중요:
+-- 공식 문서나 프로젝트 내 명확한 문서가 없으면 endpoint를 추측해서 만들지 마.
+-- 확실하지 않은 endpoint, TR ID, header, payload는 TODO로 남겨.
+-- fake endpoint를 만들지 마.
+-- 실제 주문 endpoint는 이번 작업에서 구현하지 마.
+-- 인증 / 계좌조회 / 시세조회도 확실한 공식 정보가 없으면 fail-closed + TODO로 남겨.
+-
+-## 이번 구현 범위
+-
+-가능하면 아래 기능을 구현해줘.
+-
+-### 1. KIS Auth Client
++단, 공식 문서가 확인되지 않은 endpoint, TR ID, payload는 절대 추측해서 구현하지 않는다.
+ 
+-- `.env`에서 아래 값을 읽는다.
+-  - KIS_ENV
+-  - KIS_ACCOUNT_NO
+-  - KIS_APP_KEY
+-  - KIS_APP_SECRET
+-- 모의투자 환경인지 확인한다.
+-- 인증 토큰 발급 메서드를 만든다.
+-- 토큰 만료 시 refresh 또는 재발급 가능 구조를 만든다.
+-- 인증 실패 시 fail-closed 한다.
+-- secret이 로그에 찍히지 않게 한다.
++## 구현할 내용
+ 
+-필요 메서드 예시:
+-- authenticate()
+-- refresh_token()
+-- get_access_token()
+-- is_authenticated()
+-- clear_token()
++### 1. KIS 주문 메서드 경계 정리
+ 
+-### 2. KIS Account Client
++`KisBroker` 또는 현재 구조에 맞는 KIS adapter에 아래 주문 관련 메서드를 정리해줘.
+ 
+-- 계좌 정보 조회 골격 또는 실제 연결을 구현한다.
+-- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
+-- 계좌번호는 출력 시 마스킹한다.
+-- 실패 시 주문 가능 상태로 전환하지 않는다.
+-
+-필요 메서드 예시:
+-- get_account()
+-- get_positions()
+-- get_cash_balance()
+-
+-### 3. KIS Market Data Client
+-
+-- 미국주식 시세 조회 구조를 만든다.
+-- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
+-- 최소 quote 모델을 반환한다.
+-- 실패 시 stale / unavailable 상태로 처리한다.
+-
+-필요 메서드 예시:
+-- get_quote(symbol)
+-- get_last_price(symbol)
+-- healthcheck_market_data()
+-
+-### 4. KIS Broker Adapter 연결
++- place_order()
++- cancel_order()
++- replace_order()
++- get_open_orders()
++- get_fills()
++- get_order_status()
+ 
+-기존 BrokerAdapter 구조를 유지한다.
++조건:
++- 실제 endpoint/TR ID/payload를 추측해서 만들지 마.
++- 공식 문서가 없으면 TODO + fail-closed로 둬.
++- 메서드는 존재하되, 실주문 전송은 아직 하지 마.
++- NotImplementedError 또는 안전한 Rejected 상태를 반환하게 해.
++- 에러 메시지는 secret/account를 노출하지 않아야 한다.
+ 
+-- authenticate()
+-- refresh_token()
+-- get_account()
+-- get_positions()
+-- get_quote()
+-- healthcheck()
++### 2. OMS → KIS Broker 연결 준비
+ 
+-주문 관련 메서드는 아직 실제 전송하지 않는다.
++OMS가 broker adapter를 통해 주문을 보낼 수 있는 구조인지 점검하고,
++필요하면 interface를 정리해줘.
+ 
+-- place_order()
+-- cancel_order()
+-- replace_order()
++중요:
++- Strategy가 KIS를 직접 호출하면 안 된다.
++- Agent/LLM이 KIS를 직접 호출하면 안 된다.
++- OMS를 우회해서 주문하면 안 된다.
++- 모든 주문은 반드시 RiskEngine을 통과해야 한다.
++- OMS만 executable order를 만들 수 있다.
++
++### 3. KIS 모의투자 주문 요청 모델 준비
++
++실제 전송은 하지 말고, 내부 도메인 모델 기준으로 KIS 주문 요청 변환 경계를 만들어줘.
++
++예:
++- symbol
++- side
++- quantity
++- order_type
++- limit_price
++- extended_hours
++- account_no_masked
++- broker_environment
+ 
+-위 주문 메서드는 이번 단계에서 fail-closed 또는 NotImplemented 상태로 둔다.
++조건:
++- 시장가 주문은 금지
++- 지정가 주문만 허용
++- live trading이면 차단
++- KIS_ENV가 paper가 아니면 차단
++- 계좌번호 원문은 출력하지 말고 마스킹만 사용
+ 
+-## 주문 안전 조건
++### 4. 주문 안전 guard 추가
+ 
+-반드시 유지해.
++KIS 주문 흐름에 아래 guard를 적용해줘.
+ 
+-- live trading은 false
+-- TRADING_MODE는 paper
+-- 시장가 주문 금지
+-- 실주문 전송 금지
+-- Strategy가 KIS Adapter를 직접 호출하지 않음
+-- Agent/LLM이 직접 주문하지 않음
+-- 모든 주문은 Strategy → RiskEngine → OMS → BrokerAdapter 경로 유지
+-- OMS 우회 금지
+-- RiskEngine 우회 금지
++- TRADING_MODE=paper만 허용
++- LIVE_TRADING_ENABLED=false 확인
++- ALLOW_MARKET_ORDERS=false 확인
++- KIS_ENV=paper 확인
++- order_type이 market이면 거절
++- quantity가 0 이하이면 거절
++- limit_price가 없으면 거절
++- stale quote면 거절
++- kill switch가 켜져 있으면 거절
+ 
+-## 상태 API
++### 5. `/paper/status` 또는 status에 주문 준비 상태 추가
+ 
+-가능하면 `/paper/status` 또는 기존 `/status`에 아래 정보를 추가해줘.
++가능하면 아래 상태를 추가해줘.
+ 
+-- broker_type
+-- broker_environment
+-- kis_config_loaded
+-- kis_authenticated
+-- kis_account_loaded
+-- kis_market_data_available
+-- live_trading_enabled
+-- allow_market_orders
+-- last_broker_error
++- kis_order_entry_ready
++- kis_order_entry_mode: disabled | paper_guarded | not_implemented
++- kis_order_methods_fail_closed: true
++- live_trading_enabled: false
++- allow_market_orders: false
+ - secret_exposed: false
+ 
+-중요:
+-- app key, app secret, 계좌번호 원문은 절대 출력하지 마.
+-- 계좌번호는 필요하면 마스킹해서 보여줘.
++실제 app key, app secret, 계좌번호 원문은 절대 출력하지 마.
+ 
+-## 테스트 요구사항
++### 6. 테스트 추가
+ 
+ 아래 테스트를 추가해줘.
+ 
+-1. `.env` 기반 KIS config 로딩 테스트
+-2. app secret이 repr/logging/status에 노출되지 않는지 테스트
+-3. KIS_ENV=paper 기본 동작 테스트
+-4. live trading 기본 false 테스트
+-5. 시장가 주문 기본 금지 테스트
+-6. 인증 client가 secret을 직접 출력하지 않는지 테스트
+-7. 공식 문서 정보가 없을 때 endpoint를 추측하지 않고 TODO/fail-closed 되는지 테스트
+-8. 주문 메서드가 아직 실주문을 전송하지 않는지 테스트
+-9. BrokerAdapter 인터페이스가 깨지지 않는지 테스트
+-10. `/paper/status` 또는 `/status`에 KIS 상태가 안전하게 표시되는지 테스트
++1. KIS place_order가 실주문을 보내지 않고 fail-closed 되는지
++2. KIS cancel_order가 실취소를 보내지 않고 fail-closed 되는지
++3. KIS replace_order가 실정정을 보내지 않고 fail-closed 되는지
++4. market order가 거절되는지
++5. limit_price 없는 주문이 거절되는지
++6. live trading true이면 거절되는지
++7. KIS_ENV가 paper가 아니면 거절되는지
++8. Strategy가 KIS adapter를 직접 호출하지 않는지
++9. OMS 경로를 우회하지 않는지
++10. status에 secret/account 원문이 노출되지 않는지
++11. 기존 74개 테스트가 계속 통과하는지
+ 
+ ## 수정 가능 파일
+ 
+-필요한 경우 아래 파일을 수정해도 된다.
++필요하면 아래 파일을 수정해도 된다.
+ 
+-- app/adapters/brokers/kis.py
+-- app/adapters/brokers/base.py
+-- app/core/config.py
+-- app/api/routes.py
+-- app/runtime/paper_runner.py
+-- app/monitoring/status.py
+-- app/domain/*
+-- tests/*
+-- .env.example
+-- README.md
+-- docs/architecture.md
+-- docs/runbook.md
++- projects/paper-trading/app/broker/kis.py
++- projects/paper-trading/app/broker/base.py
++- projects/paper-trading/app/oms/*
++- projects/paper-trading/app/risk/*
++- projects/paper-trading/app/api/routes.py
++- projects/paper-trading/app/api/server.py
++- projects/paper-trading/app/config/*
++- projects/paper-trading/app/models/*
++- projects/paper-trading/tests/*
++- projects/paper-trading/README.md
++- docs/ai/jobs/mvp-008/patch.md
+ 
+-실제 프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.
++프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.
+ 
+ ## 금지 사항
+ 
+-- 실제 KIS app key, app secret, 계좌번호를 코드에 쓰지 마.
+-- 실제 값을 patch.md, review.md, 로그에 출력하지 마.
+-- `.env` 파일을 Git에 추가하지 마.
+-- live trading을 true로 바꾸지 마.
+-- 실계좌 주문 기능을 만들지 마.
+-- 주문 endpoint를 연결하지 마.
+-- KIS endpoint / TR ID / payload를 추측해서 만들지 마.
++- 실제 KIS endpoint를 추측해서 만들지 마.
++- TR ID를 추측해서 넣지 마.
++- 실제 주문 전송 코드를 만들지 마.
++- live trading을 활성화하지 마.
+ - 시장가 주문을 허용하지 마.
+-- 브로커 API를 Strategy에서 직접 호출하게 만들지 마.
++- app key, app secret, 계좌번호 원문을 코드/문서/로그/test output에 쓰지 마.
++- `.env` 파일을 Git에 추가하지 마.
++- Strategy가 KIS를 직접 호출하게 만들지 마.
++- Agent/LLM이 직접 주문하게 만들지 마.
+ - auth, payment, production infra, database migrations는 건드리지 마.
+ - git commit, push, merge는 자동화하지 마.
+ 
+ ## 검증
+ 
+-가능하면 아래를 실행해줘.
+-
+-- python -m compileall app tests
+-- python -m pytest -p no:cacheprovider
+-
+-만약 현재 프로젝트 구조가 Python이 아니거나 테스트 명령이 다르면,
+-현재 repo 구조에 맞는 안전한 검증 명령을 실행하고 patch.md에 이유를 적어줘.
+-
+-## 완료 후 patch.md에 정리할 내용
+-
+-1. 어떤 파일을 수정했는지
+-2. KIS 인증 구조가 어떻게 되었는지
+-3. 계좌 조회 구조가 어떻게 되었는지
+-4. 시세 조회 구조가 어떻게 되었는지
+-5. 실제 주문 기능이 여전히 비활성인지
+-6. secret이 노출되지 않는지
+-7. 어떤 테스트를 실행했는지
+-8. 공식 문서가 없어 TODO로 남긴 부분
+-9. 다음 mvp에서 무엇을 하면 되는지
+-
+-## 다음 단계 예고
+-
+-mvp-008에서는 KIS 모의투자 주문 흐름을 연결할 예정이다.
+-단, mvp-008에서도 live trading은 비활성이고, 소액 검증 전까지 실계좌 주문은 금지한다.
+-
+-## 추가 조건
++아래를 실행해줘.
+ 
+-- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
+-- 필요한 경우에만 최소한의 질문을 해.
+\ No newline at end of file
++```bash
++cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
++.venv/bin/python -m compileall app tests
++.venv/bin/python -m pytest -p no:cacheprovider
+\ No newline at end of file
+diff --git a/web/public/app.js b/web/public/app.js
+index f27f460..d9fc2c2 100644
+--- a/web/public/app.js
++++ b/web/public/app.js
+@@ -9,6 +9,7 @@ const inputKoEl = document.querySelector('#inputKo');
+ const outputEl = document.querySelector('#output');
+ const artifactListEl = document.querySelector('#artifactList');
+ const runPipelineButton = document.querySelector('#runPipeline');
++const sendButtons = [...document.querySelectorAll('[data-send]')];
+ const pipelineStateEl = document.querySelector('#pipelineState');
+ const pipelineJobIdEl = document.querySelector('#pipelineJobId');
+ const pipelineStageEl = document.querySelector('#pipelineStage');
+@@ -31,6 +32,15 @@ const approvalModalEl = document.querySelector('#approvalModal');
+ const approvalModalStepEl = document.querySelector('#approvalModalStep');
+ const approvalModalWindowEl = document.querySelector('#approvalModalWindow');
+ const approvalModalSummaryEl = document.querySelector('#approvalModalSummary');
++const approvalModalTypeEl = document.querySelector('#approvalModalType');
++const approvalModalCommandEl = document.querySelector('#approvalModalCommand');
++const approvalModalCwdEl = document.querySelector('#approvalModalCwd');
++const approvalModalRiskEl = document.querySelector('#approvalModalRisk');
++const approvalModalRecommendationEl = document.querySelector('#approvalModalRecommendation');
++const approvalModalRawEl = document.querySelector('#approvalModalRaw');
++const approvalModalRiskWarningEl = document.querySelector('#approvalModalRiskWarning');
++const approvalModalApproveOnceEl = document.querySelector('#approvalModalApproveOnce');
++const approvalModalApproveSessionEl = document.querySelector('#approvalModalApproveSession');
+ const aiControlButtons = [
+   document.querySelector('#approveOnce'),
+   document.querySelector('#approveSession'),
+@@ -59,8 +69,18 @@ const finalPipelineStates = new Set([
+   'failed',
+   'blocked',
+   'manual_review_required',
++  'review_approved',
++  'review_changes_requested',
++  'manual_final_approval_required',
+   'idle'
+ ]);
++const stageWindows = {
++  'claude-plan': 'claude',
++  'codex-implement': 'codex',
++  'claude-review': 'claude',
++  'codex-review-fix': 'codex',
++  'claude-re-review': 'claude'
++};
+ 
+ projectDirEl.value = state.projectDir;
+ jobIdEl.value = state.jobId;
+@@ -183,6 +203,10 @@ runPipelineButton.addEventListener('click', async () => {
+ });
+ 
+ document.querySelector('#pipelineStatus').addEventListener('click', refreshPipelineStatus);
++document.querySelector('#finalManualReview').addEventListener('click', () => {
++  writeOutput('최종 확인', 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.');
++  refreshPipelineStatus();
++});
+ 
+ document.querySelector('#resetPipeline').addEventListener('click', async () => {
+   const result = await runAction('파이프라인 상태 초기화', () => requestJson('/api/pipeline/reset', {
+@@ -370,6 +394,7 @@ function renderPipelineStatus(status) {
+     summaryDiffEl.textContent = '-';
+     summaryReviewEl.textContent = '-';
+     runPipelineButton.disabled = false;
++    updateSendButtonGates(null);
+     return;
+   }
+ 
+@@ -389,6 +414,7 @@ function renderPipelineStatus(status) {
+   pipelineTargetWindowEl.textContent = pipeline.targetWindow || '-';
+   pipelineWaitingApprovalEl.textContent = pipeline.waitingApproval ? '예' : '아니오';
+   renderDetectedIssue(approvalRequest ? null : pipeline.detectedIssue);
++  updateSendButtonGates(pipeline);
+ 
+   if (pipeline.targetWindow && tmuxWindowEl.value !== pipeline.targetWindow) {
+     tmuxWindowEl.value = pipeline.targetWindow;
+@@ -410,8 +436,9 @@ function renderPipelineStatus(status) {
+   } else {
+     currentApprovalRequest = null;
+     closeApprovalModal();
+-    pipelineGuidanceEl.hidden = true;
+-    pipelineGuidanceEl.textContent = '';
++    const requirementsText = renderRequirementsText(pipeline.requirements);
++    pipelineGuidanceEl.hidden = !requirementsText;
++    pipelineGuidanceEl.textContent = requirementsText;
+     approvalInlinePromptEl.hidden = true;
+   }
+ 
+@@ -464,6 +491,47 @@ function renderPipelineStatus(status) {
+   summaryNextActionEl.textContent = pipeline.nextAction || '-';
+ }
+ 
++function renderRequirementsText(requirements) {
++  if (!requirements || !requirements.files || requirements.files.length === 0) {
++    return '';
++  }
++  const lines = [
++    `필수 파일 (${requirements.label || '현재 단계'}):`,
++    ...requirements.files.map((file) => `- ${file.name}: ${file.exists ? 'ready' : 'missing'}`),
++    `다음 단계 가능: ${requirements.nextStageAllowed ? 'yes' : 'no'}`
++  ];
++  return lines.join('\n');
++}
++
++function hasArtifact(pipeline, name) {
++  return (pipeline?.artifacts || []).some((artifact) => (artifact.name || artifact) === name);
++}
++
++function updateSendButtonGates(pipeline) {
++  sendButtons.forEach((button) => {
++    const target = button.dataset.send;
++    let disabled = false;
++    let title = '';
++    if (!pipeline) {
++      disabled = false;
++    } else if (target === 'codex-implement') {
++      disabled = !hasArtifact(pipeline, 'plan.md') || !hasArtifact(pipeline, 'codex-task.md');
++      title = disabled ? 'Claude 계획이 아직 완료되지 않았습니다. plan.md와 codex-task.md가 생성된 뒤 Codex를 실행할 수 있습니다.' : '';
++    } else if (target === 'claude-review') {
++      disabled = !hasArtifact(pipeline, 'patch.md');
++      title = disabled ? 'patch.md가 생성된 뒤 Claude 리뷰를 실행할 수 있습니다.' : '';
++    } else if (target === 'codex-review-fix') {
++      disabled = pipeline.state !== 'review_changes_requested';
++      title = disabled ? 'Claude가 수정 요청을 남긴 뒤 실행할 수 있습니다.' : '';
++    } else if (target === 'claude-re-review') {
++      disabled = !hasArtifact(pipeline, 'status.md');
++      title = disabled ? 'Codex 리뷰 반영 후 status.md가 생성된 뒤 실행할 수 있습니다.' : '';
++    }
++    button.disabled = disabled;
++    button.title = title;
++  });
++}
++
+ function getApprovalRequest(status, pipeline) {
+   const issue = pipeline.detectedIssue || {};
+   const isApproval = pipeline.state === 'approval_required' || issue.type === 'approval_required';
+@@ -472,16 +540,18 @@ function getApprovalRequest(status, pipeline) {
+   }
+ 
+   const targetWindow = issue.window || pipeline.targetWindow;
+-  if (!['claude', 'codex'].includes(targetWindow)) {
++  const stageTargetWindow = stageWindows[pipeline.step] || pipeline.targetWindow || targetWindow;
++  if (!['claude', 'codex'].includes(stageTargetWindow)) {
+     return null;
+   }
+ 
+   const jobId = status.jobId || jobIdEl.value.trim() || '-';
+   const step = pipeline.step || '-';
+-  const rawSummary = issue.summary || pipeline.message || '';
+-  const summary = cleanApprovalSummary(targetWindow);
+-  const key = `${jobId}:${step}:${targetWindow}:${rawSummary || summary}`;
+-  return { key, step, targetWindow, summary };
++  const approvalContext = issue.approvalContext || null;
++  const rawSummary = approvalContext?.rawBlock || issue.summary || pipeline.message || '';
++  const summary = approvalContext?.summary || cleanApprovalSummary(stageTargetWindow);
++  const key = `${jobId}:${step}:${stageTargetWindow}:${rawSummary || summary}`;
++  return { key, step, targetWindow: stageTargetWindow, summary, approvalContext };
+ }
+ 
+ function cleanApprovalSummary(windowName) {
+@@ -495,10 +565,41 @@ function openApprovalModal(request, force) {
+     return;
+   }
+   lastApprovalKey = request.key;
+-  approvalModalStepEl.textContent = request.step || '-';
+-  approvalModalWindowEl.textContent = request.targetWindow || '-';
+-  approvalModalSummaryEl.textContent = request.summary || '-';
++  renderApprovalContext(request, request.approvalContext);
+   approvalModalEl.hidden = false;
++  if (!request.approvalContext) {
++    loadApprovalContext(request);
++  }
++}
++
++async function loadApprovalContext(request) {
++  try {
++    const result = await requestJson(`/api/tmux/approval-context?window=${encodeURIComponent(request.targetWindow)}&step=${encodeURIComponent(request.step || '')}`);
++    if (!currentApprovalRequest || currentApprovalRequest.key !== request.key) {
++      return;
++    }
++    currentApprovalRequest.approvalContext = result.approvalContext;
++    renderApprovalContext(currentApprovalRequest, result.approvalContext);
++  } catch (error) {
++    approvalModalRawEl.textContent = error.message;
++  }
++}
++
++function renderApprovalContext(request, context) {
++  const risk = context?.risk || 'unknown';
++  approvalModalStepEl.textContent = request.step || context?.step || '-';
++  approvalModalWindowEl.textContent = request.targetWindow || context?.window || '-';
++  approvalModalSummaryEl.textContent = context?.summary || request.summary || '-';
++  approvalModalTypeEl.textContent = context?.type || 'unknown';
++  approvalModalCommandEl.textContent = context?.commandOrTarget || '확인 불가';
++  approvalModalCwdEl.textContent = context?.workingDirectory || '-';
++  approvalModalRiskEl.textContent = risk;
++  approvalModalRiskEl.dataset.risk = risk;
++  approvalModalRecommendationEl.textContent = context?.recommendation || '직접 확인 필요';
++  approvalModalRawEl.textContent = context?.rawBlock || '원문을 불러오는 중입니다.';
++  approvalModalRiskWarningEl.textContent = context?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.';
++  approvalModalApproveOnceEl.disabled = !context?.canApproveOnce;
++  approvalModalApproveSessionEl.disabled = !context?.canApproveSession;
+ }
+ 
+ function closeApprovalModal() {
+@@ -510,6 +611,10 @@ async function sendApprovalModalAction(endpoint) {
+     writeOutput('승인 명령 실패', '승인 대상 창을 확인할 수 없습니다.');
+     return;
+   }
++  if (!approvalEndpointAllowed(endpoint, currentApprovalRequest.approvalContext)) {
++    writeOutput('승인 명령 차단', currentApprovalRequest.approvalContext?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.');
++    return;
++  }
+ 
+   try {
+     await requestJson(endpoint, {
+@@ -524,6 +629,16 @@ async function sendApprovalModalAction(endpoint) {
+   }
+ }
+ 
++function approvalEndpointAllowed(endpoint, context) {
++  if (endpoint.endsWith('/approve-once')) {
++    return Boolean(context?.canApproveOnce);
++  }
++  if (endpoint.endsWith('/approve-session')) {
++    return Boolean(context?.canApproveSession);
++  }
++  return true;
++}
++
+ function normalizePipelineStatus(payload) {
+   if (payload && payload.status && typeof payload.status === 'object') {
+     return {
+@@ -534,6 +649,7 @@ function normalizePipelineStatus(payload) {
+       waitingApproval: Boolean(payload.status.waitingApproval),
+       detectedIssue: payload.status.detectedIssue || null,
+       artifacts: payload.status.artifacts || [],
++      requirements: payload.status.requirements || null,
+       gitDiff: payload.status.gitDiff || '-',
+       reviewStatus: payload.status.reviewStatus || '-',
+       nextAction: payload.status.nextAction || '-'
+@@ -548,6 +664,7 @@ function normalizePipelineStatus(payload) {
+     waitingApproval: false,
+     detectedIssue: null,
+     artifacts: payload && payload.artifacts ? payload.artifacts : [],
++    requirements: null,
+     gitDiff: '-',
+     reviewStatus: '-',
+     nextAction: '-'
+@@ -625,6 +742,10 @@ async function sendTmuxControl(title, endpoint) {
+     writeOutput(`${title} 실패`, 'Manual Shell(git-shell)은 비AI 창입니다. 승인/거절 키 입력은 Claude 또는 Codex 창에서만 사용하세요.');
+     return null;
+   }
++  if (currentApprovalRequest && currentApprovalRequest.targetWindow === windowName && !approvalEndpointAllowed(endpoint, currentApprovalRequest.approvalContext)) {
++    writeOutput(`${title} 차단`, currentApprovalRequest.approvalContext?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.');
++    return null;
++  }
+   const result = await runAction(title, () => requestJson(endpoint, {
+     method: 'POST',
+     body: JSON.stringify({ window: windowName })
+diff --git a/web/public/index.html b/web/public/index.html
+index a02de7a..60b76f9 100644
+--- a/web/public/index.html
++++ b/web/public/index.html
+@@ -16,42 +16,55 @@
+     </header>
+ 
+     <main class="layout">
+-      <section class="panel setup">
+-        <h2>작업 설정</h2>
+-        <label>
+-          프로젝트 경로
+-          <input id="projectDir" type="text" autocomplete="off" spellcheck="false">
+-        </label>
++      <section class="panel quick-actions">
++        <h2>핵심 실행</h2>
+         <label>
+           작업 ID
+           <input id="jobId" type="text" value="mvp-001" autocomplete="off" spellcheck="false">
+         </label>
+         <label>
+           한국어 작업 요청
+-          <textarea id="inputKo" spellcheck="false" rows="14"></textarea>
++          <textarea id="inputKo" spellcheck="false" rows="6"></textarea>
+         </label>
+         <p class="field-hint">여기에는 한국어 작업 요청만 입력하세요. 쉘 설정 명령, 실행 명령, 토큰, 비밀값은 넣지 않습니다.</p>
+-        <div class="role-display" aria-label="역할 안내">
+-          <div>
+-            <strong>Claude</strong>
+-            <span>planning / requirements / review</span>
+-          </div>
+-          <div>
+-            <strong>Codex</strong>
+-            <span>implementation / tests / patch summary</span>
+-          </div>
+-        </div>
+-        <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
+         <div class="pipeline-runner">
+           <button id="runPipeline" class="primary-action" type="button">Claude → Codex → Claude 전체 실행</button>
+           <div class="primary-actions">
+             <button data-send="claude-plan" type="button">Claude 계획 생성</button>
+             <button data-send="codex-implement" type="button">Codex 구현 실행</button>
+             <button data-send="claude-review" type="button">Claude 리뷰 실행</button>
++            <button data-send="codex-review-fix" type="button">Codex 리뷰 반영 실행</button>
++            <button data-send="claude-re-review" type="button">Claude 재리뷰 실행</button>
++            <button id="finalManualReview" type="button">최종 확인으로 이동</button>
+           </div>
+         </div>
+       </section>
+ 
++      <section class="panel control-panel">
++        <h2>승인 / 서비스 제어</h2>
++        <p class="warning-text">승인은 Claude 또는 Codex AI CLI 창에만 키 입력을 보내는 기능입니다. Manual Shell(git-shell)은 사람이 직접 git/test 명령을 실행하는 비AI 창입니다.</p>
++        <label>
++          제어할 tmux 창
++          <select id="tmuxWindow"></select>
++        </label>
++        <div class="actions control-actions">
++          <button id="approveOnce" type="button">승인 / 계속 진행</button>
++          <button id="approveSession" type="button">세션 승인</button>
++          <button id="rejectAction" type="button">거절</button>
++          <button id="interruptAction" type="button">중단</button>
++          <button id="restartAiTeam" type="button">AI팀 재시작</button>
++          <button id="restartGui" type="button">GUI 서버 재시작</button>
++        </div>
++      </section>
++
++      <section class="panel tmux-panel">
++        <div class="panel-head">
++          <h2>실시간 tmux 출력</h2>
++          <button id="refreshTmuxOutput" type="button">출력 새로고침</button>
++        </div>
++        <pre id="tmuxOutput" aria-live="polite"></pre>
++      </section>
++
+       <section class="panel pipeline-status">
+         <div class="panel-head">
+           <h2>파이프라인 상태</h2>
+@@ -96,29 +109,42 @@
+         <div id="pipelineSteps" class="pipeline-steps"></div>
+       </section>
+ 
+-      <section class="panel control-panel">
+-        <h2>승인 / 서비스 제어</h2>
+-        <p class="warning-text">승인은 Claude 또는 Codex AI CLI 창에만 키 입력을 보내는 기능입니다. Manual Shell(git-shell)은 사람이 직접 git/test 명령을 실행하는 비AI 창입니다.</p>
++      <details class="panel job-settings">
++        <summary>작업 설정</summary>
+         <label>
+-          제어할 tmux 창
+-          <select id="tmuxWindow"></select>
++          프로젝트 경로
++          <input id="projectDir" type="text" autocomplete="off" spellcheck="false">
+         </label>
+-        <div class="actions control-actions">
+-          <button id="approveOnce" type="button">승인 / 계속 진행</button>
+-          <button id="approveSession" type="button">세션 승인</button>
+-          <button id="rejectAction" type="button">거절</button>
+-          <button id="interruptAction" type="button">중단</button>
+-          <button id="restartAiTeam" type="button">AI팀 재시작</button>
+-          <button id="restartGui" type="button">GUI 서버 재시작</button>
++        <div class="role-display" aria-label="역할 안내">
++          <div>
++            <strong>Claude</strong>
++            <span>planning / requirements / review</span>
++          </div>
++          <div>
++            <strong>Codex</strong>
++            <span>implementation / tests / patch summary</span>
++          </div>
+         </div>
+-      </section>
++        <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
++      </details>
+ 
+-      <section class="panel tmux-panel">
++      <details class="panel advanced-panel">
++        <summary>고급 제어</summary>
++        <div class="actions">
++          <button id="startTeam" type="button">AI 팀 시작</button>
++          <button id="createJob" type="button">작업 폴더 생성</button>
++          <button id="saveInput" type="button">request.ko.md 저장</button>
++          <button id="gitStatus" type="button">git status</button>
++          <button id="gitDiff" type="button">git diff</button>
++        </div>
++      </details>
++
++      <section class="panel artifacts">
+         <div class="panel-head">
+-          <h2>실시간 tmux 출력</h2>
+-          <button id="refreshTmuxOutput" type="button">출력 새로고침</button>
++          <h2>산출물</h2>
++          <button id="loadArtifacts" type="button">목록 새로고침</button>
+         </div>
+-        <pre id="tmuxOutput" aria-live="polite"></pre>
++        <div id="artifactList" class="artifact-list"></div>
+       </section>
+ 
+       <section class="panel result-summary">
+@@ -143,25 +169,6 @@
+         </dl>
+       </section>
+ 
+-      <details class="panel advanced-panel">
+-        <summary>고급 제어</summary>
+-        <div class="actions">
+-          <button id="startTeam" type="button">AI 팀 시작</button>
+-          <button id="createJob" type="button">작업 폴더 생성</button>
+-          <button id="saveInput" type="button">request.ko.md 저장</button>
+-          <button id="gitStatus" type="button">git status</button>
+-          <button id="gitDiff" type="button">git diff</button>
+-        </div>
+-      </details>
+-
+-      <section class="panel artifacts">
+-        <div class="panel-head">
+-          <h2>산출물</h2>
+-          <button id="loadArtifacts" type="button">목록 새로고침</button>
+-        </div>
+-        <div id="artifactList" class="artifact-list"></div>
+-      </section>
+-
+       <section class="panel output-panel">
+         <div class="panel-head">
+           <h2>출력</h2>
+@@ -191,11 +198,36 @@
+             <dt>감지 요약</dt>
+             <dd id="approvalModalSummary">-</dd>
+           </div>
++          <div>
++            <dt>요청 유형</dt>
++            <dd id="approvalModalType">-</dd>
++          </div>
++          <div>
++            <dt>명령/대상</dt>
++            <dd id="approvalModalCommand">-</dd>
++          </div>
++          <div>
++            <dt>작업 디렉터리</dt>
++            <dd id="approvalModalCwd">-</dd>
++          </div>
++          <div>
++            <dt>위험도</dt>
++            <dd id="approvalModalRisk">-</dd>
++          </div>
++          <div>
++            <dt>추천 행동</dt>
++            <dd id="approvalModalRecommendation">-</dd>
++          </div>
+         </dl>
++        <details class="approval-raw">
++          <summary>원문 보기</summary>
++          <pre id="approvalModalRaw">-</pre>
++        </details>
+         <p class="modal-warning">주의: 이 버튼은 현재 AI CLI 창에 키 입력을 보내는 기능입니다. 위험한 명령은 승인하지 마세요.</p>
++        <p id="approvalModalRiskWarning" class="modal-warning">-</p>
+         <div class="modal-actions">
+-          <button data-approval-action="/api/tmux/approve-once" type="button">1회 승인</button>
+-          <button data-approval-action="/api/tmux/approve-session" type="button">세션 승인</button>
++          <button id="approvalModalApproveOnce" data-approval-action="/api/tmux/approve-once" type="button">1회 승인</button>
++          <button id="approvalModalApproveSession" data-approval-action="/api/tmux/approve-session" type="button">세션 승인</button>
+           <button data-approval-action="/api/tmux/reject" class="danger-action" type="button">거절</button>
+           <button data-approval-action="/api/tmux/interrupt" class="danger-action" type="button">중단</button>
+           <button id="dismissApprovalModal" type="button">닫기</button>
+diff --git a/web/public/style.css b/web/public/style.css
+index 9d50479..e9c85a8 100644
+--- a/web/public/style.css
++++ b/web/public/style.css
+@@ -64,11 +64,11 @@ h2 {
+ }
+ 
+ .layout {
+-  display: grid;
+-  grid-template-columns: minmax(320px, 0.95fr) minmax(360px, 1.05fr);
++  display: flex;
++  flex-direction: column;
+   gap: 18px;
+   padding: 22px;
+-  max-width: 1440px;
++  max-width: 1100px;
+   margin: 0 auto;
+ }
+ 
+@@ -80,14 +80,6 @@ h2 {
+   padding: 18px;
+ }
+ 
+-.setup {
+-  grid-row: span 4;
+-}
+-
+-.output-panel {
+-  grid-column: 2;
+-}
+-
+ .panel-head {
+   display: flex;
+   align-items: center;
+@@ -103,6 +95,26 @@ h2 {
+   justify-content: flex-end;
+ }
+ 
++.quick-actions {
++  display: grid;
++  gap: 12px;
++}
++
++.job-settings {
++  padding: 14px 18px;
++}
++
++.job-settings > summary {
++  cursor: pointer;
++  font-size: 18px;
++  font-weight: 800;
++  padding: 4px 0;
++}
++
++.job-settings[open] {
++  padding-bottom: 18px;
++}
++
+ label {
+   display: grid;
+   gap: 7px;
+@@ -173,7 +185,7 @@ select {
+ }
+ 
+ textarea {
+-  min-height: 330px;
++  min-height: 140px;
+   resize: vertical;
+   padding: 12px;
+   line-height: 1.5;
+@@ -484,6 +496,37 @@ button:disabled {
+   font-weight: 800;
+ }
+ 
++.approval-details dd[data-risk="low"] {
++  color: #0f766e;
++}
++
++.approval-details dd[data-risk="medium"],
++.approval-details dd[data-risk="unknown"] {
++  color: #92400e;
++}
++
++.approval-details dd[data-risk="high"] {
++  color: var(--danger);
++}
++
++.approval-raw {
++  margin-top: 14px;
++}
++
++.approval-raw summary {
++  cursor: pointer;
++  color: var(--muted);
++  font-size: 13px;
++  font-weight: 800;
++}
++
++.approval-raw pre {
++  min-height: 120px;
++  max-height: 220px;
++  margin-top: 8px;
++  font-size: 12px;
++}
++
+ .modal-warning {
+   margin: 14px 0 0;
+   padding: 10px 12px;
+@@ -610,16 +653,9 @@ pre {
+   }
+ 
+   .layout {
+-    grid-template-columns: 1fr;
+     padding: 14px;
+   }
+ 
+-  .setup,
+-  .output-panel {
+-    grid-row: auto;
+-    grid-column: auto;
+-  }
+-
+   .step-grid {
+     grid-template-columns: 1fr;
+   }
+diff --git a/web/server.js b/web/server.js
+index 0ce1e5d..7d07b26 100644
+--- a/web/server.js
++++ b/web/server.js
+@@ -16,6 +16,8 @@ const SAFE_WINDOWS = {
+   'claude-plan': 'claude',
+   'codex-implement': 'codex',
+   'claude-review': 'claude',
++  'codex-review-fix': 'codex',
++  'claude-re-review': 'claude',
+   claude: 'claude',
+   codex: 'codex'
+ };
+@@ -56,9 +58,7 @@ const ISSUE_PATTERNS = [
+   {
+     type: 'approval_required',
+     patterns: [
+-      /approval|approve|allow|continue|proceed|permission/i,
+-      /승인|허용|계속 진행|진행하시겠습니까|거절/i,
+-      /1\).*(approve|allow|승인|계속)|2\).*(session|세션)|3\).*(reject|거절)/i
++      /allow execution|allow edit|do you want to proceed|would you like to continue|allow for this session|no, suggest changes|enter your response/i
+     ]
+   },
+   {
+@@ -80,12 +80,16 @@ const pipelineStates = new Map();
+ const PIPELINE_STAGES = [
+   { id: 'claude-plan', state: 'claude_planning', label: 'Claude 계획 생성', role: 'claude-plan', window: 'claude', artifacts: ['plan.md', 'codex-task.md'] },
+   { id: 'codex-implement', state: 'codex_implementing', label: 'Codex 구현 실행', role: 'codex-implement', window: 'codex', artifacts: ['patch.md'] },
+-  { id: 'claude-review', state: 'claude_reviewing', label: 'Claude 리뷰 실행', role: 'claude-review', window: 'claude', artifacts: ['review.md'] }
++  { id: 'claude-review', state: 'claude_reviewing', label: 'Claude 리뷰 실행', role: 'claude-review', window: 'claude', artifacts: ['review.md'] },
++  { id: 'codex-review-fix', state: 'codex_fixing_review', label: 'Codex 리뷰 반영 실행', role: 'codex-review-fix', window: 'codex', artifacts: ['status.md'] },
++  { id: 'claude-re-review', state: 'claude_re_reviewing', label: 'Claude 재리뷰 실행', role: 'claude-re-review', window: 'claude', artifacts: ['review.md'] }
+ ];
+ const ACTIVE_PIPELINE_STATES = new Set([
+   'claude_planning',
+   'codex_implementing',
+   'claude_reviewing',
++  'codex_fixing_review',
++  'claude_re_reviewing',
+   'approval_required'
+ ]);
+ const FINAL_PIPELINE_STATES = new Set([
+@@ -93,6 +97,9 @@ const FINAL_PIPELINE_STATES = new Set([
+   'failed',
+   'blocked',
+   'manual_review_required',
++  'review_approved',
++  'review_changes_requested',
++  'manual_final_approval_required',
+   'idle'
+ ]);
+ const ARTIFACT_PRIORITY = [
+@@ -240,8 +247,97 @@ function currentTargetWindow(state) {
+   return stage ? stage.window : null;
+ }
+ 
+-function publicIdlePipelineState(projectDir = null, jobId = null) {
++function stageByState(status) {
++  return PIPELINE_STAGES.find((stage) => stage.state === status) || null;
++}
++
++function stageForGate(status, currentStep) {
++  return stageById(currentStep) || stageByState(status) || PIPELINE_STAGES[0];
++}
++
++function nextStageGate(state) {
++  if (!state) {
++    return PIPELINE_STAGES[0];
++  }
++  if (state.status === 'succeeded' || state.status === 'review_approved' || state.status === 'manual_final_approval_required') {
++    return null;
++  }
++  if (state.status === 'review_changes_requested') {
++    return stageById('codex-review-fix');
++  }
++  return stageForGate(state.status, state.currentStep);
++}
++
++function artifactPath(projectDir, jobId, name) {
++  return path.join(projectDir, 'docs', 'ai', 'jobs', jobId, name);
++}
++
++async function artifactStat(projectDir, jobId, name) {
++  const stat = await fs.stat(artifactPath(projectDir, jobId, name)).catch(() => null);
++  return stat && stat.isFile() && stat.size > 0 ? stat : null;
++}
++
++async function artifactExists(projectDir, jobId, name, afterIso = null) {
++  const stat = await artifactStat(projectDir, jobId, name);
++  if (!stat) {
++    return false;
++  }
++  if (!afterIso) {
++    return true;
++  }
++  const after = Date.parse(afterIso);
++  return Number.isNaN(after) ? true : stat.mtimeMs >= after;
++}
++
++async function artifactStatus(projectDir, jobId, names, afterIso = null) {
++  const files = [];
++  for (const name of names) {
++    const stat = await artifactStat(projectDir, jobId, name);
++    const exists = stat ? await artifactExists(projectDir, jobId, name, afterIso) : false;
++    files.push({ name, exists, modifiedAt: stat ? stat.mtime.toISOString() : null });
++  }
++  return files;
++}
++
++async function allArtifactsExist(projectDir, jobId, names, afterIso = null) {
++  const files = await artifactStatus(projectDir, jobId, names, afterIso);
++  return {
++    ok: files.every((file) => file.exists),
++    files,
++    missing: files.filter((file) => !file.exists).map((file) => file.name)
++  };
++}
++
++async function buildStageRequirements(projectDir, jobId, stage) {
++  if (!stage) {
++    return {
++      stage: null,
++      label: null,
++      files: [],
++      missing: [],
++      nextStageAllowed: true,
++      guidance: ''
++    };
++  }
++  const requirements = await allArtifactsExist(projectDir, jobId, stage.artifacts);
++  return {
++    stage: stage.id,
++    label: stage.label,
++    files: requirements.files,
++    missing: requirements.missing,
++    nextStageAllowed: requirements.ok,
++    guidance: requirements.ok
++      ? '다음 단계를 실행할 수 있습니다.'
++      : `필수 산출물이 아직 생성되지 않았습니다: ${requirements.missing.join(', ')}`
++  };
++}
++
++async function publicIdlePipelineState(projectDir = null, jobId = null) {
+   const now = new Date().toISOString();
++  const artifacts = projectDir && jobId ? await listArtifacts(projectDir, jobId) : [];
++  const requirements = projectDir && jobId
++    ? await buildStageRequirements(projectDir, jobId, PIPELINE_STAGES[0])
++    : await buildStageRequirements(null, null, null);
+   return {
+     ok: true,
+     jobKey: projectDir && jobId ? pipelineKey(projectDir, jobId) : null,
+@@ -255,15 +351,22 @@ function publicIdlePipelineState(projectDir = null, jobId = null) {
+       targetWindow: null,
+       waitingApproval: false,
+       detectedIssue: null,
+-      artifacts: [],
++      artifacts,
+       gitDiff: '-',
+       reviewStatus: '-',
+-      nextAction: '작업 요청을 입력한 뒤 Claude → Codex → Claude 전체 실행을 누르세요.'
++      nextAction: '작업 요청을 입력한 뒤 Claude → Codex → Claude 전체 실행을 누르세요.',
++      requirements
++    },
++    artifacts,
++    summary: {
++      createdArtifacts: artifacts.map((artifact) => artifact.name),
++      gitDiff: { hasChanges: false, saved: false, path: null, changedFiles: [] },
++      review: { status: 'not_started', file: null, decision: null }
+     }
+   };
+ }
+ 
+-function publicPipelineState(state) {
++async function publicPipelineState(state) {
+   if (!state) {
+     return publicIdlePipelineState();
+   }
+@@ -277,6 +380,7 @@ function publicPipelineState(state) {
+     ? `${review.status}: ${review.file}${review.decision ? ` / ${review.decision}` : ''}`
+     : review.status || '-';
+   const detectedIssue = state.detectedIssue || null;
++  const requirements = await buildStageRequirements(state.projectDir, state.jobId, nextStageGate(state));
+ 
+   return {
+     ok: true,
+@@ -297,7 +401,8 @@ function publicPipelineState(state) {
+       artifacts: state.artifacts,
+       gitDiff: gitDiffText,
+       reviewStatus,
+-      nextAction: nextRecommendedAction(state, reviewStatus)
++      nextAction: nextRecommendedAction(state, reviewStatus),
++      requirements
+     },
+     steps: state.steps,
+     artifacts: state.artifacts,
+@@ -315,6 +420,18 @@ function pipelineMessage(status) {
+   if (status === 'claude_reviewing') {
+     return 'Claude가 현재 diff와 패치 요약을 리뷰하는 단계입니다.';
+   }
++  if (status === 'codex_fixing_review') {
++    return 'Codex가 Claude 리뷰의 수정 요청만 반영하는 단계입니다.';
++  }
++  if (status === 'claude_re_reviewing') {
++    return 'Claude가 수정 반영 후 diff를 다시 리뷰하는 단계입니다.';
++  }
++  if (status === 'review_approved' || status === 'manual_final_approval_required') {
++    return 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.';
++  }
++  if (status === 'review_changes_requested') {
++    return 'Claude가 수정 요청을 남겼습니다. Codex가 리뷰 내용을 반영해야 합니다.';
++  }
+   if (status === 'succeeded') {
+     return '파이프라인이 완료되었습니다.';
+   }
+@@ -334,11 +451,14 @@ function pipelineMessage(status) {
+ }
+ 
+ function nextRecommendedAction(state, reviewStatus) {
+-  if (state.status === 'succeeded') {
++  if (state.status === 'review_approved' || state.status === 'manual_final_approval_required' || state.status === 'succeeded') {
+     return reviewStatus && reviewStatus !== '-'
+       ? 'Claude 리뷰 결과를 확인한 뒤 사람이 직접 commit, push, PR 생성 여부를 결정하세요.'
+       : '산출물과 git diff를 확인한 뒤 사람이 직접 다음 작업을 결정하세요.';
+   }
++  if (state.status === 'review_changes_requested') {
++    return 'Codex 리뷰 반영 실행을 눌러 Claude가 요청한 수정만 반영하세요.';
++  }
+   if (state.status === 'manual_review_required' || state.status === 'approval_required') {
+     return 'tmux 출력을 확인하고 필요한 경우 승인 / 계속 진행, 세션 승인, 거절, 중단 중 하나를 선택하세요.';
+   }
+@@ -438,24 +558,25 @@ async function refreshPipelineArtifacts(state) {
+ 
+ async function findFirstExistingArtifact(projectDir, jobId, names) {
+   for (const name of names) {
+-    const filePath = path.join(projectDir, 'docs', 'ai', 'jobs', jobId, name);
+-    const stat = await fs.stat(filePath).catch(() => null);
+-    if (stat && stat.isFile() && stat.size > 0) {
+-      return { name, path: filePath };
++    if (await artifactExists(projectDir, jobId, name)) {
++      return { name, path: artifactPath(projectDir, jobId, name) };
+     }
+   }
+   return null;
+ }
+ 
+-async function waitForArtifact(projectDir, jobId, names, state = null, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
++async function waitForArtifacts(projectDir, jobId, names, state = null, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
+   const started = Date.now();
++  const afterIso = state && state.currentStep
++    ? state.steps.find((step) => step.id === state.currentStep)?.startedAt || null
++    : null;
+   while (Date.now() - started < timeoutMs) {
+     if (state && !ACTIVE_PIPELINE_STATES.has(state.status)) {
+       return null;
+     }
+-    const artifact = await findFirstExistingArtifact(projectDir, jobId, names);
+-    if (artifact) {
+-      return artifact;
++    const requirements = await allArtifactsExist(projectDir, jobId, names, afterIso);
++    if (requirements.ok) {
++      return requirements.files;
+     }
+     await new Promise((resolve) => setTimeout(resolve, PIPELINE_POLL_MS));
+   }
+@@ -492,6 +613,10 @@ function markTimedOutRunningStep(state) {
+ }
+ 
+ function summarizeIssue(output, type) {
++  if (type === 'approval_required') {
++    const block = extractApprovalBlock(output);
++    return block ? block.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)[0]?.slice(0, 220) || ISSUE_RECOMMENDATIONS[type] : ISSUE_RECOMMENDATIONS[type];
++  }
+   const lines = String(output || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
+   const matcher = ISSUE_PATTERNS.find((item) => item.type === type);
+   if (matcher) {
+@@ -503,9 +628,72 @@ function summarizeIssue(output, type) {
+   return lines.slice(-3).join(' ').slice(0, 220) || ISSUE_RECOMMENDATIONS[type] || '최근 tmux 출력에서 확인이 필요한 상태를 감지했습니다.';
+ }
+ 
++function isLikelyCodeOrSearchLine(line) {
++  return /^\s*[+-]/.test(line)
++    || /\bconst\s+|\bfunction\s+|=>|stageWindows|pipelineStates|server\.js|Search\s+/i.test(line)
++    || /['"]approval_required['"]|['"]manual_review_required['"]/i.test(line)
++    || /^\s*(web\/|app\/|docs\/|projects\/).+:\d+[:\s]/.test(line)
++    || /^\s*```/.test(line);
++}
++
++function stripCodeLikeApprovalLines(output) {
++  const lines = String(output || '').split(/\r?\n/);
++  let inCodeBlock = false;
++  const kept = [];
++  for (const line of lines) {
++    if (/^\s*```/.test(line)) {
++      inCodeBlock = !inCodeBlock;
++      continue;
++    }
++    if (inCodeBlock || isLikelyCodeOrSearchLine(line)) {
++      continue;
++    }
++    kept.push(line);
++  }
++  return kept.join('\n');
++}
++
++function hasApprovalOptions(block) {
++  return /(?:^|\n)\s*(?:1[.)]|2[.)]|3[.)]).*(?:allow|approve|session|reject|승인|세션|거절|continue)/i.test(block);
++}
++
++function hasCommandOrEditSummary(block) {
++  return /(?:command|execute|run|edit|file|patch|modify|명령|실행|수정|편집|파일)\s*[:：]/i.test(block)
++    || /\b(npm|node|python3?|git|mkdir|cat|chmod|cp|mv|rm|sudo|curl|gh)\b/i.test(block)
++    || /[\w./-]+\.(?:js|css|html|md|json|py|ts|tsx|jsx|yml|yaml|sh)/i.test(block);
++}
++
++function findStrictApprovalPromptBlock(output) {
++  const cleaned = stripCodeLikeApprovalLines(output);
++  const lines = cleaned.split(/\r?\n/);
++  const strongPattern = /allow execution|allow edit|do you want to proceed|would you like to continue|allow for this session|no, suggest changes|enter your response/i;
++  for (let i = lines.length - 1; i >= 0; i -= 1) {
++    if (!strongPattern.test(lines[i])) {
++      continue;
++    }
++    const block = lines.slice(Math.max(0, i - 8), Math.min(lines.length, i + 10)).join('\n').trim();
++    if (hasApprovalOptions(block) || hasCommandOrEditSummary(block)) {
++      return block;
++    }
++  }
++  return '';
++}
++
+ function detectIssueFromOutput(output, windowName) {
+   const text = String(output || '');
+   for (const category of ISSUE_PATTERNS) {
++    if (category.type === 'approval_required') {
++      const block = findStrictApprovalPromptBlock(text);
++      if (block) {
++        return {
++          type: category.type,
++          window: windowName,
++          summary: summarizeIssue(block, category.type),
++          recommendation: ISSUE_RECOMMENDATIONS[category.type]
++        };
++      }
++      continue;
++    }
+     if (category.patterns.some((pattern) => pattern.test(text))) {
+       return {
+         type: category.type,
+@@ -527,6 +715,94 @@ async function captureRecentTmuxOutput(windowName, lines = 120) {
+   return result.ok ? redactedOutput(result.stdout) : '';
+ }
+ 
++function approvalTypeFromBlock(block) {
++  if (/edit|patch|modify|write|수정|편집|파일/i.test(block)) {
++    return 'file_edit';
++  }
++  if (/command|execute|run|명령|실행/i.test(block)) {
++    return 'command_execution';
++  }
++  return 'unknown';
++}
++
++function extractCommandOrTarget(block) {
++  const lines = String(block || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
++  const commandLine = lines.find((line) => /^\$|^>|^`[^`]+`$|^(npm|node|python|python3|git|mkdir|cat|chmod|cp|mv|rm|sudo|curl|gh)\b/i.test(line));
++  if (commandLine) {
++    return commandLine.replace(/^[$>]\s*/, '').replace(/^`|`$/g, '').slice(0, 260);
++  }
++  const fileLine = lines.find((line) => /(?:^|\s)([\w./-]+\.(?:js|css|html|md|json|py|ts|tsx|jsx|yml|yaml|sh))(?:\s|$)/i.test(line));
++  return fileLine ? fileLine.slice(0, 260) : '';
++}
++
++function classifyApprovalRisk(block, commandOrTarget) {
++  const text = `${block || ''}\n${commandOrTarget || ''}`;
++  if (/rm\s+-rf|sudo\b|curl\b.*\|\s*(bash|sh)|git\s+push|gh\s+pr\s+merge|deploy|deployment|kubectl|terraform|\.env|secret|token|api\s*key|auth\/|payment\/|billing\/|migrations?\/|production|prod\b/i.test(text)) {
++    return {
++      risk: 'high',
++      recommendation: '거절 권장',
++      canApproveOnce: false,
++      canApproveSession: false,
++      warning: '승인하지 마세요. 거절 또는 중단하세요.'
++    };
++  }
++  if (/npm\s+install|chmod\b|\bcp\b|\bmv\b/i.test(text) || /(?:^|\s)(?!docs\/ai\/jobs\/)[\w./-]+\.(?:js|css|html|py|ts|tsx|jsx|json|yml|yaml|sh)/i.test(text)) {
++    return {
++      risk: 'medium',
++      recommendation: '직접 확인 필요',
++      canApproveOnce: true,
++      canApproveSession: false,
++      warning: '명령과 수정 대상을 tmux 출력에서 확인한 뒤 1회 승인만 고려하세요.'
++    };
++  }
++  if (/mkdir\s+-p\s+docs\/ai\/jobs\/|docs\/ai\/jobs\/[\w._-]+|git\s+(status|diff)\b|node\s+--check\b|python3?\s+-m\s+(py_compile|compileall)\b|cat\s+docs\/ai\/jobs\//i.test(text)) {
++    return {
++      risk: 'low',
++      recommendation: '1회 승인 가능',
++      canApproveOnce: true,
++      canApproveSession: true,
++      warning: '세션 승인은 같은 종류의 안전한 명령이 반복될 때만 사용하세요.'
++    };
++  }
++  return {
++    risk: 'unknown',
++    recommendation: '직접 확인 필요',
++    canApproveOnce: false,
++    canApproveSession: false,
++    warning: '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.'
++  };
++}
++
++function extractApprovalBlock(output) {
++  return findStrictApprovalPromptBlock(output);
++}
++
++function cleanWorkingDirectory(block) {
++  const match = String(block || '').match(/(?:cwd|working directory|작업 디렉터리)\s*[:=]\s*([^\n]+)/i);
++  return match ? match[1].trim().slice(0, 260) : '-';
++}
++
++async function buildApprovalContext(windowName, step = null) {
++  const safeWindow = validateAiTmuxWindow(windowName);
++  const output = await captureRecentTmuxOutput(safeWindow, 180);
++  const rawBlock = extractApprovalBlock(output);
++  if (!rawBlock) {
++    return null;
++  }
++  const commandOrTarget = extractCommandOrTarget(rawBlock);
++  const risk = classifyApprovalRisk(rawBlock, commandOrTarget);
++  return {
++    window: safeWindow,
++    step,
++    type: approvalTypeFromBlock(rawBlock),
++    commandOrTarget: commandOrTarget || '확인 불가',
++    workingDirectory: cleanWorkingDirectory(rawBlock),
++    rawBlock,
++    ...risk,
++    summary: `${safeWindow === 'codex' ? 'Codex' : 'Claude'} 창에서 명령 실행 승인 요청이 감지되었습니다.`
++  };
++}
++
+ async function refreshDetectedIssue(state) {
+   if (!state || !ACTIVE_PIPELINE_STATES.has(state.status)) {
+     return;
+@@ -540,6 +816,13 @@ async function refreshDetectedIssue(state) {
+   if (!issue) {
+     return;
+   }
++  if (issue.type === 'approval_required') {
++    issue.approvalContext = await buildApprovalContext(targetWindow, state.currentStep).catch(() => null);
++    if (!issue.approvalContext) {
++      return;
++    }
++    issue.summary = issue.approvalContext.summary;
++  }
+ 
+   state.detectedIssue = issue;
+   state.error = issue.recommendation;
+@@ -565,25 +848,24 @@ async function applyArtifactProgress(state) {
+     return;
+   }
+ 
+-  for (const stage of PIPELINE_STAGES) {
+-    const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, stage.artifacts);
+-    const step = state.steps.find((item) => item.id === stage.id);
+-    if (artifact && step && step.status === 'running') {
+-      state.status = stage.state;
+-      state.error = null;
+-      state.detectedIssue = null;
+-      setStep(state, stage.id, stage.label, 'succeeded', artifact.name);
+-    }
+-  }
+-
+   const current = stageById(state.currentStep);
+   if (current) {
+-    const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, current.artifacts);
+-    if (artifact) {
++    const step = state.steps.find((item) => item.id === current.id);
++    const requirements = await allArtifactsExist(state.projectDir, state.jobId, current.artifacts, step?.startedAt || null);
++    if (requirements.ok) {
+       state.status = current.state;
+       state.error = null;
+       state.detectedIssue = null;
+-      setStep(state, current.id, current.label, 'succeeded', artifact.name);
++      setStep(state, current.id, current.label, 'succeeded', requirements.files.map((file) => file.name).join(', '));
++      if (current.id === 'codex-review-fix') {
++        state.status = 'review_changes_requested';
++        state.currentStep = null;
++        state.error = 'Codex가 리뷰 반영을 완료했습니다. Claude 재리뷰를 실행하세요.';
++      }
++      if (current.id === 'claude-review' || current.id === 'claude-re-review') {
++        await updateReviewSummary(state.projectDir, state.jobId, state);
++        applyReviewDecision(state);
++      }
+     }
+   }
+ }
+@@ -646,14 +928,60 @@ async function updateReviewSummary(projectDir, jobId, state) {
+     return;
+   }
+   const content = await fs.readFile(artifact.path, 'utf8').catch(() => '');
+-  const decisionLine = content.split(/\r?\n/).find((line) => /decision|verdict|approve|request changes|comment/i.test(line));
++  const decision = detectReviewDecision(content);
++  const decisionLine = content.split(/\r?\n/).find((line) => /decision|verdict|approve|request[_ -]?changes|block|승인|수정\s*요청|차단|보류/i.test(line));
+   state.summary.review = {
+     status: 'available',
+     file: artifact.name,
+-    decision: decisionLine ? decisionLine.trim() : null
++    decision,
++    decisionLine: decisionLine ? decisionLine.trim() : null
+   };
+ }
+ 
++function detectReviewDecision(content) {
++  const text = String(content || '');
++  if (/\bBLOCK\b|차단|보류/i.test(text)) {
++    return 'BLOCK';
++  }
++  if (/\bREQUEST[_ -]?CHANGES\b|수정\s*요청/i.test(text)) {
++    return 'REQUEST_CHANGES';
++  }
++  if (/\bAPPROVE\b|\bAPPROVED\b|승인/i.test(text)) {
++    return 'APPROVE';
++  }
++  return 'UNKNOWN';
++}
++
++function applyReviewDecision(state) {
++  const decision = state.summary.review.decision;
++  const now = new Date().toISOString();
++  if (decision === 'APPROVE') {
++    state.status = 'manual_final_approval_required';
++    state.currentStep = null;
++    state.finishedAt = now;
++    state.error = 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.';
++    return;
++  }
++  if (decision === 'REQUEST_CHANGES') {
++    state.status = 'review_changes_requested';
++    state.currentStep = null;
++    state.finishedAt = now;
++    state.error = 'Claude가 수정 요청을 남겼습니다. Codex가 리뷰 내용을 반영해야 합니다.';
++    return;
++  }
++  if (decision === 'BLOCK') {
++    state.status = 'blocked';
++    state.currentStep = null;
++    state.finishedAt = now;
++    state.error = 'Claude가 작업을 차단했습니다. 요청 범위나 안전 조건을 수정해야 합니다.';
++    return;
++  }
++  state.status = 'manual_review_required';
++  state.currentStep = null;
++  state.finishedAt = now;
++  state.error = 'Claude 리뷰 결정을 확인할 수 없습니다. review.md에서 APPROVE, REQUEST_CHANGES, BLOCK 중 하나를 확인하세요.';
++}
++
+ async function runPipeline(state, inputKo) {
+   const { projectDir, jobId } = state;
+   const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
+@@ -679,11 +1007,11 @@ async function runPipeline(state, inputKo) {
+       if (!sent.ok) {
+         throw new Error(`${step.label} 실패: ${sent.message || sent.stderr || 'tmux 전송 실패'}`);
+       }
+-      const artifact = await waitForArtifact(projectDir, jobId, step.artifacts, state);
++      const artifacts = await waitForArtifacts(projectDir, jobId, step.artifacts, state);
+       if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
+         return;
+       }
+-      if (!artifact) {
++      if (!artifacts) {
+         markManualRequired(state, step.id, step.label);
+         await refreshPipelineArtifacts(state);
+         return;
+@@ -691,7 +1019,7 @@ async function runPipeline(state, inputKo) {
+       state.status = step.state;
+       state.error = null;
+       state.detectedIssue = null;
+-      setStep(state, step.id, step.label, 'succeeded', artifact.name);
++      setStep(state, step.id, step.label, 'succeeded', artifacts.map((artifact) => artifact.name).join(', '));
+       await refreshPipelineArtifacts(state);
+ 
+       if (step.id === 'codex-implement') {
+@@ -723,11 +1051,11 @@ async function runPipeline(state, inputKo) {
+     if (!reviewed.ok) {
+       throw new Error(`Claude 리뷰 전송 실패: ${reviewed.message || reviewed.stderr || 'tmux 전송 실패'}`);
+     }
+-    const reviewArtifact = await waitForArtifact(projectDir, jobId, reviewerStep.artifacts, state);
++    const reviewArtifacts = await waitForArtifacts(projectDir, jobId, reviewerStep.artifacts, state);
+     if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
+       return;
+     }
+-    if (!reviewArtifact) {
++    if (!reviewArtifacts) {
+       markManualRequired(state, reviewerStep.id, reviewerStep.label);
+       await updateReviewSummary(projectDir, jobId, state);
+       await refreshPipelineArtifacts(state);
+@@ -736,13 +1064,10 @@ async function runPipeline(state, inputKo) {
+     state.status = reviewerStep.state;
+     state.error = null;
+     state.detectedIssue = null;
+-    setStep(state, reviewerStep.id, reviewerStep.label, 'succeeded', reviewArtifact.name);
++    setStep(state, reviewerStep.id, reviewerStep.label, 'succeeded', reviewArtifacts.map((artifact) => artifact.name).join(', '));
+     await updateReviewSummary(projectDir, jobId, state);
+     await refreshPipelineArtifacts(state);
+-
+-    state.status = 'succeeded';
+-    state.currentStep = null;
+-    state.finishedAt = new Date().toISOString();
++    applyReviewDecision(state);
+   } catch (error) {
+     state.status = 'failed';
+     state.error = error.message || '파이프라인 실행 실패';
+@@ -797,6 +1122,31 @@ function buildPrompt(role, projectDir, jobId, inputKo) {
+       '',
+       `Review the git diff saved at ${path.join(jobDir, 'local-diff.patch')} when present, ${path.join(jobDir, 'patch.md')}, and the approved request/plan.`,
+       `Write the review into ${path.join(jobDir, 'review.md')} using the Claude review output format.`,
++      'The review must include exactly one decision marker: APPROVE, REQUEST_CHANGES, or BLOCK.',
++      'Do not commit, push, merge, deploy, or run arbitrary shell commands.'
++    ].join('\n');
++  }
++
++  if (role === 'codex-review-fix') {
++    return [
++      'Use prompts/codex-implementer.md.',
++      common,
++      '',
++      `Read ${path.join(jobDir, 'patch.md')}, ${path.join(jobDir, 'review.md')}, and the current git diff.`,
++      'Apply only the changes explicitly requested by Claude review. Do not expand scope.',
++      `Update ${path.join(jobDir, 'patch.md')} and write ${path.join(jobDir, 'status.md')} with what changed and which checks ran.`,
++      'Do not commit, push, merge, deploy, or change secrets, .env, auth, payment, production infra, or database migrations.'
++    ].join('\n');
++  }
++
++  if (role === 'claude-re-review') {
++    return [
++      'Use prompts/claude.md.',
++      common,
++      '',
++      `Re-review the updated git diff, ${path.join(jobDir, 'patch.md')}, ${path.join(jobDir, 'status.md')}, and the previous review in ${path.join(jobDir, 'review.md')}.`,
++      `Update ${path.join(jobDir, 'review.md')} with the new review result.`,
++      'The review must include exactly one decision marker: APPROVE, REQUEST_CHANGES, or BLOCK.',
+       'Do not commit, push, merge, deploy, or run arbitrary shell commands.'
+     ].join('\n');
+   }
+@@ -883,6 +1233,51 @@ function handleError(res, error) {
+   res.status(400).json({ ok: false, error: error.message || '요청을 처리할 수 없습니다.' });
+ }
+ 
++function getOrCreatePipelineState(projectDir, jobId) {
++  const key = pipelineKey(projectDir, jobId);
++  let state = pipelineStates.get(key);
++  if (!state) {
++    state = createPipelineState(projectDir, jobId);
++    state.status = 'idle';
++    state.currentStep = null;
++    pipelineStates.set(key, state);
++  }
++  return state;
++}
++
++async function requireArtifacts(projectDir, jobId, names, message) {
++  const requirements = await allArtifactsExist(projectDir, jobId, names);
++  if (!requirements.ok) {
++    throw new Error(`${message} 누락: ${requirements.missing.join(', ')}`);
++  }
++}
++
++async function sendManualStage(projectDir, jobId, inputKo, stageId) {
++  const stage = stageById(stageId);
++  if (!stage) {
++    throw new Error('허용되지 않은 단계입니다.');
++  }
++  const state = getOrCreatePipelineState(projectDir, jobId);
++  if (ACTIVE_PIPELINE_STATES.has(state.status)) {
++    throw new Error('이미 실행 중인 단계가 있습니다.');
++  }
++  state.status = stage.state;
++  state.error = null;
++  state.detectedIssue = null;
++  state.finishedAt = null;
++  setStep(state, stage.id, stage.label, 'running');
++  const result = await sendToWindow(stage.role, projectDir, jobId, inputKo);
++  await appendPipelineLog(projectDir, jobId, stage.id, `${result.stdout || ''}${result.stderr || ''}${result.message || ''}`);
++  if (!result.ok) {
++    state.status = 'failed';
++    state.error = result.message || result.stderr || 'tmux 전송 실패';
++    state.finishedAt = new Date().toISOString();
++    setStep(state, stage.id, stage.label, 'failed', state.error);
++  }
++  await refreshPipelineArtifacts(state);
++  return { state, result };
++}
++
+ app.get('/api/status', async (req, res) => {
+   const result = await runFile(path.join(SCRIPTS_DIR, 'status-ai-team.sh'), []);
+   res.json(cleanOutput(result));
+@@ -1004,11 +1399,11 @@ app.get('/api/pipeline/status', async (req, res) => {
+       if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
+         await updateReviewSummary(projectDir, jobId, state);
+       }
+-      res.json(publicPipelineState(state));
++      res.json(await publicPipelineState(state));
+       return;
+     }
+ 
+-    res.json(publicIdlePipelineState(projectDir, jobId));
++    res.json(await publicIdlePipelineState(projectDir, jobId));
+   } catch (error) {
+     handleError(res, error);
+   }
+@@ -1049,6 +1444,20 @@ app.get('/api/tmux/output', async (req, res) => {
+   }
+ });
+ 
++app.get('/api/tmux/approval-context', async (req, res) => {
++  try {
++    const windowName = validateAiTmuxWindow(req.query.window);
++    const context = await buildApprovalContext(windowName, typeof req.query.step === 'string' ? req.query.step : null);
++    if (!context) {
++      res.status(404).json({ ok: false, error: '실제 승인 프롬프트를 찾지 못했습니다.' });
++      return;
++    }
++    res.json({ ok: true, approvalContext: context });
++  } catch (error) {
++    handleError(res, error);
++  }
++});
++
+ for (const [endpoint, keys] of [
+   ['/api/tmux/approve-once', ['1', 'Enter']],
+   ['/api/tmux/approve-session', ['2', 'Enter']],
+@@ -1124,15 +1533,35 @@ app.post('/api/service/restart-gui', async (req, res) => {
+ for (const [endpoint, role] of [
+   ['/api/send/claude-plan', 'claude-plan'],
+   ['/api/send/codex-implement', 'codex-implement'],
+-  ['/api/send/claude-review', 'claude-review']
++  ['/api/send/claude-review', 'claude-review'],
++  ['/api/send/codex-review-fix', 'codex-review-fix'],
++  ['/api/send/claude-re-review', 'claude-re-review']
+ ]) {
+   app.post(endpoint, async (req, res) => {
+     try {
+       const projectDir = await resolveProjectDir(req.body.projectDir);
+       const jobId = validateJobId(req.body.jobId);
+       const inputKo = typeof req.body.inputKo === 'string' ? req.body.inputKo : '';
+-      const result = await sendToWindow(role, projectDir, jobId, inputKo);
+-      res.json(cleanOutput(result));
++      if (role === 'codex-implement') {
++        await requireArtifacts(projectDir, jobId, ['plan.md', 'codex-task.md'], 'Claude 계획이 아직 완료되지 않았습니다. plan.md와 codex-task.md가 생성된 뒤 Codex를 실행할 수 있습니다.');
++      }
++      if (role === 'claude-review') {
++        await requireArtifacts(projectDir, jobId, ['patch.md'], 'patch.md가 생성된 뒤 Claude 리뷰를 실행할 수 있습니다.');
++      }
++      if (role === 'codex-review-fix') {
++        await requireArtifacts(projectDir, jobId, ['patch.md', 'review.md'], 'patch.md와 review.md가 생성된 뒤 Codex 리뷰 반영을 실행할 수 있습니다.');
++      }
++      if (role === 'claude-re-review') {
++        await requireArtifacts(projectDir, jobId, ['patch.md', 'review.md', 'status.md'], 'Codex 리뷰 반영 상태가 생성된 뒤 Claude 재리뷰를 실행할 수 있습니다.');
++      }
++      const stage = stageById(role);
++      const { state, result } = stage
++        ? await sendManualStage(projectDir, jobId, inputKo, role)
++        : { state: null, result: await sendToWindow(role, projectDir, jobId, inputKo) };
++      res.json({
++        ...cleanOutput(result),
++        pipeline: state ? (await publicPipelineState(state)).status : null
++      });
+     } catch (error) {
+       handleError(res, error);
+     }
+
+```
+
+## 2026-05-14T10:53:00.629Z — claude-review
+
+```
+(no output)
+```
diff --git a/docs/ai/jobs/mvp-007/request.ko.md b/docs/ai/jobs/mvp-007/request.ko.md
index dfd0315..9fc2cdb 100644
--- a/docs/ai/jobs/mvp-007/request.ko.md
+++ b/docs/ai/jobs/mvp-007/request.ko.md
@@ -1,227 +1,170 @@
 # 작업 ID
-mvp-007
+mvp-008
 
 # 작업명
-KIS Open API 모의투자 인증 / 계좌 / 시세 연결
+KIS 모의투자 주문 흐름 연결 준비
 
-미국주식 자동 페이퍼매매 시스템에 KIS Open API 모의투자 연결을 진행해줘.
+미국주식 자동 페이퍼매매 시스템에서 KIS 모의투자 주문 흐름을 연결할 준비를 해줘.
 
-현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 연결 검증이다.
+현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 주문 흐름 검증이다.
 live trading은 절대 활성화하지 않는다.
 
-## 현재 전제
+## 현재 상태
 
-mvp-006에서 KIS 설정 구조와 Broker Adapter 골격을 준비했다.
+mvp-006-1과 mvp-007에서 아래 작업이 완료되었다.
 
-이번 mvp-007에서는 가능한 범위 안에서 아래 기능을 연결한다.
+- paper-trading 프로젝트 기본 구조 생성
+- KIS 설정 구조 준비
+- `.env` 기반 KIS 설정 로딩
+- KIS Broker Adapter 골격
+- KIS Auth / Account / MarketData Client 골격
+- `/paper/status`에 KIS 상태 표시
+- secret/account masking 테스트
+- 74개 테스트 통과
 
-1. KIS 모의투자 인증 토큰 발급 연결
-2. 토큰 refresh / 만료 처리 구조
-3. KIS 모의투자 계좌 정보 조회
-4. KIS 해외주식 또는 미국주식 시세 조회 구조
-5. Broker healthcheck 강화
-6. `/paper/status` 또는 기존 status endpoint에 KIS 연결 상태 표시
-7. 실제 주문은 아직 연결하지 않음
+이번 mvp-008에서는 실제 실계좌 주문이 아니라,
+KIS 모의투자 주문 흐름을 안전하게 연결할 준비를 한다.
 
-## 보안 조건
+## 핵심 목표
 
-KIS 모의투자 계좌번호, app key, app secret은 `.env`에 저장되어 있다고 가정한다.
+Strategy → RiskEngine → OMS → BrokerAdapter → KIS Broker 경로가 유지되도록 하면서,
+KIS 모의투자 주문 메서드의 안전한 경계를 만든다.
 
-중요:
-- 실제 계좌번호, app key, app secret 값을 코드에 쓰지 마.
-- patch.md, review.md, 로그, 테스트 출력에 실제 secret을 노출하지 마.
-- `.env.example`에는 placeholder만 유지해.
-- `.env`는 Git에 추가하지 마.
-- 설정 객체 repr/logging에서 app secret이 노출되지 않게 해.
-- 테스트에서도 실제 secret 값을 출력하지 마.
-
-## 공식 문서 조건
-
-KIS Open API endpoint, TR ID, payload는 공식 문서 기준으로만 구현해야 한다.
-
-중요:
-- 공식 문서나 프로젝트 내 명확한 문서가 없으면 endpoint를 추측해서 만들지 마.
-- 확실하지 않은 endpoint, TR ID, header, payload는 TODO로 남겨.
-- fake endpoint를 만들지 마.
-- 실제 주문 endpoint는 이번 작업에서 구현하지 마.
-- 인증 / 계좌조회 / 시세조회도 확실한 공식 정보가 없으면 fail-closed + TODO로 남겨.
-
-## 이번 구현 범위
-
-가능하면 아래 기능을 구현해줘.
-
-### 1. KIS Auth Client
+단, 공식 문서가 확인되지 않은 endpoint, TR ID, payload는 절대 추측해서 구현하지 않는다.
 
-- `.env`에서 아래 값을 읽는다.
-  - KIS_ENV
-  - KIS_ACCOUNT_NO
-  - KIS_APP_KEY
-  - KIS_APP_SECRET
-- 모의투자 환경인지 확인한다.
-- 인증 토큰 발급 메서드를 만든다.
-- 토큰 만료 시 refresh 또는 재발급 가능 구조를 만든다.
-- 인증 실패 시 fail-closed 한다.
-- secret이 로그에 찍히지 않게 한다.
+## 구현할 내용
 
-필요 메서드 예시:
-- authenticate()
-- refresh_token()
-- get_access_token()
-- is_authenticated()
-- clear_token()
+### 1. KIS 주문 메서드 경계 정리
 
-### 2. KIS Account Client
+`KisBroker` 또는 현재 구조에 맞는 KIS adapter에 아래 주문 관련 메서드를 정리해줘.
 
-- 계좌 정보 조회 골격 또는 실제 연결을 구현한다.
-- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
-- 계좌번호는 출력 시 마스킹한다.
-- 실패 시 주문 가능 상태로 전환하지 않는다.
-
-필요 메서드 예시:
-- get_account()
-- get_positions()
-- get_cash_balance()
-
-### 3. KIS Market Data Client
-
-- 미국주식 시세 조회 구조를 만든다.
-- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
-- 최소 quote 모델을 반환한다.
-- 실패 시 stale / unavailable 상태로 처리한다.
-
-필요 메서드 예시:
-- get_quote(symbol)
-- get_last_price(symbol)
-- healthcheck_market_data()
-
-### 4. KIS Broker Adapter 연결
+- place_order()
+- cancel_order()
+- replace_order()
+- get_open_orders()
+- get_fills()
+- get_order_status()
 
-기존 BrokerAdapter 구조를 유지한다.
+조건:
+- 실제 endpoint/TR ID/payload를 추측해서 만들지 마.
+- 공식 문서가 없으면 TODO + fail-closed로 둬.
+- 메서드는 존재하되, 실주문 전송은 아직 하지 마.
+- NotImplementedError 또는 안전한 Rejected 상태를 반환하게 해.
+- 에러 메시지는 secret/account를 노출하지 않아야 한다.
 
-- authenticate()
-- refresh_token()
-- get_account()
-- get_positions()
-- get_quote()
-- healthcheck()
+### 2. OMS → KIS Broker 연결 준비
 
-주문 관련 메서드는 아직 실제 전송하지 않는다.
+OMS가 broker adapter를 통해 주문을 보낼 수 있는 구조인지 점검하고,
+필요하면 interface를 정리해줘.
 
-- place_order()
-- cancel_order()
-- replace_order()
+중요:
+- Strategy가 KIS를 직접 호출하면 안 된다.
+- Agent/LLM이 KIS를 직접 호출하면 안 된다.
+- OMS를 우회해서 주문하면 안 된다.
+- 모든 주문은 반드시 RiskEngine을 통과해야 한다.
+- OMS만 executable order를 만들 수 있다.
+
+### 3. KIS 모의투자 주문 요청 모델 준비
+
+실제 전송은 하지 말고, 내부 도메인 모델 기준으로 KIS 주문 요청 변환 경계를 만들어줘.
+
+예:
+- symbol
+- side
+- quantity
+- order_type
+- limit_price
+- extended_hours
+- account_no_masked
+- broker_environment
 
-위 주문 메서드는 이번 단계에서 fail-closed 또는 NotImplemented 상태로 둔다.
+조건:
+- 시장가 주문은 금지
+- 지정가 주문만 허용
+- live trading이면 차단
+- KIS_ENV가 paper가 아니면 차단
+- 계좌번호 원문은 출력하지 말고 마스킹만 사용
 
-## 주문 안전 조건
+### 4. 주문 안전 guard 추가
 
-반드시 유지해.
+KIS 주문 흐름에 아래 guard를 적용해줘.
 
-- live trading은 false
-- TRADING_MODE는 paper
-- 시장가 주문 금지
-- 실주문 전송 금지
-- Strategy가 KIS Adapter를 직접 호출하지 않음
-- Agent/LLM이 직접 주문하지 않음
-- 모든 주문은 Strategy → RiskEngine → OMS → BrokerAdapter 경로 유지
-- OMS 우회 금지
-- RiskEngine 우회 금지
+- TRADING_MODE=paper만 허용
+- LIVE_TRADING_ENABLED=false 확인
+- ALLOW_MARKET_ORDERS=false 확인
+- KIS_ENV=paper 확인
+- order_type이 market이면 거절
+- quantity가 0 이하이면 거절
+- limit_price가 없으면 거절
+- stale quote면 거절
+- kill switch가 켜져 있으면 거절
 
-## 상태 API
+### 5. `/paper/status` 또는 status에 주문 준비 상태 추가
 
-가능하면 `/paper/status` 또는 기존 `/status`에 아래 정보를 추가해줘.
+가능하면 아래 상태를 추가해줘.
 
-- broker_type
-- broker_environment
-- kis_config_loaded
-- kis_authenticated
-- kis_account_loaded
-- kis_market_data_available
-- live_trading_enabled
-- allow_market_orders
-- last_broker_error
+- kis_order_entry_ready
+- kis_order_entry_mode: disabled | paper_guarded | not_implemented
+- kis_order_methods_fail_closed: true
+- live_trading_enabled: false
+- allow_market_orders: false
 - secret_exposed: false
 
-중요:
-- app key, app secret, 계좌번호 원문은 절대 출력하지 마.
-- 계좌번호는 필요하면 마스킹해서 보여줘.
+실제 app key, app secret, 계좌번호 원문은 절대 출력하지 마.
 
-## 테스트 요구사항
+### 6. 테스트 추가
 
 아래 테스트를 추가해줘.
 
-1. `.env` 기반 KIS config 로딩 테스트
-2. app secret이 repr/logging/status에 노출되지 않는지 테스트
-3. KIS_ENV=paper 기본 동작 테스트
-4. live trading 기본 false 테스트
-5. 시장가 주문 기본 금지 테스트
-6. 인증 client가 secret을 직접 출력하지 않는지 테스트
-7. 공식 문서 정보가 없을 때 endpoint를 추측하지 않고 TODO/fail-closed 되는지 테스트
-8. 주문 메서드가 아직 실주문을 전송하지 않는지 테스트
-9. BrokerAdapter 인터페이스가 깨지지 않는지 테스트
-10. `/paper/status` 또는 `/status`에 KIS 상태가 안전하게 표시되는지 테스트
+1. KIS place_order가 실주문을 보내지 않고 fail-closed 되는지
+2. KIS cancel_order가 실취소를 보내지 않고 fail-closed 되는지
+3. KIS replace_order가 실정정을 보내지 않고 fail-closed 되는지
+4. market order가 거절되는지
+5. limit_price 없는 주문이 거절되는지
+6. live trading true이면 거절되는지
+7. KIS_ENV가 paper가 아니면 거절되는지
+8. Strategy가 KIS adapter를 직접 호출하지 않는지
+9. OMS 경로를 우회하지 않는지
+10. status에 secret/account 원문이 노출되지 않는지
+11. 기존 74개 테스트가 계속 통과하는지
 
 ## 수정 가능 파일
 
-필요한 경우 아래 파일을 수정해도 된다.
+필요하면 아래 파일을 수정해도 된다.
 
-- app/adapters/brokers/kis.py
-- app/adapters/brokers/base.py
-- app/core/config.py
-- app/api/routes.py
-- app/runtime/paper_runner.py
-- app/monitoring/status.py
-- app/domain/*
-- tests/*
-- .env.example
-- README.md
-- docs/architecture.md
-- docs/runbook.md
+- projects/paper-trading/app/broker/kis.py
+- projects/paper-trading/app/broker/base.py
+- projects/paper-trading/app/oms/*
+- projects/paper-trading/app/risk/*
+- projects/paper-trading/app/api/routes.py
+- projects/paper-trading/app/api/server.py
+- projects/paper-trading/app/config/*
+- projects/paper-trading/app/models/*
+- projects/paper-trading/tests/*
+- projects/paper-trading/README.md
+- docs/ai/jobs/mvp-008/patch.md
 
-실제 프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.
+프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.
 
 ## 금지 사항
 
-- 실제 KIS app key, app secret, 계좌번호를 코드에 쓰지 마.
-- 실제 값을 patch.md, review.md, 로그에 출력하지 마.
-- `.env` 파일을 Git에 추가하지 마.
-- live trading을 true로 바꾸지 마.
-- 실계좌 주문 기능을 만들지 마.
-- 주문 endpoint를 연결하지 마.
-- KIS endpoint / TR ID / payload를 추측해서 만들지 마.
+- 실제 KIS endpoint를 추측해서 만들지 마.
+- TR ID를 추측해서 넣지 마.
+- 실제 주문 전송 코드를 만들지 마.
+- live trading을 활성화하지 마.
 - 시장가 주문을 허용하지 마.
-- 브로커 API를 Strategy에서 직접 호출하게 만들지 마.
+- app key, app secret, 계좌번호 원문을 코드/문서/로그/test output에 쓰지 마.
+- `.env` 파일을 Git에 추가하지 마.
+- Strategy가 KIS를 직접 호출하게 만들지 마.
+- Agent/LLM이 직접 주문하게 만들지 마.
 - auth, payment, production infra, database migrations는 건드리지 마.
 - git commit, push, merge는 자동화하지 마.
 
 ## 검증
 
-가능하면 아래를 실행해줘.
-
-- python -m compileall app tests
-- python -m pytest -p no:cacheprovider
-
-만약 현재 프로젝트 구조가 Python이 아니거나 테스트 명령이 다르면,
-현재 repo 구조에 맞는 안전한 검증 명령을 실행하고 patch.md에 이유를 적어줘.
-
-## 완료 후 patch.md에 정리할 내용
-
-1. 어떤 파일을 수정했는지
-2. KIS 인증 구조가 어떻게 되었는지
-3. 계좌 조회 구조가 어떻게 되었는지
-4. 시세 조회 구조가 어떻게 되었는지
-5. 실제 주문 기능이 여전히 비활성인지
-6. secret이 노출되지 않는지
-7. 어떤 테스트를 실행했는지
-8. 공식 문서가 없어 TODO로 남긴 부분
-9. 다음 mvp에서 무엇을 하면 되는지
-
-## 다음 단계 예고
-
-mvp-008에서는 KIS 모의투자 주문 흐름을 연결할 예정이다.
-단, mvp-008에서도 live trading은 비활성이고, 소액 검증 전까지 실계좌 주문은 금지한다.
-
-## 추가 조건
+아래를 실행해줘.
 
-- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
-- 필요한 경우에만 최소한의 질문을 해.
\ No newline at end of file
+```bash
+cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
+.venv/bin/python -m compileall app tests
+.venv/bin/python -m pytest -p no:cacheprovider
\ No newline at end of file
diff --git a/projects/paper-trading/.env.example b/projects/paper-trading/.env.example
index 4558286..4d493ff 100644
--- a/projects/paper-trading/.env.example
+++ b/projects/paper-trading/.env.example
@@ -1,6 +1,7 @@
 TRADING_MODE=paper
 LIVE_TRADING_ENABLED=false
 ALLOW_MARKET_ORDERS=false
+KILL_SWITCH_ENGAGED=false
 
 # Alpaca Paper trading base URL must be provided by the user in .env. This repository does not guess vendor endpoints.
 ALPACA_PAPER_API_BASE=
diff --git a/projects/paper-trading/README.md b/projects/paper-trading/README.md
index 351e213..260c572 100644
--- a/projects/paper-trading/README.md
+++ b/projects/paper-trading/README.md
@@ -81,6 +81,45 @@ Blocked candidates never reach OMS.
 | `KIS_APP_KEY` | KIS app key | `.env`에서만 |
 | `KIS_APP_SECRET` | KIS app secret | `.env`에서만 |
 | `ALLOW_MARKET_ORDERS` | 항상 `false` | `true`이면 `load_settings()` 거부 |
+| `KILL_SWITCH_ENGAGED` | 주문 kill switch | `true`이면 RiskEngine/KIS pre-flight 거부 |
+
+### 주문 흐름 안전 가드와 내부 모델 (mvp-009)
+
+`KisBroker.place_order` / `cancel_order` / `replace_order` 호출 시 다음 pre-flight 가드를 통과해야 합니다(`validate_kis_order_request`):
+
+- `trading_mode == paper`
+- `live_trading_enabled is False`
+- `allow_market_orders is False`
+- `kis_env == "paper"`
+- `kill_switch_engaged is False`
+- `order_type in (LIMIT, STOP_LIMIT)`
+- `quantity > 0`
+- `limit_price > 0`
+
+가드 실패 시 `KisOrderRejectedError(reason)`로 즉시 거절합니다. 메시지에는 사유 코드만 들어가며 raw credentials/계좌번호는 포함되지 않습니다.
+
+가드를 통과하더라도 KIS HTTP 전송은 본 단계에서 구현되지 않습니다. 다음 메서드는 항상 `NotImplementedError`로 fail-closed 합니다: `place_order`, `cancel_order`, `replace_order`, `get_open_orders`, `get_fills`, `get_order_status`.
+
+`KisOrderRequest`는 내부 도메인 변환 모델로, KIS HTTP payload로 직렬화되지 않고 단위 테스트 및 향후 mvp 연결 시 입력 모델로만 사용됩니다. 계좌번호는 `account_no_masked`로만 보유합니다.
+
+`kill_switch_engaged=true`로 설정하면 RiskEngine이 모든 주문을 즉시 거절하고, KIS pre-flight도 동일하게 거절합니다. `.env`의 `KILL_SWITCH_ENGAGED=true`로 활성화할 수 있습니다.
+
+`KisOrderRequest`는 `symbol`, `market`, `side`, `quantity`, `order_type`, `limit_price`, `extended_hours`,
+`account_no_masked`, `broker_environment`, `idempotency_key`를 보유합니다. `idempotency_key`는
+`kis-paper-{oms_id}` 형식으로 결정적으로 생성되며, raw 계좌번호는 포함하지 않습니다.
+
+`KisOrderResponse`는 향후 KIS 응답을 내부 모델로 보관하기 위한 구조입니다. `raw_response_sanitized`는
+`sanitize_kis_response()`를 통과한 dict만 저장해야 하며, app key/secret/account/access token으로 보이는
+키 또는 값은 `<redacted>`로 치환됩니다.
+
+`KisBroker.capabilities()`는 현재 모든 주문 관련 기능을 `false`로 반환합니다. 공식 KIS 모의투자 주문 문서로
+endpoint/TR ID/payload를 확인하기 전까지 submission/cancel/replace/open_orders/fills/order_status는 모두
+사용 불가 상태이며 fail-closed입니다.
+
+`/paper/status`는 `kis_order_entry_ready`, `kis_order_entry_mode`(`disabled | paper_guarded | not_implemented`),
+`kis_order_methods_fail_closed`, `kill_switch_engaged`와 함께 `kis_order_submission_available`,
+`kis_cancel_available`, `kis_replace_available`, `kis_open_orders_available`, `kis_fills_available`를 노출합니다.
+현 단계에서 가용성 필드는 모두 `false`입니다.
 
 `.env`는 Git에 올라가지 않습니다(루트 `.gitignore` + 프로젝트 `.gitignore` 양쪽에서 ignore). `.env.example`은 placeholder만 보관합니다.
 
diff --git a/projects/paper-trading/app/api/routes.py b/projects/paper-trading/app/api/routes.py
index b9a7edf..8aca423 100644
--- a/projects/paper-trading/app/api/routes.py
+++ b/projects/paper-trading/app/api/routes.py
@@ -28,6 +28,8 @@ def healthz() -> dict[str, bool]:
 def paper_status(request: Request) -> dict[str, Any]:
     settings = request.app.state.settings
     broker = request.app.state.broker
+    session_router = getattr(request.app.state, "session_router", None)
+    portfolio = getattr(request.app.state, "portfolio", None)
     kis_broker = getattr(request.app.state, "kis_broker", None)
     kis_loaded = bool(
         settings.kis_env
@@ -37,6 +39,31 @@ def paper_status(request: Request) -> dict[str, Any]:
     )
     kis_health = kis_broker.healthcheck() if kis_broker else {}
     market_health = kis_health.get("market_data", {})
+    kis_order_entry_mode = "disabled"
+    if kis_broker is not None:
+        settings_safe = (
+            settings.trading_mode.value == "paper"
+            and settings.live_trading_enabled is False
+            and settings.allow_market_orders is False
+            and settings.kis_env == "paper"
+            and settings.kill_switch_engaged is False
+        )
+        kis_order_entry_mode = "not_implemented" if settings_safe else "disabled"
+    kis_order_entry_ready = kis_broker is not None and kis_order_entry_mode != "disabled"
+    capabilities = (
+        kis_broker.capabilities()
+        if kis_broker
+        else {
+            "submission": False,
+            "cancel": False,
+            "replace": False,
+            "open_orders": False,
+            "fills": False,
+            "order_status": False,
+        }
+    )
+    session_policy = session_router.policy_for_us() if session_router is not None else None
+    portfolio_snapshot = portfolio.get_snapshot() if portfolio is not None else None
     return {
         "ok": True,
         "mode": settings.trading_mode.value,
@@ -63,6 +90,26 @@ def paper_status(request: Request) -> dict[str, Any]:
         "account_no_masked": kis_broker.account.masked_account_no() if kis_broker else "<unset>",
         "secret_exposed": False,
         "configured_brokers": list(getattr(request.app.state, "configured_brokers", [])),
+        "kis_order_entry_ready": kis_order_entry_ready,
+        "kis_order_entry_mode": kis_order_entry_mode,
+        "kis_order_methods_fail_closed": True,
+        "kill_switch_engaged": bool(settings.kill_switch_engaged),
+        "kis_order_submission_available": bool(capabilities.get("submission", False)),
+        "kis_cancel_available": bool(capabilities.get("cancel", False)),
+        "kis_replace_available": bool(capabilities.get("replace", False)),
+        "kis_open_orders_available": bool(capabilities.get("open_orders", False)),
+        "kis_fills_available": bool(capabilities.get("fills", False)),
+        "session": {
+            "market": "US",
+            "current": session_policy.session.value if session_policy else None,
+            "orders_allowed": bool(session_policy.orders_allowed) if session_policy else False,
+            "allowed_strategies": list(session_policy.allowed_strategies) if session_policy else [],
+        },
+        "portfolio": {
+            "positions_count": len(portfolio_snapshot.positions) if portfolio_snapshot else 0,
+            "market_value": str(portfolio_snapshot.market_value) if portfolio_snapshot else "0",
+            "realized_pnl": str(portfolio_snapshot.realized_pnl) if portfolio_snapshot else "0",
+        },
     }
 
 
diff --git a/projects/paper-trading/app/api/server.py b/projects/paper-trading/app/api/server.py
index ba4b9cd..0d4c629 100644
--- a/projects/paper-trading/app/api/server.py
+++ b/projects/paper-trading/app/api/server.py
@@ -6,8 +6,10 @@ from app.api.routes import router
 from app.broker.paper import PaperBroker
 from app.config import load_settings
 from app.oms.manager import OMS
+from app.portfolio import PortfolioService
 from app.risk.engine import RiskEngine
 from app.runtime.paper_runner import PaperRunner
+from app.session import SessionRouter
 from app.strategy import create_strategy
 
 
@@ -19,6 +21,8 @@ def create_app() -> FastAPI:
         broker = PaperBroker()
         oms = OMS(settings, risk, broker)
         strategy = create_strategy("premarket_gap_volume_breakout", settings)
+        session_router = SessionRouter()
+        portfolio = PortfolioService()
 
         # Probe optional brokers — record which ones are instantiable given
         # current .env. The KIS adapter is never wired into OMS in this phase;
@@ -38,6 +42,8 @@ def create_app() -> FastAPI:
         app.state.oms = oms
         app.state.strategy = strategy
         app.state.runner = PaperRunner(settings, strategy, oms)
+        app.state.session_router = session_router
+        app.state.portfolio = portfolio
         app.state.configured_brokers = configured_brokers
         app.state.kis_broker = kis_broker
         yield
diff --git a/projects/paper-trading/app/broker/kis.py b/projects/paper-trading/app/broker/kis.py
index e345d65..69265c8 100644
--- a/projects/paper-trading/app/broker/kis.py
+++ b/projects/paper-trading/app/broker/kis.py
@@ -6,11 +6,13 @@ not implemented until endpoints, TR IDs, payloads, and response shapes are
 confirmed from official KIS Open API documentation.
 """
 
+from dataclasses import dataclass
 from datetime import datetime, timezone
+from decimal import Decimal
 from typing import Any
 
 from app.config import Settings
-from app.domain.enums import TradingMode
+from app.domain.enums import OrderType, Side, TradingMode
 from app.domain.orders import BrokerOrder, OrderAck
 
 
@@ -30,6 +32,118 @@ class KisDataUnavailableError(KisError):
     """Market data unavailable or stale."""
 
 
+class KisOrderRejectedError(KisError):
+    """Order rejected by KIS adapter pre-flight guard."""
+
+    def __init__(self, reason: str) -> None:
+        super().__init__(f"KIS order rejected: {reason}")
+        self.reason = reason
+
+
+@dataclass(frozen=True)
+class KisOrderRequest:
+    """Internal KIS order request model with no raw account number."""
+
+    symbol: str
+    market: str
+    side: Side
+    quantity: int
+    order_type: OrderType
+    limit_price: Decimal
+    extended_hours: bool
+    account_no_masked: str
+    broker_environment: str
+    idempotency_key: str
+
+
+@dataclass(frozen=True)
+class KisOrderResponse:
+    """Internal KIS order response model with sanitized raw broker response."""
+
+    internal_order_id: str
+    broker_order_id: str | None
+    broker: str
+    status: str
+    submitted_at: datetime
+    symbol: str
+    side: Side
+    quantity: int
+    limit_price: Decimal
+    raw_response_sanitized: dict[str, Any]
+
+
+SENSITIVE_RESPONSE_KEYS = {
+    "app_key",
+    "appkey",
+    "appsecret",
+    "app_secret",
+    "account_no",
+    "accountno",
+    "cano",
+    "acct_no",
+    "access_token",
+    "accesstoken",
+    "authorization",
+    "tr_key",
+    "trkey",
+    "secret",
+}
+
+
+def sanitize_kis_response(raw: dict[str, Any] | None, settings: Settings) -> dict[str, Any]:
+    """Return a copy of a KIS response with credentials/account values redacted."""
+    if not isinstance(raw, dict):
+        return {}
+
+    sensitive_values = {
+        value
+        for value in (settings.kis_app_key, settings.kis_app_secret, settings.kis_account_no)
+        if value
+    }
+
+    def sanitize_value(value: Any) -> Any:
+        if isinstance(value, dict):
+            return {key: sanitize_field(key, nested) for key, nested in value.items()}
+        if isinstance(value, list):
+            return [sanitize_value(item) for item in value]
+        if isinstance(value, str) and value in sensitive_values:
+            return "<redacted>"
+        return value
+
+    def sanitize_field(key: str, value: Any) -> Any:
+        normalized = key.replace("-", "_").lower()
+        if normalized in SENSITIVE_RESPONSE_KEYS:
+            return "<redacted>"
+        return sanitize_value(value)
+
+    return {key: sanitize_field(key, value) for key, value in raw.items()}
+
+
+def validate_kis_order_request(settings: Settings, broker_order: BrokerOrder) -> None:
+    """Pre-flight guards for KIS order paths."""
+    if settings.trading_mode != TradingMode.PAPER:
+        raise KisOrderRejectedError("trading_mode_not_paper")
+    if settings.live_trading_enabled:
+        raise KisOrderRejectedError("live_trading_enabled")
+    if settings.allow_market_orders:
+        raise KisOrderRejectedError("market_orders_allowed_flag_set")
+    if settings.kis_env != "paper":
+        raise KisOrderRejectedError("kis_env_not_paper")
+    if settings.kill_switch_engaged:
+        raise KisOrderRejectedError("kill_switch_engaged")
+    if broker_order.order_type not in (OrderType.LIMIT, OrderType.STOP_LIMIT):
+        raise KisOrderRejectedError("order_type_not_limit")
+    if broker_order.quantity is None or broker_order.quantity <= 0:
+        raise KisOrderRejectedError("quantity_invalid")
+    if broker_order.limit_price is None or broker_order.limit_price <= 0:
+        raise KisOrderRejectedError("limit_price_invalid")
+    if broker_order.quote_timestamp is None:
+        raise KisOrderRejectedError("stale_quote")
+    quote_age = (broker_order.submitted_at - broker_order.quote_timestamp).total_seconds()
+    if quote_age > settings.premarket_max_quote_age_seconds:
+        raise KisOrderRejectedError("stale_quote")
+
+
 class KisAuthClient:
     """KIS authentication token lifecycle state machine.
 
@@ -235,16 +349,71 @@ class KisBroker:
         )
 
     def place_order(self, broker_order: BrokerOrder) -> OrderAck:
+        validate_kis_order_request(self._settings, broker_order)
+        self._to_kis_request(broker_order)
         raise NotImplementedError(
-            "KIS place_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard."
+            "KIS place_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard. "
+            "Pre-flight passed but HTTP transmission is intentionally not implemented until KIS Open API "
+            "endpoints/TR IDs/payloads are confirmed from official documentation."
         )
 
     def cancel_order(self, broker_order_id: str) -> None:
+        if self._settings.trading_mode != TradingMode.PAPER:
+            raise KisOrderRejectedError("trading_mode_not_paper")
+        if self._settings.live_trading_enabled:
+            raise KisOrderRejectedError("live_trading_enabled")
+        if self._settings.allow_market_orders:
+            raise KisOrderRejectedError("market_orders_allowed_flag_set")
+        if self._settings.kis_env != "paper":
+            raise KisOrderRejectedError("kis_env_not_paper")
+        if self._settings.kill_switch_engaged:
+            raise KisOrderRejectedError("kill_switch_engaged")
         raise NotImplementedError("KIS cancel_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard.")
 
     def replace_order(self, broker_order_id: str, broker_order: BrokerOrder) -> OrderAck:
+        validate_kis_order_request(self._settings, broker_order)
+        self._to_kis_request(broker_order)
         raise NotImplementedError("KIS replace_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard.")
 
+    def get_fills(self) -> list[OrderAck]:
+        raise NotImplementedError(
+            "KIS get_fills(): TODO — confirm fills endpoint, TR ID, payload, and response shape "
+            "from KIS Open API official documentation. Do not invent endpoints."
+        )
+
+    def get_order_status(self, broker_order_id: str) -> dict[str, Any]:
+        raise NotImplementedError(
+            "KIS get_order_status(): TODO — confirm order status endpoint, TR ID, payload, and response shape "
+            "from KIS Open API official documentation. Do not invent endpoints."
+        )
+
+    def capabilities(self) -> dict[str, bool]:
+        return {
+            "submission": False,
+            "cancel": False,
+            "replace": False,
+            "open_orders": False,
+            "fills": False,
+            "order_status": False,
+        }
+
+    def _idempotency_key_for(self, broker_order: BrokerOrder) -> str:
+        return f"kis-paper-{broker_order.oms_id}"
+
+    def _to_kis_request(self, broker_order: BrokerOrder) -> KisOrderRequest:
+        return KisOrderRequest(
+            symbol=broker_order.symbol,
+            market="US",
+            side=broker_order.side,
+            quantity=broker_order.quantity,
+            order_type=broker_order.order_type,
+            limit_price=broker_order.limit_price,
+            extended_hours=False,
+            account_no_masked=self._account.masked_account_no(),
+            broker_environment=self._settings.kis_env or "paper",
+            idempotency_key=self._idempotency_key_for(broker_order),
+        )
+
     def healthcheck(self) -> dict[str, Any]:
         market = self._market_data.healthcheck_market_data()
         return {
@@ -256,6 +425,8 @@ class KisBroker:
             "market_data": market,
             "last_error": self._last_error,
             "order_execution_implemented": False,
+            "order_methods_fail_closed": True,
+            "capabilities": self.capabilities(),
         }
 
     def submit(self, broker_order: BrokerOrder) -> OrderAck:
diff --git a/projects/paper-trading/app/config.py b/projects/paper-trading/app/config.py
index 2187701..e7fa0e7 100644
--- a/projects/paper-trading/app/config.py
+++ b/projects/paper-trading/app/config.py
@@ -33,6 +33,7 @@ class Settings:
     kis_app_key: str | None = field(default=None, repr=False)
     kis_app_secret: str | None = field(default=None, repr=False)
     allow_market_orders: bool = False
+    kill_switch_engaged: bool = False
 
 
 def _decimal_env(name: str, default: Decimal) -> Decimal:
@@ -112,4 +113,5 @@ def load_settings() -> Settings:
         kis_app_key=_str_env("KIS_APP_KEY"),
         kis_app_secret=_str_env("KIS_APP_SECRET"),
         allow_market_orders=False,
+        kill_switch_engaged=_bool_env("KILL_SWITCH_ENGAGED", False),
     )
diff --git a/projects/paper-trading/app/domain/orders.py b/projects/paper-trading/app/domain/orders.py
index f5ffb31..b43de91 100644
--- a/projects/paper-trading/app/domain/orders.py
+++ b/projects/paper-trading/app/domain/orders.py
@@ -14,6 +14,7 @@ class OrderIntent:
     limit_price: Decimal
     stop_price: Decimal | None = None
     client_tag: str | None = None
+    quote_timestamp: datetime | None = None
 
     def __post_init__(self) -> None:
         if self.symbol != self.symbol.upper():
@@ -50,6 +51,7 @@ class BrokerOrder:
     submitted_at: datetime
     stop_price: Decimal | None = None
     client_tag: str | None = None
+    quote_timestamp: datetime | None = None
 
 
 @dataclass(frozen=True)
diff --git a/projects/paper-trading/app/oms/manager.py b/projects/paper-trading/app/oms/manager.py
index ea90f13..e50ea02 100644
--- a/projects/paper-trading/app/oms/manager.py
+++ b/projects/paper-trading/app/oms/manager.py
@@ -46,5 +46,6 @@ class OMS:
             submitted_at=now,
             stop_price=order.stop_price,
             client_tag=order.client_tag,
+            quote_timestamp=intent.quote_timestamp,
         )
         return self._broker.submit(broker_order)
diff --git a/projects/paper-trading/app/risk/engine.py b/projects/paper-trading/app/risk/engine.py
index 444d650..5293d91 100644
--- a/projects/paper-trading/app/risk/engine.py
+++ b/projects/paper-trading/app/risk/engine.py
@@ -18,6 +18,8 @@ class RiskEngine:
         self._settings = settings
 
     def evaluate(self, intent: OrderIntent) -> RiskDecision:
+        if self._settings.kill_switch_engaged:
+            return RiskDecision(False, "kill_switch_engaged")
         if self._settings.trading_mode != TradingMode.PAPER:
             return RiskDecision(False, "paper_trading_required")
         if self._settings.live_trading_enabled:
diff --git a/projects/paper-trading/app/strategy/premarket_gap.py b/projects/paper-trading/app/strategy/premarket_gap.py
index 69daad3..4ea817d 100644
--- a/projects/paper-trading/app/strategy/premarket_gap.py
+++ b/projects/paper-trading/app/strategy/premarket_gap.py
@@ -81,6 +81,7 @@ class PremarketGapVolumeBreakoutStrategy(Strategy):
             order_type=OrderType.LIMIT,
             limit_price=limit_price,
             client_tag=self.name,
+            quote_timestamp=snapshot.timestamp,
         )
         return StrategyResult(
             symbol=snapshot.symbol,
diff --git a/projects/paper-trading/tests/test_api_paper_status.py b/projects/paper-trading/tests/test_api_paper_status.py
index 79333c9..cb4000c 100644
--- a/projects/paper-trading/tests/test_api_paper_status.py
+++ b/projects/paper-trading/tests/test_api_paper_status.py
@@ -8,6 +8,7 @@ KIS_ENV_KEYS = (
     "KIS_ACCOUNT_NO",
     "KIS_APP_KEY",
     "KIS_APP_SECRET",
+    "KILL_SWITCH_ENGAGED",
 )
 
 
@@ -53,6 +54,15 @@ def test_paper_status_kis_metadata_fields(monkeypatch):
     assert body["secret_exposed"] is False
     assert "kis_" + "secret_exposed" not in body
     assert isinstance(body["configured_brokers"], list)
+    assert body["kis_order_entry_ready"] is False
+    assert body["kis_order_entry_mode"] == "disabled"
+    assert body["kis_order_methods_fail_closed"] is True
+    assert body["kill_switch_engaged"] is False
+    assert body["kis_order_submission_available"] is False
+    assert body["kis_cancel_available"] is False
+    assert body["kis_replace_available"] is False
+    assert body["kis_open_orders_available"] is False
+    assert body["kis_fills_available"] is False
     # Credentials must never appear in the response body.
     body_text = response.text
     for needle in ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_NO"):
@@ -67,6 +77,7 @@ def test_paper_status_with_kis_config_masks_account(monkeypatch):
     monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")
     monkeypatch.setenv("KIS_APP_KEY", "fake-key")
     monkeypatch.setenv("KIS_APP_SECRET", "fake-secret")
+    monkeypatch.setenv("KILL_SWITCH_ENGAGED", "false")
 
     with TestClient(create_app()) as client:
         response = client.get("/paper/status")
@@ -81,6 +92,15 @@ def test_paper_status_with_kis_config_masks_account(monkeypatch):
     assert body["last_broker_error"] is None
     assert body["account_no_masked"] == "***5678"
     assert body["secret_exposed"] is False
+    assert body["kis_order_entry_ready"] is True
+    assert body["kis_order_entry_mode"] == "not_implemented"
+    assert body["kis_order_methods_fail_closed"] is True
+    assert body["kill_switch_engaged"] is False
+    assert body["kis_order_submission_available"] is False
+    assert body["kis_cancel_available"] is False
+    assert body["kis_replace_available"] is False
+    assert body["kis_open_orders_available"] is False
+    assert body["kis_fills_available"] is False
 
     body_text = response.text
     for needle in ("12345678", "fake-key", "fake-secret", "KIS_APP_KEY", "KIS_APP_SECRET"):
diff --git a/projects/paper-trading/tests/test_broker_interface.py b/projects/paper-trading/tests/test_broker_interface.py
index 2768d4d..09b857f 100644
--- a/projects/paper-trading/tests/test_broker_interface.py
+++ b/projects/paper-trading/tests/test_broker_interface.py
@@ -4,8 +4,19 @@ from dataclasses import replace
 
 import pytest
 
-from app.broker.kis import KisAccountClient, KisAuthClient, KisBroker, KisMarketDataClient
+from datetime import datetime, timezone
+from decimal import Decimal
+
+from app.broker.kis import (
+    KisAccountClient,
+    KisAuthClient,
+    KisBroker,
+    KisMarketDataClient,
+    KisOrderRejectedError,
+)
 from app.domain.enums import TradingMode
+from app.domain.enums import OrderType, Side
+from app.domain.orders import BrokerOrder
 
 
 REQUIRED_METHODS = (
@@ -19,6 +30,7 @@ REQUIRED_METHODS = (
     "place_order",
     "cancel_order",
     "replace_order",
+    "capabilities",
     "healthcheck",
     # BrokerAdapter Protocol compatibility
     "submit",
@@ -38,6 +50,24 @@ def _configured(settings):
     )
 
 
+def _broker_order(**overrides) -> BrokerOrder:
+    now = datetime.now(timezone.utc)
+    data = {
+        "symbol": "AAPL",
+        "side": Side.BUY,
+        "quantity": 10,
+        "order_type": OrderType.LIMIT,
+        "limit_price": Decimal("100"),
+        "risk_token": "rt",
+        "created_at": now,
+        "oms_id": "oms-1",
+        "submitted_at": now,
+        "quote_timestamp": now,
+    }
+    data.update(overrides)
+    return BrokerOrder(**data)
+
+
 def test_kis_broker_has_all_required_methods(settings):
     broker = KisBroker(_configured(settings))
     for name in REQUIRED_METHODS:
@@ -78,18 +108,20 @@ def test_kis_broker_missing_credentials_fails_closed(settings, missing):
 
 def test_kis_place_cancel_replace_not_implemented(settings):
     broker = KisBroker(_configured(settings))
+    with pytest.raises(KisOrderRejectedError):
+        broker.place_order(_broker_order(quantity=0))
     with pytest.raises(NotImplementedError):
-        broker.place_order(None)  # type: ignore[arg-type]
+        broker.place_order(_broker_order())
     with pytest.raises(NotImplementedError):
         broker.cancel_order("x")
     with pytest.raises(NotImplementedError):
-        broker.replace_order("x", None)  # type: ignore[arg-type]
+        broker.replace_order("x", _broker_order())
 
 
 def test_kis_protocol_methods_delegate_to_not_implemented(settings):
     broker = KisBroker(_configured(settings))
     with pytest.raises(NotImplementedError):
-        broker.submit(None)  # type: ignore[arg-type]
+        broker.submit(_broker_order())
     with pytest.raises(NotImplementedError):
         broker.cancel("x")
     with pytest.raises(NotImplementedError):
@@ -112,6 +144,44 @@ def test_kis_data_methods_not_implemented(settings):
             getattr(broker, method)(*args)
 
 
+def test_kis_broker_has_get_fills_and_get_order_status(settings):
+    broker = KisBroker(_configured(settings))
+    assert callable(broker.get_fills)
+    assert callable(broker.get_order_status)
+    with pytest.raises(NotImplementedError, match="TODO"):
+        broker.get_fills()
+    with pytest.raises(NotImplementedError, match="TODO"):
+        broker.get_order_status("oms-1")
+
+
+def test_kis_order_request_class_is_exported():
+    from app.broker.kis import (
+        KisOrderRejectedError,
+        KisOrderRequest,
+        KisOrderResponse,
+        sanitize_kis_response,
+        validate_kis_order_request,
+    )
+
+    assert KisOrderRequest is not None
+    assert KisOrderResponse is not None
+    assert KisOrderRejectedError is not None
+    assert callable(sanitize_kis_response)
+    assert callable(validate_kis_order_request)
+
+
+def test_kis_broker_capabilities_are_exported_and_fail_closed(settings):
+    broker = KisBroker(_configured(settings))
+    assert broker.capabilities() == {
+        "submission": False,
+        "cancel": False,
+        "replace": False,
+        "open_orders": False,
+        "fills": False,
+        "order_status": False,
+    }
+
+
 def test_kis_healthcheck_returns_disconnected_dict(settings):
     broker = KisBroker(_configured(settings))
     h = broker.healthcheck()
@@ -122,6 +192,9 @@ def test_kis_healthcheck_returns_disconnected_dict(settings):
     assert h["account_loaded"] is False
     assert h["last_error"] is None
     assert h["order_execution_implemented"] is False
+    assert h["order_methods_fail_closed"] is True
+    assert h["capabilities"]["submission"] is False
+    assert h["capabilities"]["fills"] is False
     assert h["market_data"]["connected"] is False
     reason = h["market_data"]["reason"].lower()
     assert "skeleton" in reason or "not implemented" in reason
diff --git a/projects/paper-trading/tests/test_risk_engine.py b/projects/paper-trading/tests/test_risk_engine.py
index 16d598e..3854adc 100644
--- a/projects/paper-trading/tests/test_risk_engine.py
+++ b/projects/paper-trading/tests/test_risk_engine.py
@@ -27,6 +27,18 @@ def test_risk_rejects_live_enabled(settings):
     assert not decision.approved
 
 
+def test_risk_engine_kill_switch_at_top(settings):
+    bad = replace(
+        settings,
+        kill_switch_engaged=True,
+        trading_mode=TradingMode.LIVE,
+        live_trading_enabled=True,
+    )
+    decision = RiskEngine(bad).evaluate(intent())
+    assert decision.approved is False
+    assert decision.reason == "kill_switch_engaged"
+
+
 def test_risk_rejects_allowlist(settings):
     decision = RiskEngine(settings).evaluate(intent(symbol="TSLA"))
     assert decision.reason == "symbol_not_allowed"
diff --git a/projects/paper-trading/tests/test_strategy_premarket_gap.py b/projects/paper-trading/tests/test_strategy_premarket_gap.py
index 37540c2..a7f481d 100644
--- a/projects/paper-trading/tests/test_strategy_premarket_gap.py
+++ b/projects/paper-trading/tests/test_strategy_premarket_gap.py
@@ -49,10 +49,12 @@ def test_stale_quote_blocked(settings, make_snapshot):
 
 
 def test_strategy_result_is_not_executable_order(settings, make_snapshot):
-    result = PremarketGapVolumeBreakoutStrategy(settings).evaluate(make_snapshot())
+    snapshot = make_snapshot()
+    result = PremarketGapVolumeBreakoutStrategy(settings).evaluate(snapshot)
     assert isinstance(result.non_executable_order_intent, OrderIntent)
     assert not isinstance(result.non_executable_order_intent, BrokerOrder)
     assert not isinstance(result.non_executable_order_intent, Order)
+    assert result.non_executable_order_intent.quote_timestamp == snapshot.timestamp
 
 
 def test_no_market_order_generated(settings, make_snapshot):
diff --git a/web/public/app.js b/web/public/app.js
index f27f460..d9fc2c2 100644
--- a/web/public/app.js
+++ b/web/public/app.js
@@ -9,6 +9,7 @@ const inputKoEl = document.querySelector('#inputKo');
 const outputEl = document.querySelector('#output');
 const artifactListEl = document.querySelector('#artifactList');
 const runPipelineButton = document.querySelector('#runPipeline');
+const sendButtons = [...document.querySelectorAll('[data-send]')];
 const pipelineStateEl = document.querySelector('#pipelineState');
 const pipelineJobIdEl = document.querySelector('#pipelineJobId');
 const pipelineStageEl = document.querySelector('#pipelineStage');
@@ -31,6 +32,15 @@ const approvalModalEl = document.querySelector('#approvalModal');
 const approvalModalStepEl = document.querySelector('#approvalModalStep');
 const approvalModalWindowEl = document.querySelector('#approvalModalWindow');
 const approvalModalSummaryEl = document.querySelector('#approvalModalSummary');
+const approvalModalTypeEl = document.querySelector('#approvalModalType');
+const approvalModalCommandEl = document.querySelector('#approvalModalCommand');
+const approvalModalCwdEl = document.querySelector('#approvalModalCwd');
+const approvalModalRiskEl = document.querySelector('#approvalModalRisk');
+const approvalModalRecommendationEl = document.querySelector('#approvalModalRecommendation');
+const approvalModalRawEl = document.querySelector('#approvalModalRaw');
+const approvalModalRiskWarningEl = document.querySelector('#approvalModalRiskWarning');
+const approvalModalApproveOnceEl = document.querySelector('#approvalModalApproveOnce');
+const approvalModalApproveSessionEl = document.querySelector('#approvalModalApproveSession');
 const aiControlButtons = [
   document.querySelector('#approveOnce'),
   document.querySelector('#approveSession'),
@@ -59,8 +69,18 @@ const finalPipelineStates = new Set([
   'failed',
   'blocked',
   'manual_review_required',
+  'review_approved',
+  'review_changes_requested',
+  'manual_final_approval_required',
   'idle'
 ]);
+const stageWindows = {
+  'claude-plan': 'claude',
+  'codex-implement': 'codex',
+  'claude-review': 'claude',
+  'codex-review-fix': 'codex',
+  'claude-re-review': 'claude'
+};
 
 projectDirEl.value = state.projectDir;
 jobIdEl.value = state.jobId;
@@ -183,6 +203,10 @@ runPipelineButton.addEventListener('click', async () => {
 });
 
 document.querySelector('#pipelineStatus').addEventListener('click', refreshPipelineStatus);
+document.querySelector('#finalManualReview').addEventListener('click', () => {
+  writeOutput('최종 확인', 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.');
+  refreshPipelineStatus();
+});
 
 document.querySelector('#resetPipeline').addEventListener('click', async () => {
   const result = await runAction('파이프라인 상태 초기화', () => requestJson('/api/pipeline/reset', {
@@ -370,6 +394,7 @@ function renderPipelineStatus(status) {
     summaryDiffEl.textContent = '-';
     summaryReviewEl.textContent = '-';
     runPipelineButton.disabled = false;
+    updateSendButtonGates(null);
     return;
   }
 
@@ -389,6 +414,7 @@ function renderPipelineStatus(status) {
   pipelineTargetWindowEl.textContent = pipeline.targetWindow || '-';
   pipelineWaitingApprovalEl.textContent = pipeline.waitingApproval ? '예' : '아니오';
   renderDetectedIssue(approvalRequest ? null : pipeline.detectedIssue);
+  updateSendButtonGates(pipeline);
 
   if (pipeline.targetWindow && tmuxWindowEl.value !== pipeline.targetWindow) {
     tmuxWindowEl.value = pipeline.targetWindow;
@@ -410,8 +436,9 @@ function renderPipelineStatus(status) {
   } else {
     currentApprovalRequest = null;
     closeApprovalModal();
-    pipelineGuidanceEl.hidden = true;
-    pipelineGuidanceEl.textContent = '';
+    const requirementsText = renderRequirementsText(pipeline.requirements);
+    pipelineGuidanceEl.hidden = !requirementsText;
+    pipelineGuidanceEl.textContent = requirementsText;
     approvalInlinePromptEl.hidden = true;
   }
 
@@ -464,6 +491,47 @@ function renderPipelineStatus(status) {
   summaryNextActionEl.textContent = pipeline.nextAction || '-';
 }
 
+function renderRequirementsText(requirements) {
+  if (!requirements || !requirements.files || requirements.files.length === 0) {
+    return '';
+  }
+  const lines = [
+    `필수 파일 (${requirements.label || '현재 단계'}):`,
+    ...requirements.files.map((file) => `- ${file.name}: ${file.exists ? 'ready' : 'missing'}`),
+    `다음 단계 가능: ${requirements.nextStageAllowed ? 'yes' : 'no'}`
+  ];
+  return lines.join('\n');
+}
+
+function hasArtifact(pipeline, name) {
+  return (pipeline?.artifacts || []).some((artifact) => (artifact.name || artifact) === name);
+}
+
+function updateSendButtonGates(pipeline) {
+  sendButtons.forEach((button) => {
+    const target = button.dataset.send;
+    let disabled = false;
+    let title = '';
+    if (!pipeline) {
+      disabled = false;
+    } else if (target === 'codex-implement') {
+      disabled = !hasArtifact(pipeline, 'plan.md') || !hasArtifact(pipeline, 'codex-task.md');
+      title = disabled ? 'Claude 계획이 아직 완료되지 않았습니다. plan.md와 codex-task.md가 생성된 뒤 Codex를 실행할 수 있습니다.' : '';
+    } else if (target === 'claude-review') {
+      disabled = !hasArtifact(pipeline, 'patch.md');
+      title = disabled ? 'patch.md가 생성된 뒤 Claude 리뷰를 실행할 수 있습니다.' : '';
+    } else if (target === 'codex-review-fix') {
+      disabled = pipeline.state !== 'review_changes_requested';
+      title = disabled ? 'Claude가 수정 요청을 남긴 뒤 실행할 수 있습니다.' : '';
+    } else if (target === 'claude-re-review') {
+      disabled = !hasArtifact(pipeline, 'status.md');
+      title = disabled ? 'Codex 리뷰 반영 후 status.md가 생성된 뒤 실행할 수 있습니다.' : '';
+    }
+    button.disabled = disabled;
+    button.title = title;
+  });
+}
+
 function getApprovalRequest(status, pipeline) {
   const issue = pipeline.detectedIssue || {};
   const isApproval = pipeline.state === 'approval_required' || issue.type === 'approval_required';
@@ -472,16 +540,18 @@ function getApprovalRequest(status, pipeline) {
   }
 
   const targetWindow = issue.window || pipeline.targetWindow;
-  if (!['claude', 'codex'].includes(targetWindow)) {
+  const stageTargetWindow = stageWindows[pipeline.step] || pipeline.targetWindow || targetWindow;
+  if (!['claude', 'codex'].includes(stageTargetWindow)) {
     return null;
   }
 
   const jobId = status.jobId || jobIdEl.value.trim() || '-';
   const step = pipeline.step || '-';
-  const rawSummary = issue.summary || pipeline.message || '';
-  const summary = cleanApprovalSummary(targetWindow);
-  const key = `${jobId}:${step}:${targetWindow}:${rawSummary || summary}`;
-  return { key, step, targetWindow, summary };
+  const approvalContext = issue.approvalContext || null;
+  const rawSummary = approvalContext?.rawBlock || issue.summary || pipeline.message || '';
+  const summary = approvalContext?.summary || cleanApprovalSummary(stageTargetWindow);
+  const key = `${jobId}:${step}:${stageTargetWindow}:${rawSummary || summary}`;
+  return { key, step, targetWindow: stageTargetWindow, summary, approvalContext };
 }
 
 function cleanApprovalSummary(windowName) {
@@ -495,10 +565,41 @@ function openApprovalModal(request, force) {
     return;
   }
   lastApprovalKey = request.key;
-  approvalModalStepEl.textContent = request.step || '-';
-  approvalModalWindowEl.textContent = request.targetWindow || '-';
-  approvalModalSummaryEl.textContent = request.summary || '-';
+  renderApprovalContext(request, request.approvalContext);
   approvalModalEl.hidden = false;
+  if (!request.approvalContext) {
+    loadApprovalContext(request);
+  }
+}
+
+async function loadApprovalContext(request) {
+  try {
+    const result = await requestJson(`/api/tmux/approval-context?window=${encodeURIComponent(request.targetWindow)}&step=${encodeURIComponent(request.step || '')}`);
+    if (!currentApprovalRequest || currentApprovalRequest.key !== request.key) {
+      return;
+    }
+    currentApprovalRequest.approvalContext = result.approvalContext;
+    renderApprovalContext(currentApprovalRequest, result.approvalContext);
+  } catch (error) {
+    approvalModalRawEl.textContent = error.message;
+  }
+}
+
+function renderApprovalContext(request, context) {
+  const risk = context?.risk || 'unknown';
+  approvalModalStepEl.textContent = request.step || context?.step || '-';
+  approvalModalWindowEl.textContent = request.targetWindow || context?.window || '-';
+  approvalModalSummaryEl.textContent = context?.summary || request.summary || '-';
+  approvalModalTypeEl.textContent = context?.type || 'unknown';
+  approvalModalCommandEl.textContent = context?.commandOrTarget || '확인 불가';
+  approvalModalCwdEl.textContent = context?.workingDirectory || '-';
+  approvalModalRiskEl.textContent = risk;
+  approvalModalRiskEl.dataset.risk = risk;
+  approvalModalRecommendationEl.textContent = context?.recommendation || '직접 확인 필요';
+  approvalModalRawEl.textContent = context?.rawBlock || '원문을 불러오는 중입니다.';
+  approvalModalRiskWarningEl.textContent = context?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.';
+  approvalModalApproveOnceEl.disabled = !context?.canApproveOnce;
+  approvalModalApproveSessionEl.disabled = !context?.canApproveSession;
 }
 
 function closeApprovalModal() {
@@ -510,6 +611,10 @@ async function sendApprovalModalAction(endpoint) {
     writeOutput('승인 명령 실패', '승인 대상 창을 확인할 수 없습니다.');
     return;
   }
+  if (!approvalEndpointAllowed(endpoint, currentApprovalRequest.approvalContext)) {
+    writeOutput('승인 명령 차단', currentApprovalRequest.approvalContext?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.');
+    return;
+  }
 
   try {
     await requestJson(endpoint, {
@@ -524,6 +629,16 @@ async function sendApprovalModalAction(endpoint) {
   }
 }
 
+function approvalEndpointAllowed(endpoint, context) {
+  if (endpoint.endsWith('/approve-once')) {
+    return Boolean(context?.canApproveOnce);
+  }
+  if (endpoint.endsWith('/approve-session')) {
+    return Boolean(context?.canApproveSession);
+  }
+  return true;
+}
+
 function normalizePipelineStatus(payload) {
   if (payload && payload.status && typeof payload.status === 'object') {
     return {
@@ -534,6 +649,7 @@ function normalizePipelineStatus(payload) {
       waitingApproval: Boolean(payload.status.waitingApproval),
       detectedIssue: payload.status.detectedIssue || null,
       artifacts: payload.status.artifacts || [],
+      requirements: payload.status.requirements || null,
       gitDiff: payload.status.gitDiff || '-',
       reviewStatus: payload.status.reviewStatus || '-',
       nextAction: payload.status.nextAction || '-'
@@ -548,6 +664,7 @@ function normalizePipelineStatus(payload) {
     waitingApproval: false,
     detectedIssue: null,
     artifacts: payload && payload.artifacts ? payload.artifacts : [],
+    requirements: null,
     gitDiff: '-',
     reviewStatus: '-',
     nextAction: '-'
@@ -625,6 +742,10 @@ async function sendTmuxControl(title, endpoint) {
     writeOutput(`${title} 실패`, 'Manual Shell(git-shell)은 비AI 창입니다. 승인/거절 키 입력은 Claude 또는 Codex 창에서만 사용하세요.');
     return null;
   }
+  if (currentApprovalRequest && currentApprovalRequest.targetWindow === windowName && !approvalEndpointAllowed(endpoint, currentApprovalRequest.approvalContext)) {
+    writeOutput(`${title} 차단`, currentApprovalRequest.approvalContext?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.');
+    return null;
+  }
   const result = await runAction(title, () => requestJson(endpoint, {
     method: 'POST',
     body: JSON.stringify({ window: windowName })
diff --git a/web/public/index.html b/web/public/index.html
index a02de7a..60b76f9 100644
--- a/web/public/index.html
+++ b/web/public/index.html
@@ -16,42 +16,55 @@
     </header>
 
     <main class="layout">
-      <section class="panel setup">
-        <h2>작업 설정</h2>
-        <label>
-          프로젝트 경로
-          <input id="projectDir" type="text" autocomplete="off" spellcheck="false">
-        </label>
+      <section class="panel quick-actions">
+        <h2>핵심 실행</h2>
         <label>
           작업 ID
           <input id="jobId" type="text" value="mvp-001" autocomplete="off" spellcheck="false">
         </label>
         <label>
           한국어 작업 요청
-          <textarea id="inputKo" spellcheck="false" rows="14"></textarea>
+          <textarea id="inputKo" spellcheck="false" rows="6"></textarea>
         </label>
         <p class="field-hint">여기에는 한국어 작업 요청만 입력하세요. 쉘 설정 명령, 실행 명령, 토큰, 비밀값은 넣지 않습니다.</p>
-        <div class="role-display" aria-label="역할 안내">
-          <div>
-            <strong>Claude</strong>
-            <span>planning / requirements / review</span>
-          </div>
-          <div>
-            <strong>Codex</strong>
-            <span>implementation / tests / patch summary</span>
-          </div>
-        </div>
-        <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
         <div class="pipeline-runner">
           <button id="runPipeline" class="primary-action" type="button">Claude → Codex → Claude 전체 실행</button>
           <div class="primary-actions">
             <button data-send="claude-plan" type="button">Claude 계획 생성</button>
             <button data-send="codex-implement" type="button">Codex 구현 실행</button>
             <button data-send="claude-review" type="button">Claude 리뷰 실행</button>
+            <button data-send="codex-review-fix" type="button">Codex 리뷰 반영 실행</button>
+            <button data-send="claude-re-review" type="button">Claude 재리뷰 실행</button>
+            <button id="finalManualReview" type="button">최종 확인으로 이동</button>
           </div>
         </div>
       </section>
 
+      <section class="panel control-panel">
+        <h2>승인 / 서비스 제어</h2>
+        <p class="warning-text">승인은 Claude 또는 Codex AI CLI 창에만 키 입력을 보내는 기능입니다. Manual Shell(git-shell)은 사람이 직접 git/test 명령을 실행하는 비AI 창입니다.</p>
+        <label>
+          제어할 tmux 창
+          <select id="tmuxWindow"></select>
+        </label>
+        <div class="actions control-actions">
+          <button id="approveOnce" type="button">승인 / 계속 진행</button>
+          <button id="approveSession" type="button">세션 승인</button>
+          <button id="rejectAction" type="button">거절</button>
+          <button id="interruptAction" type="button">중단</button>
+          <button id="restartAiTeam" type="button">AI팀 재시작</button>
+          <button id="restartGui" type="button">GUI 서버 재시작</button>
+        </div>
+      </section>
+
+      <section class="panel tmux-panel">
+        <div class="panel-head">
+          <h2>실시간 tmux 출력</h2>
+          <button id="refreshTmuxOutput" type="button">출력 새로고침</button>
+        </div>
+        <pre id="tmuxOutput" aria-live="polite"></pre>
+      </section>
+
       <section class="panel pipeline-status">
         <div class="panel-head">
           <h2>파이프라인 상태</h2>
@@ -96,29 +109,42 @@
         <div id="pipelineSteps" class="pipeline-steps"></div>
       </section>
 
-      <section class="panel control-panel">
-        <h2>승인 / 서비스 제어</h2>
-        <p class="warning-text">승인은 Claude 또는 Codex AI CLI 창에만 키 입력을 보내는 기능입니다. Manual Shell(git-shell)은 사람이 직접 git/test 명령을 실행하는 비AI 창입니다.</p>
+      <details class="panel job-settings">
+        <summary>작업 설정</summary>
         <label>
-          제어할 tmux 창
-          <select id="tmuxWindow"></select>
+          프로젝트 경로
+          <input id="projectDir" type="text" autocomplete="off" spellcheck="false">
         </label>
-        <div class="actions control-actions">
-          <button id="approveOnce" type="button">승인 / 계속 진행</button>
-          <button id="approveSession" type="button">세션 승인</button>
-          <button id="rejectAction" type="button">거절</button>
-          <button id="interruptAction" type="button">중단</button>
-          <button id="restartAiTeam" type="button">AI팀 재시작</button>
-          <button id="restartGui" type="button">GUI 서버 재시작</button>
+        <div class="role-display" aria-label="역할 안내">
+          <div>
+            <strong>Claude</strong>
+            <span>planning / requirements / review</span>
+          </div>
+          <div>
+            <strong>Codex</strong>
+            <span>implementation / tests / patch summary</span>
+          </div>
         </div>
-      </section>
+        <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
+      </details>
 
-      <section class="panel tmux-panel">
+      <details class="panel advanced-panel">
+        <summary>고급 제어</summary>
+        <div class="actions">
+          <button id="startTeam" type="button">AI 팀 시작</button>
+          <button id="createJob" type="button">작업 폴더 생성</button>
+          <button id="saveInput" type="button">request.ko.md 저장</button>
+          <button id="gitStatus" type="button">git status</button>
+          <button id="gitDiff" type="button">git diff</button>
+        </div>
+      </details>
+
+      <section class="panel artifacts">
         <div class="panel-head">
-          <h2>실시간 tmux 출력</h2>
-          <button id="refreshTmuxOutput" type="button">출력 새로고침</button>
+          <h2>산출물</h2>
+          <button id="loadArtifacts" type="button">목록 새로고침</button>
         </div>
-        <pre id="tmuxOutput" aria-live="polite"></pre>
+        <div id="artifactList" class="artifact-list"></div>
       </section>
 
       <section class="panel result-summary">
@@ -143,25 +169,6 @@
         </dl>
       </section>
 
-      <details class="panel advanced-panel">
-        <summary>고급 제어</summary>
-        <div class="actions">
-          <button id="startTeam" type="button">AI 팀 시작</button>
-          <button id="createJob" type="button">작업 폴더 생성</button>
-          <button id="saveInput" type="button">request.ko.md 저장</button>
-          <button id="gitStatus" type="button">git status</button>
-          <button id="gitDiff" type="button">git diff</button>
-        </div>
-      </details>
-
-      <section class="panel artifacts">
-        <div class="panel-head">
-          <h2>산출물</h2>
-          <button id="loadArtifacts" type="button">목록 새로고침</button>
-        </div>
-        <div id="artifactList" class="artifact-list"></div>
-      </section>
-
       <section class="panel output-panel">
         <div class="panel-head">
           <h2>출력</h2>
@@ -191,11 +198,36 @@
             <dt>감지 요약</dt>
             <dd id="approvalModalSummary">-</dd>
           </div>
+          <div>
+            <dt>요청 유형</dt>
+            <dd id="approvalModalType">-</dd>
+          </div>
+          <div>
+            <dt>명령/대상</dt>
+            <dd id="approvalModalCommand">-</dd>
+          </div>
+          <div>
+            <dt>작업 디렉터리</dt>
+            <dd id="approvalModalCwd">-</dd>
+          </div>
+          <div>
+            <dt>위험도</dt>
+            <dd id="approvalModalRisk">-</dd>
+          </div>
+          <div>
+            <dt>추천 행동</dt>
+            <dd id="approvalModalRecommendation">-</dd>
+          </div>
         </dl>
+        <details class="approval-raw">
+          <summary>원문 보기</summary>
+          <pre id="approvalModalRaw">-</pre>
+        </details>
         <p class="modal-warning">주의: 이 버튼은 현재 AI CLI 창에 키 입력을 보내는 기능입니다. 위험한 명령은 승인하지 마세요.</p>
+        <p id="approvalModalRiskWarning" class="modal-warning">-</p>
         <div class="modal-actions">
-          <button data-approval-action="/api/tmux/approve-once" type="button">1회 승인</button>
-          <button data-approval-action="/api/tmux/approve-session" type="button">세션 승인</button>
+          <button id="approvalModalApproveOnce" data-approval-action="/api/tmux/approve-once" type="button">1회 승인</button>
+          <button id="approvalModalApproveSession" data-approval-action="/api/tmux/approve-session" type="button">세션 승인</button>
           <button data-approval-action="/api/tmux/reject" class="danger-action" type="button">거절</button>
           <button data-approval-action="/api/tmux/interrupt" class="danger-action" type="button">중단</button>
           <button id="dismissApprovalModal" type="button">닫기</button>
diff --git a/web/public/style.css b/web/public/style.css
index 9d50479..e9c85a8 100644
--- a/web/public/style.css
+++ b/web/public/style.css
@@ -64,11 +64,11 @@ h2 {
 }
 
 .layout {
-  display: grid;
-  grid-template-columns: minmax(320px, 0.95fr) minmax(360px, 1.05fr);
+  display: flex;
+  flex-direction: column;
   gap: 18px;
   padding: 22px;
-  max-width: 1440px;
+  max-width: 1100px;
   margin: 0 auto;
 }
 
@@ -80,14 +80,6 @@ h2 {
   padding: 18px;
 }
 
-.setup {
-  grid-row: span 4;
-}
-
-.output-panel {
-  grid-column: 2;
-}
-
 .panel-head {
   display: flex;
   align-items: center;
@@ -103,6 +95,26 @@ h2 {
   justify-content: flex-end;
 }
 
+.quick-actions {
+  display: grid;
+  gap: 12px;
+}
+
+.job-settings {
+  padding: 14px 18px;
+}
+
+.job-settings > summary {
+  cursor: pointer;
+  font-size: 18px;
+  font-weight: 800;
+  padding: 4px 0;
+}
+
+.job-settings[open] {
+  padding-bottom: 18px;
+}
+
 label {
   display: grid;
   gap: 7px;
@@ -173,7 +185,7 @@ select {
 }
 
 textarea {
-  min-height: 330px;
+  min-height: 140px;
   resize: vertical;
   padding: 12px;
   line-height: 1.5;
@@ -484,6 +496,37 @@ button:disabled {
   font-weight: 800;
 }
 
+.approval-details dd[data-risk="low"] {
+  color: #0f766e;
+}
+
+.approval-details dd[data-risk="medium"],
+.approval-details dd[data-risk="unknown"] {
+  color: #92400e;
+}
+
+.approval-details dd[data-risk="high"] {
+  color: var(--danger);
+}
+
+.approval-raw {
+  margin-top: 14px;
+}
+
+.approval-raw summary {
+  cursor: pointer;
+  color: var(--muted);
+  font-size: 13px;
+  font-weight: 800;
+}
+
+.approval-raw pre {
+  min-height: 120px;
+  max-height: 220px;
+  margin-top: 8px;
+  font-size: 12px;
+}
+
 .modal-warning {
   margin: 14px 0 0;
   padding: 10px 12px;
@@ -610,16 +653,9 @@ pre {
   }
 
   .layout {
-    grid-template-columns: 1fr;
     padding: 14px;
   }
 
-  .setup,
-  .output-panel {
-    grid-row: auto;
-    grid-column: auto;
-  }
-
   .step-grid {
     grid-template-columns: 1fr;
   }
diff --git a/web/server.js b/web/server.js
index 0ce1e5d..7d07b26 100644
--- a/web/server.js
+++ b/web/server.js
@@ -16,6 +16,8 @@ const SAFE_WINDOWS = {
   'claude-plan': 'claude',
   'codex-implement': 'codex',
   'claude-review': 'claude',
+  'codex-review-fix': 'codex',
+  'claude-re-review': 'claude',
   claude: 'claude',
   codex: 'codex'
 };
@@ -56,9 +58,7 @@ const ISSUE_PATTERNS = [
   {
     type: 'approval_required',
     patterns: [
-      /approval|approve|allow|continue|proceed|permission/i,
-      /승인|허용|계속 진행|진행하시겠습니까|거절/i,
-      /1\).*(approve|allow|승인|계속)|2\).*(session|세션)|3\).*(reject|거절)/i
+      /allow execution|allow edit|do you want to proceed|would you like to continue|allow for this session|no, suggest changes|enter your response/i
     ]
   },
   {
@@ -80,12 +80,16 @@ const pipelineStates = new Map();
 const PIPELINE_STAGES = [
   { id: 'claude-plan', state: 'claude_planning', label: 'Claude 계획 생성', role: 'claude-plan', window: 'claude', artifacts: ['plan.md', 'codex-task.md'] },
   { id: 'codex-implement', state: 'codex_implementing', label: 'Codex 구현 실행', role: 'codex-implement', window: 'codex', artifacts: ['patch.md'] },
-  { id: 'claude-review', state: 'claude_reviewing', label: 'Claude 리뷰 실행', role: 'claude-review', window: 'claude', artifacts: ['review.md'] }
+  { id: 'claude-review', state: 'claude_reviewing', label: 'Claude 리뷰 실행', role: 'claude-review', window: 'claude', artifacts: ['review.md'] },
+  { id: 'codex-review-fix', state: 'codex_fixing_review', label: 'Codex 리뷰 반영 실행', role: 'codex-review-fix', window: 'codex', artifacts: ['status.md'] },
+  { id: 'claude-re-review', state: 'claude_re_reviewing', label: 'Claude 재리뷰 실행', role: 'claude-re-review', window: 'claude', artifacts: ['review.md'] }
 ];
 const ACTIVE_PIPELINE_STATES = new Set([
   'claude_planning',
   'codex_implementing',
   'claude_reviewing',
+  'codex_fixing_review',
+  'claude_re_reviewing',
   'approval_required'
 ]);
 const FINAL_PIPELINE_STATES = new Set([
@@ -93,6 +97,9 @@ const FINAL_PIPELINE_STATES = new Set([
   'failed',
   'blocked',
   'manual_review_required',
+  'review_approved',
+  'review_changes_requested',
+  'manual_final_approval_required',
   'idle'
 ]);
 const ARTIFACT_PRIORITY = [
@@ -240,8 +247,97 @@ function currentTargetWindow(state) {
   return stage ? stage.window : null;
 }
 
-function publicIdlePipelineState(projectDir = null, jobId = null) {
+function stageByState(status) {
+  return PIPELINE_STAGES.find((stage) => stage.state === status) || null;
+}
+
+function stageForGate(status, currentStep) {
+  return stageById(currentStep) || stageByState(status) || PIPELINE_STAGES[0];
+}
+
+function nextStageGate(state) {
+  if (!state) {
+    return PIPELINE_STAGES[0];
+  }
+  if (state.status === 'succeeded' || state.status === 'review_approved' || state.status === 'manual_final_approval_required') {
+    return null;
+  }
+  if (state.status === 'review_changes_requested') {
+    return stageById('codex-review-fix');
+  }
+  return stageForGate(state.status, state.currentStep);
+}
+
+function artifactPath(projectDir, jobId, name) {
+  return path.join(projectDir, 'docs', 'ai', 'jobs', jobId, name);
+}
+
+async function artifactStat(projectDir, jobId, name) {
+  const stat = await fs.stat(artifactPath(projectDir, jobId, name)).catch(() => null);
+  return stat && stat.isFile() && stat.size > 0 ? stat : null;
+}
+
+async function artifactExists(projectDir, jobId, name, afterIso = null) {
+  const stat = await artifactStat(projectDir, jobId, name);
+  if (!stat) {
+    return false;
+  }
+  if (!afterIso) {
+    return true;
+  }
+  const after = Date.parse(afterIso);
+  return Number.isNaN(after) ? true : stat.mtimeMs >= after;
+}
+
+async function artifactStatus(projectDir, jobId, names, afterIso = null) {
+  const files = [];
+  for (const name of names) {
+    const stat = await artifactStat(projectDir, jobId, name);
+    const exists = stat ? await artifactExists(projectDir, jobId, name, afterIso) : false;
+    files.push({ name, exists, modifiedAt: stat ? stat.mtime.toISOString() : null });
+  }
+  return files;
+}
+
+async function allArtifactsExist(projectDir, jobId, names, afterIso = null) {
+  const files = await artifactStatus(projectDir, jobId, names, afterIso);
+  return {
+    ok: files.every((file) => file.exists),
+    files,
+    missing: files.filter((file) => !file.exists).map((file) => file.name)
+  };
+}
+
+async function buildStageRequirements(projectDir, jobId, stage) {
+  if (!stage) {
+    return {
+      stage: null,
+      label: null,
+      files: [],
+      missing: [],
+      nextStageAllowed: true,
+      guidance: ''
+    };
+  }
+  const requirements = await allArtifactsExist(projectDir, jobId, stage.artifacts);
+  return {
+    stage: stage.id,
+    label: stage.label,
+    files: requirements.files,
+    missing: requirements.missing,
+    nextStageAllowed: requirements.ok,
+    guidance: requirements.ok
+      ? '다음 단계를 실행할 수 있습니다.'
+      : `필수 산출물이 아직 생성되지 않았습니다: ${requirements.missing.join(', ')}`
+  };
+}
+
+async function publicIdlePipelineState(projectDir = null, jobId = null) {
   const now = new Date().toISOString();
+  const artifacts = projectDir && jobId ? await listArtifacts(projectDir, jobId) : [];
+  const requirements = projectDir && jobId
+    ? await buildStageRequirements(projectDir, jobId, PIPELINE_STAGES[0])
+    : await buildStageRequirements(null, null, null);
   return {
     ok: true,
     jobKey: projectDir && jobId ? pipelineKey(projectDir, jobId) : null,
@@ -255,15 +351,22 @@ function publicIdlePipelineState(projectDir = null, jobId = null) {
       targetWindow: null,
       waitingApproval: false,
       detectedIssue: null,
-      artifacts: [],
+      artifacts,
       gitDiff: '-',
       reviewStatus: '-',
-      nextAction: '작업 요청을 입력한 뒤 Claude → Codex → Claude 전체 실행을 누르세요.'
+      nextAction: '작업 요청을 입력한 뒤 Claude → Codex → Claude 전체 실행을 누르세요.',
+      requirements
+    },
+    artifacts,
+    summary: {
+      createdArtifacts: artifacts.map((artifact) => artifact.name),
+      gitDiff: { hasChanges: false, saved: false, path: null, changedFiles: [] },
+      review: { status: 'not_started', file: null, decision: null }
     }
   };
 }
 
-function publicPipelineState(state) {
+async function publicPipelineState(state) {
   if (!state) {
     return publicIdlePipelineState();
   }
@@ -277,6 +380,7 @@ function publicPipelineState(state) {
     ? `${review.status}: ${review.file}${review.decision ? ` / ${review.decision}` : ''}`
     : review.status || '-';
   const detectedIssue = state.detectedIssue || null;
+  const requirements = await buildStageRequirements(state.projectDir, state.jobId, nextStageGate(state));
 
   return {
     ok: true,
@@ -297,7 +401,8 @@ function publicPipelineState(state) {
       artifacts: state.artifacts,
       gitDiff: gitDiffText,
       reviewStatus,
-      nextAction: nextRecommendedAction(state, reviewStatus)
+      nextAction: nextRecommendedAction(state, reviewStatus),
+      requirements
     },
     steps: state.steps,
     artifacts: state.artifacts,
@@ -315,6 +420,18 @@ function pipelineMessage(status) {
   if (status === 'claude_reviewing') {
     return 'Claude가 현재 diff와 패치 요약을 리뷰하는 단계입니다.';
   }
+  if (status === 'codex_fixing_review') {
+    return 'Codex가 Claude 리뷰의 수정 요청만 반영하는 단계입니다.';
+  }
+  if (status === 'claude_re_reviewing') {
+    return 'Claude가 수정 반영 후 diff를 다시 리뷰하는 단계입니다.';
+  }
+  if (status === 'review_approved' || status === 'manual_final_approval_required') {
+    return 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.';
+  }
+  if (status === 'review_changes_requested') {
+    return 'Claude가 수정 요청을 남겼습니다. Codex가 리뷰 내용을 반영해야 합니다.';
+  }
   if (status === 'succeeded') {
     return '파이프라인이 완료되었습니다.';
   }
@@ -334,11 +451,14 @@ function pipelineMessage(status) {
 }
 
 function nextRecommendedAction(state, reviewStatus) {
-  if (state.status === 'succeeded') {
+  if (state.status === 'review_approved' || state.status === 'manual_final_approval_required' || state.status === 'succeeded') {
     return reviewStatus && reviewStatus !== '-'
       ? 'Claude 리뷰 결과를 확인한 뒤 사람이 직접 commit, push, PR 생성 여부를 결정하세요.'
       : '산출물과 git diff를 확인한 뒤 사람이 직접 다음 작업을 결정하세요.';
   }
+  if (state.status === 'review_changes_requested') {
+    return 'Codex 리뷰 반영 실행을 눌러 Claude가 요청한 수정만 반영하세요.';
+  }
   if (state.status === 'manual_review_required' || state.status === 'approval_required') {
     return 'tmux 출력을 확인하고 필요한 경우 승인 / 계속 진행, 세션 승인, 거절, 중단 중 하나를 선택하세요.';
   }
@@ -438,24 +558,25 @@ async function refreshPipelineArtifacts(state) {
 
 async function findFirstExistingArtifact(projectDir, jobId, names) {
   for (const name of names) {
-    const filePath = path.join(projectDir, 'docs', 'ai', 'jobs', jobId, name);
-    const stat = await fs.stat(filePath).catch(() => null);
-    if (stat && stat.isFile() && stat.size > 0) {
-      return { name, path: filePath };
+    if (await artifactExists(projectDir, jobId, name)) {
+      return { name, path: artifactPath(projectDir, jobId, name) };
     }
   }
   return null;
 }
 
-async function waitForArtifact(projectDir, jobId, names, state = null, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
+async function waitForArtifacts(projectDir, jobId, names, state = null, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
   const started = Date.now();
+  const afterIso = state && state.currentStep
+    ? state.steps.find((step) => step.id === state.currentStep)?.startedAt || null
+    : null;
   while (Date.now() - started < timeoutMs) {
     if (state && !ACTIVE_PIPELINE_STATES.has(state.status)) {
       return null;
     }
-    const artifact = await findFirstExistingArtifact(projectDir, jobId, names);
-    if (artifact) {
-      return artifact;
+    const requirements = await allArtifactsExist(projectDir, jobId, names, afterIso);
+    if (requirements.ok) {
+      return requirements.files;
     }
     await new Promise((resolve) => setTimeout(resolve, PIPELINE_POLL_MS));
   }
@@ -492,6 +613,10 @@ function markTimedOutRunningStep(state) {
 }
 
 function summarizeIssue(output, type) {
+  if (type === 'approval_required') {
+    const block = extractApprovalBlock(output);
+    return block ? block.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)[0]?.slice(0, 220) || ISSUE_RECOMMENDATIONS[type] : ISSUE_RECOMMENDATIONS[type];
+  }
   const lines = String(output || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
   const matcher = ISSUE_PATTERNS.find((item) => item.type === type);
   if (matcher) {
@@ -503,9 +628,72 @@ function summarizeIssue(output, type) {
   return lines.slice(-3).join(' ').slice(0, 220) || ISSUE_RECOMMENDATIONS[type] || '최근 tmux 출력에서 확인이 필요한 상태를 감지했습니다.';
 }
 
+function isLikelyCodeOrSearchLine(line) {
+  return /^\s*[+-]/.test(line)
+    || /\bconst\s+|\bfunction\s+|=>|stageWindows|pipelineStates|server\.js|Search\s+/i.test(line)
+    || /['"]approval_required['"]|['"]manual_review_required['"]/i.test(line)
+    || /^\s*(web\/|app\/|docs\/|projects\/).+:\d+[:\s]/.test(line)
+    || /^\s*```/.test(line);
+}
+
+function stripCodeLikeApprovalLines(output) {
+  const lines = String(output || '').split(/\r?\n/);
+  let inCodeBlock = false;
+  const kept = [];
+  for (const line of lines) {
+    if (/^\s*```/.test(line)) {
+      inCodeBlock = !inCodeBlock;
+      continue;
+    }
+    if (inCodeBlock || isLikelyCodeOrSearchLine(line)) {
+      continue;
+    }
+    kept.push(line);
+  }
+  return kept.join('\n');
+}
+
+function hasApprovalOptions(block) {
+  return /(?:^|\n)\s*(?:1[.)]|2[.)]|3[.)]).*(?:allow|approve|session|reject|승인|세션|거절|continue)/i.test(block);
+}
+
+function hasCommandOrEditSummary(block) {
+  return /(?:command|execute|run|edit|file|patch|modify|명령|실행|수정|편집|파일)\s*[:：]/i.test(block)
+    || /\b(npm|node|python3?|git|mkdir|cat|chmod|cp|mv|rm|sudo|curl|gh)\b/i.test(block)
+    || /[\w./-]+\.(?:js|css|html|md|json|py|ts|tsx|jsx|yml|yaml|sh)/i.test(block);
+}
+
+function findStrictApprovalPromptBlock(output) {
+  const cleaned = stripCodeLikeApprovalLines(output);
+  const lines = cleaned.split(/\r?\n/);
+  const strongPattern = /allow execution|allow edit|do you want to proceed|would you like to continue|allow for this session|no, suggest changes|enter your response/i;
+  for (let i = lines.length - 1; i >= 0; i -= 1) {
+    if (!strongPattern.test(lines[i])) {
+      continue;
+    }
+    const block = lines.slice(Math.max(0, i - 8), Math.min(lines.length, i + 10)).join('\n').trim();
+    if (hasApprovalOptions(block) || hasCommandOrEditSummary(block)) {
+      return block;
+    }
+  }
+  return '';
+}
+
 function detectIssueFromOutput(output, windowName) {
   const text = String(output || '');
   for (const category of ISSUE_PATTERNS) {
+    if (category.type === 'approval_required') {
+      const block = findStrictApprovalPromptBlock(text);
+      if (block) {
+        return {
+          type: category.type,
+          window: windowName,
+          summary: summarizeIssue(block, category.type),
+          recommendation: ISSUE_RECOMMENDATIONS[category.type]
+        };
+      }
+      continue;
+    }
     if (category.patterns.some((pattern) => pattern.test(text))) {
       return {
         type: category.type,
@@ -527,6 +715,94 @@ async function captureRecentTmuxOutput(windowName, lines = 120) {
   return result.ok ? redactedOutput(result.stdout) : '';
 }
 
+function approvalTypeFromBlock(block) {
+  if (/edit|patch|modify|write|수정|편집|파일/i.test(block)) {
+    return 'file_edit';
+  }
+  if (/command|execute|run|명령|실행/i.test(block)) {
+    return 'command_execution';
+  }
+  return 'unknown';
+}
+
+function extractCommandOrTarget(block) {
+  const lines = String(block || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
+  const commandLine = lines.find((line) => /^\$|^>|^`[^`]+`$|^(npm|node|python|python3|git|mkdir|cat|chmod|cp|mv|rm|sudo|curl|gh)\b/i.test(line));
+  if (commandLine) {
+    return commandLine.replace(/^[$>]\s*/, '').replace(/^`|`$/g, '').slice(0, 260);
+  }
+  const fileLine = lines.find((line) => /(?:^|\s)([\w./-]+\.(?:js|css|html|md|json|py|ts|tsx|jsx|yml|yaml|sh))(?:\s|$)/i.test(line));
+  return fileLine ? fileLine.slice(0, 260) : '';
+}
+
+function classifyApprovalRisk(block, commandOrTarget) {
+  const text = `${block || ''}\n${commandOrTarget || ''}`;
+  if (/rm\s+-rf|sudo\b|curl\b.*\|\s*(bash|sh)|git\s+push|gh\s+pr\s+merge|deploy|deployment|kubectl|terraform|\.env|secret|token|api\s*key|auth\/|payment\/|billing\/|migrations?\/|production|prod\b/i.test(text)) {
+    return {
+      risk: 'high',
+      recommendation: '거절 권장',
+      canApproveOnce: false,
+      canApproveSession: false,
+      warning: '승인하지 마세요. 거절 또는 중단하세요.'
+    };
+  }
+  if (/npm\s+install|chmod\b|\bcp\b|\bmv\b/i.test(text) || /(?:^|\s)(?!docs\/ai\/jobs\/)[\w./-]+\.(?:js|css|html|py|ts|tsx|jsx|json|yml|yaml|sh)/i.test(text)) {
+    return {
+      risk: 'medium',
+      recommendation: '직접 확인 필요',
+      canApproveOnce: true,
+      canApproveSession: false,
+      warning: '명령과 수정 대상을 tmux 출력에서 확인한 뒤 1회 승인만 고려하세요.'
+    };
+  }
+  if (/mkdir\s+-p\s+docs\/ai\/jobs\/|docs\/ai\/jobs\/[\w._-]+|git\s+(status|diff)\b|node\s+--check\b|python3?\s+-m\s+(py_compile|compileall)\b|cat\s+docs\/ai\/jobs\//i.test(text)) {
+    return {
+      risk: 'low',
+      recommendation: '1회 승인 가능',
+      canApproveOnce: true,
+      canApproveSession: true,
+      warning: '세션 승인은 같은 종류의 안전한 명령이 반복될 때만 사용하세요.'
+    };
+  }
+  return {
+    risk: 'unknown',
+    recommendation: '직접 확인 필요',
+    canApproveOnce: false,
+    canApproveSession: false,
+    warning: '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.'
+  };
+}
+
+function extractApprovalBlock(output) {
+  return findStrictApprovalPromptBlock(output);
+}
+
+function cleanWorkingDirectory(block) {
+  const match = String(block || '').match(/(?:cwd|working directory|작업 디렉터리)\s*[:=]\s*([^\n]+)/i);
+  return match ? match[1].trim().slice(0, 260) : '-';
+}
+
+async function buildApprovalContext(windowName, step = null) {
+  const safeWindow = validateAiTmuxWindow(windowName);
+  const output = await captureRecentTmuxOutput(safeWindow, 180);
+  const rawBlock = extractApprovalBlock(output);
+  if (!rawBlock) {
+    return null;
+  }
+  const commandOrTarget = extractCommandOrTarget(rawBlock);
+  const risk = classifyApprovalRisk(rawBlock, commandOrTarget);
+  return {
+    window: safeWindow,
+    step,
+    type: approvalTypeFromBlock(rawBlock),
+    commandOrTarget: commandOrTarget || '확인 불가',
+    workingDirectory: cleanWorkingDirectory(rawBlock),
+    rawBlock,
+    ...risk,
+    summary: `${safeWindow === 'codex' ? 'Codex' : 'Claude'} 창에서 명령 실행 승인 요청이 감지되었습니다.`
+  };
+}
+
 async function refreshDetectedIssue(state) {
   if (!state || !ACTIVE_PIPELINE_STATES.has(state.status)) {
     return;
@@ -540,6 +816,13 @@ async function refreshDetectedIssue(state) {
   if (!issue) {
     return;
   }
+  if (issue.type === 'approval_required') {
+    issue.approvalContext = await buildApprovalContext(targetWindow, state.currentStep).catch(() => null);
+    if (!issue.approvalContext) {
+      return;
+    }
+    issue.summary = issue.approvalContext.summary;
+  }
 
   state.detectedIssue = issue;
   state.error = issue.recommendation;
@@ -565,25 +848,24 @@ async function applyArtifactProgress(state) {
     return;
   }
 
-  for (const stage of PIPELINE_STAGES) {
-    const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, stage.artifacts);
-    const step = state.steps.find((item) => item.id === stage.id);
-    if (artifact && step && step.status === 'running') {
-      state.status = stage.state;
-      state.error = null;
-      state.detectedIssue = null;
-      setStep(state, stage.id, stage.label, 'succeeded', artifact.name);
-    }
-  }
-
   const current = stageById(state.currentStep);
   if (current) {
-    const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, current.artifacts);
-    if (artifact) {
+    const step = state.steps.find((item) => item.id === current.id);
+    const requirements = await allArtifactsExist(state.projectDir, state.jobId, current.artifacts, step?.startedAt || null);
+    if (requirements.ok) {
       state.status = current.state;
       state.error = null;
       state.detectedIssue = null;
-      setStep(state, current.id, current.label, 'succeeded', artifact.name);
+      setStep(state, current.id, current.label, 'succeeded', requirements.files.map((file) => file.name).join(', '));
+      if (current.id === 'codex-review-fix') {
+        state.status = 'review_changes_requested';
+        state.currentStep = null;
+        state.error = 'Codex가 리뷰 반영을 완료했습니다. Claude 재리뷰를 실행하세요.';
+      }
+      if (current.id === 'claude-review' || current.id === 'claude-re-review') {
+        await updateReviewSummary(state.projectDir, state.jobId, state);
+        applyReviewDecision(state);
+      }
     }
   }
 }
@@ -646,14 +928,60 @@ async function updateReviewSummary(projectDir, jobId, state) {
     return;
   }
   const content = await fs.readFile(artifact.path, 'utf8').catch(() => '');
-  const decisionLine = content.split(/\r?\n/).find((line) => /decision|verdict|approve|request changes|comment/i.test(line));
+  const decision = detectReviewDecision(content);
+  const decisionLine = content.split(/\r?\n/).find((line) => /decision|verdict|approve|request[_ -]?changes|block|승인|수정\s*요청|차단|보류/i.test(line));
   state.summary.review = {
     status: 'available',
     file: artifact.name,
-    decision: decisionLine ? decisionLine.trim() : null
+    decision,
+    decisionLine: decisionLine ? decisionLine.trim() : null
   };
 }
 
+function detectReviewDecision(content) {
+  const text = String(content || '');
+  if (/\bBLOCK\b|차단|보류/i.test(text)) {
+    return 'BLOCK';
+  }
+  if (/\bREQUEST[_ -]?CHANGES\b|수정\s*요청/i.test(text)) {
+    return 'REQUEST_CHANGES';
+  }
+  if (/\bAPPROVE\b|\bAPPROVED\b|승인/i.test(text)) {
+    return 'APPROVE';
+  }
+  return 'UNKNOWN';
+}
+
+function applyReviewDecision(state) {
+  const decision = state.summary.review.decision;
+  const now = new Date().toISOString();
+  if (decision === 'APPROVE') {
+    state.status = 'manual_final_approval_required';
+    state.currentStep = null;
+    state.finishedAt = now;
+    state.error = 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.';
+    return;
+  }
+  if (decision === 'REQUEST_CHANGES') {
+    state.status = 'review_changes_requested';
+    state.currentStep = null;
+    state.finishedAt = now;
+    state.error = 'Claude가 수정 요청을 남겼습니다. Codex가 리뷰 내용을 반영해야 합니다.';
+    return;
+  }
+  if (decision === 'BLOCK') {
+    state.status = 'blocked';
+    state.currentStep = null;
+    state.finishedAt = now;
+    state.error = 'Claude가 작업을 차단했습니다. 요청 범위나 안전 조건을 수정해야 합니다.';
+    return;
+  }
+  state.status = 'manual_review_required';
+  state.currentStep = null;
+  state.finishedAt = now;
+  state.error = 'Claude 리뷰 결정을 확인할 수 없습니다. review.md에서 APPROVE, REQUEST_CHANGES, BLOCK 중 하나를 확인하세요.';
+}
+
 async function runPipeline(state, inputKo) {
   const { projectDir, jobId } = state;
   const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
@@ -679,11 +1007,11 @@ async function runPipeline(state, inputKo) {
       if (!sent.ok) {
         throw new Error(`${step.label} 실패: ${sent.message || sent.stderr || 'tmux 전송 실패'}`);
       }
-      const artifact = await waitForArtifact(projectDir, jobId, step.artifacts, state);
+      const artifacts = await waitForArtifacts(projectDir, jobId, step.artifacts, state);
       if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
         return;
       }
-      if (!artifact) {
+      if (!artifacts) {
         markManualRequired(state, step.id, step.label);
         await refreshPipelineArtifacts(state);
         return;
@@ -691,7 +1019,7 @@ async function runPipeline(state, inputKo) {
       state.status = step.state;
       state.error = null;
       state.detectedIssue = null;
-      setStep(state, step.id, step.label, 'succeeded', artifact.name);
+      setStep(state, step.id, step.label, 'succeeded', artifacts.map((artifact) => artifact.name).join(', '));
       await refreshPipelineArtifacts(state);
 
       if (step.id === 'codex-implement') {
@@ -723,11 +1051,11 @@ async function runPipeline(state, inputKo) {
     if (!reviewed.ok) {
       throw new Error(`Claude 리뷰 전송 실패: ${reviewed.message || reviewed.stderr || 'tmux 전송 실패'}`);
     }
-    const reviewArtifact = await waitForArtifact(projectDir, jobId, reviewerStep.artifacts, state);
+    const reviewArtifacts = await waitForArtifacts(projectDir, jobId, reviewerStep.artifacts, state);
     if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
       return;
     }
-    if (!reviewArtifact) {
+    if (!reviewArtifacts) {
       markManualRequired(state, reviewerStep.id, reviewerStep.label);
       await updateReviewSummary(projectDir, jobId, state);
       await refreshPipelineArtifacts(state);
@@ -736,13 +1064,10 @@ async function runPipeline(state, inputKo) {
     state.status = reviewerStep.state;
     state.error = null;
     state.detectedIssue = null;
-    setStep(state, reviewerStep.id, reviewerStep.label, 'succeeded', reviewArtifact.name);
+    setStep(state, reviewerStep.id, reviewerStep.label, 'succeeded', reviewArtifacts.map((artifact) => artifact.name).join(', '));
     await updateReviewSummary(projectDir, jobId, state);
     await refreshPipelineArtifacts(state);
-
-    state.status = 'succeeded';
-    state.currentStep = null;
-    state.finishedAt = new Date().toISOString();
+    applyReviewDecision(state);
   } catch (error) {
     state.status = 'failed';
     state.error = error.message || '파이프라인 실행 실패';
@@ -797,6 +1122,31 @@ function buildPrompt(role, projectDir, jobId, inputKo) {
       '',
       `Review the git diff saved at ${path.join(jobDir, 'local-diff.patch')} when present, ${path.join(jobDir, 'patch.md')}, and the approved request/plan.`,
       `Write the review into ${path.join(jobDir, 'review.md')} using the Claude review output format.`,
+      'The review must include exactly one decision marker: APPROVE, REQUEST_CHANGES, or BLOCK.',
+      'Do not commit, push, merge, deploy, or run arbitrary shell commands.'
+    ].join('\n');
+  }
+
+  if (role === 'codex-review-fix') {
+    return [
+      'Use prompts/codex-implementer.md.',
+      common,
+      '',
+      `Read ${path.join(jobDir, 'patch.md')}, ${path.join(jobDir, 'review.md')}, and the current git diff.`,
+      'Apply only the changes explicitly requested by Claude review. Do not expand scope.',
+      `Update ${path.join(jobDir, 'patch.md')} and write ${path.join(jobDir, 'status.md')} with what changed and which checks ran.`,
+      'Do not commit, push, merge, deploy, or change secrets, .env, auth, payment, production infra, or database migrations.'
+    ].join('\n');
+  }
+
+  if (role === 'claude-re-review') {
+    return [
+      'Use prompts/claude.md.',
+      common,
+      '',
+      `Re-review the updated git diff, ${path.join(jobDir, 'patch.md')}, ${path.join(jobDir, 'status.md')}, and the previous review in ${path.join(jobDir, 'review.md')}.`,
+      `Update ${path.join(jobDir, 'review.md')} with the new review result.`,
+      'The review must include exactly one decision marker: APPROVE, REQUEST_CHANGES, or BLOCK.',
       'Do not commit, push, merge, deploy, or run arbitrary shell commands.'
     ].join('\n');
   }
@@ -883,6 +1233,51 @@ function handleError(res, error) {
   res.status(400).json({ ok: false, error: error.message || '요청을 처리할 수 없습니다.' });
 }
 
+function getOrCreatePipelineState(projectDir, jobId) {
+  const key = pipelineKey(projectDir, jobId);
+  let state = pipelineStates.get(key);
+  if (!state) {
+    state = createPipelineState(projectDir, jobId);
+    state.status = 'idle';
+    state.currentStep = null;
+    pipelineStates.set(key, state);
+  }
+  return state;
+}
+
+async function requireArtifacts(projectDir, jobId, names, message) {
+  const requirements = await allArtifactsExist(projectDir, jobId, names);
+  if (!requirements.ok) {
+    throw new Error(`${message} 누락: ${requirements.missing.join(', ')}`);
+  }
+}
+
+async function sendManualStage(projectDir, jobId, inputKo, stageId) {
+  const stage = stageById(stageId);
+  if (!stage) {
+    throw new Error('허용되지 않은 단계입니다.');
+  }
+  const state = getOrCreatePipelineState(projectDir, jobId);
+  if (ACTIVE_PIPELINE_STATES.has(state.status)) {
+    throw new Error('이미 실행 중인 단계가 있습니다.');
+  }
+  state.status = stage.state;
+  state.error = null;
+  state.detectedIssue = null;
+  state.finishedAt = null;
+  setStep(state, stage.id, stage.label, 'running');
+  const result = await sendToWindow(stage.role, projectDir, jobId, inputKo);
+  await appendPipelineLog(projectDir, jobId, stage.id, `${result.stdout || ''}${result.stderr || ''}${result.message || ''}`);
+  if (!result.ok) {
+    state.status = 'failed';
+    state.error = result.message || result.stderr || 'tmux 전송 실패';
+    state.finishedAt = new Date().toISOString();
+    setStep(state, stage.id, stage.label, 'failed', state.error);
+  }
+  await refreshPipelineArtifacts(state);
+  return { state, result };
+}
+
 app.get('/api/status', async (req, res) => {
   const result = await runFile(path.join(SCRIPTS_DIR, 'status-ai-team.sh'), []);
   res.json(cleanOutput(result));
@@ -1004,11 +1399,11 @@ app.get('/api/pipeline/status', async (req, res) => {
       if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
         await updateReviewSummary(projectDir, jobId, state);
       }
-      res.json(publicPipelineState(state));
+      res.json(await publicPipelineState(state));
       return;
     }
 
-    res.json(publicIdlePipelineState(projectDir, jobId));
+    res.json(await publicIdlePipelineState(projectDir, jobId));
   } catch (error) {
     handleError(res, error);
   }
@@ -1049,6 +1444,20 @@ app.get('/api/tmux/output', async (req, res) => {
   }
 });
 
+app.get('/api/tmux/approval-context', async (req, res) => {
+  try {
+    const windowName = validateAiTmuxWindow(req.query.window);
+    const context = await buildApprovalContext(windowName, typeof req.query.step === 'string' ? req.query.step : null);
+    if (!context) {
+      res.status(404).json({ ok: false, error: '실제 승인 프롬프트를 찾지 못했습니다.' });
+      return;
+    }
+    res.json({ ok: true, approvalContext: context });
+  } catch (error) {
+    handleError(res, error);
+  }
+});
+
 for (const [endpoint, keys] of [
   ['/api/tmux/approve-once', ['1', 'Enter']],
   ['/api/tmux/approve-session', ['2', 'Enter']],
@@ -1124,15 +1533,35 @@ app.post('/api/service/restart-gui', async (req, res) => {
 for (const [endpoint, role] of [
   ['/api/send/claude-plan', 'claude-plan'],
   ['/api/send/codex-implement', 'codex-implement'],
-  ['/api/send/claude-review', 'claude-review']
+  ['/api/send/claude-review', 'claude-review'],
+  ['/api/send/codex-review-fix', 'codex-review-fix'],
+  ['/api/send/claude-re-review', 'claude-re-review']
 ]) {
   app.post(endpoint, async (req, res) => {
     try {
       const projectDir = await resolveProjectDir(req.body.projectDir);
       const jobId = validateJobId(req.body.jobId);
       const inputKo = typeof req.body.inputKo === 'string' ? req.body.inputKo : '';
-      const result = await sendToWindow(role, projectDir, jobId, inputKo);
-      res.json(cleanOutput(result));
+      if (role === 'codex-implement') {
+        await requireArtifacts(projectDir, jobId, ['plan.md', 'codex-task.md'], 'Claude 계획이 아직 완료되지 않았습니다. plan.md와 codex-task.md가 생성된 뒤 Codex를 실행할 수 있습니다.');
+      }
+      if (role === 'claude-review') {
+        await requireArtifacts(projectDir, jobId, ['patch.md'], 'patch.md가 생성된 뒤 Claude 리뷰를 실행할 수 있습니다.');
+      }
+      if (role === 'codex-review-fix') {
+        await requireArtifacts(projectDir, jobId, ['patch.md', 'review.md'], 'patch.md와 review.md가 생성된 뒤 Codex 리뷰 반영을 실행할 수 있습니다.');
+      }
+      if (role === 'claude-re-review') {
+        await requireArtifacts(projectDir, jobId, ['patch.md', 'review.md', 'status.md'], 'Codex 리뷰 반영 상태가 생성된 뒤 Claude 재리뷰를 실행할 수 있습니다.');
+      }
+      const stage = stageById(role);
+      const { state, result } = stage
+        ? await sendManualStage(projectDir, jobId, inputKo, role)
+        : { state: null, result: await sendToWindow(role, projectDir, jobId, inputKo) };
+      res.json({
+        ...cleanOutput(result),
+        pipeline: state ? (await publicPipelineState(state)).status : null
+      });
     } catch (error) {
       handleError(res, error);
     }

```

## 2026-05-14T11:58:49.693Z — save-diff

```
diff --git a/.gitignore b/.gitignore
index 2958a59..7f7fa98 100644
--- a/.gitignore
+++ b/.gitignore
@@ -3,3 +3,6 @@ projects/paper-trading/.env
 .env
 .env.*
 !.env.example
+
+# Imported local reference code - never commit directly
+imports/
diff --git a/docs/ai/jobs/mvp-004/request.ko.md b/docs/ai/jobs/mvp-004/request.ko.md
index 7d9ecf1..dcfaa5c 100644
--- a/docs/ai/jobs/mvp-004/request.ko.md
+++ b/docs/ai/jobs/mvp-004/request.ko.md
@@ -1,10 +1,74 @@
-# 작업 요청
+# 작업 ID
+mvp-004
 
-GUI 파이프라인이 Claude 계획 완료 전에 Codex 단계로 넘어가는 문제를 수정한다.
+# 작업명
+AI 개발팀 GUI 화면 배치 개선
 
-Claude 계획 단계는 plan.md와 codex-task.md가 생성되어야 완료된 것으로 본다.
-Codex 구현 단계는 patch.md가 생성되어야 완료된 것으로 본다.
-Claude 리뷰 단계는 review.md가 생성되어야 완료된 것으로 본다.
+현재 AI 개발팀 브라우저 GUI에서 화면 배치가 불편하다.
 
-전체 파이프라인 버튼은 각 단계의 산출물 파일을 확인한 뒤 다음 단계로 넘어가야 한다.
-승인 대기, 차단, 실패 상태가 감지되면 다음 단계로 넘어가면 안 된다.
+문제점:
+1. 파이프라인 상태 영역이 너무 위에 있어서 핵심 제어 버튼과 시선 흐름이 맞지 않는다.
+2. 승인 / 서비스 제어 / 실시간 출력 영역이 아래쪽에 있어 잘 안 보인다.
+3. 작업 설정 칸이 너무 길어서 화면을 많이 차지한다.
+4. 실제 작업 중에는 승인 버튼, 서비스 제어, 실시간 출력이 더 중요하므로 위쪽에서 바로 보여야 한다.
+
+원하는 변경사항:
+
+1. “파이프라인 상태” 영역을 “Claude → Codex → Claude 전체 실행” 버튼 아래로 내려줘.
+
+2. 아래 영역들을 상단 쪽으로 올려줘.
+   - 승인 / 계속 진행
+   - 거절
+   - 중단
+   - 서비스 제어
+   - 실시간 출력
+
+3. 작업 설정 영역을 더 짧고 컴팩트하게 만들어줘.
+   - 입력칸 높이를 줄여줘.
+   - 필요하면 접기/펼치기 형태로 만들어줘.
+   - 화면에서 너무 많은 공간을 차지하지 않게 해줘.
+
+4. 화면 우선순위를 아래 순서로 재배치해줘.
+   - 상단: 작업 ID / 작업 요청 입력 / 주요 실행 버튼
+   - 그 아래: 승인 / 서비스 제어 / 실시간 출력
+   - 그 아래: 파이프라인 상태
+   - 그 아래: 작업 설정 / 고급 설정 / 산출물 목록
+
+5. Claude + Codex 2-role 구조는 유지해줘.
+   - Gemini Manager, Claude Architect, Claude Reviewer, Git Shell을 다시 노출하지 마.
+   - Claude 계획 생성
+   - Codex 구현 실행
+   - Claude 리뷰 실행
+   - Claude → Codex → Claude 전체 실행
+   이 버튼 구조는 유지해줘.
+
+6. git status와 git diff는 수동 유틸리티 버튼으로만 유지해줘.
+   - commit, push, merge는 자동화하지 마.
+
+7. 반응형 화면도 깨지지 않게 해줘.
+   - 작은 화면에서도 실시간 출력과 승인 버튼이 잘 보여야 한다.
+
+수정 대상:
+- web/public/index.html
+- web/public/app.js
+- web/public/style.css
+- 필요하면 web/server.js
+- README.md 또는 docs/ai/CLAUDE_CODEX_WORKFLOW.md는 변경 내용이 있으면 최소한만 업데이트
+
+금지:
+- 주식 페이퍼매매 로직은 건드리지 마.
+- secrets, .env, auth, payment, production infra, database migrations는 건드리지 마.
+- 임의 shell 명령 입력 기능은 만들지 마.
+- git commit, push, merge는 자동화하지 마.
+
+검증:
+- node --check web/server.js
+- node --check web/public/app.js
+- git diff --stat
+
+완료 후:
+- 어떤 UI 영역을 어디로 옮겼는지
+- 작업 설정 영역을 어떻게 줄였는지
+- Claude + Codex 구조가 유지되는지
+- 테스트 결과가 무엇인지
+patch.md에 정리해줘.
\ No newline at end of file
diff --git a/docs/ai/jobs/mvp-007/local-diff.patch b/docs/ai/jobs/mvp-007/local-diff.patch
index 559f050..ebc5221 100644
--- a/docs/ai/jobs/mvp-007/local-diff.patch
+++ b/docs/ai/jobs/mvp-007/local-diff.patch
@@ -85,6 +85,393 @@ index 7d9ecf1..dcfaa5c 100644
 +- 테스트 결과가 무엇인지
 +patch.md에 정리해줘.
 \ No newline at end of file
+diff --git a/docs/ai/jobs/mvp-007/pipeline.log.md b/docs/ai/jobs/mvp-007/pipeline.log.md
+index 75df48b..5af59ba 100644
+--- a/docs/ai/jobs/mvp-007/pipeline.log.md
++++ b/docs/ai/jobs/mvp-007/pipeline.log.md
+@@ -1477,3 +1477,27 @@ index 0ce1e5d..7d07b26 100644
+ ```
+ (no output)
+ ```
++
++## 2026-05-14T10:53:00.580Z — create-job
++
++```
++Ensured job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-007
++```
++
++## 2026-05-14T10:53:00.588Z — save-input
++
++```
++Saved: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-007/request.ko.md
++```
++
++## 2026-05-14T10:53:00.600Z — claude-plan
++
++```
++(no output)
++```
++
++## 2026-05-14T10:53:00.611Z — codex-implement
++
++```
++(no output)
++```
+diff --git a/docs/ai/jobs/mvp-007/request.ko.md b/docs/ai/jobs/mvp-007/request.ko.md
+index dfd0315..9fc2cdb 100644
+--- a/docs/ai/jobs/mvp-007/request.ko.md
++++ b/docs/ai/jobs/mvp-007/request.ko.md
+@@ -1,227 +1,170 @@
+ # 작업 ID
+-mvp-007
++mvp-008
+ 
+ # 작업명
+-KIS Open API 모의투자 인증 / 계좌 / 시세 연결
++KIS 모의투자 주문 흐름 연결 준비
+ 
+-미국주식 자동 페이퍼매매 시스템에 KIS Open API 모의투자 연결을 진행해줘.
++미국주식 자동 페이퍼매매 시스템에서 KIS 모의투자 주문 흐름을 연결할 준비를 해줘.
+ 
+-현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 연결 검증이다.
++현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 주문 흐름 검증이다.
+ live trading은 절대 활성화하지 않는다.
+ 
+-## 현재 전제
++## 현재 상태
+ 
+-mvp-006에서 KIS 설정 구조와 Broker Adapter 골격을 준비했다.
++mvp-006-1과 mvp-007에서 아래 작업이 완료되었다.
+ 
+-이번 mvp-007에서는 가능한 범위 안에서 아래 기능을 연결한다.
++- paper-trading 프로젝트 기본 구조 생성
++- KIS 설정 구조 준비
++- `.env` 기반 KIS 설정 로딩
++- KIS Broker Adapter 골격
++- KIS Auth / Account / MarketData Client 골격
++- `/paper/status`에 KIS 상태 표시
++- secret/account masking 테스트
++- 74개 테스트 통과
+ 
+-1. KIS 모의투자 인증 토큰 발급 연결
+-2. 토큰 refresh / 만료 처리 구조
+-3. KIS 모의투자 계좌 정보 조회
+-4. KIS 해외주식 또는 미국주식 시세 조회 구조
+-5. Broker healthcheck 강화
+-6. `/paper/status` 또는 기존 status endpoint에 KIS 연결 상태 표시
+-7. 실제 주문은 아직 연결하지 않음
++이번 mvp-008에서는 실제 실계좌 주문이 아니라,
++KIS 모의투자 주문 흐름을 안전하게 연결할 준비를 한다.
+ 
+-## 보안 조건
++## 핵심 목표
+ 
+-KIS 모의투자 계좌번호, app key, app secret은 `.env`에 저장되어 있다고 가정한다.
++Strategy → RiskEngine → OMS → BrokerAdapter → KIS Broker 경로가 유지되도록 하면서,
++KIS 모의투자 주문 메서드의 안전한 경계를 만든다.
+ 
+-중요:
+-- 실제 계좌번호, app key, app secret 값을 코드에 쓰지 마.
+-- patch.md, review.md, 로그, 테스트 출력에 실제 secret을 노출하지 마.
+-- `.env.example`에는 placeholder만 유지해.
+-- `.env`는 Git에 추가하지 마.
+-- 설정 객체 repr/logging에서 app secret이 노출되지 않게 해.
+-- 테스트에서도 실제 secret 값을 출력하지 마.
+-
+-## 공식 문서 조건
+-
+-KIS Open API endpoint, TR ID, payload는 공식 문서 기준으로만 구현해야 한다.
+-
+-중요:
+-- 공식 문서나 프로젝트 내 명확한 문서가 없으면 endpoint를 추측해서 만들지 마.
+-- 확실하지 않은 endpoint, TR ID, header, payload는 TODO로 남겨.
+-- fake endpoint를 만들지 마.
+-- 실제 주문 endpoint는 이번 작업에서 구현하지 마.
+-- 인증 / 계좌조회 / 시세조회도 확실한 공식 정보가 없으면 fail-closed + TODO로 남겨.
+-
+-## 이번 구현 범위
+-
+-가능하면 아래 기능을 구현해줘.
+-
+-### 1. KIS Auth Client
++단, 공식 문서가 확인되지 않은 endpoint, TR ID, payload는 절대 추측해서 구현하지 않는다.
+ 
+-- `.env`에서 아래 값을 읽는다.
+-  - KIS_ENV
+-  - KIS_ACCOUNT_NO
+-  - KIS_APP_KEY
+-  - KIS_APP_SECRET
+-- 모의투자 환경인지 확인한다.
+-- 인증 토큰 발급 메서드를 만든다.
+-- 토큰 만료 시 refresh 또는 재발급 가능 구조를 만든다.
+-- 인증 실패 시 fail-closed 한다.
+-- secret이 로그에 찍히지 않게 한다.
++## 구현할 내용
+ 
+-필요 메서드 예시:
+-- authenticate()
+-- refresh_token()
+-- get_access_token()
+-- is_authenticated()
+-- clear_token()
++### 1. KIS 주문 메서드 경계 정리
+ 
+-### 2. KIS Account Client
++`KisBroker` 또는 현재 구조에 맞는 KIS adapter에 아래 주문 관련 메서드를 정리해줘.
+ 
+-- 계좌 정보 조회 골격 또는 실제 연결을 구현한다.
+-- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
+-- 계좌번호는 출력 시 마스킹한다.
+-- 실패 시 주문 가능 상태로 전환하지 않는다.
+-
+-필요 메서드 예시:
+-- get_account()
+-- get_positions()
+-- get_cash_balance()
+-
+-### 3. KIS Market Data Client
+-
+-- 미국주식 시세 조회 구조를 만든다.
+-- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
+-- 최소 quote 모델을 반환한다.
+-- 실패 시 stale / unavailable 상태로 처리한다.
+-
+-필요 메서드 예시:
+-- get_quote(symbol)
+-- get_last_price(symbol)
+-- healthcheck_market_data()
+-
+-### 4. KIS Broker Adapter 연결
++- place_order()
++- cancel_order()
++- replace_order()
++- get_open_orders()
++- get_fills()
++- get_order_status()
+ 
+-기존 BrokerAdapter 구조를 유지한다.
++조건:
++- 실제 endpoint/TR ID/payload를 추측해서 만들지 마.
++- 공식 문서가 없으면 TODO + fail-closed로 둬.
++- 메서드는 존재하되, 실주문 전송은 아직 하지 마.
++- NotImplementedError 또는 안전한 Rejected 상태를 반환하게 해.
++- 에러 메시지는 secret/account를 노출하지 않아야 한다.
+ 
+-- authenticate()
+-- refresh_token()
+-- get_account()
+-- get_positions()
+-- get_quote()
+-- healthcheck()
++### 2. OMS → KIS Broker 연결 준비
+ 
+-주문 관련 메서드는 아직 실제 전송하지 않는다.
++OMS가 broker adapter를 통해 주문을 보낼 수 있는 구조인지 점검하고,
++필요하면 interface를 정리해줘.
+ 
+-- place_order()
+-- cancel_order()
+-- replace_order()
++중요:
++- Strategy가 KIS를 직접 호출하면 안 된다.
++- Agent/LLM이 KIS를 직접 호출하면 안 된다.
++- OMS를 우회해서 주문하면 안 된다.
++- 모든 주문은 반드시 RiskEngine을 통과해야 한다.
++- OMS만 executable order를 만들 수 있다.
++
++### 3. KIS 모의투자 주문 요청 모델 준비
++
++실제 전송은 하지 말고, 내부 도메인 모델 기준으로 KIS 주문 요청 변환 경계를 만들어줘.
++
++예:
++- symbol
++- side
++- quantity
++- order_type
++- limit_price
++- extended_hours
++- account_no_masked
++- broker_environment
+ 
+-위 주문 메서드는 이번 단계에서 fail-closed 또는 NotImplemented 상태로 둔다.
++조건:
++- 시장가 주문은 금지
++- 지정가 주문만 허용
++- live trading이면 차단
++- KIS_ENV가 paper가 아니면 차단
++- 계좌번호 원문은 출력하지 말고 마스킹만 사용
+ 
+-## 주문 안전 조건
++### 4. 주문 안전 guard 추가
+ 
+-반드시 유지해.
++KIS 주문 흐름에 아래 guard를 적용해줘.
+ 
+-- live trading은 false
+-- TRADING_MODE는 paper
+-- 시장가 주문 금지
+-- 실주문 전송 금지
+-- Strategy가 KIS Adapter를 직접 호출하지 않음
+-- Agent/LLM이 직접 주문하지 않음
+-- 모든 주문은 Strategy → RiskEngine → OMS → BrokerAdapter 경로 유지
+-- OMS 우회 금지
+-- RiskEngine 우회 금지
++- TRADING_MODE=paper만 허용
++- LIVE_TRADING_ENABLED=false 확인
++- ALLOW_MARKET_ORDERS=false 확인
++- KIS_ENV=paper 확인
++- order_type이 market이면 거절
++- quantity가 0 이하이면 거절
++- limit_price가 없으면 거절
++- stale quote면 거절
++- kill switch가 켜져 있으면 거절
+ 
+-## 상태 API
++### 5. `/paper/status` 또는 status에 주문 준비 상태 추가
+ 
+-가능하면 `/paper/status` 또는 기존 `/status`에 아래 정보를 추가해줘.
++가능하면 아래 상태를 추가해줘.
+ 
+-- broker_type
+-- broker_environment
+-- kis_config_loaded
+-- kis_authenticated
+-- kis_account_loaded
+-- kis_market_data_available
+-- live_trading_enabled
+-- allow_market_orders
+-- last_broker_error
++- kis_order_entry_ready
++- kis_order_entry_mode: disabled | paper_guarded | not_implemented
++- kis_order_methods_fail_closed: true
++- live_trading_enabled: false
++- allow_market_orders: false
+ - secret_exposed: false
+ 
+-중요:
+-- app key, app secret, 계좌번호 원문은 절대 출력하지 마.
+-- 계좌번호는 필요하면 마스킹해서 보여줘.
++실제 app key, app secret, 계좌번호 원문은 절대 출력하지 마.
+ 
+-## 테스트 요구사항
++### 6. 테스트 추가
+ 
+ 아래 테스트를 추가해줘.
+ 
+-1. `.env` 기반 KIS config 로딩 테스트
+-2. app secret이 repr/logging/status에 노출되지 않는지 테스트
+-3. KIS_ENV=paper 기본 동작 테스트
+-4. live trading 기본 false 테스트
+-5. 시장가 주문 기본 금지 테스트
+-6. 인증 client가 secret을 직접 출력하지 않는지 테스트
+-7. 공식 문서 정보가 없을 때 endpoint를 추측하지 않고 TODO/fail-closed 되는지 테스트
+-8. 주문 메서드가 아직 실주문을 전송하지 않는지 테스트
+-9. BrokerAdapter 인터페이스가 깨지지 않는지 테스트
+-10. `/paper/status` 또는 `/status`에 KIS 상태가 안전하게 표시되는지 테스트
++1. KIS place_order가 실주문을 보내지 않고 fail-closed 되는지
++2. KIS cancel_order가 실취소를 보내지 않고 fail-closed 되는지
++3. KIS replace_order가 실정정을 보내지 않고 fail-closed 되는지
++4. market order가 거절되는지
++5. limit_price 없는 주문이 거절되는지
++6. live trading true이면 거절되는지
++7. KIS_ENV가 paper가 아니면 거절되는지
++8. Strategy가 KIS adapter를 직접 호출하지 않는지
++9. OMS 경로를 우회하지 않는지
++10. status에 secret/account 원문이 노출되지 않는지
++11. 기존 74개 테스트가 계속 통과하는지
+ 
+ ## 수정 가능 파일
+ 
+-필요한 경우 아래 파일을 수정해도 된다.
++필요하면 아래 파일을 수정해도 된다.
+ 
+-- app/adapters/brokers/kis.py
+-- app/adapters/brokers/base.py
+-- app/core/config.py
+-- app/api/routes.py
+-- app/runtime/paper_runner.py
+-- app/monitoring/status.py
+-- app/domain/*
+-- tests/*
+-- .env.example
+-- README.md
+-- docs/architecture.md
+-- docs/runbook.md
++- projects/paper-trading/app/broker/kis.py
++- projects/paper-trading/app/broker/base.py
++- projects/paper-trading/app/oms/*
++- projects/paper-trading/app/risk/*
++- projects/paper-trading/app/api/routes.py
++- projects/paper-trading/app/api/server.py
++- projects/paper-trading/app/config/*
++- projects/paper-trading/app/models/*
++- projects/paper-trading/tests/*
++- projects/paper-trading/README.md
++- docs/ai/jobs/mvp-008/patch.md
+ 
+-실제 프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.
++프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.
+ 
+ ## 금지 사항
+ 
+-- 실제 KIS app key, app secret, 계좌번호를 코드에 쓰지 마.
+-- 실제 값을 patch.md, review.md, 로그에 출력하지 마.
+-- `.env` 파일을 Git에 추가하지 마.
+-- live trading을 true로 바꾸지 마.
+-- 실계좌 주문 기능을 만들지 마.
+-- 주문 endpoint를 연결하지 마.
+-- KIS endpoint / TR ID / payload를 추측해서 만들지 마.
++- 실제 KIS endpoint를 추측해서 만들지 마.
++- TR ID를 추측해서 넣지 마.
++- 실제 주문 전송 코드를 만들지 마.
++- live trading을 활성화하지 마.
+ - 시장가 주문을 허용하지 마.
+-- 브로커 API를 Strategy에서 직접 호출하게 만들지 마.
++- app key, app secret, 계좌번호 원문을 코드/문서/로그/test output에 쓰지 마.
++- `.env` 파일을 Git에 추가하지 마.
++- Strategy가 KIS를 직접 호출하게 만들지 마.
++- Agent/LLM이 직접 주문하게 만들지 마.
+ - auth, payment, production infra, database migrations는 건드리지 마.
+ - git commit, push, merge는 자동화하지 마.
+ 
+ ## 검증
+ 
+-가능하면 아래를 실행해줘.
+-
+-- python -m compileall app tests
+-- python -m pytest -p no:cacheprovider
+-
+-만약 현재 프로젝트 구조가 Python이 아니거나 테스트 명령이 다르면,
+-현재 repo 구조에 맞는 안전한 검증 명령을 실행하고 patch.md에 이유를 적어줘.
+-
+-## 완료 후 patch.md에 정리할 내용
+-
+-1. 어떤 파일을 수정했는지
+-2. KIS 인증 구조가 어떻게 되었는지
+-3. 계좌 조회 구조가 어떻게 되었는지
+-4. 시세 조회 구조가 어떻게 되었는지
+-5. 실제 주문 기능이 여전히 비활성인지
+-6. secret이 노출되지 않는지
+-7. 어떤 테스트를 실행했는지
+-8. 공식 문서가 없어 TODO로 남긴 부분
+-9. 다음 mvp에서 무엇을 하면 되는지
+-
+-## 다음 단계 예고
+-
+-mvp-008에서는 KIS 모의투자 주문 흐름을 연결할 예정이다.
+-단, mvp-008에서도 live trading은 비활성이고, 소액 검증 전까지 실계좌 주문은 금지한다.
+-
+-## 추가 조건
++아래를 실행해줘.
+ 
+-- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
+-- 필요한 경우에만 최소한의 질문을 해.
+\ No newline at end of file
++```bash
++cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
++.venv/bin/python -m compileall app tests
++.venv/bin/python -m pytest -p no:cacheprovider
+\ No newline at end of file
 diff --git a/web/public/app.js b/web/public/app.js
 index f27f460..d9fc2c2 100644
 --- a/web/public/app.js
diff --git a/docs/ai/jobs/mvp-007/pipeline.log.md b/docs/ai/jobs/mvp-007/pipeline.log.md
index 75df48b..88ef2c1 100644
--- a/docs/ai/jobs/mvp-007/pipeline.log.md
+++ b/docs/ai/jobs/mvp-007/pipeline.log.md
@@ -1477,3 +1477,1869 @@ index 0ce1e5d..7d07b26 100644
 ```
 (no output)
 ```
+
+## 2026-05-14T10:53:00.580Z — create-job
+
+```
+Ensured job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-007
+```
+
+## 2026-05-14T10:53:00.588Z — save-input
+
+```
+Saved: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-007/request.ko.md
+```
+
+## 2026-05-14T10:53:00.600Z — claude-plan
+
+```
+(no output)
+```
+
+## 2026-05-14T10:53:00.611Z — codex-implement
+
+```
+(no output)
+```
+
+## 2026-05-14T10:53:00.621Z — save-diff
+
+```
+diff --git a/docs/ai/jobs/mvp-004/request.ko.md b/docs/ai/jobs/mvp-004/request.ko.md
+index 7d9ecf1..dcfaa5c 100644
+--- a/docs/ai/jobs/mvp-004/request.ko.md
++++ b/docs/ai/jobs/mvp-004/request.ko.md
+@@ -1,10 +1,74 @@
+-# 작업 요청
++# 작업 ID
++mvp-004
+ 
+-GUI 파이프라인이 Claude 계획 완료 전에 Codex 단계로 넘어가는 문제를 수정한다.
++# 작업명
++AI 개발팀 GUI 화면 배치 개선
+ 
+-Claude 계획 단계는 plan.md와 codex-task.md가 생성되어야 완료된 것으로 본다.
+-Codex 구현 단계는 patch.md가 생성되어야 완료된 것으로 본다.
+-Claude 리뷰 단계는 review.md가 생성되어야 완료된 것으로 본다.
++현재 AI 개발팀 브라우저 GUI에서 화면 배치가 불편하다.
+ 
+-전체 파이프라인 버튼은 각 단계의 산출물 파일을 확인한 뒤 다음 단계로 넘어가야 한다.
+-승인 대기, 차단, 실패 상태가 감지되면 다음 단계로 넘어가면 안 된다.
++문제점:
++1. 파이프라인 상태 영역이 너무 위에 있어서 핵심 제어 버튼과 시선 흐름이 맞지 않는다.
++2. 승인 / 서비스 제어 / 실시간 출력 영역이 아래쪽에 있어 잘 안 보인다.
++3. 작업 설정 칸이 너무 길어서 화면을 많이 차지한다.
++4. 실제 작업 중에는 승인 버튼, 서비스 제어, 실시간 출력이 더 중요하므로 위쪽에서 바로 보여야 한다.
++
++원하는 변경사항:
++
++1. “파이프라인 상태” 영역을 “Claude → Codex → Claude 전체 실행” 버튼 아래로 내려줘.
++
++2. 아래 영역들을 상단 쪽으로 올려줘.
++   - 승인 / 계속 진행
++   - 거절
++   - 중단
++   - 서비스 제어
++   - 실시간 출력
++
++3. 작업 설정 영역을 더 짧고 컴팩트하게 만들어줘.
++   - 입력칸 높이를 줄여줘.
++   - 필요하면 접기/펼치기 형태로 만들어줘.
++   - 화면에서 너무 많은 공간을 차지하지 않게 해줘.
++
++4. 화면 우선순위를 아래 순서로 재배치해줘.
++   - 상단: 작업 ID / 작업 요청 입력 / 주요 실행 버튼
++   - 그 아래: 승인 / 서비스 제어 / 실시간 출력
++   - 그 아래: 파이프라인 상태
++   - 그 아래: 작업 설정 / 고급 설정 / 산출물 목록
++
++5. Claude + Codex 2-role 구조는 유지해줘.
++   - Gemini Manager, Claude Architect, Claude Reviewer, Git Shell을 다시 노출하지 마.
++   - Claude 계획 생성
++   - Codex 구현 실행
++   - Claude 리뷰 실행
++   - Claude → Codex → Claude 전체 실행
++   이 버튼 구조는 유지해줘.
++
++6. git status와 git diff는 수동 유틸리티 버튼으로만 유지해줘.
++   - commit, push, merge는 자동화하지 마.
++
++7. 반응형 화면도 깨지지 않게 해줘.
++   - 작은 화면에서도 실시간 출력과 승인 버튼이 잘 보여야 한다.
++
++수정 대상:
++- web/public/index.html
++- web/public/app.js
++- web/public/style.css
++- 필요하면 web/server.js
++- README.md 또는 docs/ai/CLAUDE_CODEX_WORKFLOW.md는 변경 내용이 있으면 최소한만 업데이트
++
++금지:
++- 주식 페이퍼매매 로직은 건드리지 마.
++- secrets, .env, auth, payment, production infra, database migrations는 건드리지 마.
++- 임의 shell 명령 입력 기능은 만들지 마.
++- git commit, push, merge는 자동화하지 마.
++
++검증:
++- node --check web/server.js
++- node --check web/public/app.js
++- git diff --stat
++
++완료 후:
++- 어떤 UI 영역을 어디로 옮겼는지
++- 작업 설정 영역을 어떻게 줄였는지
++- Claude + Codex 구조가 유지되는지
++- 테스트 결과가 무엇인지
++patch.md에 정리해줘.
+\ No newline at end of file
+diff --git a/docs/ai/jobs/mvp-007/pipeline.log.md b/docs/ai/jobs/mvp-007/pipeline.log.md
+index 75df48b..5af59ba 100644
+--- a/docs/ai/jobs/mvp-007/pipeline.log.md
++++ b/docs/ai/jobs/mvp-007/pipeline.log.md
+@@ -1477,3 +1477,27 @@ index 0ce1e5d..7d07b26 100644
+ ```
+ (no output)
+ ```
++
++## 2026-05-14T10:53:00.580Z — create-job
++
++```
++Ensured job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-007
++```
++
++## 2026-05-14T10:53:00.588Z — save-input
++
++```
++Saved: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-007/request.ko.md
++```
++
++## 2026-05-14T10:53:00.600Z — claude-plan
++
++```
++(no output)
++```
++
++## 2026-05-14T10:53:00.611Z — codex-implement
++
++```
++(no output)
++```
+diff --git a/docs/ai/jobs/mvp-007/request.ko.md b/docs/ai/jobs/mvp-007/request.ko.md
+index dfd0315..9fc2cdb 100644
+--- a/docs/ai/jobs/mvp-007/request.ko.md
++++ b/docs/ai/jobs/mvp-007/request.ko.md
+@@ -1,227 +1,170 @@
+ # 작업 ID
+-mvp-007
++mvp-008
+ 
+ # 작업명
+-KIS Open API 모의투자 인증 / 계좌 / 시세 연결
++KIS 모의투자 주문 흐름 연결 준비
+ 
+-미국주식 자동 페이퍼매매 시스템에 KIS Open API 모의투자 연결을 진행해줘.
++미국주식 자동 페이퍼매매 시스템에서 KIS 모의투자 주문 흐름을 연결할 준비를 해줘.
+ 
+-현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 연결 검증이다.
++현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 주문 흐름 검증이다.
+ live trading은 절대 활성화하지 않는다.
+ 
+-## 현재 전제
++## 현재 상태
+ 
+-mvp-006에서 KIS 설정 구조와 Broker Adapter 골격을 준비했다.
++mvp-006-1과 mvp-007에서 아래 작업이 완료되었다.
+ 
+-이번 mvp-007에서는 가능한 범위 안에서 아래 기능을 연결한다.
++- paper-trading 프로젝트 기본 구조 생성
++- KIS 설정 구조 준비
++- `.env` 기반 KIS 설정 로딩
++- KIS Broker Adapter 골격
++- KIS Auth / Account / MarketData Client 골격
++- `/paper/status`에 KIS 상태 표시
++- secret/account masking 테스트
++- 74개 테스트 통과
+ 
+-1. KIS 모의투자 인증 토큰 발급 연결
+-2. 토큰 refresh / 만료 처리 구조
+-3. KIS 모의투자 계좌 정보 조회
+-4. KIS 해외주식 또는 미국주식 시세 조회 구조
+-5. Broker healthcheck 강화
+-6. `/paper/status` 또는 기존 status endpoint에 KIS 연결 상태 표시
+-7. 실제 주문은 아직 연결하지 않음
++이번 mvp-008에서는 실제 실계좌 주문이 아니라,
++KIS 모의투자 주문 흐름을 안전하게 연결할 준비를 한다.
+ 
+-## 보안 조건
++## 핵심 목표
+ 
+-KIS 모의투자 계좌번호, app key, app secret은 `.env`에 저장되어 있다고 가정한다.
++Strategy → RiskEngine → OMS → BrokerAdapter → KIS Broker 경로가 유지되도록 하면서,
++KIS 모의투자 주문 메서드의 안전한 경계를 만든다.
+ 
+-중요:
+-- 실제 계좌번호, app key, app secret 값을 코드에 쓰지 마.
+-- patch.md, review.md, 로그, 테스트 출력에 실제 secret을 노출하지 마.
+-- `.env.example`에는 placeholder만 유지해.
+-- `.env`는 Git에 추가하지 마.
+-- 설정 객체 repr/logging에서 app secret이 노출되지 않게 해.
+-- 테스트에서도 실제 secret 값을 출력하지 마.
+-
+-## 공식 문서 조건
+-
+-KIS Open API endpoint, TR ID, payload는 공식 문서 기준으로만 구현해야 한다.
+-
+-중요:
+-- 공식 문서나 프로젝트 내 명확한 문서가 없으면 endpoint를 추측해서 만들지 마.
+-- 확실하지 않은 endpoint, TR ID, header, payload는 TODO로 남겨.
+-- fake endpoint를 만들지 마.
+-- 실제 주문 endpoint는 이번 작업에서 구현하지 마.
+-- 인증 / 계좌조회 / 시세조회도 확실한 공식 정보가 없으면 fail-closed + TODO로 남겨.
+-
+-## 이번 구현 범위
+-
+-가능하면 아래 기능을 구현해줘.
+-
+-### 1. KIS Auth Client
++단, 공식 문서가 확인되지 않은 endpoint, TR ID, payload는 절대 추측해서 구현하지 않는다.
+ 
+-- `.env`에서 아래 값을 읽는다.
+-  - KIS_ENV
+-  - KIS_ACCOUNT_NO
+-  - KIS_APP_KEY
+-  - KIS_APP_SECRET
+-- 모의투자 환경인지 확인한다.
+-- 인증 토큰 발급 메서드를 만든다.
+-- 토큰 만료 시 refresh 또는 재발급 가능 구조를 만든다.
+-- 인증 실패 시 fail-closed 한다.
+-- secret이 로그에 찍히지 않게 한다.
++## 구현할 내용
+ 
+-필요 메서드 예시:
+-- authenticate()
+-- refresh_token()
+-- get_access_token()
+-- is_authenticated()
+-- clear_token()
++### 1. KIS 주문 메서드 경계 정리
+ 
+-### 2. KIS Account Client
++`KisBroker` 또는 현재 구조에 맞는 KIS adapter에 아래 주문 관련 메서드를 정리해줘.
+ 
+-- 계좌 정보 조회 골격 또는 실제 연결을 구현한다.
+-- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
+-- 계좌번호는 출력 시 마스킹한다.
+-- 실패 시 주문 가능 상태로 전환하지 않는다.
+-
+-필요 메서드 예시:
+-- get_account()
+-- get_positions()
+-- get_cash_balance()
+-
+-### 3. KIS Market Data Client
+-
+-- 미국주식 시세 조회 구조를 만든다.
+-- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
+-- 최소 quote 모델을 반환한다.
+-- 실패 시 stale / unavailable 상태로 처리한다.
+-
+-필요 메서드 예시:
+-- get_quote(symbol)
+-- get_last_price(symbol)
+-- healthcheck_market_data()
+-
+-### 4. KIS Broker Adapter 연결
++- place_order()
++- cancel_order()
++- replace_order()
++- get_open_orders()
++- get_fills()
++- get_order_status()
+ 
+-기존 BrokerAdapter 구조를 유지한다.
++조건:
++- 실제 endpoint/TR ID/payload를 추측해서 만들지 마.
++- 공식 문서가 없으면 TODO + fail-closed로 둬.
++- 메서드는 존재하되, 실주문 전송은 아직 하지 마.
++- NotImplementedError 또는 안전한 Rejected 상태를 반환하게 해.
++- 에러 메시지는 secret/account를 노출하지 않아야 한다.
+ 
+-- authenticate()
+-- refresh_token()
+-- get_account()
+-- get_positions()
+-- get_quote()
+-- healthcheck()
++### 2. OMS → KIS Broker 연결 준비
+ 
+-주문 관련 메서드는 아직 실제 전송하지 않는다.
++OMS가 broker adapter를 통해 주문을 보낼 수 있는 구조인지 점검하고,
++필요하면 interface를 정리해줘.
+ 
+-- place_order()
+-- cancel_order()
+-- replace_order()
++중요:
++- Strategy가 KIS를 직접 호출하면 안 된다.
++- Agent/LLM이 KIS를 직접 호출하면 안 된다.
++- OMS를 우회해서 주문하면 안 된다.
++- 모든 주문은 반드시 RiskEngine을 통과해야 한다.
++- OMS만 executable order를 만들 수 있다.
++
++### 3. KIS 모의투자 주문 요청 모델 준비
++
++실제 전송은 하지 말고, 내부 도메인 모델 기준으로 KIS 주문 요청 변환 경계를 만들어줘.
++
++예:
++- symbol
++- side
++- quantity
++- order_type
++- limit_price
++- extended_hours
++- account_no_masked
++- broker_environment
+ 
+-위 주문 메서드는 이번 단계에서 fail-closed 또는 NotImplemented 상태로 둔다.
++조건:
++- 시장가 주문은 금지
++- 지정가 주문만 허용
++- live trading이면 차단
++- KIS_ENV가 paper가 아니면 차단
++- 계좌번호 원문은 출력하지 말고 마스킹만 사용
+ 
+-## 주문 안전 조건
++### 4. 주문 안전 guard 추가
+ 
+-반드시 유지해.
++KIS 주문 흐름에 아래 guard를 적용해줘.
+ 
+-- live trading은 false
+-- TRADING_MODE는 paper
+-- 시장가 주문 금지
+-- 실주문 전송 금지
+-- Strategy가 KIS Adapter를 직접 호출하지 않음
+-- Agent/LLM이 직접 주문하지 않음
+-- 모든 주문은 Strategy → RiskEngine → OMS → BrokerAdapter 경로 유지
+-- OMS 우회 금지
+-- RiskEngine 우회 금지
++- TRADING_MODE=paper만 허용
++- LIVE_TRADING_ENABLED=false 확인
++- ALLOW_MARKET_ORDERS=false 확인
++- KIS_ENV=paper 확인
++- order_type이 market이면 거절
++- quantity가 0 이하이면 거절
++- limit_price가 없으면 거절
++- stale quote면 거절
++- kill switch가 켜져 있으면 거절
+ 
+-## 상태 API
++### 5. `/paper/status` 또는 status에 주문 준비 상태 추가
+ 
+-가능하면 `/paper/status` 또는 기존 `/status`에 아래 정보를 추가해줘.
++가능하면 아래 상태를 추가해줘.
+ 
+-- broker_type
+-- broker_environment
+-- kis_config_loaded
+-- kis_authenticated
+-- kis_account_loaded
+-- kis_market_data_available
+-- live_trading_enabled
+-- allow_market_orders
+-- last_broker_error
++- kis_order_entry_ready
++- kis_order_entry_mode: disabled | paper_guarded | not_implemented
++- kis_order_methods_fail_closed: true
++- live_trading_enabled: false
++- allow_market_orders: false
+ - secret_exposed: false
+ 
+-중요:
+-- app key, app secret, 계좌번호 원문은 절대 출력하지 마.
+-- 계좌번호는 필요하면 마스킹해서 보여줘.
++실제 app key, app secret, 계좌번호 원문은 절대 출력하지 마.
+ 
+-## 테스트 요구사항
++### 6. 테스트 추가
+ 
+ 아래 테스트를 추가해줘.
+ 
+-1. `.env` 기반 KIS config 로딩 테스트
+-2. app secret이 repr/logging/status에 노출되지 않는지 테스트
+-3. KIS_ENV=paper 기본 동작 테스트
+-4. live trading 기본 false 테스트
+-5. 시장가 주문 기본 금지 테스트
+-6. 인증 client가 secret을 직접 출력하지 않는지 테스트
+-7. 공식 문서 정보가 없을 때 endpoint를 추측하지 않고 TODO/fail-closed 되는지 테스트
+-8. 주문 메서드가 아직 실주문을 전송하지 않는지 테스트
+-9. BrokerAdapter 인터페이스가 깨지지 않는지 테스트
+-10. `/paper/status` 또는 `/status`에 KIS 상태가 안전하게 표시되는지 테스트
++1. KIS place_order가 실주문을 보내지 않고 fail-closed 되는지
++2. KIS cancel_order가 실취소를 보내지 않고 fail-closed 되는지
++3. KIS replace_order가 실정정을 보내지 않고 fail-closed 되는지
++4. market order가 거절되는지
++5. limit_price 없는 주문이 거절되는지
++6. live trading true이면 거절되는지
++7. KIS_ENV가 paper가 아니면 거절되는지
++8. Strategy가 KIS adapter를 직접 호출하지 않는지
++9. OMS 경로를 우회하지 않는지
++10. status에 secret/account 원문이 노출되지 않는지
++11. 기존 74개 테스트가 계속 통과하는지
+ 
+ ## 수정 가능 파일
+ 
+-필요한 경우 아래 파일을 수정해도 된다.
++필요하면 아래 파일을 수정해도 된다.
+ 
+-- app/adapters/brokers/kis.py
+-- app/adapters/brokers/base.py
+-- app/core/config.py
+-- app/api/routes.py
+-- app/runtime/paper_runner.py
+-- app/monitoring/status.py
+-- app/domain/*
+-- tests/*
+-- .env.example
+-- README.md
+-- docs/architecture.md
+-- docs/runbook.md
++- projects/paper-trading/app/broker/kis.py
++- projects/paper-trading/app/broker/base.py
++- projects/paper-trading/app/oms/*
++- projects/paper-trading/app/risk/*
++- projects/paper-trading/app/api/routes.py
++- projects/paper-trading/app/api/server.py
++- projects/paper-trading/app/config/*
++- projects/paper-trading/app/models/*
++- projects/paper-trading/tests/*
++- projects/paper-trading/README.md
++- docs/ai/jobs/mvp-008/patch.md
+ 
+-실제 프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.
++프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.
+ 
+ ## 금지 사항
+ 
+-- 실제 KIS app key, app secret, 계좌번호를 코드에 쓰지 마.
+-- 실제 값을 patch.md, review.md, 로그에 출력하지 마.
+-- `.env` 파일을 Git에 추가하지 마.
+-- live trading을 true로 바꾸지 마.
+-- 실계좌 주문 기능을 만들지 마.
+-- 주문 endpoint를 연결하지 마.
+-- KIS endpoint / TR ID / payload를 추측해서 만들지 마.
++- 실제 KIS endpoint를 추측해서 만들지 마.
++- TR ID를 추측해서 넣지 마.
++- 실제 주문 전송 코드를 만들지 마.
++- live trading을 활성화하지 마.
+ - 시장가 주문을 허용하지 마.
+-- 브로커 API를 Strategy에서 직접 호출하게 만들지 마.
++- app key, app secret, 계좌번호 원문을 코드/문서/로그/test output에 쓰지 마.
++- `.env` 파일을 Git에 추가하지 마.
++- Strategy가 KIS를 직접 호출하게 만들지 마.
++- Agent/LLM이 직접 주문하게 만들지 마.
+ - auth, payment, production infra, database migrations는 건드리지 마.
+ - git commit, push, merge는 자동화하지 마.
+ 
+ ## 검증
+ 
+-가능하면 아래를 실행해줘.
+-
+-- python -m compileall app tests
+-- python -m pytest -p no:cacheprovider
+-
+-만약 현재 프로젝트 구조가 Python이 아니거나 테스트 명령이 다르면,
+-현재 repo 구조에 맞는 안전한 검증 명령을 실행하고 patch.md에 이유를 적어줘.
+-
+-## 완료 후 patch.md에 정리할 내용
+-
+-1. 어떤 파일을 수정했는지
+-2. KIS 인증 구조가 어떻게 되었는지
+-3. 계좌 조회 구조가 어떻게 되었는지
+-4. 시세 조회 구조가 어떻게 되었는지
+-5. 실제 주문 기능이 여전히 비활성인지
+-6. secret이 노출되지 않는지
+-7. 어떤 테스트를 실행했는지
+-8. 공식 문서가 없어 TODO로 남긴 부분
+-9. 다음 mvp에서 무엇을 하면 되는지
+-
+-## 다음 단계 예고
+-
+-mvp-008에서는 KIS 모의투자 주문 흐름을 연결할 예정이다.
+-단, mvp-008에서도 live trading은 비활성이고, 소액 검증 전까지 실계좌 주문은 금지한다.
+-
+-## 추가 조건
++아래를 실행해줘.
+ 
+-- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
+-- 필요한 경우에만 최소한의 질문을 해.
+\ No newline at end of file
++```bash
++cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
++.venv/bin/python -m compileall app tests
++.venv/bin/python -m pytest -p no:cacheprovider
+\ No newline at end of file
+diff --git a/web/public/app.js b/web/public/app.js
+index f27f460..d9fc2c2 100644
+--- a/web/public/app.js
++++ b/web/public/app.js
+@@ -9,6 +9,7 @@ const inputKoEl = document.querySelector('#inputKo');
+ const outputEl = document.querySelector('#output');
+ const artifactListEl = document.querySelector('#artifactList');
+ const runPipelineButton = document.querySelector('#runPipeline');
++const sendButtons = [...document.querySelectorAll('[data-send]')];
+ const pipelineStateEl = document.querySelector('#pipelineState');
+ const pipelineJobIdEl = document.querySelector('#pipelineJobId');
+ const pipelineStageEl = document.querySelector('#pipelineStage');
+@@ -31,6 +32,15 @@ const approvalModalEl = document.querySelector('#approvalModal');
+ const approvalModalStepEl = document.querySelector('#approvalModalStep');
+ const approvalModalWindowEl = document.querySelector('#approvalModalWindow');
+ const approvalModalSummaryEl = document.querySelector('#approvalModalSummary');
++const approvalModalTypeEl = document.querySelector('#approvalModalType');
++const approvalModalCommandEl = document.querySelector('#approvalModalCommand');
++const approvalModalCwdEl = document.querySelector('#approvalModalCwd');
++const approvalModalRiskEl = document.querySelector('#approvalModalRisk');
++const approvalModalRecommendationEl = document.querySelector('#approvalModalRecommendation');
++const approvalModalRawEl = document.querySelector('#approvalModalRaw');
++const approvalModalRiskWarningEl = document.querySelector('#approvalModalRiskWarning');
++const approvalModalApproveOnceEl = document.querySelector('#approvalModalApproveOnce');
++const approvalModalApproveSessionEl = document.querySelector('#approvalModalApproveSession');
+ const aiControlButtons = [
+   document.querySelector('#approveOnce'),
+   document.querySelector('#approveSession'),
+@@ -59,8 +69,18 @@ const finalPipelineStates = new Set([
+   'failed',
+   'blocked',
+   'manual_review_required',
++  'review_approved',
++  'review_changes_requested',
++  'manual_final_approval_required',
+   'idle'
+ ]);
++const stageWindows = {
++  'claude-plan': 'claude',
++  'codex-implement': 'codex',
++  'claude-review': 'claude',
++  'codex-review-fix': 'codex',
++  'claude-re-review': 'claude'
++};
+ 
+ projectDirEl.value = state.projectDir;
+ jobIdEl.value = state.jobId;
+@@ -183,6 +203,10 @@ runPipelineButton.addEventListener('click', async () => {
+ });
+ 
+ document.querySelector('#pipelineStatus').addEventListener('click', refreshPipelineStatus);
++document.querySelector('#finalManualReview').addEventListener('click', () => {
++  writeOutput('최종 확인', 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.');
++  refreshPipelineStatus();
++});
+ 
+ document.querySelector('#resetPipeline').addEventListener('click', async () => {
+   const result = await runAction('파이프라인 상태 초기화', () => requestJson('/api/pipeline/reset', {
+@@ -370,6 +394,7 @@ function renderPipelineStatus(status) {
+     summaryDiffEl.textContent = '-';
+     summaryReviewEl.textContent = '-';
+     runPipelineButton.disabled = false;
++    updateSendButtonGates(null);
+     return;
+   }
+ 
+@@ -389,6 +414,7 @@ function renderPipelineStatus(status) {
+   pipelineTargetWindowEl.textContent = pipeline.targetWindow || '-';
+   pipelineWaitingApprovalEl.textContent = pipeline.waitingApproval ? '예' : '아니오';
+   renderDetectedIssue(approvalRequest ? null : pipeline.detectedIssue);
++  updateSendButtonGates(pipeline);
+ 
+   if (pipeline.targetWindow && tmuxWindowEl.value !== pipeline.targetWindow) {
+     tmuxWindowEl.value = pipeline.targetWindow;
+@@ -410,8 +436,9 @@ function renderPipelineStatus(status) {
+   } else {
+     currentApprovalRequest = null;
+     closeApprovalModal();
+-    pipelineGuidanceEl.hidden = true;
+-    pipelineGuidanceEl.textContent = '';
++    const requirementsText = renderRequirementsText(pipeline.requirements);
++    pipelineGuidanceEl.hidden = !requirementsText;
++    pipelineGuidanceEl.textContent = requirementsText;
+     approvalInlinePromptEl.hidden = true;
+   }
+ 
+@@ -464,6 +491,47 @@ function renderPipelineStatus(status) {
+   summaryNextActionEl.textContent = pipeline.nextAction || '-';
+ }
+ 
++function renderRequirementsText(requirements) {
++  if (!requirements || !requirements.files || requirements.files.length === 0) {
++    return '';
++  }
++  const lines = [
++    `필수 파일 (${requirements.label || '현재 단계'}):`,
++    ...requirements.files.map((file) => `- ${file.name}: ${file.exists ? 'ready' : 'missing'}`),
++    `다음 단계 가능: ${requirements.nextStageAllowed ? 'yes' : 'no'}`
++  ];
++  return lines.join('\n');
++}
++
++function hasArtifact(pipeline, name) {
++  return (pipeline?.artifacts || []).some((artifact) => (artifact.name || artifact) === name);
++}
++
++function updateSendButtonGates(pipeline) {
++  sendButtons.forEach((button) => {
++    const target = button.dataset.send;
++    let disabled = false;
++    let title = '';
++    if (!pipeline) {
++      disabled = false;
++    } else if (target === 'codex-implement') {
++      disabled = !hasArtifact(pipeline, 'plan.md') || !hasArtifact(pipeline, 'codex-task.md');
++      title = disabled ? 'Claude 계획이 아직 완료되지 않았습니다. plan.md와 codex-task.md가 생성된 뒤 Codex를 실행할 수 있습니다.' : '';
++    } else if (target === 'claude-review') {
++      disabled = !hasArtifact(pipeline, 'patch.md');
++      title = disabled ? 'patch.md가 생성된 뒤 Claude 리뷰를 실행할 수 있습니다.' : '';
++    } else if (target === 'codex-review-fix') {
++      disabled = pipeline.state !== 'review_changes_requested';
++      title = disabled ? 'Claude가 수정 요청을 남긴 뒤 실행할 수 있습니다.' : '';
++    } else if (target === 'claude-re-review') {
++      disabled = !hasArtifact(pipeline, 'status.md');
++      title = disabled ? 'Codex 리뷰 반영 후 status.md가 생성된 뒤 실행할 수 있습니다.' : '';
++    }
++    button.disabled = disabled;
++    button.title = title;
++  });
++}
++
+ function getApprovalRequest(status, pipeline) {
+   const issue = pipeline.detectedIssue || {};
+   const isApproval = pipeline.state === 'approval_required' || issue.type === 'approval_required';
+@@ -472,16 +540,18 @@ function getApprovalRequest(status, pipeline) {
+   }
+ 
+   const targetWindow = issue.window || pipeline.targetWindow;
+-  if (!['claude', 'codex'].includes(targetWindow)) {
++  const stageTargetWindow = stageWindows[pipeline.step] || pipeline.targetWindow || targetWindow;
++  if (!['claude', 'codex'].includes(stageTargetWindow)) {
+     return null;
+   }
+ 
+   const jobId = status.jobId || jobIdEl.value.trim() || '-';
+   const step = pipeline.step || '-';
+-  const rawSummary = issue.summary || pipeline.message || '';
+-  const summary = cleanApprovalSummary(targetWindow);
+-  const key = `${jobId}:${step}:${targetWindow}:${rawSummary || summary}`;
+-  return { key, step, targetWindow, summary };
++  const approvalContext = issue.approvalContext || null;
++  const rawSummary = approvalContext?.rawBlock || issue.summary || pipeline.message || '';
++  const summary = approvalContext?.summary || cleanApprovalSummary(stageTargetWindow);
++  const key = `${jobId}:${step}:${stageTargetWindow}:${rawSummary || summary}`;
++  return { key, step, targetWindow: stageTargetWindow, summary, approvalContext };
+ }
+ 
+ function cleanApprovalSummary(windowName) {
+@@ -495,10 +565,41 @@ function openApprovalModal(request, force) {
+     return;
+   }
+   lastApprovalKey = request.key;
+-  approvalModalStepEl.textContent = request.step || '-';
+-  approvalModalWindowEl.textContent = request.targetWindow || '-';
+-  approvalModalSummaryEl.textContent = request.summary || '-';
++  renderApprovalContext(request, request.approvalContext);
+   approvalModalEl.hidden = false;
++  if (!request.approvalContext) {
++    loadApprovalContext(request);
++  }
++}
++
++async function loadApprovalContext(request) {
++  try {
++    const result = await requestJson(`/api/tmux/approval-context?window=${encodeURIComponent(request.targetWindow)}&step=${encodeURIComponent(request.step || '')}`);
++    if (!currentApprovalRequest || currentApprovalRequest.key !== request.key) {
++      return;
++    }
++    currentApprovalRequest.approvalContext = result.approvalContext;
++    renderApprovalContext(currentApprovalRequest, result.approvalContext);
++  } catch (error) {
++    approvalModalRawEl.textContent = error.message;
++  }
++}
++
++function renderApprovalContext(request, context) {
++  const risk = context?.risk || 'unknown';
++  approvalModalStepEl.textContent = request.step || context?.step || '-';
++  approvalModalWindowEl.textContent = request.targetWindow || context?.window || '-';
++  approvalModalSummaryEl.textContent = context?.summary || request.summary || '-';
++  approvalModalTypeEl.textContent = context?.type || 'unknown';
++  approvalModalCommandEl.textContent = context?.commandOrTarget || '확인 불가';
++  approvalModalCwdEl.textContent = context?.workingDirectory || '-';
++  approvalModalRiskEl.textContent = risk;
++  approvalModalRiskEl.dataset.risk = risk;
++  approvalModalRecommendationEl.textContent = context?.recommendation || '직접 확인 필요';
++  approvalModalRawEl.textContent = context?.rawBlock || '원문을 불러오는 중입니다.';
++  approvalModalRiskWarningEl.textContent = context?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.';
++  approvalModalApproveOnceEl.disabled = !context?.canApproveOnce;
++  approvalModalApproveSessionEl.disabled = !context?.canApproveSession;
+ }
+ 
+ function closeApprovalModal() {
+@@ -510,6 +611,10 @@ async function sendApprovalModalAction(endpoint) {
+     writeOutput('승인 명령 실패', '승인 대상 창을 확인할 수 없습니다.');
+     return;
+   }
++  if (!approvalEndpointAllowed(endpoint, currentApprovalRequest.approvalContext)) {
++    writeOutput('승인 명령 차단', currentApprovalRequest.approvalContext?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.');
++    return;
++  }
+ 
+   try {
+     await requestJson(endpoint, {
+@@ -524,6 +629,16 @@ async function sendApprovalModalAction(endpoint) {
+   }
+ }
+ 
++function approvalEndpointAllowed(endpoint, context) {
++  if (endpoint.endsWith('/approve-once')) {
++    return Boolean(context?.canApproveOnce);
++  }
++  if (endpoint.endsWith('/approve-session')) {
++    return Boolean(context?.canApproveSession);
++  }
++  return true;
++}
++
+ function normalizePipelineStatus(payload) {
+   if (payload && payload.status && typeof payload.status === 'object') {
+     return {
+@@ -534,6 +649,7 @@ function normalizePipelineStatus(payload) {
+       waitingApproval: Boolean(payload.status.waitingApproval),
+       detectedIssue: payload.status.detectedIssue || null,
+       artifacts: payload.status.artifacts || [],
++      requirements: payload.status.requirements || null,
+       gitDiff: payload.status.gitDiff || '-',
+       reviewStatus: payload.status.reviewStatus || '-',
+       nextAction: payload.status.nextAction || '-'
+@@ -548,6 +664,7 @@ function normalizePipelineStatus(payload) {
+     waitingApproval: false,
+     detectedIssue: null,
+     artifacts: payload && payload.artifacts ? payload.artifacts : [],
++    requirements: null,
+     gitDiff: '-',
+     reviewStatus: '-',
+     nextAction: '-'
+@@ -625,6 +742,10 @@ async function sendTmuxControl(title, endpoint) {
+     writeOutput(`${title} 실패`, 'Manual Shell(git-shell)은 비AI 창입니다. 승인/거절 키 입력은 Claude 또는 Codex 창에서만 사용하세요.');
+     return null;
+   }
++  if (currentApprovalRequest && currentApprovalRequest.targetWindow === windowName && !approvalEndpointAllowed(endpoint, currentApprovalRequest.approvalContext)) {
++    writeOutput(`${title} 차단`, currentApprovalRequest.approvalContext?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.');
++    return null;
++  }
+   const result = await runAction(title, () => requestJson(endpoint, {
+     method: 'POST',
+     body: JSON.stringify({ window: windowName })
+diff --git a/web/public/index.html b/web/public/index.html
+index a02de7a..60b76f9 100644
+--- a/web/public/index.html
++++ b/web/public/index.html
+@@ -16,42 +16,55 @@
+     </header>
+ 
+     <main class="layout">
+-      <section class="panel setup">
+-        <h2>작업 설정</h2>
+-        <label>
+-          프로젝트 경로
+-          <input id="projectDir" type="text" autocomplete="off" spellcheck="false">
+-        </label>
++      <section class="panel quick-actions">
++        <h2>핵심 실행</h2>
+         <label>
+           작업 ID
+           <input id="jobId" type="text" value="mvp-001" autocomplete="off" spellcheck="false">
+         </label>
+         <label>
+           한국어 작업 요청
+-          <textarea id="inputKo" spellcheck="false" rows="14"></textarea>
++          <textarea id="inputKo" spellcheck="false" rows="6"></textarea>
+         </label>
+         <p class="field-hint">여기에는 한국어 작업 요청만 입력하세요. 쉘 설정 명령, 실행 명령, 토큰, 비밀값은 넣지 않습니다.</p>
+-        <div class="role-display" aria-label="역할 안내">
+-          <div>
+-            <strong>Claude</strong>
+-            <span>planning / requirements / review</span>
+-          </div>
+-          <div>
+-            <strong>Codex</strong>
+-            <span>implementation / tests / patch summary</span>
+-          </div>
+-        </div>
+-        <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
+         <div class="pipeline-runner">
+           <button id="runPipeline" class="primary-action" type="button">Claude → Codex → Claude 전체 실행</button>
+           <div class="primary-actions">
+             <button data-send="claude-plan" type="button">Claude 계획 생성</button>
+             <button data-send="codex-implement" type="button">Codex 구현 실행</button>
+             <button data-send="claude-review" type="button">Claude 리뷰 실행</button>
++            <button data-send="codex-review-fix" type="button">Codex 리뷰 반영 실행</button>
++            <button data-send="claude-re-review" type="button">Claude 재리뷰 실행</button>
++            <button id="finalManualReview" type="button">최종 확인으로 이동</button>
+           </div>
+         </div>
+       </section>
+ 
++      <section class="panel control-panel">
++        <h2>승인 / 서비스 제어</h2>
++        <p class="warning-text">승인은 Claude 또는 Codex AI CLI 창에만 키 입력을 보내는 기능입니다. Manual Shell(git-shell)은 사람이 직접 git/test 명령을 실행하는 비AI 창입니다.</p>
++        <label>
++          제어할 tmux 창
++          <select id="tmuxWindow"></select>
++        </label>
++        <div class="actions control-actions">
++          <button id="approveOnce" type="button">승인 / 계속 진행</button>
++          <button id="approveSession" type="button">세션 승인</button>
++          <button id="rejectAction" type="button">거절</button>
++          <button id="interruptAction" type="button">중단</button>
++          <button id="restartAiTeam" type="button">AI팀 재시작</button>
++          <button id="restartGui" type="button">GUI 서버 재시작</button>
++        </div>
++      </section>
++
++      <section class="panel tmux-panel">
++        <div class="panel-head">
++          <h2>실시간 tmux 출력</h2>
++          <button id="refreshTmuxOutput" type="button">출력 새로고침</button>
++        </div>
++        <pre id="tmuxOutput" aria-live="polite"></pre>
++      </section>
++
+       <section class="panel pipeline-status">
+         <div class="panel-head">
+           <h2>파이프라인 상태</h2>
+@@ -96,29 +109,42 @@
+         <div id="pipelineSteps" class="pipeline-steps"></div>
+       </section>
+ 
+-      <section class="panel control-panel">
+-        <h2>승인 / 서비스 제어</h2>
+-        <p class="warning-text">승인은 Claude 또는 Codex AI CLI 창에만 키 입력을 보내는 기능입니다. Manual Shell(git-shell)은 사람이 직접 git/test 명령을 실행하는 비AI 창입니다.</p>
++      <details class="panel job-settings">
++        <summary>작업 설정</summary>
+         <label>
+-          제어할 tmux 창
+-          <select id="tmuxWindow"></select>
++          프로젝트 경로
++          <input id="projectDir" type="text" autocomplete="off" spellcheck="false">
+         </label>
+-        <div class="actions control-actions">
+-          <button id="approveOnce" type="button">승인 / 계속 진행</button>
+-          <button id="approveSession" type="button">세션 승인</button>
+-          <button id="rejectAction" type="button">거절</button>
+-          <button id="interruptAction" type="button">중단</button>
+-          <button id="restartAiTeam" type="button">AI팀 재시작</button>
+-          <button id="restartGui" type="button">GUI 서버 재시작</button>
++        <div class="role-display" aria-label="역할 안내">
++          <div>
++            <strong>Claude</strong>
++            <span>planning / requirements / review</span>
++          </div>
++          <div>
++            <strong>Codex</strong>
++            <span>implementation / tests / patch summary</span>
++          </div>
+         </div>
+-      </section>
++        <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
++      </details>
+ 
+-      <section class="panel tmux-panel">
++      <details class="panel advanced-panel">
++        <summary>고급 제어</summary>
++        <div class="actions">
++          <button id="startTeam" type="button">AI 팀 시작</button>
++          <button id="createJob" type="button">작업 폴더 생성</button>
++          <button id="saveInput" type="button">request.ko.md 저장</button>
++          <button id="gitStatus" type="button">git status</button>
++          <button id="gitDiff" type="button">git diff</button>
++        </div>
++      </details>
++
++      <section class="panel artifacts">
+         <div class="panel-head">
+-          <h2>실시간 tmux 출력</h2>
+-          <button id="refreshTmuxOutput" type="button">출력 새로고침</button>
++          <h2>산출물</h2>
++          <button id="loadArtifacts" type="button">목록 새로고침</button>
+         </div>
+-        <pre id="tmuxOutput" aria-live="polite"></pre>
++        <div id="artifactList" class="artifact-list"></div>
+       </section>
+ 
+       <section class="panel result-summary">
+@@ -143,25 +169,6 @@
+         </dl>
+       </section>
+ 
+-      <details class="panel advanced-panel">
+-        <summary>고급 제어</summary>
+-        <div class="actions">
+-          <button id="startTeam" type="button">AI 팀 시작</button>
+-          <button id="createJob" type="button">작업 폴더 생성</button>
+-          <button id="saveInput" type="button">request.ko.md 저장</button>
+-          <button id="gitStatus" type="button">git status</button>
+-          <button id="gitDiff" type="button">git diff</button>
+-        </div>
+-      </details>
+-
+-      <section class="panel artifacts">
+-        <div class="panel-head">
+-          <h2>산출물</h2>
+-          <button id="loadArtifacts" type="button">목록 새로고침</button>
+-        </div>
+-        <div id="artifactList" class="artifact-list"></div>
+-      </section>
+-
+       <section class="panel output-panel">
+         <div class="panel-head">
+           <h2>출력</h2>
+@@ -191,11 +198,36 @@
+             <dt>감지 요약</dt>
+             <dd id="approvalModalSummary">-</dd>
+           </div>
++          <div>
++            <dt>요청 유형</dt>
++            <dd id="approvalModalType">-</dd>
++          </div>
++          <div>
++            <dt>명령/대상</dt>
++            <dd id="approvalModalCommand">-</dd>
++          </div>
++          <div>
++            <dt>작업 디렉터리</dt>
++            <dd id="approvalModalCwd">-</dd>
++          </div>
++          <div>
++            <dt>위험도</dt>
++            <dd id="approvalModalRisk">-</dd>
++          </div>
++          <div>
++            <dt>추천 행동</dt>
++            <dd id="approvalModalRecommendation">-</dd>
++          </div>
+         </dl>
++        <details class="approval-raw">
++          <summary>원문 보기</summary>
++          <pre id="approvalModalRaw">-</pre>
++        </details>
+         <p class="modal-warning">주의: 이 버튼은 현재 AI CLI 창에 키 입력을 보내는 기능입니다. 위험한 명령은 승인하지 마세요.</p>
++        <p id="approvalModalRiskWarning" class="modal-warning">-</p>
+         <div class="modal-actions">
+-          <button data-approval-action="/api/tmux/approve-once" type="button">1회 승인</button>
+-          <button data-approval-action="/api/tmux/approve-session" type="button">세션 승인</button>
++          <button id="approvalModalApproveOnce" data-approval-action="/api/tmux/approve-once" type="button">1회 승인</button>
++          <button id="approvalModalApproveSession" data-approval-action="/api/tmux/approve-session" type="button">세션 승인</button>
+           <button data-approval-action="/api/tmux/reject" class="danger-action" type="button">거절</button>
+           <button data-approval-action="/api/tmux/interrupt" class="danger-action" type="button">중단</button>
+           <button id="dismissApprovalModal" type="button">닫기</button>
+diff --git a/web/public/style.css b/web/public/style.css
+index 9d50479..e9c85a8 100644
+--- a/web/public/style.css
++++ b/web/public/style.css
+@@ -64,11 +64,11 @@ h2 {
+ }
+ 
+ .layout {
+-  display: grid;
+-  grid-template-columns: minmax(320px, 0.95fr) minmax(360px, 1.05fr);
++  display: flex;
++  flex-direction: column;
+   gap: 18px;
+   padding: 22px;
+-  max-width: 1440px;
++  max-width: 1100px;
+   margin: 0 auto;
+ }
+ 
+@@ -80,14 +80,6 @@ h2 {
+   padding: 18px;
+ }
+ 
+-.setup {
+-  grid-row: span 4;
+-}
+-
+-.output-panel {
+-  grid-column: 2;
+-}
+-
+ .panel-head {
+   display: flex;
+   align-items: center;
+@@ -103,6 +95,26 @@ h2 {
+   justify-content: flex-end;
+ }
+ 
++.quick-actions {
++  display: grid;
++  gap: 12px;
++}
++
++.job-settings {
++  padding: 14px 18px;
++}
++
++.job-settings > summary {
++  cursor: pointer;
++  font-size: 18px;
++  font-weight: 800;
++  padding: 4px 0;
++}
++
++.job-settings[open] {
++  padding-bottom: 18px;
++}
++
+ label {
+   display: grid;
+   gap: 7px;
+@@ -173,7 +185,7 @@ select {
+ }
+ 
+ textarea {
+-  min-height: 330px;
++  min-height: 140px;
+   resize: vertical;
+   padding: 12px;
+   line-height: 1.5;
+@@ -484,6 +496,37 @@ button:disabled {
+   font-weight: 800;
+ }
+ 
++.approval-details dd[data-risk="low"] {
++  color: #0f766e;
++}
++
++.approval-details dd[data-risk="medium"],
++.approval-details dd[data-risk="unknown"] {
++  color: #92400e;
++}
++
++.approval-details dd[data-risk="high"] {
++  color: var(--danger);
++}
++
++.approval-raw {
++  margin-top: 14px;
++}
++
++.approval-raw summary {
++  cursor: pointer;
++  color: var(--muted);
++  font-size: 13px;
++  font-weight: 800;
++}
++
++.approval-raw pre {
++  min-height: 120px;
++  max-height: 220px;
++  margin-top: 8px;
++  font-size: 12px;
++}
++
+ .modal-warning {
+   margin: 14px 0 0;
+   padding: 10px 12px;
+@@ -610,16 +653,9 @@ pre {
+   }
+ 
+   .layout {
+-    grid-template-columns: 1fr;
+     padding: 14px;
+   }
+ 
+-  .setup,
+-  .output-panel {
+-    grid-row: auto;
+-    grid-column: auto;
+-  }
+-
+   .step-grid {
+     grid-template-columns: 1fr;
+   }
+diff --git a/web/server.js b/web/server.js
+index 0ce1e5d..7d07b26 100644
+--- a/web/server.js
++++ b/web/server.js
+@@ -16,6 +16,8 @@ const SAFE_WINDOWS = {
+   'claude-plan': 'claude',
+   'codex-implement': 'codex',
+   'claude-review': 'claude',
++  'codex-review-fix': 'codex',
++  'claude-re-review': 'claude',
+   claude: 'claude',
+   codex: 'codex'
+ };
+@@ -56,9 +58,7 @@ const ISSUE_PATTERNS = [
+   {
+     type: 'approval_required',
+     patterns: [
+-      /approval|approve|allow|continue|proceed|permission/i,
+-      /승인|허용|계속 진행|진행하시겠습니까|거절/i,
+-      /1\).*(approve|allow|승인|계속)|2\).*(session|세션)|3\).*(reject|거절)/i
++      /allow execution|allow edit|do you want to proceed|would you like to continue|allow for this session|no, suggest changes|enter your response/i
+     ]
+   },
+   {
+@@ -80,12 +80,16 @@ const pipelineStates = new Map();
+ const PIPELINE_STAGES = [
+   { id: 'claude-plan', state: 'claude_planning', label: 'Claude 계획 생성', role: 'claude-plan', window: 'claude', artifacts: ['plan.md', 'codex-task.md'] },
+   { id: 'codex-implement', state: 'codex_implementing', label: 'Codex 구현 실행', role: 'codex-implement', window: 'codex', artifacts: ['patch.md'] },
+-  { id: 'claude-review', state: 'claude_reviewing', label: 'Claude 리뷰 실행', role: 'claude-review', window: 'claude', artifacts: ['review.md'] }
++  { id: 'claude-review', state: 'claude_reviewing', label: 'Claude 리뷰 실행', role: 'claude-review', window: 'claude', artifacts: ['review.md'] },
++  { id: 'codex-review-fix', state: 'codex_fixing_review', label: 'Codex 리뷰 반영 실행', role: 'codex-review-fix', window: 'codex', artifacts: ['status.md'] },
++  { id: 'claude-re-review', state: 'claude_re_reviewing', label: 'Claude 재리뷰 실행', role: 'claude-re-review', window: 'claude', artifacts: ['review.md'] }
+ ];
+ const ACTIVE_PIPELINE_STATES = new Set([
+   'claude_planning',
+   'codex_implementing',
+   'claude_reviewing',
++  'codex_fixing_review',
++  'claude_re_reviewing',
+   'approval_required'
+ ]);
+ const FINAL_PIPELINE_STATES = new Set([
+@@ -93,6 +97,9 @@ const FINAL_PIPELINE_STATES = new Set([
+   'failed',
+   'blocked',
+   'manual_review_required',
++  'review_approved',
++  'review_changes_requested',
++  'manual_final_approval_required',
+   'idle'
+ ]);
+ const ARTIFACT_PRIORITY = [
+@@ -240,8 +247,97 @@ function currentTargetWindow(state) {
+   return stage ? stage.window : null;
+ }
+ 
+-function publicIdlePipelineState(projectDir = null, jobId = null) {
++function stageByState(status) {
++  return PIPELINE_STAGES.find((stage) => stage.state === status) || null;
++}
++
++function stageForGate(status, currentStep) {
++  return stageById(currentStep) || stageByState(status) || PIPELINE_STAGES[0];
++}
++
++function nextStageGate(state) {
++  if (!state) {
++    return PIPELINE_STAGES[0];
++  }
++  if (state.status === 'succeeded' || state.status === 'review_approved' || state.status === 'manual_final_approval_required') {
++    return null;
++  }
++  if (state.status === 'review_changes_requested') {
++    return stageById('codex-review-fix');
++  }
++  return stageForGate(state.status, state.currentStep);
++}
++
++function artifactPath(projectDir, jobId, name) {
++  return path.join(projectDir, 'docs', 'ai', 'jobs', jobId, name);
++}
++
++async function artifactStat(projectDir, jobId, name) {
++  const stat = await fs.stat(artifactPath(projectDir, jobId, name)).catch(() => null);
++  return stat && stat.isFile() && stat.size > 0 ? stat : null;
++}
++
++async function artifactExists(projectDir, jobId, name, afterIso = null) {
++  const stat = await artifactStat(projectDir, jobId, name);
++  if (!stat) {
++    return false;
++  }
++  if (!afterIso) {
++    return true;
++  }
++  const after = Date.parse(afterIso);
++  return Number.isNaN(after) ? true : stat.mtimeMs >= after;
++}
++
++async function artifactStatus(projectDir, jobId, names, afterIso = null) {
++  const files = [];
++  for (const name of names) {
++    const stat = await artifactStat(projectDir, jobId, name);
++    const exists = stat ? await artifactExists(projectDir, jobId, name, afterIso) : false;
++    files.push({ name, exists, modifiedAt: stat ? stat.mtime.toISOString() : null });
++  }
++  return files;
++}
++
++async function allArtifactsExist(projectDir, jobId, names, afterIso = null) {
++  const files = await artifactStatus(projectDir, jobId, names, afterIso);
++  return {
++    ok: files.every((file) => file.exists),
++    files,
++    missing: files.filter((file) => !file.exists).map((file) => file.name)
++  };
++}
++
++async function buildStageRequirements(projectDir, jobId, stage) {
++  if (!stage) {
++    return {
++      stage: null,
++      label: null,
++      files: [],
++      missing: [],
++      nextStageAllowed: true,
++      guidance: ''
++    };
++  }
++  const requirements = await allArtifactsExist(projectDir, jobId, stage.artifacts);
++  return {
++    stage: stage.id,
++    label: stage.label,
++    files: requirements.files,
++    missing: requirements.missing,
++    nextStageAllowed: requirements.ok,
++    guidance: requirements.ok
++      ? '다음 단계를 실행할 수 있습니다.'
++      : `필수 산출물이 아직 생성되지 않았습니다: ${requirements.missing.join(', ')}`
++  };
++}
++
++async function publicIdlePipelineState(projectDir = null, jobId = null) {
+   const now = new Date().toISOString();
++  const artifacts = projectDir && jobId ? await listArtifacts(projectDir, jobId) : [];
++  const requirements = projectDir && jobId
++    ? await buildStageRequirements(projectDir, jobId, PIPELINE_STAGES[0])
++    : await buildStageRequirements(null, null, null);
+   return {
+     ok: true,
+     jobKey: projectDir && jobId ? pipelineKey(projectDir, jobId) : null,
+@@ -255,15 +351,22 @@ function publicIdlePipelineState(projectDir = null, jobId = null) {
+       targetWindow: null,
+       waitingApproval: false,
+       detectedIssue: null,
+-      artifacts: [],
++      artifacts,
+       gitDiff: '-',
+       reviewStatus: '-',
+-      nextAction: '작업 요청을 입력한 뒤 Claude → Codex → Claude 전체 실행을 누르세요.'
++      nextAction: '작업 요청을 입력한 뒤 Claude → Codex → Claude 전체 실행을 누르세요.',
++      requirements
++    },
++    artifacts,
++    summary: {
++      createdArtifacts: artifacts.map((artifact) => artifact.name),
++      gitDiff: { hasChanges: false, saved: false, path: null, changedFiles: [] },
++      review: { status: 'not_started', file: null, decision: null }
+     }
+   };
+ }
+ 
+-function publicPipelineState(state) {
++async function publicPipelineState(state) {
+   if (!state) {
+     return publicIdlePipelineState();
+   }
+@@ -277,6 +380,7 @@ function publicPipelineState(state) {
+     ? `${review.status}: ${review.file}${review.decision ? ` / ${review.decision}` : ''}`
+     : review.status || '-';
+   const detectedIssue = state.detectedIssue || null;
++  const requirements = await buildStageRequirements(state.projectDir, state.jobId, nextStageGate(state));
+ 
+   return {
+     ok: true,
+@@ -297,7 +401,8 @@ function publicPipelineState(state) {
+       artifacts: state.artifacts,
+       gitDiff: gitDiffText,
+       reviewStatus,
+-      nextAction: nextRecommendedAction(state, reviewStatus)
++      nextAction: nextRecommendedAction(state, reviewStatus),
++      requirements
+     },
+     steps: state.steps,
+     artifacts: state.artifacts,
+@@ -315,6 +420,18 @@ function pipelineMessage(status) {
+   if (status === 'claude_reviewing') {
+     return 'Claude가 현재 diff와 패치 요약을 리뷰하는 단계입니다.';
+   }
++  if (status === 'codex_fixing_review') {
++    return 'Codex가 Claude 리뷰의 수정 요청만 반영하는 단계입니다.';
++  }
++  if (status === 'claude_re_reviewing') {
++    return 'Claude가 수정 반영 후 diff를 다시 리뷰하는 단계입니다.';
++  }
++  if (status === 'review_approved' || status === 'manual_final_approval_required') {
++    return 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.';
++  }
++  if (status === 'review_changes_requested') {
++    return 'Claude가 수정 요청을 남겼습니다. Codex가 리뷰 내용을 반영해야 합니다.';
++  }
+   if (status === 'succeeded') {
+     return '파이프라인이 완료되었습니다.';
+   }
+@@ -334,11 +451,14 @@ function pipelineMessage(status) {
+ }
+ 
+ function nextRecommendedAction(state, reviewStatus) {
+-  if (state.status === 'succeeded') {
++  if (state.status === 'review_approved' || state.status === 'manual_final_approval_required' || state.status === 'succeeded') {
+     return reviewStatus && reviewStatus !== '-'
+       ? 'Claude 리뷰 결과를 확인한 뒤 사람이 직접 commit, push, PR 생성 여부를 결정하세요.'
+       : '산출물과 git diff를 확인한 뒤 사람이 직접 다음 작업을 결정하세요.';
+   }
++  if (state.status === 'review_changes_requested') {
++    return 'Codex 리뷰 반영 실행을 눌러 Claude가 요청한 수정만 반영하세요.';
++  }
+   if (state.status === 'manual_review_required' || state.status === 'approval_required') {
+     return 'tmux 출력을 확인하고 필요한 경우 승인 / 계속 진행, 세션 승인, 거절, 중단 중 하나를 선택하세요.';
+   }
+@@ -438,24 +558,25 @@ async function refreshPipelineArtifacts(state) {
+ 
+ async function findFirstExistingArtifact(projectDir, jobId, names) {
+   for (const name of names) {
+-    const filePath = path.join(projectDir, 'docs', 'ai', 'jobs', jobId, name);
+-    const stat = await fs.stat(filePath).catch(() => null);
+-    if (stat && stat.isFile() && stat.size > 0) {
+-      return { name, path: filePath };
++    if (await artifactExists(projectDir, jobId, name)) {
++      return { name, path: artifactPath(projectDir, jobId, name) };
+     }
+   }
+   return null;
+ }
+ 
+-async function waitForArtifact(projectDir, jobId, names, state = null, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
++async function waitForArtifacts(projectDir, jobId, names, state = null, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
+   const started = Date.now();
++  const afterIso = state && state.currentStep
++    ? state.steps.find((step) => step.id === state.currentStep)?.startedAt || null
++    : null;
+   while (Date.now() - started < timeoutMs) {
+     if (state && !ACTIVE_PIPELINE_STATES.has(state.status)) {
+       return null;
+     }
+-    const artifact = await findFirstExistingArtifact(projectDir, jobId, names);
+-    if (artifact) {
+-      return artifact;
++    const requirements = await allArtifactsExist(projectDir, jobId, names, afterIso);
++    if (requirements.ok) {
++      return requirements.files;
+     }
+     await new Promise((resolve) => setTimeout(resolve, PIPELINE_POLL_MS));
+   }
+@@ -492,6 +613,10 @@ function markTimedOutRunningStep(state) {
+ }
+ 
+ function summarizeIssue(output, type) {
++  if (type === 'approval_required') {
++    const block = extractApprovalBlock(output);
++    return block ? block.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)[0]?.slice(0, 220) || ISSUE_RECOMMENDATIONS[type] : ISSUE_RECOMMENDATIONS[type];
++  }
+   const lines = String(output || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
+   const matcher = ISSUE_PATTERNS.find((item) => item.type === type);
+   if (matcher) {
+@@ -503,9 +628,72 @@ function summarizeIssue(output, type) {
+   return lines.slice(-3).join(' ').slice(0, 220) || ISSUE_RECOMMENDATIONS[type] || '최근 tmux 출력에서 확인이 필요한 상태를 감지했습니다.';
+ }
+ 
++function isLikelyCodeOrSearchLine(line) {
++  return /^\s*[+-]/.test(line)
++    || /\bconst\s+|\bfunction\s+|=>|stageWindows|pipelineStates|server\.js|Search\s+/i.test(line)
++    || /['"]approval_required['"]|['"]manual_review_required['"]/i.test(line)
++    || /^\s*(web\/|app\/|docs\/|projects\/).+:\d+[:\s]/.test(line)
++    || /^\s*```/.test(line);
++}
++
++function stripCodeLikeApprovalLines(output) {
++  const lines = String(output || '').split(/\r?\n/);
++  let inCodeBlock = false;
++  const kept = [];
++  for (const line of lines) {
++    if (/^\s*```/.test(line)) {
++      inCodeBlock = !inCodeBlock;
++      continue;
++    }
++    if (inCodeBlock || isLikelyCodeOrSearchLine(line)) {
++      continue;
++    }
++    kept.push(line);
++  }
++  return kept.join('\n');
++}
++
++function hasApprovalOptions(block) {
++  return /(?:^|\n)\s*(?:1[.)]|2[.)]|3[.)]).*(?:allow|approve|session|reject|승인|세션|거절|continue)/i.test(block);
++}
++
++function hasCommandOrEditSummary(block) {
++  return /(?:command|execute|run|edit|file|patch|modify|명령|실행|수정|편집|파일)\s*[:：]/i.test(block)
++    || /\b(npm|node|python3?|git|mkdir|cat|chmod|cp|mv|rm|sudo|curl|gh)\b/i.test(block)
++    || /[\w./-]+\.(?:js|css|html|md|json|py|ts|tsx|jsx|yml|yaml|sh)/i.test(block);
++}
++
++function findStrictApprovalPromptBlock(output) {
++  const cleaned = stripCodeLikeApprovalLines(output);
++  const lines = cleaned.split(/\r?\n/);
++  const strongPattern = /allow execution|allow edit|do you want to proceed|would you like to continue|allow for this session|no, suggest changes|enter your response/i;
++  for (let i = lines.length - 1; i >= 0; i -= 1) {
++    if (!strongPattern.test(lines[i])) {
++      continue;
++    }
++    const block = lines.slice(Math.max(0, i - 8), Math.min(lines.length, i + 10)).join('\n').trim();
++    if (hasApprovalOptions(block) || hasCommandOrEditSummary(block)) {
++      return block;
++    }
++  }
++  return '';
++}
++
+ function detectIssueFromOutput(output, windowName) {
+   const text = String(output || '');
+   for (const category of ISSUE_PATTERNS) {
++    if (category.type === 'approval_required') {
++      const block = findStrictApprovalPromptBlock(text);
++      if (block) {
++        return {
++          type: category.type,
++          window: windowName,
++          summary: summarizeIssue(block, category.type),
++          recommendation: ISSUE_RECOMMENDATIONS[category.type]
++        };
++      }
++      continue;
++    }
+     if (category.patterns.some((pattern) => pattern.test(text))) {
+       return {
+         type: category.type,
+@@ -527,6 +715,94 @@ async function captureRecentTmuxOutput(windowName, lines = 120) {
+   return result.ok ? redactedOutput(result.stdout) : '';
+ }
+ 
++function approvalTypeFromBlock(block) {
++  if (/edit|patch|modify|write|수정|편집|파일/i.test(block)) {
++    return 'file_edit';
++  }
++  if (/command|execute|run|명령|실행/i.test(block)) {
++    return 'command_execution';
++  }
++  return 'unknown';
++}
++
++function extractCommandOrTarget(block) {
++  const lines = String(block || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
++  const commandLine = lines.find((line) => /^\$|^>|^`[^`]+`$|^(npm|node|python|python3|git|mkdir|cat|chmod|cp|mv|rm|sudo|curl|gh)\b/i.test(line));
++  if (commandLine) {
++    return commandLine.replace(/^[$>]\s*/, '').replace(/^`|`$/g, '').slice(0, 260);
++  }
++  const fileLine = lines.find((line) => /(?:^|\s)([\w./-]+\.(?:js|css|html|md|json|py|ts|tsx|jsx|yml|yaml|sh))(?:\s|$)/i.test(line));
++  return fileLine ? fileLine.slice(0, 260) : '';
++}
++
++function classifyApprovalRisk(block, commandOrTarget) {
++  const text = `${block || ''}\n${commandOrTarget || ''}`;
++  if (/rm\s+-rf|sudo\b|curl\b.*\|\s*(bash|sh)|git\s+push|gh\s+pr\s+merge|deploy|deployment|kubectl|terraform|\.env|secret|token|api\s*key|auth\/|payment\/|billing\/|migrations?\/|production|prod\b/i.test(text)) {
++    return {
++      risk: 'high',
++      recommendation: '거절 권장',
++      canApproveOnce: false,
++      canApproveSession: false,
++      warning: '승인하지 마세요. 거절 또는 중단하세요.'
++    };
++  }
++  if (/npm\s+install|chmod\b|\bcp\b|\bmv\b/i.test(text) || /(?:^|\s)(?!docs\/ai\/jobs\/)[\w./-]+\.(?:js|css|html|py|ts|tsx|jsx|json|yml|yaml|sh)/i.test(text)) {
++    return {
++      risk: 'medium',
++      recommendation: '직접 확인 필요',
++      canApproveOnce: true,
++      canApproveSession: false,
++      warning: '명령과 수정 대상을 tmux 출력에서 확인한 뒤 1회 승인만 고려하세요.'
++    };
++  }
++  if (/mkdir\s+-p\s+docs\/ai\/jobs\/|docs\/ai\/jobs\/[\w._-]+|git\s+(status|diff)\b|node\s+--check\b|python3?\s+-m\s+(py_compile|compileall)\b|cat\s+docs\/ai\/jobs\//i.test(text)) {
++    return {
++      risk: 'low',
++      recommendation: '1회 승인 가능',
++      canApproveOnce: true,
++      canApproveSession: true,
++      warning: '세션 승인은 같은 종류의 안전한 명령이 반복될 때만 사용하세요.'
++    };
++  }
++  return {
++    risk: 'unknown',
++    recommendation: '직접 확인 필요',
++    canApproveOnce: false,
++    canApproveSession: false,
++    warning: '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.'
++  };
++}
++
++function extractApprovalBlock(output) {
++  return findStrictApprovalPromptBlock(output);
++}
++
++function cleanWorkingDirectory(block) {
++  const match = String(block || '').match(/(?:cwd|working directory|작업 디렉터리)\s*[:=]\s*([^\n]+)/i);
++  return match ? match[1].trim().slice(0, 260) : '-';
++}
++
++async function buildApprovalContext(windowName, step = null) {
++  const safeWindow = validateAiTmuxWindow(windowName);
++  const output = await captureRecentTmuxOutput(safeWindow, 180);
++  const rawBlock = extractApprovalBlock(output);
++  if (!rawBlock) {
++    return null;
++  }
++  const commandOrTarget = extractCommandOrTarget(rawBlock);
++  const risk = classifyApprovalRisk(rawBlock, commandOrTarget);
++  return {
++    window: safeWindow,
++    step,
++    type: approvalTypeFromBlock(rawBlock),
++    commandOrTarget: commandOrTarget || '확인 불가',
++    workingDirectory: cleanWorkingDirectory(rawBlock),
++    rawBlock,
++    ...risk,
++    summary: `${safeWindow === 'codex' ? 'Codex' : 'Claude'} 창에서 명령 실행 승인 요청이 감지되었습니다.`
++  };
++}
++
+ async function refreshDetectedIssue(state) {
+   if (!state || !ACTIVE_PIPELINE_STATES.has(state.status)) {
+     return;
+@@ -540,6 +816,13 @@ async function refreshDetectedIssue(state) {
+   if (!issue) {
+     return;
+   }
++  if (issue.type === 'approval_required') {
++    issue.approvalContext = await buildApprovalContext(targetWindow, state.currentStep).catch(() => null);
++    if (!issue.approvalContext) {
++      return;
++    }
++    issue.summary = issue.approvalContext.summary;
++  }
+ 
+   state.detectedIssue = issue;
+   state.error = issue.recommendation;
+@@ -565,25 +848,24 @@ async function applyArtifactProgress(state) {
+     return;
+   }
+ 
+-  for (const stage of PIPELINE_STAGES) {
+-    const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, stage.artifacts);
+-    const step = state.steps.find((item) => item.id === stage.id);
+-    if (artifact && step && step.status === 'running') {
+-      state.status = stage.state;
+-      state.error = null;
+-      state.detectedIssue = null;
+-      setStep(state, stage.id, stage.label, 'succeeded', artifact.name);
+-    }
+-  }
+-
+   const current = stageById(state.currentStep);
+   if (current) {
+-    const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, current.artifacts);
+-    if (artifact) {
++    const step = state.steps.find((item) => item.id === current.id);
++    const requirements = await allArtifactsExist(state.projectDir, state.jobId, current.artifacts, step?.startedAt || null);
++    if (requirements.ok) {
+       state.status = current.state;
+       state.error = null;
+       state.detectedIssue = null;
+-      setStep(state, current.id, current.label, 'succeeded', artifact.name);
++      setStep(state, current.id, current.label, 'succeeded', requirements.files.map((file) => file.name).join(', '));
++      if (current.id === 'codex-review-fix') {
++        state.status = 'review_changes_requested';
++        state.currentStep = null;
++        state.error = 'Codex가 리뷰 반영을 완료했습니다. Claude 재리뷰를 실행하세요.';
++      }
++      if (current.id === 'claude-review' || current.id === 'claude-re-review') {
++        await updateReviewSummary(state.projectDir, state.jobId, state);
++        applyReviewDecision(state);
++      }
+     }
+   }
+ }
+@@ -646,14 +928,60 @@ async function updateReviewSummary(projectDir, jobId, state) {
+     return;
+   }
+   const content = await fs.readFile(artifact.path, 'utf8').catch(() => '');
+-  const decisionLine = content.split(/\r?\n/).find((line) => /decision|verdict|approve|request changes|comment/i.test(line));
++  const decision = detectReviewDecision(content);
++  const decisionLine = content.split(/\r?\n/).find((line) => /decision|verdict|approve|request[_ -]?changes|block|승인|수정\s*요청|차단|보류/i.test(line));
+   state.summary.review = {
+     status: 'available',
+     file: artifact.name,
+-    decision: decisionLine ? decisionLine.trim() : null
++    decision,
++    decisionLine: decisionLine ? decisionLine.trim() : null
+   };
+ }
+ 
++function detectReviewDecision(content) {
++  const text = String(content || '');
++  if (/\bBLOCK\b|차단|보류/i.test(text)) {
++    return 'BLOCK';
++  }
++  if (/\bREQUEST[_ -]?CHANGES\b|수정\s*요청/i.test(text)) {
++    return 'REQUEST_CHANGES';
++  }
++  if (/\bAPPROVE\b|\bAPPROVED\b|승인/i.test(text)) {
++    return 'APPROVE';
++  }
++  return 'UNKNOWN';
++}
++
++function applyReviewDecision(state) {
++  const decision = state.summary.review.decision;
++  const now = new Date().toISOString();
++  if (decision === 'APPROVE') {
++    state.status = 'manual_final_approval_required';
++    state.currentStep = null;
++    state.finishedAt = now;
++    state.error = 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.';
++    return;
++  }
++  if (decision === 'REQUEST_CHANGES') {
++    state.status = 'review_changes_requested';
++    state.currentStep = null;
++    state.finishedAt = now;
++    state.error = 'Claude가 수정 요청을 남겼습니다. Codex가 리뷰 내용을 반영해야 합니다.';
++    return;
++  }
++  if (decision === 'BLOCK') {
++    state.status = 'blocked';
++    state.currentStep = null;
++    state.finishedAt = now;
++    state.error = 'Claude가 작업을 차단했습니다. 요청 범위나 안전 조건을 수정해야 합니다.';
++    return;
++  }
++  state.status = 'manual_review_required';
++  state.currentStep = null;
++  state.finishedAt = now;
++  state.error = 'Claude 리뷰 결정을 확인할 수 없습니다. review.md에서 APPROVE, REQUEST_CHANGES, BLOCK 중 하나를 확인하세요.';
++}
++
+ async function runPipeline(state, inputKo) {
+   const { projectDir, jobId } = state;
+   const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
+@@ -679,11 +1007,11 @@ async function runPipeline(state, inputKo) {
+       if (!sent.ok) {
+         throw new Error(`${step.label} 실패: ${sent.message || sent.stderr || 'tmux 전송 실패'}`);
+       }
+-      const artifact = await waitForArtifact(projectDir, jobId, step.artifacts, state);
++      const artifacts = await waitForArtifacts(projectDir, jobId, step.artifacts, state);
+       if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
+         return;
+       }
+-      if (!artifact) {
++      if (!artifacts) {
+         markManualRequired(state, step.id, step.label);
+         await refreshPipelineArtifacts(state);
+         return;
+@@ -691,7 +1019,7 @@ async function runPipeline(state, inputKo) {
+       state.status = step.state;
+       state.error = null;
+       state.detectedIssue = null;
+-      setStep(state, step.id, step.label, 'succeeded', artifact.name);
++      setStep(state, step.id, step.label, 'succeeded', artifacts.map((artifact) => artifact.name).join(', '));
+       await refreshPipelineArtifacts(state);
+ 
+       if (step.id === 'codex-implement') {
+@@ -723,11 +1051,11 @@ async function runPipeline(state, inputKo) {
+     if (!reviewed.ok) {
+       throw new Error(`Claude 리뷰 전송 실패: ${reviewed.message || reviewed.stderr || 'tmux 전송 실패'}`);
+     }
+-    const reviewArtifact = await waitForArtifact(projectDir, jobId, reviewerStep.artifacts, state);
++    const reviewArtifacts = await waitForArtifacts(projectDir, jobId, reviewerStep.artifacts, state);
+     if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
+       return;
+     }
+-    if (!reviewArtifact) {
++    if (!reviewArtifacts) {
+       markManualRequired(state, reviewerStep.id, reviewerStep.label);
+       await updateReviewSummary(projectDir, jobId, state);
+       await refreshPipelineArtifacts(state);
+@@ -736,13 +1064,10 @@ async function runPipeline(state, inputKo) {
+     state.status = reviewerStep.state;
+     state.error = null;
+     state.detectedIssue = null;
+-    setStep(state, reviewerStep.id, reviewerStep.label, 'succeeded', reviewArtifact.name);
++    setStep(state, reviewerStep.id, reviewerStep.label, 'succeeded', reviewArtifacts.map((artifact) => artifact.name).join(', '));
+     await updateReviewSummary(projectDir, jobId, state);
+     await refreshPipelineArtifacts(state);
+-
+-    state.status = 'succeeded';
+-    state.currentStep = null;
+-    state.finishedAt = new Date().toISOString();
++    applyReviewDecision(state);
+   } catch (error) {
+     state.status = 'failed';
+     state.error = error.message || '파이프라인 실행 실패';
+@@ -797,6 +1122,31 @@ function buildPrompt(role, projectDir, jobId, inputKo) {
+       '',
+       `Review the git diff saved at ${path.join(jobDir, 'local-diff.patch')} when present, ${path.join(jobDir, 'patch.md')}, and the approved request/plan.`,
+       `Write the review into ${path.join(jobDir, 'review.md')} using the Claude review output format.`,
++      'The review must include exactly one decision marker: APPROVE, REQUEST_CHANGES, or BLOCK.',
++      'Do not commit, push, merge, deploy, or run arbitrary shell commands.'
++    ].join('\n');
++  }
++
++  if (role === 'codex-review-fix') {
++    return [
++      'Use prompts/codex-implementer.md.',
++      common,
++      '',
++      `Read ${path.join(jobDir, 'patch.md')}, ${path.join(jobDir, 'review.md')}, and the current git diff.`,
++      'Apply only the changes explicitly requested by Claude review. Do not expand scope.',
++      `Update ${path.join(jobDir, 'patch.md')} and write ${path.join(jobDir, 'status.md')} with what changed and which checks ran.`,
++      'Do not commit, push, merge, deploy, or change secrets, .env, auth, payment, production infra, or database migrations.'
++    ].join('\n');
++  }
++
++  if (role === 'claude-re-review') {
++    return [
++      'Use prompts/claude.md.',
++      common,
++      '',
++      `Re-review the updated git diff, ${path.join(jobDir, 'patch.md')}, ${path.join(jobDir, 'status.md')}, and the previous review in ${path.join(jobDir, 'review.md')}.`,
++      `Update ${path.join(jobDir, 'review.md')} with the new review result.`,
++      'The review must include exactly one decision marker: APPROVE, REQUEST_CHANGES, or BLOCK.',
+       'Do not commit, push, merge, deploy, or run arbitrary shell commands.'
+     ].join('\n');
+   }
+@@ -883,6 +1233,51 @@ function handleError(res, error) {
+   res.status(400).json({ ok: false, error: error.message || '요청을 처리할 수 없습니다.' });
+ }
+ 
++function getOrCreatePipelineState(projectDir, jobId) {
++  const key = pipelineKey(projectDir, jobId);
++  let state = pipelineStates.get(key);
++  if (!state) {
++    state = createPipelineState(projectDir, jobId);
++    state.status = 'idle';
++    state.currentStep = null;
++    pipelineStates.set(key, state);
++  }
++  return state;
++}
++
++async function requireArtifacts(projectDir, jobId, names, message) {
++  const requirements = await allArtifactsExist(projectDir, jobId, names);
++  if (!requirements.ok) {
++    throw new Error(`${message} 누락: ${requirements.missing.join(', ')}`);
++  }
++}
++
++async function sendManualStage(projectDir, jobId, inputKo, stageId) {
++  const stage = stageById(stageId);
++  if (!stage) {
++    throw new Error('허용되지 않은 단계입니다.');
++  }
++  const state = getOrCreatePipelineState(projectDir, jobId);
++  if (ACTIVE_PIPELINE_STATES.has(state.status)) {
++    throw new Error('이미 실행 중인 단계가 있습니다.');
++  }
++  state.status = stage.state;
++  state.error = null;
++  state.detectedIssue = null;
++  state.finishedAt = null;
++  setStep(state, stage.id, stage.label, 'running');
++  const result = await sendToWindow(stage.role, projectDir, jobId, inputKo);
++  await appendPipelineLog(projectDir, jobId, stage.id, `${result.stdout || ''}${result.stderr || ''}${result.message || ''}`);
++  if (!result.ok) {
++    state.status = 'failed';
++    state.error = result.message || result.stderr || 'tmux 전송 실패';
++    state.finishedAt = new Date().toISOString();
++    setStep(state, stage.id, stage.label, 'failed', state.error);
++  }
++  await refreshPipelineArtifacts(state);
++  return { state, result };
++}
++
+ app.get('/api/status', async (req, res) => {
+   const result = await runFile(path.join(SCRIPTS_DIR, 'status-ai-team.sh'), []);
+   res.json(cleanOutput(result));
+@@ -1004,11 +1399,11 @@ app.get('/api/pipeline/status', async (req, res) => {
+       if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
+         await updateReviewSummary(projectDir, jobId, state);
+       }
+-      res.json(publicPipelineState(state));
++      res.json(await publicPipelineState(state));
+       return;
+     }
+ 
+-    res.json(publicIdlePipelineState(projectDir, jobId));
++    res.json(await publicIdlePipelineState(projectDir, jobId));
+   } catch (error) {
+     handleError(res, error);
+   }
+@@ -1049,6 +1444,20 @@ app.get('/api/tmux/output', async (req, res) => {
+   }
+ });
+ 
++app.get('/api/tmux/approval-context', async (req, res) => {
++  try {
++    const windowName = validateAiTmuxWindow(req.query.window);
++    const context = await buildApprovalContext(windowName, typeof req.query.step === 'string' ? req.query.step : null);
++    if (!context) {
++      res.status(404).json({ ok: false, error: '실제 승인 프롬프트를 찾지 못했습니다.' });
++      return;
++    }
++    res.json({ ok: true, approvalContext: context });
++  } catch (error) {
++    handleError(res, error);
++  }
++});
++
+ for (const [endpoint, keys] of [
+   ['/api/tmux/approve-once', ['1', 'Enter']],
+   ['/api/tmux/approve-session', ['2', 'Enter']],
+@@ -1124,15 +1533,35 @@ app.post('/api/service/restart-gui', async (req, res) => {
+ for (const [endpoint, role] of [
+   ['/api/send/claude-plan', 'claude-plan'],
+   ['/api/send/codex-implement', 'codex-implement'],
+-  ['/api/send/claude-review', 'claude-review']
++  ['/api/send/claude-review', 'claude-review'],
++  ['/api/send/codex-review-fix', 'codex-review-fix'],
++  ['/api/send/claude-re-review', 'claude-re-review']
+ ]) {
+   app.post(endpoint, async (req, res) => {
+     try {
+       const projectDir = await resolveProjectDir(req.body.projectDir);
+       const jobId = validateJobId(req.body.jobId);
+       const inputKo = typeof req.body.inputKo === 'string' ? req.body.inputKo : '';
+-      const result = await sendToWindow(role, projectDir, jobId, inputKo);
+-      res.json(cleanOutput(result));
++      if (role === 'codex-implement') {
++        await requireArtifacts(projectDir, jobId, ['plan.md', 'codex-task.md'], 'Claude 계획이 아직 완료되지 않았습니다. plan.md와 codex-task.md가 생성된 뒤 Codex를 실행할 수 있습니다.');
++      }
++      if (role === 'claude-review') {
++        await requireArtifacts(projectDir, jobId, ['patch.md'], 'patch.md가 생성된 뒤 Claude 리뷰를 실행할 수 있습니다.');
++      }
++      if (role === 'codex-review-fix') {
++        await requireArtifacts(projectDir, jobId, ['patch.md', 'review.md'], 'patch.md와 review.md가 생성된 뒤 Codex 리뷰 반영을 실행할 수 있습니다.');
++      }
++      if (role === 'claude-re-review') {
++        await requireArtifacts(projectDir, jobId, ['patch.md', 'review.md', 'status.md'], 'Codex 리뷰 반영 상태가 생성된 뒤 Claude 재리뷰를 실행할 수 있습니다.');
++      }
++      const stage = stageById(role);
++      const { state, result } = stage
++        ? await sendManualStage(projectDir, jobId, inputKo, role)
++        : { state: null, result: await sendToWindow(role, projectDir, jobId, inputKo) };
++      res.json({
++        ...cleanOutput(result),
++        pipeline: state ? (await publicPipelineState(state)).status : null
++      });
+     } catch (error) {
+       handleError(res, error);
+     }
+
+```
+
+## 2026-05-14T10:53:00.629Z — claude-review
+
+```
+(no output)
+```
diff --git a/docs/ai/jobs/mvp-007/request.ko.md b/docs/ai/jobs/mvp-007/request.ko.md
index dfd0315..9fc2cdb 100644
--- a/docs/ai/jobs/mvp-007/request.ko.md
+++ b/docs/ai/jobs/mvp-007/request.ko.md
@@ -1,227 +1,170 @@
 # 작업 ID
-mvp-007
+mvp-008
 
 # 작업명
-KIS Open API 모의투자 인증 / 계좌 / 시세 연결
+KIS 모의투자 주문 흐름 연결 준비
 
-미국주식 자동 페이퍼매매 시스템에 KIS Open API 모의투자 연결을 진행해줘.
+미국주식 자동 페이퍼매매 시스템에서 KIS 모의투자 주문 흐름을 연결할 준비를 해줘.
 
-현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 연결 검증이다.
+현재 목표는 실전매매가 아니라 KIS 모의투자 / paper trading 주문 흐름 검증이다.
 live trading은 절대 활성화하지 않는다.
 
-## 현재 전제
+## 현재 상태
 
-mvp-006에서 KIS 설정 구조와 Broker Adapter 골격을 준비했다.
+mvp-006-1과 mvp-007에서 아래 작업이 완료되었다.
 
-이번 mvp-007에서는 가능한 범위 안에서 아래 기능을 연결한다.
+- paper-trading 프로젝트 기본 구조 생성
+- KIS 설정 구조 준비
+- `.env` 기반 KIS 설정 로딩
+- KIS Broker Adapter 골격
+- KIS Auth / Account / MarketData Client 골격
+- `/paper/status`에 KIS 상태 표시
+- secret/account masking 테스트
+- 74개 테스트 통과
 
-1. KIS 모의투자 인증 토큰 발급 연결
-2. 토큰 refresh / 만료 처리 구조
-3. KIS 모의투자 계좌 정보 조회
-4. KIS 해외주식 또는 미국주식 시세 조회 구조
-5. Broker healthcheck 강화
-6. `/paper/status` 또는 기존 status endpoint에 KIS 연결 상태 표시
-7. 실제 주문은 아직 연결하지 않음
+이번 mvp-008에서는 실제 실계좌 주문이 아니라,
+KIS 모의투자 주문 흐름을 안전하게 연결할 준비를 한다.
 
-## 보안 조건
+## 핵심 목표
 
-KIS 모의투자 계좌번호, app key, app secret은 `.env`에 저장되어 있다고 가정한다.
+Strategy → RiskEngine → OMS → BrokerAdapter → KIS Broker 경로가 유지되도록 하면서,
+KIS 모의투자 주문 메서드의 안전한 경계를 만든다.
 
-중요:
-- 실제 계좌번호, app key, app secret 값을 코드에 쓰지 마.
-- patch.md, review.md, 로그, 테스트 출력에 실제 secret을 노출하지 마.
-- `.env.example`에는 placeholder만 유지해.
-- `.env`는 Git에 추가하지 마.
-- 설정 객체 repr/logging에서 app secret이 노출되지 않게 해.
-- 테스트에서도 실제 secret 값을 출력하지 마.
-
-## 공식 문서 조건
-
-KIS Open API endpoint, TR ID, payload는 공식 문서 기준으로만 구현해야 한다.
-
-중요:
-- 공식 문서나 프로젝트 내 명확한 문서가 없으면 endpoint를 추측해서 만들지 마.
-- 확실하지 않은 endpoint, TR ID, header, payload는 TODO로 남겨.
-- fake endpoint를 만들지 마.
-- 실제 주문 endpoint는 이번 작업에서 구현하지 마.
-- 인증 / 계좌조회 / 시세조회도 확실한 공식 정보가 없으면 fail-closed + TODO로 남겨.
-
-## 이번 구현 범위
-
-가능하면 아래 기능을 구현해줘.
-
-### 1. KIS Auth Client
+단, 공식 문서가 확인되지 않은 endpoint, TR ID, payload는 절대 추측해서 구현하지 않는다.
 
-- `.env`에서 아래 값을 읽는다.
-  - KIS_ENV
-  - KIS_ACCOUNT_NO
-  - KIS_APP_KEY
-  - KIS_APP_SECRET
-- 모의투자 환경인지 확인한다.
-- 인증 토큰 발급 메서드를 만든다.
-- 토큰 만료 시 refresh 또는 재발급 가능 구조를 만든다.
-- 인증 실패 시 fail-closed 한다.
-- secret이 로그에 찍히지 않게 한다.
+## 구현할 내용
 
-필요 메서드 예시:
-- authenticate()
-- refresh_token()
-- get_access_token()
-- is_authenticated()
-- clear_token()
+### 1. KIS 주문 메서드 경계 정리
 
-### 2. KIS Account Client
+`KisBroker` 또는 현재 구조에 맞는 KIS adapter에 아래 주문 관련 메서드를 정리해줘.
 
-- 계좌 정보 조회 골격 또는 실제 연결을 구현한다.
-- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
-- 계좌번호는 출력 시 마스킹한다.
-- 실패 시 주문 가능 상태로 전환하지 않는다.
-
-필요 메서드 예시:
-- get_account()
-- get_positions()
-- get_cash_balance()
-
-### 3. KIS Market Data Client
-
-- 미국주식 시세 조회 구조를 만든다.
-- 공식 문서 기준이 확인된 경우에만 실제 요청을 작성한다.
-- 최소 quote 모델을 반환한다.
-- 실패 시 stale / unavailable 상태로 처리한다.
-
-필요 메서드 예시:
-- get_quote(symbol)
-- get_last_price(symbol)
-- healthcheck_market_data()
-
-### 4. KIS Broker Adapter 연결
+- place_order()
+- cancel_order()
+- replace_order()
+- get_open_orders()
+- get_fills()
+- get_order_status()
 
-기존 BrokerAdapter 구조를 유지한다.
+조건:
+- 실제 endpoint/TR ID/payload를 추측해서 만들지 마.
+- 공식 문서가 없으면 TODO + fail-closed로 둬.
+- 메서드는 존재하되, 실주문 전송은 아직 하지 마.
+- NotImplementedError 또는 안전한 Rejected 상태를 반환하게 해.
+- 에러 메시지는 secret/account를 노출하지 않아야 한다.
 
-- authenticate()
-- refresh_token()
-- get_account()
-- get_positions()
-- get_quote()
-- healthcheck()
+### 2. OMS → KIS Broker 연결 준비
 
-주문 관련 메서드는 아직 실제 전송하지 않는다.
+OMS가 broker adapter를 통해 주문을 보낼 수 있는 구조인지 점검하고,
+필요하면 interface를 정리해줘.
 
-- place_order()
-- cancel_order()
-- replace_order()
+중요:
+- Strategy가 KIS를 직접 호출하면 안 된다.
+- Agent/LLM이 KIS를 직접 호출하면 안 된다.
+- OMS를 우회해서 주문하면 안 된다.
+- 모든 주문은 반드시 RiskEngine을 통과해야 한다.
+- OMS만 executable order를 만들 수 있다.
+
+### 3. KIS 모의투자 주문 요청 모델 준비
+
+실제 전송은 하지 말고, 내부 도메인 모델 기준으로 KIS 주문 요청 변환 경계를 만들어줘.
+
+예:
+- symbol
+- side
+- quantity
+- order_type
+- limit_price
+- extended_hours
+- account_no_masked
+- broker_environment
 
-위 주문 메서드는 이번 단계에서 fail-closed 또는 NotImplemented 상태로 둔다.
+조건:
+- 시장가 주문은 금지
+- 지정가 주문만 허용
+- live trading이면 차단
+- KIS_ENV가 paper가 아니면 차단
+- 계좌번호 원문은 출력하지 말고 마스킹만 사용
 
-## 주문 안전 조건
+### 4. 주문 안전 guard 추가
 
-반드시 유지해.
+KIS 주문 흐름에 아래 guard를 적용해줘.
 
-- live trading은 false
-- TRADING_MODE는 paper
-- 시장가 주문 금지
-- 실주문 전송 금지
-- Strategy가 KIS Adapter를 직접 호출하지 않음
-- Agent/LLM이 직접 주문하지 않음
-- 모든 주문은 Strategy → RiskEngine → OMS → BrokerAdapter 경로 유지
-- OMS 우회 금지
-- RiskEngine 우회 금지
+- TRADING_MODE=paper만 허용
+- LIVE_TRADING_ENABLED=false 확인
+- ALLOW_MARKET_ORDERS=false 확인
+- KIS_ENV=paper 확인
+- order_type이 market이면 거절
+- quantity가 0 이하이면 거절
+- limit_price가 없으면 거절
+- stale quote면 거절
+- kill switch가 켜져 있으면 거절
 
-## 상태 API
+### 5. `/paper/status` 또는 status에 주문 준비 상태 추가
 
-가능하면 `/paper/status` 또는 기존 `/status`에 아래 정보를 추가해줘.
+가능하면 아래 상태를 추가해줘.
 
-- broker_type
-- broker_environment
-- kis_config_loaded
-- kis_authenticated
-- kis_account_loaded
-- kis_market_data_available
-- live_trading_enabled
-- allow_market_orders
-- last_broker_error
+- kis_order_entry_ready
+- kis_order_entry_mode: disabled | paper_guarded | not_implemented
+- kis_order_methods_fail_closed: true
+- live_trading_enabled: false
+- allow_market_orders: false
 - secret_exposed: false
 
-중요:
-- app key, app secret, 계좌번호 원문은 절대 출력하지 마.
-- 계좌번호는 필요하면 마스킹해서 보여줘.
+실제 app key, app secret, 계좌번호 원문은 절대 출력하지 마.
 
-## 테스트 요구사항
+### 6. 테스트 추가
 
 아래 테스트를 추가해줘.
 
-1. `.env` 기반 KIS config 로딩 테스트
-2. app secret이 repr/logging/status에 노출되지 않는지 테스트
-3. KIS_ENV=paper 기본 동작 테스트
-4. live trading 기본 false 테스트
-5. 시장가 주문 기본 금지 테스트
-6. 인증 client가 secret을 직접 출력하지 않는지 테스트
-7. 공식 문서 정보가 없을 때 endpoint를 추측하지 않고 TODO/fail-closed 되는지 테스트
-8. 주문 메서드가 아직 실주문을 전송하지 않는지 테스트
-9. BrokerAdapter 인터페이스가 깨지지 않는지 테스트
-10. `/paper/status` 또는 `/status`에 KIS 상태가 안전하게 표시되는지 테스트
+1. KIS place_order가 실주문을 보내지 않고 fail-closed 되는지
+2. KIS cancel_order가 실취소를 보내지 않고 fail-closed 되는지
+3. KIS replace_order가 실정정을 보내지 않고 fail-closed 되는지
+4. market order가 거절되는지
+5. limit_price 없는 주문이 거절되는지
+6. live trading true이면 거절되는지
+7. KIS_ENV가 paper가 아니면 거절되는지
+8. Strategy가 KIS adapter를 직접 호출하지 않는지
+9. OMS 경로를 우회하지 않는지
+10. status에 secret/account 원문이 노출되지 않는지
+11. 기존 74개 테스트가 계속 통과하는지
 
 ## 수정 가능 파일
 
-필요한 경우 아래 파일을 수정해도 된다.
+필요하면 아래 파일을 수정해도 된다.
 
-- app/adapters/brokers/kis.py
-- app/adapters/brokers/base.py
-- app/core/config.py
-- app/api/routes.py
-- app/runtime/paper_runner.py
-- app/monitoring/status.py
-- app/domain/*
-- tests/*
-- .env.example
-- README.md
-- docs/architecture.md
-- docs/runbook.md
+- projects/paper-trading/app/broker/kis.py
+- projects/paper-trading/app/broker/base.py
+- projects/paper-trading/app/oms/*
+- projects/paper-trading/app/risk/*
+- projects/paper-trading/app/api/routes.py
+- projects/paper-trading/app/api/server.py
+- projects/paper-trading/app/config/*
+- projects/paper-trading/app/models/*
+- projects/paper-trading/tests/*
+- projects/paper-trading/README.md
+- docs/ai/jobs/mvp-008/patch.md
 
-실제 프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.
+프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.
 
 ## 금지 사항
 
-- 실제 KIS app key, app secret, 계좌번호를 코드에 쓰지 마.
-- 실제 값을 patch.md, review.md, 로그에 출력하지 마.
-- `.env` 파일을 Git에 추가하지 마.
-- live trading을 true로 바꾸지 마.
-- 실계좌 주문 기능을 만들지 마.
-- 주문 endpoint를 연결하지 마.
-- KIS endpoint / TR ID / payload를 추측해서 만들지 마.
+- 실제 KIS endpoint를 추측해서 만들지 마.
+- TR ID를 추측해서 넣지 마.
+- 실제 주문 전송 코드를 만들지 마.
+- live trading을 활성화하지 마.
 - 시장가 주문을 허용하지 마.
-- 브로커 API를 Strategy에서 직접 호출하게 만들지 마.
+- app key, app secret, 계좌번호 원문을 코드/문서/로그/test output에 쓰지 마.
+- `.env` 파일을 Git에 추가하지 마.
+- Strategy가 KIS를 직접 호출하게 만들지 마.
+- Agent/LLM이 직접 주문하게 만들지 마.
 - auth, payment, production infra, database migrations는 건드리지 마.
 - git commit, push, merge는 자동화하지 마.
 
 ## 검증
 
-가능하면 아래를 실행해줘.
-
-- python -m compileall app tests
-- python -m pytest -p no:cacheprovider
-
-만약 현재 프로젝트 구조가 Python이 아니거나 테스트 명령이 다르면,
-현재 repo 구조에 맞는 안전한 검증 명령을 실행하고 patch.md에 이유를 적어줘.
-
-## 완료 후 patch.md에 정리할 내용
-
-1. 어떤 파일을 수정했는지
-2. KIS 인증 구조가 어떻게 되었는지
-3. 계좌 조회 구조가 어떻게 되었는지
-4. 시세 조회 구조가 어떻게 되었는지
-5. 실제 주문 기능이 여전히 비활성인지
-6. secret이 노출되지 않는지
-7. 어떤 테스트를 실행했는지
-8. 공식 문서가 없어 TODO로 남긴 부분
-9. 다음 mvp에서 무엇을 하면 되는지
-
-## 다음 단계 예고
-
-mvp-008에서는 KIS 모의투자 주문 흐름을 연결할 예정이다.
-단, mvp-008에서도 live trading은 비활성이고, 소액 검증 전까지 실계좌 주문은 금지한다.
-
-## 추가 조건
+아래를 실행해줘.
 
-- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
-- 필요한 경우에만 최소한의 질문을 해.
\ No newline at end of file
+```bash
+cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
+.venv/bin/python -m compileall app tests
+.venv/bin/python -m pytest -p no:cacheprovider
\ No newline at end of file
diff --git a/projects/paper-trading/.env.example b/projects/paper-trading/.env.example
index 4558286..4d493ff 100644
--- a/projects/paper-trading/.env.example
+++ b/projects/paper-trading/.env.example
@@ -1,6 +1,7 @@
 TRADING_MODE=paper
 LIVE_TRADING_ENABLED=false
 ALLOW_MARKET_ORDERS=false
+KILL_SWITCH_ENGAGED=false
 
 # Alpaca Paper trading base URL must be provided by the user in .env. This repository does not guess vendor endpoints.
 ALPACA_PAPER_API_BASE=
diff --git a/projects/paper-trading/README.md b/projects/paper-trading/README.md
index 351e213..260c572 100644
--- a/projects/paper-trading/README.md
+++ b/projects/paper-trading/README.md
@@ -81,6 +81,45 @@ Blocked candidates never reach OMS.
 | `KIS_APP_KEY` | KIS app key | `.env`에서만 |
 | `KIS_APP_SECRET` | KIS app secret | `.env`에서만 |
 | `ALLOW_MARKET_ORDERS` | 항상 `false` | `true`이면 `load_settings()` 거부 |
+| `KILL_SWITCH_ENGAGED` | 주문 kill switch | `true`이면 RiskEngine/KIS pre-flight 거부 |
+
+### 주문 흐름 안전 가드와 내부 모델 (mvp-009)
+
+`KisBroker.place_order` / `cancel_order` / `replace_order` 호출 시 다음 pre-flight 가드를 통과해야 합니다(`validate_kis_order_request`):
+
+- `trading_mode == paper`
+- `live_trading_enabled is False`
+- `allow_market_orders is False`
+- `kis_env == "paper"`
+- `kill_switch_engaged is False`
+- `order_type in (LIMIT, STOP_LIMIT)`
+- `quantity > 0`
+- `limit_price > 0`
+
+가드 실패 시 `KisOrderRejectedError(reason)`로 즉시 거절합니다. 메시지에는 사유 코드만 들어가며 raw credentials/계좌번호는 포함되지 않습니다.
+
+가드를 통과하더라도 KIS HTTP 전송은 본 단계에서 구현되지 않습니다. 다음 메서드는 항상 `NotImplementedError`로 fail-closed 합니다: `place_order`, `cancel_order`, `replace_order`, `get_open_orders`, `get_fills`, `get_order_status`.
+
+`KisOrderRequest`는 내부 도메인 변환 모델로, KIS HTTP payload로 직렬화되지 않고 단위 테스트 및 향후 mvp 연결 시 입력 모델로만 사용됩니다. 계좌번호는 `account_no_masked`로만 보유합니다.
+
+`kill_switch_engaged=true`로 설정하면 RiskEngine이 모든 주문을 즉시 거절하고, KIS pre-flight도 동일하게 거절합니다. `.env`의 `KILL_SWITCH_ENGAGED=true`로 활성화할 수 있습니다.
+
+`KisOrderRequest`는 `symbol`, `market`, `side`, `quantity`, `order_type`, `limit_price`, `extended_hours`,
+`account_no_masked`, `broker_environment`, `idempotency_key`를 보유합니다. `idempotency_key`는
+`kis-paper-{oms_id}` 형식으로 결정적으로 생성되며, raw 계좌번호는 포함하지 않습니다.
+
+`KisOrderResponse`는 향후 KIS 응답을 내부 모델로 보관하기 위한 구조입니다. `raw_response_sanitized`는
+`sanitize_kis_response()`를 통과한 dict만 저장해야 하며, app key/secret/account/access token으로 보이는
+키 또는 값은 `<redacted>`로 치환됩니다.
+
+`KisBroker.capabilities()`는 현재 모든 주문 관련 기능을 `false`로 반환합니다. 공식 KIS 모의투자 주문 문서로
+endpoint/TR ID/payload를 확인하기 전까지 submission/cancel/replace/open_orders/fills/order_status는 모두
+사용 불가 상태이며 fail-closed입니다.
+
+`/paper/status`는 `kis_order_entry_ready`, `kis_order_entry_mode`(`disabled | paper_guarded | not_implemented`),
+`kis_order_methods_fail_closed`, `kill_switch_engaged`와 함께 `kis_order_submission_available`,
+`kis_cancel_available`, `kis_replace_available`, `kis_open_orders_available`, `kis_fills_available`를 노출합니다.
+현 단계에서 가용성 필드는 모두 `false`입니다.
 
 `.env`는 Git에 올라가지 않습니다(루트 `.gitignore` + 프로젝트 `.gitignore` 양쪽에서 ignore). `.env.example`은 placeholder만 보관합니다.
 
diff --git a/projects/paper-trading/app/api/routes.py b/projects/paper-trading/app/api/routes.py
index b9a7edf..8aca423 100644
--- a/projects/paper-trading/app/api/routes.py
+++ b/projects/paper-trading/app/api/routes.py
@@ -28,6 +28,8 @@ def healthz() -> dict[str, bool]:
 def paper_status(request: Request) -> dict[str, Any]:
     settings = request.app.state.settings
     broker = request.app.state.broker
+    session_router = getattr(request.app.state, "session_router", None)
+    portfolio = getattr(request.app.state, "portfolio", None)
     kis_broker = getattr(request.app.state, "kis_broker", None)
     kis_loaded = bool(
         settings.kis_env
@@ -37,6 +39,31 @@ def paper_status(request: Request) -> dict[str, Any]:
     )
     kis_health = kis_broker.healthcheck() if kis_broker else {}
     market_health = kis_health.get("market_data", {})
+    kis_order_entry_mode = "disabled"
+    if kis_broker is not None:
+        settings_safe = (
+            settings.trading_mode.value == "paper"
+            and settings.live_trading_enabled is False
+            and settings.allow_market_orders is False
+            and settings.kis_env == "paper"
+            and settings.kill_switch_engaged is False
+        )
+        kis_order_entry_mode = "not_implemented" if settings_safe else "disabled"
+    kis_order_entry_ready = kis_broker is not None and kis_order_entry_mode != "disabled"
+    capabilities = (
+        kis_broker.capabilities()
+        if kis_broker
+        else {
+            "submission": False,
+            "cancel": False,
+            "replace": False,
+            "open_orders": False,
+            "fills": False,
+            "order_status": False,
+        }
+    )
+    session_policy = session_router.policy_for_us() if session_router is not None else None
+    portfolio_snapshot = portfolio.get_snapshot() if portfolio is not None else None
     return {
         "ok": True,
         "mode": settings.trading_mode.value,
@@ -63,6 +90,26 @@ def paper_status(request: Request) -> dict[str, Any]:
         "account_no_masked": kis_broker.account.masked_account_no() if kis_broker else "<unset>",
         "secret_exposed": False,
         "configured_brokers": list(getattr(request.app.state, "configured_brokers", [])),
+        "kis_order_entry_ready": kis_order_entry_ready,
+        "kis_order_entry_mode": kis_order_entry_mode,
+        "kis_order_methods_fail_closed": True,
+        "kill_switch_engaged": bool(settings.kill_switch_engaged),
+        "kis_order_submission_available": bool(capabilities.get("submission", False)),
+        "kis_cancel_available": bool(capabilities.get("cancel", False)),
+        "kis_replace_available": bool(capabilities.get("replace", False)),
+        "kis_open_orders_available": bool(capabilities.get("open_orders", False)),
+        "kis_fills_available": bool(capabilities.get("fills", False)),
+        "session": {
+            "market": "US",
+            "current": session_policy.session.value if session_policy else None,
+            "orders_allowed": bool(session_policy.orders_allowed) if session_policy else False,
+            "allowed_strategies": list(session_policy.allowed_strategies) if session_policy else [],
+        },
+        "portfolio": {
+            "positions_count": len(portfolio_snapshot.positions) if portfolio_snapshot else 0,
+            "market_value": str(portfolio_snapshot.market_value) if portfolio_snapshot else "0",
+            "realized_pnl": str(portfolio_snapshot.realized_pnl) if portfolio_snapshot else "0",
+        },
     }
 
 
diff --git a/projects/paper-trading/app/api/server.py b/projects/paper-trading/app/api/server.py
index ba4b9cd..0d4c629 100644
--- a/projects/paper-trading/app/api/server.py
+++ b/projects/paper-trading/app/api/server.py
@@ -6,8 +6,10 @@ from app.api.routes import router
 from app.broker.paper import PaperBroker
 from app.config import load_settings
 from app.oms.manager import OMS
+from app.portfolio import PortfolioService
 from app.risk.engine import RiskEngine
 from app.runtime.paper_runner import PaperRunner
+from app.session import SessionRouter
 from app.strategy import create_strategy
 
 
@@ -19,6 +21,8 @@ def create_app() -> FastAPI:
         broker = PaperBroker()
         oms = OMS(settings, risk, broker)
         strategy = create_strategy("premarket_gap_volume_breakout", settings)
+        session_router = SessionRouter()
+        portfolio = PortfolioService()
 
         # Probe optional brokers — record which ones are instantiable given
         # current .env. The KIS adapter is never wired into OMS in this phase;
@@ -38,6 +42,8 @@ def create_app() -> FastAPI:
         app.state.oms = oms
         app.state.strategy = strategy
         app.state.runner = PaperRunner(settings, strategy, oms)
+        app.state.session_router = session_router
+        app.state.portfolio = portfolio
         app.state.configured_brokers = configured_brokers
         app.state.kis_broker = kis_broker
         yield
diff --git a/projects/paper-trading/app/broker/kis.py b/projects/paper-trading/app/broker/kis.py
index e345d65..69265c8 100644
--- a/projects/paper-trading/app/broker/kis.py
+++ b/projects/paper-trading/app/broker/kis.py
@@ -6,11 +6,13 @@ not implemented until endpoints, TR IDs, payloads, and response shapes are
 confirmed from official KIS Open API documentation.
 """
 
+from dataclasses import dataclass
 from datetime import datetime, timezone
+from decimal import Decimal
 from typing import Any
 
 from app.config import Settings
-from app.domain.enums import TradingMode
+from app.domain.enums import OrderType, Side, TradingMode
 from app.domain.orders import BrokerOrder, OrderAck
 
 
@@ -30,6 +32,118 @@ class KisDataUnavailableError(KisError):
     """Market data unavailable or stale."""
 
 
+class KisOrderRejectedError(KisError):
+    """Order rejected by KIS adapter pre-flight guard."""
+
+    def __init__(self, reason: str) -> None:
+        super().__init__(f"KIS order rejected: {reason}")
+        self.reason = reason
+
+
+@dataclass(frozen=True)
+class KisOrderRequest:
+    """Internal KIS order request model with no raw account number."""
+
+    symbol: str
+    market: str
+    side: Side
+    quantity: int
+    order_type: OrderType
+    limit_price: Decimal
+    extended_hours: bool
+    account_no_masked: str
+    broker_environment: str
+    idempotency_key: str
+
+
+@dataclass(frozen=True)
+class KisOrderResponse:
+    """Internal KIS order response model with sanitized raw broker response."""
+
+    internal_order_id: str
+    broker_order_id: str | None
+    broker: str
+    status: str
+    submitted_at: datetime
+    symbol: str
+    side: Side
+    quantity: int
+    limit_price: Decimal
+    raw_response_sanitized: dict[str, Any]
+
+
+SENSITIVE_RESPONSE_KEYS = {
+    "app_key",
+    "appkey",
+    "appsecret",
+    "app_secret",
+    "account_no",
+    "accountno",
+    "cano",
+    "acct_no",
+    "access_token",
+    "accesstoken",
+    "authorization",
+    "tr_key",
+    "trkey",
+    "secret",
+}
+
+
+def sanitize_kis_response(raw: dict[str, Any] | None, settings: Settings) -> dict[str, Any]:
+    """Return a copy of a KIS response with credentials/account values redacted."""
+    if not isinstance(raw, dict):
+        return {}
+
+    sensitive_values = {
+        value
+        for value in (settings.kis_app_key, settings.kis_app_secret, settings.kis_account_no)
+        if value
+    }
+
+    def sanitize_value(value: Any) -> Any:
+        if isinstance(value, dict):
+            return {key: sanitize_field(key, nested) for key, nested in value.items()}
+        if isinstance(value, list):
+            return [sanitize_value(item) for item in value]
+        if isinstance(value, str) and value in sensitive_values:
+            return "<redacted>"
+        return value
+
+    def sanitize_field(key: str, value: Any) -> Any:
+        normalized = key.replace("-", "_").lower()
+        if normalized in SENSITIVE_RESPONSE_KEYS:
+            return "<redacted>"
+        return sanitize_value(value)
+
+    return {key: sanitize_field(key, value) for key, value in raw.items()}
+
+
+def validate_kis_order_request(settings: Settings, broker_order: BrokerOrder) -> None:
+    """Pre-flight guards for KIS order paths."""
+    if settings.trading_mode != TradingMode.PAPER:
+        raise KisOrderRejectedError("trading_mode_not_paper")
+    if settings.live_trading_enabled:
+        raise KisOrderRejectedError("live_trading_enabled")
+    if settings.allow_market_orders:
+        raise KisOrderRejectedError("market_orders_allowed_flag_set")
+    if settings.kis_env != "paper":
+        raise KisOrderRejectedError("kis_env_not_paper")
+    if settings.kill_switch_engaged:
+        raise KisOrderRejectedError("kill_switch_engaged")
+    if broker_order.order_type not in (OrderType.LIMIT, OrderType.STOP_LIMIT):
+        raise KisOrderRejectedError("order_type_not_limit")
+    if broker_order.quantity is None or broker_order.quantity <= 0:
+        raise KisOrderRejectedError("quantity_invalid")
+    if broker_order.limit_price is None or broker_order.limit_price <= 0:
+        raise KisOrderRejectedError("limit_price_invalid")
+    if broker_order.quote_timestamp is None:
+        raise KisOrderRejectedError("stale_quote")
+    quote_age = (broker_order.submitted_at - broker_order.quote_timestamp).total_seconds()
+    if quote_age > settings.premarket_max_quote_age_seconds:
+        raise KisOrderRejectedError("stale_quote")
+
+
 class KisAuthClient:
     """KIS authentication token lifecycle state machine.
 
@@ -235,16 +349,71 @@ class KisBroker:
         )
 
     def place_order(self, broker_order: BrokerOrder) -> OrderAck:
+        validate_kis_order_request(self._settings, broker_order)
+        self._to_kis_request(broker_order)
         raise NotImplementedError(
-            "KIS place_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard."
+            "KIS place_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard. "
+            "Pre-flight passed but HTTP transmission is intentionally not implemented until KIS Open API "
+            "endpoints/TR IDs/payloads are confirmed from official documentation."
         )
 
     def cancel_order(self, broker_order_id: str) -> None:
+        if self._settings.trading_mode != TradingMode.PAPER:
+            raise KisOrderRejectedError("trading_mode_not_paper")
+        if self._settings.live_trading_enabled:
+            raise KisOrderRejectedError("live_trading_enabled")
+        if self._settings.allow_market_orders:
+            raise KisOrderRejectedError("market_orders_allowed_flag_set")
+        if self._settings.kis_env != "paper":
+            raise KisOrderRejectedError("kis_env_not_paper")
+        if self._settings.kill_switch_engaged:
+            raise KisOrderRejectedError("kill_switch_engaged")
         raise NotImplementedError("KIS cancel_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard.")
 
     def replace_order(self, broker_order_id: str, broker_order: BrokerOrder) -> OrderAck:
+        validate_kis_order_request(self._settings, broker_order)
+        self._to_kis_request(broker_order)
         raise NotImplementedError("KIS replace_order(): TODO — DO NOT WIRE without OMS-only execution + RiskEngine guard.")
 
+    def get_fills(self) -> list[OrderAck]:
+        raise NotImplementedError(
+            "KIS get_fills(): TODO — confirm fills endpoint, TR ID, payload, and response shape "
+            "from KIS Open API official documentation. Do not invent endpoints."
+        )
+
+    def get_order_status(self, broker_order_id: str) -> dict[str, Any]:
+        raise NotImplementedError(
+            "KIS get_order_status(): TODO — confirm order status endpoint, TR ID, payload, and response shape "
+            "from KIS Open API official documentation. Do not invent endpoints."
+        )
+
+    def capabilities(self) -> dict[str, bool]:
+        return {
+            "submission": False,
+            "cancel": False,
+            "replace": False,
+            "open_orders": False,
+            "fills": False,
+            "order_status": False,
+        }
+
+    def _idempotency_key_for(self, broker_order: BrokerOrder) -> str:
+        return f"kis-paper-{broker_order.oms_id}"
+
+    def _to_kis_request(self, broker_order: BrokerOrder) -> KisOrderRequest:
+        return KisOrderRequest(
+            symbol=broker_order.symbol,
+            market="US",
+            side=broker_order.side,
+            quantity=broker_order.quantity,
+            order_type=broker_order.order_type,
+            limit_price=broker_order.limit_price,
+            extended_hours=False,
+            account_no_masked=self._account.masked_account_no(),
+            broker_environment=self._settings.kis_env or "paper",
+            idempotency_key=self._idempotency_key_for(broker_order),
+        )
+
     def healthcheck(self) -> dict[str, Any]:
         market = self._market_data.healthcheck_market_data()
         return {
@@ -256,6 +425,8 @@ class KisBroker:
             "market_data": market,
             "last_error": self._last_error,
             "order_execution_implemented": False,
+            "order_methods_fail_closed": True,
+            "capabilities": self.capabilities(),
         }
 
     def submit(self, broker_order: BrokerOrder) -> OrderAck:
diff --git a/projects/paper-trading/app/config.py b/projects/paper-trading/app/config.py
index 2187701..e7fa0e7 100644
--- a/projects/paper-trading/app/config.py
+++ b/projects/paper-trading/app/config.py
@@ -33,6 +33,7 @@ class Settings:
     kis_app_key: str | None = field(default=None, repr=False)
     kis_app_secret: str | None = field(default=None, repr=False)
     allow_market_orders: bool = False
+    kill_switch_engaged: bool = False
 
 
 def _decimal_env(name: str, default: Decimal) -> Decimal:
@@ -112,4 +113,5 @@ def load_settings() -> Settings:
         kis_app_key=_str_env("KIS_APP_KEY"),
         kis_app_secret=_str_env("KIS_APP_SECRET"),
         allow_market_orders=False,
+        kill_switch_engaged=_bool_env("KILL_SWITCH_ENGAGED", False),
     )
diff --git a/projects/paper-trading/app/domain/orders.py b/projects/paper-trading/app/domain/orders.py
index f5ffb31..b43de91 100644
--- a/projects/paper-trading/app/domain/orders.py
+++ b/projects/paper-trading/app/domain/orders.py
@@ -14,6 +14,7 @@ class OrderIntent:
     limit_price: Decimal
     stop_price: Decimal | None = None
     client_tag: str | None = None
+    quote_timestamp: datetime | None = None
 
     def __post_init__(self) -> None:
         if self.symbol != self.symbol.upper():
@@ -50,6 +51,7 @@ class BrokerOrder:
     submitted_at: datetime
     stop_price: Decimal | None = None
     client_tag: str | None = None
+    quote_timestamp: datetime | None = None
 
 
 @dataclass(frozen=True)
diff --git a/projects/paper-trading/app/oms/manager.py b/projects/paper-trading/app/oms/manager.py
index ea90f13..e50ea02 100644
--- a/projects/paper-trading/app/oms/manager.py
+++ b/projects/paper-trading/app/oms/manager.py
@@ -46,5 +46,6 @@ class OMS:
             submitted_at=now,
             stop_price=order.stop_price,
             client_tag=order.client_tag,
+            quote_timestamp=intent.quote_timestamp,
         )
         return self._broker.submit(broker_order)
diff --git a/projects/paper-trading/app/risk/engine.py b/projects/paper-trading/app/risk/engine.py
index 444d650..5293d91 100644
--- a/projects/paper-trading/app/risk/engine.py
+++ b/projects/paper-trading/app/risk/engine.py
@@ -18,6 +18,8 @@ class RiskEngine:
         self._settings = settings
 
     def evaluate(self, intent: OrderIntent) -> RiskDecision:
+        if self._settings.kill_switch_engaged:
+            return RiskDecision(False, "kill_switch_engaged")
         if self._settings.trading_mode != TradingMode.PAPER:
             return RiskDecision(False, "paper_trading_required")
         if self._settings.live_trading_enabled:
diff --git a/projects/paper-trading/app/strategy/premarket_gap.py b/projects/paper-trading/app/strategy/premarket_gap.py
index 69daad3..4ea817d 100644
--- a/projects/paper-trading/app/strategy/premarket_gap.py
+++ b/projects/paper-trading/app/strategy/premarket_gap.py
@@ -81,6 +81,7 @@ class PremarketGapVolumeBreakoutStrategy(Strategy):
             order_type=OrderType.LIMIT,
             limit_price=limit_price,
             client_tag=self.name,
+            quote_timestamp=snapshot.timestamp,
         )
         return StrategyResult(
             symbol=snapshot.symbol,
diff --git a/projects/paper-trading/tests/test_api_paper_status.py b/projects/paper-trading/tests/test_api_paper_status.py
index 79333c9..cb4000c 100644
--- a/projects/paper-trading/tests/test_api_paper_status.py
+++ b/projects/paper-trading/tests/test_api_paper_status.py
@@ -8,6 +8,7 @@ KIS_ENV_KEYS = (
     "KIS_ACCOUNT_NO",
     "KIS_APP_KEY",
     "KIS_APP_SECRET",
+    "KILL_SWITCH_ENGAGED",
 )
 
 
@@ -53,6 +54,15 @@ def test_paper_status_kis_metadata_fields(monkeypatch):
     assert body["secret_exposed"] is False
     assert "kis_" + "secret_exposed" not in body
     assert isinstance(body["configured_brokers"], list)
+    assert body["kis_order_entry_ready"] is False
+    assert body["kis_order_entry_mode"] == "disabled"
+    assert body["kis_order_methods_fail_closed"] is True
+    assert body["kill_switch_engaged"] is False
+    assert body["kis_order_submission_available"] is False
+    assert body["kis_cancel_available"] is False
+    assert body["kis_replace_available"] is False
+    assert body["kis_open_orders_available"] is False
+    assert body["kis_fills_available"] is False
     # Credentials must never appear in the response body.
     body_text = response.text
     for needle in ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_NO"):
@@ -67,6 +77,7 @@ def test_paper_status_with_kis_config_masks_account(monkeypatch):
     monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")
     monkeypatch.setenv("KIS_APP_KEY", "fake-key")
     monkeypatch.setenv("KIS_APP_SECRET", "fake-secret")
+    monkeypatch.setenv("KILL_SWITCH_ENGAGED", "false")
 
     with TestClient(create_app()) as client:
         response = client.get("/paper/status")
@@ -81,6 +92,15 @@ def test_paper_status_with_kis_config_masks_account(monkeypatch):
     assert body["last_broker_error"] is None
     assert body["account_no_masked"] == "***5678"
     assert body["secret_exposed"] is False
+    assert body["kis_order_entry_ready"] is True
+    assert body["kis_order_entry_mode"] == "not_implemented"
+    assert body["kis_order_methods_fail_closed"] is True
+    assert body["kill_switch_engaged"] is False
+    assert body["kis_order_submission_available"] is False
+    assert body["kis_cancel_available"] is False
+    assert body["kis_replace_available"] is False
+    assert body["kis_open_orders_available"] is False
+    assert body["kis_fills_available"] is False
 
     body_text = response.text
     for needle in ("12345678", "fake-key", "fake-secret", "KIS_APP_KEY", "KIS_APP_SECRET"):
diff --git a/projects/paper-trading/tests/test_broker_interface.py b/projects/paper-trading/tests/test_broker_interface.py
index 2768d4d..09b857f 100644
--- a/projects/paper-trading/tests/test_broker_interface.py
+++ b/projects/paper-trading/tests/test_broker_interface.py
@@ -4,8 +4,19 @@ from dataclasses import replace
 
 import pytest
 
-from app.broker.kis import KisAccountClient, KisAuthClient, KisBroker, KisMarketDataClient
+from datetime import datetime, timezone
+from decimal import Decimal
+
+from app.broker.kis import (
+    KisAccountClient,
+    KisAuthClient,
+    KisBroker,
+    KisMarketDataClient,
+    KisOrderRejectedError,
+)
 from app.domain.enums import TradingMode
+from app.domain.enums import OrderType, Side
+from app.domain.orders import BrokerOrder
 
 
 REQUIRED_METHODS = (
@@ -19,6 +30,7 @@ REQUIRED_METHODS = (
     "place_order",
     "cancel_order",
     "replace_order",
+    "capabilities",
     "healthcheck",
     # BrokerAdapter Protocol compatibility
     "submit",
@@ -38,6 +50,24 @@ def _configured(settings):
     )
 
 
+def _broker_order(**overrides) -> BrokerOrder:
+    now = datetime.now(timezone.utc)
+    data = {
+        "symbol": "AAPL",
+        "side": Side.BUY,
+        "quantity": 10,
+        "order_type": OrderType.LIMIT,
+        "limit_price": Decimal("100"),
+        "risk_token": "rt",
+        "created_at": now,
+        "oms_id": "oms-1",
+        "submitted_at": now,
+        "quote_timestamp": now,
+    }
+    data.update(overrides)
+    return BrokerOrder(**data)
+
+
 def test_kis_broker_has_all_required_methods(settings):
     broker = KisBroker(_configured(settings))
     for name in REQUIRED_METHODS:
@@ -78,18 +108,20 @@ def test_kis_broker_missing_credentials_fails_closed(settings, missing):
 
 def test_kis_place_cancel_replace_not_implemented(settings):
     broker = KisBroker(_configured(settings))
+    with pytest.raises(KisOrderRejectedError):
+        broker.place_order(_broker_order(quantity=0))
     with pytest.raises(NotImplementedError):
-        broker.place_order(None)  # type: ignore[arg-type]
+        broker.place_order(_broker_order())
     with pytest.raises(NotImplementedError):
         broker.cancel_order("x")
     with pytest.raises(NotImplementedError):
-        broker.replace_order("x", None)  # type: ignore[arg-type]
+        broker.replace_order("x", _broker_order())
 
 
 def test_kis_protocol_methods_delegate_to_not_implemented(settings):
     broker = KisBroker(_configured(settings))
     with pytest.raises(NotImplementedError):
-        broker.submit(None)  # type: ignore[arg-type]
+        broker.submit(_broker_order())
     with pytest.raises(NotImplementedError):
         broker.cancel("x")
     with pytest.raises(NotImplementedError):
@@ -112,6 +144,44 @@ def test_kis_data_methods_not_implemented(settings):
             getattr(broker, method)(*args)
 
 
+def test_kis_broker_has_get_fills_and_get_order_status(settings):
+    broker = KisBroker(_configured(settings))
+    assert callable(broker.get_fills)
+    assert callable(broker.get_order_status)
+    with pytest.raises(NotImplementedError, match="TODO"):
+        broker.get_fills()
+    with pytest.raises(NotImplementedError, match="TODO"):
+        broker.get_order_status("oms-1")
+
+
+def test_kis_order_request_class_is_exported():
+    from app.broker.kis import (
+        KisOrderRejectedError,
+        KisOrderRequest,
+        KisOrderResponse,
+        sanitize_kis_response,
+        validate_kis_order_request,
+    )
+
+    assert KisOrderRequest is not None
+    assert KisOrderResponse is not None
+    assert KisOrderRejectedError is not None
+    assert callable(sanitize_kis_response)
+    assert callable(validate_kis_order_request)
+
+
+def test_kis_broker_capabilities_are_exported_and_fail_closed(settings):
+    broker = KisBroker(_configured(settings))
+    assert broker.capabilities() == {
+        "submission": False,
+        "cancel": False,
+        "replace": False,
+        "open_orders": False,
+        "fills": False,
+        "order_status": False,
+    }
+
+
 def test_kis_healthcheck_returns_disconnected_dict(settings):
     broker = KisBroker(_configured(settings))
     h = broker.healthcheck()
@@ -122,6 +192,9 @@ def test_kis_healthcheck_returns_disconnected_dict(settings):
     assert h["account_loaded"] is False
     assert h["last_error"] is None
     assert h["order_execution_implemented"] is False
+    assert h["order_methods_fail_closed"] is True
+    assert h["capabilities"]["submission"] is False
+    assert h["capabilities"]["fills"] is False
     assert h["market_data"]["connected"] is False
     reason = h["market_data"]["reason"].lower()
     assert "skeleton" in reason or "not implemented" in reason
diff --git a/projects/paper-trading/tests/test_risk_engine.py b/projects/paper-trading/tests/test_risk_engine.py
index 16d598e..3854adc 100644
--- a/projects/paper-trading/tests/test_risk_engine.py
+++ b/projects/paper-trading/tests/test_risk_engine.py
@@ -27,6 +27,18 @@ def test_risk_rejects_live_enabled(settings):
     assert not decision.approved
 
 
+def test_risk_engine_kill_switch_at_top(settings):
+    bad = replace(
+        settings,
+        kill_switch_engaged=True,
+        trading_mode=TradingMode.LIVE,
+        live_trading_enabled=True,
+    )
+    decision = RiskEngine(bad).evaluate(intent())
+    assert decision.approved is False
+    assert decision.reason == "kill_switch_engaged"
+
+
 def test_risk_rejects_allowlist(settings):
     decision = RiskEngine(settings).evaluate(intent(symbol="TSLA"))
     assert decision.reason == "symbol_not_allowed"
diff --git a/projects/paper-trading/tests/test_strategy_premarket_gap.py b/projects/paper-trading/tests/test_strategy_premarket_gap.py
index 37540c2..a7f481d 100644
--- a/projects/paper-trading/tests/test_strategy_premarket_gap.py
+++ b/projects/paper-trading/tests/test_strategy_premarket_gap.py
@@ -49,10 +49,12 @@ def test_stale_quote_blocked(settings, make_snapshot):
 
 
 def test_strategy_result_is_not_executable_order(settings, make_snapshot):
-    result = PremarketGapVolumeBreakoutStrategy(settings).evaluate(make_snapshot())
+    snapshot = make_snapshot()
+    result = PremarketGapVolumeBreakoutStrategy(settings).evaluate(snapshot)
     assert isinstance(result.non_executable_order_intent, OrderIntent)
     assert not isinstance(result.non_executable_order_intent, BrokerOrder)
     assert not isinstance(result.non_executable_order_intent, Order)
+    assert result.non_executable_order_intent.quote_timestamp == snapshot.timestamp
 
 
 def test_no_market_order_generated(settings, make_snapshot):
diff --git a/web/public/app.js b/web/public/app.js
index f27f460..d9fc2c2 100644
--- a/web/public/app.js
+++ b/web/public/app.js
@@ -9,6 +9,7 @@ const inputKoEl = document.querySelector('#inputKo');
 const outputEl = document.querySelector('#output');
 const artifactListEl = document.querySelector('#artifactList');
 const runPipelineButton = document.querySelector('#runPipeline');
+const sendButtons = [...document.querySelectorAll('[data-send]')];
 const pipelineStateEl = document.querySelector('#pipelineState');
 const pipelineJobIdEl = document.querySelector('#pipelineJobId');
 const pipelineStageEl = document.querySelector('#pipelineStage');
@@ -31,6 +32,15 @@ const approvalModalEl = document.querySelector('#approvalModal');
 const approvalModalStepEl = document.querySelector('#approvalModalStep');
 const approvalModalWindowEl = document.querySelector('#approvalModalWindow');
 const approvalModalSummaryEl = document.querySelector('#approvalModalSummary');
+const approvalModalTypeEl = document.querySelector('#approvalModalType');
+const approvalModalCommandEl = document.querySelector('#approvalModalCommand');
+const approvalModalCwdEl = document.querySelector('#approvalModalCwd');
+const approvalModalRiskEl = document.querySelector('#approvalModalRisk');
+const approvalModalRecommendationEl = document.querySelector('#approvalModalRecommendation');
+const approvalModalRawEl = document.querySelector('#approvalModalRaw');
+const approvalModalRiskWarningEl = document.querySelector('#approvalModalRiskWarning');
+const approvalModalApproveOnceEl = document.querySelector('#approvalModalApproveOnce');
+const approvalModalApproveSessionEl = document.querySelector('#approvalModalApproveSession');
 const aiControlButtons = [
   document.querySelector('#approveOnce'),
   document.querySelector('#approveSession'),
@@ -59,8 +69,18 @@ const finalPipelineStates = new Set([
   'failed',
   'blocked',
   'manual_review_required',
+  'review_approved',
+  'review_changes_requested',
+  'manual_final_approval_required',
   'idle'
 ]);
+const stageWindows = {
+  'claude-plan': 'claude',
+  'codex-implement': 'codex',
+  'claude-review': 'claude',
+  'codex-review-fix': 'codex',
+  'claude-re-review': 'claude'
+};
 
 projectDirEl.value = state.projectDir;
 jobIdEl.value = state.jobId;
@@ -183,6 +203,10 @@ runPipelineButton.addEventListener('click', async () => {
 });
 
 document.querySelector('#pipelineStatus').addEventListener('click', refreshPipelineStatus);
+document.querySelector('#finalManualReview').addEventListener('click', () => {
+  writeOutput('최종 확인', 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.');
+  refreshPipelineStatus();
+});
 
 document.querySelector('#resetPipeline').addEventListener('click', async () => {
   const result = await runAction('파이프라인 상태 초기화', () => requestJson('/api/pipeline/reset', {
@@ -370,6 +394,7 @@ function renderPipelineStatus(status) {
     summaryDiffEl.textContent = '-';
     summaryReviewEl.textContent = '-';
     runPipelineButton.disabled = false;
+    updateSendButtonGates(null);
     return;
   }
 
@@ -389,6 +414,7 @@ function renderPipelineStatus(status) {
   pipelineTargetWindowEl.textContent = pipeline.targetWindow || '-';
   pipelineWaitingApprovalEl.textContent = pipeline.waitingApproval ? '예' : '아니오';
   renderDetectedIssue(approvalRequest ? null : pipeline.detectedIssue);
+  updateSendButtonGates(pipeline);
 
   if (pipeline.targetWindow && tmuxWindowEl.value !== pipeline.targetWindow) {
     tmuxWindowEl.value = pipeline.targetWindow;
@@ -410,8 +436,9 @@ function renderPipelineStatus(status) {
   } else {
     currentApprovalRequest = null;
     closeApprovalModal();
-    pipelineGuidanceEl.hidden = true;
-    pipelineGuidanceEl.textContent = '';
+    const requirementsText = renderRequirementsText(pipeline.requirements);
+    pipelineGuidanceEl.hidden = !requirementsText;
+    pipelineGuidanceEl.textContent = requirementsText;
     approvalInlinePromptEl.hidden = true;
   }
 
@@ -464,6 +491,47 @@ function renderPipelineStatus(status) {
   summaryNextActionEl.textContent = pipeline.nextAction || '-';
 }
 
+function renderRequirementsText(requirements) {
+  if (!requirements || !requirements.files || requirements.files.length === 0) {
+    return '';
+  }
+  const lines = [
+    `필수 파일 (${requirements.label || '현재 단계'}):`,
+    ...requirements.files.map((file) => `- ${file.name}: ${file.exists ? 'ready' : 'missing'}`),
+    `다음 단계 가능: ${requirements.nextStageAllowed ? 'yes' : 'no'}`
+  ];
+  return lines.join('\n');
+}
+
+function hasArtifact(pipeline, name) {
+  return (pipeline?.artifacts || []).some((artifact) => (artifact.name || artifact) === name);
+}
+
+function updateSendButtonGates(pipeline) {
+  sendButtons.forEach((button) => {
+    const target = button.dataset.send;
+    let disabled = false;
+    let title = '';
+    if (!pipeline) {
+      disabled = false;
+    } else if (target === 'codex-implement') {
+      disabled = !hasArtifact(pipeline, 'plan.md') || !hasArtifact(pipeline, 'codex-task.md');
+      title = disabled ? 'Claude 계획이 아직 완료되지 않았습니다. plan.md와 codex-task.md가 생성된 뒤 Codex를 실행할 수 있습니다.' : '';
+    } else if (target === 'claude-review') {
+      disabled = !hasArtifact(pipeline, 'patch.md');
+      title = disabled ? 'patch.md가 생성된 뒤 Claude 리뷰를 실행할 수 있습니다.' : '';
+    } else if (target === 'codex-review-fix') {
+      disabled = pipeline.state !== 'review_changes_requested';
+      title = disabled ? 'Claude가 수정 요청을 남긴 뒤 실행할 수 있습니다.' : '';
+    } else if (target === 'claude-re-review') {
+      disabled = !hasArtifact(pipeline, 'status.md');
+      title = disabled ? 'Codex 리뷰 반영 후 status.md가 생성된 뒤 실행할 수 있습니다.' : '';
+    }
+    button.disabled = disabled;
+    button.title = title;
+  });
+}
+
 function getApprovalRequest(status, pipeline) {
   const issue = pipeline.detectedIssue || {};
   const isApproval = pipeline.state === 'approval_required' || issue.type === 'approval_required';
@@ -472,16 +540,18 @@ function getApprovalRequest(status, pipeline) {
   }
 
   const targetWindow = issue.window || pipeline.targetWindow;
-  if (!['claude', 'codex'].includes(targetWindow)) {
+  const stageTargetWindow = stageWindows[pipeline.step] || pipeline.targetWindow || targetWindow;
+  if (!['claude', 'codex'].includes(stageTargetWindow)) {
     return null;
   }
 
   const jobId = status.jobId || jobIdEl.value.trim() || '-';
   const step = pipeline.step || '-';
-  const rawSummary = issue.summary || pipeline.message || '';
-  const summary = cleanApprovalSummary(targetWindow);
-  const key = `${jobId}:${step}:${targetWindow}:${rawSummary || summary}`;
-  return { key, step, targetWindow, summary };
+  const approvalContext = issue.approvalContext || null;
+  const rawSummary = approvalContext?.rawBlock || issue.summary || pipeline.message || '';
+  const summary = approvalContext?.summary || cleanApprovalSummary(stageTargetWindow);
+  const key = `${jobId}:${step}:${stageTargetWindow}:${rawSummary || summary}`;
+  return { key, step, targetWindow: stageTargetWindow, summary, approvalContext };
 }
 
 function cleanApprovalSummary(windowName) {
@@ -495,10 +565,41 @@ function openApprovalModal(request, force) {
     return;
   }
   lastApprovalKey = request.key;
-  approvalModalStepEl.textContent = request.step || '-';
-  approvalModalWindowEl.textContent = request.targetWindow || '-';
-  approvalModalSummaryEl.textContent = request.summary || '-';
+  renderApprovalContext(request, request.approvalContext);
   approvalModalEl.hidden = false;
+  if (!request.approvalContext) {
+    loadApprovalContext(request);
+  }
+}
+
+async function loadApprovalContext(request) {
+  try {
+    const result = await requestJson(`/api/tmux/approval-context?window=${encodeURIComponent(request.targetWindow)}&step=${encodeURIComponent(request.step || '')}`);
+    if (!currentApprovalRequest || currentApprovalRequest.key !== request.key) {
+      return;
+    }
+    currentApprovalRequest.approvalContext = result.approvalContext;
+    renderApprovalContext(currentApprovalRequest, result.approvalContext);
+  } catch (error) {
+    approvalModalRawEl.textContent = error.message;
+  }
+}
+
+function renderApprovalContext(request, context) {
+  const risk = context?.risk || 'unknown';
+  approvalModalStepEl.textContent = request.step || context?.step || '-';
+  approvalModalWindowEl.textContent = request.targetWindow || context?.window || '-';
+  approvalModalSummaryEl.textContent = context?.summary || request.summary || '-';
+  approvalModalTypeEl.textContent = context?.type || 'unknown';
+  approvalModalCommandEl.textContent = context?.commandOrTarget || '확인 불가';
+  approvalModalCwdEl.textContent = context?.workingDirectory || '-';
+  approvalModalRiskEl.textContent = risk;
+  approvalModalRiskEl.dataset.risk = risk;
+  approvalModalRecommendationEl.textContent = context?.recommendation || '직접 확인 필요';
+  approvalModalRawEl.textContent = context?.rawBlock || '원문을 불러오는 중입니다.';
+  approvalModalRiskWarningEl.textContent = context?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.';
+  approvalModalApproveOnceEl.disabled = !context?.canApproveOnce;
+  approvalModalApproveSessionEl.disabled = !context?.canApproveSession;
 }
 
 function closeApprovalModal() {
@@ -510,6 +611,10 @@ async function sendApprovalModalAction(endpoint) {
     writeOutput('승인 명령 실패', '승인 대상 창을 확인할 수 없습니다.');
     return;
   }
+  if (!approvalEndpointAllowed(endpoint, currentApprovalRequest.approvalContext)) {
+    writeOutput('승인 명령 차단', currentApprovalRequest.approvalContext?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.');
+    return;
+  }
 
   try {
     await requestJson(endpoint, {
@@ -524,6 +629,16 @@ async function sendApprovalModalAction(endpoint) {
   }
 }
 
+function approvalEndpointAllowed(endpoint, context) {
+  if (endpoint.endsWith('/approve-once')) {
+    return Boolean(context?.canApproveOnce);
+  }
+  if (endpoint.endsWith('/approve-session')) {
+    return Boolean(context?.canApproveSession);
+  }
+  return true;
+}
+
 function normalizePipelineStatus(payload) {
   if (payload && payload.status && typeof payload.status === 'object') {
     return {
@@ -534,6 +649,7 @@ function normalizePipelineStatus(payload) {
       waitingApproval: Boolean(payload.status.waitingApproval),
       detectedIssue: payload.status.detectedIssue || null,
       artifacts: payload.status.artifacts || [],
+      requirements: payload.status.requirements || null,
       gitDiff: payload.status.gitDiff || '-',
       reviewStatus: payload.status.reviewStatus || '-',
       nextAction: payload.status.nextAction || '-'
@@ -548,6 +664,7 @@ function normalizePipelineStatus(payload) {
     waitingApproval: false,
     detectedIssue: null,
     artifacts: payload && payload.artifacts ? payload.artifacts : [],
+    requirements: null,
     gitDiff: '-',
     reviewStatus: '-',
     nextAction: '-'
@@ -625,6 +742,10 @@ async function sendTmuxControl(title, endpoint) {
     writeOutput(`${title} 실패`, 'Manual Shell(git-shell)은 비AI 창입니다. 승인/거절 키 입력은 Claude 또는 Codex 창에서만 사용하세요.');
     return null;
   }
+  if (currentApprovalRequest && currentApprovalRequest.targetWindow === windowName && !approvalEndpointAllowed(endpoint, currentApprovalRequest.approvalContext)) {
+    writeOutput(`${title} 차단`, currentApprovalRequest.approvalContext?.warning || '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.');
+    return null;
+  }
   const result = await runAction(title, () => requestJson(endpoint, {
     method: 'POST',
     body: JSON.stringify({ window: windowName })
diff --git a/web/public/index.html b/web/public/index.html
index a02de7a..60b76f9 100644
--- a/web/public/index.html
+++ b/web/public/index.html
@@ -16,42 +16,55 @@
     </header>
 
     <main class="layout">
-      <section class="panel setup">
-        <h2>작업 설정</h2>
-        <label>
-          프로젝트 경로
-          <input id="projectDir" type="text" autocomplete="off" spellcheck="false">
-        </label>
+      <section class="panel quick-actions">
+        <h2>핵심 실행</h2>
         <label>
           작업 ID
           <input id="jobId" type="text" value="mvp-001" autocomplete="off" spellcheck="false">
         </label>
         <label>
           한국어 작업 요청
-          <textarea id="inputKo" spellcheck="false" rows="14"></textarea>
+          <textarea id="inputKo" spellcheck="false" rows="6"></textarea>
         </label>
         <p class="field-hint">여기에는 한국어 작업 요청만 입력하세요. 쉘 설정 명령, 실행 명령, 토큰, 비밀값은 넣지 않습니다.</p>
-        <div class="role-display" aria-label="역할 안내">
-          <div>
-            <strong>Claude</strong>
-            <span>planning / requirements / review</span>
-          </div>
-          <div>
-            <strong>Codex</strong>
-            <span>implementation / tests / patch summary</span>
-          </div>
-        </div>
-        <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
         <div class="pipeline-runner">
           <button id="runPipeline" class="primary-action" type="button">Claude → Codex → Claude 전체 실행</button>
           <div class="primary-actions">
             <button data-send="claude-plan" type="button">Claude 계획 생성</button>
             <button data-send="codex-implement" type="button">Codex 구현 실행</button>
             <button data-send="claude-review" type="button">Claude 리뷰 실행</button>
+            <button data-send="codex-review-fix" type="button">Codex 리뷰 반영 실행</button>
+            <button data-send="claude-re-review" type="button">Claude 재리뷰 실행</button>
+            <button id="finalManualReview" type="button">최종 확인으로 이동</button>
           </div>
         </div>
       </section>
 
+      <section class="panel control-panel">
+        <h2>승인 / 서비스 제어</h2>
+        <p class="warning-text">승인은 Claude 또는 Codex AI CLI 창에만 키 입력을 보내는 기능입니다. Manual Shell(git-shell)은 사람이 직접 git/test 명령을 실행하는 비AI 창입니다.</p>
+        <label>
+          제어할 tmux 창
+          <select id="tmuxWindow"></select>
+        </label>
+        <div class="actions control-actions">
+          <button id="approveOnce" type="button">승인 / 계속 진행</button>
+          <button id="approveSession" type="button">세션 승인</button>
+          <button id="rejectAction" type="button">거절</button>
+          <button id="interruptAction" type="button">중단</button>
+          <button id="restartAiTeam" type="button">AI팀 재시작</button>
+          <button id="restartGui" type="button">GUI 서버 재시작</button>
+        </div>
+      </section>
+
+      <section class="panel tmux-panel">
+        <div class="panel-head">
+          <h2>실시간 tmux 출력</h2>
+          <button id="refreshTmuxOutput" type="button">출력 새로고침</button>
+        </div>
+        <pre id="tmuxOutput" aria-live="polite"></pre>
+      </section>
+
       <section class="panel pipeline-status">
         <div class="panel-head">
           <h2>파이프라인 상태</h2>
@@ -96,29 +109,42 @@
         <div id="pipelineSteps" class="pipeline-steps"></div>
       </section>
 
-      <section class="panel control-panel">
-        <h2>승인 / 서비스 제어</h2>
-        <p class="warning-text">승인은 Claude 또는 Codex AI CLI 창에만 키 입력을 보내는 기능입니다. Manual Shell(git-shell)은 사람이 직접 git/test 명령을 실행하는 비AI 창입니다.</p>
+      <details class="panel job-settings">
+        <summary>작업 설정</summary>
         <label>
-          제어할 tmux 창
-          <select id="tmuxWindow"></select>
+          프로젝트 경로
+          <input id="projectDir" type="text" autocomplete="off" spellcheck="false">
         </label>
-        <div class="actions control-actions">
-          <button id="approveOnce" type="button">승인 / 계속 진행</button>
-          <button id="approveSession" type="button">세션 승인</button>
-          <button id="rejectAction" type="button">거절</button>
-          <button id="interruptAction" type="button">중단</button>
-          <button id="restartAiTeam" type="button">AI팀 재시작</button>
-          <button id="restartGui" type="button">GUI 서버 재시작</button>
+        <div class="role-display" aria-label="역할 안내">
+          <div>
+            <strong>Claude</strong>
+            <span>planning / requirements / review</span>
+          </div>
+          <div>
+            <strong>Codex</strong>
+            <span>implementation / tests / patch summary</span>
+          </div>
         </div>
-      </section>
+        <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
+      </details>
 
-      <section class="panel tmux-panel">
+      <details class="panel advanced-panel">
+        <summary>고급 제어</summary>
+        <div class="actions">
+          <button id="startTeam" type="button">AI 팀 시작</button>
+          <button id="createJob" type="button">작업 폴더 생성</button>
+          <button id="saveInput" type="button">request.ko.md 저장</button>
+          <button id="gitStatus" type="button">git status</button>
+          <button id="gitDiff" type="button">git diff</button>
+        </div>
+      </details>
+
+      <section class="panel artifacts">
         <div class="panel-head">
-          <h2>실시간 tmux 출력</h2>
-          <button id="refreshTmuxOutput" type="button">출력 새로고침</button>
+          <h2>산출물</h2>
+          <button id="loadArtifacts" type="button">목록 새로고침</button>
         </div>
-        <pre id="tmuxOutput" aria-live="polite"></pre>
+        <div id="artifactList" class="artifact-list"></div>
       </section>
 
       <section class="panel result-summary">
@@ -143,25 +169,6 @@
         </dl>
       </section>
 
-      <details class="panel advanced-panel">
-        <summary>고급 제어</summary>
-        <div class="actions">
-          <button id="startTeam" type="button">AI 팀 시작</button>
-          <button id="createJob" type="button">작업 폴더 생성</button>
-          <button id="saveInput" type="button">request.ko.md 저장</button>
-          <button id="gitStatus" type="button">git status</button>
-          <button id="gitDiff" type="button">git diff</button>
-        </div>
-      </details>
-
-      <section class="panel artifacts">
-        <div class="panel-head">
-          <h2>산출물</h2>
-          <button id="loadArtifacts" type="button">목록 새로고침</button>
-        </div>
-        <div id="artifactList" class="artifact-list"></div>
-      </section>
-
       <section class="panel output-panel">
         <div class="panel-head">
           <h2>출력</h2>
@@ -191,11 +198,36 @@
             <dt>감지 요약</dt>
             <dd id="approvalModalSummary">-</dd>
           </div>
+          <div>
+            <dt>요청 유형</dt>
+            <dd id="approvalModalType">-</dd>
+          </div>
+          <div>
+            <dt>명령/대상</dt>
+            <dd id="approvalModalCommand">-</dd>
+          </div>
+          <div>
+            <dt>작업 디렉터리</dt>
+            <dd id="approvalModalCwd">-</dd>
+          </div>
+          <div>
+            <dt>위험도</dt>
+            <dd id="approvalModalRisk">-</dd>
+          </div>
+          <div>
+            <dt>추천 행동</dt>
+            <dd id="approvalModalRecommendation">-</dd>
+          </div>
         </dl>
+        <details class="approval-raw">
+          <summary>원문 보기</summary>
+          <pre id="approvalModalRaw">-</pre>
+        </details>
         <p class="modal-warning">주의: 이 버튼은 현재 AI CLI 창에 키 입력을 보내는 기능입니다. 위험한 명령은 승인하지 마세요.</p>
+        <p id="approvalModalRiskWarning" class="modal-warning">-</p>
         <div class="modal-actions">
-          <button data-approval-action="/api/tmux/approve-once" type="button">1회 승인</button>
-          <button data-approval-action="/api/tmux/approve-session" type="button">세션 승인</button>
+          <button id="approvalModalApproveOnce" data-approval-action="/api/tmux/approve-once" type="button">1회 승인</button>
+          <button id="approvalModalApproveSession" data-approval-action="/api/tmux/approve-session" type="button">세션 승인</button>
           <button data-approval-action="/api/tmux/reject" class="danger-action" type="button">거절</button>
           <button data-approval-action="/api/tmux/interrupt" class="danger-action" type="button">중단</button>
           <button id="dismissApprovalModal" type="button">닫기</button>
diff --git a/web/public/style.css b/web/public/style.css
index 9d50479..e9c85a8 100644
--- a/web/public/style.css
+++ b/web/public/style.css
@@ -64,11 +64,11 @@ h2 {
 }
 
 .layout {
-  display: grid;
-  grid-template-columns: minmax(320px, 0.95fr) minmax(360px, 1.05fr);
+  display: flex;
+  flex-direction: column;
   gap: 18px;
   padding: 22px;
-  max-width: 1440px;
+  max-width: 1100px;
   margin: 0 auto;
 }
 
@@ -80,14 +80,6 @@ h2 {
   padding: 18px;
 }
 
-.setup {
-  grid-row: span 4;
-}
-
-.output-panel {
-  grid-column: 2;
-}
-
 .panel-head {
   display: flex;
   align-items: center;
@@ -103,6 +95,26 @@ h2 {
   justify-content: flex-end;
 }
 
+.quick-actions {
+  display: grid;
+  gap: 12px;
+}
+
+.job-settings {
+  padding: 14px 18px;
+}
+
+.job-settings > summary {
+  cursor: pointer;
+  font-size: 18px;
+  font-weight: 800;
+  padding: 4px 0;
+}
+
+.job-settings[open] {
+  padding-bottom: 18px;
+}
+
 label {
   display: grid;
   gap: 7px;
@@ -173,7 +185,7 @@ select {
 }
 
 textarea {
-  min-height: 330px;
+  min-height: 140px;
   resize: vertical;
   padding: 12px;
   line-height: 1.5;
@@ -484,6 +496,37 @@ button:disabled {
   font-weight: 800;
 }
 
+.approval-details dd[data-risk="low"] {
+  color: #0f766e;
+}
+
+.approval-details dd[data-risk="medium"],
+.approval-details dd[data-risk="unknown"] {
+  color: #92400e;
+}
+
+.approval-details dd[data-risk="high"] {
+  color: var(--danger);
+}
+
+.approval-raw {
+  margin-top: 14px;
+}
+
+.approval-raw summary {
+  cursor: pointer;
+  color: var(--muted);
+  font-size: 13px;
+  font-weight: 800;
+}
+
+.approval-raw pre {
+  min-height: 120px;
+  max-height: 220px;
+  margin-top: 8px;
+  font-size: 12px;
+}
+
 .modal-warning {
   margin: 14px 0 0;
   padding: 10px 12px;
@@ -610,16 +653,9 @@ pre {
   }
 
   .layout {
-    grid-template-columns: 1fr;
     padding: 14px;
   }
 
-  .setup,
-  .output-panel {
-    grid-row: auto;
-    grid-column: auto;
-  }
-
   .step-grid {
     grid-template-columns: 1fr;
   }
diff --git a/web/server.js b/web/server.js
index 0ce1e5d..7d07b26 100644
--- a/web/server.js
+++ b/web/server.js
@@ -16,6 +16,8 @@ const SAFE_WINDOWS = {
   'claude-plan': 'claude',
   'codex-implement': 'codex',
   'claude-review': 'claude',
+  'codex-review-fix': 'codex',
+  'claude-re-review': 'claude',
   claude: 'claude',
   codex: 'codex'
 };
@@ -56,9 +58,7 @@ const ISSUE_PATTERNS = [
   {
     type: 'approval_required',
     patterns: [
-      /approval|approve|allow|continue|proceed|permission/i,
-      /승인|허용|계속 진행|진행하시겠습니까|거절/i,
-      /1\).*(approve|allow|승인|계속)|2\).*(session|세션)|3\).*(reject|거절)/i
+      /allow execution|allow edit|do you want to proceed|would you like to continue|allow for this session|no, suggest changes|enter your response/i
     ]
   },
   {
@@ -80,12 +80,16 @@ const pipelineStates = new Map();
 const PIPELINE_STAGES = [
   { id: 'claude-plan', state: 'claude_planning', label: 'Claude 계획 생성', role: 'claude-plan', window: 'claude', artifacts: ['plan.md', 'codex-task.md'] },
   { id: 'codex-implement', state: 'codex_implementing', label: 'Codex 구현 실행', role: 'codex-implement', window: 'codex', artifacts: ['patch.md'] },
-  { id: 'claude-review', state: 'claude_reviewing', label: 'Claude 리뷰 실행', role: 'claude-review', window: 'claude', artifacts: ['review.md'] }
+  { id: 'claude-review', state: 'claude_reviewing', label: 'Claude 리뷰 실행', role: 'claude-review', window: 'claude', artifacts: ['review.md'] },
+  { id: 'codex-review-fix', state: 'codex_fixing_review', label: 'Codex 리뷰 반영 실행', role: 'codex-review-fix', window: 'codex', artifacts: ['status.md'] },
+  { id: 'claude-re-review', state: 'claude_re_reviewing', label: 'Claude 재리뷰 실행', role: 'claude-re-review', window: 'claude', artifacts: ['review.md'] }
 ];
 const ACTIVE_PIPELINE_STATES = new Set([
   'claude_planning',
   'codex_implementing',
   'claude_reviewing',
+  'codex_fixing_review',
+  'claude_re_reviewing',
   'approval_required'
 ]);
 const FINAL_PIPELINE_STATES = new Set([
@@ -93,6 +97,9 @@ const FINAL_PIPELINE_STATES = new Set([
   'failed',
   'blocked',
   'manual_review_required',
+  'review_approved',
+  'review_changes_requested',
+  'manual_final_approval_required',
   'idle'
 ]);
 const ARTIFACT_PRIORITY = [
@@ -240,8 +247,97 @@ function currentTargetWindow(state) {
   return stage ? stage.window : null;
 }
 
-function publicIdlePipelineState(projectDir = null, jobId = null) {
+function stageByState(status) {
+  return PIPELINE_STAGES.find((stage) => stage.state === status) || null;
+}
+
+function stageForGate(status, currentStep) {
+  return stageById(currentStep) || stageByState(status) || PIPELINE_STAGES[0];
+}
+
+function nextStageGate(state) {
+  if (!state) {
+    return PIPELINE_STAGES[0];
+  }
+  if (state.status === 'succeeded' || state.status === 'review_approved' || state.status === 'manual_final_approval_required') {
+    return null;
+  }
+  if (state.status === 'review_changes_requested') {
+    return stageById('codex-review-fix');
+  }
+  return stageForGate(state.status, state.currentStep);
+}
+
+function artifactPath(projectDir, jobId, name) {
+  return path.join(projectDir, 'docs', 'ai', 'jobs', jobId, name);
+}
+
+async function artifactStat(projectDir, jobId, name) {
+  const stat = await fs.stat(artifactPath(projectDir, jobId, name)).catch(() => null);
+  return stat && stat.isFile() && stat.size > 0 ? stat : null;
+}
+
+async function artifactExists(projectDir, jobId, name, afterIso = null) {
+  const stat = await artifactStat(projectDir, jobId, name);
+  if (!stat) {
+    return false;
+  }
+  if (!afterIso) {
+    return true;
+  }
+  const after = Date.parse(afterIso);
+  return Number.isNaN(after) ? true : stat.mtimeMs >= after;
+}
+
+async function artifactStatus(projectDir, jobId, names, afterIso = null) {
+  const files = [];
+  for (const name of names) {
+    const stat = await artifactStat(projectDir, jobId, name);
+    const exists = stat ? await artifactExists(projectDir, jobId, name, afterIso) : false;
+    files.push({ name, exists, modifiedAt: stat ? stat.mtime.toISOString() : null });
+  }
+  return files;
+}
+
+async function allArtifactsExist(projectDir, jobId, names, afterIso = null) {
+  const files = await artifactStatus(projectDir, jobId, names, afterIso);
+  return {
+    ok: files.every((file) => file.exists),
+    files,
+    missing: files.filter((file) => !file.exists).map((file) => file.name)
+  };
+}
+
+async function buildStageRequirements(projectDir, jobId, stage) {
+  if (!stage) {
+    return {
+      stage: null,
+      label: null,
+      files: [],
+      missing: [],
+      nextStageAllowed: true,
+      guidance: ''
+    };
+  }
+  const requirements = await allArtifactsExist(projectDir, jobId, stage.artifacts);
+  return {
+    stage: stage.id,
+    label: stage.label,
+    files: requirements.files,
+    missing: requirements.missing,
+    nextStageAllowed: requirements.ok,
+    guidance: requirements.ok
+      ? '다음 단계를 실행할 수 있습니다.'
+      : `필수 산출물이 아직 생성되지 않았습니다: ${requirements.missing.join(', ')}`
+  };
+}
+
+async function publicIdlePipelineState(projectDir = null, jobId = null) {
   const now = new Date().toISOString();
+  const artifacts = projectDir && jobId ? await listArtifacts(projectDir, jobId) : [];
+  const requirements = projectDir && jobId
+    ? await buildStageRequirements(projectDir, jobId, PIPELINE_STAGES[0])
+    : await buildStageRequirements(null, null, null);
   return {
     ok: true,
     jobKey: projectDir && jobId ? pipelineKey(projectDir, jobId) : null,
@@ -255,15 +351,22 @@ function publicIdlePipelineState(projectDir = null, jobId = null) {
       targetWindow: null,
       waitingApproval: false,
       detectedIssue: null,
-      artifacts: [],
+      artifacts,
       gitDiff: '-',
       reviewStatus: '-',
-      nextAction: '작업 요청을 입력한 뒤 Claude → Codex → Claude 전체 실행을 누르세요.'
+      nextAction: '작업 요청을 입력한 뒤 Claude → Codex → Claude 전체 실행을 누르세요.',
+      requirements
+    },
+    artifacts,
+    summary: {
+      createdArtifacts: artifacts.map((artifact) => artifact.name),
+      gitDiff: { hasChanges: false, saved: false, path: null, changedFiles: [] },
+      review: { status: 'not_started', file: null, decision: null }
     }
   };
 }
 
-function publicPipelineState(state) {
+async function publicPipelineState(state) {
   if (!state) {
     return publicIdlePipelineState();
   }
@@ -277,6 +380,7 @@ function publicPipelineState(state) {
     ? `${review.status}: ${review.file}${review.decision ? ` / ${review.decision}` : ''}`
     : review.status || '-';
   const detectedIssue = state.detectedIssue || null;
+  const requirements = await buildStageRequirements(state.projectDir, state.jobId, nextStageGate(state));
 
   return {
     ok: true,
@@ -297,7 +401,8 @@ function publicPipelineState(state) {
       artifacts: state.artifacts,
       gitDiff: gitDiffText,
       reviewStatus,
-      nextAction: nextRecommendedAction(state, reviewStatus)
+      nextAction: nextRecommendedAction(state, reviewStatus),
+      requirements
     },
     steps: state.steps,
     artifacts: state.artifacts,
@@ -315,6 +420,18 @@ function pipelineMessage(status) {
   if (status === 'claude_reviewing') {
     return 'Claude가 현재 diff와 패치 요약을 리뷰하는 단계입니다.';
   }
+  if (status === 'codex_fixing_review') {
+    return 'Codex가 Claude 리뷰의 수정 요청만 반영하는 단계입니다.';
+  }
+  if (status === 'claude_re_reviewing') {
+    return 'Claude가 수정 반영 후 diff를 다시 리뷰하는 단계입니다.';
+  }
+  if (status === 'review_approved' || status === 'manual_final_approval_required') {
+    return 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.';
+  }
+  if (status === 'review_changes_requested') {
+    return 'Claude가 수정 요청을 남겼습니다. Codex가 리뷰 내용을 반영해야 합니다.';
+  }
   if (status === 'succeeded') {
     return '파이프라인이 완료되었습니다.';
   }
@@ -334,11 +451,14 @@ function pipelineMessage(status) {
 }
 
 function nextRecommendedAction(state, reviewStatus) {
-  if (state.status === 'succeeded') {
+  if (state.status === 'review_approved' || state.status === 'manual_final_approval_required' || state.status === 'succeeded') {
     return reviewStatus && reviewStatus !== '-'
       ? 'Claude 리뷰 결과를 확인한 뒤 사람이 직접 commit, push, PR 생성 여부를 결정하세요.'
       : '산출물과 git diff를 확인한 뒤 사람이 직접 다음 작업을 결정하세요.';
   }
+  if (state.status === 'review_changes_requested') {
+    return 'Codex 리뷰 반영 실행을 눌러 Claude가 요청한 수정만 반영하세요.';
+  }
   if (state.status === 'manual_review_required' || state.status === 'approval_required') {
     return 'tmux 출력을 확인하고 필요한 경우 승인 / 계속 진행, 세션 승인, 거절, 중단 중 하나를 선택하세요.';
   }
@@ -438,24 +558,25 @@ async function refreshPipelineArtifacts(state) {
 
 async function findFirstExistingArtifact(projectDir, jobId, names) {
   for (const name of names) {
-    const filePath = path.join(projectDir, 'docs', 'ai', 'jobs', jobId, name);
-    const stat = await fs.stat(filePath).catch(() => null);
-    if (stat && stat.isFile() && stat.size > 0) {
-      return { name, path: filePath };
+    if (await artifactExists(projectDir, jobId, name)) {
+      return { name, path: artifactPath(projectDir, jobId, name) };
     }
   }
   return null;
 }
 
-async function waitForArtifact(projectDir, jobId, names, state = null, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
+async function waitForArtifacts(projectDir, jobId, names, state = null, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
   const started = Date.now();
+  const afterIso = state && state.currentStep
+    ? state.steps.find((step) => step.id === state.currentStep)?.startedAt || null
+    : null;
   while (Date.now() - started < timeoutMs) {
     if (state && !ACTIVE_PIPELINE_STATES.has(state.status)) {
       return null;
     }
-    const artifact = await findFirstExistingArtifact(projectDir, jobId, names);
-    if (artifact) {
-      return artifact;
+    const requirements = await allArtifactsExist(projectDir, jobId, names, afterIso);
+    if (requirements.ok) {
+      return requirements.files;
     }
     await new Promise((resolve) => setTimeout(resolve, PIPELINE_POLL_MS));
   }
@@ -492,6 +613,10 @@ function markTimedOutRunningStep(state) {
 }
 
 function summarizeIssue(output, type) {
+  if (type === 'approval_required') {
+    const block = extractApprovalBlock(output);
+    return block ? block.split(/\r?\n/).map((line) => line.trim()).filter(Boolean)[0]?.slice(0, 220) || ISSUE_RECOMMENDATIONS[type] : ISSUE_RECOMMENDATIONS[type];
+  }
   const lines = String(output || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
   const matcher = ISSUE_PATTERNS.find((item) => item.type === type);
   if (matcher) {
@@ -503,9 +628,72 @@ function summarizeIssue(output, type) {
   return lines.slice(-3).join(' ').slice(0, 220) || ISSUE_RECOMMENDATIONS[type] || '최근 tmux 출력에서 확인이 필요한 상태를 감지했습니다.';
 }
 
+function isLikelyCodeOrSearchLine(line) {
+  return /^\s*[+-]/.test(line)
+    || /\bconst\s+|\bfunction\s+|=>|stageWindows|pipelineStates|server\.js|Search\s+/i.test(line)
+    || /['"]approval_required['"]|['"]manual_review_required['"]/i.test(line)
+    || /^\s*(web\/|app\/|docs\/|projects\/).+:\d+[:\s]/.test(line)
+    || /^\s*```/.test(line);
+}
+
+function stripCodeLikeApprovalLines(output) {
+  const lines = String(output || '').split(/\r?\n/);
+  let inCodeBlock = false;
+  const kept = [];
+  for (const line of lines) {
+    if (/^\s*```/.test(line)) {
+      inCodeBlock = !inCodeBlock;
+      continue;
+    }
+    if (inCodeBlock || isLikelyCodeOrSearchLine(line)) {
+      continue;
+    }
+    kept.push(line);
+  }
+  return kept.join('\n');
+}
+
+function hasApprovalOptions(block) {
+  return /(?:^|\n)\s*(?:1[.)]|2[.)]|3[.)]).*(?:allow|approve|session|reject|승인|세션|거절|continue)/i.test(block);
+}
+
+function hasCommandOrEditSummary(block) {
+  return /(?:command|execute|run|edit|file|patch|modify|명령|실행|수정|편집|파일)\s*[:：]/i.test(block)
+    || /\b(npm|node|python3?|git|mkdir|cat|chmod|cp|mv|rm|sudo|curl|gh)\b/i.test(block)
+    || /[\w./-]+\.(?:js|css|html|md|json|py|ts|tsx|jsx|yml|yaml|sh)/i.test(block);
+}
+
+function findStrictApprovalPromptBlock(output) {
+  const cleaned = stripCodeLikeApprovalLines(output);
+  const lines = cleaned.split(/\r?\n/);
+  const strongPattern = /allow execution|allow edit|do you want to proceed|would you like to continue|allow for this session|no, suggest changes|enter your response/i;
+  for (let i = lines.length - 1; i >= 0; i -= 1) {
+    if (!strongPattern.test(lines[i])) {
+      continue;
+    }
+    const block = lines.slice(Math.max(0, i - 8), Math.min(lines.length, i + 10)).join('\n').trim();
+    if (hasApprovalOptions(block) || hasCommandOrEditSummary(block)) {
+      return block;
+    }
+  }
+  return '';
+}
+
 function detectIssueFromOutput(output, windowName) {
   const text = String(output || '');
   for (const category of ISSUE_PATTERNS) {
+    if (category.type === 'approval_required') {
+      const block = findStrictApprovalPromptBlock(text);
+      if (block) {
+        return {
+          type: category.type,
+          window: windowName,
+          summary: summarizeIssue(block, category.type),
+          recommendation: ISSUE_RECOMMENDATIONS[category.type]
+        };
+      }
+      continue;
+    }
     if (category.patterns.some((pattern) => pattern.test(text))) {
       return {
         type: category.type,
@@ -527,6 +715,94 @@ async function captureRecentTmuxOutput(windowName, lines = 120) {
   return result.ok ? redactedOutput(result.stdout) : '';
 }
 
+function approvalTypeFromBlock(block) {
+  if (/edit|patch|modify|write|수정|편집|파일/i.test(block)) {
+    return 'file_edit';
+  }
+  if (/command|execute|run|명령|실행/i.test(block)) {
+    return 'command_execution';
+  }
+  return 'unknown';
+}
+
+function extractCommandOrTarget(block) {
+  const lines = String(block || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
+  const commandLine = lines.find((line) => /^\$|^>|^`[^`]+`$|^(npm|node|python|python3|git|mkdir|cat|chmod|cp|mv|rm|sudo|curl|gh)\b/i.test(line));
+  if (commandLine) {
+    return commandLine.replace(/^[$>]\s*/, '').replace(/^`|`$/g, '').slice(0, 260);
+  }
+  const fileLine = lines.find((line) => /(?:^|\s)([\w./-]+\.(?:js|css|html|md|json|py|ts|tsx|jsx|yml|yaml|sh))(?:\s|$)/i.test(line));
+  return fileLine ? fileLine.slice(0, 260) : '';
+}
+
+function classifyApprovalRisk(block, commandOrTarget) {
+  const text = `${block || ''}\n${commandOrTarget || ''}`;
+  if (/rm\s+-rf|sudo\b|curl\b.*\|\s*(bash|sh)|git\s+push|gh\s+pr\s+merge|deploy|deployment|kubectl|terraform|\.env|secret|token|api\s*key|auth\/|payment\/|billing\/|migrations?\/|production|prod\b/i.test(text)) {
+    return {
+      risk: 'high',
+      recommendation: '거절 권장',
+      canApproveOnce: false,
+      canApproveSession: false,
+      warning: '승인하지 마세요. 거절 또는 중단하세요.'
+    };
+  }
+  if (/npm\s+install|chmod\b|\bcp\b|\bmv\b/i.test(text) || /(?:^|\s)(?!docs\/ai\/jobs\/)[\w./-]+\.(?:js|css|html|py|ts|tsx|jsx|json|yml|yaml|sh)/i.test(text)) {
+    return {
+      risk: 'medium',
+      recommendation: '직접 확인 필요',
+      canApproveOnce: true,
+      canApproveSession: false,
+      warning: '명령과 수정 대상을 tmux 출력에서 확인한 뒤 1회 승인만 고려하세요.'
+    };
+  }
+  if (/mkdir\s+-p\s+docs\/ai\/jobs\/|docs\/ai\/jobs\/[\w._-]+|git\s+(status|diff)\b|node\s+--check\b|python3?\s+-m\s+(py_compile|compileall)\b|cat\s+docs\/ai\/jobs\//i.test(text)) {
+    return {
+      risk: 'low',
+      recommendation: '1회 승인 가능',
+      canApproveOnce: true,
+      canApproveSession: true,
+      warning: '세션 승인은 같은 종류의 안전한 명령이 반복될 때만 사용하세요.'
+    };
+  }
+  return {
+    risk: 'unknown',
+    recommendation: '직접 확인 필요',
+    canApproveOnce: false,
+    canApproveSession: false,
+    warning: '명령 내용을 파악하지 못했습니다. tmux 출력에서 직접 확인하세요.'
+  };
+}
+
+function extractApprovalBlock(output) {
+  return findStrictApprovalPromptBlock(output);
+}
+
+function cleanWorkingDirectory(block) {
+  const match = String(block || '').match(/(?:cwd|working directory|작업 디렉터리)\s*[:=]\s*([^\n]+)/i);
+  return match ? match[1].trim().slice(0, 260) : '-';
+}
+
+async function buildApprovalContext(windowName, step = null) {
+  const safeWindow = validateAiTmuxWindow(windowName);
+  const output = await captureRecentTmuxOutput(safeWindow, 180);
+  const rawBlock = extractApprovalBlock(output);
+  if (!rawBlock) {
+    return null;
+  }
+  const commandOrTarget = extractCommandOrTarget(rawBlock);
+  const risk = classifyApprovalRisk(rawBlock, commandOrTarget);
+  return {
+    window: safeWindow,
+    step,
+    type: approvalTypeFromBlock(rawBlock),
+    commandOrTarget: commandOrTarget || '확인 불가',
+    workingDirectory: cleanWorkingDirectory(rawBlock),
+    rawBlock,
+    ...risk,
+    summary: `${safeWindow === 'codex' ? 'Codex' : 'Claude'} 창에서 명령 실행 승인 요청이 감지되었습니다.`
+  };
+}
+
 async function refreshDetectedIssue(state) {
   if (!state || !ACTIVE_PIPELINE_STATES.has(state.status)) {
     return;
@@ -540,6 +816,13 @@ async function refreshDetectedIssue(state) {
   if (!issue) {
     return;
   }
+  if (issue.type === 'approval_required') {
+    issue.approvalContext = await buildApprovalContext(targetWindow, state.currentStep).catch(() => null);
+    if (!issue.approvalContext) {
+      return;
+    }
+    issue.summary = issue.approvalContext.summary;
+  }
 
   state.detectedIssue = issue;
   state.error = issue.recommendation;
@@ -565,25 +848,24 @@ async function applyArtifactProgress(state) {
     return;
   }
 
-  for (const stage of PIPELINE_STAGES) {
-    const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, stage.artifacts);
-    const step = state.steps.find((item) => item.id === stage.id);
-    if (artifact && step && step.status === 'running') {
-      state.status = stage.state;
-      state.error = null;
-      state.detectedIssue = null;
-      setStep(state, stage.id, stage.label, 'succeeded', artifact.name);
-    }
-  }
-
   const current = stageById(state.currentStep);
   if (current) {
-    const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, current.artifacts);
-    if (artifact) {
+    const step = state.steps.find((item) => item.id === current.id);
+    const requirements = await allArtifactsExist(state.projectDir, state.jobId, current.artifacts, step?.startedAt || null);
+    if (requirements.ok) {
       state.status = current.state;
       state.error = null;
       state.detectedIssue = null;
-      setStep(state, current.id, current.label, 'succeeded', artifact.name);
+      setStep(state, current.id, current.label, 'succeeded', requirements.files.map((file) => file.name).join(', '));
+      if (current.id === 'codex-review-fix') {
+        state.status = 'review_changes_requested';
+        state.currentStep = null;
+        state.error = 'Codex가 리뷰 반영을 완료했습니다. Claude 재리뷰를 실행하세요.';
+      }
+      if (current.id === 'claude-review' || current.id === 'claude-re-review') {
+        await updateReviewSummary(state.projectDir, state.jobId, state);
+        applyReviewDecision(state);
+      }
     }
   }
 }
@@ -646,14 +928,60 @@ async function updateReviewSummary(projectDir, jobId, state) {
     return;
   }
   const content = await fs.readFile(artifact.path, 'utf8').catch(() => '');
-  const decisionLine = content.split(/\r?\n/).find((line) => /decision|verdict|approve|request changes|comment/i.test(line));
+  const decision = detectReviewDecision(content);
+  const decisionLine = content.split(/\r?\n/).find((line) => /decision|verdict|approve|request[_ -]?changes|block|승인|수정\s*요청|차단|보류/i.test(line));
   state.summary.review = {
     status: 'available',
     file: artifact.name,
-    decision: decisionLine ? decisionLine.trim() : null
+    decision,
+    decisionLine: decisionLine ? decisionLine.trim() : null
   };
 }
 
+function detectReviewDecision(content) {
+  const text = String(content || '');
+  if (/\bBLOCK\b|차단|보류/i.test(text)) {
+    return 'BLOCK';
+  }
+  if (/\bREQUEST[_ -]?CHANGES\b|수정\s*요청/i.test(text)) {
+    return 'REQUEST_CHANGES';
+  }
+  if (/\bAPPROVE\b|\bAPPROVED\b|승인/i.test(text)) {
+    return 'APPROVE';
+  }
+  return 'UNKNOWN';
+}
+
+function applyReviewDecision(state) {
+  const decision = state.summary.review.decision;
+  const now = new Date().toISOString();
+  if (decision === 'APPROVE') {
+    state.status = 'manual_final_approval_required';
+    state.currentStep = null;
+    state.finishedAt = now;
+    state.error = 'Claude 리뷰가 승인되었습니다. 이제 사람이 git diff를 확인하고 commit/PR 여부를 결정하세요.';
+    return;
+  }
+  if (decision === 'REQUEST_CHANGES') {
+    state.status = 'review_changes_requested';
+    state.currentStep = null;
+    state.finishedAt = now;
+    state.error = 'Claude가 수정 요청을 남겼습니다. Codex가 리뷰 내용을 반영해야 합니다.';
+    return;
+  }
+  if (decision === 'BLOCK') {
+    state.status = 'blocked';
+    state.currentStep = null;
+    state.finishedAt = now;
+    state.error = 'Claude가 작업을 차단했습니다. 요청 범위나 안전 조건을 수정해야 합니다.';
+    return;
+  }
+  state.status = 'manual_review_required';
+  state.currentStep = null;
+  state.finishedAt = now;
+  state.error = 'Claude 리뷰 결정을 확인할 수 없습니다. review.md에서 APPROVE, REQUEST_CHANGES, BLOCK 중 하나를 확인하세요.';
+}
+
 async function runPipeline(state, inputKo) {
   const { projectDir, jobId } = state;
   const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
@@ -679,11 +1007,11 @@ async function runPipeline(state, inputKo) {
       if (!sent.ok) {
         throw new Error(`${step.label} 실패: ${sent.message || sent.stderr || 'tmux 전송 실패'}`);
       }
-      const artifact = await waitForArtifact(projectDir, jobId, step.artifacts, state);
+      const artifacts = await waitForArtifacts(projectDir, jobId, step.artifacts, state);
       if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
         return;
       }
-      if (!artifact) {
+      if (!artifacts) {
         markManualRequired(state, step.id, step.label);
         await refreshPipelineArtifacts(state);
         return;
@@ -691,7 +1019,7 @@ async function runPipeline(state, inputKo) {
       state.status = step.state;
       state.error = null;
       state.detectedIssue = null;
-      setStep(state, step.id, step.label, 'succeeded', artifact.name);
+      setStep(state, step.id, step.label, 'succeeded', artifacts.map((artifact) => artifact.name).join(', '));
       await refreshPipelineArtifacts(state);
 
       if (step.id === 'codex-implement') {
@@ -723,11 +1051,11 @@ async function runPipeline(state, inputKo) {
     if (!reviewed.ok) {
       throw new Error(`Claude 리뷰 전송 실패: ${reviewed.message || reviewed.stderr || 'tmux 전송 실패'}`);
     }
-    const reviewArtifact = await waitForArtifact(projectDir, jobId, reviewerStep.artifacts, state);
+    const reviewArtifacts = await waitForArtifacts(projectDir, jobId, reviewerStep.artifacts, state);
     if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
       return;
     }
-    if (!reviewArtifact) {
+    if (!reviewArtifacts) {
       markManualRequired(state, reviewerStep.id, reviewerStep.label);
       await updateReviewSummary(projectDir, jobId, state);
       await refreshPipelineArtifacts(state);
@@ -736,13 +1064,10 @@ async function runPipeline(state, inputKo) {
     state.status = reviewerStep.state;
     state.error = null;
     state.detectedIssue = null;
-    setStep(state, reviewerStep.id, reviewerStep.label, 'succeeded', reviewArtifact.name);
+    setStep(state, reviewerStep.id, reviewerStep.label, 'succeeded', reviewArtifacts.map((artifact) => artifact.name).join(', '));
     await updateReviewSummary(projectDir, jobId, state);
     await refreshPipelineArtifacts(state);
-
-    state.status = 'succeeded';
-    state.currentStep = null;
-    state.finishedAt = new Date().toISOString();
+    applyReviewDecision(state);
   } catch (error) {
     state.status = 'failed';
     state.error = error.message || '파이프라인 실행 실패';
@@ -797,6 +1122,31 @@ function buildPrompt(role, projectDir, jobId, inputKo) {
       '',
       `Review the git diff saved at ${path.join(jobDir, 'local-diff.patch')} when present, ${path.join(jobDir, 'patch.md')}, and the approved request/plan.`,
       `Write the review into ${path.join(jobDir, 'review.md')} using the Claude review output format.`,
+      'The review must include exactly one decision marker: APPROVE, REQUEST_CHANGES, or BLOCK.',
+      'Do not commit, push, merge, deploy, or run arbitrary shell commands.'
+    ].join('\n');
+  }
+
+  if (role === 'codex-review-fix') {
+    return [
+      'Use prompts/codex-implementer.md.',
+      common,
+      '',
+      `Read ${path.join(jobDir, 'patch.md')}, ${path.join(jobDir, 'review.md')}, and the current git diff.`,
+      'Apply only the changes explicitly requested by Claude review. Do not expand scope.',
+      `Update ${path.join(jobDir, 'patch.md')} and write ${path.join(jobDir, 'status.md')} with what changed and which checks ran.`,
+      'Do not commit, push, merge, deploy, or change secrets, .env, auth, payment, production infra, or database migrations.'
+    ].join('\n');
+  }
+
+  if (role === 'claude-re-review') {
+    return [
+      'Use prompts/claude.md.',
+      common,
+      '',
+      `Re-review the updated git diff, ${path.join(jobDir, 'patch.md')}, ${path.join(jobDir, 'status.md')}, and the previous review in ${path.join(jobDir, 'review.md')}.`,
+      `Update ${path.join(jobDir, 'review.md')} with the new review result.`,
+      'The review must include exactly one decision marker: APPROVE, REQUEST_CHANGES, or BLOCK.',
       'Do not commit, push, merge, deploy, or run arbitrary shell commands.'
     ].join('\n');
   }
@@ -883,6 +1233,51 @@ function handleError(res, error) {
   res.status(400).json({ ok: false, error: error.message || '요청을 처리할 수 없습니다.' });
 }
 
+function getOrCreatePipelineState(projectDir, jobId) {
+  const key = pipelineKey(projectDir, jobId);
+  let state = pipelineStates.get(key);
+  if (!state) {
+    state = createPipelineState(projectDir, jobId);
+    state.status = 'idle';
+    state.currentStep = null;
+    pipelineStates.set(key, state);
+  }
+  return state;
+}
+
+async function requireArtifacts(projectDir, jobId, names, message) {
+  const requirements = await allArtifactsExist(projectDir, jobId, names);
+  if (!requirements.ok) {
+    throw new Error(`${message} 누락: ${requirements.missing.join(', ')}`);
+  }
+}
+
+async function sendManualStage(projectDir, jobId, inputKo, stageId) {
+  const stage = stageById(stageId);
+  if (!stage) {
+    throw new Error('허용되지 않은 단계입니다.');
+  }
+  const state = getOrCreatePipelineState(projectDir, jobId);
+  if (ACTIVE_PIPELINE_STATES.has(state.status)) {
+    throw new Error('이미 실행 중인 단계가 있습니다.');
+  }
+  state.status = stage.state;
+  state.error = null;
+  state.detectedIssue = null;
+  state.finishedAt = null;
+  setStep(state, stage.id, stage.label, 'running');
+  const result = await sendToWindow(stage.role, projectDir, jobId, inputKo);
+  await appendPipelineLog(projectDir, jobId, stage.id, `${result.stdout || ''}${result.stderr || ''}${result.message || ''}`);
+  if (!result.ok) {
+    state.status = 'failed';
+    state.error = result.message || result.stderr || 'tmux 전송 실패';
+    state.finishedAt = new Date().toISOString();
+    setStep(state, stage.id, stage.label, 'failed', state.error);
+  }
+  await refreshPipelineArtifacts(state);
+  return { state, result };
+}
+
 app.get('/api/status', async (req, res) => {
   const result = await runFile(path.join(SCRIPTS_DIR, 'status-ai-team.sh'), []);
   res.json(cleanOutput(result));
@@ -1004,11 +1399,11 @@ app.get('/api/pipeline/status', async (req, res) => {
       if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
         await updateReviewSummary(projectDir, jobId, state);
       }
-      res.json(publicPipelineState(state));
+      res.json(await publicPipelineState(state));
       return;
     }
 
-    res.json(publicIdlePipelineState(projectDir, jobId));
+    res.json(await publicIdlePipelineState(projectDir, jobId));
   } catch (error) {
     handleError(res, error);
   }
@@ -1049,6 +1444,20 @@ app.get('/api/tmux/output', async (req, res) => {
   }
 });
 
+app.get('/api/tmux/approval-context', async (req, res) => {
+  try {
+    const windowName = validateAiTmuxWindow(req.query.window);
+    const context = await buildApprovalContext(windowName, typeof req.query.step === 'string' ? req.query.step : null);
+    if (!context) {
+      res.status(404).json({ ok: false, error: '실제 승인 프롬프트를 찾지 못했습니다.' });
+      return;
+    }
+    res.json({ ok: true, approvalContext: context });
+  } catch (error) {
+    handleError(res, error);
+  }
+});
+
 for (const [endpoint, keys] of [
   ['/api/tmux/approve-once', ['1', 'Enter']],
   ['/api/tmux/approve-session', ['2', 'Enter']],
@@ -1124,15 +1533,35 @@ app.post('/api/service/restart-gui', async (req, res) => {
 for (const [endpoint, role] of [
   ['/api/send/claude-plan', 'claude-plan'],
   ['/api/send/codex-implement', 'codex-implement'],
-  ['/api/send/claude-review', 'claude-review']
+  ['/api/send/claude-review', 'claude-review'],
+  ['/api/send/codex-review-fix', 'codex-review-fix'],
+  ['/api/send/claude-re-review', 'claude-re-review']
 ]) {
   app.post(endpoint, async (req, res) => {
     try {
       const projectDir = await resolveProjectDir(req.body.projectDir);
       const jobId = validateJobId(req.body.jobId);
       const inputKo = typeof req.body.inputKo === 'string' ? req.body.inputKo : '';
-      const result = await sendToWindow(role, projectDir, jobId, inputKo);
-      res.json(cleanOutput(result));
+      if (role === 'codex-implement') {
+        await requireArtifacts(projectDir, jobId, ['plan.md', 'codex-task.md'], 'Claude 계획이 아직 완료되지 않았습니다. plan.md와 codex-task.md가 생성된 뒤 Codex를 실행할 수 있습니다.');
+      }
+      if (role === 'claude-review') {
+        await requireArtifacts(projectDir, jobId, ['patch.md'], 'patch.md가 생성된 뒤 Claude 리뷰를 실행할 수 있습니다.');
+      }
+      if (role === 'codex-review-fix') {
+        await requireArtifacts(projectDir, jobId, ['patch.md', 'review.md'], 'patch.md와 review.md가 생성된 뒤 Codex 리뷰 반영을 실행할 수 있습니다.');
+      }
+      if (role === 'claude-re-review') {
+        await requireArtifacts(projectDir, jobId, ['patch.md', 'review.md', 'status.md'], 'Codex 리뷰 반영 상태가 생성된 뒤 Claude 재리뷰를 실행할 수 있습니다.');
+      }
+      const stage = stageById(role);
+      const { state, result } = stage
+        ? await sendManualStage(projectDir, jobId, inputKo, role)
+        : { state: null, result: await sendToWindow(role, projectDir, jobId, inputKo) };
+      res.json({
+        ...cleanOutput(result),
+        pipeline: state ? (await publicPipelineState(state)).status : null
+      });
     } catch (error) {
       handleError(res, error);
     }

```

## 2026-05-14T11:58:49.702Z — claude-review

```
(no output)
```

## 2026-05-14T11:58:49.703Z — claude-review

```
(no output)
```
