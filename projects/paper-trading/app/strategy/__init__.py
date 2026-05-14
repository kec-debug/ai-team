from app.config import Settings
from app.strategy.premarket_gap import PremarketGapVolumeBreakoutStrategy


STRATEGY_NAMES = ("premarket_gap_volume_breakout",)


def create_strategy(name: str, settings: Settings):
    if name == "premarket_gap_volume_breakout":
        return PremarketGapVolumeBreakoutStrategy(settings)
    raise KeyError(name)


__all__ = ["PremarketGapVolumeBreakoutStrategy", "STRATEGY_NAMES", "create_strategy"]
