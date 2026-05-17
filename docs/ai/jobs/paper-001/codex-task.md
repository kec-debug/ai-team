# Codex Task — paper-001 (확장판): 내부 paper trading MVP 6개 기능 일괄

## 0. 전제

- 상위 plan: `docs/ai/jobs/paper-001/plan.md` (필독). 6개 기능 모두 포함:
  1. LIMIT/STOP_LIMIT/**MARKET** 시뮬레이션
  2. **Partial fill** (volume 비율 기반)
  3. **Quote staleness** 검사 in broker
  4. **Session/장중 시간** 검사
  5. Cash + Realized/Unrealized PnL (multi-currency)
  6. **Multi-currency** (USD/KRW 등 분리 보관, FX 변환 없음)
- 사전 land: api-auth-001까지 완료, 242 PASS.
- 본 job은 8단계 phase로 순차 적용. 각 phase 끝에 부분 테스트 실행 권장.

### Hard rules (위반 시 BLOCK)

- `OrderType.MARKET` 도입은 본 job에서 처음 허용. 단 3중 가드(`ALLOW_PAPER_MARKET_ORDERS=true` + `TradingMode=PAPER` + `live_trading_enabled=False`) 통과해야 RiskEngine 승인. 셋 중 하나라도 깨지면 reject.
- 외부 HTTP lib(`requests`/`httpx`/`aiohttp`/`urllib3`) import 금지.
- `.env` 읽기/수정 금지. `.env.example`은 변수 이름 + 한 줄 설명만.
- 실 app key/secret/token/계좌번호 기록 금지. fake 값만.
- live trading 활성화 / 실주문 / RiskEngine 우회 / OMS 우회 / Strategy의 broker 직접 호출 / LLM의 broker 직접 호출 금지.
- GUI(`app/api/`, `app/static/`, `app/main.py`) 변경 금지.
- `app/runtime/dry_run.py`, `dry_run_report.py`, `paper_runner.py` 본문 변경 금지.
- `KisBroker`/`KisAccountClient`/`KisMarketDataClient`/`KisAuthClient`/`KisHttpClient` 본문 변경 금지.
- **FX 변환 / 환율 적용 0건**. 통화별로 분리 보관 + 분리 보고만.
- 자동 git commit/push/merge/deploy 금지.

---

## §Phase 1 — 도메인 enums + orders + quote + fills

### §1.A 수정 — `app/domain/enums.py`

```python
from enum import Enum


class TradingMode(str, Enum):
    PAPER = "paper"
    LIVE = "live"


class Side(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    LIMIT = "limit"
    STOP_LIMIT = "stop_limit"
    MARKET = "market"


class Session(str, Enum):
    PRE_MARKET = "pre_market"
    REGULAR = "regular"
    AFTER_HOURS = "after_hours"
    CLOSED = "closed"
```

`OrderType.MARKET` 새로 추가됨. **다른 enum은 변경 금지.**

### §1.B 수정 — `app/domain/orders.py`

기존 dataclass에 `currency: str = "USD"` 필드 추가. 기존 invariant + 새 invariant:

```python
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.enums import OrderType, Side, TradingMode


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType
    limit_price: Decimal
    stop_price: Decimal | None = None
    client_tag: str | None = None
    quote_timestamp: datetime | None = None
    currency: str = "USD"

    def __post_init__(self) -> None:
        if self.symbol != self.symbol.upper():
            raise ValueError("symbol must be uppercase")
        if self.quantity <= 0:
            raise ValueError("quantity must be positive")
        if self.limit_price <= 0:
            raise ValueError("limit_price must be positive (MARKET intents use expected fill price)")
        if not self.currency.isascii() or len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError("currency must be 3-letter uppercase ISO code")


@dataclass(frozen=True)
class Order:
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType
    limit_price: Decimal
    risk_token: str
    created_at: datetime
    stop_price: Decimal | None = None
    client_tag: str | None = None
    currency: str = "USD"


@dataclass(frozen=True)
class BrokerOrder:
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType
    limit_price: Decimal
    risk_token: str
    created_at: datetime
    oms_id: str
    submitted_at: datetime
    stop_price: Decimal | None = None
    client_tag: str | None = None
    quote_timestamp: datetime | None = None
    currency: str = "USD"


@dataclass(frozen=True)
class OrderAck:
    oms_id: str
    broker_order_id: str | None
    status: str
    mode: TradingMode
```

> `limit_price>0` 단정 유지(MARKET intent도 expected fill price를 limit_price에 채워 와야 RiskEngine notional 검증을 통과한다는 plan §2.3 결정).

### §1.C 수정 — `app/domain/quote.py`

기존 `Quote` frozen dataclass에 `session: Session | None = None`, `currency: str = "USD"` 추가. invariant 보강. 다른 메서드(`spread_pct`, `is_stale`)는 변경 금지.

```python
# 기존 import에 추가:
from app.domain.enums import Session
```

`Quote` dataclass의 필드에 다음 라인 추가(`source` 뒤에):

```python
session: Session | None = None
currency: str = "USD"
```

`__post_init__`에 다음 단정 추가(기존 단정 뒤에):

```python
if not self.currency.isascii() or len(self.currency) != 3 or not self.currency.isupper():
    raise ValueError("currency must be 3-letter uppercase ISO code")
if self.session is not None and not isinstance(self.session, Session):
    raise ValueError("session must be Session enum or None")
```

기존 `test_quote_model.py`는 default 값을 사용하므로 회귀 없음.

### §1.D 신설 — `app/domain/fills.py`

```python
"""Fill domain model — paper broker execution result."""

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
    currency: str = "USD"
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
        if not self.currency.isascii() or len(self.currency) != 3 or not self.currency.isupper():
            raise ValueError("currency must be 3-letter uppercase ISO code")
```

---

## §Phase 2 — PortfolioService dict 시그니처

### §2.A 수정 — `app/portfolio/service.py`

`Position`에 `currency: str = "USD"` 필드 추가. `PortfolioSnapshot`은 **기존 단일 `Decimal` 필드를 그대로 유지**(`app/api/routes.py`가 직접 읽고 있어 후방호환 필수) + **새 `_per_currency: dict[str, Decimal]` 3개 필드 추가**. 단일 필드는 모든 통화 합산(단일 통화 기본 케이스에선 정확). `apply_fill` 시그니처에 `currency` 인자 추가.

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal

from app.domain.enums import Side


@dataclass
class Position:
    symbol: str
    quantity: int = 0
    avg_price: Decimal = Decimal("0")
    realized_pnl: Decimal = Decimal("0")
    last_price: Decimal | None = None
    currency: str = "USD"
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def market_value(self) -> Decimal:
        price = self.last_price if self.last_price is not None else self.avg_price
        return abs(self.quantity) * price


@dataclass
class PortfolioSnapshot:
    positions: dict[str, Position] = field(default_factory=dict)
    # Legacy single Decimal totals: sum across all positions regardless of currency.
    # Mathematically meaningful only when all positions share a currency (default USD case).
    # Multi-currency callers must read the *_per_currency dicts below.
    realized_pnl: Decimal = Decimal("0")
    market_value: Decimal = Decimal("0")
    unrealized_pnl: Decimal = Decimal("0")
    # New multi-currency-aware breakdowns. Empty dict if no positions.
    realized_pnl_per_currency: dict[str, Decimal] = field(default_factory=dict)
    market_value_per_currency: dict[str, Decimal] = field(default_factory=dict)
    unrealized_pnl_per_currency: dict[str, Decimal] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def total_pnl_per_currency(self) -> dict[str, Decimal]:
        currencies = set(self.realized_pnl_per_currency) | set(self.unrealized_pnl_per_currency)
        return {
            c: self.realized_pnl_per_currency.get(c, Decimal("0"))
               + self.unrealized_pnl_per_currency.get(c, Decimal("0"))
            for c in currencies
        }


class PortfolioService:
    def __init__(self) -> None:
        self._snapshot = PortfolioSnapshot()

    def get_snapshot(self) -> PortfolioSnapshot:
        self._recalculate_totals()
        return self._snapshot

    def apply_fill(
        self,
        symbol: str,
        side: Side,
        quantity: int,
        price: Decimal,
        commission: Decimal = Decimal("0"),
        currency: str = "USD",
    ) -> Position:
        if quantity <= 0:
            raise ValueError("fill quantity must be positive")
        if price <= 0:
            raise ValueError("fill price must be positive")
        symbol = symbol.upper()
        position = self._snapshot.positions.get(symbol)
        if position is None:
            position = Position(symbol=symbol, currency=currency)
        elif position.currency != currency:
            raise ValueError(f"position {symbol} currency mismatch: {position.currency} vs {currency}")
        signed_qty = quantity if side == Side.BUY else -quantity
        old_qty = position.quantity
        new_qty = old_qty + signed_qty
        if old_qty == 0 or (old_qty > 0 and signed_qty > 0) or (old_qty < 0 and signed_qty < 0):
            gross_cost = abs(old_qty) * position.avg_price + abs(signed_qty) * price
            position.avg_price = gross_cost / abs(new_qty) if new_qty else Decimal("0")
        else:
            closing_qty = min(abs(old_qty), abs(signed_qty))
            pnl_per_unit = price - position.avg_price
            if old_qty < 0:
                pnl_per_unit = -pnl_per_unit
            position.realized_pnl += closing_qty * pnl_per_unit - commission
            if new_qty == 0:
                position.avg_price = Decimal("0")
            elif (old_qty > 0 > new_qty) or (old_qty < 0 < new_qty):
                position.avg_price = price
        position.quantity = new_qty
        position.last_price = price
        position.updated_at = datetime.now(timezone.utc)
        self._snapshot.positions[symbol] = position
        self._recalculate_totals()
        return position

    def mark_price(self, symbol: str, price: Decimal) -> None:
        if price <= 0:
            raise ValueError("mark price must be positive")
        position = self._snapshot.positions.get(symbol.upper())
        if position is None:
            return
        position.last_price = price
        position.updated_at = datetime.now(timezone.utc)
        self._recalculate_totals()

    def _recalculate_totals(self) -> None:
        realized_dict: dict[str, Decimal] = {}
        mv_dict: dict[str, Decimal] = {}
        unrealized_dict: dict[str, Decimal] = {}
        realized_sum = Decimal("0")
        mv_sum = Decimal("0")
        unrealized_sum = Decimal("0")
        for position in self._snapshot.positions.values():
            c = position.currency
            realized_dict[c] = realized_dict.get(c, Decimal("0")) + position.realized_pnl
            mv_dict[c] = mv_dict.get(c, Decimal("0")) + position.market_value
            realized_sum += position.realized_pnl
            mv_sum += position.market_value
            if position.last_price is not None and position.quantity != 0:
                u = (position.last_price - position.avg_price) * Decimal(position.quantity)
                unrealized_dict[c] = unrealized_dict.get(c, Decimal("0")) + u
                unrealized_sum += u
        self._snapshot.realized_pnl = realized_sum
        self._snapshot.market_value = mv_sum
        self._snapshot.unrealized_pnl = unrealized_sum
        self._snapshot.realized_pnl_per_currency = realized_dict
        self._snapshot.market_value_per_currency = mv_dict
        self._snapshot.unrealized_pnl_per_currency = unrealized_dict
        self._snapshot.updated_at = datetime.now(timezone.utc)
```

기존 `test_portfolio_service.py`가 영향. §Phase 8에서 dict 시그니처로 갱신.

---

## §Phase 3 — PaperAccount

### §3.A 신설 — `app/portfolio/account.py`

```python
"""Paper account: multi-currency cash + portfolio aggregation."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal

from app.config import Settings
from app.domain.enums import Side
from app.domain.fills import Fill
from app.portfolio.service import PortfolioService


class PaperAccountError(Exception):
    """Paper-account business rule violation."""


@dataclass
class PaperAccount:
    cash: dict[str, Decimal]
    starting_cash: dict[str, Decimal]
    portfolio: PortfolioService = field(default_factory=PortfolioService)
    base_currency: str = "USD"

    @classmethod
    def from_settings(cls, settings: Settings, portfolio: PortfolioService | None = None) -> "PaperAccount":
        base = settings.paper_base_currency
        by_currency = dict(settings.paper_starting_cash_by_currency or {})
        if not by_currency:
            by_currency = {base: settings.paper_starting_cash}
        return cls(
            cash=dict(by_currency),
            starting_cash=dict(by_currency),
            portfolio=portfolio or PortfolioService(),
            base_currency=base,
        )

    def apply_fill(self, fill: Fill) -> None:
        if fill.currency not in self.cash:
            raise PaperAccountError(f"currency_not_funded:{fill.currency}")
        notional = Decimal(fill.quantity) * fill.price
        if fill.side is Side.BUY:
            cost = notional + fill.commission
            if self.cash[fill.currency] - cost < Decimal("0"):
                raise PaperAccountError("insufficient_cash")
            self.cash[fill.currency] -= cost
        else:
            self.cash[fill.currency] += notional - fill.commission
        self.portfolio.apply_fill(
            symbol=fill.symbol,
            side=fill.side,
            quantity=fill.quantity,
            price=fill.price,
            commission=fill.commission,
            currency=fill.currency,
        )

    def equity_per_currency(self) -> dict[str, Decimal]:
        snap = self.portfolio.get_snapshot()
        currencies = set(self.cash) | set(snap.market_value_per_currency)
        return {
            c: self.cash.get(c, Decimal("0")) + snap.market_value_per_currency.get(c, Decimal("0"))
            for c in currencies
        }

    def realized_pnl_per_currency(self) -> dict[str, Decimal]:
        return dict(self.portfolio.get_snapshot().realized_pnl_per_currency)

    def unrealized_pnl_per_currency(self) -> dict[str, Decimal]:
        return dict(self.portfolio.get_snapshot().unrealized_pnl_per_currency)

    def total_pnl_per_currency(self) -> dict[str, Decimal]:
        return self.portfolio.get_snapshot().total_pnl_per_currency()
```

**FX 변환 함수 추가 금지**. `equity_total_in_base_currency` 같은 메서드 만들지 말 것.

---

## §Phase 4 — PaperBroker fill 시뮬레이션

### §4.A 수정 — `app/broker/paper.py`

기존 클래스 보존, 확장.

```python
import math
import secrets
from datetime import datetime, timezone
from decimal import Decimal

from app.domain.enums import OrderType, Session, Side, TradingMode
from app.domain.fills import Fill
from app.domain.orders import BrokerOrder, OrderAck
from app.domain.quote import Quote


class PaperBroker:
    mode = TradingMode.PAPER

    def __init__(
        self,
        max_quote_age_seconds: int = 60,
        allowed_sessions: tuple[Session, ...] = (Session.REGULAR,),
        max_fill_ratio_of_volume: Decimal = Decimal("0.05"),
    ) -> None:
        self._open_orders: dict[str, BrokerOrder] = {}
        self._positions: dict[str, int] = {}
        self._triggered_stops: set[str] = set()
        self._remaining_qty: dict[str, int] = {}
        self._max_quote_age_seconds = max_quote_age_seconds
        self._allowed_sessions: set[Session] = set(allowed_sessions)
        self._max_fill_ratio = max_fill_ratio_of_volume

    def submit(self, order: BrokerOrder) -> OrderAck:
        if order.order_type not in (OrderType.LIMIT, OrderType.STOP_LIMIT, OrderType.MARKET):
            raise ValueError(f"unsupported order type: {order.order_type}")
        broker_order_id = secrets.token_hex(8)
        self._open_orders[broker_order_id] = order
        self._remaining_qty[broker_order_id] = order.quantity
        return OrderAck(
            oms_id=order.oms_id,
            broker_order_id=broker_order_id,
            status="accepted",
            mode=self.mode,
        )

    def cancel(self, broker_order_id: str) -> None:
        self._open_orders.pop(broker_order_id, None)
        self._remaining_qty.pop(broker_order_id, None)
        self._triggered_stops.discard(broker_order_id)

    def cancel_all(self, reason: str | None = None) -> int:
        count = len(self._open_orders)
        self._open_orders.clear()
        self._remaining_qty.clear()
        self._triggered_stops.clear()
        return count

    def open_orders(self) -> list[BrokerOrder]:
        return list(self._open_orders.values())

    def positions(self) -> dict[str, int]:
        return dict(self._positions)

    def tick(self, quote: Quote) -> list[Fill]:
        if quote.last <= 0 or quote.bid <= 0 or quote.ask <= 0:
            raise ValueError("invalid quote: non-positive price")
        # staleness
        if quote.is_stale(datetime.now(timezone.utc), self._max_quote_age_seconds):
            return []
        # session
        if quote.session is not None and quote.session not in self._allowed_sessions:
            return []
        if quote.volume <= 0:
            volume_cap = 0
        else:
            volume_cap = int((Decimal(quote.volume) * self._max_fill_ratio).to_integral_value(rounding="ROUND_FLOOR"))
        now = datetime.now(timezone.utc)
        fills: list[Fill] = []
        fully_filled: list[str] = []
        for broker_order_id, order in list(self._open_orders.items()):
            if order.symbol != quote.symbol:
                continue
            fill_price = self._eligible_fill_price(broker_order_id, order, quote)
            if fill_price is None:
                continue
            remaining = self._remaining_qty.get(broker_order_id, 0)
            if remaining <= 0:
                fully_filled.append(broker_order_id)
                continue
            fill_qty = min(remaining, volume_cap) if volume_cap > 0 else 0
            if fill_qty <= 0:
                continue
            fills.append(
                Fill(
                    symbol=order.symbol,
                    side=order.side,
                    quantity=fill_qty,
                    price=fill_price,
                    filled_at=now,
                    broker_order_id=broker_order_id,
                    oms_id=order.oms_id,
                    risk_token=order.risk_token,
                    currency=quote.currency,
                )
            )
            self._remaining_qty[broker_order_id] = remaining - fill_qty
            if self._remaining_qty[broker_order_id] <= 0:
                fully_filled.append(broker_order_id)
            signed = fill_qty if order.side is Side.BUY else -fill_qty
            self._positions[order.symbol] = self._positions.get(order.symbol, 0) + signed
        for broker_order_id in fully_filled:
            self._open_orders.pop(broker_order_id, None)
            self._remaining_qty.pop(broker_order_id, None)
            self._triggered_stops.discard(broker_order_id)
        return fills

    def _eligible_fill_price(self, broker_order_id: str, order: BrokerOrder, quote: Quote) -> Decimal | None:
        if order.order_type is OrderType.MARKET:
            return quote.ask if order.side is Side.BUY else quote.bid
        if order.order_type is OrderType.LIMIT:
            return order.limit_price if self._limit_fillable(order, quote) else None
        if order.order_type is OrderType.STOP_LIMIT:
            if broker_order_id not in self._triggered_stops:
                if not self._stop_triggered(order, quote):
                    return None
                self._triggered_stops.add(broker_order_id)
            return order.limit_price if self._limit_fillable(order, quote) else None
        return None

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

---

## §Phase 5 — RiskEngine MARKET 분기

### §5.A 수정 — `app/risk/engine.py`

```python
import secrets
from dataclasses import dataclass

from app.config import Settings
from app.domain.enums import OrderType, TradingMode
from app.domain.orders import OrderIntent


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reason: str
    risk_token: str | None = None


class RiskEngine:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def evaluate(self, intent: OrderIntent) -> RiskDecision:
        if self._settings.kill_switch_engaged:
            return RiskDecision(False, "kill_switch_engaged")
        if self._settings.trading_mode != TradingMode.PAPER:
            return RiskDecision(False, "paper_trading_required")
        if self._settings.live_trading_enabled:
            return RiskDecision(False, "live_trading_disabled")
        if intent.order_type is OrderType.MARKET:
            if not self._settings.allow_paper_market_orders:
                return RiskDecision(False, "paper_market_orders_disabled")
            if self._settings.trading_mode != TradingMode.PAPER:
                return RiskDecision(False, "market_only_in_paper")
            if self._settings.live_trading_enabled:
                return RiskDecision(False, "market_disabled_in_live")
        elif intent.order_type not in (OrderType.LIMIT, OrderType.STOP_LIMIT):
            return RiskDecision(False, "order_type_not_supported")
        if intent.quantity <= 0:
            return RiskDecision(False, "quantity_must_be_positive")
        if self._settings.symbol_allowlist and intent.symbol not in self._settings.symbol_allowlist:
            return RiskDecision(False, "symbol_not_allowed")
        if intent.quantity * intent.limit_price > self._settings.max_order_notional_usd:
            return RiskDecision(False, "max_order_notional_exceeded")
        return RiskDecision(True, "approved", secrets.token_hex(16))
```

기존 `ALLOW_MARKET_ORDERS=true` 거절은 `load_settings` 단계 그대로(`allow_market_orders=False` 강제). 새 `allow_paper_market_orders`는 별도 단순 bool, load_settings에서 그대로 통과.

---

## §Phase 6 — Journal + Engine

### §6.A 신설 — `app/runtime/paper_journal.py`

```python
"""Paper trading journal — order log + trade log (memory default, JSONL opt-in)."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from decimal import Decimal
from pathlib import Path

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
    currency: str = "USD"
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
    currency: str
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

### §6.B 신설 — `app/runtime/paper_engine.py`

```python
"""Paper trading engine: ties Strategy outputs to fills (multi-currency aware)."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
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
                        currency=intent.currency,
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
                    currency=intent.currency,
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
                        currency=fill.currency,
                        detail=str(exc),
                    )
                )
                continue
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
                    currency=fill.currency,
                    cash_after=self._account.cash.get(fill.currency, Decimal("0")),
                    realized_pnl_after=self._account.realized_pnl_per_currency().get(fill.currency, Decimal("0")),
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
                    order_type=OrderType.LIMIT,
                    limit_price=fill.price,
                    risk_token=fill.risk_token,
                    currency=fill.currency,
                    detail="fill",
                )
            )
            applied.append(fill)
        return applied
```

---

## §Phase 7 — Config + .env.example + README

### §7.A 수정 — `app/config.py`

`Settings`에 다음 필드 추가(기존 필드 뒤):

```python
allow_paper_market_orders: bool = False
paper_commission_per_share: Decimal = Decimal("0.005")
paper_commission_per_fill: Decimal = Decimal("0")
paper_log_dir: str | None = field(default=None, repr=False)
paper_max_quote_age_seconds: int = 60
paper_allowed_sessions: tuple[str, ...] = ("regular",)
paper_max_fill_ratio_of_volume: Decimal = Decimal("0.05")
paper_starting_cash_by_currency: dict[str, Decimal] | None = field(default=None, repr=False)
paper_base_currency: str = "USD"
```

`load_settings()`에 다음 추가:

```python
def _decimal_dict_env(name: str) -> dict[str, Decimal] | None:
    raw = _str_env(name)
    if raw is None:
        return None
    result: dict[str, Decimal] = {}
    for part in raw.split(","):
        if not part.strip():
            continue
        if "=" not in part:
            raise ValueError(f"invalid {name} entry: {part!r}")
        key, value = part.split("=", 1)
        result[key.strip().upper()] = Decimal(value.strip())
    return result or None


def _session_tuple_env(name: str, default: tuple[str, ...]) -> tuple[str, ...]:
    raw = _str_env(name)
    if raw is None:
        return default
    valid = {"pre_market", "regular", "after_hours", "closed"}
    out = []
    for part in raw.split(","):
        s = part.strip().lower()
        if not s:
            continue
        if s not in valid:
            raise ValueError(f"invalid {name} value: {s!r}")
        out.append(s)
    return tuple(out) or default
```

(위 두 헬퍼는 `_str_env` 정의 이후, `load_settings` 정의 이전에 추가. 둘 다 `_str_env`를 사용함.)

`load_settings()`의 `return Settings(...)` 호출에 다음 인자 추가:

```python
allow_paper_market_orders=_bool_env("ALLOW_PAPER_MARKET_ORDERS", False),
paper_commission_per_share=_decimal_env("PAPER_COMMISSION_PER_SHARE", Decimal("0.005")),
paper_commission_per_fill=_decimal_env("PAPER_COMMISSION_PER_FILL", Decimal("0")),
paper_log_dir=_str_env("PAPER_LOG_DIR"),
paper_max_quote_age_seconds=_int_env("PAPER_MAX_QUOTE_AGE_SECONDS", 60),
paper_allowed_sessions=_session_tuple_env("PAPER_ALLOWED_SESSIONS", ("regular",)),
paper_max_fill_ratio_of_volume=_decimal_env("PAPER_MAX_FILL_RATIO_OF_VOLUME", Decimal("0.05")),
paper_starting_cash_by_currency=_decimal_dict_env("PAPER_STARTING_CASH_BY_CURRENCY"),
paper_base_currency=_str_env("PAPER_BASE_CURRENCY") or "USD",
```

기존 라인 삭제 금지.

### §7.B 수정 — `.env.example`

파일 끝에 다음 블록 추가:

```
# --- Paper trading MVP (paper-001) ---
# ALLOW_PAPER_MARKET_ORDERS          optional, default false. enables MARKET in paper only
# PAPER_COMMISSION_PER_SHARE         optional, default 0.005 (USD/share equivalent in each currency)
# PAPER_COMMISSION_PER_FILL          optional, default 0 (flat per-fill add-on)
# PAPER_LOG_DIR                      optional. when set, writes orders.jsonl + trades.jsonl
# PAPER_MAX_QUOTE_AGE_SECONDS        optional, default 60. PaperBroker rejects fills on stale quotes
# PAPER_ALLOWED_SESSIONS             optional, default regular. comma list: pre_market,regular,after_hours,closed
# PAPER_MAX_FILL_RATIO_OF_VOLUME     optional, default 0.05. fraction of quote.volume that can fill per tick
# PAPER_STARTING_CASH_BY_CURRENCY    optional. format: USD=100000,KRW=130000000
# PAPER_BASE_CURRENCY                optional, default USD
```

### §7.C 수정 — `README.md`

파일 끝에 다음 단락 추가:

```markdown
## Paper trading MVP (paper-001)

내부 paper trading의 첫 동작 완결판입니다. 6개 기능 일괄 land:

- LIMIT / STOP_LIMIT / **MARKET** 시뮬레이션 (MARKET은 `ALLOW_PAPER_MARKET_ORDERS=true` 필요).
- **Partial fill**: `floor(quote.volume * PAPER_MAX_FILL_RATIO_OF_VOLUME)` 만큼 채결, 잔량은 다음 tick.
- **Quote staleness**: `PaperBroker`가 `PAPER_MAX_QUOTE_AGE_SECONDS`로 판단해 stale이면 fill 0건.
- **Session 검사**: `PAPER_ALLOWED_SESSIONS`로 허용 세션 외 quote는 fill 0건.
- **Multi-currency**: `PaperAccount.cash`가 통화별 dict. FX 변환은 본 MVP 미지원 — 통화별 분리 보고만.
- **Commission**: `PAPER_COMMISSION_PER_SHARE * quantity + PAPER_COMMISSION_PER_FILL` (per fill 적용).
- 모든 주문은 `Strategy → OMS → RiskEngine → PaperBroker` 통과. live 비활성, 실 broker 호출 0건.
```

---

## §Phase 8 — 테스트

### §8.A 신규 — `tests/test_fill_model.py`

happy path + 8개 invariant 거절 + frozen 검증 + `currency` 검증 (소문자/2자리 reject).

### §8.B 신규 — `tests/test_order_type_market.py`

- `OrderType.MARKET.value == "market"`.
- `OrderIntent(order_type=MARKET, limit_price=Decimal("0"))` → `ValueError`.
- `OrderIntent(order_type=MARKET, limit_price=Decimal("100"))` → OK.

### §8.C 신규 — `tests/test_risk_engine_market.py`

- `ALLOW_PAPER_MARKET_ORDERS=False` + MARKET intent → reject `"paper_market_orders_disabled"`.
- `ALLOW_PAPER_MARKET_ORDERS=True` + paper + intent → approve.
- 기존 LIMIT/STOP_LIMIT 케이스 회귀 0.

### §8.D 신규 — `tests/test_paper_account.py`

- `from_settings` 단일 통화 default.
- `from_settings` multi-currency: `paper_starting_cash_by_currency={"USD": 1000, "KRW": 2_000_000}`.
- BUY USD fill 후 USD cash 차감, KRW 변경 없음.
- 미funded 통화로 fill → `PaperAccountError("currency_not_funded:XXX")`.
- USD insufficient → reject + 잔액 미변경.
- `equity_per_currency` / `realized_pnl_per_currency` / `unrealized_pnl_per_currency`.
- FX 변환 메서드 부재 검증 (hasattr → False).

### §8.E 신규 — `tests/test_paper_broker_fill.py`

- LIMIT BUY/SELL fill at limit_price.
- LIMIT 미매치 시 open 유지 + remaining 변화 0.
- STOP_LIMIT BUY 트리거 + LIMIT 조건 충족 → fill, 후속 tick에서 remaining 처리.
- MARKET BUY → fill at quote.ask. MARKET SELL → fill at quote.bid.
- `cancel_all`로 일괄 취소 + count 반환.
- 잘못된 quote (price ≤ 0) → `ValueError`.

### §8.F 신규 — `tests/test_paper_broker_staleness.py`

기존 `Quote.is_stale`는 `age > max_age_seconds`(strict greater) → 정확히 60초 전은 stale 아님.

- `max_quote_age_seconds=60`, quote 61초 전 → `tick` 빈 list.
- quote 59초 전 → 정상 fill 흐름.
- `quote.timestamp`가 미래(now보다 늦음) → `is_stale` 의도(`age < 0` 분기)대로 빈 list.

### §8.G 신규 — `tests/test_paper_broker_session.py`

- `quote.session=None` → 허용.
- `quote.session=REGULAR` → 허용 (기본).
- `quote.session=PRE_MARKET` → 거절 (기본).
- broker init에 `allowed_sessions=(Session.REGULAR, Session.PRE_MARKET)` 설정 후 PRE_MARKET 허용.

### §8.H 신규 — `tests/test_paper_broker_partial.py`

- `quote.volume=100`, `max_fill_ratio=0.05` → 한 tick에 최대 5주.
- 주문 20주 + 위 quote 한 번 → 5주 fill, remaining 15.
- 같은 quote 한 번 더 → 5주 fill, remaining 10.
- 4번 더 호출 → 결국 0 remaining, _open_orders에서 제거.
- `quote.volume=0` → fill 0건.
- `quote.volume*ratio<1` (예: volume=10, ratio=0.05 → cap=0) → fill 0건.

### §8.I 신규 — `tests/test_paper_journal.py`

- 메모리 only: record_order/trade 후 list 반영.
- `log_dir` 설정: orders.jsonl + trades.jsonl 생성, append-only (2 호출 → 2 line).
- TradeLogEntry.currency 직렬화 보존.
- `log_dir` 디렉터리 미존재 시 자동 생성.

### §8.J 신규 — `tests/test_portfolio_multi_currency.py`

- USD position + KRW position 동시.
- `snapshot.realized_pnl_per_currency == {"USD": ..., "KRW": ...}`.
- `snapshot.market_value_per_currency == {"USD": ..., "KRW": ...}`.
- `snapshot.unrealized_pnl_per_currency` 동일.
- 단일 `snapshot.realized_pnl`은 모든 통화 합산 Decimal (현재 USD+KRW 두 통화면 의미적으로 부정확하나 backward compat 목적; 단일 통화 케이스 정확).
- `total_pnl_per_currency()` = sum dict.

### §8.K 신규 — `tests/test_portfolio_unrealized_pnl.py`

- 롱 + last_price > avg → `snapshot.unrealized_pnl_per_currency["USD"] > 0`, `snapshot.unrealized_pnl > 0`.
- 숏 + last_price < avg → `snapshot.unrealized_pnl_per_currency["USD"] > 0`.
- last_price 부재 → key 부재 + 단일 `snapshot.unrealized_pnl == 0`.
- 기존 `tests/test_portfolio_service.py`의 `snapshot.realized_pnl == Decimal("39")` 류 단정은 **변경 없이 PASS** 유지(단일 통화 USD 합산이라 backward compat).

### §8.L 신규 — `tests/test_commission.py`

- per_share=0.01, fill 10주 → commission `Decimal("0.10")`.
- per_share=0.005, per_fill=1, fill 10주 → `Decimal("1.05")`.
- multi-currency: 동일 per_share/per_fill 적용 (FX 없음).

### §8.M 신규 — `tests/test_paper_engine.py`

- `submit_intents` 정상 → ack 반환 + journal "submitted".
- `submit_intents` RiskEngine reject (예: kill switch) → ack 없음 + journal "rejected".
- `on_quote` 후 fill 있음 → account 갱신 + journal "filled" + "trade".
- BUY cash 부족 → journal "rejected" + account 미변경.
- partial fill 시 fill당 1 trade entry.

### §8.N 신규 — `tests/test_paper_end_to_end.py` (통합)

```python
def test_full_cycle_usd_limit_with_partial_fills(settings):
    # 1. Settings: paper_starting_cash=10000, paper_max_fill_ratio_of_volume=0.5
    # 2. broker + risk + oms + account + journal + engine 와이어
    # 3. BUY 10 @ $100 LIMIT, SELL 10 @ $110 LIMIT
    # 4. engine.submit_intents([buy, sell]) → 2 ack
    # 5. engine.on_quote(Q("AAPL", last=99, bid=98.5, ask=99.5, volume=10, ts=now, currency="USD"))
    #     → BUY fills 5 (volume*0.5)
    # 6. engine.on_quote(same) → BUY fills nothing more (volume still 10 — same tick context)?
    #    실제로는 같은 호출 → 다시 5주 fill가능. 테스트로 검증.
    # 7. account.cash["USD"] = 10000 - 10*100 - commission
    # 8. SELL 처리 후 cash 회복 + realized_pnl["USD"] == 100 - 2*commission
    # 9. positions["AAPL"] = 0


def test_full_cycle_multi_currency_krw(settings):
    # paper_starting_cash_by_currency={"USD": 10000, "KRW": 2_000_000}
    # KRW symbol 005930 BUY/SELL cycle. currency 정합성 검증.


def test_market_order_with_allow_flag(settings):
    # allow_paper_market_orders=True
    # MARKET BUY → quote.ask로 fill, slippage 0
    # MARKET SELL → quote.bid로 fill
```

### §8.O 기존 테스트 갱신

- `tests/test_paper_broker.py` — 기존 라인 보존 + 새 fixture에 `PaperBroker(max_quote_age_seconds=..., allowed_sessions=..., max_fill_ratio_of_volume=...)` 인자 명시.
- `tests/test_portfolio_service.py` — **기존 단정 그대로** 유지(`snapshot.realized_pnl == Decimal("39")` 등). 단일 통화 USD 케이스이고 단일 Decimal 필드는 backward compat로 보존됨. 신규 케이스 1–2개만 추가(`snapshot.realized_pnl_per_currency["USD"] == Decimal("39")`).
- `app/api/routes.py`는 **변경 안 함** — `snapshot.market_value`/`realized_pnl`이 여전히 Decimal 그대로.

---

## §I. 적용 절차

1. Phase 1~7 파일 적용.
2. Phase 8 신규 테스트 14개 작성 + 기존 테스트 dict 시그니처로 보정.
3. 안전 grep:

   ```bash
   cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
   git diff -- app/ tests/ | grep -E "FX|exchange_rate|to_base_currency|equity_total_in_base" || echo "fx-grep: clean"
   git diff -- app/ tests/ | grep -E "import requests|import httpx|import aiohttp|import urllib3" || echo "http-lib-grep: clean"
   git diff -- app/ tests/ .env.example README.md | grep -E "PSNFD|PKID|AKIA|sk-|ghp_|Bearer eyJ|appkey=|appsecret=|\b\d{10,}\b" || echo "secret-grep: clean"
   git diff --stat -- app/api/ app/static/ app/main.py | grep -v '^$' && echo "GUI changed — BLOCK" || echo "gui-grep: clean"
   git diff --stat -- app/runtime/dry_run.py app/runtime/dry_run_report.py app/runtime/paper_runner.py | grep -v '^$' && echo "dry_run changed — BLOCK" || echo "dry-run-grep: clean"
   git diff --stat -- app/broker/kis.py app/broker/kis_http.py app/broker/kis_token_cache.py app/broker/kis_quote_mapper.py app/broker/alpaca_paper.py | grep -v '^$' && echo "kis/alpaca changed — BLOCK" || echo "kis-grep: clean"
   ```

   모든 grep 라벨 `clean`이어야 함.

4. 테스트:

   ```bash
   .venv/bin/python -m compileall app tests
   .venv/bin/python -m pytest -p no:cacheprovider
   ```

   - 기존 242 + 신규 60+ 모두 PASS.

5. `docs/ai/jobs/paper-001/patch.md` 작성. 다음 9개 섹션:
   - Implementation Summary
   - Phase별 적용 요약 (Phase 1~8)
   - 변경 파일 목록 (plan §3과 일치)
   - 신규 도메인/클래스/메서드 (`OrderType.MARKET`, `Fill`, `PaperAccount`, `PaperJournal`, `PaperEngine`, `PaperBroker.tick`, multi-currency snapshot)
   - 안전 grep 결과 (6개 라벨 × `clean`)
   - 테스트 결과 (전체 PASS 수치)
   - `compileall` 결과
   - 정책/안전 invariant 확인 (MARKET 3중 가드, FX 0건, GUI 미접촉, dry-run 미접촉, kis* 미접촉)
   - commit/push/merge 미실행 확인
6. `git commit` / `push` / `merge` / 배포 **미실행**.

---

## §J. Codex가 절대 하지 말아야 할 것 (반복)

- FX 변환 함수 / 환율 상수 / `equity_total_in_base_currency` / `to_base_currency` 도입.
- `ALLOW_MARKET_ORDERS=true` 허용 (별 flag — `ALLOW_PAPER_MARKET_ORDERS`만 추가).
- `live_trading_enabled=True` 활성 경로.
- 외부 HTTP lib 도입.
- KIS / Alpaca broker 본문 변경.
- `dry_run.py` / `dry_run_report.py` / `paper_runner.py` 본문 변경.
- `app/api/` / `app/static/` / `app/main.py` 변경.
- `app/strategy/*` 변경.
- `app/oms/manager.py` 본문 변경 (RiskEngine 분기만 §Phase 5에서 수정).
- `.env` 읽기/수정.
- 사용자 app key/secret/계좌번호/token 어디든 기록.
- 실제 broker 호스트로 네트워크 호출하는 테스트.
- 자동 git commit/push/merge/deploy.
- 본 codex-task에 없는 추가 endpoint/feature 도입.

---

## §K. 완료 조건

- Phase 1~8 적용 완료.
- 안전 grep 모든 라벨 `clean`.
- 전체 pytest PASS (242 기존 + 60+ 신규), `compileall` 무오류.
- `patch.md`에 §I.5의 9개 섹션 기록.
- 사람이 직접 staging/commit하도록 변경만 남기고 종료.
