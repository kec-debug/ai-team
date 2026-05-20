# live-validation-001 — 최종 UX / 운영 안정화 및 live validation 준비

본 job 은 master plan §6 Phase 5 슬롯에 속하지만 **실거래 활성화 코드를 추가하지 않는다.** request body 가 명시적으로 "이번 작업은 실거래를 시작하는 작업이 아니다" 를 선언하고 모든 live arm / live order / dry-run-disable / market-allow 버튼을 금지한다. 본 작업의 산출물은 **paper 안전 경계를 유지한 채 운영자가 readiness 를 확인할 수 있는 read-only UX + preflight 점검** 뿐이며, 실제 live arm / live activation 은 별도 인-future job 에서 명시적 사용자 승인 이후에만 진입한다.

## 1. 요청 요약

paper trading 기반 (paper-001 / paper-002 / runtime-002 / paper-ux-001 / api-orders-paper-001..003-query / strategy-002 / runtime-soak-001) 이 완성된 시점에서, 다음 단계로 실제 live validation 을 결정하기 전 **운영자가 "현재 시스템이 live validation 진입 조건을 모두 만족하는가" 를 한눈에 확인할 수 있어야 한다**. 본 작업은:

- 대시보드에 "Live Validation 준비 상태" 카드 + "Preflight Checklist" + "사고 방지 경고 배너" 추가.
- 신규 read-only endpoint (`GET /ops/preflight`, `GET /ops/checklist`) 로 운영 상태 노출.
- README 의 운영자용 runbook (한국어) 보강.
- 위험 설정 (`live_trading_enabled=true` / `allow_market_orders=true` / `secret_exposed=true`) 감지 시 dashboard 배너 escalation.
- 기존 paper / dry-run / simulation 회귀 0 건.

본 작업의 핵심 안전 원칙: **`live_validation_ready=true` 가 표시된다고 해도 실제 live 주문은 절대 발생하지 않는다**. ready 플래그는 UX 신호일 뿐 코드 단의 새 가드를 푸는 게이트가 아니다.

## 2. 작업 범위

포함:

- **Backend (read-only, 새 endpoint)**:
  - `app/ops/__init__.py` (NEW, 패키지 표시).
  - `app/ops/preflight.py` (NEW) — pure-function 형태의 preflight 평가 로직. `compute_live_validation_status(settings, paper_engine, kis_broker)` 가 모든 플래그 + checklist 항목을 dict 로 반환.
  - `app/api/routes.py` (좁은 추가) — `GET /ops/status` + `GET /ops/preflight` 두 read-only endpoint. 기존 endpoint 본문 무변동.
  - `app/config.py` (선택 / 좁은 추가) — `live_validation_daily_loss_limit_usd: Decimal | None = None`, `live_validation_max_orders_per_day: int | None = None` 두 settings 필드 (default None, 옵션). 환경변수 `LIVE_VALIDATION_DAILY_LOSS_LIMIT_USD` / `LIVE_VALIDATION_MAX_ORDERS_PER_DAY` 로 옵트인. 본 settings 는 **status-reporting only** — 코드 어디서도 이 값을 enforcement 게이트로 사용하지 않는다. checklist 가 "configured / not configured" 로만 표시.
  - **새 settings 도 본 job 에서 enforcement 코드를 작성하지 않는다.** future job 에서 실 enforcement 추가 시까지는 operator-side reminder 역할.

- **Frontend (한국어 dashboard 보강)**:
  - `app/static/dashboard.html` 에 3 개 신규 섹션 + 1 개 escalating 배너 추가:
    1. **사고 방지 경고 배너** (상단, 항상 표시): "현재 시스템은 paper / dry-run 전용입니다. live trading 은 비활성화되어 있으며, 실제 주문은 전송되지 않습니다." 위험 플래그 감지 시 강한 경고 텍스트로 escalate.
    2. **"🛡️ Live Validation 준비 상태" 카드**: request §1 의 12 개 플래그 + `live_validation_ready` boolean.
    3. **"✅ Preflight Checklist" 카드**: request §2 의 14 개 항목, 각각 ✅/❌/⚠️ 표시 + 한국어 설명.
  - 기존 dashboard 의 paper simulation / dry-run / report 영역 무변동.
  - **신규 버튼 절대 금지**: live arm / live enable / KIS_ORDER_DRY_RUN toggle / allow_market_orders toggle 모두 추가 금지.

