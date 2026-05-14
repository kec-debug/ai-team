import json
from datetime import datetime, timezone

import pytest

from app.runtime.dry_run_report import (
    UnsafeReportPayloadError,
    append_event,
    append_order,
    dump_safe,
    make_run_dir,
    write_summary,
)


def test_dump_safe_rejects_app_key_key():
    with pytest.raises(UnsafeReportPayloadError):
        dump_safe({"app_key": "x"})


def test_dump_safe_rejects_nested_secret():
    with pytest.raises(UnsafeReportPayloadError):
        dump_safe({"outer": {"app_secret": "x"}})


def test_dump_safe_allows_safe_dict():
    assert dump_safe({"symbol": "AAPL", "status": "ok"}) == {"symbol": "AAPL", "status": "ok"}


def test_make_run_dir_is_deterministic_per_timestamp(tmp_path):
    ts = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
    first = make_run_dir(tmp_path, ts)
    second = make_run_dir(tmp_path, ts)
    assert first == second
    assert first.is_dir()
    assert first.name == "run_2026-01-02T03-04-05"


def test_append_event_writes_jsonl_line(tmp_path):
    append_event(tmp_path, {"type": "tick", "symbol": "AAPL"})
    lines = (tmp_path / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["symbol"] == "AAPL"


def test_append_event_blocks_secret_payload(tmp_path):
    with pytest.raises(UnsafeReportPayloadError):
        append_event(tmp_path, {"access_token": "x"})


def test_write_summary_overwrites(tmp_path):
    write_summary(tmp_path, {"state": "running"})
    write_summary(tmp_path, {"state": "stopped"})
    data = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    assert data == {"state": "stopped"}


def test_append_order_creates_header_then_appends(tmp_path):
    append_order(tmp_path, {"ts": "1", "symbol": "AAPL", "oms_status": "accepted"})
    append_order(tmp_path, {"ts": "2", "symbol": "MSFT", "oms_status": "accepted"})
    lines = (tmp_path / "orders.csv").read_text(encoding="utf-8").splitlines()
    assert lines[0].startswith("ts,symbol,side,quantity")
    assert len(lines) == 3
    assert "AAPL" in lines[1]
    assert "MSFT" in lines[2]
