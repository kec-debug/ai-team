## 1. 요청 요약

**최초의 내부 paper trading MVP — 확장판.** 사용자가 6개 기능을 모두 포함하기로 결정:

1. LIMIT/STOP_LIMIT 시뮬레이션 (기본)
2. **MARKET 시뮬레이션** (slippage 0)
3. **Partial fill** (quote.volume 비율 기반)
4. **Quote staleness 검사** (PaperBroker가 책임)
5. **Session/장중 시간 고려** (REGULAR 외 fill 거절)
6. **Multi-currency** (USD/KRW 등 분리, FX 변환은 본 MVP에서 안 함)

기존 plan(LIMIT-only)에서 scope가 약 2배로 늘어남. 위 5번 multi-currency가 가장 invasive — `Quote`/`Position`/`PortfolioSnapshot`/`PaperAccount`/`Fill` 다 손대야 함. **scope 확인 후 진행 권장** (§ scope 경고 참고).

### 사전 land 상태 (2026-05-17 commit 시점)

- 워크트리 깨끗, 242 PASS.
- Strategy → OMS → RiskEngine → PaperBroker 체인 wired.
- `PaperBroker.submit()` 작동, fill 시뮬레이션 부재.
- `PortfolioService`에 positions/realized PnL만, cash/unrealized 부재.
- `Fill`/`PaperAccount`/Journal/`PaperEngine` 부재.

### 안전 원칙 (변경 없음)

1. Paper 기본, live 비활성.
2. Live는 비활성 유지 — 본 job은 live 경로 코드 추가 0건.
3. LLM은 절대 executable order 못 만듦.
4. 추천 agent는 `OrderIntent`(non-executable)만.
5. Executable order는 OMS만.
6. 모든 주문은 Strategy → RiskEngine → OMS → PaperBroker 통과.
7. 실 broker API 호출 0건 — KIS/Alpaca client 본문 미접촉.
8. 실 API 키 0건.
9. `.env` 미접촉. `.env.example`은 변수 이름 + 한 줄 설명만.
10. Live 주문 실행 코드 0건.

추가:

- **`OrderType.MARKET` 도입은 본 job에서 invariant 변경**. 도입 조건은 별도 flag `ALLOW_PAPER_MARKET_ORDERS=true` + `TradingMode=PAPER` + `live_trading_enabled=False` 동시 만족. 기존 `ALLOW_MARKET_ORDERS`(load_settings reject)는 그대로.
- GUI 미접촉. dry-run 모듈 미접촉.
- 자동 commit/push/merge/deploy 금지.

---

## ⚠️ Scope 경고 (사람 결정 필요)

본 plan은 6개 기능을 한 job에 모두 담는다. 예상 규모:

| 항목 | 신규 LoC (대략) | 신규 테스트 |
| --- | --- | --- |
| LIMIT/STOP_LIMIT fill + cash + journal + engine (기본) | 약 600 | 약 25 |
| MARKET fill + flag + RiskEngine 가드 | 약 80 | 약 6 |
| Partial fill (volume 비율) | 약 100 | 약 8 |
| Staleness 검사 in broker | 약 30 | 약 3 |
| Session 검사 | 약 50 | 약 4 |
| Commission per-share default 변경 | 약 15 | 약 3 |
| **Multi-currency** (Quote/Position/Snapshot/Account/Fill 다 손댐) | 약 200 | 약 12 |
| **합계** | **약 1100** | **약 60+** |

이는 한 Codex pass로 가능하긴 하나 review 부담이 큼. 권장 분할(plan §6 사람 액션 아이템에도 동일):

- **paper-001**: LIMIT/STOP_LIMIT + MARKET + cash + journal + engine + staleness + session + commission (multi-currency 제외).
- **paper-001-mc**: multi-currency만 별도 job. Quote/Position/Snapshot 등 도메인 변경 + FX 정책 결정 포함.
- **paper-002**: partial fill만 별도 job. 거래량 기반 fill rate + 주문 잔량 추적 + 다중 Fill 시퀀스 테스트.

**본 plan은 일단 6개 모두 포함한 형태로 작성**. 사람이 분할 결정하면 §3/§5/§6에서 해당 섹션 제외 가능. **Codex로 보내기 전에 분할 여부 확정.**

---

## 2. 작업 범위

### 2.1 도메인 모델

#### `Fill` (신규, `app/domain/fills.py`)

```python
@dataclass(frozen=True)
class Fill:
    symbol: str
    side: Side
    quantity: int             # 이 fill에서 실제 채결된 수량 (partial일 수 있음)
    price: Decimal
    filled_at: datetime
    broker_order_id: str
    oms_id: str
    risk_token: str
    currency: str = "USD"     # 본 fill의 가격/commission이 표시된 통화
    commission: Decimal = Decimal("0")
    source: str = "paper_internal"
```

`__post_init__`에서 invariant 검증(수량/가격>0, commission>=0, currency uppercase ASCII 3자리, tz-aware filled_at).

#### `OrderType.MARKET` 추가 (`app/domain/enums.py`)

```python
class OrderType(str, Enum):
    LIMIT = "limit"
    STOP_LIMIT = "stop_limit"
    MARKET = "market"  # paper 전용, ALLOW_PAPER_MARKET_ORDERS=true 필요
```

`OrderIntent.__post_init__` 변경: MARKET이면 `limit_price`가 quote에서 결정되므로 0 허용. 단 `quantity>0` invariant는 그대로.

`OrderIntent` / `Order` / `BrokerOrder`에 `currency: str = "USD"` 필드 추가. 기존 사용처는 default 사용으로 backward compatible.

#### `Quote` 확장 (`app/domain/quote.py`)

기존 frozen `Quote` dataclass에 다음 필드 추가:

```python
session: Session | None = None       # None이면 broker session 검사 skip
currency: str = "USD"                # quote의 통화
```

기존 invariant + 새 invariant:

- `currency`는 3자리 대문자 ASCII (예: `USD`, `KRW`, `HKD`, `JPY`).
- `session`은 `None` 또는 `Session` enum 멤버.

mvp-023 테스트(`test_quote_model.py`)는 default 값이라 회귀 없음.

#### `PaperAccount` (신규, `app/portfolio/account.py`)

```python
@dataclass
class PaperAccount:
    cash: dict[str, Decimal]                  # currency → balance
    starting_cash: dict[str, Decimal]         # immutable baseline
    portfolio: PortfolioService
    base_currency: str = "USD"

    @classmethod
    def from_settings(cls, settings: Settings) -> "PaperAccount":
        # 기본: {base_currency: settings.paper_starting_cash}
        # 옵션: settings.paper_starting_cash_by_currency (dict) 우선 사용

    def apply_fill(self, fill: Fill) -> None: ...
    def equity_per_currency(self) -> dict[str, Decimal]: ...
    def realized_pnl_per_currency(self) -> dict[str, Decimal]: ...
    def unrealized_pnl_per_currency(self) -> dict[str, Decimal]: ...
    # FX 변환은 본 MVP 미지원 — 통화별 분리 보고
```

`apply_fill`은 fill.currency 키에 대해 cash 차감/가산. 해당 통화 cash가 없으면 `PaperAccountError("currency_not_funded")`. 부족 시 `PaperAccountError("insufficient_cash")`.

### 2.2 PaperBroker fill 시뮬레이션 (`app/broker/paper.py`)

기존 시그니처 보존 + 메서드 추가.

#### 새 `__init__`

```python
def __init__(
    self,
    max_quote_age_seconds: int = 60,
    allowed_sessions: tuple[Session, ...] = (Session.REGULAR,),
    max_fill_ratio_of_volume: Decimal = Decimal("0.05"),
) -> None:
    self._open_orders: dict[str, BrokerOrder] = {}
    self._positions: dict[str, int] = {}
    self._triggered_stops: set[str] = set()
    self._remaining_qty: dict[str, int] = {}   # broker_order_id → 남은 수량
    self._max_quote_age_seconds = max_quote_age_seconds
    self._allowed_sessions = set(allowed_sessions)
    self._max_fill_ratio = max_fill_ratio_of_volume
```

#### `tick(quote: Quote) -> list[Fill]`

```python
def tick(self, quote: Quote) -> list[Fill]:
    # 1. 입력 검증: quote.last/bid/ask > 0 (아니면 ValueError)
    # 2. Staleness 검사: quote.is_stale(now, _max_quote_age_seconds) 면 [] 반환
    # 3. Session 검사: quote.session is not None and quote.session not in _allowed_sessions 면 [] 반환
    # 4. quote.symbol 매치 open orders 순회:
    #    - LIMIT BUY: quote.ask <= limit → fill_price = limit_price
    #    - LIMIT SELL: quote.bid >= limit → fill_price = limit_price
    #    - STOP_LIMIT: stop 트리거 후 LIMIT 조건
    #    - MARKET BUY: 즉시 fill, fill_price = quote.ask
    #    - MARKET SELL: 즉시 fill, fill_price = quote.bid
    # 5. Partial fill 계산:
    #    remaining = self._remaining_qty[broker_order_id]
    #    cap = floor(quote.volume * self._max_fill_ratio)
    #    fill_qty = min(remaining, cap)  (단, cap이 0이고 quote.volume>0이면 1 최소 보장은 선택)
    #    fill_qty가 0이면 skip (no Fill emitted)
    # 6. Fill 생성 (currency = quote.currency).
    # 7. remaining -= fill_qty. remaining==0이면 _open_orders/triggered_stops에서 제거.
    # 8. self._positions[symbol] 갱신 (signed 합).
    # 9. fills list 반환.
```

가격 정책:

- LIMIT/STOP_LIMIT: fill_price = order.limit_price (스프레드 개선 없음).
- MARKET: fill_price = quote.ask (BUY) / quote.bid (SELL). **slippage 0** (호가 그대로).

Partial fill 정책:

- 한 tick에 최대 `floor(quote.volume * max_fill_ratio)` 채결.
- 남은 수량은 다음 tick에서 처리.
- 주문은 fully filled되어야 `_open_orders`에서 제거.
- `cancel(broker_order_id)`은 remaining 무관 즉시 제거.

#### `submit` 본문 확장

`submit`에서 MARKET 허용 (RiskEngine이 이미 가드). `_remaining_qty[broker_order_id] = order.quantity` 초기화.

#### `cancel_all(reason: str | None = None) -> int`

기존 plan 그대로.

### 2.3 RiskEngine 확장 (`app/risk/engine.py`)

기존 `evaluate`에 MARKET 분기 추가:

```python
if intent.order_type is OrderType.MARKET:
    if not self._settings.allow_paper_market_orders:
        return RiskDecision(False, "paper_market_orders_disabled")
    if self._settings.trading_mode != TradingMode.PAPER:
        return RiskDecision(False, "market_only_in_paper")
    if self._settings.live_trading_enabled:
        return RiskDecision(False, "market_disabled_in_live")
    # quantity check은 공통 분기 통과
elif intent.order_type not in (OrderType.LIMIT, OrderType.STOP_LIMIT):
    return RiskDecision(False, "order_type_not_supported")
```

기존 `intent.order_type not in (OrderType.LIMIT, OrderType.STOP_LIMIT)` 거절은 위로 통합. notional 계산에서 MARKET이면 `quote.last`를 추정치로 사용 — 다만 RiskEngine은 quote에 접근하지 않으므로 MARKET notional 검증은 **skip** (caller가 Strategy 단계에서 `limit_price`를 expected fill price로 채워 보내는 것으로 우회) — Strategy 책임.

> 주: 더 안전한 대안은 `OrderIntent.limit_price`를 MARKET에서도 expected fill price로 강제하고, RiskEngine notional 검증을 그대로 수행하는 것. 본 plan은 이 대안 채택. MARKET intent에도 `limit_price>0` 요구.

### 2.4 Cash + PnL + multi-currency

§2.1의 `PaperAccount` 참고. 핵심:

- Cash는 `dict[currency, Decimal]`.
- BUY: `cash[fill.currency] -= notional + commission`. 부족하면 `PaperAccountError("insufficient_cash")`.
- SELL: `cash[fill.currency] += notional - commission`.
- 통화별로 분리 보고. FX 변환 없음.

#### PortfolioService 수정 (`app/portfolio/service.py`)

- `Position`에 `currency: str = "USD"` 필드 추가.
- `PortfolioSnapshot`:
  - `realized_pnl: dict[str, Decimal]` (currency별)
  - `unrealized_pnl: dict[str, Decimal]` (currency별)
  - `market_value: dict[str, Decimal]` (currency별)
  - `total_pnl_per_currency()` 메서드
  - 기존 단일 Decimal 시그니처는 `_legacy` deprecated property로 유지하지 않음 — 본 job의 `PortfolioSnapshot` consumer는 paper-001 신규 코드뿐이라 breaking 허용 (기존 호출자 0건).
- `apply_fill(symbol, side, quantity, price, commission, currency="USD")` — currency 인자 추가, position.currency 일관성 검증.

기존 `test_portfolio_service.py`가 영향 — 일부 단정은 dict 인덱싱으로 수정 필요. 본 plan §3에 명시.

### 2.5 Quote staleness

`PaperBroker.tick()`이 `quote.is_stale(datetime.now(UTC), self._max_quote_age_seconds)` 직접 호출. stale이면 fills 없음. caller는 stale quote 걸러낼 책임 없음.

설정: `Settings.paper_max_quote_age_seconds` (기본 60).

### 2.6 Session 검사

- `Quote.session` 필드 추가(§2.1).
- `PaperBroker._allowed_sessions` (기본 `{Session.REGULAR}`).
- 설정: `Settings.paper_allowed_sessions: tuple[str, ...]` (기본 `("regular",)`). load_settings에서 enum 변환.
- `quote.session is None` (모르면) → broker 허용 (backward compat).
- `quote.session`이 allowed_sessions에 없으면 fill 0건, journal에 "rejected: session_not_allowed" 기록 (engine 책임).

### 2.7 Commission

기본값 변경: `PAPER_COMMISSION_USD` → `PAPER_COMMISSION_PER_SHARE`. 기본 `Decimal("0.005")` (IB tier-like). 총 commission = `fill.quantity * commission_per_share` (이 fill의 통화 단위).

설정 이름:
- `PAPER_COMMISSION_PER_SHARE` (기본 0.005)
- (선택) `PAPER_COMMISSION_PER_FILL` (기본 0). flat 추가분.
- 최종 commission = `quantity * per_share + per_fill`.

Multi-currency에서 commission은 fill.currency에 적용. KRW에서 `0.005 KRW`는 비현실적 — 정책 결정: `PAPER_COMMISSION_PER_SHARE_BY_CURRENCY: dict[str, Decimal] | None` 옵션. None이면 모든 통화에 `PAPER_COMMISSION_PER_SHARE` 동일 적용 (기본).

### 2.8 Order log / Trade log

기존 plan §2.8 그대로. `PaperJournal`. 메모리 default, `PAPER_LOG_DIR` opt-in. TradeLogEntry에 `currency` 필드 추가.

### 2.9 Runtime 통합 (`app/runtime/paper_engine.py`)

기존 plan §2.9 + session check 책임 분리.

`PaperEngine.on_quote(quote)`:

1. `broker.tick(quote)` 호출 (broker가 stale/session/partial 다 처리).
2. fills 각각에 `account.apply_fill(fill)` (실패 시 journal rejected).
3. journal에 trade + filled order 기록.

`PaperEngine.submit_intents(intents)`: 기존 그대로.

### 2.10 환경변수 (값 없이 이름만)

기존 + 신설:

- `TRADING_MODE`, `LIVE_TRADING_ENABLED`, `PAPER_STARTING_CASH`, `MAX_ORDER_NOTIONAL_USD`, `MAX_OPEN_POSITIONS`, `SYMBOL_ALLOWLIST`, `ALLOW_MARKET_ORDERS`, `KILL_SWITCH_ENGAGED` (기존)
- `ALLOW_PAPER_MARKET_ORDERS` — 기본 `false`. paper에서 MARKET 활성.
- `PAPER_COMMISSION_PER_SHARE` — 기본 `0.005`.
- `PAPER_COMMISSION_PER_FILL` — 기본 `0`.
- `PAPER_LOG_DIR` — 기본 미설정.
- `PAPER_FILL_POLICY` — 기본 `"limit"`. 본 MVP는 `limit`만 허용. MARKET은 `OrderType`으로 결정되지 `fill_policy`로 결정되지 않음.
- `PAPER_MAX_QUOTE_AGE_SECONDS` — 기본 `60`.
- `PAPER_ALLOWED_SESSIONS` — 기본 `regular`. 쉼표 분리 (예: `regular,pre_market`).
- `PAPER_MAX_FILL_RATIO_OF_VOLUME` — 기본 `0.05`. 0.05 = 5%.
- `PAPER_STARTING_CASH_BY_CURRENCY` — 기본 미설정. JSON 또는 `USD=100000,KRW=130000000` 형태. 미설정 시 `{base_currency: PAPER_STARTING_CASH}`.
- `PAPER_BASE_CURRENCY` — 기본 `USD`.

### 2.11 테스트

| 파일 | 단정 |
| --- | --- |
| `test_fill_model.py` | invariants + currency 검증 |
| `test_quote_model.py` (기존 확장) | session/currency 기본값, invariants |
| `test_order_type_market.py` | enum 멤버, OrderIntent MARKET + limit_price=0 거절, MARKET + limit_price>0 허용 |
| `test_risk_engine_market.py` | MARKET + flag off → reject, flag on + paper → approve, live + flag on → reject |
| `test_paper_account.py` | 단일 통화, multi-currency cash dict, currency_not_funded reject, insufficient_cash reject, equity_per_currency |
| `test_paper_broker_fill.py` | LIMIT/MARKET/STOP_LIMIT × BUY/SELL, partial fill 흐름, 잔량 누적, fully filled되어야 open에서 제거 |
| `test_paper_broker_staleness.py` | stale quote → 0 fills, age_seconds 경계 |
| `test_paper_broker_session.py` | session=None 허용, session=REGULAR 허용, session=PRE_MARKET 거절(기본), 설정으로 PRE_MARKET 허용 후 통과 |
| `test_paper_broker_partial.py` | volume=100 + max_ratio=0.05 → 한 tick에 max 5주, 잔량 다음 tick까지 누적 |
| `test_paper_journal.py` | 메모리 default, log_dir 영속화, TradeLogEntry.currency 보존 |
| `test_portfolio_multi_currency.py` | USD + KRW position 동시, per-currency snapshot, unrealized/realized 분리 |
| `test_portfolio_unrealized_pnl.py` (기존 확장) | dict 시그니처로 갱신 |
| `test_paper_engine.py` | submit_intents/on_quote 흐름, partial fill 시 1 trade entry per fill |
| `test_paper_end_to_end.py` | 통합: LIMIT BUY + LIMIT SELL cycle, partial fill 2회로 fully filled, KRW 계좌로 한국 주식 cycle |
| `test_commission.py` | per_share + per_fill 합산, multi-currency commission 적용 |
| 기존 `test_paper_broker.py` | tick/cancel_all 케이스 추가, 기존 단정 보존 |
| 기존 `test_portfolio_service.py` | dict 시그니처 갱신 |
| 기존 `test_risk_engine.py` (있다면) | MARKET 케이스 추가 |

### 포함 (In scope) — 요약

§2.1–2.11 전부. 6개 기능 모두.

### 제외 (Out of scope; 절대 만지지 않음)

