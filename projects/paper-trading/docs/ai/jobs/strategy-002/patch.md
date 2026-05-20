# strategy-002 — Implementation Patch

본 patch 는 roadmap-implementation-plan 의 Phase 3 으로 Claude 가 직접 구현 (사용자 "B" interpretation).

## 1. Files Changed

- `app/strategy/opening_range_breakout.py` (NEW) — `OpeningRangeBreakoutStrategy` 클래스. `evaluate(snapshot)` 가 정규장 + opening range 돌파 + volume + VWAP + spread + freshness gate 통과 시 `OrderIntent(LIMIT BUY)` 생성.
- `app/strategy/__init__.py` — `STRATEGY_NAMES` 에 `"opening_range_breakout"` 추가, `create_strategy` 분기 추가, `__all__` 갱신.
- `app/domain/market.py` — `StrategyInput` 에 optional `opening_range_high`, `opening_range_low`, `vwap` 필드 (default `None`, 후방 호환) + positive-when-provided validator.
- `tests/test_strategy_opening_range_breakout.py` (NEW) — 19 테스트 (registry / happy path / 모든 blocker / score / Strategy-broker isolation / MARKET 금지 회귀).

## 2. Implementation Summary

ORB 통과 조건 (전부 충족 시 LIMIT BUY intent 생성):

- `trading_mode == PAPER` AND `live_trading_enabled == False`
- `market == "US"`
- `session == REGULAR`
- `opening_range_high` 제공됨 AND `current_price >= opening_range_high * (1 - tolerance)`
- `relative_volume` 제공됨 AND `>= premarket_min_relative_volume` (`relative_volume_missing` 도 blocker)
- (옵션) `vwap` 제공되면 `current_price >= vwap`
- `(ask - bid) / current_price <= premarket_max_spread_pct`
- quote age `<= premarket_max_quote_age_seconds`

Score: `min(1.0, max(0, (current_price - opening_range_high) / opening_range_high * 10))` — 돌파 폭이 클수록 1.0 으로 수렴.

`StrategyInput` 확장 3 필드 모두 optional + default `None` 이라 기존 fixture / 호출자 영향 없음. 기존 `PremarketGapVolumeBreakout` 회귀 0 건.

## 3. Safety Confirmation

- Strategy 가 `app.broker.*` import 0 (테스트 회귀로 강제).
- Strategy 가 OMS / RiskEngine 인스턴스화·호출 0 (`OMS(`, `RiskEngine(`, `.place(`, `.evaluate_intent(` 모두 부재 — 테스트 회귀).
- `OrderType.MARKET` 생성 0 (모든 변종에서 `LIMIT` 만 생성됨을 회귀 테스트로 단언).
- `OrderType.STOP` 도입 없음.
- live trading 활성화 / 실 broker 호출 / KIS 의존성 0.
- FX 변환 도입 없음.
- 외부 HTTP 라이브러리 / `openpyxl` / `pandas` import 없음.
- `.env` / `.env.example` / `app/config.py` 무변동 (기존 `premarket_*` settings 재사용 — 새 env 변수 없음).
- GUI / `app/api/*` / `app/static/*` 무변동.
- 기존 `PremarketGapVolumeBreakout` 동작 무변동.

## 4. Test Results

```text
$ .venv/bin/python -m compileall app tests
PASS

$ .venv/bin/python -m pytest -p no:cacheprovider tests/test_strategy_opening_range_breakout.py
19 passed in 0.03s

$ .venv/bin/python -m pytest -p no:cacheprovider
520 passed in 0.76s  ← Phase 2 베이스라인 501 + new 19
```

## 5. Remaining TODOs

- ORB 전략을 server.py 의 default 또는 옵션 strategy 로 활성화하려면 별 micro-job 필요 (GUI 인접).
- Opening range 데이터 source (5/10/15 min from open) 를 KIS 시세 / synthetic feed 와 연결하는 작업은 별 job.
- 다중 전략 동시 평가 / strategy selection 로직은 별 job.

Verdict: READY FOR REVIEW.
