import json
import pathlib
import re
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.api.server import create_app
from app.broker.kis import KisBroker
from app.broker.paper import PaperBroker
from app.config import load_settings
from app.domain.enums import OrderType, Session, Side, TradingMode
from app.domain.orders import OrderIntent
from app.domain.quote import Quote
from app.oms.manager import OMS
from app.portfolio.account import PaperAccount
from app.portfolio.service import PortfolioService
from app.risk.engine import RiskEngine
from app.runtime.paper_engine import PaperEngine
from app.runtime.paper_journal import PaperJournal
from app.runtime.paper_runner import PaperRunner
from app.strategy.premarket_gap import PremarketGapVolumeBreakoutStrategy


def _wire_paper_pipeline(settings):
    risk = RiskEngine(settings)
    broker = PaperBroker(
        max_quote_age_seconds=settings.paper_max_quote_age_seconds,
        allowed_sessions={Session(s) for s in settings.paper_allowed_sessions},
        max_fill_ratio_of_volume=settings.paper_max_fill_ratio_of_volume,
        commission_per_share=settings.paper_commission_per_share,
        commission_per_fill=settings.paper_commission_per_fill,
    )
    oms = OMS(settings, risk, broker)
    portfolio = PortfolioService()
    starting_cash = dict(
        settings.paper_starting_cash_by_currency
        or {settings.paper_base_currency: settings.paper_starting_cash}
    )
    account = PaperAccount(cash=starting_cash)
    journal = PaperJournal()
    paper_engine = PaperEngine(
        settings,
        broker=broker,
        account=account,
        portfolio=portfolio,
        journal=journal,
        oms=oms,
    )
    strategy = PremarketGapVolumeBreakoutStrategy(settings)
    runner = PaperRunner(settings, strategy, oms=oms, paper_engine=paper_engine)
    return {
        "strategy": strategy,
        "risk": risk,
        "broker": broker,
        "account": account,
        "portfolio": portfolio,
        "journal": journal,
        "oms": oms,
        "paper_engine": paper_engine,
        "runner": runner,
    }


def _matching_quote(snapshot, *, volume=500_000):
    return Quote(
        symbol=snapshot.symbol,
        last=snapshot.ask,
        bid=snapshot.bid,
        ask=snapshot.ask,
        volume=volume,
        timestamp=datetime.now(timezone.utc),
        source="e2e_test",
        session=Session.REGULAR,
        currency="USD",
    )


def _kis_paper_settings(settings, **overrides):
    data = {
        "kis_env": "paper",
        "kis_account_no": "12345678-01",
        "kis_app_key": "fake-key-XYZ",
        "kis_app_secret": "fake-secret-XYZ",
        "kis_api_mode": "paper",
        "kis_order_dry_run": True,
    }
    data.update(overrides)
    return replace(settings, **data)


class _RaiseOnCallOrderTransport:
    """KisOrderTransport that asserts no HTTP path is ever invoked."""

    def submit_order(self, **kwargs):  # pragma: no cover - invocation is a failure
        raise AssertionError(
            "KisBroker dry-run unexpectedly invoked the order transport; kwargs="
            + ", ".join(sorted(kwargs))
        )


def _build_intent(
    symbol="AAPL",
    side=Side.BUY,
    quantity=10,
    limit=Decimal("100.50"),
    order_type=OrderType.LIMIT,
):
    return OrderIntent(
        symbol=symbol,
        side=side,
        quantity=quantity,
        order_type=order_type,
        limit_price=limit,
        currency="USD",
        client_tag="e2e_test",
        quote_timestamp=datetime.now(timezone.utc),
    )


def _order_payload(**overrides):
    payload = {
        "symbol": "AAPL",
        "side": "buy",
        "quantity": 1,
        "order_type": "limit",
        "limit_price": "100",
        "stop_price": None,
        "mock_bid": "99",
        "mock_ask": "100",
        "mock_last": "100",
        "mock_volume": 100,
        "currency": "USD",
    }
    payload.update(overrides)
    return payload


