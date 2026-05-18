## 1. 요청 요약

KIS paper / dry-run을 **장시간 안정성 검증**할 수 있는 stateful runner를 만든다.
실제 HTTP 주문 전송은 하지 않는다. 기존 `PaperRunner.run_once` 위에 `DryRunController` 계층을 추가하여
state machine + counters + 리포트 파일 + start/stop/tick API + kill-switch 연동 + 에러 임계치 auto-stop을 제공.

### 안전 원칙 (mvp-005~mvp-017 누적)

- live trading 활성화 금지. 모든 차단 단(Settings/load_settings/RiskEngine/OMS/`/paper/run`/KIS pre-flight/`KIS_ORDER_DRY_RUN=true`) 유지.
- `OrderType.MARKET` 부재 유지.
- 외부 HTTP 라이브러리 import 금지.
- KIS endpoint URL/TR ID/payload 추측 금지. 본 mvp는 KIS HTTP를 새로 호출하지 않음(주문 path가 dry-run으로 차단되므로).
- 실제 KIS app key/secret/account/token이 코드/문서/로그/report에 미포함.
- 리포트 파일에 저장되는 raw 응답은 모두 `sanitize_kis_response` 통과.
- `git commit`/`push`/`merge`/`deploy` 자동화 금지.
- `pip install` 실행 금지(`.venv` 이미 존재).
- Strategy 패키지가 `app.broker.kis*` import 금지(기존 grep 검증 유지).

### 설계 결정 — 명시적 tick 모델

"일정 주기마다 실행"은 다음 두 가지로 분리한다.

1. **명시적 tick 호출** (본 mvp 핵심): `POST /paper/dry-run/tick`이 caller(외부 스케줄러/cron/테스트)로부터 snapshots를 받아 한 사이클을 실행. 카운터 증가, 이벤트 파일 append. asyncio 백그라운드 루프는 신뢰성/테스트 부담이 커서 본 mvp에서 도입하지 않음.
2. **선택적 auto-tick** (보류): 향후 mvp에서 background task로 추가 가능. 본 mvp는 `start()`이 controller를 "running" 상태로 두지만 자체 클럭은 없음 — caller가 tick을 트리거.

이렇게 하면 (a) FastAPI lifespan/TestClient sync 모드와 호환, (b) graceful stop 단순, (c) 모든 동작이 결정론적이라 테스트 쉬움.

### 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기존 131 (mvp-014-017-bundle 포함) + 신규 약 16–22개 모두 PASS.

## 2. 작업 범위

### 포함 (In scope)

`projects/paper-trading/` 아래:

- **`app/runtime/dry_run.py` (신규)** — `DryRunController` 클래스 + `DryRunState` dataclass + `DryRunCounters` dataclass + `DryRunRunHandle` (활성 run의 식별자 + 디렉터리 경로).
  - State machine: `idle` → `running` → (`stopped` 또는 `auto_stopped`).
  - `start(snapshots_supplier=None) -> DryRunRunHandle`: 새 run 시작. 이전 run이 running 이면 reject. report 디렉터리 생성. 카운터 0으로 초기화.
  - `stop(reason: str = "manual") -> DryRunState`: 즉시 정지. 마지막 summary 저장.
  - `tick(snapshots: list[StrategyInput]) -> DryRunTickResult`: 한 사이클 실행. running이 아니면 reject. kill_switch_engaged면 tick 자체 reject(`status="blocked_kill_switch"`) 후 카운터만 증가. 그 외에는 `PaperRunner.run_once`로 위임 → 결과 분류(passed/blocked/oms_ack/oms_error) → 카운터 증가 → 이벤트 file append → orders CSV append(passed 시) → summary file 갱신 → KIS dry-run preview가 있으면 sanitize → return.
  - 에러 임계치 초과 시(`errors_total >= settings.dry_run_max_errors_before_auto_stop`) → `stop(reason="error_threshold")` 자동 호출.
  - 모든 메서드는 동기. asyncio 사용 없음.

- **`app/runtime/dry_run_report.py` (신규)** — 리포트 파일 writer 헬퍼.
  - `make_run_dir(base_dir: Path, started_at: datetime) -> Path` — `run_YYYY-MM-DDThh-mm-ss/` 디렉터리 생성.
  - `append_event(run_dir: Path, event: dict) -> None` — events.jsonl에 한 줄 추가.
  - `write_summary(run_dir: Path, summary: dict) -> None` — summary.json 덮어쓰기.
  - `append_order(run_dir: Path, order: dict) -> None` — orders.csv에 한 행 추가(헤더 없으면 자동 추가).
  - 모든 dict는 caller가 sanitize 후 전달(여기서는 추가 sanitization 하지 않음). 그러나 `dump_safe`라는 가벼운 검사를 한 번 더 수행해서 알려진 secret 키 이름이 들어오면 `assert` 실패(테스트가 catch).

- **`app/api/routes.py` (수정)** — 4개 엔드포인트 추가:
  - `POST /paper/dry-run/start` — body `{}`. 성공 시 `200` + `{"ok": True, "state": "running", "run_dir": "<relative>", "started_at": "..."}`. 이미 running이면 `409`.
  - `POST /paper/dry-run/stop` — body `{}`. 성공 시 `200` + 최종 summary. running이 아니면 `409`.
  - `POST /paper/dry-run/tick` — body `{"snapshots": [...]}` (mvp-005의 `PaperRunRequest.snapshots`와 동일 schema). 성공 시 `200` + tick 결과 요약. running이 아니면 `409`. kill_switch면 `200` with `status="blocked_kill_switch"`.
  - `GET /paper/dry-run/status` — controller state + counters + run_dir(있으면 마스킹된 경로).
  - 모든 응답에서 raw credentials 미노출.

