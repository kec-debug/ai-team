from app.config import Settings
from app.domain.enums import TradingMode
from app.domain.orders import BrokerOrder, OrderAck


class AlpacaPaperBroker:
    mode = TradingMode.PAPER

    def __init__(self, settings: Settings) -> None:
        if not settings.alpaca_paper_api_base or not settings.alpaca_paper_api_base.startswith("https://"):
            raise RuntimeError("Alpaca Paper API base URL must be configured with https://")
        if not settings.alpaca_paper_key_id or not settings.alpaca_paper_secret_key:
            raise RuntimeError("Alpaca Paper credentials are required")
        self._settings = settings

    def submit(self, order: BrokerOrder) -> OrderAck:
        raise NotImplementedError("Alpaca Paper network calls are not implemented in Phase 1")

    def cancel(self, broker_order_id: str) -> None:
        raise NotImplementedError("Alpaca Paper network calls are not implemented in Phase 1")

    def open_orders(self) -> list[BrokerOrder]:
        raise NotImplementedError("Alpaca Paper network calls are not implemented in Phase 1")

    def positions(self) -> dict[str, int]:
        raise NotImplementedError("Alpaca Paper network calls are not implemented in Phase 1")
