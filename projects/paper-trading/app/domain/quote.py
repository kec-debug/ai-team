"""Quote domain model: broker-agnostic market data snapshot.

``bid_ask_present`` marks whether bid/ask came from the source or were
synthetically derived from ``last``.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from app.domain.enums import Session


@dataclass(frozen=True)
class Quote:
    symbol: str
    last: Decimal
    bid: Decimal
    ask: Decimal
    volume: int
    timestamp: datetime
    source: str
    session: Session | None = None
    currency: str = "USD"
    bid_ask_present: bool = True

    def __post_init__(self) -> None:
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be non-empty uppercase")
        if self.last <= 0:
            raise ValueError("last must be > 0")
        if self.bid <= 0:
            raise ValueError("bid must be > 0")
        if self.ask < self.bid:
            raise ValueError("ask must be >= bid")
        if self.volume < 0:
            raise ValueError("volume must be >= 0")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        if not self.source:
            raise ValueError("source must be non-empty")
        if self.currency != self.currency.upper():
            raise ValueError("currency must be uppercase")

    @property
    def spread_pct(self) -> Decimal:
        """Return (ask - bid) / last as a Decimal fraction."""
        if self.last == 0:
            return Decimal("0")
        return (self.ask - self.bid) / self.last

    def is_stale(self, now: datetime, max_age_seconds: int) -> bool:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        age = (now - self.timestamp).total_seconds()
        return age > max_age_seconds or age < 0
