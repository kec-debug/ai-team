import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.server import create_app


@pytest.fixture
def app_with_run(monkeypatch):
    test_subdir = "reports/test_runs_mvp019"
    monkeypatch.setenv("DRY_RUN_REPORTS_DIR", test_subdir)
    monkeypatch.setenv("TRADING_MODE", "paper")
    monkeypatch.setenv("LIVE_TRADING_ENABLED", "false")
    monkeypatch.setenv("ALLOW_MARKET_ORDERS", "false")
    project_dir = Path(__file__).resolve().parents[1]
    base = project_dir / test_subdir
    shutil.rmtree(base, ignore_errors=True)
    base.mkdir(parents=True, exist_ok=True)
    run_dir = base / "run_2026-05-14T08-00-00"
    run_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "state": "stopped",
        "counters": {
            "candidates_seen": 1,
            "candidates_blocked": 0,
            "candidates_passed_risk": 1,
        },
    }
    (run_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (run_dir / "events.jsonl").write_text(
        json.dumps({"type": "tick_result", "symbol": "AAPL", "passed": True, "blockers": []}) + "\n",
        encoding="utf-8",
    )
    yield create_app()
    shutil.rmtree(base, ignore_errors=True)


def test_analyze_latest_via_post(app_with_run):
    with TestClient(app_with_run) as client:
        response = client.post("/reports/dry-run/analyze", json={})
    assert response.status_code == 200
    body = response.json()
    assert body["run_dir"] == "run_2026-05-14T08-00-00"
    assert body["summary"]["secret_exposed"] is False
    assert "analysis_summary.json" in body["files"]["summary"]


def test_get_latest_after_analyze(app_with_run):
    with TestClient(app_with_run) as client:
        client.post("/reports/dry-run/analyze", json={})
        response = client.get("/reports/dry-run/latest")
    assert response.status_code == 200
    assert response.json()["summary"]["secret_exposed"] is False


def test_latest_auto_analyzes_if_missing(app_with_run):
    with TestClient(app_with_run) as client:
        response = client.get("/reports/dry-run/latest")
    assert response.status_code == 200
    assert response.json()["summary"]["strategy_pass_rate"] == 1.0


def test_analyze_rejects_path_traversal(app_with_run):
    with TestClient(app_with_run) as client:
        response = client.post("/reports/dry-run/analyze", json={"run_dir": "../../../etc"})
    assert response.status_code == 400


def test_analyze_returns_404_if_run_dir_missing(app_with_run):
    with TestClient(app_with_run) as client:
        response = client.post("/reports/dry-run/analyze", json={"run_dir": "run_missing"})
    assert response.status_code == 404


def test_response_does_not_leak_credentials(app_with_run, monkeypatch):
    monkeypatch.setenv("KIS_ACCOUNT_NO", "12345678")
    monkeypatch.setenv("KIS_APP_KEY", "fake-key")
    monkeypatch.setenv("KIS_APP_SECRET", "fake-secret")
    with TestClient(app_with_run) as client:
        response = client.post("/reports/dry-run/analyze", json={})
    for needle in ("KIS_APP_KEY", "KIS_APP_SECRET", "12345678", "fake-key", "fake-secret"):
        assert needle not in response.text