def test_e2e_happy_path_strategy_to_fill_through_oms_paper_engine(settings, make_snapshot):
    components = _wire_paper_pipeline(settings)
    runner = components["runner"]
    broker = components["broker"]
    paper_engine = components["paper_engine"]
    account = components["account"]
    portfolio = components["portfolio"]
    journal = components["journal"]

    snapshot = make_snapshot(
        symbol="AAPL",
        previous_close=Decimal("100"),
        current_price=Decimal("106"),
        premarket_high=Decimal("106"),
        premarket_volume=200_000,
        bid=Decimal("105.90"),
        ask=Decimal("106.00"),
    )

    results = runner.run_once([snapshot])
    assert len(results) == 1
    assert results[0].strategy.passed is True
    assert results[0].oms_ack is not None
    assert results[0].oms_error is None

    open_orders = broker.open_orders()
    assert len(open_orders) == 1
    assert open_orders[0].symbol == "AAPL"
    assert open_orders[0].side is Side.BUY
    assert open_orders[0].order_type is OrderType.LIMIT
    assert open_orders[0].risk_token

    starting_cash = dict(account.cash)
    trades = paper_engine.on_quote(_matching_quote(snapshot))
    assert len(trades) >= 1
    assert trades[0].symbol == "AAPL"
    assert trades[0].oms_id == results[0].oms_ack.oms_id

    assert account.cash["USD"] < starting_cash["USD"]
    snapshot_portfolio = portfolio.get_snapshot()
    assert "AAPL" in snapshot_portfolio.positions
    assert snapshot_portfolio.positions["AAPL"].quantity > 0
    assert len(journal.trades) >= 1
    assert journal.trades[0].symbol == "AAPL"


def test_e2e_strategy_blocker_does_not_reach_oms_or_broker(settings, make_snapshot):
    components = _wire_paper_pipeline(settings)
    components["oms"].place = Mock(wraps=components["oms"].place)
    snapshot = make_snapshot(premarket_volume=10)

    results = components["runner"].run_once([snapshot])
    trades = components["paper_engine"].on_quote(_matching_quote(snapshot))

    assert results[0].strategy.passed is False
    assert "volume_below_threshold" in results[0].strategy.blockers
    assert components["oms"].place.call_count == 0
    assert components["broker"].open_orders() == []
    assert trades == []
    assert components["account"].cash["USD"] == settings.paper_starting_cash


def test_e2e_risk_engine_reject_does_not_reach_broker(settings, make_snapshot):
    configured = replace(settings, symbol_allowlist=("MSFT",))
    components = _wire_paper_pipeline(configured)
    snapshot = make_snapshot(symbol="AAPL")

    results = components["runner"].run_once([snapshot])
    assert results[0].oms_error is not None
    assert "RiskEngine rejected" in results[0].oms_error
    assert components["broker"].open_orders() == []

    batch = components["paper_engine"].submit_intents([_build_intent()])
    assert batch.results[0].accepted is False
    assert batch.results[0].rejected_by == "risk_engine"
    assert components["broker"].open_orders() == []


def test_e2e_oms_rejects_non_paper_broker_mode(settings):
    class _NonPaperBroker:
        mode = TradingMode.LIVE

    oms = OMS(settings, RiskEngine(settings), _NonPaperBroker())
    with pytest.raises(RuntimeError, match="OMS rejects non-paper broker"):
        oms.place(_build_intent())


def test_e2e_oms_rejects_live_trading_enabled(settings):
    bad_settings = replace(settings, live_trading_enabled=True)
    components = _wire_paper_pipeline(bad_settings)
    with pytest.raises(RuntimeError, match="OMS refuses live trading"):
        components["oms"].place(_build_intent())


