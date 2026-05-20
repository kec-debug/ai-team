# 작업 ID
paper-002

# 작업명
Paper fill 현실성 강화 — partial fill 시퀀스 / 슬리피지 / market impact / spread 가드

paper-001 의 `PaperBroker.tick(quote)` 기반 fill 시뮬레이션 위에, 장시간 paper trading 검증의 신뢰도를 높이기 위한 현실성 강화 옵션을 추가한다.

## 목표

- PaperBroker 생성자에 새 옵션 (모두 default 0 = backward compatible) 추가:
  - `slippage_bps` — 기본 basis-point 슬리피지 (BUY 가격↑, SELL 가격↓)
  - `market_impact_bps_per_pct_volume` — fill_qty / quote.volume 비율에 비례한 추가 슬리피지
  - `max_spread_pct_for_fill` — (ask-bid)/last 가 이보다 크면 체결 거부 (0 = 비활성)
- 한 주문이 여러 tick 에 걸쳐 partial fill 누적 (이미 구조는 있음 — 회귀 테스트로 명시).
- FX 변환 도입 없음. 통화별 분리 보고만.
- 모든 변경은 default 동작에서 backward compatible.

## 절대 하지 말 것

- live trading / 실주문 / KIS 추측 / 외부 HTTP lib / OMS·RiskEngine 우회 / Strategy·Agent broker 직접 호출 / `OrderType.MARKET` 가드 우회 / `OrderType.STOP` 도입 / `ALLOW_MARKET_ORDERS=true` 허용 / FX 변환 / `.env` 수정 / secret 노출 / GUI 수정 / 자동 git ops.

## 완료 기준

- 슬리피지·impact·spread 가드 동작 검증.
- multi-tick partial fill 누적 검증.
- BUY / SELL 양방향 검증.
- 통화별 분리 (HKD 등) 보존.
- 기존 paper 엔진 e2e 회귀 0건.
