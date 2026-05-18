from dataclasses import dataclass

from app.domain.enums import TradingMode
from app.domain.market import StrategyInput
from app.domain.orders import OrderAck
from app.runtime.paper_engine import PaperEngine
from app.strategy.base import Strategy, StrategyResult


@dataclass(frozen=True)
class PaperRunResult:
    symbol: str
    strategy: StrategyResult
    oms_ack: OrderAck | None
    oms_error: str | None


class PaperRunner:
    def __init__(
        self,
        settings,
        strategy: Strategy,
        oms=None,
        *,
        paper_engine: PaperEngine | None = None,
    ) -> None:
        if oms is None and paper_engine is None:
            raise ValueError("PaperRunner requires oms or paper_engine")
        self._settings = settings
        self._strategy = strategy
        self._oms = oms
        self._paper_engine = paper_engine

    def run_once(self, snapshots: list[StrategyInput]) -> list[PaperRunResult]:
        results: list[PaperRunResult] = []
        for snapshot in snapshots:
            strategy_result = self._strategy.evaluate(snapshot)
            ack: OrderAck | None = None
            error: str | None = None
            if strategy_result.passed and strategy_result.non_executable_order_intent is not None:
                intent = strategy_result.non_executable_order_intent
                if self._paper_engine is not None:
                    batch = self._paper_engine.submit_intents([intent])
                    first = batch.results[0]
                    if first.accepted and first.oms_id is not None:
                        ack = OrderAck(
                            oms_id=first.oms_id,
                            broker_order_id=first.broker_order_id,
                            status=first.status or "accepted",
                            mode=TradingMode.PAPER,
                        )
                    else:
                        error = first.reason
                else:
                    try:
                        ack = self._oms.place(intent)
                    except RuntimeError as exc:
                        error = str(exc)
            results.append(PaperRunResult(snapshot.symbol, strategy_result, ack, error))
        return results
