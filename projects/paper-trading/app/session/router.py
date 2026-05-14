from dataclasses import dataclass
from datetime import datetime, time, timezone
from fnmatch import fnmatch
from zoneinfo import ZoneInfo

from app.domain.enums import Session


US_EASTERN = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class SessionPolicy:
    session: Session
    orders_allowed: bool
    allowed_strategies: tuple[str, ...] = ()
    symbol_filters: tuple[str, ...] = ("*",)
    max_spread_pct: float | None = None

    def symbol_allowed(self, symbol: str) -> bool:
        return any(fnmatch(symbol.upper(), pattern.upper()) for pattern in self.symbol_filters)

    def strategy_allowed(self, strategy_name: str) -> bool:
        return not self.allowed_strategies or strategy_name in self.allowed_strategies


class SessionRouter:
    def __init__(self, policies: dict[Session, SessionPolicy] | None = None) -> None:
        self._policies = policies or default_session_policies()

    def resolve_us(self, now: datetime | None = None) -> Session:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        et = current.astimezone(US_EASTERN)
        if et.weekday() >= 5:
            return Session.CLOSED

        current_time = et.time()
        if time(4, 0) <= current_time < time(9, 30):
            return Session.PRE_MARKET
        if time(9, 30) <= current_time < time(16, 0):
            return Session.REGULAR
        if time(16, 0) <= current_time < time(20, 0):
            return Session.AFTER_HOURS
        return Session.CLOSED

    def policy_for_us(self, now: datetime | None = None) -> SessionPolicy:
        return self._policies[self.resolve_us(now)]

    def policy_for_session(self, session: Session) -> SessionPolicy:
        return self._policies[session]


def default_session_policies() -> dict[Session, SessionPolicy]:
    return {
        Session.PRE_MARKET: SessionPolicy(
            session=Session.PRE_MARKET,
            orders_allowed=True,
            allowed_strategies=("premarket_gap_volume_breakout",),
            max_spread_pct=0.003,
        ),
        Session.REGULAR: SessionPolicy(
            session=Session.REGULAR,
            orders_allowed=False,
            allowed_strategies=(),
        ),
        Session.AFTER_HOURS: SessionPolicy(
            session=Session.AFTER_HOURS,
            orders_allowed=False,
            allowed_strategies=(),
        ),
        Session.CLOSED: SessionPolicy(
            session=Session.CLOSED,
            orders_allowed=False,
            allowed_strategies=(),
        ),
    }
