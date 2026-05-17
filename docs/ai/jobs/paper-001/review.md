# Review — paper-001: 내부 paper trading MVP 확장판

## Verdict

**REQUEST CHANGES** (high-severity 1건 + medium-severity 2건 + low-severity 5건. 안전 영향은 paper-only로 제한적이나 plan §2.3에서 명시적으로 채택한 안전 대안이 깨졌고 RiskEngine notional 가드가 MARKET에 대해 무력화됨.)

전체적으로 6개 기능 모두 구현되었고 301 PASS, 안전 grep 6/6 clean, KIS/Alpaca/dry-run/GUI/Strategy/OMS manager/.env 미접촉. 기본값(`ALLOW_PAPER_MARKET_ORDERS=false`)에선 노출 0건이지만, flag 활성 시 RiskEngine의 max notional 검증이 MARKET 주문에 한해 우회된다. 한 번 수정 후 재제출 권장.

## 검증된 사실 (직접 확인)

### 1. 안전 grep (자체 재실행, 6/6 clean)

| 라벨 | 결과 |
| --- | --- |
| `fx-grep` (FX 변환 함수/환율 상수) | clean |
| `http-lib-grep` (requests/httpx/aiohttp/urllib3) | clean |
| `secret-grep` (PSNFD/PKID/AKIA/sk-/ghp_/Bearer eyJ/appkey=/appsecret=) | clean |
| `gui-grep` (`app/api/`, `app/static/`, `app/main.py`) | clean |
| `dry-run-grep` (`dry_run.py`, `dry_run_report.py`, `paper_runner.py`) | clean |
| `kis-grep` (broker/{base, kis*, alpaca_paper}.py) | clean |

### 2. 테스트 (자체 재실행)

`projects/paper-trading/.venv/bin/python -m pytest -p no:cacheprovider` → **301 passed in 0.48s**. 회귀 0건.

### 3. 미접촉 invariant (자체 grep + diff stat)

- `KisBroker`/`KisMarketDataClient`/`KisAccountClient`/`KisAuthClient`/`KisHttpClient`/`KisHttpTransport` 본문 미접촉 (`app/broker/kis.py`, `kis_http.py`, `kis_token_cache.py`, `kis_quote_mapper.py` 변경 0건).
- `app/broker/{base.py, alpaca_paper.py}` 미접촉.
- `app/api/{server.py, routes.py}`, `app/static/*`, `app/main.py` 미접촉.
- `app/runtime/{dry_run.py, dry_run_report.py, paper_runner.py}` 미접촉.
- `app/strategy/*`, `app/oms/manager.py` 미접촉.
- `.env`, `.gitignore`, `docs/kis/*`, `prompts/*`, `scripts/*` 미접촉.
- `OrderType` enum에 `MARKET` 추가됐고, RiskEngine 분기에서 `ALLOW_PAPER_MARKET_ORDERS=true` AND `TradingMode=PAPER` AND `live_trading_enabled=False` 3중 가드 작동(확인: `app/risk/engine.py:27-34`).
- 기존 `ALLOW_MARKET_ORDERS=true` load_settings 거절 유지(`app/config.py:110-113` unchanged).
- `live_trading_enabled=False` 기본 유지.

### 4. 통합 동작 (matrix 테스트 자체 검토)

`tests/test_paper_001_simulation_matrix.py`가 LIMIT/MARKET/STOP_LIMIT × BUY/SELL 6개 케이스를 parametrize로 검증. 모두 통과.

## Findings (severity 순)

### 1. HIGH — RiskEngine notional 가드가 MARKET 주문에 무력화

**위치**: `app/domain/orders.py:14` (`limit_price: Decimal = Decimal("0")`) + `app/domain/orders.py:25` (`if self.order_type != OrderType.MARKET and self.limit_price <= 0`) + `app/risk/engine.py:42` (`intent.quantity * intent.limit_price > self._settings.max_order_notional_usd`).

**관찰**:

