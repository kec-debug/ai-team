"""strategy-002 — Opening Range Breakout (regular-session breakout above opening-range high).

Non-executable: emits OrderIntent only. Risk / OMS / broker boundaries unchanged.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN

from app.config import Settings
from app.domain.enums import OrderType, Session, Side, TradingMode
from app.domain.market import StrategyInput
from app.domain.orders import OrderIntent
from app.strategy.base import Strategy, StrategyResult


class OpeningRangeBreakoutStrategy(Strategy):
    name = "opening_range_breakout"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def evaluate(self, snapshot: StrategyInput) -> StrategyResult:
        blockers: list[str] = []
        reasons: list[str] = []

        if self._settings.trading_mode != TradingMode.PAPER or self._settings.live_trading_enabled:
            blockers.append("live_trading_disabled")
        if snapshot.market.upper() != "US":
            blockers.append("market_not_supported")
        if snapshot.session != Session.REGULAR:
            blockers.append("not_regular_session")

        if snapshot.opening_range_high is None:
            blockers.append("no_opening_range_data")
        else:
            breakout_floor = snapshot.opening_range_high * (
                Decimal("1") - self._settings.premarket_breakout_tolerance_pct
            )
            if snapshot.current_price < breakout_floor:
                blockers.append("not_above_opening_range_high")
            else:
                reasons.append("above_opening_range_high")

        if snapshot.relative_volume is not None:
            if snapshot.relative_volume < self._settings.premarket_min_relative_volume:
                blockers.append("relative_volume_below_threshold")
            else:
                reasons.append("relative_volume_above_threshold")
        else:
            blockers.append("relative_volume_missing")

        if snapshot.vwap is not None:
            if snapshot.current_price < snapshot.vwap:
                blockers.append("price_below_vwap")
            else:
                reasons.append("price_above_vwap")

        spread_pct = (snapshot.ask - snapshot.bid) / snapshot.current_price
        if spread_pct < 0:
            blockers.append("invalid_spread")
        elif spread_pct > self._settings.premarket_max_spread_pct:
            blockers.append("spread_above_threshold")
        else:
            reasons.append("spread_within_threshold")

        now = datetime.now(timezone.utc)
        quote_age = (now - snapshot.timestamp).total_seconds()
        if quote_age > self._settings.premarket_max_quote_age_seconds:
            blockers.append("stale_quote")
        else:
            reasons.append("quote_fresh")

        if blockers:
            return StrategyResult(
                symbol=snapshot.symbol,
                passed=False,
                score=0.0,
                reasons=reasons,
                blockers=blockers,
            )

        limit_price = snapshot.ask.quantize(Decimal("0.01"))
        quantity = max(
            1,
            int(
                (self._settings.max_order_notional_usd / limit_price).to_integral_value(
                    rounding=ROUND_DOWN
                )
            ),
        )
        intent = OrderIntent(
            symbol=snapshot.symbol,
            side=Side.BUY,
            quantity=quantity,
            order_type=OrderType.LIMIT,
            limit_price=limit_price,
            client_tag=self.name,
            quote_timestamp=snapshot.timestamp,
        )
        # score: how far above opening-range high the price has broken out (capped at 1.0).
        assert snapshot.opening_range_high is not None
        breakout_pct = (snapshot.current_price - snapshot.opening_range_high) / snapshot.opening_range_high
        score = float(min(Decimal("1"), max(Decimal("0"), breakout_pct * Decimal("10"))))
        return StrategyResult(
            symbol=snapshot.symbol,
            passed=True,
            score=score,
            reasons=reasons,
            blockers=[],
            suggested_limit_price=limit_price,
            non_executable_order_intent=intent,
        )
