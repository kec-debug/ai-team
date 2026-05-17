# 작업 ID
mvp-021

# 작업명
paper trading 브라우저 대시보드 UI 추가

현재 서버는 http://127.0.0.1:8000/docs 에서는 API 확인이 가능하지만,
http://127.0.0.1:8000/dashboard 는 {"detail":"Not Found"}가 나온다.

초보자가 curl이나 Swagger UI 없이 확인할 수 있도록
브라우저 대시보드 UI를 추가해줘.

## 목표

아래 주소에서 대시보드가 열리게 해줘.

- GET /dashboard

## 대시보드에 보여줄 내용

1. Paper trading 상태
   - mode
   - live_enabled
   - market_orders_allowed
   - KIS_ORDER_DRY_RUN
   - secret_exposed

2. KIS 상태
   - kis_config_loaded
   - kis_authenticated
   - kis_account_loaded
   - kis_market_data_available
   - kis_order_entry_ready
   - kis_last_error

3. Dry-run 상태
   - running
   - started_at
   - last_tick_at
   - ticks_total
   - candidates_seen
   - candidates_blocked
   - dry_run_orders_created
   - errors_total
   - last_error

4. 버튼
   - 상태 새로고침
   - Dry-run 시작
   - Tick 1회 실행
   - Dry-run 중지
   - 리포트 분석
   - 최신 리포트 보기

5. 최신 리포트
   - analysis_report.md 내용을 화면에 표시하거나
   - 최신 리포트 경로와 요약을 표시

## 안전 조건

- 실제 주문 버튼은 만들지 마.
- live trading 활성화 버튼은 만들지 마.
- market order 허용 버튼은 만들지 마.
- KIS app key, app secret, 계좌번호, token을 화면에 표시하지 마.
- .env 내용을 화면에 출력하지 마.
- 모든 버튼은 기존 safe endpoint만 호출하게 해.
- KIS_ORDER_DRY_RUN=true 상태를 기본으로 유지해.

## 구현 방식

현재 프로젝트 구조에 맞게 최소 구현해줘.

가능한 방식:
- FastAPI HTMLResponse로 간단한 /dashboard 반환
- static HTML/JS/CSS 추가 가능
- 외부 프론트엔드 프레임워크 추가하지 마
- 한 화면에서 상태 확인과 버튼 실행이 가능하게 해줘

## 수정 가능 파일

- projects/paper-trading/app/api/routes.py
- projects/paper-trading/app/api/server.py
- projects/paper-trading/app/static/*
- projects/paper-trading/tests/*
- projects/paper-trading/README.md
- docs/ai/jobs/mvp-021/patch.md

## 금지

- 실제 주문 기능 만들지 마
- live trading 활성화하지 마
- 시장가 주문 허용하지 마
- KIS endpoint/TR ID/payload 추측하지 마
- app key, app secret, account number, token 출력하지 마
- .env Git에 추가하지 마
- git commit, push, merge 자동화하지 마

## 검증

cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider

## 완료 후 patch.md에 정리

1. /dashboard 주소
2. 어떤 상태를 보여주는지
3. 어떤 버튼이 있는지
4. secret이 노출되지 않는지
5. live trading 버튼이 없는지
6. 테스트 결과

## 추가 조건

- 승인된 작업 범위 안에서는 추가 plan 확인을 묻지 말고 바로 구현을 시작해.
- 필요한 경우에만 최소한의 질문을 해.