- **FX 변환 / 환율 적용**. 통화별로 분리 보고만. 통합 equity는 본 MVP에서 산출 안 함.
- 실 시세 연결 (KIS/Alpaca). caller가 Quote 주입.
- GUI / `app/api/*` / `app/static/*` 변경.
- dry-run 모듈 (`dry_run.py`, `dry_run_report.py`, `paper_runner.py`) 본문 변경.
- 새 AI agent / LLM 호출.
- 슬리피지 모델, market impact, 거래시간 외 처리.
- `OrderType.STOP` (지정가 없는 stop) — STOP_LIMIT만 유지.
- Live 활성 경로.
- `.env` 수정/읽기.
- 자동 git commit/push/merge/deploy.

---

## 3. 수정해야 할 파일

### 신규

- `app/domain/fills.py`
- `app/portfolio/account.py`
- `app/runtime/paper_journal.py`
- `app/runtime/paper_engine.py`
- 15개+ 신규 테스트 파일 (§2.11)

### 수정

- `app/domain/enums.py` — `OrderType.MARKET` 추가.
- `app/domain/orders.py` — `OrderIntent`/`Order`/`BrokerOrder`에 `currency: str = "USD"` 추가.
- `app/domain/quote.py` — `session: Session | None = None`, `currency: str = "USD"` 추가 + invariants.
- `app/broker/paper.py` — `tick`/`cancel_all`/`_remaining_qty`/MARKET 분기/staleness/session 검사.
- `app/risk/engine.py` — MARKET 분기 추가.
- `app/portfolio/service.py` — `Position.currency`, `Snapshot`의 PnL/market_value dict화, `apply_fill` currency 인자.
- `app/config.py` — 위 §2.10 신설 환경변수 7개 추가 + load 로직.
- `.env.example` — 신설 변수 이름 + 한 줄 설명만.
- `README.md` — paper-001 단락.
- 기존 테스트 일부 (§2.11 — `test_portfolio_service`, `test_paper_broker`, `test_risk_engine` 등).
- `docs/ai/jobs/paper-001/patch.md` (Codex 작성).

### 미변경 (절대)

`app/api/*`, `app/static/*`, `app/main.py`, `app/strategy/*`, `app/runtime/{dry_run.py, dry_run_report.py, paper_runner.py}`, `app/oms/manager.py`, `app/broker/{base.py, kis*.py, alpaca_paper.py, kis_quote_mapper.py}`, `.env`, `.gitignore`, `docs/kis/*`, `docs/ai/MASTER_TRADING_ROADMAP.md`, `prompts/*`, `scripts/*`, `imports/*`, 이전 모든 mvp 산출물.

---

## 4. Codex 구현 지시문

`docs/ai/jobs/paper-001/codex-task.md`에 본문까지 박힌 형태로 제공할 예정. 본 plan 승인 후 codex-task 재작성.

핵심 골격(§K-style 적용 절차):

1. §3 파일 목록만 변경. 그 외 0건.
2. **MARKET 도입 가드 3중**: `ALLOW_PAPER_MARKET_ORDERS=true` + `TradingMode=PAPER` + `live_trading_enabled=False`. 셋 중 하나라도 깨지면 RiskEngine reject.
3. Partial fill은 **한 tick에서 1 주문당 최대 1 fill** (volume*ratio 이내). 다음 tick에 잔량 처리.
4. Multi-currency는 **FX 변환 없이 dict 분리**. equity 통합 계산 없음.
5. Quote에 `session`/`currency` 추가 — 기존 코드/테스트는 default로 backward compatible.
6. PortfolioSnapshot의 realized/unrealized/market_value가 **dict로 시그니처 변경**. 기존 호출자 update 필요(`test_portfolio_service.py` 등).
7. 외부 HTTP 라이브러리 0건. fake 값만 사용. secrets/key 0건.
8. 자동 commit/push/merge/deploy 0건.

---

## 5. 테스트 기준

### 5.1 회귀

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

