"""Dry-run report analyzer.

Reads dry-run artifacts and produces human-facing analysis files. This module
is read-only with respect to trading runtime state and does not import broker,
settings, or HTTP modules.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator


_FORBIDDEN_KEY_FRAGMENTS = (
    "app_key",
    "appkey",
    "app_secret",
    "appsecret",
    "account_no",
    "accountno",
    "cano",
    "access_token",
    "accesstoken",
    "authorization",
    "secret",
)


class UnsafeReportPayloadError(ValueError):
    """Analyzer output contains a credential-like key name."""


def dump_safe(payload: Any) -> Any:
    """Reject payloads with credential-like dict keys, except secret_exposed."""
    if isinstance(payload, dict):
        for key, value in payload.items():
            normalized = str(key).lower()
            if normalized == "secret_exposed":
                dump_safe(value)
                continue
            for forbidden in _FORBIDDEN_KEY_FRAGMENTS:
                if forbidden in normalized:
                    raise UnsafeReportPayloadError(
                        f"Analyzer output contains forbidden key fragment: {key!r}"
                    )
            dump_safe(value)
    elif isinstance(payload, list):
        for item in payload:
            dump_safe(item)
    return payload


@dataclass
class SymbolStat:
    symbol: str
    seen: int = 0
    passed: int = 0
    blocked: int = 0


@dataclass
class AnalysisResult:
    run_dir: Path
    metadata: dict[str, Any] = field(default_factory=dict)
    counters: dict[str, Any] = field(default_factory=dict)
    top_block_reasons: list[tuple[str, int]] = field(default_factory=list)
    symbols: list[SymbolStat] = field(default_factory=list)
    strategy_pass_rate: float = 0.0
    suggestions: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    invalid_event_lines: int = 0
    orders_count: int = 0


def load_summary(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def load_events(path: Path) -> Iterator[dict[str, Any]]:
    if not path.is_file():
        return
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"__invalid__": True}


def load_orders(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def analyze_run(run_dir: Path, top_n_block_reasons: int = 10) -> AnalysisResult:
    run_dir = Path(run_dir)
    if not run_dir.is_dir():
        raise FileNotFoundError(f"run_dir not found: {run_dir}")

    summary = load_summary(run_dir / "summary.json")
    counters = dict(summary.get("counters", {}))
    metadata = {
        "state": summary.get("state"),
        "started_at": summary.get("started_at"),
        "stopped_at": summary.get("stopped_at"),
        "last_tick_at": summary.get("last_tick_at"),
        "stop_reason": summary.get("stop_reason"),
        "uptime_seconds": summary.get("uptime_seconds"),
        "run_dir": run_dir.name,
    }

    block_reasons: Counter[str] = Counter()
    symbol_stats: dict[str, SymbolStat] = {}
    invalid_lines = 0

    for event in load_events(run_dir / "events.jsonl"):
        if event.get("__invalid__"):
            invalid_lines += 1
            continue
        if event.get("type") != "tick_result":
            continue
        symbol = str(event.get("symbol") or "<unknown>")
        stat = symbol_stats.setdefault(symbol, SymbolStat(symbol=symbol))
        stat.seen += 1
        if event.get("passed"):
            stat.passed += 1
        else:
            stat.blocked += 1
            for blocker in event.get("blockers") or ():
                block_reasons[str(blocker)] += 1

    seen = sum(stat.seen for stat in symbol_stats.values())
    passed = sum(stat.passed for stat in symbol_stats.values())
    pass_rate = (passed / seen) if seen > 0 else 0.0

    result = AnalysisResult(
        run_dir=run_dir,
        metadata=metadata,
        counters=counters,
        top_block_reasons=block_reasons.most_common(top_n_block_reasons),
        symbols=sorted(symbol_stats.values(), key=lambda stat: (-stat.seen, stat.symbol)),
        strategy_pass_rate=round(pass_rate, 4),
        invalid_event_lines=invalid_lines,
        orders_count=len(load_orders(run_dir / "orders.csv")),
    )
    result.suggestions = compute_suggestions(result)
    result.warnings = compute_warnings(result)
    return result


def compute_suggestions(result: AnalysisResult) -> list[str]:
    suggestions: list[str] = []
    counters = result.counters
    blocked = int(counters.get("candidates_blocked", 0) or 0)
    seen = int(counters.get("candidates_seen", 0) or 0)
    spread = int(counters.get("spread_rejections", 0) or 0)
    stale = int(counters.get("stale_quote_rejections", 0) or 0)
    market = int(counters.get("market_order_rejections", 0) or 0)
    oms = int(counters.get("oms_rejections", 0) or 0)
    passed_risk = int(counters.get("candidates_passed_risk", 0) or 0)

    if seen == 0:
        suggestions.append("후보 데이터 0 - 더 많은 tick 또는 더 다양한 snapshot 입력이 필요합니다.")
        return suggestions
    if blocked > 0 and spread / max(1, blocked) > 0.3:
        suggestions.append("스프레드 차단 비율이 높습니다 - 스프레드 허용 범위를 재검토하세요.")
    if blocked > 0 and stale / max(1, blocked) > 0.3:
        suggestions.append("stale quote 차단이 잦습니다 - 시세 데이터 신선도/타임아웃을 검토하세요.")
    if market > 0:
        suggestions.append("시장가 주문 시도가 감지되었습니다 - 전략 코드의 order_type 분기를 점검하세요.")
    if passed_risk > 0 and oms / max(1, passed_risk) > 0.5:
        suggestions.append("OMS 거절 비율이 높습니다 - 허용 심볼/노션 한도/RiskEngine 한도를 재검토하세요.")
    if seen > 0 and passed_risk == 0:
        suggestions.append("RiskEngine을 통과한 후보가 0 - 전략이 너무 보수적이거나 RiskEngine 한도가 너무 빡빡합니다.")
    if seen > 0 and result.strategy_pass_rate < 0.05:
        suggestions.append(f"전략 pass rate({result.strategy_pass_rate:.2%})가 매우 낮습니다 - 전략 임계값 완화를 고려하세요.")
    if not suggestions:
        suggestions.append("현재 데이터로는 즉시 권장할 변경이 없습니다.")
    return suggestions


def compute_warnings(result: AnalysisResult) -> list[str]:
    warnings: list[str] = []
    counters = result.counters
    if int(counters.get("errors_total", 0) or 0) > 0:
        warnings.append(f"errors_total={counters.get('errors_total')} - last_error={counters.get('last_error')}")
    if int(counters.get("kis_fail_closed_count", 0) or 0) > 0:
        warnings.append("KIS fail-closed 감지 - KIS HTTP 미구현 또는 NotImplementedError 발생.")
    if int(counters.get("kill_switch_blocked_ticks", 0) or 0) > 0:
        warnings.append("kill switch로 차단된 tick이 있습니다.")
    if result.invalid_event_lines > 0:
        warnings.append(f"events.jsonl에 invalid JSON {result.invalid_event_lines}건 - 파일 손상 또는 동시 쓰기 가능성.")
    return warnings


def find_latest_run_dir(reports_dir: Path) -> Path | None:
    if not reports_dir.is_dir():
        return None
    candidates = sorted(
        path for path in reports_dir.iterdir() if path.is_dir() and path.name.startswith("run_")
    )
    return candidates[-1] if candidates else None


def write_analysis_files(result: AnalysisResult) -> dict[str, Path]:
    from app.reports.render import render_analysis_report, render_claude_review_input

    run_dir = result.run_dir
    summary_payload = {
        "metadata": result.metadata,
        "counters": dict(result.counters),
        "top_block_reasons": [
            {"reason": reason, "count": count} for reason, count in result.top_block_reasons
        ],
        "symbols": [
            {"symbol": stat.symbol, "seen": stat.seen, "passed": stat.passed, "blocked": stat.blocked}
            for stat in result.symbols
        ],
        "strategy_pass_rate": result.strategy_pass_rate,
        "orders_count": result.orders_count,
        "suggestions": list(result.suggestions),
        "warnings": list(result.warnings),
        "invalid_event_lines": result.invalid_event_lines,
        "secret_exposed": False,
    }
    dump_safe(summary_payload)
    paths = {
        "summary": run_dir / "analysis_summary.json",
        "report": run_dir / "analysis_report.md",
        "review_input": run_dir / "claude_review_input.md",
    }
    paths["summary"].write_text(
        json.dumps(summary_payload, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    paths["report"].write_text(render_analysis_report(result), encoding="utf-8")
    paths["review_input"].write_text(render_claude_review_input(result), encoding="utf-8")
    return paths