- `OrderIntent`의 `limit_price`가 default `Decimal("0")`이고, MARKET 주문은 `__post_init__`에서 `limit_price > 0` 검증을 skip한다.
- 결과적으로 `OrderIntent("AAPL", Side.BUY, 1_000_000, OrderType.MARKET)` (limit_price 미설정 → 0)이 생성 가능.
- RiskEngine의 notional ceiling 검사: `1_000_000 * Decimal("0") = 0`, `0 > max_order_notional_usd(5000)` → **False** → 통과.
- 즉, `ALLOW_PAPER_MARKET_ORDERS=true` 활성 시 **임의 크기의 MARKET 주문이 notional 가드를 우회**.
- `tests/test_models.py:24-27`이 이 동작을 명시적으로 단정(`OrderIntent(..., MARKET).limit_price == Decimal("0")`). 즉 의도된 deviation이지 우발적 버그 아님.

**Plan 대비 deviation**:

- `plan.md` §2.3 명시: "**더 안전한 대안은 `OrderIntent.limit_price`를 MARKET에서도 expected fill price로 강제하고, RiskEngine notional 검증을 그대로 수행하는 것. 본 plan은 이 대안 채택. MARKET intent에도 `limit_price>0` 요구.**"
- Codex는 반대 방향(limit_price 선택 사항)을 채택.

**영향 평가**:

- 안전 영향: paper-only 컨텍스트 한정. 실 자금 위험 0. 하지만 paper 시뮬레이션 결과가 비현실적으로 부풀려질 수 있음(사용자가 자기 알고리즘이 1M주를 한 번에 체결할 수 있다고 오해할 위험).
- 정책 영향: paper-001의 "Strategy → RiskEngine → OMS → PaperBroker 통과" invariant 정신은 유지되지만, RiskEngine의 한 검사(notional)가 MARKET에서만 실효 없음.
- 향후 위험: MARKET 시뮬이 작동하면 사용자가 이를 실시간 의사결정 입력으로 신뢰할 가능성. notional 가드 부재가 의사결정 오염원이 됨.

**권장 수정**:

옵션 A (plan 그대로 따르기): `OrderIntent.limit_price` default 제거, `__post_init__`에서 `limit_price > 0`을 MARKET에도 적용. caller가 expected fill price를 채워 보내야 RiskEngine notional이 의미 있게 동작.

옵션 B (RiskEngine에 MARKET 전용 가드 추가): MARKET 주문은 `intent.quantity * quote.last`(혹은 별 expected_price 필드)로 notional 계산. 단 RiskEngine이 quote에 접근하지 않으므로 OrderIntent에 `expected_fill_price` 필드 추가 필요. 옵션 A보다 침습적.

**옵션 A 권장**. 수정 분량 ~5 LoC + `test_market_order_intent_does_not_require_limit_price` 단정 반전.

### 2. MEDIUM — `Quote.session=None`이 PaperBroker fill을 차단

**위치**: `app/broker/paper.py` `tick()` — `if quote.session not in self._allowed_sessions: return []`.

**관찰**:

- `Quote.session`은 default `None`. `None not in {Session.REGULAR}` → True → return [] (fill 0건).
- 즉 session을 명시하지 않은 quote는 영원히 fill 안 됨.

**Plan 대비 deviation**:

- `plan.md` §2.6 명시: "**quote.session is None (모르면) → broker 허용 (backward compat).**"

**영향 평가**:

- 신규 테스트는 모두 `session=Session.REGULAR`을 명시해 통과. 따라서 회귀 없음.
- 하지만 외부 caller가 `Quote(..., source="x")`로 생성하면 session=None → 모든 fill 침묵 거절. 디버깅 어려움.
- backward compat invariant 깨짐.

**권장 수정**:

```python
if quote.session is not None and quote.session not in self._allowed_sessions:
    return []
```

`tests/test_paper_001_simulation_matrix.py` 또는 별도 broker session 테스트에 `session=None`이 허용되는지 단정 1개 추가.

### 3. MEDIUM — `PaperAccount`가 `PortfolioService`를 갖지 않음 (split responsibility)

**위치**: `app/portfolio/account.py:13` — `cash: dict[str, Decimal]`만 보관. `portfolio` 필드 부재.

**관찰**:

- `PaperAccount.apply_fill(fill)`는 cash만 갱신. positions는 `PortfolioService.apply_trade(fill)`에서 별도 갱신.
- 두 호출은 `PaperEngine.on_quote`가 순차로 수행하므로 정상 경로에서는 일관.
- 하지만 raw `PaperAccount`를 broker fills와 직접 wire하면 positions가 빈 채로 남음.

**Plan 대비 deviation**:

