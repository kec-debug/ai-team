import json
from pathlib import Path

import pytest

from app.reports.dry_run_analyzer import (
    UnsafeReportPayloadError,
    analyze_run,
    dump_safe,
    find_latest_run_dir,
    write_analysis_files,
)


@pytest.fixture
def empty_run_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run_2026-05-14T08-00-00"
    run_dir.mkdir()
    return run_dir


@pytest.fixture
def populated_run_dir(tmp_path: Path) -> Path:
    run_dir = tmp_path / "run_2026-05-14T08-00-00"
    run_dir.mkdir()
    summary = {
        "state": "stopped",
        "started_at": "2026-05-14T08:00:00+00:00",
        "stopped_at": "2026-05-14T08:30:00+00:00",
        "uptime_seconds": 1800,
        "counters": {
            "ticks_total": 30,
            "candidates_seen": 100,
            "candidates_blocked": 70,
            "candidates_passed_risk": 30,
            "dry_run_orders_created": 25,
            "dry_run_orders_rejected": 5,
            "risk_rejections": 8,
            "oms_rejections": 5,
            "stale_quote_rejections": 30,
            "spread_rejections": 25,
            "market_order_rejections": 0,
            "kis_fail_closed_count": 0,
            "errors_total": 0,
            "last_error": None,
            "kill_switch_blocked_ticks": 0,
        },
    }
    (run_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    events = [
        {"ts": "2026-05-14T08:00:01+00:00", "type": "tick_result", "symbol": "AAPL", "passed": True, "blockers": []},
        {"ts": "2026-05-14T08:00:02+00:00", "type": "tick_result", "symbol": "AAPL", "passed": False, "blockers": ["spread_too_wide"]},
        {"ts": "2026-05-14T08:00:03+00:00", "type": "tick_result", "symbol": "MSFT", "passed": False, "blockers": ["stale_quote", "spread_too_wide"]},
        {"ts": "2026-05-14T08:00:04+00:00", "type": "tick_blocked", "reason": "kill_switch_engaged", "snapshots": 1},
    ]
    (run_dir / "events.jsonl").write_text(
        "\n".join(json.dumps(event) for event in events) + "\n",
        encoding="utf-8",
    )
    (run_dir / "orders.csv").write_text("ts,symbol,oms_status\n1,AAPL,accepted\n", encoding="utf-8")
    return run_dir


def test_analyze_empty_run(empty_run_dir):
    result = analyze_run(empty_run_dir)
    assert result.counters == {}
    assert result.top_block_reasons == []
    assert result.symbols == []
    assert result.strategy_pass_rate == 0.0
    assert "후보 데이터 0" in result.suggestions[0]


def test_analyze_populated_run(populated_run_dir):
    result = analyze_run(populated_run_dir)
    assert result.counters["candidates_seen"] == 100
    assert result.counters["candidates_blocked"] == 70
    symbols = {stat.symbol: stat for stat in result.symbols}
    assert symbols["AAPL"].seen == 2
    assert symbols["AAPL"].passed == 1
    assert symbols["AAPL"].blocked == 1
    assert symbols["MSFT"].seen == 1
    assert symbols["MSFT"].blocked == 1
    reasons = dict(result.top_block_reasons)
    assert reasons["spread_too_wide"] == 2
    assert reasons["stale_quote"] == 1
    assert abs(result.strategy_pass_rate - (1 / 3)) < 1e-3
    assert result.orders_count == 1


def test_invalid_event_lines_counted(tmp_path):
    run_dir = tmp_path / "run_2026-05-14T08-00-00"
    run_dir.mkdir()
    (run_dir / "events.jsonl").write_text(
        'not-json\n{"type":"tick_result","symbol":"AAPL","passed":true}\n',
        encoding="utf-8",
    )
    result = analyze_run(run_dir)
    assert result.invalid_event_lines == 1


def test_dump_safe_blocks_app_secret():
    with pytest.raises(UnsafeReportPayloadError):
        dump_safe({"app_secret": "x"})


def test_dump_safe_allows_secret_exposed_flag():
    assert dump_safe({"secret_exposed": False}) == {"secret_exposed": False}


def test_dump_safe_blocks_nested_account_no():
    with pytest.raises(UnsafeReportPayloadError):
        dump_safe({"data": {"account_no": "12345678"}})


def test_compute_suggestions_high_spread_and_stale(populated_run_dir):
    result = analyze_run(populated_run_dir)
    text = " ".join(result.suggestions)
    assert "스프레드" in text
    assert "stale quote" in text


def test_write_analysis_files_creates_three_outputs(populated_run_dir):
    result = analyze_run(populated_run_dir)
    paths = write_analysis_files(result)
    assert paths["summary"].is_file()
    assert paths["report"].is_file()
    assert paths["review_input"].is_file()
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    assert summary["secret_exposed"] is False
    assert summary["strategy_pass_rate"] >= 0


def test_outputs_do_not_leak_fake_credentials(populated_run_dir):
    result = analyze_run(populated_run_dir)
    paths = write_analysis_files(result)
    for path in paths.values():
        text = path.read_text(encoding="utf-8")
        for forbidden in ("KIS_APP_KEY", "KIS_APP_SECRET", "12345678", "fake-key", "fake-secret"):
            assert forbidden not in text


def test_find_latest_run_dir(tmp_path):
    base = tmp_path / "reports" / "dry_run"
    base.mkdir(parents=True)
    (base / "run_2026-05-14T08-00-00").mkdir()
    (base / "run_2026-05-14T09-00-00").mkdir()
    latest = find_latest_run_dir(base)
    assert latest is not None
    assert latest.name == "run_2026-05-14T09-00-00"


def test_find_latest_returns_none_when_empty(tmp_path):
    assert find_latest_run_dir(tmp_path / "missing") is None
