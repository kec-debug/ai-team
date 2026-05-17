## 1. 요청 요약

**최초의 내부 paper trading MVP 설계.** GUI 작업은 중지하고, 백엔드 차원에서 "**주문이 시작에서 fill까지 흘러가서 cash/positions/PnL이 실제로 갱신되는**" end-to-end 흐름을 완성한다.

현재 상태 (직접 확인):

- `Strategy → OMS → RiskEngine → PaperBroker` 체인이 이미 wired (`app/oms/manager.py`, `app/risk/engine.py`, `app/broker/paper.py`).
- 하지만 **`PaperBroker.submit()`이 주문을 받아 `_open_orders`에 넣기만 하고 fill을 만들지 않음**. `tick(quote)` 같은 매칭 메서드 부재.
- `PortfolioService`는 positions/realized PnL/avg price는 처리하나 **cash balance는 추적하지 않음**, `apply_fill`을 호출하는 곳도 없음 — 즉 portfolio가 broker 결과를 받지 못함.
- `Fill` 도메인 모델 부재.
- Order log / Trade log 부재 (dry-run report는 별도 목적).
- Unrealized PnL이 snapshot에 노출되지 않음(`market_value`만 있음).
- 242 tests PASS (api-auth-001 land 직후).

paper-001은 **위 gap을 닫고 단일 통합 happy-path가 테스트로 검증되는 상태**까지를 정의한다. KIS/Alpaca 실시 quote 연결은 본 job 범위 외 — 테스트가 Quote를 직접 주입.

### 안전 원칙 (모든 작업에 적용)

1. **Paper가 기본**. `Settings.trading_mode` 기본 `PAPER`. 모든 신규 경로 `TradingMode.PAPER`에서만 활성.
2. **Live는 비활성 유지**. `live_trading_enabled=False` 기본. 본 job은 live 경로 코드 추가 0건.
3. **LLM은 절대 executable order 못 만듦**. 본 job은 LLM/Agent 코드 추가 0건.
4. **추천 agent는 `OrderIntent`(non-executable)만 생성**. `OrderIntent`→`Order`→`BrokerOrder` 변환은 OMS만 가능 — 변경 없음.
5. **Executable order는 OMS만**. `BrokerOrder` 생성 경로 OMS에 국한 — 변경 없음.
6. **모든 주문은 Strategy → RiskEngine → OMS → PaperBroker 통과** — 변경 없음.
7. **실 broker API 호출 0건**. `KisBroker`/`KisMarketDataClient`/`KisAccountClient` 본문 미접촉(여전히 `NotImplementedError`).
8. **실 API 키 0건**. 본 job은 `KIS_*` 키를 읽지 않음.
9. **`.env` 미접촉**. `.env.example`도 본 job에서는 한 줄 설명만 추가(값/placeholder 0건).
10. **Live 주문 실행 코드 0건**. `OrderType.MARKET` 부재 유지 — 시장가 시뮬레이션은 본 job 범위 외(이유는 §2 마지막).

추가:

- GUI(`app/api/`, `app/static/`, dashboard) 변경 0건. 본 job은 백엔드 전용.
- `app/broker/kis*.py` 본문 변경 0건. import만 필요 시 추가 가능하나 권장 안 함.
- 자동 `git commit` / `push` / `merge` / `deploy` 금지.

---

## 2. 작업 범위

### 2.1 도메인 모델

#### `Fill` (신규, `app/domain/fills.py`)

```python
@dataclass(frozen=True)
class Fill:
    symbol: str            # uppercase, ASCII
    side: Side
    quantity: int          # > 0, full quantity of this fill (partial fills allowed via multiple Fills)
    price: Decimal         # > 0, execution price
    filled_at: datetime    # tz-aware UTC
    broker_order_id: str   # echo from OrderAck
    oms_id: str            # echo from BrokerOrder.oms_id
    risk_token: str        # echo from BrokerOrder.risk_token
    commission: Decimal = Decimal("0")  # >= 0
    source: str = "paper_internal"      # provenance tag, similar to Quote.source
```

`__post_init__`: invariants 검증(quantity>0, price>0, commission>=0, symbol uppercase, filled_at tz-aware).

#### `PaperAccount` (신규, `app/portfolio/account.py`)

