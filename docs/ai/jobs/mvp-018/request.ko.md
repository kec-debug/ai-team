# 작업 ID
mvp-018

# 작업명
장시간 KIS paper / dry-run 검증

미국주식 자동 페이퍼매매 시스템에서 KIS paper / dry-run 장시간 검증 기능을 만들어줘.

현재 목표는 실전거래가 아니라 KIS 모의투자 또는 dry-run 기반 안정성 검증이다.
live trading은 절대 활성화하지 않는다.

## 현재 상태

이미 완료된 것:
- paper-trading 프로젝트 기본 구조
- KIS 설정 구조
- KIS Auth / Account / MarketData / Order 경계
- KIS dry-run / fail-closed 구조
- KIS_ORDER_DRY_RUN=true 기본값
- /paper/status KIS 상태 표시
- RiskEngine / OMS / BrokerAdapter 경계
- 프리마켓 갭 + 거래량 돌파 전략
- secret/account/token masking
- 테스트 통과 상태

## 이번 목표

KIS paper / dry-run을 장시간 돌려도 안전하게 상태를 추적하고,
주문 후보, RiskEngine 차단, OMS 처리, KIS dry-run 주문 preview, 에러, 통계를 기록할 수 있게 해줘.

이번 단계에서는 실제 주문 전송을 하지 않는다.

## 구현할 기능

### 1. 장시간 dry-run runner

KIS dry-run 전용 runner를 추가하거나 기존 paper runner를 확장해줘.

필수 동작:
- 일정 주기마다 실행
- 전략 후보 생성
- RiskEngine 통과 여부 확인
- OMS 경로 확인
- KIS dry-run order preview 생성
- 실제 HTTP 주문 전송은 하지 않음
- 결과를 로그/파일/상태로 기록
- graceful start / stop 지원

가능한 API:
- POST /paper/dry-run/start
- POST /paper/dry-run/stop
- POST /paper/dry-run/tick
- GET /paper/dry-run/status

기존 /paper/start, /paper/stop, /paper/status 구조가 있으면 그 구조에 맞춰 최소 확장해줘.

### 2. 검증 지표 수집

아래 지표를 수집해줘.

- run_started_at
- last_tick_at
- ticks_total
- candidates_seen
- candidates_blocked
- candidates_passed_risk
- dry_run_orders_created
- dry_run_orders_rejected
- oms_rejections
- risk_rejections
- stale_quote_rejections
- spread_rejections
- market_order_rejections
- kis_fail_closed_count
- errors_total
- last_error
- uptime_seconds

### 3. 결과 저장

장시간 검증 결과를 파일로 저장할 수 있게 해줘.

가능한 위치:
- projects/paper-trading/reports/dry_run/
- 또는 현재 프로젝트 구조에 맞는 reports 폴더

파일 예시:
- dry_run_events.jsonl
- dry_run_summary.json
- dry_run_orders.csv

중요:
- app key, app secret, account number, token 원문 저장 금지
- account는 마스킹만 허용
- raw KIS response 저장 시 sanitized only
- .env 저장 금지

### 4. safety guard 유지

반드시 유지:
- TRADING_MODE=paper
- LIVE_TRADING_ENABLED=false
- ALLOW_MARKET_ORDERS=false
- KIS_ORDER_DRY_RUN=true
- 시장가 주문 금지
- live 주문 금지
- 실전 주문 금지
- Strategy가 KIS 직접 호출 금지
- Agent/LLM이 KIS 직접 호출 금지
- OMS 우회 금지
- RiskEngine 우회 금지

### 5. dry-run status 확장

/paper/status 또는 별도 /paper/dry-run/status에 아래를 추가해줘.

- dry_run_running
- dry_run_started_at
- dry_run_last_tick_at
- dry_run_ticks_total
- dry_run_orders_created
- dry_run_orders_rejected
- dry_run_errors_total
- dry_run_last_error
- kis_order_dry_run
- live_trading_enabled
- allow_market_orders
- secret_exposed

### 6. kill switch / stop

장시간 실행 중에도 즉시 멈출 수 있어야 한다.

필수:
- stop API
- kill switch가 켜지면 새 dry-run 주문 후보 생성 중단
- 오류가 일정 횟수 이상이면 자동 stop 또는 blocked 상태
- 상태에 stop reason 기록

### 7. 테스트

아래 테스트를 추가해줘.

1. dry-run runner start / stop
2. one tick 실행
3. KIS_ORDER_DRY_RUN=true이면 HTTP 주문 전송 안 함
4. live trading true이면 dry-run 주문도 차단
5. market order 후보는 거절
6. RiskEngine 차단 후보는 OMS로 넘어가지 않음
7. OMS rejection 카운트 증가
8. dry-run order preview 생성
9. secret/account/token이 report/status에 노출되지 않음
10. kill switch 작동 시 새 tick 차단
11. errors_total / last_error 기록
12. report 파일 생성
13. 기존 테스트 계속 통과

## 수정 가능 파일

필요하면 아래 파일을 수정해도 된다.

- projects/paper-trading/app/runtime/*
- projects/paper-trading/app/broker/kis.py
- projects/paper-trading/app/api/routes.py
- projects/paper-trading/app/api/server.py
- projects/paper-trading/app/oms/*
- projects/paper-trading/app/risk/*
- projects/paper-trading/app/models/*
- projects/paper-trading/app/config.py
- projects/paper-trading/tests/*
- projects/paper-trading/README.md
- docs/ai/jobs/mvp-018/patch.md

현재 프로젝트 구조가 다르면 현재 구조에 맞춰 최소 수정해줘.

## 금지 사항

- 실제 KIS app key, app secret, 계좌번호, token을 코드/문서/로그/report에 쓰지 마
- .env를 Git에 추가하지 마
- 실전 주문 기능을 만들지 마
- live trading을 활성화하지 마
- 시장가 주문을 허용하지 마
- KIS endpoint/TR ID/payload를 추측하지 마
- Strategy가 KIS를 직접 호출하게 만들지 마
- Agent/LLM이 직접 주문하게 만들지 마
- auth, payment, production infra, database migrations는 건드리지 마
- git commit, push, merge는 자동화하지 마

## 검증

아래를 실행해줘.

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider