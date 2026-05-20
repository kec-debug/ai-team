# roadmap-implementation-plan — Implementation Patch (Phase 1 + 2 + 3 sequential)

본 patch 는 사용자의 "B" interpretation 요청 (Phase 1→2→3 sequential 자동 실행) 결과다. 별도 Codex pass 없이 Claude 가 직접 구현 + 인-conversation 테스트 검증을 수행했다. **commit / push / merge / deploy 는 수행하지 않음** (안전 규칙 §"Hard Stops" 그대로 적용).

각 phase 의 상세 patch 는 별도 디렉터리에 작성:

- `docs/ai/jobs/api-orders-paper-003-query/patch.md` (Phase 1)
- `docs/ai/jobs/paper-002/patch.md` (Phase 2)
- `docs/ai/jobs/strategy-002/patch.md` (Phase 3)

## 1. 통합 결과 요약

| Phase | Job ID | 신규 테스트 | 누적 pytest | 상태 |
| --- | --- | --- | --- | --- |
| baseline (전) | — | — | 458 passed | — |
| Phase 1 | `api-orders-paper-003-query` | +30 | 488 passed | PASS |
| Phase 2 | `paper-002` | +13 | 501 passed | PASS |
| Phase 3 | `strategy-002` | +19 | 520 passed | PASS |

최종: **520 passed, 0 failed**. compileall PASS. 안전 grep clean.

## 2. 수정된 파일 (모든 phase 통합)

### Phase 1 — KIS query

- `app/broker/kis.py` — query transport 3 종 + 상수 + `KisBroker.get_open_orders` / `get_fills` / `get_order_status` 본문 + `_fetch_ccnl_rows` helper.
- `tests/test_kis_paper_order_query.py` (NEW) — 30 tests.
- `tests/test_broker_interface.py` (narrow) — 3 함수의 NotImplementedError 단언을 `KisOrderRejectedError("authentication_required")` 로 갱신.
- `tests/test_kis_http_boundaries.py` (narrow) — `test_cancel_replace_queries_fail_closed` 의 `get_*` 단언 갱신. cancel/replace 단언 무변동.
- `tests/test_kis_paper_order_cancel_replace.py` (narrow) — `test_get_*_still_not_implemented_after_cancel_replace` 3 함수 이름과 단언 갱신.

### Phase 2 — paper fill realism

- `app/broker/paper.py` — `PaperBroker.__init__` 에 `slippage_bps` / `market_impact_bps_per_pct_volume` / `max_spread_pct_for_fill` 추가 (모두 default 0), `tick()` 에 spread guard + slippage 적용, 2 helper 메서드 신규.
- `tests/test_paper_broker_realism.py` (NEW) — 13 tests.

### Phase 3 — Opening Range Breakout

- `app/strategy/opening_range_breakout.py` (NEW) — `OpeningRangeBreakoutStrategy`.
- `app/strategy/__init__.py` — `STRATEGY_NAMES` 확장, `create_strategy` 분기, `__all__` 갱신.
- `app/domain/market.py` — `StrategyInput` 에 optional `opening_range_high` / `opening_range_low` / `vwap` 필드 추가 (default None, 후방 호환).
- `tests/test_strategy_opening_range_breakout.py` (NEW) — 19 tests.

### Job 디렉터리 (NEW)

- `docs/ai/jobs/api-orders-paper-003-query/` — request.ko.md (이전 turn 에 사용자가 준비) + patch.md.
- `docs/ai/jobs/paper-002/` — request.ko.md + patch.md.
- `docs/ai/jobs/strategy-002/` — request.ko.md + patch.md.

## 3. 안전 규칙 준수

