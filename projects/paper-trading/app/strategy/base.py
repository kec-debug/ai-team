from abc import ABC, abstractmethod
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.domain.market import StrategyInput
from app.domain.orders import OrderIntent


class StrategyResult(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    symbol: str
    passed: bool
    score: float | None = None
    reasons: list[str] = []
    blockers: list[str] = []
    suggested_limit_price: Decimal | None = None
    non_executable_order_intent: OrderIntent | None = None


class Strategy(ABC):
    name: str

    @abstractmethod
    def evaluate(self, snapshot: StrategyInput) -> StrategyResult:
        ...
