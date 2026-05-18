from decimal import Decimal

from fastapi.testclient import TestClient

from app.api.server import create_app
from app.portfolio.account import PaperAccount


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


def test_get_paper_account():
    with TestClient(create_app()) as client:
        response = client.get("/paper/account")
    assert response.status_code == 200
    body = response.json()
    assert body["cash"]["USD"] == "100000"
    assert body["starting_cash"]["USD"] == "100000"
    assert body["safety"]["live_trading_enabled"] is False
    assert body["secret_exposed"] is False


def test_get_paper_positions_initial_empty():
    with TestClient(create_app()) as client:
        response = client.get("/paper/positions")
    assert response.status_code == 200
    assert response.json()["positions"] == []


def test_get_paper_fills_initial_empty():
    with TestClient(create_app()) as client:
        response = client.get("/paper/fills")
    assert response.status_code == 200
    assert response.json()["fills"] == []


def test_get_paper_orders_initial_empty():
    with TestClient(create_app()) as client:
        response = client.get("/paper/orders")
    assert response.status_code == 200
    assert response.json()["open_orders"] == []


def test_post_paper_order_simulate_limit_buy_success():
    with TestClient(create_app()) as client:
        response = client.post("/paper/order/simulate", json=_order_payload())
        account = client.get("/paper/account").json()
        positions = client.get("/paper/positions").json()
        fills = client.get("/paper/fills").json()
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    assert body["filled"] is True
    assert body["reason"] == "filled"
    assert body["rejection_reason"] is None
    assert body["summary_ko"] == "모의 주문이 체결되었습니다. 현금, 보유 종목, 체결 내역이 업데이트되었습니다."
    assert body["risk_result"]["approved"] is True
    assert body["risk_result"]["summary_ko"] == "리스크 검사를 통과했습니다."
    assert body["order"]["symbol"] == "AAPL"
    assert body["cash_before"]["USD"] == "100000"
    assert body["cash_after"]["USD"] == "99899.995"
    assert body["safety_flags"]["live_trading_enabled"] is False
    assert body["fills"][0]["symbol"] == "AAPL"
    assert account["cash"]["USD"] == "99899.995"
    assert positions["positions"][0]["quantity"] == 1
    assert isinstance(positions["positions"][0]["unrealized_pnl"], str)
    assert fills["fills"][0]["symbol"] == "AAPL"
    assert fills["fills"][0]["side"] in ("buy", "sell")
    assert isinstance(fills["recent_orders"], list)


def test_post_paper_order_simulate_insufficient_cash_rejected():
    with TestClient(create_app()) as client:
        client.app.state.paper_engine.account = PaperAccount(cash={"USD": Decimal("10")})
        response = client.post("/paper/order/simulate", json=_order_payload())
        account = client.get("/paper/account").json()
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is False
    assert body["filled"] is False
    assert body["reason"] == "insufficient_cash"
    assert body["rejection_reason"] == "insufficient_cash"
    assert "현금이 부족" in body["summary_ko"]
    assert account["cash"]["USD"] == "10"


def test_post_paper_order_simulate_insufficient_position_rejected():
    with TestClient(create_app()) as client:
        response = client.post(
            "/paper/order/simulate",
            json=_order_payload(side="sell", mock_bid="101", mock_ask="102"),
        )
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is False
    assert body["reason"] == "insufficient_position"
    assert "보유 수량이 부족" in body["summary_ko"]


def test_post_paper_order_simulate_limit_sell_success_after_buy():
    with TestClient(create_app()) as client:
        buy = client.post("/paper/order/simulate", json=_order_payload()).json()
        sell = client.post(
            "/paper/order/simulate",
            json=_order_payload(
                side="sell",
                limit_price="101",
                mock_bid="101",
                mock_ask="102",
                mock_last="101",
            ),
        ).json()
        positions = client.get("/paper/positions").json()
    assert buy["accepted"] is True
    assert sell["accepted"] is True
    assert sell["fills"][0]["price"] == "101"
    assert positions["positions"][0]["quantity"] == 0


def test_post_paper_order_simulate_market_rejected_by_default():
    with TestClient(create_app()) as client:
        response = client.post(
            "/paper/order/simulate",
            json=_order_payload(order_type="market"),
        )
    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is False
    assert body["reason"] == "paper_market_orders_disabled"
    assert body["safety"]["allow_paper_market_orders"] is False


def test_paper_e2e_safety_flags_remain_paper_and_live_false():
    with TestClient(create_app()) as client:
        response = client.post("/paper/order/simulate", json=_order_payload())
    body = response.json()
    assert body["safety"]["mode"] == "paper"
    assert body["safety"]["live_trading_enabled"] is False
    assert body["safety"]["real_broker_orders_enabled"] is False
    assert body["safety_flags"]["real_broker_orders_enabled"] is False


def test_paper_order_simulate_demo_test_order_success(monkeypatch):
    monkeypatch.setenv("SYMBOL_ALLOWLIST", "")
    with TestClient(create_app()) as client:
        response = client.post(
            "/paper/order/simulate",
            json=_order_payload(symbol="TEST", quantity=10, mock_volume=100000),
        )
    body = response.json()
    assert response.status_code == 200
    assert body["accepted"] is True
    assert body["filled"] is True
    assert body["fills"][0]["symbol"] == "TEST"


def test_paper_report_summary_returns_korean_explanation():
    with TestClient(create_app()) as client:
        response = client.get("/paper/report/summary")
    assert response.status_code == 200
    body = response.json()
    assert body["secret_exposed"] is False
    assert "user_summary" in body
    assert "한글 해석" in body["user_summary"]
    assert "이번 tick에서는 주문 후보가 발생하지 않았습니다." in " ".join(body["user_summary"]["한글 해석"])


def test_paper_e2e_responses_do_not_expose_secrets():
    forbidden = ("KIS_APP_KEY", "KIS_APP_SECRET", "KIS_ACCOUNT_NO", "app_secret", "access_token")
    with TestClient(create_app()) as client:
        responses = [
            client.get("/paper/account"),
            client.get("/paper/positions"),
            client.get("/paper/fills"),
            client.get("/paper/orders"),
            client.get("/paper/engine/status"),
            client.post("/paper/order/simulate", json=_order_payload()),
        ]
    for response in responses:
        text = response.text
        assert response.status_code == 200
        for marker in forbidden:
            assert marker not in text
