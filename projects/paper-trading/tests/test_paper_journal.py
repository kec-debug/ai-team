from datetime import datetime, timezone
from decimal import Decimal

from app.domain.enums import Side
from app.domain.fills import Fill
from app.runtime.paper_journal import PaperJournal, TradeLogEntry


def test_paper_journal_records_trade_in_memory():
    fill = Fill(
        broker_order_id="broker",
        oms_id="oms",
        symbol="AAPL",
        side=Side.BUY,
        quantity=1,
        price=Decimal("10"),
        currency="USD",
        commission=Decimal("0"),
        liquidity="simulated",
        filled_at=datetime.now(timezone.utc),
    )
    journal = PaperJournal()
    journal.record_trade(TradeLogEntry.from_fill(fill))
    assert journal.trades[0].symbol == "AAPL"


def test_paper_journal_records_rejected_order():
    journal = PaperJournal()
    journal.rejected_order(
        broker_order_id="broker",
        oms_id="oms",
        symbol="AAPL",
        reason="insufficient_cash",
    )
    assert journal.orders[0].reason == "insufficient_cash"
