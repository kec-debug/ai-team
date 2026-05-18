# 작업 ID
paper-001-gui

# 작업명
Paper trading 계좌 / 체결 / PnL 대시보드 노출

paper-001 v2에서 내부 paper trading 엔진이 구현되었다.

현재 백엔드에는 PaperAccount, PaperJournal, PaperEngine, Fill 모델, 통화별 cash, realized/unrealized PnL, partial fill, paper broker tick 흐름이 들어갔다.

하지만 대시보드에서는 아직 이 정보를 사람이 보기 쉽게 확인하기 어렵다.

이번 작업의 목표는 기존 `/dashboard`에 paper trading 계좌 상태와 체결/거래 기록, 통화별 PnL을 보기 쉽게 노출하는 것이다.

## 목표

- `/dashboard`에 PaperAccount 상태를 표시한다.
- 통화별 cash balance를 표시한다.
- portfolio positions를 표시한다.
- realized PnL / unrealized PnL을 표시한다.
- 최근 fills / trades / orders journal을 표시한다.
- PaperEngine / PaperJournal 상태를 표시한다.
- 기존 dry-run 상태 카드와 충돌하지 않게 배치한다.
- 초보자가 브라우저에서 현재 paper 계좌 상태를 바로 확인할 수 있게 만든다.

## 표시할 정보

가능한 범위에서 아래 정보를 대시보드에 추가한다.

### 1. Paper Account

- starting cash
- current cash by currency
- buying power 또는 available cash가 있으면 표시
- currency별 분리 표시
- FX 변환은 하지 않는다.

### 2. Portfolio / PnL

- positions count
- symbol
- quantity
- average price
- market value
- realized PnL
- unrealized PnL
- currency
- total PnL이 있다면 통화별로만 표시한다.

### 3. Paper Journal

- recent orders
- recent fills
- recent trades
- fill price
- fill quantity
- side
- timestamp
- status
- commission이 있으면 표시

### 4. Paper Engine 상태

- paper engine enabled
- journal enabled
- persistent log path가 있으면 마스킹/안전하게 표시
- last fill time
- last trade time

## 절대 하지 말 것

- live trading 활성화 금지
- 실제 broker API 호출 금지
- KIS endpoint/TR ID/payload/header 추측 금지
- KIS 주문/시세/계좌 HTTP 구현 금지
- Strategy, Agent, LLM이 broker를 직접 호출하는 경로 추가 금지
- executable order를 Agent나 LLM이 생성하게 만들지 말 것
- `ALLOW_MARKET_ORDERS=true` 허용 금지
- `OrderType.MARKET` 3중 가드 우회 금지
- FX 변환 함수나 환율 상수 도입 금지
- `.env` 읽기/수정 금지
- app key, app secret, 계좌번호, access token, Bearer token 노출 금지
- 자동 git commit / push / merge / deploy 금지
- dashboard에 live trading 활성화 버튼 추가 금지
- dashboard에 market order 허용 버튼 추가 금지

## 수정 가능 파일

GUI 전용 job이므로 아래 파일 수정 가능하다.

- projects/paper-trading/app/api/routes.py
- projects/paper-trading/app/api/server.py
- projects/paper-trading/app/static/dashboard.html
- projects/paper-trading/app/static/*
- projects/paper-trading/tests/*
- projects/paper-trading/README.md
- docs/ai/jobs/paper-001-gui/patch.md

필요하면 paper account/journal 정보를 읽기 위한 read-only status helper는 추가 가능하다.
단, paper engine의 주문/체결 로직 자체는 바꾸지 않는다.

## 완료 기준

- `/dashboard`에서 paper account cash가 보인다.
- `/dashboard`에서 통화별 cash / PnL이 보인다.
- `/dashboard`에서 최근 fills/trades/journal이 보인다.
- secret/account/token 원문이 화면에 노출되지 않는다.
- live trading 버튼이 없다.
- market order 허용 버튼이 없다.
- 기존 dry-run 상태 UI가 깨지지 않는다.
- 기존 API 응답이 후방 호환된다.
- 테스트가 추가된다.
- 전체 테스트가 통과한다.

## 검증

아래를 실행한다.

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider