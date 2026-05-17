## 1. 요청 요약

브라우저로 paper-trading 서버의 상태/dry-run 운영을 한 화면에서 볼 수 있는 **단일 HTML 대시보드** (`GET /dashboard`)를 추가한다. 외부 프론트엔드 프레임워크 없이 단일 파일(`app/static/dashboard.html`) + inline CSS/JS로 최소 구현. `fetch`로 mvp-018/019에서 만든 안전 endpoint만 호출. 실제 주문/live/시장가 버튼은 **만들지 않는다**.

### 안전 원칙 (mvp-005~mvp-020 누적 유지)

- live trading 활성화 금지. 대시보드에 live 토글/실주문/시장가 버튼 **없음**.
- `OrderType.MARKET` 부재 유지(코드 미변경).
- 외부 HTTP 라이브러리/외부 CDN/외부 JS framework 추가 금지(inline only, fetch only).
- KIS endpoint URL/TR ID/payload 추가 금지.
- 실제 KIS app key/secret/account/token이 HTML/JS/응답 어디에도 미포함. 대시보드는 서버가 이미 sanitize한 상태 응답(`secret_exposed: false`, `account_no_masked`, `kis_*_loaded` bool flags)만 표시.
- `app/` 도메인/broker/oms/risk/strategy/runtime/config 코드 변경 0건.
- `git commit`/`push`/`merge`/`deploy` 자동화 금지.
- `pip install` 실행 금지.
- 임의 shell 명령 입력 UI/API 신설 금지.

### 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기존 181 + 신규 약 6–8개 모두 PASS.

## 2. 작업 범위

### 포함 (In scope)

`projects/paper-trading/` 아래:

- **`app/static/dashboard.html` (신규)** — 단일 자가 완결 파일. inline `<style>` + inline `<script>`. 외부 CDN/라이브러리 없음. 4개 섹션(Paper 상태 / KIS 상태 / Dry-run 상태 / 최신 리포트) + 6개 버튼. 모든 `fetch` 호출은 동일-origin 상대 경로(`/paper/status`, `/paper/dry-run/{start,tick,stop,status}`, `/reports/dry-run/{analyze,latest}`)만.
- **`app/api/routes.py` (수정)** — `GET /dashboard` endpoint 추가. `HTMLResponse(path("app/static/dashboard.html").read_text(...))` 패턴. 또는 module load 시 한 번 읽어 메모리 cache(테스트 격리 위해 매 요청 read도 OK — 파일 사이즈 작음).
- **`projects/paper-trading/README.md` (수정)** — 짧은 한 단락 추가: 대시보드 URL + 안전 가드 안내.
- **신규 테스트** `tests/test_dashboard.py`:
  - 200 + text/html 응답
  - 4개 섹션 헤더 + 6개 버튼 라벨 존재
  - 금지 패턴 부재(`KIS_APP_KEY`/`KIS_APP_SECRET`/`KIS_ACCOUNT_NO`, "live trading 활성화" 토글 류, market order submit form, `/paper/run` URL 호출)
  - `fetch(...)` URL이 화이트리스트에만 등장
  - safety 안내 텍스트(paper / dry-run only) 존재
- **`docs/ai/jobs/mvp-021/patch.md` (신규)** — Codex 변경 요약.

### 제외 (Out of scope; 절대 만지지 않음)

- 실제 주문 / HTTP / Strategy / OMS / RiskEngine / Broker 코드 변경.
- live trading 활성화 UI/엔드포인트.
- 시장가 주문 UI/엔드포인트.
- `/paper/run`을 대시보드에서 호출(이 endpoint는 caller가 snapshots 임의 주입 가능 — 초보자용 대시보드에는 부적합).
- KIS endpoint URL/TR ID/payload.
- 외부 JS framework / CDN / 외부 의존성.
- `StaticFiles` mount(파일이 1개라 endpoint가 직접 읽으면 충분).
- `app/broker/*`, `app/runtime/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*` 변경.
- `app/config.py`, `Settings`, `.env.example`, 프로젝트/루트 `.gitignore` 변경.
- mvp-001..mvp-020 산출물 변경.
- `web/`, `prompts/`, `scripts/`(루트), `imports/`, 기존 `docs/`(`docs/ai/jobs/mvp-021/` 외) 변경.
- 자동 commit/push/merge/deploy.
- 임의 shell 명령 입력 UI/API 신설.

