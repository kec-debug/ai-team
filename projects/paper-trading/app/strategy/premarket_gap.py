from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN

from app.config import Settings
from app.domain.enums import OrderType, Session, Side, TradingMode
from app.domain.market import StrategyInput
from app.domain.orders import OrderIntent
from app.strategy.base import Strategy, StrategyResult


class PremarketGapVolumeBreakoutStrategy(Strategy):
    name = "premarket_gap_volume_breakout"

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def evaluate(self, snapshot: StrategyInput) -> StrategyResult:
        blockers: list[str] = []
        reasons: list[str] = []

        if self._settings.trading_mode != TradingMode.PAPER or self._settings.live_trading_enabled:
            blockers.append("live_trading_disabled")
        if snapshot.market.upper() != "US":
            blockers.append("market_not_supported")
        if snapshot.session != Session.PRE_MARKET:
            blockers.append("not_premarket_session")

        gap_pct = (snapshot.current_price - snapshot.previous_close) / snapshot.previous_close
        if gap_pct < self._settings.premarket_gap_min_pct:
            blockers.append("gap_below_threshold")
        else:
            reasons.append("gap_above_threshold")

        if snapshot.premarket_volume < self._settings.premarket_min_volume:
            blockers.append("volume_below_threshold")
        else:
            reasons.append("volume_above_threshold")

        if snapshot.relative_volume is not None:
            if snapshot.relative_volume < self._settings.premarket_min_relative_volume:
                blockers.append("relative_volume_below_threshold")
            else:
                reasons.append("relative_volume_above_threshold")

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

        breakout_floor = snapshot.premarket_high * (Decimal("1") - self._settings.premarket_breakout_tolerance_pct)
        if snapshot.current_price < breakout_floor:
            blockers.append("not_near_premarket_high")
        else:
            reasons.append("near_premarket_high")

        if blockers:
            return StrategyResult(
                symbol=snapshot.symbol,
                passed=False,
                score=0.0,
                reasons=reasons,
                blockers=blockers,
            )

        limit_price = snapshot.ask.quantize(Decimal("0.01"))
        quantity = max(1, int((self._settings.max_order_notional_usd / limit_price).to_integral_value(rounding=ROUND_DOWN)))
        intent = OrderIntent(
            symbol=snapshot.symbol,
            side=Side.BUY,
            quantity=quantity,
            order_type=OrderType.LIMIT,
            limit_price=limit_price,
            client_tag=self.name,
            quote_timestamp=snapshot.timestamp,
        )
        return StrategyResult(
            symbol=snapshot.symbol,
            passed=True,
            score=float(min(Decimal("1"), gap_pct / self._settings.premarket_gap_min_pct)),
            reasons=reasons,
            blockers=[],
            suggested_limit_price=limit_price,
            non_executable_order_intent=intent,
        )