- `plan.md` §2.1: `PaperAccount.portfolio: PortfolioService` + `apply_fill`이 `portfolio.apply_fill` 위임.
- Codex: PaperAccount = cash 전용 컨테이너. PortfolioService 통합은 PaperEngine 책임으로 이전.

**영향 평가**:

- PaperEngine만 사용하는 한 안전. 그러나 PaperAccount 단독 사용 시 portfolio drift 가능.
- 단독 사용 사례가 코드에 없음(테스트 포함). 잠재적 함정.

**권장 수정**:

- 옵션 A: `PaperAccount`에 `portfolio: PortfolioService` 필드 추가하고 `apply_fill`에서 위임 (plan 따르기). PaperEngine은 `account.apply_fill`만 호출하면 portfolio도 함께 갱신.
- 옵션 B: 현재 분리 구조 유지하되 `PaperAccount` docstring에 "cash-only, use PaperEngine for full bookkeeping" 명시 + 단독 사용 시 분리된 부분 명시.

옵션 A가 plan과 일치하고 안전. 옵션 B는 현재 코드 유지 + 문서화.

### 4. LOW — `PaperEngine.submit_intents` 누락

**위치**: `app/runtime/paper_engine.py` — `on_quote`, `mark_quote`, `cash_by_currency`만 노출.

**관찰**: plan §2.9는 `submit_intents(intents)` 메서드(OMS 호출 + journal 기록)를 포함. Codex는 fill 처리만 PaperEngine에 두고 intent 제출은 외부에 맡김.

**영향**: 외부 caller가 OMS를 직접 호출해야 함. journal에 "submitted" 이벤트 기록 없음(rejected only).

**권장**: 다음 mvp에서 추가하거나 본 review에서 함께 보강. 안전 영향 0, UX 차이만.

### 5. LOW — LIMIT fill 가격 = `quote.ask/bid` (plan: `order.limit_price`)

**위치**: `app/broker/paper.py` `_execution_price()`.

**관찰**: LIMIT BUY는 `quote.ask` (≤ limit_price 시), LIMIT SELL는 `quote.bid` (≥ limit_price 시). 매수자는 limit보다 비싸게 못 사고 매도자는 limit보다 싸게 못 팜 → 안전.

**Plan 대비 deviation**: plan §2.2는 `fill_price = order.limit_price` (결정론).

**영향**: 실제 시장 행동에 더 가깝지만 결정론적 테스트에는 덜 친화적. 안전 정책상으로는 buyer never overpays / seller never undersells가 유지되므로 OK.

**권장**: 인정. 본 review는 통과. 추후 paper-001 변형에서 정책 선택권 부여 가능.

### 6. LOW — STOP_LIMIT 트리거 상태가 tick 간 유지 안 됨

**위치**: `app/broker/paper.py` `_execution_price()` STOP_LIMIT 분기.

**관찰**: 매 tick마다 stop 조건과 limit 조건 둘 다 동시 만족해야 fill. 한 번 stop이 트리거되면 다음 tick에 limit만 평가하는 plan 의도와 다름.

**Plan 대비 deviation**: plan §2.2의 `_triggered_stops` 추적 미구현.

**영향**: 일부 현실적 stop+limit 시나리오(가격이 stop 위로 갔다가 다시 fillable 범위로 내려옴)에서 fill 안 됨. 안전 영향 0.

**권장**: 인정. paper-001 변형에서 보강 가능.

### 7. LOW — Partial fill 볼륨 budget이 tick 안에서 주문들에 의해 소진

**위치**: `app/broker/paper.py` `tick()` — `remaining_volume = max_fill_qty` 단일 budget을 모든 주문이 공유.

**관찰**: 한 tick에서 같은 심볼의 여러 주문이 있으면 첫 주문이 volume*ratio를 먼저 가져가고 나머지는 0.

**Plan 대비 deviation**: plan §2.2 pseudo-code는 주문별 독립 cap을 가정.

**영향**: 다중 주문 동시 보유 시 fill 분배가 plan과 다름. 안전 영향 0; 실 시장 행동에는 더 가까움(전체 거래량 한도).

**권장**: 인정. plan에 명시되지 않았으나 합리적 선택.

### 8. LOW — 필드 명명 `_by_currency` (plan: `_per_currency`)

**위치**: `PortfolioSnapshot.realized_pnl_by_currency`/`market_value_by_currency`/`unrealized_pnl_by_currency`.