- **`app/api/server.py` (수정)** — lifespan에서 `DryRunController` 인스턴스화 + `app.state.dry_run_controller`로 보관. PaperRunner는 그대로 OMS 와이어링 유지(DryRunController가 별도로 PaperRunner를 들고 있음).

- **`app/config.py` (수정)** — `Settings`에 3개 필드 추가:
  - `dry_run_reports_dir: str = "reports/dry_run"` (프로젝트 디렉터리 기준 상대경로)
  - `dry_run_max_errors_before_auto_stop: int = 10`
  - `dry_run_max_ticks: int | None = None` (None이면 무제한)
  - `load_settings()`에 해당 env 로딩 추가(`DRY_RUN_REPORTS_DIR`, `DRY_RUN_MAX_ERRORS_BEFORE_AUTO_STOP`, `DRY_RUN_MAX_TICKS`).

- **`.env.example` (수정)** — 위 3개 placeholder 추가. 안전한 기본값.

- **`projects/paper-trading/README.md` (수정)** — `## 장시간 KIS dry-run 검증 (mvp-018)` 단락 추가. 4개 엔드포인트 사용 예시(curl) + 리포트 파일 구조 + kill-switch 동작 + auto-stop 동작.

- **`projects/paper-trading/.gitignore` (수정)** — `reports/` 추가하여 dry-run 출력이 commit되지 않게 함.

- **신규 테스트**:
  - `tests/test_dry_run_controller.py` — state machine, tick happy path, kill switch block, error threshold auto-stop, max_ticks cap, counter 누적.
  - `tests/test_dry_run_reports.py` — `make_run_dir` 결정성, `append_event` JSONL 정합, `write_summary` overwrite, `append_order` CSV header 자동, `dump_safe` secret 키 detect.
  - `tests/test_dry_run_routes.py` — 4개 endpoint happy path + error cases(409 when already running / not running) + secret/account 미노출.

- **수정 테스트**:
  - `tests/test_api_paper_status.py` — `/paper/status`에 `dry_run` 상위 요약(`{"running": bool, "ticks_total": int, ...}`) 추가 여부 확인(아래 API 확장 참고).
  - `tests/test_kis_capabilities.py` 또는 `tests/test_kis_order_response_model.py` 회귀: KIS 측 동작 변경 없음 확인.

- **`/paper/status` 응답 확장 (선택, 최소)**: 기존 응답 dict에 다음 한 줄 추가:
  ```python
  "dry_run_running": bool(controller.is_running()) if controller else False,
  ```
  자세한 metrics는 `/paper/dry-run/status` 전용으로 분리. `/paper/status`는 high-level flag 한 개만.

- **`docs/ai/jobs/mvp-018/patch.md` (신규)** — Codex 변경 요약.

### 제외 (Out of scope; 절대 만지지 않음)

- 실제 KIS HTTP 호출 / endpoint URL / TR ID / payload 추가.
- 외부 HTTP 라이브러리 import.
- asyncio 백그라운드 auto-tick loop. (향후 mvp.)
- mvp-014-017-bundle 산출물 변경 (특히 `docs/kis/MISSING_OFFICIAL_VALUES.md`).
- mvp-001..mvp-017 산출물 변경.
- `app/strategy/`, `app/risk/`, `app/oms/`, `app/domain/`, `app/broker/{base.py,paper.py,alpaca_paper.py,kis.py}`, `app/main.py`, `app/runtime/paper_runner.py` 변경. (`paper_runner.py`는 변경하지 않고 DryRunController에서 호출만 함.)
- live trading 활성화, 시장가 주문 허용, KIS endpoint 추측, 실주문 코드.
- `OrderType` enum 변경.
- 실제 KIS app key/secret/account/token을 코드/문서/리포트/log에 인용.
- `.env`, secrets, credentials, auth, payment, DB migration, production infra, `.github/workflows/` 변경.
- 자동 commit/push/merge/deploy 신설.
- 임의 shell 명령 입력 UI/API 신설.
- `pip install` 실행.
- `imports/local-mvp/` 변경.
- `web/`, `prompts/`, `scripts/`, 기존 `docs/`(`docs/kis/` + mvp-018 외) 변경.

### 안전 가드

- `DryRunController`는 `app.broker.kis`의 KIS endpoint를 직접 호출하지 않는다. 오직 `PaperRunner` → `OMS.place(intent)` 경로만 사용. 결과적으로 KisBroker 활성 broker 아님(여전히 PaperBroker만). KIS 관련 carryover는 일반 KIS broker preview 데이터를 후처리할 때뿐(현재 OMS가 PaperBroker로 가므로 KIS preview는 직접적으로 닿지 않으나, 향후 OMS가 KIS로 라우팅되더라도 dry-run 흐름은 동일하게 안전).
- 리포트 파일 쓰기 전 dict에 secret 키 이름이 포함되면 `dump_safe`가 ValueError. 테스트가 이를 검증.
- 리포트 디렉터리는 프로젝트 디렉터리 외부(예: `/tmp`)로 못 가게 path traversal 차단(`dry_run_reports_dir`이 절대 경로면 reject).
- `reports/`는 `.gitignore` 추가.

