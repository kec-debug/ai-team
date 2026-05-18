"""Markdown rendering for dry-run analysis."""

from __future__ import annotations

from app.reports.dry_run_analyzer import AnalysisResult


def render_analysis_report(result: AnalysisResult) -> str:
    lines: list[str] = []
    metadata = result.metadata
    lines.append(f"# Dry-run Analysis Report - {metadata.get('run_dir', '<unknown>')}")
    lines.append("")
    lines.append(f"- state: `{metadata.get('state')}`")
    lines.append(f"- started_at: `{metadata.get('started_at')}`")
    lines.append(f"- stopped_at: `{metadata.get('stopped_at')}`")
    lines.append(f"- last_tick_at: `{metadata.get('last_tick_at')}`")
    lines.append(f"- stop_reason: `{metadata.get('stop_reason')}`")
    lines.append(f"- uptime_seconds: {metadata.get('uptime_seconds')}")
    lines.append(f"- strategy_pass_rate: {result.strategy_pass_rate:.2%}")
    lines.append("")
    lines.append("## Counters")
    for key, value in sorted(result.counters.items()):
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Top Block Reasons")
    if not result.top_block_reasons:
        lines.append("- (none)")
    else:
        for reason, count in result.top_block_reasons:
            lines.append(f"- {reason}: {count}")
    lines.append("")
    lines.append("## Symbols")
    if not result.symbols:
        lines.append("- (none)")
    else:
        lines.append("| symbol | seen | passed | blocked |")
        lines.append("| --- | --- | --- | --- |")
        for stat in result.symbols:
            lines.append(f"| {stat.symbol} | {stat.seen} | {stat.passed} | {stat.blocked} |")
    lines.append("")
    lines.append("## Warnings")
    if not result.warnings:
        lines.append("- (none)")
    else:
        for warning in result.warnings:
            lines.append(f"- {warning}")
    lines.append("")
    lines.append("## Suggestions")
    for suggestion in result.suggestions:
        lines.append(f"- {suggestion}")
    lines.append("")
    lines.append("---")
    lines.append(
        "이 리포트는 자동 분석 결과입니다. LLM/Agent는 본 리포트를 기반으로 직접 주문을 결정하지 않습니다. 모든 전략 변경은 사람이 검토합니다."
    )
    return "\n".join(lines) + "\n"


def render_claude_review_input(result: AnalysisResult) -> str:
    """Structured input for Claude/Codex strategy improvement review."""
    metadata = result.metadata
    counters = result.counters
    lines: list[str] = []
    lines.append("# Claude/Codex Review Input - Strategy Improvement")
    lines.append("")
    lines.append("## Scope")
    lines.append("- 본 문서는 dry-run 결과 분석을 기반으로 한 사람용 검토 자료입니다.")
    lines.append("- LLM/Agent가 본 문서를 읽어도 직접 주문을 만들거나 KIS를 직접 호출하지 않습니다.")
    lines.append("- 모든 전략 변경은 사람이 plan/codex-task를 작성한 뒤 별도 mvp로 진행됩니다.")
    lines.append("")
    lines.append("## Run Metadata")
    lines.append(f"- run_dir: `{metadata.get('run_dir')}`")
    lines.append(f"- state: `{metadata.get('state')}`")
    lines.append(f"- started_at: `{metadata.get('started_at')}`")
    lines.append(f"- stopped_at: `{metadata.get('stopped_at')}`")
    lines.append(f"- uptime_seconds: {metadata.get('uptime_seconds')}")
    lines.append(f"- stop_reason: `{metadata.get('stop_reason')}`")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- ticks_total: {counters.get('ticks_total', 0)}")
    lines.append(f"- candidates_seen: {counters.get('candidates_seen', 0)}")
    lines.append(f"- candidates_passed_risk: {counters.get('candidates_passed_risk', 0)}")
    lines.append(f"- candidates_blocked: {counters.get('candidates_blocked', 0)}")
    lines.append(f"- dry_run_orders_created: {counters.get('dry_run_orders_created', 0)}")
    lines.append(f"- dry_run_orders_rejected: {counters.get('dry_run_orders_rejected', 0)}")
    lines.append(f"- strategy_pass_rate: {result.strategy_pass_rate:.2%}")
    lines.append("")
    lines.append("## Top Block Reasons")
    if not result.top_block_reasons:
        lines.append("- (none)")
    else:
        for reason, count in result.top_block_reasons:
            lines.append(f"- {reason}: {count}")
    lines.append("")
    lines.append("## Warnings")
    if not result.warnings:
        lines.append("- (none)")
    else:
        for warning in result.warnings:
            lines.append(f"- {warning}")
    lines.append("")
    lines.append("## Suggestions (heuristic - human must validate)")
    for suggestion in result.suggestions:
        lines.append(f"- {suggestion}")
    lines.append("")
    lines.append("## Safety Reminders")
    lines.append("- live trading 비활성 유지.")
    lines.append("- KIS_ORDER_DRY_RUN=true 기본값 유지.")
    lines.append("- 시장가 주문 금지.")
    lines.append("- Strategy/Agent/LLM이 KIS 직접 호출 금지.")
    lines.append("- OMS/RiskEngine 우회 금지.")
    lines.append("- KIS endpoint/TR ID/payload 추측 금지.")
    lines.append("")
    lines.append("## Next Step Hints")
    lines.append("- 전략 임계값 조정이 필요하다고 판단되면, plan/codex-task를 작성한 뒤 별도 mvp로 진행하세요.")
    lines.append("- `app/strategy/premarket_gap.py`와 `app/config.py`의 `STRATEGY_PREMARKET_*` 환경변수가 주된 튜닝 지점입니다.")
    lines.append("- 실제 HTTP 연결은 `docs/kis/MISSING_OFFICIAL_VALUES.md`의 항목이 `Confirmed: yes`로 채워진 뒤에만 별도 mvp로 진행합니다.")
    return "\n".join(lines) + "\n"