### 안전 가드

- 대시보드 HTML은 **하나의 외부 fetch URL 화이트리스트만** 호출. 테스트가 `fetch(...)` 정규식 추출 + 화이트리스트 비교로 검증.
- credentials 표시 금지: 대시보드는 server JSON 응답의 sanitize된 필드(`*_masked`, `*_loaded` bool, `secret_exposed: false`)만 렌더. 응답을 그대로 `<pre>`에 뿌리면 OK(서버가 이미 sanitize했고, `secret_exposed: false`가 명시되어 있음).
- "안전 가드 안내" 한 줄(빨간색): "paper / dry-run only · live trading disabled · market orders disabled · no real orders" 명시.
- live/market 관련 버튼 부재 — 테스트가 검증.

## 3. 수정해야 할 파일

### 신규

| 파일 | 목적 |
| --- | --- |
| `app/static/dashboard.html` | 단일 HTML+CSS+JS |
| `tests/test_dashboard.py` | endpoint + 안전 검증 |
| `docs/ai/jobs/mvp-021/patch.md` | Codex 변경 요약 |

### 수정

| 파일 | 변경 내용 |
| --- | --- |
| `app/api/routes.py` | `GET /dashboard` 엔드포인트 + import `HTMLResponse` |
| `README.md` | 대시보드 한 단락 |

### 절대 미수정

- `app/api/server.py` (lifespan 변경 없음)
- `app/config.py`, `app/main.py`
- `app/broker/*`, `app/runtime/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*`
- `.env.example`, 프로젝트 `.gitignore`, 루트 `.gitignore`
- mvp-001..mvp-020 산출물
- `scripts/`(mvp-020 산출물), `imports/`, `web/`, `prompts/`

## 4. Codex 구현 지시문

### 4.1 사전 점검

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m pytest -p no:cacheprovider --co -q 2>&1 | tail -3
# expect: 181+ tests collected