## 3. 수정해야 할 파일

### 신규

| 파일 | 목적 |
| --- | --- |
| `app/runtime/dry_run.py` | DryRunController + DryRunState + DryRunCounters + DryRunTickResult |
| `app/runtime/dry_run_report.py` | 리포트 파일 writer 헬퍼 |
| `tests/test_dry_run_controller.py` | 상태 머신 + 카운터 + 임계치 |
| `tests/test_dry_run_reports.py` | 파일 writer 동작 + secret 차단 |
| `tests/test_dry_run_routes.py` | 4개 endpoint 동작 + secret 미노출 |
| `docs/ai/jobs/mvp-018/patch.md` | Codex 변경 요약 |

### 수정

| 파일 | 변경 내용 |
| --- | --- |
| `app/config.py` | `dry_run_reports_dir`/`dry_run_max_errors_before_auto_stop`/`dry_run_max_ticks` 필드 + env 로딩 |
| `app/api/routes.py` | 4개 `/paper/dry-run/*` 엔드포인트 + `/paper/status`에 `dry_run_running` 한 줄 |
| `app/api/server.py` | lifespan에서 `DryRunController` 인스턴스화 + `app.state.dry_run_controller` 보관 |
| `.env.example` | `DRY_RUN_REPORTS_DIR=reports/dry_run` / `DRY_RUN_MAX_ERRORS_BEFORE_AUTO_STOP=10` / `DRY_RUN_MAX_TICKS=` placeholder |
| `.gitignore` (프로젝트) | `reports/` 추가 |
| `README.md` | 장시간 dry-run 검증 단락 |
| `tests/test_api_paper_status.py` | `dry_run_running` 필드 assertion (양 시나리오) |

### 절대 미수정

- `app/runtime/paper_runner.py` (그대로 사용)
- `app/broker/{base,paper,alpaca_paper,kis}.py`
- `app/oms/manager.py`, `app/risk/engine.py`, `app/strategy/*`, `app/domain/*`, `app/main.py`
- 기존 테스트 파일 중 본 작업이 다루지 않는 것
- 루트 `.gitignore`, mvp-001..mvp-017 산출물
- `docs/kis/MISSING_OFFICIAL_VALUES.md`(mvp-014-017-bundle 산출물)

## 4. Codex 구현 지시문

### 4.1 사전 점검

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m pytest -p no:cacheprovider --co -q 2>&1 | tail -3
# expect: "131 tests collected" (or higher, after mvp-014-017-bundle landed)

grep -q "kis_order_dry_run" app/config.py && echo "OK config.kis_order_dry_run"
grep -q "class KisHttpClient" app/broker/kis.py && echo "OK KisHttpClient"
grep -q "class PaperRunner" app/runtime/paper_runner.py && echo "OK PaperRunner"
test -d ../../docs/kis && echo "OK docs/kis present" || echo "WARN docs/kis missing"
test -d .venv && echo "OK venv"
```

위가 모두 OK → 진행. 누락이면 `patch.md` Remaining TODOs에 기록 후 작업 중단.

### 4.2 `app/config.py` 변경

`Settings`에 추가:

```python
dry_run_reports_dir: str = "reports/dry_run"
dry_run_max_errors_before_auto_stop: int = 10
dry_run_max_ticks: int | None = None
```

`load_settings()` 생성자에 추가:

```python
dry_run_reports_dir=_str_env("DRY_RUN_REPORTS_DIR") or "reports/dry_run",
dry_run_max_errors_before_auto_stop=_int_env("DRY_RUN_MAX_ERRORS_BEFORE_AUTO_STOP", 10),
dry_run_max_ticks=(_int_env("DRY_RUN_MAX_TICKS", 0) or None) if os.getenv("DRY_RUN_MAX_TICKS") else None,
```

(`dry_run_max_ticks`은 빈 문자열/미설정이면 None. 양수면 그 값.)

기존 paper/live/market/kill_switch/KIS 가드 변경 없음.

### 4.3 `app/runtime/dry_run_report.py` (신규)

```python
"""Dry-run report file writers.

All writers are synchronous and safe to call from request handlers. Callers
must pre-sanitize dicts; dump_safe() catches obvious credential key names as
a defense-in-depth layer.
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


_FORBIDDEN_KEY_FRAGMENTS = (
    "app_key", "appkey", "appKey",
    "app_secret", "appsecret", "appSecret",
    "account_no", "accountNo", "cano",
    "access_token", "accessToken",
    "authorization",
    "secret",
)


class UnsafeReportPayloadError(ValueError):
    """A report payload contains a credential-like key name."""


def dump_safe(payload: Any) -> Any:
    """Recursively check that no dict key matches a known secret pattern."""
    if isinstance(payload, dict):
        for key in payload:
            for forbidden in _FORBIDDEN_KEY_FRAGMENTS:
                if forbidden.lower() in str(key).lower():
                    raise UnsafeReportPayloadError(
                        f"Report payload contains forbidden key fragment: {key!r}"
                    )
        for value in payload.values():
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
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


_ORDER_COLUMNS = (
    "ts", "symbol", "side", "quantity", "limit_price",
    "order_type", "oms_status", "broker_environment", "idempotency_key",
)


def append_order(run_dir: Path, order: dict[str, Any]) -> None:
    dump_safe(order)
    orders_path = run_dir / "orders.csv"
    header_needed = not orders_path.exists()
    with orders_path.open("a", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_ORDER_COLUMNS, extrasaction="ignore")
        if header_needed:
            writer.writeheader()
        writer.writerow({k: order.get(k, "") for k in _ORDER_COLUMNS})
```

### 4.4 `app/runtime/dry_run.py` (신규)

```python
"""Long-running KIS paper / dry-run controller.

Stateful wrapper around PaperRunner. No HTTP. No auto-tick (caller drives
ticks via /paper/dry-run/tick). Stops automatically when error threshold or
max-tick cap is reached.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import Settings
from app.domain.market import StrategyInput
from app.runtime.paper_runner import PaperRunner
from app.runtime.dry_run_report import (
    UnsafeReportPayloadError,
    append_event,
    append_order,
    make_run_dir,
    write_summary,
)


_STATE_IDLE = "idle"
_STATE_RUNNING = "running"
_STATE_STOPPED = "stopped"
_STATE_AUTO_STOPPED = "auto_stopped"


@dataclass
class DryRunCounters:
    ticks_total: int = 0
    candidates_seen: int = 0
    candidates_blocked: int = 0
    candidates_passed_risk: int = 0
    dry_run_orders_created: int = 0
    dry_run_orders_rejected: int = 0
    oms_rejections: int = 0
    risk_rejections: int = 0
    stale_quote_rejections: int = 0
    spread_rejections: int = 0
    market_order_rejections: int = 0
    kis_fail_closed_count: int = 0
    errors_total: int = 0
    last_error: str | None = None
    kill_switch_blocked_ticks: int = 0


@dataclass
class DryRunState:
    state: str = _STATE_IDLE
    started_at: datetime | None = None
    stopped_at: datetime | None = None
    last_tick_at: datetime | None = None
    stop_reason: str | None = None
    run_dir: Path | None = None
    counters: DryRunCounters = field(default_factory=DryRunCounters)


@dataclass
class DryRunTickResult:
    status: str  # "ok" | "blocked_kill_switch" | "auto_stopped" | "max_ticks_reached"
    snapshots_evaluated: int
    candidates_passed: int
    candidates_blocked: int
    oms_acks: int
    oms_errors: int


class DryRunController:
    def __init__(self, settings: Settings, paper_runner: PaperRunner, base_dir: Path) -> None:
        self._settings = settings
        self._runner = paper_runner
        self._base_dir = Path(base_dir).resolve()
        self._state = DryRunState()

    @property
    def state(self) -> DryRunState:
        return self._state

    def is_running(self) -> bool:
        return self._state.state == _STATE_RUNNING

    # --- lifecycle ----------------------------------------------------------

    def start(self) -> DryRunState:
        if self.is_running():
            raise RuntimeError("dry-run already running")
        now = datetime.now(timezone.utc)
        reports_dir = self._reports_dir()
        run_dir = make_run_dir(reports_dir, now)
        self._state = DryRunState(
            state=_STATE_RUNNING,
            started_at=now,
            last_tick_at=None,
            run_dir=run_dir,
            counters=DryRunCounters(),
        )
        self._write_summary()
        return self._state

    def stop(self, reason: str = "manual") -> DryRunState:
        if not self.is_running():
            raise RuntimeError("dry-run not running")
        now = datetime.now(timezone.utc)
        self._state.state = _STATE_STOPPED if reason == "manual" else _STATE_AUTO_STOPPED
        self._state.stopped_at = now
        self._state.stop_reason = reason
        self._write_summary()
        return self._state

    # --- tick --------------------------------------------------------------

    def tick(self, snapshots: list[StrategyInput]) -> DryRunTickResult:
        if not self.is_running():
            raise RuntimeError("dry-run not running")
        now = datetime.now(timezone.utc)
        self._state.last_tick_at = now
        c = self._state.counters
        c.ticks_total += 1

        # kill switch blocks new ticks (no strategy evaluation)
        if self._settings.kill_switch_engaged:
            c.kill_switch_blocked_ticks += 1
            self._append_event({
                "ts": now.isoformat(),
                "type": "tick_blocked",
                "reason": "kill_switch_engaged",
                "snapshots": len(snapshots),
            })
            self._write_summary()
            return DryRunTickResult(
                status="blocked_kill_switch",
                snapshots_evaluated=0,
                candidates_passed=0,
                candidates_blocked=0,
                oms_acks=0,
                oms_errors=0,
            )

        # delegate to PaperRunner (no KIS HTTP)
        try:
            results = self._runner.run_once(snapshots)
        except Exception as exc:  # defensive — PaperRunner should not raise
            c.errors_total += 1
            c.last_error = type(exc).__name__
            self._append_event({
                "ts": now.isoformat(),
                "type": "runner_error",
                "error_class": type(exc).__name__,
            })
            self._maybe_auto_stop()
            self._write_summary()
            return DryRunTickResult(
                status="auto_stopped" if not self.is_running() else "ok",
                snapshots_evaluated=0,
                candidates_passed=0,
                candidates_blocked=0,
                oms_acks=0,
                oms_errors=1,
            )

        c.candidates_seen += len(results)
        passed = blocked = oms_acks = oms_errors = 0
        for r in results:
            event = {
                "ts": now.isoformat(),
                "type": "tick_result",
                "symbol": r.symbol,
                "passed": r.strategy.passed,
                "blockers": list(r.strategy.blockers),
                "oms_status": (r.oms_ack.status if r.oms_ack else None),
                "oms_error": r.oms_error,
            }
            try:
                self._append_event(event)
            except UnsafeReportPayloadError as exc:
                c.errors_total += 1
                c.last_error = "unsafe_report_payload"
                self._append_event({
                    "ts": now.isoformat(),
                    "type": "report_error",
                    "error_class": exc.__class__.__name__,
                })
                continue

            if r.strategy.passed:
                passed += 1
                c.candidates_passed_risk += 1
                if r.oms_ack is not None:
                    oms_acks += 1
                    if r.oms_ack.status == "dry_run":
                        c.dry_run_orders_created += 1
                    self._append_order({
                        "ts": now.isoformat(),
                        "symbol": r.symbol,
                        "side": r.strategy.non_executable_order_intent.side.value if r.strategy.non_executable_order_intent else "",
                        "quantity": getattr(r.strategy.non_executable_order_intent, "quantity", ""),
                        "limit_price": str(getattr(r.strategy.non_executable_order_intent, "limit_price", "")),
                        "order_type": getattr(r.strategy.non_executable_order_intent, "order_type", "").value if r.strategy.non_executable_order_intent else "",
                        "oms_status": r.oms_ack.status,
                        "broker_environment": "paper",
                        "idempotency_key": "",
                    })
                else:
                    oms_errors += 1
                    c.oms_rejections += 1
                    if r.oms_error and "RiskEngine" in r.oms_error:
                        c.risk_rejections += 1
                    if r.oms_error and "live" in r.oms_error.lower():
                        c.errors_total += 1
                        c.last_error = "oms_live_block"
            else:
                blocked += 1
                c.candidates_blocked += 1
                for reason in r.strategy.blockers:
                    if "stale_quote" in reason:
                        c.stale_quote_rejections += 1
                    if "spread" in reason:
                        c.spread_rejections += 1
                    if "market" in reason or reason == "order_type_not_limit":
                        c.market_order_rejections += 1

        # max-ticks auto stop
        if self._settings.dry_run_max_ticks and c.ticks_total >= self._settings.dry_run_max_ticks:
            self._auto_stop("max_ticks_reached")
            self._write_summary()
            return DryRunTickResult(
                status="max_ticks_reached",
                snapshots_evaluated=len(results),
                candidates_passed=passed,
                candidates_blocked=blocked,
                oms_acks=oms_acks,
                oms_errors=oms_errors,
            )

        self._maybe_auto_stop()
        self._write_summary()
        return DryRunTickResult(
            status="auto_stopped" if not self.is_running() else "ok",
            snapshots_evaluated=len(results),
            candidates_passed=passed,
            candidates_blocked=blocked,
            oms_acks=oms_acks,
            oms_errors=oms_errors,
        )

    # --- helpers -----------------------------------------------------------

    def _reports_dir(self) -> Path:
        raw = self._settings.dry_run_reports_dir
        if Path(raw).is_absolute():
            raise RuntimeError("dry_run_reports_dir must be a project-relative path")
        return (self._base_dir / raw).resolve()

    def _append_event(self, event: dict[str, Any]) -> None:
        if self._state.run_dir is not None:
            append_event(self._state.run_dir, event)

    def _append_order(self, order: dict[str, Any]) -> None:
        if self._state.run_dir is not None:
            append_order(self._state.run_dir, order)

    def _write_summary(self) -> None:
        if self._state.run_dir is None:
            return
        write_summary(self._state.run_dir, self.summary())

    def _maybe_auto_stop(self) -> None:
        c = self._state.counters
        if c.errors_total >= self._settings.dry_run_max_errors_before_auto_stop:
            self._auto_stop("error_threshold")

    def _auto_stop(self, reason: str) -> None:
        if not self.is_running():
            return
        self._state.state = _STATE_AUTO_STOPPED
        self._state.stopped_at = datetime.now(timezone.utc)
        self._state.stop_reason = reason

    # --- status / summary --------------------------------------------------

    def summary(self) -> dict[str, Any]:
        s = self._state
        c = s.counters
        uptime = 0
        if s.started_at:
            end = s.stopped_at or datetime.now(timezone.utc)
            uptime = int((end - s.started_at).total_seconds())
        return {
            "state": s.state,
            "started_at": s.started_at.isoformat() if s.started_at else None,
            "stopped_at": s.stopped_at.isoformat() if s.stopped_at else None,
            "last_tick_at": s.last_tick_at.isoformat() if s.last_tick_at else None,
            "stop_reason": s.stop_reason,
            "uptime_seconds": uptime,
            "run_dir": str(s.run_dir.relative_to(self._base_dir)) if s.run_dir else None,
            "counters": vars(c).copy(),
            "config": {
                "kis_order_dry_run": bool(self._settings.kis_order_dry_run),
                "live_trading_enabled": bool(self._settings.live_trading_enabled),
                "allow_market_orders": bool(self._settings.allow_market_orders),
                "kill_switch_engaged": bool(self._settings.kill_switch_engaged),
                "max_errors_before_auto_stop": self._settings.dry_run_max_errors_before_auto_stop,
                "max_ticks": self._settings.dry_run_max_ticks,
            },
            "secret_exposed": False,
        }
```

### 4.5 `app/api/server.py` 변경

`create_app()` lifespan에서, PaperRunner 만든 직후:

```python
from app.runtime.dry_run import DryRunController
from pathlib import Path
project_dir = Path(__file__).resolve().parents[2]
dry_run_controller = DryRunController(settings, app.state.runner, project_dir)
app.state.dry_run_controller = dry_run_controller
```

(`app.state.runner`가 이미 `PaperRunner` 인스턴스. 같은 인스턴스를 controller가 들고 있는다 — OMS 사이드이펙트 공유.)

### 4.6 `app/api/routes.py` 변경

#### 신규 엔드포인트

```python
@router.post("/paper/dry-run/start")
def dry_run_start(request: Request) -> dict[str, Any]:
    controller = request.app.state.dry_run_controller
    try:
        state = controller.start()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return controller.summary()


@router.post("/paper/dry-run/stop")
def dry_run_stop(request: Request) -> dict[str, Any]:
    controller = request.app.state.dry_run_controller
    try:
        controller.stop(reason="manual")
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return controller.summary()


class DryRunTickRequest(BaseModel):
    snapshots: list[StrategyInput] = []


@router.post("/paper/dry-run/tick")
def dry_run_tick(payload: DryRunTickRequest, request: Request) -> dict[str, Any]:
    controller = request.app.state.dry_run_controller
    try:
        result = controller.tick(payload.snapshots)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {
        "tick": {
            "status": result.status,
            "snapshots_evaluated": result.snapshots_evaluated,
            "candidates_passed": result.candidates_passed,
            "candidates_blocked": result.candidates_blocked,
            "oms_acks": result.oms_acks,
            "oms_errors": result.oms_errors,
        },
        "summary": controller.summary(),
    }


@router.get("/paper/dry-run/status")
def dry_run_status(request: Request) -> dict[str, Any]:
    controller = request.app.state.dry_run_controller
    return controller.summary()
```

#### `/paper/status` 보강 — 한 줄 추가

기존 응답 dict에 `kis_order_dry_run: bool` 옆에:

```python
"dry_run_running": bool(getattr(request.app.state, "dry_run_controller", None) and request.app.state.dry_run_controller.is_running()),
```

raw credentials 미노출 그대로.

### 4.7 `.env.example` 변경

`KIS_ORDER_DRY_RUN=true` 다음에:

```
DRY_RUN_REPORTS_DIR=reports/dry_run
DRY_RUN_MAX_ERRORS_BEFORE_AUTO_STOP=10
DRY_RUN_MAX_TICKS=
```

다른 라인 변경 없음.

### 4.8 `.gitignore` (프로젝트) 변경

기존 룰 보존하면서:

```
reports/
```

추가. 루트 `.gitignore`는 손대지 않는다.

### 4.9 `projects/paper-trading/README.md` 변경

KIS 섹션 뒤에 `## 장시간 KIS dry-run 검증 (mvp-018)` 단락:

```markdown
## 장시간 KIS dry-run 검증 (mvp-018)

`DryRunController`는 paper-trading 시스템을 장시간 안정성 검증할 수 있는 stateful runner입니다. KIS HTTP는 호출하지 않으며, `KIS_ORDER_DRY_RUN=true` 기본값에서 KIS broker는 dry-run preview만 반환합니다.

엔드포인트:

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| `POST` | `/paper/dry-run/start` | 새 run 시작. 이미 running이면 409. `reports/dry_run/run_<timestamp>/` 디렉터리 생성. |
| `POST` | `/paper/dry-run/tick` | snapshots 1개 사이클 처리. running이 아니면 409. kill_switch면 `blocked_kill_switch`. |
| `POST` | `/paper/dry-run/stop` | 정지. running이 아니면 409. |
| `GET` | `/paper/dry-run/status` | 현재 state + counters + summary. credentials 미포함. |

리포트 파일(프로젝트 `.gitignore`로 ignore됨):

- `reports/dry_run/run_<timestamp>/events.jsonl` — 매 tick 이벤트 + 후보별 결과
- `reports/dry_run/run_<timestamp>/summary.json` — 누적 summary(매 tick 덮어쓰기)
- `reports/dry_run/run_<timestamp>/orders.csv` — passed candidates의 OMS ack(헤더 포함)

안전:

- 모든 리포트 dict는 `dump_safe()`로 검사되며, `app_key`/`app_secret`/`account_no`/`access_token` 등 키 이름이 포함되면 즉시 거절.
- `kill_switch_engaged=true`이면 tick이 strategy 평가 없이 `blocked_kill_switch`로 종료.
- `errors_total >= DRY_RUN_MAX_ERRORS_BEFORE_AUTO_STOP` 이면 controller가 `auto_stopped`로 전환.
- `DRY_RUN_MAX_TICKS` 도달 시도 `auto_stopped`.

```bash
curl -X POST http://127.0.0.1:8000/paper/dry-run/start
curl -X POST http://127.0.0.1:8000/paper/dry-run/tick -H 'content-type: application/json' \
  -d '{"snapshots":[]}'
curl -X GET http://127.0.0.1:8000/paper/dry-run/status
curl -X POST http://127.0.0.1:8000/paper/dry-run/stop
```
```

