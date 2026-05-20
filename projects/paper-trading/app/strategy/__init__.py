from app.config import Settings
from app.strategy.opening_range_breakout import OpeningRangeBreakoutStrategy
from app.strategy.premarket_gap import PremarketGapVolumeBreakoutStrategy


STRATEGY_NAMES = ("premarket_gap_volume_breakout", "opening_range_breakout")


def create_strategy(name: str, settings: Settings):
    if name == "premarket_gap_volume_breakout":
        return PremarketGapVolumeBreakoutStrategy(settings)
    if name == "opening_range_breakout":
        return OpeningRangeBreakoutStrategy(settings)
    raise KeyError(name)


__all__ = [
    "OpeningRangeBreakoutStrategy",
    "PremarketGapVolumeBreakoutStrategy",
    "STRATEGY_NAMES",
    "create_strategy",
]
