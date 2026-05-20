# paper-002 — Implementation Patch

본 patch 는 roadmap-implementation-plan 의 Phase 2 으로 Claude 가 직접 구현 (사용자 "B" interpretation).

## 1. Files Changed

- `app/broker/paper.py` — `PaperBroker.__init__` 에 3 개 새 인자 추가 (`slippage_bps`, `market_impact_bps_per_pct_volume`, `max_spread_pct_for_fill`, 모두 default `Decimal("0")`). `tick()` 에 `_spread_blocks_fill(quote)` 게이트 + `_apply_slippage_and_impact(...)` 호출 추가. 두 helper 메서드 신규.
- `tests/test_paper_broker_realism.py` (NEW) — 13 테스트.

## 2. Implementation Summary

- **Slippage (bps)**: BUY → `price * (1 + bps/10000)`. SELL → `price * (1 - bps/10000)`. Default 0 = unchanged.
- **Market impact**: `bps_per_pct_volume * (fill_qty / quote.volume * 100)` 이 base slippage 에 추가. Default 0 = unchanged.
- **Spread guard**: `max_spread_pct_for_fill > 0` 이고 `(ask - bid) / last > threshold` 일 때 tick 단위로 fill 거부. Default 0 = guard 비활성.
- **Multi-tick partial fill**: 기존 `_open_orders` 잔여 quantity 업데이트 로직이 이미 지원 — 회귀 테스트로 명시적으로 잠금.
- **Backward compatibility**: 모든 새 인자 default `Decimal("0")` → 기존 호출자 (PaperEngine / server.py / 모든 기존 테스트) 영향 없음.

## 3. Safety Confirmation

- `OrderType.MARKET` 3중 가드 / `ALLOW_MARKET_ORDERS=true` reject / kill switch 변경 없음.
- `OrderType.STOP` 미도입.
- FX 변환 도입 없음. Fill.currency 는 quote.currency 그대로 (통화별 분리 보존 — 회귀 테스트).
- KIS / live broker 의존성 없음.
- 외부 HTTP 라이브러리 import 없음.
- `.env` / `.env.example` / `app/config.py` 무변동 (새 env 변수 없음, 인자만 PaperBroker 생성자 수준에서).
- GUI / `app/api/*` 무변동.
- Strategy / Agent / LLM 의 broker 직접 호출 경로 추가 없음.

## 4. Test Results

```text
$ .venv/bin/python -m compileall app tests
PASS

$ .venv/bin/python -m pytest -p no:cacheprovider tests/test_paper_broker_realism.py
13 passed in 0.03s

$ .venv/bin/python -m pytest -p no:cacheprovider
501 passed in 0.75s  ← Phase 1 베이스라인 488 + new 13
```

## 5. Remaining TODOs

- 사용자가 새 PaperBroker 옵션을 실제로 활성화하려면 `app/api/server.py` 의 PaperBroker 생성자 호출 site 에서 settings 또는 env 기반 값을 넘겨야 함 — server.py 가 GUI 인접이므로 별 micro-job 으로 분리 권고.
- 다양한 시장 시나리오 (개장 직후 wide spread, 마감 직전 thin liquidity 등) 의 시나리오 회귀 테스트는 별 job 으로.

Verdict: READY FOR REVIEW.
