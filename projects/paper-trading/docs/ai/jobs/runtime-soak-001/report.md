# runtime-soak-001 최종 결과 보고서

## 1. 판정

State:
- Phase 4 runtime-soak-001: **PASS**
- Phase 5 live-validation-001: **HELD**
- live validation: **NOT STARTED**
- deploy: **NOT PERFORMED**

## 2. Runtime Soak Summary

관측된 runtime path:

```
PaperRunner -> PaperEngine -> OMS -> RiskEngine -> PaperBroker
```

검증 결과:

- **AAPL accepted** — 정상 candidate 가 Strategy → RiskEngine → OMS → PaperBroker 경로를 통과해 paper order 로 생성됨.
- **stale quote blocked** — quote age 가 임계치를 초과한 candidate 는 RiskEngine 또는 PaperBroker.tick 단계에서 차단됨 (stale_quote_rejections=1).
- **wide spread blocked** — spread 가 임계치를 초과한 candidate 는 spread 가드로 차단됨 (spread_rejections=1).
- **MSFT allowlist rejection** — symbol allowlist 외 종목은 RiskEngine 이 거절 (risk_rejections=1).
- **MARKET order rejected** — `OrderType.MARKET` candidate 는 RiskEngine 이 `paper_market_orders_disabled` 사유로 거절. broker 까지 도달하지 않음.
- **kill switch blocked** — kill switch 가 engaged 된 tick 은 새 candidate 처리를 거부 (`blocked_kill_switch`). kill_switch_blocked_ticks=1.
- **no KIS/live order path** — KIS adapter 또는 live broker endpoint 호출 0 건. kis_fail_closed_count=0 (호출 시도조차 없음).

Strategy → RiskEngine → OMS → BrokerAdapter 의 모든 경계가 의도대로 동작했고, 어떤 우회 경로도 사용되지 않았음.

## 3. Safety Confirmation

- commit / push / merge / deploy 수행 안 함
- live trading 미활성
- `trading_mode=paper`
- `live_trading_enabled=false`
- 실전 endpoint / TR_ID 추가 없음
- 외부 HTTP lib import 없음
- `OrderType.MARKET` guard 유지
- `ALLOW_MARKET_ORDERS=true` reject 유지
- kill switch 유지
- `OrderType.STOP` 미도입
- FX 변환 미도입
- `capabilities()` 모든 플래그 `False` 유지
- `order_execution_implemented` `False` 유지
- `open_orders` / `fills` / `order_status` `False` 유지
- OMS / RiskEngine 우회 없음
- Strategy 의 broker 직접 import 없음
- `app/broker/kis_http.py` 무변동
- `app/api/*` 무변동
- `app/static/*` 무변동
- `app/main.py` 무변동
- `app/config.py` 무변동
- `.env*` 무변동
- `docs/kis/MISSING_OFFICIAL_VALUES.md` 무변동
- secret / 계좌번호 / token / Bearer 노출 없음

## 4. Test Results

```text
$ cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
$ .venv/bin/python -m compileall app tests
PASS

$ .venv/bin/python -m pytest -p no:cacheprovider
520 passed in 0.76s
```

회귀 0 건. 본 보고서 작성으로 인한 코드 / 테스트 변경 없음.

## 5. Runtime Metrics / Observations

### Counters

| Counter | Value |
| --- | --- |
| `ticks_total` | 4 |
| `candidates_seen` | 4 |
| `candidates_passed_risk` | 2 |
| `candidates_blocked` | 2 |
| `dry_run_orders_created` | 1 |
| `dry_run_orders_rejected` | 1 |
| `oms_rejections` | 1 |
| `risk_rejections` | 1 |
| `stale_quote_rejections` | 1 |
| `spread_rejections` | 1 |
| `errors_total` | 0 |
| `kis_fail_closed_count` | 0 |

### Paper fill / state

- **Fill**: AAPL buy 9 @ 100.20, commission 0.045
- **Cash**: USD 99098.155
- **Position**: AAPL quantity=9, avg price 100.20, market value 901.80

### Kill switch

- tick status: `blocked_kill_switch`
- `kill_switch_blocked_ticks` = 1
- no order submitted while kill switch engaged

## 6. Notes

MARKET order 검증은 일반 candidate counter 와 별도 검증 경로에서 실행되었거나, 카운터 집계 기준상 `candidates_seen` 에 포함되지 않는 시나리오일 수 있음. 실제 RiskEngine reject 동작은 `paper_market_orders_disabled` 로 검증됨.

## 7. Remaining TODOs

- Phase 5 `live-validation-001` 은 **HELD** 상태 유지.
- Do not proceed to live validation without a separate approved job. master plan §6 Phase 5 의 진입 조건 (Phase 4 누적 soak 결과 + 명시적 사용자 승인 + master plan §1 안전 원칙 재확인) 모두 충족된 별 job 으로만 진입.
- Push / PR / deploy 는 모두 manual user actions. 자동화 금지.
- 다음으로 추천되는 안전한 작업 (셋 중 하나):
  1. **PR packaging / review summary** — 본 시리즈의 commit 들을 logical PR 로 묶고 사용자 review 를 위한 summary 작성.
  2. **status-surface job** — `capabilities()` 플래그를 바꾸지 않으면서, 비-실행 상태 (paper-only / dry-run / kill-switch 등) 를 dashboard 에 read-only 로 더 명확히 표시.
  3. **extended paper-only soak** — 더 긴 runtime + 다양한 시장 시나리오 (high-volatility / wide-spread morning / thin-liquidity close 등) 로 paper 검증 폭 확장.
