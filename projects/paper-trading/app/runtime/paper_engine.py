from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal

from app.broker.paper import PaperBroker
from app.config import Settings
from app.domain.enums import Session
from app.domain.orders import OrderIntent
from app.domain.quote import Quote
from app.oms.manager import OMS
from app.portfolio.account import PaperAccount, PaperAccountError
from app.portfolio.service import PortfolioService
from app.runtime.paper_journal import PaperJournal, TradeLogEntry


@dataclass(frozen=True)
class IntentSubmitResult:
    intent: OrderIntent
    accepted: bool
    oms_id: str | None
    broker_order_id: str | None
    status: str | None
    rejected_by: str | None
    reason: str | None
    submitted_at: datetime | None


@dataclass(frozen=True)
class SubmitIntentsBatchResult:
    submitted_count: int
    accepted_count: int
    rejected_count: int
    risk_rejected_count: int
    oms_rejected_count: int
    results: tuple[IntentSubmitResult, ...]
    accepted_oms_ids: tuple[str, ...]
    accepted_broker_order_ids: tuple[str, ...]


def _classify_rejection(reason: str) -> str:
    return "risk_engine" if reason.startswith("RiskEngine rejected") else "oms"


class PaperEngine:
    def __init__(
        self,
        settings: Settings,
        *,
        broker: PaperBroker | None = None,
        account: PaperAccount | None = None,
        portfolio: PortfolioService | None = None,
        journal: PaperJournal | None = None,
        oms: OMS | None = None,
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
        self._oms = oms

    def submit_intents(self, intents: Iterable[OrderIntent]) -> SubmitIntentsBatchResult:
        if self._oms is None:
            raise RuntimeError("PaperEngine.submit_intents requires an OMS")
        materialized = list(intents)
        for index, item in enumerate(materialized):
            if not isinstance(item, OrderIntent):
                raise TypeError(
                    f"submit_intents accepts OrderIntent only; got {type(item).__name__} at index {index}"
                )

        results: list[IntentSubmitResult] = []
        accepted_oms_ids: list[str] = []
        accepted_broker_order_ids: list[str] = []
        accepted_count = 0
        risk_rejected_count = 0
        oms_rejected_count = 0

        for intent in materialized:
            try:
                ack = self._oms.place(intent)
            except (RuntimeError, ValueError) as exc:
                reason = str(exc)
                rejected_by = _classify_rejection(reason)
                if rejected_by == "risk_engine":
                    risk_rejected_count += 1
                else:
                    oms_rejected_count += 1
                results.append(
                    IntentSubmitResult(
                        intent=intent,
                        accepted=False,
                        oms_id=None,
                        broker_order_id=None,
                        status=None,
                        rejected_by=rejected_by,
                        reason=reason,
                        submitted_at=None,
                    )
                )
                continue

            accepted_count += 1
            accepted_oms_ids.append(ack.oms_id)
            if ack.broker_order_id is not None:
                accepted_broker_order_ids.append(ack.broker_order_id)
            results.append(
                IntentSubmitResult(
                    intent=intent,
                    accepted=True,
                    oms_id=ack.oms_id,
                    broker_order_id=ack.broker_order_id,
                    status=ack.status,
                    rejected_by=None,
                    reason=None,
                    submitted_at=datetime.now(timezone.utc),
                )
            )

        return SubmitIntentsBatchResult(
            submitted_count=len(materialized),
            accepted_count=accepted_count,
            rejected_count=len(materialized) - accepted_count,
            risk_rejected_count=risk_rejected_count,
            oms_rejected_count=oms_rejected_count,
            results=tuple(results),
            accepted_oms_ids=tuple(accepted_oms_ids),
            accepted_broker_order_ids=tuple(accepted_broker_order_ids),
        )

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
