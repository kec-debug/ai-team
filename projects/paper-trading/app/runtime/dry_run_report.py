"""Dry-run report file writers.

Callers must pre-sanitize dicts; dump_safe() catches obvious credential key
names as a defense-in-depth layer before anything is written.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any


_FORBIDDEN_KEY_FRAGMENTS = (
    "app_key",
    "appkey",
    "appsecret",
    "app_secret",
    "account_no",
    "accountno",
    "cano",
    "access_token",
    "accesstoken",
    "authorization",
    "secret",
)


class UnsafeReportPayloadError(ValueError):
    """A report payload contains a credential-like key name."""


def dump_safe(payload: Any) -> Any:
    """Reject payloads containing credential-like dict keys."""
    if isinstance(payload, dict):
        for key, value in payload.items():
            normalized = str(key).lower()
            if normalized == "secret_exposed":
                dump_safe(value)
                continue
            for forbidden in _FORBIDDEN_KEY_FRAGMENTS:
                if forbidden in normalized:
                    raise UnsafeReportPayloadError(
                        f"Report payload contains forbidden key fragment: {key!r}"
                    )
            dump_safe(value)
    elif isinstance(payload, list):
        for item in payload:
            dump_safe(item)
    return payload


def make_run_dir(base_dir: Path, started_at: datetime) -> Path:
    safe_ts = started_at.strftime("%Y-%m-%dT%H-%M-%S")
    run_dir = base_dir / f"run_{safe_ts}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def append_event(run_dir: Path, event: dict[str, Any]) -> None:
    dump_safe(event)
    events_path = run_dir / "events.jsonl"
    with events_path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")


def write_summary(run_dir: Path, summary: dict[str, Any]) -> None:
    dump_safe(summary)
    summary_path = run_dir / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )


_ORDER_COLUMNS = (
    "ts",
    "symbol",
    "side",
    "quantity",
    "limit_price",
    "order_type",
    "oms_status",
    "broker_environment",
    "idempotency_key",
)


def append_order(run_dir: Path, order: dict[str, Any]) -> None:
    dump_safe(order)
    orders_path = run_dir / "orders.csv"
    header_needed = not orders_path.exists()
    with orders_path.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_ORDER_COLUMNS, extrasaction="ignore")
        if header_needed:
            writer.writeheader()
        writer.writerow({key: order.get(key, "") for key in _ORDER_COLUMNS})
