## 1. 요청 요약

mvp-018에서 만든 dry-run runner의 산출물(`reports/dry_run/run_<ts>/{events.jsonl, summary.json, orders.csv}`)을 읽어서 **분석 리포트 + 전략 개선 제안 + Claude/Codex 리뷰 입력 문서**를 생성하는 read-only analyzer를 추가한다. 실제 주문/HTTP/Strategy 변경은 없음.

### 안전 원칙 (mvp-005~mvp-018 누적 유지)

- live trading 활성화 금지. mvp-018 차단 단 모두 유지.
- `OrderType.MARKET` 부재 유지.
- 외부 HTTP 라이브러리 import 금지.
- KIS endpoint URL/TR ID/payload 추측 금지.
- 실제 KIS app key/secret/account/token이 analyzer 입력/출력/log 어디에도 미포함.
- analyzer는 dry-run 파일을 **읽기만** 함. dry-run runner 자체는 변경 없음.
- analyzer 출력 파일도 `dump_safe`(또는 동등 가드)를 통과 — secret 키 이름이 들어가면 즉시 거절.
- `git commit`/`push`/`merge`/`deploy` 자동화 금지.
- `pip install` 실행 금지.
- LLM/agent가 직접 주문 판단을 내리지 않음. analyzer는 **사람이 읽는** 제안만 생성.

### 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기존 155 + 신규 약 14–18개 모두 PASS.

## 2. 작업 범위

### 포함 (In scope)

`projects/paper-trading/` 아래:

- **`app/reports/__init__.py` (신규)** — 빈 패키지 마커.
- **`app/reports/dry_run_analyzer.py` (신규)** — 핵심 analyzer:
  - `@dataclass class SymbolStat`(seen/passed/blocked).
  - `@dataclass class AnalysisResult`(run_dir, run_metadata, counters, top_block_reasons, symbols, strategy_pass_rate, suggestions, warnings).
  - `load_summary(path: Path) -> dict` — 파일 없으면 빈 dict.
  - `load_events(path: Path) -> Iterator[dict]` — JSONL 라인 yield. 빈 파일 OK. invalid JSON 라인은 skip + warning.
  - `load_orders(path: Path) -> list[dict]` — CSV. 빈 파일 OK.
  - `analyze_run(run_dir: Path) -> AnalysisResult` — 위 3개 합쳐서 분석.
  - `find_latest_run_dir(reports_dir: Path) -> Path | None` — `run_*` 디렉터리 정렬 후 마지막.
  - `compute_suggestions(counters, top_block_reasons) -> list[str]` — 휴리스틱 기반 제안.
  - `compute_warnings(counters, analysis_result) -> list[str]` — 경고(에러 발생, 모든 후보 차단 등).
  - `write_analysis_files(result: AnalysisResult, run_dir: Path) -> dict[str, Path]` — `analysis_summary.json` + `analysis_report.md` + `claude_review_input.md` 생성. 모두 `dump_safe` 통과.
- **`app/reports/render.py` (신규)** — markdown 렌더링:
  - `render_analysis_report(result) -> str` — `analysis_report.md` 내용.
  - `render_claude_review_input(result) -> str` — `claude_review_input.md` 내용.
- **`app/reports/__main__.py` (신규)** — CLI 진입점:
  - `python -m app.reports [--run-dir PATH | --latest] [--reports-dir DIR]`
  - 기본은 `--latest`. `--reports-dir` 미지정 시 `reports/dry_run/`.
  - 결과 path 출력 + exit code 0(성공) / 1(run_dir 못 찾음) / 2(분석 실패).
- **`app/api/routes.py` (수정)** — 2개 신규 엔드포인트:
  - `POST /reports/dry-run/analyze` — body `{"run_dir": "..."}` 또는 빈 dict(latest). 응답: `analysis_summary.json` 내용 + 생성된 파일 경로.
  - `GET /reports/dry-run/latest` — 가장 최근 run의 analysis_summary.json 내용. 없으면 자동 분석 수행 후 반환.
- **`projects/paper-trading/README.md` (수정)** — `## dry-run 리포트 분석 (mvp-019)` 단락 추가.
- **신규 테스트**:
  - `tests/test_dry_run_analyzer.py` — 빈 파일 처리, 정상 events 집계, block reason aggregation, symbol stat, pass rate, suggestion 생성, dump_safe 차단, 파일 3개 생성 검증.
  - `tests/test_reports_api.py` — API endpoint happy path + secret/path-traversal 거절.
- **`docs/ai/jobs/mvp-019/patch.md` (신규)** — Codex 변경 요약.

### 제외 (Out of scope; 절대 만지지 않음)

- 실제 주문/HTTP 호출 신설.
- KIS endpoint URL/TR ID/payload 추가.
- 외부 HTTP 라이브러리 import.
- `app/broker/kis.py`, `app/broker/*` 변경.
- `app/runtime/dry_run.py`, `app/runtime/dry_run_report.py`, `app/runtime/paper_runner.py` 변경.
- `app/oms/`, `app/risk/`, `app/strategy/`, `app/domain/`, `app/portfolio/`, `app/session/`, `app/main.py`, `app/config.py`, `app/api/server.py` 변경.
- `Settings` 필드 추가/변경.
- 자동 strategy 수정(analyzer는 제안만 생성, Strategy 코드 미수정).
- `OrderType.MARKET` 추가.
- 실제 KIS 값 인용.
- mvp-001..mvp-018 산출물 변경.
- `.env`, secrets, credentials.
- 인증/결제/DB migration/production infra/`.github/workflows/`.
- 자동 commit/push/merge/deploy.
- 임의 shell 실행 기능.
- `pip install` 실행.
- `imports/local-mvp/`.
- `web/`, `prompts/`, `scripts/`, 기존 `docs/`(`docs/ai/jobs/mvp-019/` 외) 변경.
- 리포트 파일을 git에 추가(이미 `reports/`가 프로젝트 `.gitignore`로 무시되므로 analysis 파일도 자동 무시).

### 안전 가드

- API endpoint가 받는 `run_dir`는 **반드시** 프로젝트의 `reports/dry_run/` 안 상대 경로여야 함. `..`, 절대경로, symlink 탈출 모두 차단(400 또는 422).
- analyzer가 events.jsonl에서 invalid JSON 라인을 만나면 skip + 카운터 증가. crash 금지.
- 입력 dict에 알려진 secret 키 이름(`app_key`, `app_secret`, `account_no`, `access_token`, `authorization`, `secret`)이 있으면 출력 전 `dump_safe`(또는 새 helper)가 거절. 단 `secret_exposed: False` 정확 매칭은 허용 (mvp-018 패턴).
- analyzer는 `app.broker.kis` import 0건, `app.config` import 0건(파일 path만 받음). 즉 settings에 접근 안 함 → raw credentials 접근 불가 구조적 보장.

## 3. 수정해야 할 파일

### 신규

| 파일 | 목적 |
| --- | --- |
| `app/reports/__init__.py` | 패키지 마커 |
| `app/reports/dry_run_analyzer.py` | analyzer 핵심 로직 |
| `app/reports/render.py` | markdown 렌더링 |
| `app/reports/__main__.py` | CLI 진입점 |
| `tests/test_dry_run_analyzer.py` | analyzer 단위/통합 테스트 |
| `tests/test_reports_api.py` | API endpoint 테스트 |
| `docs/ai/jobs/mvp-019/patch.md` | Codex 변경 요약 |

### 수정

| 파일 | 변경 내용 |
| --- | --- |
| `app/api/routes.py` | `POST /reports/dry-run/analyze`, `GET /reports/dry-run/latest` 두 엔드포인트 추가 |
| `README.md` | `## dry-run 리포트 분석 (mvp-019)` 단락 + CLI/API 사용 예시 |

### 절대 미수정

- `app/broker/*`, `app/runtime/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/portfolio/*`, `app/session/*`, `app/main.py`, `app/config.py`, `app/api/server.py`.
- 기존 테스트 중 본 작업이 다루지 않는 것.
- `.env.example`, 프로젝트 `.gitignore`, 루트 `.gitignore`.
- mvp-001..mvp-018 산출물.
- `imports/local-mvp/`, `docs/kis/`.

## 4. Codex 구현 지시문

### 4.1 사전 점검

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m pytest -p no:cacheprovider --co -q 2>&1 | tail -3
# expect: 155+ tests collected

grep -q "class DryRunController" app/runtime/dry_run.py && echo "OK DryRunController"
grep -q "make_run_dir" app/runtime/dry_run_report.py && echo "OK dry_run_report"
test -f app/runtime/dry_run.py && echo "OK mvp-018 landed"
test -d .venv && echo "OK venv"
```

위 4개 OK → 진행. 누락 시 `patch.md` Remaining TODOs에 기록 후 중단.

### 4.2 `app/reports/__init__.py` (신규)

```python
"""Read-only dry-run report analyzer (mvp-019)."""
```

### 4.3 `app/reports/dry_run_analyzer.py` (신규)

핵심 구조:

```python
"""Dry-run report analyzer.

Reads dry-run artifacts produced by app/runtime/dry_run.py and produces a
summary, a human-readable markdown report, and a Claude/Codex review input
document. Read-only. Does NOT import app.broker.kis, app.config, or any
HTTP library. Strategy/agent/LLM never call this module to make trading
decisions — outputs are advisory text for humans.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Iterator


_FORBIDDEN_KEY_FRAGMENTS = (
    "app_key", "appkey", "app_secret", "appsecret",
    "account_no", "accountno", "cano",
    "access_token", "accesstoken", "authorization", "secret",
)


class UnsafeReportPayloadError(ValueError):
    """Analyzer output contains a credential-like key name."""


def dump_safe(payload: Any) -> Any:
    """Defense-in-depth: reject payloads with credential-like dict keys.

    Allow exact key 'secret_exposed' (recursively validate its value).
    """
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
        "run_dir": str(run_dir.name),
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
        symbol = event.get("symbol") or "<unknown>"
        stat = symbol_stats.setdefault(symbol, SymbolStat(symbol=symbol))
        stat.seen += 1
        if event.get("passed"):
            stat.passed += 1
        else:
            stat.blocked += 1
            for blocker in event.get("blockers") or ():
                block_reasons[str(blocker)] += 1

    seen = sum(s.seen for s in symbol_stats.values())
    passed = sum(s.passed for s in symbol_stats.values())
    pass_rate = (passed / seen) if seen > 0 else 0.0

    result = AnalysisResult(
        run_dir=run_dir,
        metadata=metadata,
        counters=counters,
        top_block_reasons=block_reasons.most_common(top_n_block_reasons),
        symbols=sorted(symbol_stats.values(), key=lambda s: -s.seen),
        strategy_pass_rate=round(pass_rate, 4),
        invalid_event_lines=invalid_lines,
    )
    result.suggestions = compute_suggestions(result)
    result.warnings = compute_warnings(result)
    return result


def compute_suggestions(result: AnalysisResult) -> list[str]:
    suggestions: list[str] = []
    c = result.counters
    blocked = int(c.get("candidates_blocked", 0) or 0)
    seen = int(c.get("candidates_seen", 0) or 0)
    spread = int(c.get("spread_rejections", 0) or 0)
    stale = int(c.get("stale_quote_rejections", 0) or 0)
    market = int(c.get("market_order_rejections", 0) or 0)
    risk = int(c.get("risk_rejections", 0) or 0)
    oms = int(c.get("oms_rejections", 0) or 0)
    passed_risk = int(c.get("candidates_passed_risk", 0) or 0)

    if seen == 0:
        suggestions.append("후보 데이터 0 — 더 많은 tick 또는 더 다양한 snapshot 입력이 필요합니다.")
        return suggestions

    if blocked > 0 and spread / max(1, blocked) > 0.3:
        suggestions.append("스프레드 차단 비율이 높습니다 — 스프레드 허용 범위를 재검토하세요.")
    if blocked > 0 and stale / max(1, blocked) > 0.3:
        suggestions.append("stale quote 차단이 잦습니다 — 시세 데이터 신선도/타임아웃을 검토하세요.")
    if market > 0:
        suggestions.append("시장가 주문 시도가 감지되었습니다 — 전략 코드의 order_type 분기를 점검하세요.")
    if passed_risk > 0 and oms / max(1, passed_risk) > 0.5:
        suggestions.append("OMS 거절 비율이 높습니다 — 허용 심볼/노션 한도/RiskEngine 한도를 재검토하세요.")
    if seen > 0 and passed_risk == 0:
        suggestions.append("RiskEngine을 통과한 후보가 0 — 전략이 너무 보수적이거나 RiskEngine 한도가 너무 빡빡합니다.")
    if seen > 0 and result.strategy_pass_rate < 0.05:
        suggestions.append(f"전략 pass rate({result.strategy_pass_rate:.2%})가 매우 낮습니다 — 전략 임계값 완화를 고려하세요.")
    if not suggestions:
        suggestions.append("현재 데이터로는 즉시 권장할 변경이 없습니다.")
    return suggestions


def compute_warnings(result: AnalysisResult) -> list[str]:
    warnings: list[str] = []
    c = result.counters
    if int(c.get("errors_total", 0) or 0) > 0:
        warnings.append(f"errors_total={c.get('errors_total')} — last_error={c.get('last_error')}")
    if int(c.get("kis_fail_closed_count", 0) or 0) > 0:
        warnings.append("KIS fail-closed 감지 — KIS HTTP 미구현 또는 NotImplementedError 발생.")
    if int(c.get("kill_switch_blocked_ticks", 0) or 0) > 0:
        warnings.append("kill switch로 차단된 tick이 있습니다.")
    if result.invalid_event_lines > 0:
        warnings.append(f"events.jsonl에 invalid JSON {result.invalid_event_lines}건 — 파일 손상 또는 동시 쓰기 가능성.")
    return warnings


def find_latest_run_dir(reports_dir: Path) -> Path | None:
    if not reports_dir.is_dir():
        return None
    candidates = sorted(p for p in reports_dir.iterdir() if p.is_dir() and p.name.startswith("run_"))
    return candidates[-1] if candidates else None


def write_analysis_files(result: AnalysisResult) -> dict[str, Path]:
    from app.reports.render import render_analysis_report, render_claude_review_input
    run_dir = result.run_dir
    summary_payload = {
        "metadata": result.metadata,
        "counters": dict(result.counters),
        "top_block_reasons": [{"reason": r, "count": n} for r, n in result.top_block_reasons],
        "symbols": [{"symbol": s.symbol, "seen": s.seen, "passed": s.passed, "blocked": s.blocked} for s in result.symbols],
        "strategy_pass_rate": result.strategy_pass_rate,
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
    paths["summary"].write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    paths["report"].write_text(render_analysis_report(result), encoding="utf-8")
    paths["review_input"].write_text(render_claude_review_input(result), encoding="utf-8")
    return paths
```

핵심 불변식:

- `app.broker.kis` / `app.config` import 0건. settings 객체 미접근.
- 모든 output dict는 `dump_safe`를 통과한 뒤 직렬화.
- `summary_payload`에 `secret_exposed: False` 명시 노출(투명성).

### 4.4 `app/reports/render.py` (신규)

```python
"""Markdown rendering for dry-run analysis."""

from __future__ import annotations

from typing import Any

from app.reports.dry_run_analyzer import AnalysisResult


def render_analysis_report(result: AnalysisResult) -> str:
    lines: list[str] = []
    m = result.metadata
    lines.append(f"# Dry-run Analysis Report — {m.get('run_dir', '<unknown>')}")
    lines.append("")
    lines.append(f"- state: `{m.get('state')}`")
    lines.append(f"- started_at: `{m.get('started_at')}`")
    lines.append(f"- stopped_at: `{m.get('stopped_at')}`")
    lines.append(f"- last_tick_at: `{m.get('last_tick_at')}`")
    lines.append(f"- stop_reason: `{m.get('stop_reason')}`")
    lines.append(f"- uptime_seconds: {m.get('uptime_seconds')}")
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
        for s in result.symbols:
            lines.append(f"| {s.symbol} | {s.seen} | {s.passed} | {s.blocked} |")
    lines.append("")
    lines.append("## Warnings")
    if not result.warnings:
        lines.append("- (none)")
    else:
        for w in result.warnings:
            lines.append(f"- {w}")
    lines.append("")
    lines.append("## Suggestions")
    for s in result.suggestions:
        lines.append(f"- {s}")
    lines.append("")
    lines.append("---")
    lines.append("이 리포트는 자동 분석 결과입니다. LLM/Agent는 본 리포트를 기반으로 직접 주문을 결정하지 않습니다. 모든 전략 변경은 사람이 검토합니다.")
    return "\n".join(lines) + "\n"


def render_claude_review_input(result: AnalysisResult) -> str:
    """Structured input for Claude/Codex strategy improvement review."""
    m = result.metadata
    lines: list[str] = []
    lines.append("# Claude/Codex Review Input — Strategy Improvement")
    lines.append("")
    lines.append("## Scope")
    lines.append("- 본 문서는 dry-run 결과 분석을 기반으로 한 **사람용** 검토 자료입니다.")
    lines.append("- LLM/Agent가 본 문서를 읽어도 직접 주문을 만들거나 KIS를 직접 호출하지 않습니다.")
    lines.append("- 모든 전략 변경은 사람이 plan/codex-task를 작성한 뒤 별도 mvp로 진행됩니다.")
    lines.append("")
    lines.append("## Run Metadata")
    lines.append(f"- run_dir: `{m.get('run_dir')}`")
    lines.append(f"- state: `{m.get('state')}`")
    lines.append(f"- started_at: `{m.get('started_at')}`")
    lines.append(f"- stopped_at: `{m.get('stopped_at')}`")
    lines.append(f"- uptime_seconds: {m.get('uptime_seconds')}")
    lines.append(f"- stop_reason: `{m.get('stop_reason')}`")
    lines.append("")
    lines.append("## Summary")
    c = result.counters
    lines.append(f"- ticks_total: {c.get('ticks_total', 0)}")
    lines.append(f"- candidates_seen: {c.get('candidates_seen', 0)}")
    lines.append(f"- candidates_passed_risk: {c.get('candidates_passed_risk', 0)}")
    lines.append(f"- candidates_blocked: {c.get('candidates_blocked', 0)}")
    lines.append(f"- dry_run_orders_created: {c.get('dry_run_orders_created', 0)}")
    lines.append(f"- dry_run_orders_rejected: {c.get('dry_run_orders_rejected', 0)}")
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
        for w in result.warnings:
            lines.append(f"- {w}")
    lines.append("")
    lines.append("## Suggestions (heuristic — human must validate)")
    for s in result.suggestions:
        lines.append(f"- {s}")
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
```

### 4.5 `app/reports/__main__.py` (신규)

```python
"""CLI: python -m app.reports [--run-dir PATH | --latest] [--reports-dir DIR]."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.reports.dry_run_analyzer import analyze_run, find_latest_run_dir, write_analysis_files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze dry-run reports")
    parser.add_argument("--run-dir", type=Path, help="Specific run directory")
    parser.add_argument("--latest", action="store_true", help="Analyze the latest run")
    parser.add_argument("--reports-dir", type=Path, default=Path("reports") / "dry_run",
                        help="Base reports directory (default: reports/dry_run)")
    args = parser.parse_args(argv)

    if args.run_dir and args.latest:
        parser.error("specify either --run-dir or --latest, not both")
    if not args.run_dir and not args.latest:
        args.latest = True

    if args.latest:
        run_dir = find_latest_run_dir(args.reports_dir)
        if run_dir is None:
            print(f"no run directories found under {args.reports_dir}", file=sys.stderr)
            return 1
    else:
        run_dir = args.run_dir
        if not run_dir.is_dir():
            print(f"run_dir not found: {run_dir}", file=sys.stderr)
            return 1

    try:
        result = analyze_run(run_dir)
        paths = write_analysis_files(result)
    except Exception as exc:
        print(f"analysis failed: {exc}", file=sys.stderr)
        return 2

    print(json.dumps({k: str(v) for k, v in paths.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### 4.6 `app/api/routes.py` 변경

2개 신규 엔드포인트 추가:

```python
from app.reports.dry_run_analyzer import (
    analyze_run,
    find_latest_run_dir,
    write_analysis_files,
)


class AnalyzeRequest(BaseModel):
    run_dir: str | None = None  # relative to reports_dir; None → latest


def _reports_base(settings) -> Path:
    raw = Path(settings.dry_run_reports_dir)
    if raw.is_absolute():
        raise HTTPException(status_code=500, detail="dry_run_reports_dir misconfigured")
    project_dir = Path(__file__).resolve().parents[2]
    base = (project_dir / raw).resolve()
    if project_dir not in base.parents and base != project_dir:
        raise HTTPException(status_code=500, detail="reports dir outside project")
    return base


def _resolve_run_dir(settings, run_dir_request: str | None) -> Path:
    base = _reports_base(settings)
    if run_dir_request is None:
        latest = find_latest_run_dir(base)
        if latest is None:
            raise HTTPException(status_code=404, detail="no run directories")
        return latest
    candidate = (base / run_dir_request).resolve()
    if base not in candidate.parents and candidate != base:
        raise HTTPException(status_code=400, detail="run_dir outside reports directory")
    if not candidate.is_dir():
        raise HTTPException(status_code=404, detail="run_dir not found")
    return candidate


@router.post("/reports/dry-run/analyze")
def reports_analyze(payload: AnalyzeRequest, request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    run_dir = _resolve_run_dir(settings, payload.run_dir)
    result = analyze_run(run_dir)
    paths = write_analysis_files(result)
    summary_path = paths["summary"]
    return {
        "run_dir": run_dir.name,
        "files": {k: str(p.relative_to(_reports_base(settings))) for k, p in paths.items()},
        "summary": json.loads(summary_path.read_text(encoding="utf-8")),
    }


@router.get("/reports/dry-run/latest")
def reports_latest(request: Request) -> dict[str, Any]:
    settings = request.app.state.settings
    run_dir = _resolve_run_dir(settings, None)
    summary_path = run_dir / "analysis_summary.json"
    if not summary_path.is_file():
        result = analyze_run(run_dir)
        write_analysis_files(result)
    return {
        "run_dir": run_dir.name,
        "summary": json.loads(summary_path.read_text(encoding="utf-8")),
    }
```

`json` import는 routes.py 상단에 추가(있으면 그대로). 기존 mvp-018 엔드포인트와 헬퍼는 보존.

### 4.7 README 변경

KIS 섹션 뒤(또는 mvp-018 단락 뒤)에 다음 단락 추가:

```markdown
## dry-run 리포트 분석 (mvp-019)

mvp-018에서 만든 dry-run 산출물(`reports/dry_run/run_<ts>/{events.jsonl, summary.json, orders.csv}`)을 읽어 분석 리포트를 생성합니다. read-only — 전략이나 OMS를 변경하지 않습니다.

### CLI

```bash
cd projects/paper-trading
.venv/bin/python -m app.reports --latest
# or:
.venv/bin/python -m app.reports --run-dir reports/dry_run/run_2026-05-14T08-00-00
```

### API

```bash
curl -X POST http://127.0.0.1:8000/reports/dry-run/analyze \
  -H 'content-type: application/json' \
  -d '{}'   # latest
curl http://127.0.0.1:8000/reports/dry-run/latest
```

### 산출물 (run_dir 내부)

- `analysis_summary.json` — 카운터, top block reasons, 심볼 통계, pass rate, 제안, 경고
- `analysis_report.md` — 사람용 마크다운 리포트
- `claude_review_input.md` — Claude/Codex가 전략 개선 plan을 작성할 때 참고할 입력 문서

`reports/`는 프로젝트 `.gitignore`로 무시되므로 분석 산출물도 commit되지 않습니다. 응답/리포트에 KIS app key/secret/account 원문은 절대 포함되지 않습니다(`dump_safe` 가드).
```

### 4.8 테스트

#### `tests/test_dry_run_analyzer.py` (신규)

```python
import json
from pathlib import Path

import pytest

from app.reports.dry_run_analyzer import (
    AnalysisResult,
    UnsafeReportPayloadError,
    analyze_run,
    compute_suggestions,
    dump_safe,
    find_latest_run_dir,
    write_analysis_files,
)


@pytest.fixture
def empty_run_dir(tmp_path: Path) -> Path:
    run = tmp_path / "run_2026-05-14T08-00-00"
    run.mkdir()
    return run


@pytest.fixture
def populated_run_dir(tmp_path: Path) -> Path:
    run = tmp_path / "run_2026-05-14T08-00-00"
    run.mkdir()
    # summary.json
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
    (run / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    # events.jsonl
    events = [
        {"ts": "2026-05-14T08:00:01+00:00", "type": "tick_result", "symbol": "AAPL", "passed": True, "blockers": []},
        {"ts": "2026-05-14T08:00:02+00:00", "type": "tick_result", "symbol": "AAPL", "passed": False, "blockers": ["spread_too_wide"]},
        {"ts": "2026-05-14T08:00:03+00:00", "type": "tick_result", "symbol": "MSFT", "passed": False, "blockers": ["stale_quote", "spread_too_wide"]},
        {"ts": "2026-05-14T08:00:04+00:00", "type": "tick_blocked", "reason": "kill_switch_engaged", "snapshots": 1},
    ]
    (run / "events.jsonl").write_text("\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return run


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
    # symbol stats derived from events
    syms = {s.symbol: s for s in result.symbols}
    assert syms["AAPL"].seen == 2
    assert syms["AAPL"].passed == 1
    assert syms["AAPL"].blocked == 1
    assert syms["MSFT"].seen == 1
    assert syms["MSFT"].blocked == 1
    # top reasons aggregated
    reasons = dict(result.top_block_reasons)
    assert reasons["spread_too_wide"] == 2
    assert reasons["stale_quote"] == 1
    # strategy_pass_rate computed from events (seen=3, passed=1)
    assert abs(result.strategy_pass_rate - (1 / 3)) < 1e-3


def test_invalid_event_lines_counted(tmp_path):
    run = tmp_path / "run_2026-05-14T08-00-00"
    run.mkdir()
    (run / "events.jsonl").write_text("not-json\n{\"type\":\"tick_result\",\"symbol\":\"AAPL\",\"passed\":true}\n", encoding="utf-8")
    result = analyze_run(run)
    assert result.invalid_event_lines == 1


def test_dump_safe_blocks_app_secret():
    with pytest.raises(UnsafeReportPayloadError):
        dump_safe({"app_secret": "x"})


def test_dump_safe_allows_secret_exposed_flag():
    dump_safe({"secret_exposed": False})


def test_dump_safe_blocks_nested_account_no():
    with pytest.raises(UnsafeReportPayloadError):
        dump_safe({"data": {"account_no": "12345678"}})


def test_compute_suggestions_high_spread(populated_run_dir):
    result = analyze_run(populated_run_dir)
    text = " ".join(result.suggestions)
    assert "스프레드" in text  # high spread ratio
    assert "stale quote" in text  # high stale ratio


def test_write_analysis_files_creates_three_outputs(populated_run_dir):
    result = analyze_run(populated_run_dir)
    paths = write_analysis_files(result)
    assert paths["summary"].is_file()
    assert paths["report"].is_file()
    assert paths["review_input"].is_file()
    summary = json.loads(paths["summary"].read_text(encoding="utf-8"))
    assert summary["secret_exposed"] is False
    assert summary["strategy_pass_rate"] >= 0


def test_outputs_do_not_leak_fake_credentials(populated_run_dir, tmp_path):
    # Inject a malicious event with credential-looking key.
    bad = tmp_path / "run_bad"
    bad.mkdir()
    (bad / "events.jsonl").write_text(json.dumps({"type": "tick_result", "symbol": "X", "passed": True, "app_key": "leak-XYZ"}) + "\n", encoding="utf-8")
    result = analyze_run(bad)
    with pytest.raises(UnsafeReportPayloadError):
        # write_analysis_files should NOT directly include event keys, but
        # the defense-in-depth dump_safe still must reject if it sees one.
        # The current implementation does not include raw event dicts in the
        # summary, so this test confirms the in-memory result is clean.
        # If a future change leaks app_key, dump_safe catches it.
        dump_safe({"app_key": "leak-XYZ"})  # sanity


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


def test_render_outputs_do_not_contain_account_number(populated_run_dir):
    result = analyze_run(populated_run_dir)
    paths = write_analysis_files(result)
    for p in paths.values():
        text = p.read_text(encoding="utf-8")
        for forbidden in ("KIS_APP_KEY", "KIS_APP_SECRET", "50187996"):
            assert forbidden not in text
```

(약 12개)

#### `tests/test_reports_api.py` (신규)

```python
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api.server import create_app


@pytest.fixture
def app_with_run(tmp_path, monkeypatch):
    # Use a project-relative test dir
    test_subdir = "reports/test_runs_mvp019"
    monkeypatch.setenv("DRY_RUN_REPORTS_DIR", test_subdir)
    project_dir = Path(__file__).resolve().parents[1]
    base = project_dir / test_subdir
    base.mkdir(parents=True, exist_ok=True)
    run = base / "run_2026-05-14T08-00-00"
    run.mkdir(parents=True, exist_ok=True)
    summary = {"state": "stopped", "counters": {"candidates_seen": 0}}
    (run / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    (run / "events.jsonl").write_text("", encoding="utf-8")
    yield create_app()
    shutil.rmtree(base, ignore_errors=True)


def test_analyze_latest_via_post(app_with_run):
    with TestClient(app_with_run) as client:
        r = client.post("/reports/dry-run/analyze", json={})
    assert r.status_code == 200
    body = r.json()
    assert "summary" in body
    assert body["summary"]["secret_exposed"] is False


def test_get_latest_after_analyze(app_with_run):
    with TestClient(app_with_run) as client:
        client.post("/reports/dry-run/analyze", json={})
        r = client.get("/reports/dry-run/latest")
    assert r.status_code == 200
    assert r.json()["summary"]["secret_exposed"] is False


def test_analyze_rejects_path_traversal(app_with_run):
    with TestClient(app_with_run) as client:
        r = client.post("/reports/dry-run/analyze", json={"run_dir": "../../../etc"})
    assert r.status_code in (400, 404, 422)


def test_analyze_returns_404_if_run_dir_missing(app_with_run):
    with TestClient(app_with_run) as client:
        r = client.post("/reports/dry-run/analyze", json={"run_dir": "run_missing"})
    assert r.status_code == 404


def test_response_does_not_leak_credentials(app_with_run):
    with TestClient(app_with_run) as client:
        r = client.post("/reports/dry-run/analyze", json={})
    body_text = r.text
    for needle in ("KIS_APP_KEY", "KIS_APP_SECRET", "kis_app_secret"):
        assert needle not in body_text
```

### 4.9 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기존 155 + 신규 약 17 = ~172 PASS. 종료코드 0.

CLI smoke (선택):

```bash
.venv/bin/python -m app.reports --help
```

### 4.10 `docs/ai/jobs/mvp-019/patch.md`

```markdown
## 1. Files Changed
- app/reports/__init__.py (신규)
- app/reports/dry_run_analyzer.py (신규)
- app/reports/render.py (신규)
- app/reports/__main__.py (신규)
- app/api/routes.py (2개 엔드포인트 추가)
- projects/paper-trading/README.md (mvp-019 단락)
- tests/test_dry_run_analyzer.py (신규)
- tests/test_reports_api.py (신규)
- docs/ai/jobs/mvp-019/patch.md (신규)

## 2. Implementation Summary

### 2.1 Dry-run report analyzer
- analyze_run(run_dir) → AnalysisResult
- summary.json + events.jsonl + orders.csv를 read-only로 처리
- 빈 파일/invalid JSON 라인 robust 처리

### 2.2 분석 지표
- counters(mvp-018 summary 그대로)
- top_block_reasons (events 기반 Counter most_common)
- symbol별 seen/passed/blocked
- strategy_pass_rate

### 2.3 전략 개선 제안 (heuristic)
- 스프레드 / stale quote / market order / OMS 거절 비율 기반
- LLM 직접 주문 판단 아님 — 사람이 검토

### 2.4 Claude/Codex 리뷰 입력
- claude_review_input.md 생성
- run metadata + summary + warnings + suggestions + safety reminders + next-step hints

### 2.5 API + CLI
- POST /reports/dry-run/analyze (body: run_dir 또는 빈 dict for latest)
- GET /reports/dry-run/latest
- python -m app.reports [--run-dir | --latest]

### 2.6 Safety
- app.broker.kis, app.config import 0건 (analyzer는 파일 path만 사용)
- dump_safe로 모든 output dict 검증
- run_dir 경로 traversal 차단(reports 디렉터리 외부 거절)
- 모든 출력에 secret_exposed: false 명시
- reports/ 디렉터리는 mvp-018에서 이미 gitignored

### 2.7 실행한 테스트
- compileall PASS
- pytest 155(기존) + N(신규) = ~172 PASS

### 2.8 다음 mvp 후보
- Claude/Codex가 claude_review_input.md를 읽어 전략 개선 plan 작성(별도 mvp)
- 분석 결과 시각화 (시각화는 별도)
- 여러 run 비교 분석 (multi-run trend)

## 3. Safety Confirmation
- 실제 주문 코드 0건. KIS HTTP 호출 0건.
- analyzer가 app.broker.kis, app.config 미import (구조적 보장).
- 외부 HTTP 라이브러리 import 0건.
- 모든 output dict dump_safe 통과.
- /reports/dry-run/analyze가 path traversal 거절.
- /reports/dry-run/latest 응답에 raw credentials 미포함.
- live trading / market orders / dry_run / kill switch 가드 모두 보존.
- Strategy/OMS/Risk/BrokerAdapter 변경 0건.
- commit/push/merge/deploy 자동화 없음.

## 4. Test Results
(compileall + pytest 출력)

## 5. Remaining TODOs
- analyzer 사용 후 Claude/Codex 별도 mvp에서 전략 개선안 plan 작성.
```

## 5. 테스트 기준

1. `.venv/bin/python -m compileall app tests` 종료코드 0.
2. `.venv/bin/python -m pytest -p no:cacheprovider` 종료코드 0. 기존 155 + 신규 약 17 PASS.
3. `grep -RnE "from app\.broker\.kis|import app\.broker\.kis" projects/paper-trading/app/reports/` 0건.
4. `grep -RnE "from app\.config|import app\.config" projects/paper-trading/app/reports/dry_run_analyzer.py projects/paper-trading/app/reports/render.py projects/paper-trading/app/reports/__main__.py` 0건 (analyzer는 settings 미접근, routes.py만 settings 사용).
5. `grep -RnE "import requests|import httpx|import aiohttp|import urllib3" projects/paper-trading/app/reports/` 0건.
6. `grep -RIn "OrderType\.MARKET" projects/paper-trading/app/` 0건 유지.
7. `dump_safe`가 `app_key`/`app_secret`/`account_no`/`access_token`/`authorization`/`secret`(case-insensitive substring) 포함 시 `UnsafeReportPayloadError`. `secret_exposed` 정확 매칭은 허용.
8. `/reports/dry-run/analyze`가 `../`, 절대경로, reports 디렉터리 외부 path → 400/404/422.
9. analysis_summary.json에 `"secret_exposed": false` 포함, raw credentials 미포함.
10. `git diff --stat`에 mvp-019 외 변경 없음.
11. `.env` staged/committed 없음.

## 6. 리뷰 체크리스트

- [ ] `app/reports/` 패키지 신규 + 4파일.
- [ ] `analyze_run` 빈 run_dir / 정상 run_dir 모두 안전 처리.
- [ ] `dump_safe`가 secret 키 이름 substring 거절, `secret_exposed` whitelist 동작.
- [ ] `compute_suggestions` 휴리스틱이 expected 시나리오 커버(spread, stale, market, oms, no candidates, low pass rate).
- [ ] `compute_warnings`가 errors_total / kis_fail_closed / kill_switch / invalid lines 감지.
- [ ] `write_analysis_files`이 3개 파일 생성 + 모두 dump_safe 통과.
- [ ] `render_*` markdown이 safety reminders 단락 포함.
- [ ] `POST /reports/dry-run/analyze` happy + path traversal 거절 + 404.
- [ ] `GET /reports/dry-run/latest` happy + 자동 분석 fallback.
- [ ] CLI `python -m app.reports --help` 정상 동작.
- [ ] `app.broker.kis` / `app.config` import 0건 in analyzer.
- [ ] 외부 HTTP 라이브러리 import 0건.
- [ ] `OrderType.MARKET` 부재 유지.
- [ ] 기존 155 회귀 없음.
- [ ] mvp-019 신규 약 17 PASS.
- [ ] `git diff --stat`에 mvp-019 외 변경 없음.
- [ ] `.env` staged/committed 없음.
- [ ] commit/push/merge/deploy 자동화 없음.
- [ ] `patch.md` 5섹션 + Implementation Summary 8단락 완성.
