import secrets
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR

from app.domain.enums import OrderType, Session, Side, TradingMode
from app.domain.fills import Fill
from app.domain.orders import BrokerOrder, OrderAck
from app.domain.quote import Quote


class PaperBroker:
    mode = TradingMode.PAPER

    def __init__(
        self,
        *,
        max_quote_age_seconds: int = 60,
        allowed_sessions: set[Session] | None = None,
        max_fill_ratio_of_volume: Decimal = Decimal("0.05"),
        commission_per_share: Decimal = Decimal("0"),
        commission_per_fill: Decimal = Decimal("0"),
        slippage_bps: Decimal = Decimal("0"),
        market_impact_bps_per_pct_volume: Decimal = Decimal("0"),
        max_spread_pct_for_fill: Decimal = Decimal("0"),
    ) -> None:
        self._open_orders: dict[str, BrokerOrder] = {}
        self._positions: dict[str, int] = {}
        self._max_quote_age_seconds = max_quote_age_seconds
        self._allowed_sessions = allowed_sessions or {Session.REGULAR}
        self._max_fill_ratio_of_volume = max_fill_ratio_of_volume
        self._commission_per_share = commission_per_share
        self._commission_per_fill = commission_per_fill
        self._slippage_bps = Decimal(slippage_bps)
        self._market_impact_bps_per_pct_volume = Decimal(market_impact_bps_per_pct_volume)
        self._max_spread_pct_for_fill = Decimal(max_spread_pct_for_fill)

    def submit(self, order: BrokerOrder) -> OrderAck:
        if order.order_type not in (OrderType.LIMIT, OrderType.STOP_LIMIT, OrderType.MARKET):
            raise ValueError("unsupported order type")
        broker_order_id = secrets.token_hex(8)
        self._open_orders[broker_order_id] = order
        return OrderAck(
            oms_id=order.oms_id,
            broker_order_id=broker_order_id,
            status="accepted",
            mode=self.mode,
        )

    def cancel(self, broker_order_id: str) -> None:
        self._open_orders.pop(broker_order_id, None)

    def cancel_all(self) -> int:
        count = len(self._open_orders)
        self._open_orders.clear()
        return count

    def open_orders(self) -> list[BrokerOrder]:
        return list(self._open_orders.values())

    def positions(self) -> dict[str, int]:
        return dict(self._positions)

    def tick(self, quote: Quote, now: datetime | None = None) -> list[Fill]:
        now = now or datetime.now(timezone.utc)
        if quote.is_stale(now, self._max_quote_age_seconds):
            return []
        if quote.session is not None and quote.session not in self._allowed_sessions:
            return []
        if self._spread_blocks_fill(quote):
            return []

        max_fill_qty = int(
            (Decimal(quote.volume) * self._max_fill_ratio_of_volume).to_integral_value(
                rounding=ROUND_FLOOR
            )
        )
        if max_fill_qty <= 0:
            return []

        fills: list[Fill] = []
        remaining_volume = max_fill_qty
        for broker_order_id, order in list(self._open_orders.items()):
            if order.symbol != quote.symbol or remaining_volume <= 0:
                continue
            base_price = self._execution_price(order, quote)
            if base_price is None:
                continue

            fill_qty = min(order.quantity, remaining_volume)
            fill_price = self._apply_slippage_and_impact(
                base_price=base_price,
                side=order.side,
                fill_qty=fill_qty,
                quote_volume=quote.volume,
            )
            commission = (
                self._commission_per_share * Decimal(fill_qty) + self._commission_per_fill
            )
            fill = Fill(
                broker_order_id=broker_order_id,
                oms_id=order.oms_id,
                symbol=order.symbol,
                side=order.side,
                quantity=fill_qty,
                price=fill_price,
                currency=quote.currency or order.currency,
                commission=commission,
                liquidity="simulated",
                filled_at=now,
            )
            fills.append(fill)
            self._positions[order.symbol] = self._positions.get(order.symbol, 0) + (
                fill_qty if order.side == Side.BUY else -fill_qty
            )
            remaining_volume -= fill_qty

            if fill_qty == order.quantity:
                del self._open_orders[broker_order_id]
            else:
                self._open_orders[broker_order_id] = BrokerOrder(
                    symbol=order.symbol,
                    side=order.side,
                    quantity=order.quantity - fill_qty,
                    order_type=order.order_type,
                    limit_price=order.limit_price,
                    risk_token=order.risk_token,
                    created_at=order.created_at,
                    oms_id=order.oms_id,
                    submitted_at=order.submitted_at,
                    stop_price=order.stop_price,
                    currency=order.currency,
                    client_tag=order.client_tag,
                    quote_timestamp=order.quote_timestamp,
                )

        return fills

    def _execution_price(self, order: BrokerOrder, quote: Quote) -> Decimal | None:
        if order.order_type == OrderType.MARKET:
            return quote.ask if order.side == Side.BUY else quote.bid

        if order.order_type == OrderType.LIMIT:
            if order.side == Side.BUY and quote.ask <= order.limit_price:
                return quote.ask
            if order.side == Side.SELL and quote.bid >= order.limit_price:
                return quote.bid
            return None

        if order.order_type == OrderType.STOP_LIMIT:
            if order.stop_price is None:
                return None
            if order.side == Side.BUY:
                if quote.last < order.stop_price or quote.ask > order.limit_price:
                    return None
                return quote.ask
            if quote.last > order.stop_price or quote.bid < order.limit_price:
                return None
            return quote.bid

        return None

    def _spread_blocks_fill(self, quote: Quote) -> bool:
        """Refuse to fill when spread exceeds the configured threshold.

        Disabled when max_spread_pct_for_fill == 0 (default; backward compatible).
        """
        if self._max_spread_pct_for_fill <= 0:
            return False
        if quote.last <= 0:
            return False
        spread_pct = (quote.ask - quote.bid) / quote.last
        return spread_pct > self._max_spread_pct_for_fill

    def _apply_slippage_and_impact(
        self,
        *,
        base_price: Decimal,
        side: Side,
        fill_qty: int,
        quote_volume: int,
    ) -> Decimal:
        """Apply slippage (basis points) + market impact scaled by fill_qty / quote_volume.

        BUY → price moves up (more expensive); SELL → price moves down (worse).
        Returns base_price unchanged when both slippage settings are 0.
        """
        bps = self._slippage_bps
        if self._market_impact_bps_per_pct_volume > 0 and quote_volume > 0:
            pct_volume_consumed = (Decimal(fill_qty) / Decimal(quote_volume)) * Decimal(100)
            bps = bps + self._market_impact_bps_per_pct_volume * pct_volume_consumed
        if bps == 0:
            return base_price
        factor = Decimal(1) + (bps / Decimal(10000))
        if side == Side.BUY:
            return base_price * factor
        return base_price * (Decimal(2) - factor)
