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
        if intent.order_type == OrderType.MARKET:
            if not self._settings.allow_paper_market_orders:
                return RiskDecision(False, "paper_market_orders_disabled")
            if self._settings.trading_mode != TradingMode.PAPER:
                return RiskDecision(False, "paper_trading_required")
            if self._settings.live_trading_enabled:
                return RiskDecision(False, "live_trading_disabled")
        elif intent.order_type not in (OrderType.LIMIT, OrderType.STOP_LIMIT):
            return RiskDecision(False, "unsupported_order_type")
        if intent.quantity <= 0:
            return RiskDecision(False, "quantity_must_be_positive")
        if self._settings.symbol_allowlist and intent.symbol not in self._settings.symbol_allowlist:
            return RiskDecision(False, "symbol_not_allowed")
        if intent.quantity * intent.limit_price > self._settings.max_order_notional_usd:
            return RiskDecision(False, "max_order_notional_exceeded")
        return RiskDecision(True, "approved", secrets.token_hex(16))
