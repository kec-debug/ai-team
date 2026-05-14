from app.broker.paper import PaperBroker
from app.oms.manager import OMS
from app.risk.engine import RiskEngine
from app.strategy.premarket_gap import PremarketGapVolumeBreakoutStrategy


def test_strategy_to_oms_to_paper_broker_flow(settings, make_snapshot):
    strategy_result = PremarketGapVolumeBreakoutStrategy(settings).evaluate(make_snapshot())
    assert strategy_result.passed
    ack = OMS(settings, RiskEngine(settings), PaperBroker()).place(strategy_result.non_executable_order_intent)
    assert ack.status == "accepted"
