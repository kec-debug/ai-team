from dataclasses import replace

from fastapi.testclient import TestClient

from app.api.server import create_app


def _snapshot(symbol: str = "AAPL") -> dict:
    return {
        "symbol": symbol,
        "market": "US",
        "session": "pre_market",
        "previous_close": "100",
        "current_price": "106",
        "premarket_high": "105",
        "premarket_volume": 200000,
        "bid": "105.80",
        "ask": "106.00",
        "timestamp": "2026-05-20T13:30:00Z",
        "relative_volume": "2.0",
        "opening_range_high": "106.50",
        "opening_range_low": "104.50",
        "vwap": "105.20",
    }


def test_paper_training_endpoints_are_paper_only_smoke():
    with TestClient(create_app()) as client:
        status = client.get("/paper/training/status")
        assert status.status_code == 200
        assert status.json()["mode"] == "paper"
        assert status.json()["secret_exposed"] is False

        assert client.post("/paper/training/start").status_code == 200
        second_start = client.post("/paper/training/start")
        assert second_start.status_code == 200
        assert second_start.json()["already_running"] is True
        tick = client.post("/paper/training/tick", json={"snapshots": []})
        assert tick.status_code == 200
        assert "tick_result" in tick.json()
        runs = client.get("/paper/training/runs")
        assert runs.status_code == 200
        assert runs.json()["secret_exposed"] is False
        assert client.post("/paper/training/stop").status_code == 200


def test_paper_training_start_blocks_when_live_enabled():
    with TestClient(create_app()) as client:
        client.app.state.settings = replace(client.app.state.settings, live_trading_enabled=True)
        response = client.post("/paper/training/start")
        assert response.status_code == 423
        assert response.json()["detail"] == "paper_training_locked"


def test_agent_research_endpoints_are_deterministic_and_non_executable():
    with TestClient(create_app()) as client:
        status = client.get("/agents/status")
        assert status.status_code == 200
        assert status.json()["provider_used"] == "deterministic_stub"
        assert "analysis_count" in status.json()
        assert status.json()["primary_symbols"]

        run = client.post("/agents/run", json={"symbols": ["aapl", "msft"], "context": {"source": "test"}})
        assert run.status_code == 200
        body = run.json()
        assert body["fallback_used"] is False
        assert body["parse_status"] == "parsed"
        assert body["analysis_count"] == 2
        assert body["analyzed_symbols"] == ["AAPL", "MSFT"]
        assert body["primary_symbols"] == ["AAPL", "MSFT"]
        assert body["flow_analysis"]["analysis_count"] == 2
        assert body["flow_analysis"]["signals"][0]["metadata"]["no_hidden_actor_claim"] is True
        assert body["recommendations"][0]["non_executable_order_intent"]["executable"] is False

        traces = client.get("/agents/traces")
        assert traces.status_code == 200
        assert len(traces.json()["traces"]) == 1