```python
@dataclass
class PaperAccount:
    cash: Decimal                        # running cash balance
    starting_cash: Decimal               # immutable for PnL baseline
    portfolio: PortfolioService          # references positions/PnL
    base_currency: str = "USD"

    def equity(self) -> Decimal:
        snap = self.portfolio.get_snapshot()
        return self.cash + snap.market_value

    def total_realized_pnl(self) -> Decimal: ...
    def total_unrealized_pnl(self) -> Decimal: ...
    def total_pnl(self) -> Decimal: ...    # realized + unrealized

    @classmethod
    def from_settings(cls, settings: Settings) -> "PaperAccount":
        return cls(cash=settings.paper_starting_cash,
                   starting_cash=settings.paper_starting_cash,
                   portfolio=PortfolioService())
```

`apply_fill(fill)` 메서드: `portfolio.apply_fill(...)` 위임 + cash 차감/증가 + commission 차감.

- BUY: `cash -= fill.quantity * fill.price + fill.commission`. cash가 음수가 되면 **`PaperAccountError("insufficient_cash")`** raise. fill은 적용되지 않음.
- SELL: `cash += fill.quantity * fill.price - fill.commission`.

### 2.2 PaperBroker fill 시뮬레이션

`app/broker/paper.py` 수정. **기존 `submit`/`cancel`/`open_orders`/`positions` 시그니처 보존.**

#### 새 메서드 `tick(quote: Quote) -> list[Fill]`

```python
def tick(self, quote: Quote) -> list[Fill]:
    # 1. quote.symbol에 해당하는 open orders만 본다.
    # 2. is_stale 검사 (caller가 max_age_seconds 정해서 호출 — 본 메서드는 stale 판단 안 함).
    # 3. 각 open order에 대해:
    #    - LIMIT BUY:  quote.ask <= order.limit_price 면 fill at order.limit_price
    #    - LIMIT SELL: quote.bid >= order.limit_price 면 fill at order.limit_price
    #    - STOP_LIMIT: 본 MVP에서는 stop 트리거 검사 후 LIMIT처럼 처리
    #      * BUY:  quote.last >= stop_price 트리거 후 LIMIT BUY 조건 검사
    #      * SELL: quote.last <= stop_price 트리거 후 LIMIT SELL 조건 검사
    #      * 트리거된 상태는 broker가 내부 dict (`_triggered_stops`)에 추적
    # 4. 매치된 주문은 _open_orders에서 제거, Fill 생성하여 반환.
    # 5. 부분 체결은 본 MVP에서 미지원(주문 전체가 한 번에 fill 또는 미fill).
```

가격 정책(보수적): fill 가격 = order.limit_price (호가에서의 spread 개선 없음). 단순화 + 결정론적 테스트.

수량 정책: 전 quantity 한 번에 fill (partial 미지원). 후속 paper-002에서 거래량 기반 partial fill 검토.

Stale quote 정책: broker는 stale 판단 안 함(runtime이 판단). 단, `quote.last <= 0` 같은 명백한 invalid 입력에는 `ValueError`.

#### 새 메서드 `cancel_all(reason: str | None = None) -> int`

세션 종료/킬스위치 발동 시 일괄 취소용.

### 2.3 Cash balance 처리

위 §2.1의 `PaperAccount`에 통합. `PortfolioService.apply_fill`은 cash 모름; cash는 `PaperAccount.apply_fill(fill)`이 책임. 분리 이유: `PortfolioService`는 broker-agnostic 도메인, `PaperAccount`는 paper-specific.

### 2.4 Positions / Realized / Unrealized PnL

- Positions: `PortfolioService` 그대로 (이미 OK).
- Realized PnL: `PortfolioService.snapshot.realized_pnl` 그대로 (이미 OK).
- Unrealized PnL: **신규 `PortfolioSnapshot.unrealized_pnl: Decimal`** 추가. 계산식:
  - 각 position에 대해, `last_price`가 있으면 `(last_price - avg_price) * quantity` (signed: 롱은 +/-, 숏도 부호로 처리). `last_price`가 없으면 0.
- Total PnL: `realized_pnl + unrealized_pnl`. `PortfolioSnapshot.total_pnl` property 추가.

### 2.5 Orders / Fills

- Orders: 기존 `OrderIntent`/`Order`/`BrokerOrder`/`OrderAck` 그대로.
- Fills: §2.1의 `Fill` 신규.
- PaperBroker는 fill을 returns만; 외부에서 PaperAccount에 적용.

### 2.6 Basic 시장가/지정가 시뮬레이션

본 MVP에서는 **지정가(LIMIT) + 손절지정가(STOP_LIMIT)만** 시뮬레이션. 이유:

