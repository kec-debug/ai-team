from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.enums import Session


class StrategyInput(BaseModel):
    model_config = ConfigDict(use_enum_values=False)

    symbol: str
    market: str
    session: Session
    previous_close: Decimal
    current_price: Decimal
    premarket_high: Decimal
    premarket_volume: int
    bid: Decimal
    ask: Decimal
    timestamp: datetime
    relative_volume: Decimal | None = None
    opening_range_high: Decimal | None = None
    opening_range_low: Decimal | None = None
    vwap: Decimal | None = None

    @field_validator("symbol")
    @classmethod
    def uppercase_symbol(cls, value: str) -> str:
        return value.upper()

    @field_validator("previous_close", "current_price", "premarket_high", "bid", "ask")
    @classmethod
    def positive_decimal(cls, value: Decimal) -> Decimal:
        if value <= 0:
            raise ValueError("price fields must be positive")
        return value

    @field_validator("opening_range_high", "opening_range_low", "vwap")
    @classmethod
    def positive_optional_decimal(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("opening range / vwap fields must be positive when provided")
        return value

    @field_validator("premarket_volume")
    @classmethod
    def non_negative_volume(cls, value: int) -> int:
        if value < 0:
            raise ValueError("premarket_volume must be non-negative")
        return value