- **운영 문서 (README)**:
  - `projects/paper-trading/README.md` 에 한국어 "운영자 가이드" 섹션 추가:
    - 초보자용 실행 순서 (`scripts/start_server.sh` → `/dashboard` 접속).
    - paper simulation / dry-run / report 실행 방법 (기존 + 새 ops endpoints 인용).
    - **"live validation 전에 반드시 확인할 것"** 체크리스트 (preflight checklist 의 텍스트 버전).
    - **"live validation 은 아직 실제 실행 단계가 아니라는 설명"** 명시.
    - 실거래 전환 전 필요한 조건 (Phase 5 의 향후 단계).

- **테스트**:
  - `tests/test_ops_preflight.py` (NEW) — preflight 로직 회귀 (각 플래그별 ready=False 트리거 / happy path / secret leak / banner escalation).
  - `tests/test_ops_endpoints.py` (NEW) — TestClient 로 `/ops/status` / `/ops/preflight` 응답 검증.
  - `tests/test_dashboard.py` (narrow) — 신규 섹션 헤더 / 배너 텍스트 / 금지 버튼 부재 회귀.
  - `tests/test_api_paper_status.py` (narrow, 가능하면 변경 없음) — 기존 회귀 보존.

제외 (절대 안 하는 것):

- live trading 활성화 코드 추가.
- live order 버튼 / live arm 버튼 / `KIS_ORDER_DRY_RUN=false` toggle / `ALLOW_MARKET_ORDERS=true` toggle UI 추가.
- 실전 주문 endpoint 사용 / 실계좌 주문 전송 코드.
- `KisBroker.place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` 본문 변경. (paper-only 분기 모두 그대로 유지.)
- `validate_kis_order_request` / `_validate_paper_settings` / `OrderType.MARKET` 가드 / `OrderType.STOP` / FX 변환 도입.
- KIS endpoint / TR ID / payload / header 추측. catalog 미확인 값 사용.
- 외부 HTTP 라이브러리 import.
- Strategy / Agent / LLM 의 broker 직접 호출.
- OMS / RiskEngine 우회.
- `.env` 읽기 / 수정. `.env.example` 변경.
- 실 secret / 계좌번호 / token / Bearer 코드/문서/테스트/patch 기록.
- 자동 git commit / push / merge / deploy.

## 3. 수정해야 할 파일

| 경로 | 변경 종류 | 요약 |
| --- | --- | --- |
| `app/ops/__init__.py` | NEW | `from app.ops.preflight import compute_live_validation_status`. 패키지 표시. |
| `app/ops/preflight.py` | NEW | preflight 평가 pure functions. ~150 줄. |
| `app/api/routes.py` | MODIFY (좁은 추가) | `GET /ops/status` + `GET /ops/preflight` 두 read-only endpoint 추가. 기존 endpoint 본문 무변동. |
| `app/config.py` | MODIFY (좁은 추가) | `live_validation_daily_loss_limit_usd: Decimal \| None = None` + `live_validation_max_orders_per_day: int \| None = None` 추가. `load_settings()` 에서 env 옵트인 로딩 (값 없으면 None). 기존 필드 무변동. |
| `app/static/dashboard.html` | MODIFY (좁은 추가) | 배너 + 2 개 신규 섹션 (Live Validation 준비 상태 / Preflight Checklist) + JS 함수 (`refreshOpsStatus` / `renderChecklist` / `escalateBanner`). 기존 섹션 무변동. |
| `projects/paper-trading/README.md` | MODIFY | "운영자 가이드 (한국어)" 절 추가. |
| `tests/test_ops_preflight.py` | NEW | preflight 로직 회귀 (~15 tests). |
| `tests/test_ops_endpoints.py` | NEW | TestClient 기반 endpoint 회귀 (~8 tests). |
| `tests/test_dashboard.py` | MODIFY (좁은 추가) | 신규 섹션 / 배너 / 금지 버튼 부재 회귀. 기존 단언 무변동. |
| `docs/ai/jobs/live-validation-001/patch.md` | NEW (Codex 작성) | 결과 보고. |

**손대지 않는 파일**:

- `app/broker/*` 전부 (kis.py / kis_http.py / paper.py / alpaca_paper.py / base.py / kis_token_cache.py / kis_quote_mapper.py).
- `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/domain/*`.
- `app/api/server.py` (paper engine wiring 무변동).
- `app/main.py`.
- `docs/kis/MISSING_OFFICIAL_VALUES.md`.
- `.env`, `.env.example`.
- 모든 기존 test (단 `test_dashboard.py` 의 narrow 추가는 예외 — 새 섹션 회귀를 위해).

