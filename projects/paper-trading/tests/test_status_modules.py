from app.api.routes import paper_status
from app.broker.paper import PaperBroker
from app.config import Settings
from app.portfolio import PortfolioService
from app.session import SessionRouter


class _State:
    pass


class _App:
    pass


class _Request:
    pass


def _request() -> _Request:
    req = _Request()
    req.app = _App()
    req.app.state = _State()
    req.app.state.settings = Settings(symbol_allowlist=("AAPL",))
    req.app.state.broker = PaperBroker()
    req.app.state.kis_broker = None
    req.app.state.configured_brokers = []
    req.app.state.session_router = SessionRouter()
    req.app.state.portfolio = PortfolioService()
    return req


def test_paper_status_includes_session_and_portfolio_without_secrets():
    body = paper_status(_request())

    assert body["session"]["market"] == "US"
    assert body["session"]["current"] in {"pre_market", "regular", "after_hours", "closed"}
    assert isinstance(body["session"]["orders_allowed"], bool)
    assert "premarket_gap_volume_breakout" in body["session"]["allowed_strategies"] or (
        body["session"]["orders_allowed"] is False
    )
    assert body["portfolio"] == {
        "positions_count": 0,
        "market_value": "0",
        "realized_pnl": "0",
    }
    assert body["live_trading_enabled"] is False
    assert body["market_orders_allowed"] is False
    assert body["secret_exposed"] is False