- **commit / push / merge / deploy 수행 안 함** — 모든 변경은 working tree 에 남고 사용자가 직접 logical commit 으로 분할.
- live trading 활성화 없음. 실전 endpoint / TR_ID 추가 없음.
- KIS endpoint / TR ID / payload / response field 추측 없음 — Phase 1 의 모든 인용이 catalog §4.7 / §4.7.1 의 `Confirmed: yes` 행에서.
- 외부 HTTP 라이브러리 (`requests` / `httpx` / `aiohttp` / `urllib3` / `openpyxl` / `pandas`) import 없음.
- `OrderType.MARKET` 3중 가드 / `ALLOW_MARKET_ORDERS=true` reject / kill switch 변경 없음.
- `OrderType.STOP` 도입 없음.
- FX 변환 도입 없음.
- OMS / RiskEngine 경계 약화 없음.
- Strategy / Agent / LLM 의 broker 직접 호출 추가 없음.
- `app/broker/kis_http.py` 무변동.
- `app/api/*` / `app/static/*` / `app/main.py` / `app/config.py` 무변동.
- `.env` / `.env.example` 무변동. 새 env 변수 0.
- `docs/kis/MISSING_OFFICIAL_VALUES.md` 무변동.
- secret / 계좌번호 / token / Bearer 노출 없음.
- `capabilities()` 의 모든 플래그 `False` 유지. `healthcheck()["order_execution_implemented"]` `False` 유지.
- 기존 회귀 0 건 깨짐 — narrow 갱신은 NotImplementedError 단언만 새 fail-closed 동작에 맞춰 정정.

### 안전 grep (재실행 결과)

```text
$ grep -rnE "^(from|import) (requests|httpx|aiohttp|urllib3|openpyxl|pandas)" app tests
<no output>

$ grep -rn "TTTS3035R\|TTTS3018R\|TTTT3039R" app
<no output>

$ grep -rnE "^\s*(from|import)\s+app\.broker\." app/strategy
<no output>
```

## 4. 통합 테스트 결과

```text
$ cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
$ .venv/bin/python -m compileall app tests
PASS

$ .venv/bin/python -m pytest -p no:cacheprovider
520 passed in 0.76s
```

각 phase 단독 결과는 각 phase 의 `patch.md` 참고.

## 5. 사용자 후속 작업

본 patch 가 작성됐을 뿐 commit / push / merge / deploy 는 자동 수행되지 않았다. 사용자가 직접:

1. (선택) `git diff` / `git status` 로 변경 범위 검토.
2. logical commit 분리 권고:
   ```bash
   # Phase 1
   git add projects/paper-trading/app/broker/kis.py \
           projects/paper-trading/tests/test_kis_paper_order_query.py \
           projects/paper-trading/tests/test_broker_interface.py \
           projects/paper-trading/tests/test_kis_http_boundaries.py \
           projects/paper-trading/tests/test_kis_paper_order_cancel_replace.py \
           projects/paper-trading/docs/ai/jobs/api-orders-paper-003-query/
   git commit -m "implement KIS paper inquire-ccnl query methods (VTTS3035R)"

   # Phase 2
   git add projects/paper-trading/app/broker/paper.py \
           projects/paper-trading/tests/test_paper_broker_realism.py \
           projects/paper-trading/docs/ai/jobs/paper-002/
   git commit -m "paper broker realism: slippage / market impact / spread guard"

   # Phase 3
   git add projects/paper-trading/app/strategy/opening_range_breakout.py \
           projects/paper-trading/app/strategy/__init__.py \
           projects/paper-trading/app/domain/market.py \
           projects/paper-trading/tests/test_strategy_opening_range_breakout.py \
           projects/paper-trading/docs/ai/jobs/strategy-002/
   git commit -m "add opening range breakout strategy (paper, LIMIT only)"

   # roadmap doc bundle
   git add projects/paper-trading/docs/ai/jobs/roadmap-implementation-plan/
   git commit -m "docs: roadmap implementation plan (phase 1-3 patch summary)"
   ```
3. push / PR / deploy 는 사용자 명시 승인 후만.

## 6. Remaining TODOs (다음 phase)

- **Phase 4 — `runtime-soak-001`**: 장시간 paper trading runner + counter / summary report / kill switch / dashboard read-only 노출. (paper-002 의 realism + strategy-002 의 ORB 위에서 의미 있는 soak data 생성 가능.)
- **Phase 5 — `live-validation-001`** (HELD): Phase 4 의 누적 soak 결과 + 명시적 사용자 승인 + master plan §1 안전 원칙 재확인 후만.
- 마스터 플랜의 ROADMAP_STATUS.md 갱신 제안은 별 micro-job 으로.

Verdict: READY FOR REVIEW (인-conversation 자체 검증 완료, commit 사용자).