def test_e2e_kis_dry_run_returns_dry_run_ack_without_http(settings):
    kis_settings = _kis_paper_settings(settings, symbol_allowlist=("AAPL",))
    risk = RiskEngine(kis_settings)
    kis_broker = KisBroker(kis_settings)
    kis_broker._order_transport = _RaiseOnCallOrderTransport()
    oms_kis = OMS(kis_settings, risk, kis_broker)

    ack = oms_kis.place(_build_intent())

    assert ack.status == "dry_run"
    assert ack.broker_order_id is None
    assert ack.mode is TradingMode.PAPER
    assert kis_broker.last_order_preview is not None
    assert kis_broker.last_order_response is None
    assert kis_broker.last_error is None

    health = kis_broker.healthcheck()
    assert health["order_dry_run"] is True
    assert health["order_execution_implemented"] is False
    assert health["order_methods_fail_closed"] is True


def test_e2e_market_order_intent_is_blocked_before_broker(settings, monkeypatch):
    components = _wire_paper_pipeline(settings)
    market_intent = _build_intent(order_type=OrderType.MARKET)

    with pytest.raises(RuntimeError, match="RiskEngine rejected"):
        components["oms"].place(market_intent)
    assert components["broker"].open_orders() == []

    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "false")
    monkeypatch.setenv("ALLOW_MARKET_ORDERS", "true")
    with pytest.raises(ValueError, match="ALLOW_MARKET_ORDERS.*rejected"):
        load_settings()


def test_e2e_dashboard_status_reflects_paper_engine_state_after_fill():
    with TestClient(create_app()) as client:
        before_account = client.get("/paper/account").json()
        sim = client.post("/paper/order/simulate", json=_order_payload()).json()
        after_account = client.get("/paper/account").json()
        after_positions = client.get("/paper/positions").json()
        after_fills = client.get("/paper/fills").json()
        after_engine = client.get("/paper/engine/status").json()
        after_status = client.get("/paper/status").json()

    assert sim["accepted"] is True
    assert sim["filled"] is True
    assert Decimal(after_account["cash"]["USD"]) < Decimal(before_account["cash"]["USD"])
    assert after_positions["positions"][0]["quantity"] >= 1
    assert "unrealized_pnl" in after_positions["positions"][0]
    assert after_fills["fills"][0]["symbol"] == "AAPL"
    assert after_fills["fills"][0]["side"] == "buy"
    assert after_fills["fills"][0]["price"] == "100"
    assert after_engine["account"]["cash"]["USD"] == after_account["cash"]["USD"]
    assert after_engine["portfolio"]["positions"][0]["quantity"] >= 1
    assert after_engine["journal"]["fills_count"] >= 1
    assert after_engine["journal"]["recent_fills"][0]["symbol"] == "AAPL"
    assert after_status["mode"] == "paper"
    assert after_status["live_enabled"] is False
    assert after_status["safety"]["market_orders_disabled"] is True
    assert after_status["kis_order_methods_fail_closed"] is True
    assert after_status["kis_order_dry_run"] is True
    assert after_status["secret_exposed"] is False

    forbidden_text_tokens = (
        "KIS_APP_KEY",
        "KIS_APP_SECRET",
        "KIS_ACCOUNT_NO",
        "app_secret",
        "access_token",
        "Bearer ",
    )
    combined_text = json.dumps(
        [
            before_account,
            sim,
            after_account,
            after_positions,
            after_fills,
            after_engine,
            after_status,
        ]
    )
    for token in forbidden_text_tokens:
        assert token not in combined_text


def test_e2e_strategy_and_agent_packages_do_not_import_broker_modules():
    project_root = pathlib.Path(__file__).resolve().parents[1] / "app"
    forbidden = re.compile(r"^\s*(from|import)\s+app\.broker\.(kis|paper)\b", re.MULTILINE)
    for package in ("strategy", "agent"):
        package_dir = project_root / package
        if not package_dir.is_dir():
            continue
        for path in package_dir.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            assert not forbidden.search(text), f"{path} imports a broker module directly"