**범위 확장 사유 (UI + backend 혼합)**:

- 본 시리즈의 기존 원칙은 "GUI + backend 를 한 job 에 섞지 마" 였다. 그러나 본 request body 는 명시적으로 두 영역을 함께 다루고 (대시보드 + ops endpoint), preflight readiness 는 그 둘이 함께 있어야 의미가 있다 — backend 만으로는 운영자가 못 보고, frontend 만으로는 ready 계산 근거가 없다. 따라서 본 job 은 의도된 "mixed UX prep" job. 단 broker / OMS / Risk 등 위험 영역은 일체 건드리지 않는다.

## 4. Codex 구현 지시문

자세한 단계는 `codex-task.md` 에 기록. 요지:

### 4.1 `app/ops/preflight.py` 구조

```python
"""Live validation preflight evaluation (read-only)."""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from app.config import Settings
from app.domain.enums import TradingMode


@dataclass(frozen=True)
class PreflightItem:
    key: str          # e.g. "paper_mode_confirmed"
    label_ko: str     # e.g. "Paper mode 확인"
    passed: bool
    detail_ko: str    # e.g. "trading_mode=paper"


@dataclass(frozen=True)
class LiveValidationStatus:
    live_trading_enabled: bool
    trading_mode: str
    market_orders_allowed: bool
    kis_order_dry_run: bool
    kill_switch_engaged: bool
    broker_type: str
    kis_config_loaded: bool
    kis_authenticated: bool
    kis_market_data_available: bool
    kis_account_loaded: bool
    kis_order_entry_ready: bool
    live_validation_ready: bool
    banner_level: str          # "info" | "warning" | "danger"
    banner_text_ko: str
    items: tuple[PreflightItem, ...]


def compute_live_validation_status(
    *,
    settings: Settings,
    paper_engine,
    kis_broker,
    paper_status_payload: dict[str, Any],
) -> LiveValidationStatus:
    ...
```

- 모든 flag 는 `paper_status_payload` (기존 `/paper/status` 응답을 통과시키는 방식) 또는 settings / paper_engine / kis_broker 에서 직접 derive.
- `live_validation_ready` 는 ALL of:
  - `settings.trading_mode == TradingMode.PAPER`
  - `settings.live_trading_enabled is False`
  - `settings.allow_market_orders is False`
  - `settings.kis_order_dry_run is True`
  - `not settings.kill_switch_engaged`
  - `bool(settings.kis_account_no and settings.kis_app_key and settings.kis_app_secret)`
  - `secret_exposed is False` (always False in our system; included for explicit check)
  - `paper_engine.journal.trades` 또는 `dry_run_controller.summary().counters.ticks_total > 0` (최근 paper 결과 존재 증거)
- `banner_level`:
  - `"danger"` if `live_trading_enabled=True` or `allow_market_orders=True` or `secret_exposed=True`.
  - `"warning"` if `kill_switch_engaged=True` or `kis_authenticated=False` (with KIS config present).
  - `"info"` otherwise.
- `items` (14 개):
  - `paper_mode_confirmed` — trading_mode == "paper"
  - `live_disabled_confirmed` — live_trading_enabled is False
  - `market_orders_disabled_confirmed` — allow_market_orders is False
  - `kis_dry_run_enabled_confirmed` — kis_order_dry_run is True
  - `secret_exposed_false_confirmed` — secret_exposed is False
  - `kill_switch_off_confirmed` — kill_switch_engaged is False
  - `kis_config_loaded_confirmed` — kis_config_loaded is True
  - `dashboard_simulation_available` — server has paper_engine + risk + oms 객체 가능
  - `paper_journal_writable` — `paper_engine.journal` 존재 여부
  - `report_generation_available` — `dry_run_controller` 존재 여부
  - `daily_loss_limit_configured` — `settings.live_validation_daily_loss_limit_usd is not None`
  - `max_orders_per_day_configured` — `settings.live_validation_max_orders_per_day is not None`
  - `symbol_allowlist_configured` — `len(settings.symbol_allowlist) > 0`
  - `recent_test_passed_manual` — 수동 확인 항목 (`passed=False` default, label 에 "수동 확인 필요" 명시)

