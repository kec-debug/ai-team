# Codex Task — paper-001: 내부 paper trading MVP (fill 시뮬레이션 + cash + journal + 통합)

## 0. 전제

- 상위 plan: `docs/ai/jobs/paper-001/plan.md`.
- 기존 land: api-auth-001까지 완료. 242 PASS.
- 본 job은 코드 변경 + 신규 테스트. GUI/api/strategy/runtime(dry_run*)/oms/risk/broker(base/kis*/alpaca_paper)/domain(enums/orders/market/quote) 본문 미접촉.

### Hard rules (위반 시 BLOCK)

- `OrderType.MARKET` 도입 금지. enum/사용 전부.
- 시장가(market order) 시뮬레이션 로직 추가 금지.
- 외부 HTTP lib(`requests`/`httpx`/`aiohttp`/`urllib3`) import 금지.
- `.env` 읽기/수정 금지. `.env.example`은 변수 이름 + 한 줄 설명만(값/placeholder 0건).
- 실 app key / secret / token / 계좌번호 / Bearer 토큰 패턴 기록 금지. 테스트는 `"fake-*"` 또는 8자리 이하 fake 숫자만.
- live trading 활성화 / 실주문 / RiskEngine 우회 / OMS 우회 / Strategy의 broker 직접 호출 / LLM의 broker 직접 호출 금지.
- 자동 `git commit` / `push` / `merge` / `deploy` 금지.
- GUI 코드(`app/api/`, `app/static/`, `app/main.py`) 변경 금지.
- `app/runtime/dry_run.py`, `app/runtime/dry_run_report.py`, `app/runtime/paper_runner.py` 본문 변경 금지(import 추가 외 변경 없음 — 본 job에서는 import도 추가 안 함).
- `KisBroker`/`KisAccountClient`/`KisMarketDataClient`/`KisAuthClient` 본문 변경 금지.

---

## §A. 신설 — `projects/paper-trading/app/domain/fills.py`

```python
"""Fill domain model — paper broker execution result.

Provenance via ``source`` (default ``"paper_internal"``) lets downstream
consumers tell paper-simulated fills apart from any future real-broker fills.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.enums import Side


@dataclass(frozen=True)
class Fill:
    symbol: str
    side: Side
    quantity: int
    price: Decimal
    filled_at: datetime
    broker_order_id: str
    oms_id: str
    risk_token: str
    commission: Decimal = Decimal("0")
    source: str = "paper_internal"

    def __post_init__(self) -> None:
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be uppercase")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.price <= 0:
            raise ValueError("price must be positive")
        if self.commission < 0:
            raise ValueError("commission must be non-negative")
        if self.filled_at.tzinfo is None:
            raise ValueError("filled_at must be timezone-aware")
        if not self.broker_order_id:
            raise ValueError("broker_order_id required")
        if not self.oms_id:
            raise ValueError("oms_id required")
        if not self.risk_token:
            raise ValueError("risk_token required")
        if not self.source:
            raise ValueError("source required")
```

---

## §B. 신설 — `projects/paper-trading/app/portfolio/account.py`

```python
"""Paper account: cash balance + portfolio aggregation."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.config import Settings
from app.domain.enums import Side
from app.domain.fills import Fill
from app.portfolio.service import PortfolioService


class PaperAccountError(Exception):
    """Paper-account business rule violation (e.g. insufficient cash)."""


@dataclass
class PaperAccount:
    cash: Decimal
    starting_cash: Decimal
    portfolio: PortfolioService
    base_currency: str = "USD"

    @classmethod
    def from_settings(cls, settings: Settings, portfolio: PortfolioService | None = None) -> "PaperAccount":
        return cls(
            cash=settings.paper_starting_cash,
            starting_cash=settings.paper_starting_cash,
            portfolio=portfolio or PortfolioService(),
        )

    def apply_fill(self, fill: Fill) -> None:
        notional = Decimal(fill.quantity) * fill.price
        if fill.side is Side.BUY:
            cost = notional + fill.commission
            if self.cash - cost < Decimal("0"):
                raise PaperAccountError("insufficient_cash")
            self.cash -= cost
        else:
            self.cash += notional - fill.commission
        self.portfolio.apply_fill(
            symbol=fill.symbol,
            side=fill.side,
            quantity=fill.quantity,
            price=fill.price,
            commission=fill.commission,
        )

    def equity(self) -> Decimal:
        snap = self.portfolio.get_snapshot()
        return self.cash + snap.market_value

    def total_realized_pnl(self) -> Decimal:
        return self.portfolio.get_snapshot().realized_pnl

    def total_unrealized_pnl(self) -> Decimal:
        return self.portfolio.get_snapshot().unrealized_pnl

    def total_pnl(self) -> Decimal:
        snap = self.portfolio.get_snapshot()
        return snap.realized_pnl + snap.unrealized_pnl
```

---

## §C. 수정 — `projects/paper-trading/app/portfolio/service.py`

기존 파일을 다음 변경만 적용:

### C.1 `PortfolioSnapshot`에 `unrealized_pnl` 필드 추가

```python
@dataclass
class PortfolioSnapshot:
    positions: dict[str, Position] = field(default_factory=dict)
    realized_pnl: Decimal = Decimal("0")
    market_value: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_pnl(self) -> Decimal:
        return self.realized_pnl + self.unrealized_pnl
```

### C.2 `_recalculate_totals` 본문에 `unrealized_pnl` 갱신 추가

```python
def _recalculate_totals(self) -> None:
    realized = Decimal("0")
    market_value = Decimal("0")
    unrealized = Decimal("0")
    for position in self._snapshot.positions.values():
        realized += position.realized_pnl
        market_value += position.market_value
        if position.last_price is not None and position.quantity != 0:
            unrealized += (position.last_price - position.avg_price) * Decimal(position.quantity)
    self._snapshot.realized_pnl = realized
    self._snapshot.market_value = market_value
    self._snapshot.unrealized_pnl = unrealized
    self._snapshot.updated_at = datetime.now(timezone.utc)
```

### C.3 그 외 미변경

`Position` dataclass, `apply_fill`, `mark_price`는 손대지 말 것.

---

## §D. 수정 — `projects/paper-trading/app/broker/paper.py`

기존 클래스에 메서드 추가 + 내부 상태 추가. 기존 `submit`/`cancel`/`open_orders`/`positions` 시그니처와 본문은 그대로 보존.

### D.1 import 확장

```python
import secrets
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable

from app.domain.enums import OrderType, Side, TradingMode
from app.domain.fills import Fill
from app.domain.orders import BrokerOrder, OrderAck
from app.domain.quote import Quote
```

### D.2 `__init__` 확장

```python
def __init__(self) -> None:
    self._open_orders: dict[str, BrokerOrder] = {}
    self._positions: dict[str, int] = {}
    self._triggered_stops: set[str] = set()  # broker_order_id set
```

### D.3 새 메서드 `tick(quote: Quote) -> list[Fill]`

```python
def tick(self, quote: Quote) -> list[Fill]:
    if quote.last <= 0 or quote.bid <= 0 or quote.ask <= 0:
        raise ValueError("invalid quote: non-positive price")
    fills: list[Fill] = []
    now = datetime.now(timezone.utc)
    matched_ids: list[str] = []
    for broker_order_id, order in self._open_orders.items():
        if order.symbol != quote.symbol:
            continue
        if order.order_type is OrderType.LIMIT:
            if not self._limit_fillable(order, quote):
                continue
            fill_price = order.limit_price
        elif order.order_type is OrderType.STOP_LIMIT:
            if broker_order_id not in self._triggered_stops:
                if not self._stop_triggered(order, quote):
                    continue
                self._triggered_stops.add(broker_order_id)
            if not self._limit_fillable(order, quote):
                continue
            fill_price = order.limit_price
        else:
            continue
        fills.append(
            Fill(
                symbol=order.symbol,
                side=order.side,
                quantity=order.quantity,
                price=fill_price,
                filled_at=now,
                broker_order_id=broker_order_id,
                oms_id=order.oms_id,
                risk_token=order.risk_token,
            )
        )
        matched_ids.append(broker_order_id)
    for broker_order_id in matched_ids:
        self._open_orders.pop(broker_order_id, None)
        self._triggered_stops.discard(broker_order_id)
        order = None  # cleared above
    # update broker-local positions tally for the existing Protocol .positions() method
    for fill in fills:
        signed = fill.quantity if fill.side is Side.BUY else -fill.quantity
        self._positions[fill.symbol] = self._positions.get(fill.symbol, 0) + signed
    return fills


@staticmethod
def _limit_fillable(order: BrokerOrder, quote: Quote) -> bool:
    if order.side is Side.BUY:
        return quote.ask <= order.limit_price
    return quote.bid >= order.limit_price


@staticmethod
def _stop_triggered(order: BrokerOrder, quote: Quote) -> bool:
    if order.stop_price is None:
        return False
    if order.side is Side.BUY:
        return quote.last >= order.stop_price
    return quote.last <= order.stop_price
```

### D.4 새 메서드 `cancel_all(reason: str | None = None) -> int`

```python
def cancel_all(self, reason: str | None = None) -> int:
    count = len(self._open_orders)
    self._open_orders.clear()
    self._triggered_stops.clear()
    return count
```

### D.5 기존 `submit` 본문 미변경

LIMIT/STOP_LIMIT 외 거절 그대로. 시장가 도입 금지.

---

## §E. 신설 — `projects/paper-trading/app/runtime/paper_journal.py`

```python
"""Paper trading journal — order log + trade log.

In-memory by default. If ``log_dir`` is provided, also writes append-only
JSONL to ``orders.jsonl`` and ``trades.jsonl`` in that directory.

The journal does not store secrets, so file permissions are 0o644.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Iterable

from app.domain.enums import OrderType, Side


@dataclass(frozen=True)
class OrderLogEntry:
    event: str
    at: datetime
    oms_id: str
    broker_order_id: str | None
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType
    limit_price: Decimal
    risk_token: str | None
    detail: str | None = None


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


def _serialize(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (Side, OrderType)):
        return value.value
    return value


def _to_json_line(record) -> str:
    payload = {k: _serialize(v) for k, v in asdict(record).items()}
    return json.dumps(payload, ensure_ascii=False)


class PaperJournal:
    def __init__(self, log_dir: str | os.PathLike[str] | None = None) -> None:
        self._orders: list[OrderLogEntry] = []
        self._trades: list[TradeLogEntry] = []
        self._log_dir: Path | None = Path(log_dir) if log_dir else None
        if self._log_dir is not None:
            self._log_dir.mkdir(parents=True, exist_ok=True)

    def record_order(self, entry: OrderLogEntry) -> None:
        self._orders.append(entry)
        if self._log_dir is not None:
            self._append(self._log_dir / "orders.jsonl", _to_json_line(entry))

    def record_trade(self, entry: TradeLogEntry) -> None:
        self._trades.append(entry)
        if self._log_dir is not None:
            self._append(self._log_dir / "trades.jsonl", _to_json_line(entry))

    @property
    def orders(self) -> list[OrderLogEntry]:
        return list(self._orders)

    @property
    def trades(self) -> list[TradeLogEntry]:
        return list(self._trades)

    @staticmethod
    def _append(path: Path, line: str) -> None:
        with path.open("a", encoding="utf-8") as fh:
            fh.write(line)
            fh.write("\n")
```

---

## §F. 신설 — `projects/paper-trading/app/runtime/paper_engine.py`

```python
"""Paper trading engine: ties Strategy outputs to fills.

- ``submit_intents`` takes ``OrderIntent`` list, runs each through OMS, and
  records OrderLogEntry per result.
- ``on_quote`` calls broker.tick(quote), applies each Fill to PaperAccount,
  and records TradeLogEntry + OrderLogEntry("filled").
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from app.broker.paper import PaperBroker
from app.config import Settings
from app.domain.enums import OrderType, Side
from app.domain.fills import Fill
from app.domain.orders import OrderAck, OrderIntent
from app.domain.quote import Quote
from app.oms.manager import OMS
from app.portfolio.account import PaperAccount, PaperAccountError
from app.runtime.paper_journal import OrderLogEntry, PaperJournal, TradeLogEntry


class PaperEngine:
    def __init__(
        self,
        settings: Settings,
        oms: OMS,
        broker: PaperBroker,
        account: PaperAccount,
        journal: PaperJournal,
    ) -> None:
        self._settings = settings
        self._oms = oms
        self._broker = broker
        self._account = account
        self._journal = journal

    def submit_intents(self, intents: Iterable[OrderIntent]) -> list[OrderAck]:
        acks: list[OrderAck] = []
        for intent in intents:
            now = datetime.now(timezone.utc)
            try:
                ack = self._oms.place(intent)
            except RuntimeError as exc:
                self._journal.record_order(
                    OrderLogEntry(
                        event="rejected",
                        at=now,
                        oms_id="",
                        broker_order_id=None,
                        symbol=intent.symbol,
                        side=intent.side,
                        quantity=intent.quantity,
                        order_type=intent.order_type,
                        limit_price=intent.limit_price,
                        risk_token=None,
                        detail=str(exc),
                    )
                )
                continue
            self._journal.record_order(
                OrderLogEntry(
                    event="submitted",
                    at=now,
                    oms_id=ack.oms_id,
                    broker_order_id=ack.broker_order_id,
                    symbol=intent.symbol,
                    side=intent.side,
                    quantity=intent.quantity,
                    order_type=intent.order_type,
                    limit_price=intent.limit_price,
                    risk_token=None,
                    detail=ack.status,
                )
            )
            acks.append(ack)
        return acks

    def on_quote(self, quote: Quote) -> list[Fill]:
        fills = self._broker.tick(quote)
        applied: list[Fill] = []
        for fill in fills:
            try:
                self._account.apply_fill(fill)
            except PaperAccountError as exc:
                self._journal.record_order(
                    OrderLogEntry(
                        event="rejected",
                        at=fill.filled_at,
                        oms_id=fill.oms_id,
                        broker_order_id=fill.broker_order_id,
                        symbol=fill.symbol,
                        side=fill.side,
                        quantity=fill.quantity,
                        order_type=OrderType.LIMIT,
                        limit_price=fill.price,
                        risk_token=fill.risk_token,
                        detail=str(exc),
                    )
                )
                continue
            snap = self._account.portfolio.get_snapshot()
            self._journal.record_trade(
                TradeLogEntry(
                    at=fill.filled_at,
                    oms_id=fill.oms_id,
                    broker_order_id=fill.broker_order_id,
                    symbol=fill.symbol,
                    side=fill.side,
                    quantity=fill.quantity,
                    price=fill.price,
                    commission=fill.commission,
                    risk_token=fill.risk_token,
                    cash_after=self._account.cash,
                    realized_pnl_after=snap.realized_pnl,
                )
            )
            self._journal.record_order(
                OrderLogEntry(
                    event="filled",
                    at=fill.filled_at,
                    oms_id=fill.oms_id,
                    broker_order_id=fill.broker_order_id,
                    symbol=fill.symbol,
                    side=fill.side,
                    quantity=fill.quantity,
                    order_type=__import__("app.domain.enums", fromlist=["OrderType"]).OrderType.LIMIT,
                    limit_price=fill.price,
                    risk_token=fill.risk_token,
                    detail="fill",
                )
            )
            applied.append(fill)
        return applied
```

> 주: 위 본문은 `from app.domain.enums import OrderType, Side`를 이미 import에 포함하고 `OrderType.LIMIT`을 직접 사용한다. 추가 import 변경 불요.

---

## §G. 수정 — `projects/paper-trading/app/config.py`

`Settings` dataclass에 다음 필드 추가(기존 필드 뒤에). 안전 기본값.

```python
paper_commission_usd: Decimal = Decimal("0")
paper_log_dir: str | None = field(default=None, repr=False)
paper_fill_policy: str = "limit"
```

`load_settings()`에 다음 read 라인 추가:

```python
paper_commission_usd=_decimal_env("PAPER_COMMISSION_USD", Decimal("0")),
paper_log_dir=_str_env("PAPER_LOG_DIR"),
paper_fill_policy=_str_env("PAPER_FILL_POLICY") or "limit",
```

`load_settings()`에 검증 추가:

```python
paper_fill_policy = _str_env("PAPER_FILL_POLICY") or "limit"
if paper_fill_policy not in {"limit"}:
    raise ValueError(f"invalid PAPER_FILL_POLICY: {paper_fill_policy!r}")
```

(코드 흐름에 맞게 변수 캡처 + return Settings(...) 호출에서 사용. 기존 라인 삭제 금지.)

---

## §H. 수정 — `projects/paper-trading/.env.example`

파일 끝에 다음 블록만 추가. 기존 라인 변경 금지.

```
# --- Paper trading MVP (paper-001) ---
# PAPER_COMMISSION_USD   optional, default 0. flat commission per fill (Decimal)
# PAPER_LOG_DIR          optional, default empty. when set, writes orders.jsonl + trades.jsonl
# PAPER_FILL_POLICY      optional, default "limit". only "limit" accepted in paper-001
```

---

## §I. 수정 — `projects/paper-trading/README.md`

파일 끝에 다음 단락만 추가. 기존 단락 변경 금지.

```markdown
## Paper trading MVP (paper-001)

내부 paper trading의 최소 동작 완결판입니다.

- 모든 주문은 `Strategy → OMS → RiskEngine → PaperBroker` 체인 통과.
- `PaperBroker.tick(quote)`가 LIMIT/STOP_LIMIT 주문을 quote에 매치해 `Fill`을 만들고, `PaperAccount.apply_fill`이 cash·positions·PnL을 갱신합니다.
- `PaperJournal`이 orders + trades 로그를 메모리에 기록합니다. `PAPER_LOG_DIR`를 설정하면 JSONL 두 파일로 영속화합니다.
- `OrderType.MARKET`은 본 MVP 범위 외. 시장가 시뮬레이션은 별 job에서 추가됩니다.
- 실 broker API 호출 0건. KIS/Alpaca 시세는 본 MVP 범위 외 — 호출자가 Quote를 직접 주입합니다.
```

---

## §J. 신설 테스트 본문 (요지만)

각 파일은 다음 카테고리 단정을 포함. Codex는 한 파일당 5–8개 테스트 함수를 작성. 외부 네트워크 호출 0건. fake 값만 사용.

### J.1 `tests/test_fill_model.py`

- `Fill` 생성 happy path.
- `symbol` 소문자 → `ValueError`.
- `quantity <= 0` → `ValueError`.
- `price <= 0` → `ValueError`.
- `commission < 0` → `ValueError`.
- `filled_at`이 naive → `ValueError`.
- `broker_order_id`/`oms_id`/`risk_token`/`source` 빈 문자열 → `ValueError`.
- `frozen=True` 검증 (`dataclasses.FrozenInstanceError`).

### J.2 `tests/test_paper_account.py`

- `from_settings`로 starting_cash 일치.
- BUY fill 후 cash 차감 일치(commission 포함).
- SELL fill 후 cash 가산.
- BUY가 cash 초과 → `PaperAccountError("insufficient_cash")` + 잔액/portfolio 미변경.
- `equity` = cash + market_value.
- `total_realized_pnl` / `total_unrealized_pnl` / `total_pnl` 일치.

### J.3 `tests/test_paper_broker_fill.py`

- `submit` 후 `tick` 미매치 시 open_orders 유지.
- LIMIT BUY: quote.ask = limit_price 이하 → fill at limit_price.
- LIMIT SELL: quote.bid >= limit_price → fill at limit_price.
- LIMIT BUY 미매치 (quote.ask > limit) → 미체결.
- STOP_LIMIT BUY: quote.last >= stop, 그 후 LIMIT 조건 충족 → fill.
- STOP_LIMIT 트리거 후 다음 tick에서 LIMIT 조건 미충족 → 여전히 open, _triggered_stops 보존.
- `cancel_all` → open_orders 전부 비우고 count 반환.
- `tick(quote)` 입력 quote.last/bid/ask 중 하나가 ≤0 → `ValueError`.

### J.4 `tests/test_paper_journal.py`

- 메모리 only: `record_order`/`record_trade` 후 `.orders`/`.trades` 길이.
- `log_dir` 설정: orders.jsonl + trades.jsonl 생성, 라인 수 일치, append-only (두 번 호출 후 두 줄).
- JSON line 파싱 시 `Decimal` → str, `datetime` → ISO, `Side/OrderType` → value.
- `log_dir`가 디렉터리 미존재 시 자동 생성.
- 파일 권한 검사 (가능한 경우 0o644).

### J.5 `tests/test_portfolio_unrealized_pnl.py`

- 롱 position + last_price > avg → 양의 unrealized.
- 숏 position + last_price < avg → 양의 unrealized (숏 이익).
- last_price 없음 → unrealized = 0.
- mark_price 갱신 후 recalc → unrealized 변경.
- `total_pnl` = realized + unrealized.

### J.6 `tests/test_paper_engine.py`

- `submit_intents` 정상 → ack 반환 + journal "submitted" 기록.
- `submit_intents` RiskEngine reject → ack 없음 + journal "rejected" 기록.
- `on_quote` 후 fill 없음 → 빈 list + journal 변경 없음.
- `on_quote` 후 fill 있음 → account.cash 갱신 + journal "filled" + trade 기록.
- BUY fill cash 부족 → journal "rejected"(insufficient_cash) + account 미변경.

### J.7 `tests/test_paper_end_to_end.py` (통합)

다음 시나리오를 명시적으로:

1. `Settings`: `trading_mode=PAPER`, `paper_starting_cash=10000`, `paper_commission_usd=0`.
2. `PaperBroker`, `RiskEngine`, `OMS` 와이어.
3. `PaperAccount.from_settings(settings)`.
4. `PaperJournal()` (메모리).
5. `PaperEngine(settings, oms, broker, account, journal)`.
6. Stub Strategy 또는 직접 `OrderIntent` 생성:
   - intent1: BUY AAPL 10주 @ $100 LIMIT.
   - intent2: SELL AAPL 10주 @ $110 LIMIT.
7. `engine.submit_intents([intent1, intent2])` → 두 ack.
8. `engine.on_quote(Quote(symbol="AAPL", last=99, bid=98.5, ask=99.5, volume=1000, timestamp=tz, source="test"))` → BUY fill (ask=99.5 ≤ 100).
9. `engine.on_quote(Quote(symbol="AAPL", last=111, bid=110.5, ask=111.5, volume=1000, timestamp=tz, source="test"))` → SELL fill (bid=110.5 ≥ 110).
10. 검증:
    - `account.cash == 10000 - 10*100 + 10*110 == 10100`.
    - `account.total_realized_pnl == 10 * (110 - 100) == 100`.
    - `account.portfolio.get_snapshot().positions["AAPL"].quantity == 0`.
    - `journal.orders` length == 4 (2 submitted + 2 filled).
    - `journal.trades` length == 2.

### J.8 기존 테스트 보강

- `tests/test_paper_broker.py`: 기존 happy/reject 케이스 유지. 새 케이스 1–2 추가 (cancel_all, tick noop).
- `tests/test_portfolio_service.py`: 기존 유지. `unrealized_pnl` 단정 1–2 추가.

---

## §K. 적용 절차

1. §A, §B, §E, §F의 신규 파일 작성.
2. §C, §D, §G에 따라 기존 파일 수정.
3. §H에 따라 `.env.example` 끝에 한 블록 추가.
4. §I에 따라 README 끝에 한 단락 추가.
5. §J의 7개 신규 테스트 파일 작성 + §J.8 기존 2개 테스트 확장.
6. 안전 grep:

   ```bash
   cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
   git diff --stat
   # OrderType.MARKET 도입 0건
   git diff -- app/ tests/ | grep -E "OrderType\.MARKET|MARKET\s*=\s*\"market\"" || echo "market-grep: clean"
   # 외부 HTTP lib 미도입
   git diff -- app/ tests/ | grep -E "import requests|import httpx|import aiohttp|import urllib3" || echo "http-lib-grep: clean"
   # secrets 패턴 미도입
   git diff -- app/ tests/ .env.example README.md | grep -E "PSNFD|PKID|AKIA|sk-|ghp_|Bearer eyJ|appkey=|appsecret=|\b\d{10,}\b" || echo "secret-grep: clean"
   # GUI 미접촉
   git diff --stat -- app/api/ app/static/ app/main.py | grep -v '^$' && echo "GUI changed — BLOCK" || echo "gui-grep: clean"
   # dry_run 미접촉
   git diff --stat -- app/runtime/dry_run.py app/runtime/dry_run_report.py app/runtime/paper_runner.py | grep -v '^$' && echo "dry_run changed — BLOCK" || echo "dry-run-grep: clean"
   ```

   모든 grep 라벨이 `clean`이어야 함.

7. 테스트:

   ```bash
   .venv/bin/python -m compileall app tests
   .venv/bin/python -m pytest -p no:cacheprovider
   ```

   - 기존 242 + 신규 약 25–35 모두 PASS.
   - 회귀 0건.
8. `docs/ai/jobs/paper-001/patch.md` 작성. 다음 8개 섹션:
   - Implementation Summary
   - 변경 파일 목록(plan §3과 일치)
   - 신규 도메인/클래스/메서드 요약 (`Fill`, `PaperAccount`, `PaperJournal`, `PaperEngine`, `PaperBroker.tick`, `unrealized_pnl`)
   - 안전 grep 결과 (위 6개 라벨 × `clean` 확인)
   - 테스트 결과 (전체 PASS 수치)
   - `compileall` 결과
   - 정책/안전 invariant 확인 (LIMIT only, OrderType.MARKET 부재, live 미활성, OMS/Risk 우회 0건, GUI 미접촉, dry_run 미접촉)
   - commit/push/merge 미실행 확인
9. `git commit` / `push` / `merge` / 배포 **미실행**.

---

## §L. Codex가 절대 하지 말아야 할 것 (반복)

- `OrderType.MARKET` 추가, `ALLOW_MARKET_ORDERS` 기본값 변경, `live_trading_enabled=True` 코드 추가.
- 시장가(market) 시뮬레이션 로직.
- partial fill 또는 슬리피지 모델.
- 외부 HTTP lib 도입.
- `KisBroker`/`KisAccountClient`/`KisMarketDataClient`/`KisAuthClient` 본문 변경.
- `dry_run.py`, `dry_run_report.py`, `paper_runner.py` 본문 변경.
- `app/api/`, `app/static/`, `app/main.py` 변경.
- `app/strategy/*`, `app/oms/manager.py`, `app/risk/engine.py` 본문 변경.
- `app/domain/{enums,orders,market,quote}.py` 변경.
- `.env` 읽기/수정.
- 사용자 app key/secret/계좌번호/token을 어떤 코드/문서/테스트에도 기록.
- 실제 broker 호스트로의 네트워크 호출하는 테스트.
- 자동 git commit/push/merge/deploy.

---

## §M. 완료 조건

- §A~§J의 파일이 본 codex-task 본문에 부합하게 작성됨.
- 안전 grep 모든 라벨 `clean`.
- 전체 `pytest` PASS, `compileall` 무오류.
- `patch.md`에 §K.8의 8개 섹션 기록.
- 사람이 직접 staging/commit하도록 변경만 남기고 종료.
