from fastapi.testclient import TestClient

from app.api.server import create_app
from tests.test_paper_e2e_api import _order_payload


def test_paper_engine_status_initial_state():
    with TestClient(create_app()) as client:
        response = client.get("/paper/engine/status")

    assert response.status_code == 200
    body = response.json()
    assert set(body) >= {"account", "portfolio", "journal", "engine", "safety", "secret_exposed"}
    assert body["secret_exposed"] is False
    assert body["engine"]["paper_engine_enabled"] is True
    assert body["engine"]["paper_journal_enabled"] is True
    assert isinstance(body["engine"]["paper_journal_persistent_logging"], bool)
    assert body["engine"]["last_fill_at"] is None
    assert body["journal"]["fills_count"] == 0
    assert body["journal"]["recent_fills"] == []
    assert body["journal"]["recent_orders"] == []
    assert isinstance(body["account"]["starting_cash"], dict)
    assert body["account"]["starting_cash"]["USD"] == "100000"


def test_paper_engine_status_after_fill():
    with TestClient(create_app()) as client:
        order = client.post("/paper/order/simulate", json=_order_payload()).json()
        response = client.get("/paper/engine/status")

    assert order["accepted"] is True
    assert response.status_code == 200
    body = response.json()
    assert body["journal"]["recent_fills"][0]["side"] in ("buy", "sell")
    assert body["engine"]["last_fill_at"]
    assert body["engine"]["last_trade_at"] == body["engine"]["last_fill_at"]
    assert body["portfolio"]["positions_count"] == 1
    assert "USD" in body["portfolio"]["unrealized_pnl_by_currency"]


def test_paper_engine_status_masks_sensitive_values(monkeypatch):
    monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")
    monkeypatch.setenv("KIS_APP_KEY", "fake-key")
    monkeypatch.setenv("KIS_APP_SECRET", "fake-secret")
    with TestClient(create_app()) as client:
        response = client.get("/paper/engine/status")

    assert response.status_code == 200
    text = response.text
    for marker in (
        "/root/",
        "/home/",
        "KIS_APP_KEY",
        "KIS_APP_SECRET",
        "KIS_ACCOUNT_NO",
        "Bearer ",
        "access_token",
        "12345678",
    ):
        assert marker not in text
    masked = response.json()["engine"]["paper_journal_log_dir_masked"]
    assert masked == "disabled" or masked.startswith("…/") or masked.startswith("reports/")