### 4.2 `GET /ops/status` 와 `GET /ops/preflight`

```python
@router.get("/ops/status")
def ops_status(request: Request) -> dict[str, Any]:
    # Reuse existing /paper/status payload internally.
    paper_payload = paper_status(request)
    settings = request.app.state.settings
    paper_engine = getattr(request.app.state, "paper_engine", None)
    kis_broker = getattr(request.app.state, "kis_broker", None)
    status = compute_live_validation_status(
        settings=settings,
        paper_engine=paper_engine,
        kis_broker=kis_broker,
        paper_status_payload=paper_payload,
    )
    return _serialize_live_validation_status(status, include_checklist=False)


@router.get("/ops/preflight")
def ops_preflight(request: Request) -> dict[str, Any]:
    paper_payload = paper_status(request)
    settings = request.app.state.settings
    paper_engine = getattr(request.app.state, "paper_engine", None)
    kis_broker = getattr(request.app.state, "kis_broker", None)
    status = compute_live_validation_status(
        settings=settings,
        paper_engine=paper_engine,
        kis_broker=kis_broker,
        paper_status_payload=paper_payload,
    )
    return _serialize_live_validation_status(status, include_checklist=True)
```

응답 dict 에는 항상 `secret_exposed: False` 포함. `account_no_masked` 는 기존 `paper_status` 의 값 재사용. 실제 secret 값 (settings.kis_app_key / kis_app_secret / kis_account_no) 절대 응답에 포함되지 않음.

### 4.3 Dashboard HTML 보강

추가할 섹션 (기존 섹션 사이에 삽입):

1. **상단 배너** (`<body>` 첫 직접 자식, 모든 섹션 전에):

   ```html
   <div id="ops-banner" class="banner banner-info" role="status">
     <strong>현재 시스템은 paper / dry-run 전용입니다.</strong>
     live trading 은 비활성화되어 있으며, 실제 주문은 전송되지 않습니다.
   </div>
   ```

   JS 가 `/ops/status` 응답의 `banner_level` 에 따라 `class` 를 `banner-info` / `banner-warning` / `banner-danger` 로 교체하고 `banner_text_ko` 로 본문 갱신.

2. **"🛡️ Live Validation 준비 상태" 카드** (KIS status 섹션 직후):

   ```html
   <section id="live-validation-readiness">
     <h2>🛡️ Live Validation 준비 상태</h2>
     <p class="muted">아래 상태는 read-only 입니다. live 활성화는 별도 절차로만 가능합니다.</p>
     <table><!-- 12 행 --></table>
   </section>
   ```

3. **"✅ Preflight Checklist" 카드** (Live Validation 카드 직후):

   ```html
   <section id="preflight-checklist">
     <h2>✅ Preflight Checklist</h2>
     <ul id="preflight-items"><!-- JS 가 채움 --></ul>
   </section>
   ```

CSS (`<style>` 추가):

```css
.banner { padding: 1em; margin-bottom: 1em; border-radius: 6px; font-size: 1em; }
.banner-info { background: #e3f2fd; color: #0d47a1; border: 1px solid #90caf9; }
.banner-warning { background: #fff3e0; color: #e65100; border: 2px solid #ffb74d; }
.banner-danger { background: #ffebee; color: #b71c1c; border: 3px solid #ef5350; font-weight: bold; }
.check-pass { color: #2e7d32; }
.check-fail { color: #c62828; }
.check-warn { color: #ef6c00; }
.muted { color: #666; font-size: 0.9em; }
```

JS:

```javascript
async function refreshOpsStatus() {
  const ops = await fetchJson("/ops/preflight");
  setText("lv-live-trading-enabled", boolKo(ops.live_trading_enabled, "위험", "비활성"));
  setText("lv-trading-mode", ops.trading_mode);
  // ... 12 flags
  setText("lv-validation-ready", boolKo(ops.live_validation_ready, "READY", "NOT READY"));
  const banner = document.getElementById("ops-banner");
  banner.className = "banner banner-" + ops.banner_level;
  banner.querySelector("strong").textContent = ops.banner_level === "danger" ? "⚠️ 위험" : "ℹ️ 안내";
  banner.insertAdjacentText("beforeend", ops.banner_text_ko);
  renderChecklist(ops.items);
}
function renderChecklist(items) {
  const ul = document.getElementById("preflight-items");
  ul.innerHTML = "";
  for (const item of items) {
    const li = document.createElement("li");
    li.className = "check-" + (item.passed ? "pass" : "fail");
    li.textContent = (item.passed ? "✅ " : "❌ ") + item.label_ko + " — " + item.detail_ko;
    ul.appendChild(li);
  }
}
```

