"""KIS raw quote to domain Quote mapper skeleton.

The exact KIS overseas/US-stock quote response field names are not available in
this repository. See docs/kis/MISSING_MARKET_DATA_VALUES.md for required values.
"""

from __future__ import annotations

from typing import Any

from app.domain.quote import Quote


def kis_raw_quote_to_domain(
    raw: dict[str, Any] | None,
    symbol: str,
    source: str = "kis_paper",
) -> Quote:
    """Convert a raw KIS quote response dict into a domain Quote."""
    if raw is None:
        raise ValueError("raw quote payload is None")
    if not symbol:
        raise ValueError("symbol must be non-empty")
    raise NotImplementedError(
        "KIS quote response field mapping is not implemented. "
        "Confirm field names (last/bid/ask/volume/timestamp) from KIS Open API "
        "official documentation and update docs/kis/MISSING_MARKET_DATA_VALUES.md "
        "before wiring this mapper."
    )