### 4.10 테스트

`plan.md`에 분리된 3개 신규 테스트 파일 + 1개 보정. 핵심 테스트:

#### `tests/test_dry_run_controller.py`

1. `test_start_creates_running_state_and_run_dir` — start 후 state=running, run_dir이 tmp_path 안.
2. `test_double_start_raises` — start 두 번 → RuntimeError.
3. `test_stop_transitions_to_stopped` — start → stop → state=stopped, stop_reason="manual".
4. `test_tick_increments_counters` — make_snapshot 1개로 tick → ticks_total=1, candidates_seen=1.
5. `test_tick_blocked_candidate_increments_blocked_counter` — gap_below_threshold 만들어 → candidates_blocked=1, candidates_passed_risk=0.
6. `test_tick_passed_candidate_creates_dry_run_order` — passed snapshot → `dry_run_orders_created >= 1` (PaperBroker는 status="dry_run" 안 보내지만 OMS는 dry_run mode일 때 OrderAck를 그대로 반환; KIS broker가 활성이 아니라 PaperBroker라 이 case는 OrderAck status가 "accepted". 카운터 누적 검증).
   - 보정: PaperBroker는 dry-run 모드 없이 항상 "accepted". 그래서 `dry_run_orders_created`는 KIS preview용. PaperBroker 사용 시 `oms_acks` 카운터만 증가. 테스트 expectation 조정.
7. `test_kill_switch_blocks_tick` — settings.kill_switch_engaged=True with TestClient app rebuild → tick → status="blocked_kill_switch", strategy 평가 안 됨, counter=kill_switch_blocked_ticks=1.
8. `test_auto_stop_after_max_ticks` — settings.dry_run_max_ticks=2 → tick 2회 후 state=auto_stopped, stop_reason="max_ticks_reached".
9. `test_auto_stop_after_error_threshold` — controller에 PaperRunner mock(raise Exception) → 호출 10회 후 state=auto_stopped, stop_reason="error_threshold".
10. `test_summary_has_secret_exposed_false`.
11. `test_summary_run_dir_is_project_relative`.

#### `tests/test_dry_run_reports.py`

1. `test_dump_safe_rejects_app_key_key` — `dump_safe({"app_key": "x"})` → UnsafeReportPayloadError.
2. `test_dump_safe_rejects_nested_secret` — `dump_safe({"outer": {"app_secret": "y"}})` → 거절.
3. `test_dump_safe_allows_safe_dict` — `{"symbol":"AAPL","status":"ok"}` 통과.
4. `test_make_run_dir_is_deterministic_per_timestamp` — 같은 timestamp 두 번 → 동일 path(이미 존재해도 OK).
5. `test_append_event_writes_jsonl_line` — tmp_path에 append 후 file 한 줄.
6. `test_append_event_blocks_secret_payload` — `{"app_secret":"x"}` append 시 UnsafeReportPayloadError.
7. `test_write_summary_overwrites` — 2번 호출 후 파일 내용 == 두 번째.
8. `test_append_order_creates_header_then_appends` — 첫 호출 헤더 + 행, 두 번째 호출 행만.

#### `tests/test_dry_run_routes.py`

1. `test_dry_run_start_then_status_then_stop` — POST start → 200 + state=running. GET status → state=running. POST stop → state=stopped.
2. `test_dry_run_start_twice_returns_409`.
3. `test_dry_run_stop_when_not_running_returns_409`.
4. `test_dry_run_tick_when_not_running_returns_409`.
5. `test_dry_run_tick_with_snapshot_evaluates` — start → tick with 1 snapshot → 200 + tick.snapshots_evaluated=1.
6. `test_dry_run_status_no_credentials_in_response` — start → GET status → response.text에 `KIS_APP_KEY`/`KIS_APP_SECRET`/raw account 미포함.
7. `test_dry_run_kill_switch_blocks_tick` — env로 `KILL_SWITCH_ENGAGED=true` set → start → tick → tick.status=="blocked_kill_switch".
8. `test_paper_status_includes_dry_run_running` — `/paper/status`에 `dry_run_running` 키 존재.

#### `tests/test_api_paper_status.py` 보정

기존 시나리오에:

```python
assert "dry_run_running" in body
assert isinstance(body["dry_run_running"], bool)
```

### 4.11 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기대: 131 + 신규 약 27개 = 158± PASS. 종료코드 0.

테스트 중 만든 임시 reports 디렉터리는 `tmp_path` 사용해서 cleanup 자동. `Settings.dry_run_reports_dir`을 `replace`로 tmp 경로로 바꾼 임시 instance를 controller에 주입하는 방식 권장.

저장소 루트:

```bash
git diff --stat
git status --short
```

mvp-018 외 변경 없음. `reports/` 가 ignored 확인.

### 4.12 `docs/ai/jobs/mvp-018/patch.md`