**관찰**: 단순 명명 차이. 의미 동일.

**영향**: 0. 일관되게 적용됨.

**권장**: 인정.

## 누락된 테스트 / 잔존 위험

- **Finding #1 후속 보강 필요**: 옵션 A 수정 적용 시 `OrderIntent(..., MARKET)`이 `limit_price` 없이는 reject되는 단정 추가. RiskEngine notional 체크가 MARKET에 효과적인지 검증.
- **Finding #2 후속 보강 필요**: `session=None` quote가 broker에서 어떻게 처리되는지 단정.
- **Quote staleness 미래 timestamp 케이스**: `is_stale`의 `age < 0` 분기를 명시 검증하는 테스트 없음(`test_paper_001_simulation_matrix.py`에 staleness 케이스 1개 있으나 미래 timestamp 안 다룸).
- **Multi-currency end-to-end**: KRW 주문 cycle 통합 테스트가 matrix에 1줄로 포함되었으나 cash bucket 분리 + journal currency 전파 모두 통합으로 보증하는 명시적 e2e 테스트는 보강 여지.
- **PaperJournal `OrderLogEntry "submitted"` 부재**: plan §2.9 의도는 모든 intent submit/reject가 journal에 기록되는 것. Codex는 rejected only.

## File / line references (요청 review focus + scope)