grep -q "paper/dry-run/start" app/api/routes.py && echo "OK dry-run routes"
grep -q "reports/dry-run/analyze" app/api/routes.py && echo "OK reports routes"
grep -q "paper/status" app/api/routes.py && echo "OK paper/status"
test -d .venv && echo "OK venv"
test -d app/static && echo "WARN app/static exists" || echo "OK app/static absent (will be created)"
```

위 5개 OK → 진행.

### 4.2 `app/static/dashboard.html` (신규)

단일 자가 완결 HTML. 외부 CDN/라이브러리 없음. 인라인 CSS + 인라인 JS. 다음 구조를 그대로 따른다(섹션 ID/라벨/fetch URL을 테스트가 검증함).

```html
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<title>Paper Trading Dashboard (mvp-021)</title>
<style>
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; max-width: 1000px; margin: 1rem auto; padding: 0 1rem; color: #222; }
  h1 { font-size: 1.4rem; margin-bottom: .25rem; }
  .safety-banner { background: #fff3f3; border: 1px solid #f3b6b6; color: #a40000; padding: .5rem .75rem; border-radius: 4px; margin-bottom: 1rem; font-weight: 600; }
  .button-row { display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: 1rem; }
  .button-row button { padding: .5rem .75rem; border: 1px solid #888; background: #f3f3f3; cursor: pointer; border-radius: 4px; }
  .button-row button:hover { background: #e7e7e7; }
  section { border: 1px solid #ddd; padding: .5rem .75rem; margin-bottom: 1rem; border-radius: 4px; }
  section h2 { font-size: 1.05rem; margin: 0 0 .5rem; }
  table { width: 100%; border-collapse: collapse; font-size: .9rem; }
  table th { text-align: left; width: 38%; color: #555; font-weight: 500; padding: .25rem .5rem; border-bottom: 1px solid #f0f0f0; }
  table td { padding: .25rem .5rem; border-bottom: 1px solid #f0f0f0; font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }
  pre { background: #f7f7f7; padding: .5rem; border-radius: 4px; overflow-x: auto; font-size: .8rem; max-height: 280px; }
  .log { color: #555; font-size: .85rem; margin-top: .5rem; }
  .ok { color: #0a7d2c; }
  .warn { color: #a96a00; }
  .bad { color: #a40000; }
</style>
</head>
<body>
<h1>Paper Trading Dashboard</h1>
<div class="safety-banner">paper / dry-run only · live trading disabled · market orders disabled · no real orders</div>

<div class="button-row">
  <button id="btn-refresh">상태 새로고침</button>
  <button id="btn-start-dry-run">Dry-run 시작</button>
  <button id="btn-tick">Tick 1회 실행</button>
  <button id="btn-stop-dry-run">Dry-run 중지</button>
  <button id="btn-analyze">리포트 분석</button>
  <button id="btn-latest">최신 리포트 보기</button>
</div>

<section id="paper-status-section">
  <h2>Paper trading 상태</h2>
  <table>
    <tr><th>mode</th><td id="ps-mode">-</td></tr>
    <tr><th>live_enabled</th><td id="ps-live-enabled">-</td></tr>
    <tr><th>market_orders_allowed</th><td id="ps-market">-</td></tr>
    <tr><th>kis_order_dry_run</th><td id="ps-kis-dry-run">-</td></tr>
    <tr><th>secret_exposed</th><td id="ps-secret-exposed">-</td></tr>
  </table>
</section>

<section id="kis-status-section">
  <h2>KIS 상태</h2>
  <table>
    <tr><th>kis_config_loaded</th><td id="kis-config-loaded">-</td></tr>
    <tr><th>kis_authenticated</th><td id="kis-authenticated">-</td></tr>
    <tr><th>kis_account_loaded</th><td id="kis-account-loaded">-</td></tr>
    <tr><th>kis_market_data_available</th><td id="kis-market-data">-</td></tr>
    <tr><th>kis_order_entry_ready</th><td id="kis-order-entry-ready">-</td></tr>
    <tr><th>kis_last_error</th><td id="kis-last-error">-</td></tr>
  </table>
</section>

<section id="dry-run-status-section">
  <h2>Dry-run 상태</h2>
  <table>
    <tr><th>running</th><td id="dr-running">-</td></tr>
    <tr><th>started_at</th><td id="dr-started-at">-</td></tr>
    <tr><th>last_tick_at</th><td id="dr-last-tick-at">-</td></tr>
    <tr><th>ticks_total</th><td id="dr-ticks-total">-</td></tr>
    <tr><th>candidates_seen</th><td id="dr-candidates-seen">-</td></tr>
    <tr><th>candidates_blocked</th><td id="dr-candidates-blocked">-</td></tr>
    <tr><th>dry_run_orders_created</th><td id="dr-orders-created">-</td></tr>
    <tr><th>errors_total</th><td id="dr-errors-total">-</td></tr>
    <tr><th>last_error</th><td id="dr-last-error">-</td></tr>
  </table>
</section>

<section id="report-section">
  <h2>최신 리포트</h2>
  <div id="report-meta" class="log">-</div>
  <pre id="report-content">(아직 분석되지 않음)</pre>
</section>

<div id="log" class="log"></div>

<script>
"use strict";

const ENDPOINTS = {
  paperStatus: "/paper/status",
  dryRunStatus: "/paper/dry-run/status",
  dryRunStart: "/paper/dry-run/start",
  dryRunStop: "/paper/dry-run/stop",
  dryRunTick: "/paper/dry-run/tick",
  reportsAnalyze: "/reports/dry-run/analyze",
  reportsLatest: "/reports/dry-run/latest",
};

const logEl = document.getElementById("log");

function logMsg(msg) {
  const ts = new Date().toISOString();
  const line = document.createElement("div");
  line.textContent = "[" + ts + "] " + msg;
  logEl.prepend(line);
}

function setText(id, value) {
  const el = document.getElementById(id);
  if (!el) return;
  if (value === null || value === undefined) {
    el.textContent = "-";
  } else if (typeof value === "boolean") {
    el.textContent = value ? "true" : "false";
    el.className = value ? "ok" : "";
  } else {
    el.textContent = String(value);
  }
}

async function fetchJson(url, init) {
  const r = await fetch(url, init);
  let body = null;
  try { body = await r.json(); } catch (_) { body = null; }
  if (!r.ok) {
    const detail = body && body.detail ? body.detail : r.statusText;
    throw new Error(url + " → " + r.status + ": " + detail);
  }
  return body;
}

async function refreshAll() {
  try {
    const paper = await fetchJson(ENDPOINTS.paperStatus);
    setText("ps-mode", paper.mode);
    setText("ps-live-enabled", paper.live_enabled);
    setText("ps-market", paper.market_orders_allowed);
    setText("ps-kis-dry-run", paper.kis_order_dry_run);
    setText("ps-secret-exposed", paper.secret_exposed);
    setText("kis-config-loaded", paper.kis_config_loaded);
    setText("kis-authenticated", paper.kis_authenticated);
    setText("kis-account-loaded", paper.kis_account_loaded);
    setText("kis-market-data", paper.kis_market_data_available);
    setText("kis-order-entry-ready", paper.kis_order_entry_ready);
    setText("kis-last-error", paper.kis_last_error);
  } catch (e) {
    logMsg("paper/status error: " + e.message);
  }
  try {
    const dr = await fetchJson(ENDPOINTS.dryRunStatus);
    setText("dr-running", dr.running);
    setText("dr-started-at", dr.started_at);
    setText("dr-last-tick-at", dr.last_tick_at);
    const c = dr.counters || {};
    setText("dr-ticks-total", c.ticks_total);
    setText("dr-candidates-seen", c.candidates_seen);
    setText("dr-candidates-blocked", c.candidates_blocked);
    setText("dr-orders-created", c.dry_run_orders_created);
    setText("dr-errors-total", c.errors_total);
    setText("dr-last-error", c.last_error);
  } catch (e) {
    logMsg("dry-run/status error: " + e.message);
  }
}

async function startDryRun() {
  try {
    await fetchJson(ENDPOINTS.dryRunStart, { method: "POST", headers: { "content-type": "application/json" }, body: "{}" });
    logMsg("dry-run started");
  } catch (e) { logMsg("start error: " + e.message); }
  refreshAll();
}

async function stopDryRun() {
  try {
    await fetchJson(ENDPOINTS.dryRunStop, { method: "POST", headers: { "content-type": "application/json" }, body: "{}" });
    logMsg("dry-run stopped");
  } catch (e) { logMsg("stop error: " + e.message); }
  refreshAll();
}

async function tickOnce() {
  try {
    const r = await fetchJson(ENDPOINTS.dryRunTick, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ snapshots: [] }) });
    logMsg("tick " + (r.tick ? r.tick.status : "ok"));
  } catch (e) { logMsg("tick error: " + e.message); }
  refreshAll();
}

async function analyze() {
  try {
    const r = await fetchJson(ENDPOINTS.reportsAnalyze, { method: "POST", headers: { "content-type": "application/json" }, body: "{}" });
    document.getElementById("report-meta").textContent = "run_dir: " + (r.run_dir || "-");
    document.getElementById("report-content").textContent = JSON.stringify(r.summary || {}, null, 2);
    logMsg("analyze ok");
  } catch (e) { logMsg("analyze error: " + e.message); }
}

async function showLatest() {
  try {
    const r = await fetchJson(ENDPOINTS.reportsLatest);
    document.getElementById("report-meta").textContent = "run_dir: " + (r.run_dir || "-");
    document.getElementById("report-content").textContent = JSON.stringify(r.summary || {}, null, 2);
    logMsg("latest ok");
  } catch (e) { logMsg("latest error: " + e.message); }
}

document.getElementById("btn-refresh").addEventListener("click", refreshAll);
document.getElementById("btn-start-dry-run").addEventListener("click", startDryRun);
document.getElementById("btn-stop-dry-run").addEventListener("click", stopDryRun);
document.getElementById("btn-tick").addEventListener("click", tickOnce);
document.getElementById("btn-analyze").addEventListener("click", analyze);
document.getElementById("btn-latest").addEventListener("click", showLatest);

refreshAll();
</script>
</body>
</html>
```

핵심 불변식(테스트로 검증):

- 6개 버튼 라벨이 정확한 한국어 문자열.
- `ENDPOINTS` 객체의 URL은 화이트리스트 7개와 일치.
- 안전 banner "paper / dry-run only · live trading disabled · market orders disabled · no real orders" 포함.
- `KIS_APP_KEY` / `KIS_APP_SECRET` / `KIS_ACCOUNT_NO` 문자열 부재.
- "live trading 활성화" / "Enable live trading" / "Allow market orders" / "Submit real order" 같은 위험 라벨 부재.
- `<form action="...">` 부재(외부 사용자가 임의 POST 가능한 form 없음). 모든 트리거는 JS의 화이트리스트 fetch.

### 4.3 `app/api/routes.py` 변경

기존 import에 `HTMLResponse` 추가(없으면):

```python
from fastapi.responses import HTMLResponse
from pathlib import Path
```

새 핸들러를 파일 끝(또는 `/paper/status` 부근)에 추가:

```python
_DASHBOARD_HTML_PATH = Path(__file__).resolve().parents[1] / "static" / "dashboard.html"


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page() -> HTMLResponse:
    text = _DASHBOARD_HTML_PATH.read_text(encoding="utf-8")
    return HTMLResponse(content=text)
```

기존 핸들러는 한 줄도 바꾸지 마. import 외 다른 변경 없음.

### 4.4 README 변경

mvp-020 단락 뒤에 짧은 단락 추가(기존 단락 변경 금지):

```markdown
## 브라우저 대시보드 (mvp-021)

서버 실행 후 `http://127.0.0.1:8000/dashboard`에서 다음을 한 화면에 볼 수 있습니다.

- Paper trading 상태(`mode`, `live_enabled`, `market_orders_allowed`, `kis_order_dry_run`, `secret_exposed`)
- KIS 상태(`kis_config_loaded`, `kis_authenticated`, `kis_account_loaded`, `kis_market_data_available`, `kis_order_entry_ready`, `kis_last_error`)
- Dry-run 상태(`running`, `started_at`, `last_tick_at`, `ticks_total`, `candidates_seen`, `candidates_blocked`, `dry_run_orders_created`, `errors_total`, `last_error`)
- 최신 리포트 요약(`/reports/dry-run/latest`)

버튼: 상태 새로고침 / Dry-run 시작 / Tick 1회 실행 / Dry-run 중지 / 리포트 분석 / 최신 리포트 보기.

대시보드는 단일 HTML(`app/static/dashboard.html`) + inline JS로 외부 프레임워크/CDN 의존 없이 동작합니다. live trading 활성화 / 시장가 허용 / 실제 주문 같은 위험한 버튼은 없습니다. 모든 fetch 호출은 paper-trading 서버의 안전한 endpoint만 사용합니다(`/paper/status`, `/paper/dry-run/{start,tick,stop,status}`, `/reports/dry-run/{analyze,latest}`). 응답에 raw KIS app key/secret/계좌번호/token이 포함되지 않으며, 화면에는 마스킹된 / boolean flag만 표시됩니다.
```

### 4.5 테스트 (`tests/test_dashboard.py`, 신규)

```python
import re
from fastapi.testclient import TestClient
from app.api.server import create_app


ALLOWED_FETCH_URLS = {
    "/paper/status",
    "/paper/dry-run/status",
    "/paper/dry-run/start",
    "/paper/dry-run/stop",
    "/paper/dry-run/tick",
    "/reports/dry-run/analyze",
    "/reports/dry-run/latest",
}

REQUIRED_BUTTON_LABELS = (
    "상태 새로고침",
    "Dry-run 시작",
    "Tick 1회 실행",
    "Dry-run 중지",
    "리포트 분석",
    "최신 리포트 보기",
)

FORBIDDEN_STRINGS = (
    "KIS_APP_KEY",
    "KIS_APP_SECRET",
    "KIS_ACCOUNT_NO",
    "Enable live trading",
    "live trading 활성화",
    "Allow market orders",
    "Submit real order",
    "Place real order",
)


def test_dashboard_returns_html():
    with TestClient(create_app()) as client:
        r = client.get("/dashboard")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert "Paper Trading Dashboard" in r.text


def test_dashboard_safety_banner_present():
    with TestClient(create_app()) as client:
        body = client.get("/dashboard").text
    assert "paper / dry-run only" in body
    assert "live trading disabled" in body
    assert "market orders disabled" in body
    assert "no real orders" in body


def test_dashboard_has_required_buttons():
    with TestClient(create_app()) as client:
        body = client.get("/dashboard").text
    for label in REQUIRED_BUTTON_LABELS:
        assert label in body, f"missing button: {label}"


def test_dashboard_has_no_forbidden_strings():
    with TestClient(create_app()) as client:
        body = client.get("/dashboard").text
    for needle in FORBIDDEN_STRINGS:
        assert needle not in body, f"forbidden string: {needle}"


def test_dashboard_fetch_urls_are_whitelisted():
    with TestClient(create_app()) as client:
        body = client.get("/dashboard").text
    # Allow both fetch("/url") and fetch(ENDPOINTS.key) — but the inline ENDPOINTS dict
    # uses literal URLs we can extract.
    urls = re.findall(r"\"(/[A-Za-z0-9/_\-]+)\"", body)
    seen_paths = set()
    for u in urls:
        seen_paths.add(u)
    bad = seen_paths - ALLOWED_FETCH_URLS - {
        "/dashboard",  # self-reference is OK if appears
    }
    # filter trivially: only consider paths that look like API endpoints (start with /paper or /reports)
    api_only = {u for u in seen_paths if u.startswith("/paper") or u.startswith("/reports")}
    assert api_only.issubset(ALLOWED_FETCH_URLS), f"unexpected endpoints in dashboard: {api_only - ALLOWED_FETCH_URLS}"


def test_dashboard_does_not_include_form_action():
    with TestClient(create_app()) as client:
        body = client.get("/dashboard").text
    # No <form action="..."> submitting arbitrary data to the server.
    assert "<form" not in body.lower()


def test_dashboard_has_no_paper_run_endpoint():
    # /paper/run is technically safe but accepts arbitrary snapshots — beginner dashboard
    # should not expose it.
    with TestClient(create_app()) as client:
        body = client.get("/dashboard").text
    assert "/paper/run" not in body or '"/paper/run"' not in body
    # stricter:
    assert "/paper/run\"" not in body
    assert "'/paper/run'" not in body
```

### 4.6 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기대: 기존 181 + 신규 7 = ~188 PASS. compileall exit 0.

### 4.7 `docs/ai/jobs/mvp-021/patch.md`

```markdown
## 1. Files Changed
- projects/paper-trading/app/static/dashboard.html (신규)
- projects/paper-trading/app/api/routes.py (GET /dashboard 추가)
- projects/paper-trading/README.md (mvp-021 단락)
- projects/paper-trading/tests/test_dashboard.py (신규)
- docs/ai/jobs/mvp-021/patch.md (신규)

## 2. Implementation Summary

### 2.1 /dashboard endpoint
- GET /dashboard returns HTMLResponse with content read from app/static/dashboard.html
- single self-contained file (inline CSS + JS)
- no external framework, no CDN, no StaticFiles mount

### 2.2 표시되는 상태
- Paper trading: mode / live_enabled / market_orders_allowed / kis_order_dry_run / secret_exposed
- KIS: config_loaded / authenticated / account_loaded / market_data_available / order_entry_ready / last_error
- Dry-run: running / started_at / last_tick_at / ticks_total / candidates_seen / candidates_blocked / dry_run_orders_created / errors_total / last_error
- 최신 리포트: run_dir + summary JSON (from /reports/dry-run/latest)

### 2.3 버튼 6개
- 상태 새로고침 / Dry-run 시작 / Tick 1회 실행 / Dry-run 중지 / 리포트 분석 / 최신 리포트 보기

### 2.4 Secret 노출 차단
- HTML/JS 어디에도 KIS_APP_KEY/KIS_APP_SECRET/KIS_ACCOUNT_NO 문자열 없음 (테스트 검증)
- 서버 응답이 이미 sanitize 처리 (secret_exposed: false, account_no_masked, *_loaded bool flags)
- HTML이 boolean flag와 마스킹된 값만 표시

### 2.5 live/market 버튼 부재
- "Enable live trading" / "live trading 활성화" / "Allow market orders" / "Submit real order" 문자열 0건
- form action 0건 (모든 트리거는 JS의 화이트리스트 fetch)
- /paper/run endpoint 호출 부재 (대시보드 화이트리스트에서 제외)

### 2.6 테스트
- compileall PASS
- pytest 181(기존) + 7(신규) = 188 PASS
- fetch URL 화이트리스트 7개와 화면 등장 URL 비교

## 3. Safety Confirmation
- live trading 활성화 신규 경로 0건
- 시장가 주문 / 실주문 버튼 0건
- KIS endpoint URL/TR ID/payload 추가 0건
- 외부 HTTP 라이브러리 import 0건
- raw credentials HTML/JS 0건
- 모든 fetch URL이 화이트리스트(/paper/status, /paper/dry-run/{start,tick,stop,status}, /reports/dry-run/{analyze,latest})
- /paper/run 미사용 (초보자용 대시보드에는 부적합)
- form action 0건
- app/broker/*, app/runtime/*, app/oms/*, app/risk/*, app/strategy/*, app/domain/*, app/portfolio/*, app/session/*, app/reports/*, app/config.py, app/main.py, app/api/server.py, .env.example, .gitignore 미변경
- mvp-001..mvp-020 산출물 미변경
- commit/push/merge/deploy 자동화 0건

## 4. Test Results
- compileall: PASS
- pytest 181 + 7 = 188 PASS

## 5. Remaining TODOs
- analysis_report.md 본문(마크다운) 직접 화면 표시는 별도 mvp 후보 (현재는 summary JSON만 표시)
- 백그라운드 polling/SSE는 별도 mvp 후보
- 다국어/번역은 별도 mvp 후보
```

## 5. 테스트 기준

1. `.venv/bin/python -m compileall app tests` 종료코드 0.
2. `.venv/bin/python -m pytest -p no:cacheprovider` 종료코드 0. 기존 181 + 신규 ~7 PASS.
3. `GET /dashboard` 응답 status 200, content-type `text/html`.
4. HTML 본문에 6개 버튼 라벨 모두 포함.
5. HTML 본문에 안전 banner 4개 키워드(`paper / dry-run only`, `live trading disabled`, `market orders disabled`, `no real orders`) 포함.
6. HTML 본문에 금지 문자열(`KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO`, `Enable live trading`, `live trading 활성화`, `Allow market orders`, `Submit real order`) 0건.
7. HTML 본문의 fetch URL이 화이트리스트 7개의 부분집합.
8. HTML 본문에 `<form` 0건.
9. HTML 본문에 `/paper/run` 사용 0건.
10. `app/broker/*`, `app/runtime/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*`, `app/config.py`, `app/main.py`, `app/api/server.py` 변경 0건.
11. `OrderType.MARKET` 부재 유지.
12. `git diff --stat`에 mvp-021 외 변경 없음.
13. `.env` staged/committed 없음.

## 6. 리뷰 체크리스트

- [ ] `GET /dashboard` 200 + text/html.
- [ ] `app/static/dashboard.html` 단일 자가 완결 파일, 외부 CDN/framework 부재.
- [ ] 6개 버튼 라벨 정확.
- [ ] 4개 섹션(Paper/KIS/Dry-run/Report) 모두 존재.
- [ ] 안전 banner 노출.
- [ ] 화면에 표시되는 KIS 필드는 `*_loaded` / `*_ready` / `last_error` 같은 sanitize된 값만.
- [ ] HTML 본문에 raw credentials 0건.
- [ ] HTML 본문에 live trading / 시장가 활성화 버튼 0건.
- [ ] HTML 본문에 `<form>` 0건.
- [ ] fetch URL이 화이트리스트 7개에 한정.
- [ ] `/paper/run` 호출 0건.
- [ ] `app/api/routes.py`에 신규 `GET /dashboard` 핸들러만 추가, 기존 핸들러 변경 없음.
- [ ] `app/api/server.py` 변경 없음 (StaticFiles mount 등 추가 없음).
- [ ] `app/config.py`, `.env.example`, `.gitignore` 변경 없음.
- [ ] mvp-001..mvp-020 산출물 미변경.
- [ ] 기존 181 회귀 없음.
- [ ] mvp-021 신규 약 7개 PASS.
- [ ] `OrderType.MARKET` 부재 유지.
- [ ] `git diff --stat`에 mvp-021 외 변경 없음.
- [ ] `.env` staged/committed 없음.
- [ ] commit/push/merge/deploy 자동화 없음.
- [ ] `patch.md` 5섹션 + Implementation Summary 6단락 완성.