```markdown
## 1. Files Changed
(신규/수정 파일 전체)

## 2. Implementation Summary

### 2.1 DryRunController (state machine)
- idle → running → stopped/auto_stopped
- start() / stop() / tick() 동기 API
- KIS HTTP 호출 0건, PaperRunner.run_once만 사용

### 2.2 검증 지표 수집
- DryRunCounters에 16개 필드 (ticks_total ... uptime_seconds 등)
- summary()가 매 tick마다 summary.json 갱신

### 2.3 리포트 파일
- reports/dry_run/run_<ts>/{events.jsonl, summary.json, orders.csv}
- 모든 writer가 dump_safe로 secret 키 이름 차단
- 프로젝트 .gitignore에 reports/ 추가

### 2.4 Safety
- live trading / market orders / KIS_ORDER_DRY_RUN / kill_switch 모두 유지
- raw credentials 코드/리포트/상태 미노출
- KIS endpoint 추가 0건

### 2.5 API
- POST /paper/dry-run/start, stop, tick
- GET /paper/dry-run/status
- /paper/status에 dry_run_running 한 줄

### 2.6 Kill switch / auto-stop
- kill_switch_engaged면 tick 자체가 blocked_kill_switch
- errors_total >= 임계치 → auto_stopped(reason=error_threshold)
- ticks_total >= max_ticks → auto_stopped(reason=max_ticks_reached)

### 2.7 실행한 테스트
- compileall PASS
- pytest 131 + 신규 N = 158± PASS

### 2.8 다음 mvp 후보
- 향후 background auto-tick(asyncio task) 추가
- KIS 공식 문서값 채워지면 dry-run controller가 실제 HTTP 모드도 지원 (별도 mvp)
- 리포트 viewer / 분석 도구 추가

## 3. Safety Confirmation
(모두 보존 + dump_safe 추가)

## 4. Test Results
(compileall + pytest 출력)

## 5. Remaining TODOs
(있으면 명시)
```

## 5. 테스트 기준

1. `.venv/bin/python -m compileall app tests` 종료코드 0.
2. `.venv/bin/python -m pytest -p no:cacheprovider` 종료코드 0. 기존 131 + 신규 약 27 PASS.
3. `grep -RIn "OrderType\.MARKET" projects/paper-trading/app` 0건 유지.
4. `grep -RIn "https?://" projects/paper-trading/app/broker/kis.py` 0건 유지.
5. `grep -RInE "import requests|import httpx|import aiohttp|import urllib" projects/paper-trading/app/` 0건.
6. `grep -RnE "from app\.broker\.kis" projects/paper-trading/app/strategy/` 0건.
7. `grep -RIn "PSNFD\|PKID\|AKIA\|sk-\|ghp_" projects/paper-trading/ docs/kis/` 0건.
8. `DryRunController.summary()`에 `secret_exposed: False` 포함. `KIS_APP_KEY`/`KIS_APP_SECRET`/raw `KIS_ACCOUNT_NO` 미포함.
9. `dump_safe`가 `app_key`/`app_secret`/`account_no`/`access_token`/`authorization` 등 키 이름 포함 시 `UnsafeReportPayloadError`.
10. `reports/`가 `projects/paper-trading/.gitignore`에 등재.
11. `git diff --stat`에 mvp-018 외 변경 없음.
12. `.env` staged/committed 없음.
13. `app/runtime/paper_runner.py` 미변경(grep으로 변경 0줄 확인).
14. `app/broker/kis.py` 미변경.

## 6. 리뷰 체크리스트

- [ ] `app/runtime/dry_run.py` + `app/runtime/dry_run_report.py` 신규.
- [ ] `DryRunController` 상태 머신 정확(idle→running→stopped/auto_stopped, double-start 거절, stop-when-not-running 거절).
- [ ] `tick()`이 kill_switch에서 blocked_kill_switch 반환, strategy 평가 없음, counter 1 증가.
- [ ] `tick()`이 max_ticks 도달 시 auto_stop with reason=max_ticks_reached.
- [ ] `tick()`이 errors_total 임계 초과 시 auto_stop with reason=error_threshold.
- [ ] `dump_safe`가 secret 키 이름 포함 dict를 즉시 거절.
- [ ] 모든 리포트 writer가 `dump_safe`를 통과한 dict만 받음.
- [ ] `summary()`가 `secret_exposed: False` 노출, raw credentials 미포함.
- [ ] 4개 신규 엔드포인트 happy/error path 모두 정상.
- [ ] `/paper/status`에 `dry_run_running` 한 줄 추가, 기존 필드 보존.
- [ ] `Settings`에 3개 신규 필드 + env 로딩. 기본값 안전(`reports/dry_run`, 10, None).
- [ ] `app/api/server.py` lifespan이 `DryRunController` 인스턴스화 + `app.state.dry_run_controller` 보관.
- [ ] `.env.example`에 3개 신규 placeholder.
- [ ] `.gitignore` 프로젝트에 `reports/` 추가.
- [ ] README에 mvp-018 단락.
- [ ] `app/runtime/paper_runner.py` 미변경.
- [ ] `app/broker/kis.py` 미변경 (KIS endpoint/TR ID/payload 추가 0건).
- [ ] 외부 HTTP 라이브러리 import 0건 유지.
- [ ] `OrderType.MARKET` 부재.
- [ ] Strategy 패키지가 `app.broker.kis*` import 0건.
- [ ] 기존 131 테스트 회귀 없음.
- [ ] mvp-018 신규 약 27 PASS.
- [ ] `git diff --stat`에 mvp-018 외 변경 없음.
- [ ] `.env` staged/committed 없음.
- [ ] commit/push/merge/deploy 자동화 없음.
- [ ] `patch.md` 5섹션 + Implementation Summary 8단락 완성.