`ENDPOINTS` map 에 `opsStatus: "/ops/status"`, `opsPreflight: "/ops/preflight"` 추가.

**절대 추가 금지** (현재 dashboard 에 없음 + 본 job 에서도 도입 금지):

- `<button id="btn-arm-live">` / `<button id="btn-disable-dry-run">` / `<button id="btn-allow-market">` 같은 위험 토글.
- `POST /ops/*` 또는 `PUT /ops/*` (mutating endpoint). 본 job 의 모든 ops endpoint 는 GET only.

### 4.4 README 운영자 가이드

`projects/paper-trading/README.md` 끝에 추가:

```markdown
## 운영자 가이드 (한국어)

### 초보자 실행 순서

1. `scripts/start_server.sh` 실행.
2. 브라우저에서 `http://127.0.0.1:8000/dashboard` 접속.
3. 상단 배너 색깔 확인: 파랑 (안내) = 정상.
4. "Live Validation 준비 상태" 카드의 `live_validation_ready` 가 READY 인지 확인.
5. "Preflight Checklist" 의 모든 ✅ 확인.

### Paper Simulation

- "수동 모의 주문" 또는 "바로 모의테스트 해보기" 영역에서 `예시 모의 주문 실행`.
- 결과는 한국어로 표시되며 raw JSON 은 `원본 JSON 보기` 안에 숨김.

### Dry-run

- "Dry-run 시작" 버튼으로 시작.
- "Dry-run 중지" 로 정지.
- "최신 리포트 보기" 로 결과 확인.

### Live Validation 전에 반드시 확인할 것

1. Preflight Checklist 14 개 모두 ✅.
2. `live_validation_ready: READY` 확인.
3. `live_trading_enabled=false` 확인.
4. `KIS_ORDER_DRY_RUN=true` 확인.
5. `ALLOW_MARKET_ORDERS=true` 가 거부되는지 (`load_settings()` ValueError 확인).
6. `kill_switch_engaged=false` 확인.
7. paper journal 에 최근 fill 기록이 있는지.
8. dry-run report 의 summary 가 정상.

### 중요 — live validation 은 아직 실제 실행 단계가 아닙니다

본 시스템은 `live_validation_ready=READY` 가 표시되어도 **실제 live 주문을 전송할 코드 경로를 보유하지 않습니다**. live 활성화는 별도 신규 job (`live-validation-002` 등) 에서 사용자 명시 승인 후에만 가능하며, 다음 추가 요건이 충족되어야 합니다:

- 별도 manual arm 메커니즘 (본 job 에서 만들지 않음).
- 사용자 명시 승인 (구두/문서).
- 소액 한도 / 종목 whitelist / daily loss limit 가 코드 레벨에서 enforce.
- KIS 실전 환경 검증 (mock 아닌 sandbox 또는 별도 단계).
- 모든 회귀 테스트 + 1 회 이상의 paper soak 정상 종료.

### 실거래 전환 전 필요한 조건

[Phase 5+ 의 향후 작업으로 별도 plan 필요. 현재 본 시스템에서는 실거래 코드 경로 0 줄.]
```

### 4.5 `app/config.py` 좁은 추가

```python
@dataclass(frozen=True)
class Settings:
    # ... 기존 필드 ...
    live_validation_daily_loss_limit_usd: Decimal | None = None
    live_validation_max_orders_per_day: int | None = None
```

`load_settings()` 안:

```python
return Settings(
    # ... 기존 ...
    live_validation_daily_loss_limit_usd=_optional_decimal_env("LIVE_VALIDATION_DAILY_LOSS_LIMIT_USD"),
    live_validation_max_orders_per_day=_optional_int_env("LIVE_VALIDATION_MAX_ORDERS_PER_DAY"),
)
```

새 helper:

```python
def _optional_decimal_env(name: str) -> Decimal | None:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return None
    try:
        return Decimal(raw)
    except InvalidOperation as exc:
        raise ValueError(f"Invalid decimal for {name}") from exc

