# 작업 ID
mvp-020

# 작업명
초보자용 실행 스크립트 추가

현재 paper-trading 서버 확인과 dry-run 실행을 하려면 curl 명령을 너무 많이 입력해야 해서 사용하기 어렵다.

목표:
초보자도 짧은 명령어 하나로 상태 확인, dry-run 실행, 분석 리포트 생성을 할 수 있게 scripts를 만들어줘.

## 만들 스크립트

아래 스크립트를 추가해줘.

1. scripts/start_server.sh
   - paper trading 서버 실행
   - TRADING_MODE=paper
   - LIVE_TRADING_ENABLED=false
   - ALLOW_MARKET_ORDERS=false
   - KIS_ORDER_DRY_RUN=true
   - uvicorn 실행

2. scripts/status.sh
   - /paper/status 호출
   - /paper/dry-run/status 호출
   - 보기 쉽게 출력

3. scripts/start_dry_run.sh
   - /paper/dry-run/start 호출

4. scripts/tick.sh
   - dry-run이 running 상태인지 확인
   - running이 아니면 start 먼저 호출
   - /paper/dry-run/tick 호출
   - 결과 보기 쉽게 출력

5. scripts/stop_dry_run.sh
   - /paper/dry-run/stop 호출

6. scripts/analyze.sh
   - /reports/dry-run/analyze 호출
   - /reports/dry-run/latest 호출
   - analysis_report.md 위치를 출력

7. scripts/smoke_check.sh
   - status
   - start dry-run
   - tick
   - analyze
   - latest
   - stop
   전체를 한 번에 실행

## 중요 조건

- 실제 주문은 절대 실행하지 않는다.
- KIS_ORDER_DRY_RUN=true를 기본으로 강제한다.
- LIVE_TRADING_ENABLED=false를 기본으로 강제한다.
- ALLOW_MARKET_ORDERS=false를 기본으로 강제한다.
- market order를 허용하지 않는다.
- .env나 secret 값을 출력하지 않는다.
- app key, app secret, account number, token을 출력하지 않는다.
- live trading을 활성화하지 않는다.
- git commit, push, merge는 자동화하지 않는다.

## README 업데이트

README에 “초보자용 실행 방법” 섹션을 추가해줘.

예:

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading

./scripts/start_server.sh
./scripts/status.sh
./scripts/tick.sh
./scripts/analyze.sh