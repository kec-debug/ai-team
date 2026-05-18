from dataclasses import dataclass

from app.domain.market import StrategyInput
from app.domain.orders import OrderAck
from app.strategy.base import Strategy, StrategyResult


@dataclass(frozen=True)
class PaperRunResult:
    symbol: str
    strategy: StrategyResult
    oms_ack: OrderAck | None
    oms_error: str | None


class PaperRunner:
    def __init__(self, settings, strategy: Strategy, oms) -> None:
        self._settings = settings
        self._strategy = strategy
        self._oms = oms

    def run_once(self, snapshots: list[StrategyInput]) -> list[PaperRunResult]:
        results: list[PaperRunResult] = []
        for snapshot in snapshots:
            strategy_result = self._strategy.evaluate(snapshot)
            ack = None
            error = None
            if strategy_result.passed and strategy_result.non_executable_order_intent is not None:
                try:
                    ack = self._oms.place(strategy_result.non_executable_order_intent)
                except RuntimeError as exc:
                    error = str(exc)
            results.append(PaperRunResult(snapshot.symbol, strategy_result, ack, error))
        return results
