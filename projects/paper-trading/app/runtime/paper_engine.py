from decimal import Decimal

from app.broker.paper import PaperBroker
from app.config import Settings
from app.domain.enums import Session
from app.domain.quote import Quote
from app.portfolio.account import PaperAccount, PaperAccountError
from app.portfolio.service import PortfolioService
from app.runtime.paper_journal import PaperJournal, TradeLogEntry


class PaperEngine:
    def __init__(
        self,
        settings: Settings,
        *,
        broker: PaperBroker | None = None,
        account: PaperAccount | None = None,
        portfolio: PortfolioService | None = None,
        journal: PaperJournal | None = None,
    ) -> None:
        allowed_sessions = {Session(session) for session in settings.paper_allowed_sessions}
        self.broker = broker or PaperBroker(
            max_quote_age_seconds=settings.paper_max_quote_age_seconds,
            allowed_sessions=allowed_sessions,
            max_fill_ratio_of_volume=settings.paper_max_fill_ratio_of_volume,
            commission_per_share=settings.paper_commission_per_share,
            commission_per_fill=settings.paper_commission_per_fill,
        )
        starting_cash = settings.paper_starting_cash_by_currency or {
            settings.paper_base_currency: settings.paper_starting_cash
        }
        self.account = account or PaperAccount(cash=dict(starting_cash))
        self.portfolio = portfolio or PortfolioService()
        self.journal = journal or PaperJournal(settings.paper_log_dir)

    def on_quote(self, quote: Quote) -> list[TradeLogEntry]:
        trade_entries: list[TradeLogEntry] = []
        for fill in self.broker.tick(quote):
            try:
                self.account.apply_fill(fill)
            except PaperAccountError as exc:
                self.journal.rejected_order(
                    broker_order_id=fill.broker_order_id,
                    oms_id=fill.oms_id,
                    symbol=fill.symbol,
                    reason=str(exc),
                )
                continue
            self.portfolio.apply_trade(fill)
            self.portfolio.mark_price(fill.symbol, fill.price, fill.currency)
            entry = TradeLogEntry.from_fill(fill)
            self.journal.record_trade(entry)
            trade_entries.append(entry)
        return trade_entries

    def mark_quote(self, quote: Quote) -> None:
        self.portfolio.mark_price(quote.symbol, quote.last, quote.currency)

    def cash_by_currency(self) -> dict[str, Decimal]:
        return dict(self.account.cash)
