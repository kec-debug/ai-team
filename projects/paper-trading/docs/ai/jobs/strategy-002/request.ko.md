# 작업 ID
strategy-002

# 작업명
두 번째 paper 전략 추가 — Opening Range Breakout

기존 `PremarketGapVolumeBreakout` 전략 위에, 정규장 시작 후 일정 시간 동안의 opening range high 를 돌파하는 후보를 만드는 두 번째 전략을 추가한다. 실주문이 아니라 paper trading 검증 범위 확장.

## 목표

- 정규장 (`Session.REGULAR`) 에서 opening range high 돌파 시 long 후보 생성.
- volume confirmation (`relative_volume`) 과 VWAP confirmation (optional) 추가.
- spread 넓음 / stale quote / non-paper / non-US / opening range 데이터 부재 모두 blocker.
- 전략은 non-executable `OrderIntent` (LIMIT BUY) 만 생성. RiskEngine / OMS / broker 호출 0.
- `StrategyInput` 에 `opening_range_high`, `opening_range_low`, `vwap` optional 필드 추가 (default `None`, 후방 호환).

## 절대 하지 말 것

- live trading / 실주문 / KIS 추측 / 외부 HTTP lib / OMS·RiskEngine 우회 / Strategy 의 broker 직접 호출 / `OrderType.MARKET` 가드 우회 / `OrderType.STOP` 도입 / `ALLOW_MARKET_ORDERS=true` 허용 / FX 변환 / `.env` 수정 / secret 노출 / GUI 수정 / 자동 git ops.

## 완료 기준

- Opening Range Breakout 전략 클래스 신규 + STRATEGY_NAMES 등록 + create_strategy 분기.
- breakout / volume / VWAP / spread / stale / session / market / live blocker 모두 회귀.
- LIMIT BUY only, MARKET 절대 생성 안 함.
- Strategy 의 `app.broker.*` 직접 import 0.
- 기존 회귀 0 건.