- 코드베이스 기존 invariant: `OrderType.MARKET` enum에 부재. RiskEngine과 PaperBroker 모두 LIMIT/STOP_LIMIT 외 거절. 사용자 요청 §3-10이 이 invariant를 명시적으로 풀라고 하지 않음.
- 시장가 시뮬레이션은 fill가격 정책(quote.ask로 채울지, 슬리피지를 둘지) 결정이 추가로 필요해 MVP scope 키움.
- 결정: **본 job은 LIMIT/STOP_LIMIT만**. 시장가 paper 시뮬레이션은 별 job(`paper-002`)에서 `OrderType.MARKET` + `ALLOW_PAPER_MARKET_ORDERS` flag + 슬리피지 모델과 함께 도입 후보.

사용자가 본 MVP에 시장가도 포함하길 원하면 plan 승인 전에 알려달라고 코드ex-task에 적시.

### 2.7 Risk checks

기존 `RiskEngine` 그대로 사용. 본 job은 RiskEngine 본문 변경 없음. 이미 다음 검사 통과:

- kill switch
- paper-only
- live disabled
- LIMIT/STOP_LIMIT only
- positive quantity
- symbol allowlist (set 되어 있을 때만)
- max order notional

### 2.8 Order log / Trade log

신규 `app/runtime/paper_journal.py`:

```python
@dataclass(frozen=True)
class OrderLogEntry:
    event: str              # "submitted" | "rejected" | "cancelled" | "filled"
    at: datetime
    oms_id: str
    broker_order_id: str | None
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType
    limit_price: Decimal
    risk_token: str | None
    detail: str | None      # rejection reason or fill ref

@dataclass(frozen=True)
class TradeLogEntry:
    at: datetime
    oms_id: str
    broker_order_id: str
    symbol: str
    side: Side
    quantity: int
    price: Decimal
    commission: Decimal
    risk_token: str
    cash_after: Decimal
    realized_pnl_after: Decimal


class PaperJournal:
    def __init__(self, log_dir: str | os.PathLike | None = None) -> None:
        # log_dir가 None이면 메모리 only (default).
        # log_dir 설정 시 ${log_dir}/orders.jsonl 와 ${log_dir}/trades.jsonl에 append-only JSONL.
        ...

    def record_order(self, entry: OrderLogEntry) -> None: ...
    def record_trade(self, entry: TradeLogEntry) -> None: ...

    @property
    def orders(self) -> list[OrderLogEntry]: ...   # in-memory snapshot
    @property
    def trades(self) -> list[TradeLogEntry]: ...
```

기본 메모리 only. `PAPER_LOG_DIR` env var 설정 시 disk 영속화. 파일 권한 0644(secrets 미포함이라 0600 불요).

### 2.9 Runtime 통합

기존 `PaperRunner`(`app/runtime/paper_runner.py`)와 별개로 **fill까지 완결하는 새 runtime** 추가:

신규 `app/runtime/paper_engine.py`:

```python
class PaperEngine:
    def __init__(self, settings, strategy, oms, broker: PaperBroker,
                 account: PaperAccount, journal: PaperJournal) -> None: ...

    def submit_intents(self, intents: list[OrderIntent]) -> list[OrderAck]:
        # for each intent: OMS.place → record OrderLogEntry("submitted"/"rejected") → return list of acks (or skip rejections)

    def on_quote(self, quote: Quote) -> list[Fill]:
        # 1. broker.tick(quote) → list[Fill]
        # 2. for each fill:
        #     - account.apply_fill(fill)  (raises if insufficient cash → record OrderLogEntry("rejected") and skip)
        #     - journal.record_trade(...)
        #     - journal.record_order(OrderLogEntry("filled", ...))
        # 3. return fills
```

이는 dry-run controller와 별개의 단순 동기 엔진. dry-run은 그대로.

### 2.10 Test cases

신규 테스트 파일:

| 파일 | 핵심 단정 |
| --- | --- |
| `tests/test_fill_model.py` | `Fill` 도메인 invariants (quantity/price/commission/timezone), frozen 검증 |
| `tests/test_paper_account.py` | starting cash, BUY 차감, SELL 가산, 부족 시 raise, equity 계산, PnL 합계 |
| `tests/test_paper_broker_fill.py` | LIMIT BUY/SELL fill 조건, STOP_LIMIT 트리거, 미매치 시 open_orders 유지, cancel_all |
| `tests/test_paper_journal.py` | 메모리 only 기본, log_dir 설정 시 JSONL append, 권한 0644, 파일 invalid 시 self-heal |
| `tests/test_portfolio_unrealized_pnl.py` | unrealized 계산, mark_price 후 갱신, last_price 부재 시 0 |
| `tests/test_paper_engine.py` | submit_intents → OMS 통과, on_quote → fill → account 갱신 → journal 기록, risk reject 경로 |
| `tests/test_paper_end_to_end.py` | **통합**: Strategy(스텁) → OMS → RiskEngine → PaperBroker → tick → Fill → PaperAccount → Journal. 1 BUY 채결 + 1 SELL 채결로 cycle 닫기. realized PnL 정확. |

기존 테스트:

- `tests/test_paper_broker.py` — 기존 단정 유지 + 신규 메서드 추가 케이스.
- `tests/test_portfolio_service.py` — 기존 유지 + unrealized_pnl 단정 추가.
- `tests/test_oms.py` — 변경 없음 (OMS 본문 미접촉).
- `tests/test_paper_runner.py` — 변경 없음 (PaperRunner 미접촉).

### 2.11 Env vars (값 없이 이름만)

기존 그대로:

- `TRADING_MODE` (= `paper`)
- `LIVE_TRADING_ENABLED` (= `false`)
- `PAPER_STARTING_CASH` (`Decimal`, 기존 default 100000)
- `MAX_ORDER_NOTIONAL_USD`, `MAX_OPEN_POSITIONS`, `SYMBOL_ALLOWLIST` (기존)
- `ALLOW_MARKET_ORDERS` (기존, `true`면 load_settings reject)
- `KILL_SWITCH_ENGAGED` (기존)

신설(이 job에서 추가):

- `PAPER_COMMISSION_USD` — 기본 `0`. 모든 fill에 적용되는 평탄 commission. 옵션.
- `PAPER_LOG_DIR` — 기본 미설정(메모리 only). 설정 시 orders.jsonl + trades.jsonl 영속화.
- `PAPER_FILL_POLICY` — `limit` (기본). 향후 `aggressive`/`mid` 등 확장 후보. 본 MVP에서는 `limit`만 수용, 다른 값은 reject.

`.env.example`에 위 3개의 이름 + 한 줄 설명만 추가. 값/placeholder 0건.

### 포함 (In scope) — 요약

위 2.1–2.11 전부.

### 제외 (Out of scope; 절대 만지지 않음)

- 시장가(`OrderType.MARKET`) 시뮬레이션.
- KIS/Alpaca 실 quote 연결, KIS HTTP 호출, 시세 fetch.
- GUI/`app/api/*`/`app/static/*` 변경. `dry_run_report.py` / `dry_run.py` 본문 변경.
- 새 AI agent / LLM 호출 / 새 추천 모듈.
- Partial fill, 슬리피지, market impact.
- Multi-currency. 본 MVP는 USD 단일 통화 가정.
- 시간외 세션 처리. `Session` enum은 있으나 본 MVP는 세션과 무관하게 quote가 들어오면 매칭.
- Live trading 활성 경로.
- `.env` 수정 또는 읽기. 자동 git commit / push / merge / deploy.

---

## 3. 수정해야 할 파일

| 파일 | 동작 |
| --- | --- |
| `projects/paper-trading/app/domain/fills.py` | 신규 — `Fill` frozen dataclass |
| `projects/paper-trading/app/portfolio/account.py` | 신규 — `PaperAccount` + `PaperAccountError` |
| `projects/paper-trading/app/portfolio/service.py` | 수정 — `PortfolioSnapshot.unrealized_pnl`/`total_pnl` 추가 |
| `projects/paper-trading/app/broker/paper.py` | 수정 — `tick(quote)`, `cancel_all`, 내부 `_triggered_stops` |
| `projects/paper-trading/app/runtime/paper_journal.py` | 신규 — `OrderLogEntry`/`TradeLogEntry`/`PaperJournal` |
| `projects/paper-trading/app/runtime/paper_engine.py` | 신규 — `PaperEngine` |
| `projects/paper-trading/app/config.py` | 수정 — `PAPER_COMMISSION_USD`, `PAPER_LOG_DIR`, `PAPER_FILL_POLICY` 추가 |
| `projects/paper-trading/.env.example` | 신설 3개 변수 이름 + 한 줄 설명 |
| `projects/paper-trading/README.md` | `## Paper trading MVP (paper-001)` 단락 추가 |
| `projects/paper-trading/tests/test_fill_model.py` | 신규 |
| `projects/paper-trading/tests/test_paper_account.py` | 신규 |
| `projects/paper-trading/tests/test_paper_broker_fill.py` | 신규 |
| `projects/paper-trading/tests/test_paper_journal.py` | 신규 |
| `projects/paper-trading/tests/test_portfolio_unrealized_pnl.py` | 신규 |
| `projects/paper-trading/tests/test_paper_engine.py` | 신규 |
| `projects/paper-trading/tests/test_paper_end_to_end.py` | 신규 (통합) |
| `projects/paper-trading/tests/test_paper_broker.py` | 기존 + tick/cancel_all 케이스 |
| `projects/paper-trading/tests/test_portfolio_service.py` | 기존 + unrealized 단정 |
| `docs/ai/jobs/paper-001/patch.md` | 신규 — Codex 적용 요약 |

**미변경 (절대)**:
`app/api/*`, `app/static/*`, `app/main.py`, `app/strategy/*`, `app/runtime/dry_run.py`, `app/runtime/dry_run_report.py`, `app/runtime/paper_runner.py`, `app/oms/manager.py`, `app/risk/engine.py`, `app/broker/{base.py, kis*.py, alpaca_paper.py}`, `app/domain/{enums.py, orders.py, market.py, quote.py}`, `.env`, `.gitignore`, `docs/kis/*`, `docs/ai/MASTER_TRADING_ROADMAP.md`, `prompts/*`, `scripts/*`, `imports/*`, mvp-001..api-auth-001 산출물.

---

## 4. Codex 구현 지시문

상세 본문은 `docs/ai/jobs/paper-001/codex-task.md`에 박혀 있음. 요점:

1. **§3 파일 목록만 변경.** 그 외 0건. 특히 GUI/api/static/strategy/runtime(dry_run*)/oms/risk/domain(enums/orders/market/quote)/broker(base/kis*/alpaca_paper) 본문 미접촉.
2. **LIMIT + STOP_LIMIT만** 시뮬레이션. `OrderType.MARKET` 도입 금지.
3. **fill가격 = order.limit_price** (단순 결정론). 슬리피지 0.
4. **Partial fill 금지** — 전 quantity 한 번에 fill 또는 0.
5. **Cash 부족 시 fill 거절** + `OrderLogEntry("rejected", detail="insufficient_cash")`. 주문은 broker open에서 빠지지만 PortfolioService 미변경.
6. **메모리 default**. `PAPER_LOG_DIR` 설정 시에만 JSONL append.
7. **테스트가 외부 네트워크/시세 0건 호출**. Quote는 명시적으로 주입.
8. **secrets 0건**. fake values만 사용. 새 파일에 `appkey`/`appsecret`/`Bearer eyJ` 패턴 0건.
9. **자동 commit/push/merge/deploy 금지**.

---

## 5. 테스트 기준

### 5.1 Unit + Integration

| 카테고리 | 파일 | PASS 기준 |
| --- | --- | --- |
| Fill 모델 | `test_fill_model.py` | invariant 4개, frozen, source 기본값 |
| PaperAccount | `test_paper_account.py` | starting cash, BUY/SELL cash 변화, commission, insufficient_cash raise, equity, total_pnl |
| Broker fill | `test_paper_broker_fill.py` | LIMIT BUY 매치 / 미매치, LIMIT SELL 매치, STOP_LIMIT 트리거 → fill, cancel_all, ValueError on invalid quote |
| Journal | `test_paper_journal.py` | 메모리 only, log_dir 설정 시 두 JSONL append, append-only (기존 라인 변경 0), 권한 0644, invalid 라인 무시 |
| Unrealized PnL | `test_portfolio_unrealized_pnl.py` | 롱/숏 양방향, last_price 갱신 후 변화, last_price 부재 시 0, frozen positions에서 일관 |
| Engine | `test_paper_engine.py` | submit_intents 성공/risk reject 경로, on_quote 후 fill 흐름, journal 기록 누락 0, account 잔액 일치 |
| End-to-end | `test_paper_end_to_end.py` | stub Strategy → 2개 intent → OMS 통과 → broker submit → 2번 tick → BUY fill → SELL fill → realized PnL 정확 + cash 일치 + journal 4개 entry (2 submit + 2 fill) |

### 5.2 회귀

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

- 기존 242 + 신규 약 25–35 모두 PASS.
- 외부 네트워크 호출 0건.
- 기존 dry-run / GUI / KIS 테스트 회귀 0건.

