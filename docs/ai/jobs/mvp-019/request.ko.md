# 작업 ID
mvp-019

# 작업명
dry-run 결과 리포트 분석 및 전략 개선 루프

미국주식 자동 페이퍼매매 시스템에서 장시간 KIS paper / dry-run 결과를 분석하고,
전략 개선 루프를 만들고 싶다.

현재 목표는 실전거래가 아니라 dry-run / paper trading 결과 분석이다.
live trading은 절대 활성화하지 않는다.

## 현재 상태

이미 완료된 것:
- KIS dry-run / fail-closed 구조
- KIS_ORDER_DRY_RUN=true 기본값
- 장시간 dry-run runner
- dry-run status
- dry-run report 파일 생성
- RiskEngine / OMS / BrokerAdapter 경계
- 프리마켓 갭 + 거래량 돌파 전략
- 테스트 통과 상태

## 이번 목표

dry-run 실행 결과를 읽어서 아래를 분석하고 리포트로 남기는 기능을 만들어줘.

1. 후보 종목 수
2. RiskEngine 통과/차단 수
3. 차단 사유별 통계
4. 스프레드 초과 차단 수
5. stale quote 차단 수
6. 시장가 주문 차단 수
7. OMS 거절 수
8. dry-run 주문 preview 생성 수
9. 전략별 후보 성과
10. 세션별 후보 성과
11. 에러 횟수
12. 개선이 필요한 전략 조건

## 구현할 기능

### 1. dry-run report analyzer

dry-run 결과 파일을 읽고 요약 리포트를 생성해줘.

입력 후보:
- reports/dry_run/dry_run_events.jsonl
- reports/dry_run/dry_run_summary.json
- reports/dry_run/dry_run_orders.csv

출력 후보:
- reports/dry_run/analysis_summary.json
- reports/dry_run/analysis_report.md

### 2. 분석 지표

아래 지표를 계산해줘.

- total_ticks
- total_candidates
- candidates_blocked
- candidates_passed_risk
- dry_run_orders_created
- dry_run_orders_rejected
- risk_rejections
- oms_rejections
- stale_quote_rejections
- spread_rejections
- market_order_rejections
- kis_fail_closed_count
- errors_total
- top_block_reasons
- symbols_seen
- symbols_blocked
- symbols_passed
- strategy_pass_rate

### 3. 전략 개선 제안

LLM이 직접 주문 판단을 하지는 않는다.

다만 리포트 기반으로 사람이 볼 수 있는 개선 제안을 생성해줘.

예:
- 스프레드 제한이 너무 빡센지
- 거래량 기준이 너무 낮거나 높은지
- stale quote가 자주 발생하는지
- 후보는 많지만 RiskEngine에서 대부분 막히는지
- 전략 조건을 더 보수적으로 해야 하는지

### 4. Claude/Codex 리뷰 루프 연결

분석 결과를 Claude가 읽고 전략 개선안을 작성할 수 있게 문서 포맷을 만들어줘.

예:
- reports/dry_run/claude_review_input.md

이 파일에는 아래가 포함되어야 한다.

- dry-run summary
- 주요 차단 사유
- 전략별 통계
- 위험 경고
- 다음 개선 후보

### 5. API 또는 CLI

가능하면 아래 중 하나를 추가해줘.

API:
- POST /reports/dry-run/analyze
- GET /reports/dry-run/latest

또는 CLI:
- python -m app.reports.analyze_dry_run

현재 프로젝트 구조에 맞춰 더 자연스러운 방식으로 구현해줘.

## 안전 조건

반드시 유지:
- live trading 비활성
- KIS_ORDER_DRY_RUN=true 기본값
- 시장가 주문 금지
- 실제 주문 전송 금지
- Strategy가 KIS 직접 호출 금지
- Agent/LLM이 직접 주문 금지
- OMS 우회 금지
- RiskEngine 우회 금지

## 보안 조건

리포트에 아래 값이 노출되면 안 된다.

- KIS app key
- KIS app secret
- KIS account number 원문
- access token
- refresh token
- .env 내용

계좌번호가 필요하면 마스킹만 허용한다.

## 테스트 요구사항

아래 테스트를 추가해줘.

1. 빈 dry-run 파일 분석 가능
2. 정상 dry-run events 분석 가능
3. block reason 집계 가능
4. symbol별 통계 가능
5. strategy pass rate 계산 가능
6. analysis_summary.json 생성
7. analysis_report.md 생성
8. claude_review_input.md 생성
9. secret/account/token이 리포트에 노출되지 않음
10. 기존 테스트 계속 통과

## 수정 가능 파일

필요하면 아래 파일을 수정해도 된다.

- projects/paper-trading/app/reports/*
- projects/paper-trading/app/api/routes.py
- projects/paper-trading/app/api/server.py
- projects/paper-trading/app/runtime/*
- projects/paper-trading/tests/*
- projects/paper-trading/README.md
- docs/ai/jobs/mvp-019/patch.md

## 금지 사항

- 실제 주문 기능을 만들지 마.
- live trading을 활성화하지 마.
- 시장가 주문을 허용하지 마.
- KIS endpoint/TR ID/payload를 추측하지 마.
- app key, app secret, account number, token을 출력하지 마.
- .env를 Git에 추가하지 마.
- auth, payment, production infra, database migrations는 건드리지 마.
- git commit, push, merge는 자동화하지 마.

## 검증

아래를 실행해줘.

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider