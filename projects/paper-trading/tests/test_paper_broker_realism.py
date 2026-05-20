"""paper-002 — PaperBroker fill realism (slippage, market impact, multi-tick partial fills, spread guard)."""

from datetime import datetime, timezone
from decimal import Decimal

from app.broker.paper import PaperBroker
from app.domain.enums import OrderType, Session, Side
from app.domain.orders import BrokerOrder
from app.domain.quote import Quote


def _order(quantity: int = 10, side: Side = Side.BUY, **overrides) -> BrokerOrder:
    now = datetime.now(timezone.utc)
    data = {
        "symbol": "AAPL",
        "side": side,
        "quantity": quantity,
        "order_type": OrderType.LIMIT,
        "limit_price": Decimal("100"),
        "risk_token": "rt",
        "created_at": now,
        "oms_id": "oms-1",
        "submitted_at": now,
    }
    data.update(overrides)
    return BrokerOrder(**data)


def _quote(*, last: Decimal = Decimal("100"), bid: Decimal | None = None, ask: Decimal | None = None, volume: int = 1_000_000) -> Quote:
    return Quote(
        symbol="AAPL",
        last=last,
        bid=bid if bid is not None else last,
        ask=ask if ask is not None else last,
        volume=volume,
        timestamp=datetime.now(timezone.utc),
        source="test",
        session=Session.REGULAR,
        currency="USD",
    )


# ── Backward compatibility (default settings = 0 slippage, no spread cap) ────


def test_default_settings_preserve_existing_fill_behavior():
    """With default 0 slippage / 0 impact / 0 spread cap, fill price equals base execution price."""
    broker = PaperBroker(max_fill_ratio_of_volume=Decimal("1"))
    broker.submit(_order(quantity=5, side=Side.BUY))
    fills = broker.tick(_quote(last=Decimal("100"), bid=Decimal("99"), ask=Decimal("100"), volume=1000))
    assert len(fills) == 1
    # BUY LIMIT fills at quote.ask = 100; no slippage applied
    assert fills[0].price == Decimal("100")
    assert fills[0].quantity == 5


# ── Slippage (basis points) ──────────────────────────────────────────────────


def test_slippage_moves_buy_price_up():
    broker = PaperBroker(
        max_fill_ratio_of_volume=Decimal("1"),
        slippage_bps=Decimal("10"),  # 10 bps = 0.1%
    )
    broker.submit(_order(quantity=5, side=Side.BUY))
    fills = broker.tick(_quote(last=Decimal("100"), bid=Decimal("99"), ask=Decimal("100"), volume=1000))
    # 100 * (1 + 10/10000) = 100.10
    assert fills[0].price == Decimal("100.10")


def test_slippage_moves_sell_price_down():
    broker = PaperBroker(
        max_fill_ratio_of_volume=Decimal("1"),
        slippage_bps=Decimal("10"),
    )
    broker.submit(_order(quantity=5, side=Side.SELL, limit_price=Decimal("99")))
    fills = broker.tick(_quote(last=Decimal("100"), bid=Decimal("100"), ask=Decimal("101"), volume=1000))
    # SELL fills at bid=100; slippage moves it down: 100 * (1 - 10/10000) = 99.90
    assert fills[0].price == Decimal("99.90")


# ── Market impact (scales with fill_qty / quote.volume) ──────────────────────


def test_market_impact_increases_slippage_with_size():
    broker = PaperBroker(
        max_fill_ratio_of_volume=Decimal("1"),
        market_impact_bps_per_pct_volume=Decimal("100"),  # 100 bps per 1% of volume consumed
    )
    # Order of 100 vs volume 1000 = 10% consumed → 1000 bps = 10% impact
    broker.submit(_order(quantity=100, side=Side.BUY))
    fills = broker.tick(_quote(last=Decimal("100"), bid=Decimal("99"), ask=Decimal("100"), volume=1000))
    # 100 * (1 + 1000/10000) = 110
    assert fills[0].price == Decimal("110")


def test_market_impact_proportional_to_size():
    broker = PaperBroker(
        max_fill_ratio_of_volume=Decimal("1"),
        market_impact_bps_per_pct_volume=Decimal("100"),
    )
    # Smaller order (1% of volume) → less impact
    broker.submit(_order(quantity=10, side=Side.BUY))
    fills = broker.tick(_quote(last=Decimal("100"), bid=Decimal("99"), ask=Decimal("100"), volume=1000))
    # 100 * (1 + 100/10000) = 101
    assert fills[0].price == Decimal("101")


def test_slippage_and_market_impact_compose():
    broker = PaperBroker(
        max_fill_ratio_of_volume=Decimal("1"),
        slippage_bps=Decimal("5"),
        market_impact_bps_per_pct_volume=Decimal("10"),
    )
    # 10/1000 = 1% volume → impact 10 bps; total = 5 + 10 = 15 bps
    broker.submit(_order(quantity=10, side=Side.BUY))
    fills = broker.tick(_quote(last=Decimal("100"), bid=Decimal("99"), ask=Decimal("100"), volume=1000))
    # 100 * (1 + 15/10000) = 100.15
    assert fills[0].price == Decimal("100.15")


# ── Spread guard ──────────────────────────────────────────────────────────────


def test_spread_guard_blocks_fill_when_spread_exceeds_threshold():
    broker = PaperBroker(
        max_fill_ratio_of_volume=Decimal("1"),
        max_spread_pct_for_fill=Decimal("0.01"),  # 1% max spread
    )
    broker.submit(_order(quantity=5, side=Side.BUY))
    # spread = (105 - 99) / 100 = 6% > 1% → block
    fills = broker.tick(_quote(last=Decimal("100"), bid=Decimal("99"), ask=Decimal("105"), volume=1000))
    assert fills == []


def test_spread_guard_allows_fill_when_spread_within_threshold():
    broker = PaperBroker(
        max_fill_ratio_of_volume=Decimal("1"),
        max_spread_pct_for_fill=Decimal("0.10"),
    )
    broker.submit(_order(quantity=5, side=Side.BUY))
    # spread = (100 - 99.50) / 100 = 0.5% < 10% → allow
    fills = broker.tick(_quote(last=Decimal("100"), bid=Decimal("99.50"), ask=Decimal("100"), volume=1000))
    assert len(fills) == 1


def test_spread_guard_disabled_by_default():
    """max_spread_pct_for_fill=0 (default) disables guard regardless of spread."""
    broker = PaperBroker(max_fill_ratio_of_volume=Decimal("1"))
    broker.submit(_order(quantity=5, side=Side.BUY))
    # wide spread but no guard
    fills = broker.tick(_quote(last=Decimal("100"), bid=Decimal("90"), ask=Decimal("100"), volume=1000))
    assert len(fills) == 1


# ── Multi-tick partial fill sequences ────────────────────────────────────────


def test_multi_tick_partial_fill_accumulates():
    """A single order spans multiple ticks until fully filled."""
    broker = PaperBroker(max_fill_ratio_of_volume=Decimal("0.05"))  # 5% of volume per tick
    broker.submit(_order(quantity=100, side=Side.BUY))

    # Tick 1: volume=400 → max_fill_qty = 20 → partial fill 20, remaining 80
    fills_1 = broker.tick(_quote(last=Decimal("100"), bid=Decimal("99"), ask=Decimal("100"), volume=400))
    assert len(fills_1) == 1
    assert fills_1[0].quantity == 20
    assert len(broker.open_orders()) == 1
    assert broker.open_orders()[0].quantity == 80

    # Tick 2: volume=1600 → max_fill_qty = 80 → fills remaining 80, order closed
    fills_2 = broker.tick(_quote(last=Decimal("100"), bid=Decimal("99"), ask=Decimal("100"), volume=1600))
    assert len(fills_2) == 1
    assert fills_2[0].quantity == 80
    assert broker.open_orders() == []


def test_multi_tick_partial_fill_preserves_oms_id():
    """All partial fills of a single order carry the same oms_id."""
    broker = PaperBroker(max_fill_ratio_of_volume=Decimal("0.05"))
    broker.submit(_order(quantity=100, oms_id="oms-multi-tick", side=Side.BUY))
    fills_1 = broker.tick(_quote(volume=400))
    fills_2 = broker.tick(_quote(volume=1600))
    assert fills_1[0].oms_id == "oms-multi-tick"
    assert fills_2[0].oms_id == "oms-multi-tick"


def test_multi_tick_partial_fill_with_slippage_each_tick():
    """Slippage applies to each tick's fill independently."""
    broker = PaperBroker(
        max_fill_ratio_of_volume=Decimal("0.05"),
        slippage_bps=Decimal("10"),
    )
    broker.submit(_order(quantity=100, side=Side.BUY))
    fills_1 = broker.tick(_quote(last=Decimal("100"), bid=Decimal("99"), ask=Decimal("100"), volume=400))
    fills_2 = broker.tick(_quote(last=Decimal("100"), bid=Decimal("99"), ask=Decimal("100"), volume=1600))
    # Both ticks apply 10 bps slippage to BUY → price = 100.10 each
    assert fills_1[0].price == Decimal("100.10")
    assert fills_2[0].price == Decimal("100.10")


# ── Currency separation preserved (no FX) ────────────────────────────────────


def test_fill_currency_comes_from_quote_no_fx_conversion():
    broker = PaperBroker(max_fill_ratio_of_volume=Decimal("1"))
    broker.submit(_order(quantity=5, side=Side.BUY, currency="HKD"))
    hkd_quote = Quote(
        symbol="AAPL",
        last=Decimal("100"),
        bid=Decimal("99"),
        ask=Decimal("100"),
        volume=1000,
        timestamp=datetime.now(timezone.utc),
        source="test",
        session=Session.REGULAR,
        currency="HKD",
    )
    fills = broker.tick(hkd_quote)
    assert fills[0].currency == "HKD"
    # Fill price is in HKD; no FX conversion to USD
    assert fills[0].price == Decimal("100")
