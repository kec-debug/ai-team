from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.config import Settings
from app.domain.enums import Session
from app.domain.market import StrategyInput


@pytest.fixture
def settings() -> Settings:
    return Settings(symbol_allowlist=("AAPL", "MSFT"))


@pytest.fixture
def make_snapshot():
    def _make_snapshot(**overrides) -> StrategyInput:
        data = {
            "symbol": "AAPL",
            "market": "US",
            "session": Session.PRE_MARKET,
            "previous_close": Decimal("100"),
            "current_price": Decimal("106"),
            "premarket_high": Decimal("106"),
            "premarket_volume": 200_000,
            "bid": Decimal("105.90"),
            "ask": Decimal("106.00"),
            "timestamp": datetime.now(timezone.utc),
            "relative_volume": Decimal("2.0"),
        }
        data.update(overrides)
        return StrategyInput(**data)

    return _make_snapshot