def _optional_int_env(name: str) -> int | None:
    raw = os.getenv(name)
    if raw is None or raw == "":
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for {name}") from exc
```

**중요**: 이 두 settings 는 **어떤 코드 경로에서도 enforcement 로 사용되지 않는다**. preflight checklist 의 "configured / not configured" 표시 전용. Future job 에서 enforce 추가 시까지 operator-side reminder. `.env.example` 에 추가하지 않음 (request §"절대 하지 말 것").

## 5. 테스트 기준

신규 `tests/test_ops_preflight.py` (~15 tests):

1. `test_status_includes_all_twelve_flags` — 12 개 플래그 모두 응답에 포함.
2. `test_ready_true_with_clean_paper_state` — paper / live=False / dry_run=True / no kill switch + KIS config + 최근 paper fill 있을 때 ready=True.
3. `test_ready_false_when_live_trading_enabled` — `live_trading_enabled=True` 시 ready=False + banner_level="danger".
4. `test_ready_false_when_market_orders_allowed` — `allow_market_orders=True` 시 ready=False + banner danger.
5. `test_ready_false_when_kis_dry_run_disabled` — `kis_order_dry_run=False` 시 ready=False.
6. `test_ready_false_when_kill_switch_engaged` — kill switch on 시 ready=False + banner warning.
7. `test_ready_false_when_kis_config_missing` — `kis_app_key/secret/account_no` 중 하나 누락 시 ready=False.
8. `test_ready_false_when_no_recent_simulation` — paper_engine.journal.trades empty + dry_run ticks_total=0 시 ready=False.
9. `test_checklist_items_count_is_fourteen` — 정확히 14 개 item.
10. `test_checklist_daily_loss_limit_configured_via_settings` — settings 의 limit 설정 시 item passed=True.
11. `test_checklist_max_orders_per_day_configured_via_settings`.
12. `test_checklist_symbol_allowlist_configured_when_nonempty`.
13. `test_banner_text_changes_with_level` — banner_text_ko 가 level 에 따라 다른 한국어 텍스트.
14. `test_status_does_not_leak_secrets` — response dict 에 settings.kis_app_key / kis_app_secret / kis_account_no 원문 absent.
15. `test_recent_test_passed_manual_item_default_false` — 수동 확인 항목은 default `passed=False` 로 표시되어 운영자에게 명시.

신규 `tests/test_ops_endpoints.py` (~8 tests):

1. `test_get_ops_status_returns_200_with_all_flags` — TestClient 로 `/ops/status` 호출, 200 + 12 flags + banner_level/text 존재. checklist 미포함.
2. `test_get_ops_preflight_returns_200_with_checklist` — `/ops/preflight` 호출, 14 개 checklist item 포함.
3. `test_ops_endpoints_are_get_only` — `POST /ops/status` / `POST /ops/preflight` → 405 Method Not Allowed (FastAPI 기본 동작).
4. `test_ops_endpoints_do_not_expose_secrets` — 응답 텍스트에 `KIS_APP_KEY` / `KIS_APP_SECRET` / `KIS_ACCOUNT_NO` / `app_secret` / `access_token` / `Bearer ` 부재.
5. `test_ops_endpoints_have_no_mutating_paths` — `app/api/routes.py` 파일 텍스트에 `@router.post("/ops/`, `@router.put("/ops/`, `@router.delete("/ops/` 등 mutating 라우트 부재 회귀.
6. `test_ops_banner_escalates_on_live_trading_enabled` — TestClient + monkeypatch env 로 `LIVE_TRADING_ENABLED=true` 설정 시 (단 load_settings 의 reject 가 먼저 발동 — 본 테스트는 reject 경로 회귀).
7. `test_ops_banner_escalates_on_market_orders_allowed` — 동일 (load_settings reject 회귀).
8. `test_ops_preflight_recent_simulation_signal` — paper 1 회 simulate 후 `recent_simulation_or_dry_run_present` 항목이 passed=True 로 전환.

`tests/test_dashboard.py` (narrow 추가, 기존 단언 무변동):

- `test_dashboard_has_live_validation_readiness_section` — HTML 본문에 `"Live Validation 준비 상태"` 텍스트.
- `test_dashboard_has_preflight_checklist_section` — `"Preflight Checklist"` 텍스트.
- `test_dashboard_has_safety_banner` — `"paper / dry-run 전용입니다"` 텍스트.
- `test_dashboard_has_no_live_arm_button` — `id="btn-arm-live"` / `id="btn-disable-dry-run"` / `id="btn-allow-market"` / `id="btn-enable-live"` 부재 회귀.

회귀 / 안전 회귀 (기존 테스트 무변동):

- `test_paper_e2e_api.py` 의 21 개 함수 모두 통과 — paper simulation / dry-run / report UX 무변동.
- `test_api_paper_status.py` 의 모든 함수 통과 — `/paper/status` 응답 무변동.
- `test_kis_*` 모든 회귀 통과 — KIS adapter 본문 무변동.
- `test_paper_e2e_pipeline.py` 의 9 개 함수 통과 — Strategy → Risk → OMS → Broker 경로 무변동.
- 안전 grep: `app/strategy/*` 의 `app.broker.*` import 0, 외부 HTTP 라이브러리 import 0, 실전 TR_ID 0, 본 시리즈 출력에 secret leak 0.

전체 pytest 카운트 예상: 520 baseline + ~26 신규 = ~546 passed.

## 6. 리뷰 체크리스트

안전 회귀:

- [ ] live trading 활성화 코드 / live arm UI / live order 버튼 / `KIS_ORDER_DRY_RUN=false` toggle / `ALLOW_MARKET_ORDERS=true` toggle UI 추가 없음.
- [ ] `KisBroker.place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` 본문 무변동.
- [ ] `validate_kis_order_request` / `_validate_paper_settings` / `OrderType.MARKET` 가드 / `OrderType.STOP` 미도입 / FX 변환 미도입.
- [ ] KIS endpoint / TR ID / payload / header / response field 추측 0.
- [ ] 외부 HTTP 라이브러리 import 0.
- [ ] Strategy / Agent / LLM 의 broker 직접 호출 추가 없음.
- [ ] OMS / RiskEngine 우회 없음.
- [ ] `app/broker/*`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/domain/*`, `app/api/server.py`, `app/main.py`, `docs/kis/MISSING_OFFICIAL_VALUES.md`, `.env`, `.env.example` 무변동.

스코프 / 동작:

- [ ] `app/ops/preflight.py` 의 `compute_live_validation_status` 가 pure function — settings / paper_engine / kis_broker / paper_status_payload 4 인자만 받음. 부수효과 0.
- [ ] `live_validation_ready` 가 8 개 AND 조건 충족 시에만 True. 하나라도 False 면 ready=False.
- [ ] `live_validation_ready=True` 가 표시되더라도 실제 live 주문 코드 경로 0 줄 — UI 신호일 뿐.
- [ ] `GET /ops/status` 와 `GET /ops/preflight` 모두 read-only. POST/PUT/DELETE 0.
- [ ] 응답 dict 에 settings.kis_app_key / kis_app_secret / kis_account_no 원문 absent. `account_no_masked` 만.
- [ ] Dashboard 배너 escalation 이 위험 플래그 감지 시 `banner-danger` class + 강한 한국어 텍스트.
- [ ] Dashboard 에 신규 위험 토글 버튼 absent.
- [ ] 기존 paper simulation / dry-run / report / 한국어 UX 회귀 0.
- [ ] `app/config.py` 의 2 개 신규 settings 가 enforcement 게이트로 쓰이지 않음 (코드 어디서도 `settings.live_validation_*` 읽고 차단하지 않음 — 단지 status reporting 전용).

테스트 / 문서:

- [ ] `compileall app tests` PASS.
- [ ] `pytest -p no:cacheprovider` 전체 PASS. baseline 520 + ~26 신규 = ~546 expected.
- [ ] 신규 `tests/test_ops_preflight.py` + `tests/test_ops_endpoints.py` 가 모든 ready=False 트리거 + secret leak + banner level + GET-only 회귀를 검증.
- [ ] `tests/test_dashboard.py` 의 좁은 추가는 신규 섹션 / 배너 / 금지 버튼 부재만 검증. 기존 단언 무변동.
- [ ] README 의 "운영자 가이드 (한국어)" 절이 추가됐고, "live validation 은 아직 실제 실행 단계가 아닙니다" 가 명시됨.
- [ ] `patch.md` 에 수정 파일 / 표시 방식 / checklist 항목 / 실 live 주문 불가능한 이유 / secret 회귀 / live trading off 회귀 / market order guard 유지 / 테스트 결과 / Claude 검증 프롬프트 / Follow-up Codex 프롬프트 작성 규칙 모두 포함.

자동화 금지:

- [ ] commit / push / merge / PR / deploy 수행 없음.
- [ ] `.env` / secret / credential / API key / token 수정 / 노출 없음.