- 기존 242 + 신규 약 60+ 모두 PASS.
- 기존 dry-run / KIS / GUI / KIS_1 / api-auth-001 테스트 회귀 0건.
- 외부 네트워크 호출 0건.

### 5.2 안전 grep (Codex가 patch.md에 기록)

| 패턴 | 범위 | 기대 |
| --- | --- | --- |
| `LiveTransport` 또는 live mode 활성 코드 | 본 job 변경/신설 | 0건 |
| `import requests` / `import httpx` / `import aiohttp` / `import urllib3` | 동 | 0건 |
| 실 key/secret/Bearer/계좌번호 패턴 | 동 | 0건 |
| `app.api.*` import (GUI 차단 확인) | 신설 `app/runtime/paper_engine.py`, `paper_journal.py`, `app/broker/paper.py` | 0건 |
| `dry_run.py` / `dry_run_report.py` / `paper_runner.py` 변경 | 동 | 0건 |
| FX 변환 함수 또는 환율 상수 | 동 | 0건 (FX 변환 0건) |

---

## 6. 리뷰 체크리스트

### 콘텐츠

- [ ] `OrderType.MARKET` 도입 + 3중 가드 (`ALLOW_PAPER_MARKET_ORDERS` + PAPER + !live).
- [ ] MARKET BUY = quote.ask, MARKET SELL = quote.bid, slippage 0.
- [ ] Partial fill: `floor(quote.volume * max_fill_ratio)` cap.
- [ ] `PaperBroker.tick`이 staleness + session 검사 책임.
- [ ] `Quote`에 `session`/`currency` 옵션 필드 추가, 기존 테스트 회귀 0.
- [ ] `PaperAccount.cash`가 currency dict.
- [ ] `Position.currency` + `Snapshot` PnL/market_value dict 시그니처.
- [ ] FX 변환 0건. 통합 equity 0건.
- [ ] Journal TradeLogEntry에 `currency`.
- [ ] commission per-share + per-fill 합산.
- [ ] End-to-end 테스트가 LIMIT + MARKET + partial + multi-currency cycle 닫음.

### 안전

- [ ] `OrderType.MARKET`은 `ALLOW_PAPER_MARKET_ORDERS=true` 없으면 RiskEngine reject.
- [ ] live trading 활성화 변경 0건.
- [ ] LLM/Agent의 broker 직접 호출 새 경로 0건.
- [ ] `KisBroker`/`KisMarketDataClient`/`KisAccountClient`/`KisAuthClient` 본문 변경 0건.
- [ ] `.env` 미접촉. `.env.example`은 이름 + 한 줄 설명만.
- [ ] GUI 미접촉. dry-run 모듈 미접촉.
- [ ] 외부 HTTP lib 0건.

### 테스트 / 프로세스

- [ ] 기존 242 PASS + 신규 60+ PASS.
- [ ] `compileall` 무오류. 외부 네트워크 0건.
- [ ] `patch.md`에 변경 / grep / 테스트 / commit-skip 기록.
- [ ] commit / push / merge / 배포 자동화 0건.

### 사람이 직접 결정해야 할 사항 (Codex 호출 전)

1. **본 plan을 6개 기능 한 번에 보낼지, 분할할지** (scope 경고 §). 권장 분할:
   - paper-001: MARKET + cash + journal + engine + staleness + session + commission. (multi-currency, partial 제외)
   - paper-001-mc: multi-currency만.
   - paper-002: partial fill만.
2. MARKET 도입의 정책 변경 (저장소 invariant `OrderType.MARKET 부재` 종료) 명시적 승인.
3. Commission 기본값 `$0.005/share` 적절성 검토.

### 후속 액션 (Codex 적용 후)

1. `git status` / `git diff` 직접 확인 후 staging.
2. commit 시 §3의 파일만.
3. 후속 job 후보:
   - `api-market-data-001` (KIS 현재체결가 → 실 Quote 주입)
   - `paper-001-gui` (대시보드에 PaperAccount/Journal 노출)
   - `paper-003` (slippage 모델, market impact)