| Focus | 위치 | 상태 |
| --- | --- | --- |
| 1. Paper 기본 + live 비활성 유지 | `app/config.py:103-108`, `app/domain/enums.py:6-9` | ✓ |
| 2. LLM/Agent의 executable order 경로 추가 없음 | grep `app/strategy/*` + `app/oms/*` 변경 0건 | ✓ |
| 3. 추천 agent는 `OrderIntent`만 | `app/oms/manager.py` 본문 변경 0건 | ✓ |
| 4. Executable order는 OMS만 | OMS 본문 변경 0건. `BrokerOrder` 생성 경로 OMS 내부 그대로 | ✓ |
| 5. Strategy → Risk → OMS → PaperBroker 통과 | RiskEngine MARKET 분기 추가, OMS/Strategy 본문 미접촉 | ✓ |
| 6. 실 broker API 호출 0건 | KIS/Alpaca client 본문 변경 0건 | ✓ |
| 7. 실 API key 0건 | `.env.example` 신규 변수 이름 + 한 줄 설명만, 실 키 패턴 grep 0건 | ✓ |
| 8. `.env` 읽기/수정 0건 | git status에 `.env` 부재. config.py도 `.env`를 직접 읽지 않고 dotenv 위임 | ✓ |
| 9. live 주문 실행 코드 0건 | RiskEngine MARKET 3중 가드 통과 시에만 승인. live=True 시 reject. | ✓ |
| 10. `OrderType.MARKET` 도입 가드 | RiskEngine `if intent.order_type == OrderType.MARKET:` 분기, default `ALLOW_PAPER_MARKET_ORDERS=False` | ✓ but **notional 우회 (Finding #1)** |
| 11. FX 변환 0건 | `equity_total_in_base_currency` 등 부재, fx-grep clean | ✓ |
| 12. PortfolioSnapshot 후방호환 | 단일 `Decimal` 필드 보존. `app/api/routes.py:136-137`이 그대로 작동 | ✓ |
| 13. 외부 HTTP lib 미도입 | http-lib-grep clean | ✓ |
| 14. GUI/dry-run/strategy/kis*/alpaca 미접촉 | git diff --stat 확인 0건 | ✓ |
| 15. 301 PASS | 자체 재실행 확인 | ✓ |

## Final checklist (plan §6 대비)

### 콘텐츠

- [x] `OrderType.MARKET` 도입 + 3중 가드 (3중 가드 RiskEngine에서 작동).
- [x] MARKET BUY = quote.ask, MARKET SELL = quote.bid, slippage 0.
- [x] Partial fill: `floor(quote.volume * max_fill_ratio_of_volume)`.
- [x] `PaperBroker.tick`이 staleness + session 검사 책임.
- [⚠] `Quote`에 `session`/`currency` 옵션 필드 추가 — `currency` invariant는 `isupper()` 일부만 검사 (3자 ASCII 검증 누락, low). session=None backward compat **미준수**(Finding #2).
- [x] `PaperAccount.cash`가 currency dict.
- [⚠] `Position.currency` + `Snapshot` PnL/market_value dict 시그니처 — 시그니처는 추가됨. 단일 Decimal 필드 보존됨. (`_by_currency` 명명)
- [x] FX 변환 0건. 통합 equity 0건.
- [x] Journal TradeLogEntry에 `currency`.
- [x] commission per-share + per-fill 합산 — PaperBroker가 적용.
- [⚠] End-to-end 테스트가 LIMIT + MARKET + partial + multi-currency cycle 닫음 — matrix로 LIMIT/MARKET 포함, KRW multi-currency 케이스 1개 보강 여지.

### 안전

- [⚠] **`OrderType.MARKET`은 `ALLOW_PAPER_MARKET_ORDERS=true` 없으면 RiskEngine reject** — 가드 작동하나 활성 시 **notional 우회 (Finding #1, HIGH)**.
- [x] live trading 활성화 변경 0건.
- [x] LLM/Agent의 broker 직접 호출 새 경로 0건.
- [x] `KisBroker`/`KisMarketDataClient`/`KisAccountClient`/`KisAuthClient` 본문 변경 0건.
- [x] `.env` 미접촉. `.env.example`은 이름 + 한 줄 설명만.
- [x] GUI 미접촉. dry-run 모듈 미접촉.
- [x] 외부 HTTP lib 0건.

### 테스트 / 프로세스

- [x] 기존 242 PASS + 신규 59 PASS = **총 301 PASS**.
- [x] `compileall` 무오류. 외부 네트워크 0건.
- [x] `patch.md`에 변경 / grep / 테스트 / commit-skip 기록 (9 섹션).
- [x] commit / push / merge / 배포 자동화 0건.

## 사람에게 남기는 액션 아이템

### 필수 — Finding #1 수정 후 재제출 (작은 변경)

1. `app/domain/orders.py:14`: `limit_price: Decimal = Decimal("0")` → default 제거(positional required).
2. `app/domain/orders.py:25`: `if self.order_type != OrderType.MARKET and self.limit_price <= 0:` → `if self.limit_price <= 0:` (MARKET에도 적용).
3. `tests/test_models.py`의 `test_market_order_intent_does_not_require_limit_price`를 반전 — MARKET intent에 limit_price 없으면 `ValueError`.
4. `tests/test_risk_engine.py`의 `market_intent()` fixture: `OrderIntent("AAPL", Side.BUY, 1, OrderType.MARKET)` → `OrderIntent("AAPL", Side.BUY, 1, OrderType.MARKET, Decimal("100"))` (expected fill price 명시).
5. 추가 테스트: MARKET intent + `quantity * expected_price > max_order_notional_usd` 케이스 → RiskEngine reject(`max_order_notional_exceeded`).

### 권장 — Finding #2 수정

1. `app/broker/paper.py` `tick()`: `if quote.session not in self._allowed_sessions:` → `if quote.session is not None and quote.session not in self._allowed_sessions:`.
2. 테스트 1개 추가: `session=None` quote가 broker에서 fill 차단 안 됨.

### 권장 — Finding #3 검토 (선택)

`PaperAccount`에 portfolio 통합 vs 현재 분리 구조 유지 결정. 분리 유지 시 docstring + plan §2.1 갱신.

### 수정 적용 후

1. `pytest` 재실행 → 301 PASS 유지 + 신규 보강.
2. 안전 grep 6/6 clean 재확인.
3. `patch.md`에 변경 추가 기록(`READY FOR REVIEW v2`).
4. Claude 재리뷰 → APPROVE 예상.

### 사람이 직접 할 git 작업 (수정 land 후)

```bash
cd /root/ai-dev-center/projects/ai-team
git status
git diff
git add projects/paper-trading/app/domain/fills.py \
        projects/paper-trading/app/portfolio/account.py \
        projects/paper-trading/app/runtime/paper_engine.py \
        projects/paper-trading/app/runtime/paper_journal.py \
        projects/paper-trading/app/broker/paper.py \
        projects/paper-trading/app/risk/engine.py \
        projects/paper-trading/app/portfolio/service.py \
        projects/paper-trading/app/domain/{enums.py,orders.py,quote.py} \
        projects/paper-trading/app/config.py \
        projects/paper-trading/.env.example \
        projects/paper-trading/README.md \
        projects/paper-trading/tests/test_paper_*.py \
        projects/paper-trading/tests/test_fill*.py \
        projects/paper-trading/tests/test_models.py \
        projects/paper-trading/tests/test_paper_broker.py \
        projects/paper-trading/tests/test_portfolio_service.py \
        projects/paper-trading/tests/test_risk_engine.py \
        projects/paper-trading/tests/test_strategy_premarket_gap.py \
        projects/paper-trading/tests/test_kis_order_preflight.py \
        docs/ai/jobs/paper-001/
git diff --cached --stat
```

`docs/ai/jobs/KIS_1/{patch.md, pipeline.log.md}`의 dirty(test count 갱신, 파이프라인 로그 추가)는 paper-001 scope 외 — 별 commit 또는 본 commit에 묶을지 사람이 결정.

## 다음 작업 후보

- **paper-001-gui** — 대시보드에 PaperAccount/Journal 노출.
- **paper-002** — 다중 fill 시퀀스 / 슬리피지 / market impact 모델.
- **api-market-data-001** — KIS 현재체결가로 실 Quote 주입, paper-001의 PaperEngine과 결합.
- **`paper-001`의 paper-only MARKET notional 정책 결정 문서화** — `docs/ai/MASTER_TRADING_ROADMAP.md`에 한 줄 보강.

---

# Review v2 (Codex fix 적용 후)

## Verdict v2

**APPROVE** (v1의 high-severity Finding #1 + medium-severity #2 모두 해소. Finding #3는 명시적 설계 결정 + docstring으로 문서화. low-severity 5건은 인정/follow-up.)

## v2 검증 (자체 재실행)

### 안전 grep
- 6/6 라벨 clean — Codex 보고대로 재확인.

### 테스트
- `pytest`: **303 passed in 0.49s** (v1 301 + Finding #1·#2 회귀 테스트 2개 추가).
- `compileall`: passed.

### Finding #1 fix 확인

| 위치 | 변경 | 검증 |
| --- | --- | --- |
| `app/domain/orders.py:14` | `limit_price: Decimal` (default 제거, positional required) | ✓ |
| `app/domain/orders.py:25` | MARKET 분기 없이 `if self.limit_price <= 0: raise` | ✓ MARKET에도 강제 |
| `tests/test_models.py:25-29` | `test_market_order_intent_requires_limit_price`: MARKET without limit → `TypeError`, MARKET + limit_price=0 → `ValueError` | ✓ |
| `tests/test_risk_engine.py:14` | `market_intent(quantity=1, limit=Decimal("100"))` fixture에 limit 명시 | ✓ |
| `tests/test_risk_engine.py:76-80` | `market_intent(quantity=1000, limit=100)` → notional 100,000 > 5,000 → `max_order_notional_exceeded` | ✓ **MARKET notional gate 실효 회복** |

### Finding #2 fix 확인

| 위치 | 변경 | 검증 |
| --- | --- | --- |
| `app/broker/paper.py:61` | `if quote.session is not None and quote.session not in self._allowed_sessions` | ✓ backward compat |
| `tests/test_paper_broker.py:84-92` | `test_paper_broker_tick_allows_missing_session_for_backward_compat`: quote without session → fill 1건 | ✓ |

### Finding #3 결정

- 분리 유지 + `PaperAccount` docstring 명시: *"Cash ledger only; positions and PnL remain owned by PortfolioService. Keeping cash and portfolio state separate avoids hidden exchange-rate or mark-to-market behavior inside account settlement."*
- 합리적 정당화 (FX 미지원 invariant와 정합). Plan §2.1의 통합형 제안은 부결 — 사용자/Codex 명시적 채택.
- `PaperEngine`이 fill을 account + portfolio 양쪽으로 routing하는 책임을 보유. raw `PaperAccount` 단독 사용은 본 docstring으로 차단된다(설계 의도 명시).

## 잔존 low-severity (paper-001 외 follow-up)

v1 review §Findings 4–8 그대로 유효. 안전 영향 0, paper-001 land 막지 않음.

1. `PaperEngine.submit_intents` 부재 (UX deviation).
2. LIMIT fill 가격 = `quote.ask/bid` (plan deviation, 안전 측면 OK — buyer never overpays).
3. STOP_LIMIT 트리거 상태 tick 간 미보존.
4. Partial fill volume budget이 한 tick에서 주문 간 공유.
5. 필드 명명 `_by_currency` vs `_per_currency` (cosmetic).
6. `Position.currency` 변경 불가 검증, `Quote.currency` 검증이 `isupper()`만 — ISO 3-letter 검증 누락 (low).

각각 별 mvp 또는 paper-002에서 보강 가능. 본 review에서는 인정.

## v2 안전 / 정책 invariant 최종 점검

- [x] paper 기본, live 비활성 유지.
- [x] LLM/Agent의 executable order 경로 추가 0건.
- [x] 추천 agent는 OrderIntent만. OMS만 BrokerOrder 생성.
- [x] 모든 주문 Strategy → Risk → OMS → PaperBroker 통과.
- [x] **MARKET 주문 notional gate 실효** (Finding #1 fix 후): `quantity × limit_price > max_order_notional_usd` 검증이 MARKET에도 의미 있게 동작.
- [x] **MARKET 3중 가드** (`ALLOW_PAPER_MARKET_ORDERS=true` + `TradingMode.PAPER` + `live_trading_enabled=False`) 유지.
- [x] 실 broker API 호출 0건. KIS/Alpaca/base broker 본문 0건.
- [x] 실 API key 0건. `.env` 미접촉. `.env.example`은 이름 + 설명만.
- [x] FX 변환 함수 0건. `PaperAccount` docstring으로 명시.
- [x] GUI/dry-run/strategy/oms manager 미접촉.
- [x] `PortfolioSnapshot` 단일 `Decimal` 필드 보존 → `app/api/routes.py:136-137` 후방호환.
- [x] 외부 HTTP lib 0건.
- [x] 자동 commit/push/merge/deploy 0건.
- [x] 303 PASS, compileall 무오류, 회귀 0건.

## 사람에게 남기는 액션 아이템 (v2)

### 필수 — git staging (paper-001 commit)

워크트리 정리는 사람 직접. 권장 staging:

```bash
cd /root/ai-dev-center/projects/ai-team
git add projects/paper-trading/app/domain/fills.py \
        projects/paper-trading/app/domain/{enums.py,orders.py,quote.py} \
        projects/paper-trading/app/portfolio/account.py \
        projects/paper-trading/app/portfolio/service.py \
        projects/paper-trading/app/broker/paper.py \
        projects/paper-trading/app/risk/engine.py \
        projects/paper-trading/app/runtime/paper_engine.py \
        projects/paper-trading/app/runtime/paper_journal.py \
        projects/paper-trading/app/config.py \
        projects/paper-trading/.env.example \
        projects/paper-trading/README.md \
        projects/paper-trading/tests/test_paper_account.py \
        projects/paper-trading/tests/test_paper_engine.py \
        projects/paper-trading/tests/test_paper_fills.py \
        projects/paper-trading/tests/test_paper_journal.py \
        projects/paper-trading/tests/test_paper_001_simulation_matrix.py \
        projects/paper-trading/tests/test_paper_broker.py \
        projects/paper-trading/tests/test_portfolio_service.py \
        projects/paper-trading/tests/test_risk_engine.py \
        projects/paper-trading/tests/test_models.py \
        projects/paper-trading/tests/test_strategy_premarket_gap.py \
        projects/paper-trading/tests/test_kis_order_preflight.py \
        docs/ai/jobs/paper-001/
git diff --cached --stat
```

별 commit (선택): `docs/ai/jobs/KIS_1/{patch.md, pipeline.log.md}` dirty (test count 갱신 + 파이프라인 로그) — paper-001 scope 외. 같은 commit에 묶을지 별로 둘지는 사람 결정.

### 권장 follow-up jobs

- **paper-001-gui** — 대시보드에 PaperAccount/Journal 노출 (사용자가 GUI 재개 신호 보낸 후).
- **paper-002** — partial fill 다중 시퀀스 보강, slippage 모델, market impact.
- **api-market-data-001** — KIS 현재체결가로 실 Quote 주입, PaperEngine과 결합.
- **roadmap 보강** — `docs/ai/MASTER_TRADING_ROADMAP.md`에 "paper-001: MARKET 도입 (ALLOW_PAPER_MARKET_ORDERS=true 시만 활성, 3중 가드 + notional ceiling 유지)" 한 줄 추가.

## v2 Verdict 요약

**APPROVE**. paper-001 v2 코드 land 가능. 사람 직접 `git status` / `git diff` 확인 후 staging/commit.