### 5.3 안전 grep (Codex가 patch.md에 기록)

| 패턴 | 범위 | 기대 |
| --- | --- | --- |
| `OrderType.MARKET` 도입 (enum 또는 사용) | 본 job 변경/신설 파일 | 0건 |
| `import requests` / `import httpx` / `import aiohttp` / `import urllib3` | 동 | 0건 |
| `appkey=` / `appsecret=` / `Bearer eyJ` / 실 키 prefix | 동 | 0건 |
| 10자리 이상 연속 숫자 (계좌번호 패턴) | 동 | 0건 |
| `live_trading_enabled = True` 또는 `LIVE_TRADING_ENABLED=true` 설정 코드 | 동 | 0건 |
| `app.api.*` import (GUI 차단 확인) | 신설 `app/runtime/paper_engine.py`, `paper_journal.py` | 0건 |

---

## 6. 리뷰 체크리스트

### 콘텐츠

- [ ] `Fill` 모델이 frozen + invariants 검증 + tz-aware 강제.
- [ ] `PaperAccount.apply_fill`이 cash 차감/가산 + commission + insufficient_cash 거절 모두 처리.
- [ ] `PaperBroker.tick(quote)`가 LIMIT/STOP_LIMIT 매치 후 `_open_orders`에서 제거 + Fill 반환.
- [ ] `PaperJournal`이 메모리 default, `PAPER_LOG_DIR` 설정 시 JSONL append-only.
- [ ] `PortfolioSnapshot.unrealized_pnl` + `total_pnl` 노출.
- [ ] `PaperEngine`이 submit_intents + on_quote 두 메서드로 full cycle 처리.
- [ ] End-to-end 통합 테스트가 BUY→SELL cycle을 닫고 realized PnL 일치 검증.

### 안전

- [ ] `OrderType.MARKET` 도입 0건. 시장가 시뮬레이션 코드 0건.
- [ ] 시뮬레이션이 quote stale 판단을 broker 책임으로 두지 않음 (caller가 결정).
- [ ] live trading 활성화 변경 0건. `live_trading_enabled` 기본 False 유지.
- [ ] LLM/Agent가 broker API 직접 호출하는 새 경로 0건.
- [ ] 모든 새 주문은 `OrderIntent → OMS → RiskEngine → BrokerOrder → PaperBroker` 거침.
- [ ] PaperBroker가 `BrokerOrder` 외 입력으로 fill 만들지 않음.
- [ ] `KisBroker`/`KisMarketDataClient`/`KisAccountClient`/`KisAuthClient` 본문 변경 0건.
- [ ] `.env` 읽기/수정 0건. `.env.example`은 변수 이름 + 한 줄 설명만 추가.
- [ ] GUI 코드(`app/api/`, `app/static/`, dashboard) 변경 0건.
- [ ] `app/runtime/dry_run.py` / `dry_run_report.py` / `paper_runner.py` 본문 변경 0건.

### 테스트 / 프로세스

- [ ] 기존 242 PASS + 신규 25–35 PASS.
- [ ] `compileall` 무오류.
- [ ] 외부 네트워크 호출 0건.
- [ ] `patch.md`에 변경 파일 / 안전 grep / 테스트 결과 / commit-skip 확인 기록.
- [ ] commit / push / merge / 배포 자동화 0건.

### 사람이 직접 해야 할 후속 액션

1. `git status` / `git diff` 직접 확인 후 staging.
2. commit 시 `app/domain/fills.py`, `app/portfolio/account.py`, `app/portfolio/service.py`, `app/broker/paper.py`, `app/runtime/paper_journal.py`, `app/runtime/paper_engine.py`, `app/config.py`, `.env.example`, `README.md`, 새/수정 테스트, `docs/ai/jobs/paper-001/`만 staging.
3. 후속 job 후보:
   - **`paper-002`** — 시장가 시뮬레이션(`OrderType.MARKET` + `ALLOW_PAPER_MARKET_ORDERS` flag + 슬리피지 모델). 별 plan에서 정책 확장 명시.
   - **`paper-003`** — partial fill, 거래량 기반 fill rate, market impact 모델.
   - **`paper-004`** — multi-currency 지원.
   - **`api-market-data-001`** — KIS 현재체결가로 실 Quote 연결 (KIS_1 catalog 활용).
   - **`paper-001-gui`** — GUI에 PaperAccount/Journal 노출 (사용자가 GUI 재개 신호 보낸 후).
