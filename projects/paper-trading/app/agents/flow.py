"""Deterministic market-structure and large-flow analysis helpers.

This module does not infer hidden participants as fact. It scores visible
signals only, and marks missing order-flow inputs as blockers so the UI can
show what is known versus what still needs data.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class FlowSymbolInput(BaseModel):
    symbol: str
    market: str = "US"
    current_price: Decimal | None = None
    vwap: Decimal | None = None
    volume: int | None = Field(default=None, ge=0)
    avg_volume: int | None = Field(default=None, ge=0)
    support_zones: list[Decimal] = []
    resistance_zones: list[Decimal] = []
    foreign_net_buy_value: Decimal | None = None
    institutional_net_buy_value: Decimal | None = None
    large_trade_net_value: Decimal | None = None
    metadata: dict[str, Any] = {}


class FlowAnalysisRequest(BaseModel):
    symbols: list[str] = []
    candidates: list[FlowSymbolInput] = []
    context: dict[str, Any] = {}


class FlowSignal(BaseModel):
    symbol: str
    market: str
    score: float
    confidence: float
    volume_profile_score: float
    pullback_score: float
    accumulation_score: float
    whale_flow_score: float
    support_zones: list[str]
    resistance_zones: list[str]
    reasons: list[str]
    blockers: list[str]
    metadata: dict[str, Any]
    analyzed_at: datetime


class FlowAnalysisResponse(BaseModel):
    provider_used: str = "deterministic_flow_scorer"
    status: str = "completed"
    analysis_count: int
    signals: list[FlowSignal]
    top_symbols: list[str]
    blockers: list[str]
    secret_exposed: bool = False


def _score_to_unit(value: Decimal, scale: Decimal) -> float:
    if scale <= 0:
        return 0.0
    ratio = max(Decimal("-1"), min(Decimal("1"), value / scale))
    return float((ratio + Decimal("1")) / Decimal("2"))


def _fmt(values: list[Decimal]) -> list[str]:
    return [format(value, "f") for value in values]


def analyze_flow(payload: FlowAnalysisRequest, default_symbols: list[str]) -> FlowAnalysisResponse:
    inputs = list(payload.candidates)
    seen = {candidate.symbol.strip().upper() for candidate in inputs}
    fallback_symbols = [] if inputs else default_symbols
    for symbol in payload.symbols or fallback_symbols:
        normalized = symbol.strip().upper()
        if normalized and normalized not in seen:
            inputs.append(FlowSymbolInput(symbol=normalized))
            seen.add(normalized)

    signals = [_analyze_one(candidate) for candidate in inputs[:20]]
    top = [
        signal.symbol
        for signal in sorted(signals, key=lambda item: (item.score, item.confidence), reverse=True)
        if signal.confidence > 0
    ][:5]
    blockers = sorted({blocker for signal in signals for blocker in signal.blockers})
    return FlowAnalysisResponse(
        analysis_count=len(signals),
        signals=signals,
        top_symbols=top,
        blockers=blockers,
    )


def _analyze_one(candidate: FlowSymbolInput) -> FlowSignal:
    symbol = candidate.symbol.strip().upper()
    blockers: list[str] = []
    reasons: list[str] = []

    volume_profile_score = 0.0
    if candidate.volume is None or candidate.avg_volume in (None, 0):
        blockers.append("volume_profile_requires_volume_and_average_volume")
    else:
        ratio = Decimal(candidate.volume) / Decimal(candidate.avg_volume)
        volume_profile_score = float(min(Decimal("1"), ratio / Decimal("3")))
        if ratio >= Decimal("1.5"):
            reasons.append("relative_volume_above_baseline")

    pullback_score = 0.0
    if candidate.current_price is None or candidate.vwap is None:
        blockers.append("pullback_requires_current_price_and_vwap")
    else:
        distance = abs(candidate.current_price - candidate.vwap)
        denominator = max(abs(candidate.vwap), Decimal("1"))
        pullback_score = float(max(Decimal("0"), Decimal("1") - (distance / denominator) * Decimal("20")))
        if candidate.current_price >= candidate.vwap:
            reasons.append("price_holding_near_or_above_vwap")

    accumulation_score = 0.0
    flow_inputs = [
        candidate.foreign_net_buy_value,
        candidate.institutional_net_buy_value,
        candidate.large_trade_net_value,
    ]
    if all(value is None for value in flow_inputs):
        blockers.append("accumulation_requires_foreign_institution_or_large_trade_flow")
    else:
        total = sum((value or Decimal("0")) for value in flow_inputs)
        accumulation_score = _score_to_unit(total, Decimal("1000000"))
        if total > 0:
            reasons.append("net_buy_flow_positive")
        elif total < 0:
            blockers.append("net_buy_flow_negative")

    whale_flow_score = 0.0
    if candidate.large_trade_net_value is None:
        blockers.append("whale_flow_requires_large_trade_net_value")
    else:
        whale_flow_score = _score_to_unit(candidate.large_trade_net_value, Decimal("500000"))
        if candidate.large_trade_net_value > 0:
            reasons.append("large_trade_net_buy_positive")

    score = round(
        volume_profile_score * 0.25
        + pullback_score * 0.25
        + accumulation_score * 0.30
        + whale_flow_score * 0.20,
        4,
    )
    available_groups = sum(
        1
        for available in (
            candidate.volume is not None and candidate.avg_volume not in (None, 0),
            candidate.current_price is not None and candidate.vwap is not None,
            any(value is not None for value in flow_inputs),
            candidate.large_trade_net_value is not None,
        )
        if available
    )
    confidence = round(available_groups / 4, 4)
    if not reasons:
        reasons.append("visible_flow_data_insufficient_for_positive_signal")

    return FlowSignal(
        symbol=symbol,
        market=candidate.market.strip().upper() or "US",
        score=score,
        confidence=confidence,
        volume_profile_score=round(volume_profile_score, 4),
        pullback_score=round(pullback_score, 4),
        accumulation_score=round(accumulation_score, 4),
        whale_flow_score=round(whale_flow_score, 4),
        support_zones=_fmt(candidate.support_zones),
        resistance_zones=_fmt(candidate.resistance_zones),
        reasons=reasons,
        blockers=blockers,
        metadata={
            **candidate.metadata,
            "analysis_boundary": "visible_market_data_only",
            "no_hidden_actor_claim": True,
        },
        analyzed_at=datetime.now(timezone.utc),
    )
