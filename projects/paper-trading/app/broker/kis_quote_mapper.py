"""Map confirmed KIS overseas current-price responses into domain quotes."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from app.domain.enums import Session
from app.domain.quote import Quote


def _decimal_field(value: Any, field_name: str) -> Decimal:
    if value is None or value == "":
        raise ValueError(f"malformed_response: {field_name} missing")
    try:
        return Decimal(str(value).replace(",", ""))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"malformed_response: {field_name} invalid") from exc


def kis_raw_quote_to_domain(
    raw: dict[str, Any] | None,
    symbol: str,
    *,
    received_at: datetime,
    source: str = "kis_paper",
    currency: str = "USD",
    session: Session | None = None,
) -> Quote:
    """Convert a confirmed KIS overseas current-price response into ``Quote``."""
    if raw is None:
        raise ValueError("raw quote payload is None")
    if not isinstance(raw, dict):
        raise ValueError("malformed_response: raw is not dict")
    symbol_upper = symbol.strip().upper()
    if not symbol_upper:
        raise ValueError("symbol must be non-empty")
    if received_at.tzinfo is None:
        raise ValueError("received_at must be timezone-aware")

    rt_cd = raw.get("rt_cd")
    if rt_cd not in (None, "0"):
        code = raw.get("msg_cd") or raw.get("msg1") or "unknown"
        raise ValueError(f"kis_error:{code}")

    output = raw.get("output")
    if not isinstance(output, dict):
        raise ValueError("malformed_response: output missing")

    last = _decimal_field(output.get("last"), "last")
    if last <= 0:
        raise ValueError("malformed_response: last not positive")

    volume_decimal = _decimal_field(output.get("tvol"), "tvol")
    volume = int(volume_decimal)
    if volume < 0:
        raise ValueError("malformed_response: volume negative")

    return Quote(
        symbol=symbol_upper,
        last=last,
        bid=last,
        ask=last,
        volume=volume,
        timestamp=received_at,
        source=source,
        session=session,
        currency=currency,
        bid_ask_present=False,
    )