def test_flow_agent_scores_visible_inputs_and_marks_missing_data():
    with TestClient(create_app()) as client:
        response = client.post(
            "/agents/flow/run",
            json={
                "candidates": [
                    {
                        "symbol": "AAPL",
                        "current_price": "101",
                        "vwap": "100",
                        "volume": 300000,
                        "avg_volume": 100000,
                        "large_trade_net_value": "250000",
                        "institutional_net_buy_value": "100000",
                    },
                    {"symbol": "MSFT"},
                ]
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["analysis_count"] == 2
    assert body["signals"][0]["symbol"] == "AAPL"
    assert body["signals"][0]["confidence"] > body["signals"][1]["confidence"]
    assert "pullback_requires_current_price_and_vwap" in body["signals"][1]["blockers"]


def test_strategy_lab_endpoints_do_not_submit_orders():
    with TestClient(create_app()) as client:
        listing = client.get("/strategies")
        assert listing.status_code == 200
        strategy_id = listing.json()["strategies"][0]["id"]

        detail = client.get(f"/strategies/{strategy_id}")
        assert detail.status_code == 200
        assert detail.json()["paper_only"] is True
        assert detail.json()["broker_direct_call"] is False

        simulation = client.post(f"/strategies/{strategy_id}/simulate", json={"snapshot": _snapshot()})
        assert simulation.status_code == 200
        body = simulation.json()
        assert body["submitted_to_oms"] is False
        assert "result" in body


def test_reports_aliases_smoke_after_training_run():
    with TestClient(create_app()) as client:
        client.post("/paper/training/start")
        client.post("/paper/training/stop")
        index = client.get("/reports")
        assert index.status_code == 200
        assert index.json()["secret_exposed"] is False
        latest = client.get("/reports/latest")
        assert latest.status_code == 200
        assert latest.json()["summary"]["secret_exposed"] is False


def test_live_console_read_only_endpoints_are_locked():
    with TestClient(create_app()) as client:
        status = client.get("/live/status")
        assert status.status_code == 200
        assert status.json()["armed"] is False
        assert status.json()["locked"] is True
        assert status.json()["can_trade"] is False

        preflight = client.get("/live/preflight")
        assert preflight.status_code == 200
        assert preflight.json()["read_only"] is True

        account = client.get("/live/account")
        positions = client.get("/live/positions")
        assert account.status_code == 200
        assert positions.status_code == 200
        assert account.json()["locked"] is True
        assert positions.json()["locked"] is True
        assert client.post("/live/status").status_code == 405
        assert client.post("/live/account").status_code == 405


def test_live_validation_can_arm_and_disarm_without_enabling_trading():
    with TestClient(create_app()) as client:
        missing_ack = client.post("/live/arm", json={"acknowledge": False})
        assert missing_ack.status_code == 400

        armed = client.post("/live/arm", json={"acknowledge": True})
        assert armed.status_code == 200
        assert armed.json()["armed"] is True
        assert armed.json()["locked"] is False
        assert armed.json()["can_trade"] is False
        assert armed.json()["read_only"] is True

        ops = client.get("/ops/status")
        assert ops.status_code == 200
        assert ops.json()["live_validation_armed"] is True

        disarmed = client.post("/live/disarm")
        assert disarmed.status_code == 200
        assert disarmed.json()["armed"] is False
        assert disarmed.json()["locked"] is True
        assert disarmed.json()["can_trade"] is False


def test_live_order_entry_request_is_gated_and_does_not_enable_trading():
    with TestClient(create_app()) as client:
        bad_phrase = client.post(
            "/live/order-entry/request",
            json={"acknowledge": True, "phrase": "enable"},
        )
        assert bad_phrase.status_code == 400

        client.post("/live/arm", json={"acknowledge": True})
        requested = client.post(
            "/live/order-entry/request",
            json={
                "acknowledge": True,
                "phrase": "실전거래 위험을 이해하고 직접 승인합니다",
            },
        )
        assert requested.status_code == 200
        body = requested.json()
        assert body["requested"] is True
        assert body["can_trade"] is False
        assert "live_trading_enabled_env_false" in body["blockers"]

        status = client.get("/live/status").json()
        assert status["order_entry"]["requested"] is True
        assert status["can_trade"] is False

        disabled = client.post("/live/order-entry/disable")
        assert disabled.status_code == 200
        assert disabled.json()["requested"] is False


def test_kis_runtime_endpoints_never_expose_secrets():
    with TestClient(create_app()) as client:
        status = client.get("/kis/status")
        assert status.status_code == 200
        assert status.json()["secret_exposed"] is False

        auth = client.post("/kis/authenticate")
        if auth.status_code == 200:
            assert auth.json()["secret_exposed"] is False
            assert "ok" in auth.json()
            assert "KIS_APP_KEY" not in auth.text
            assert "KIS_APP_SECRET" not in auth.text
            assert "KIS_ACCOUNT_NO" not in auth.text
        else:
            assert auth.status_code == 424
