# Codex Task — mvp-021: paper trading 브라우저 대시보드 (`GET /dashboard`)

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-021/plan.md` and `docs/ai/jobs/mvp-021/request.ko.md` first.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-021`
- 대상: `projects/paper-trading/app/static/dashboard.html` 신규 + `app/api/routes.py`에 `GET /dashboard` + 테스트 + README + patch.md.
- 외부 프레임워크/CDN 0건. 단일 자가 완결 HTML(inline CSS+JS) + fetch로 mvp-018/019의 안전 endpoint만 호출.

## 사전 점검 (Codex 첫 단계)

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

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, KIS app key/secret/account/token 변경/생성/읽기/노출 금지.
- 외부 HTTP 라이브러리/외부 JS framework/CDN 추가 금지. dashboard.html은 자체 인라인만 사용.
- 외부 HTTP 라이브러리 import 금지.
- 실주문 코드 신설 금지. 실제 KIS HTTP 호출 코드 신설 금지.
- KIS endpoint URL/TR ID/payload 코드 신설 금지.
- live trading 활성화 버튼/엔드포인트 신설 금지. 시장가 주문 버튼/엔드포인트 신설 금지.
- `OrderType`에 MARKET 멤버 추가 금지.
- RiskEngine/OMS 우회 코드 경로 신설 금지.
- Strategy 패키지가 `app.broker.kis*` import 금지(기존 상태 유지).
- 대시보드에 `<form action="...">` 사용 금지(임의 POST 가능성 차단). 모든 트리거는 JS의 화이트리스트 fetch.
- 대시보드에서 `/paper/run` 호출 금지(초보자용 대시보드에 부적합). `app/api/routes.py`의 기존 `/paper/run` 핸들러 자체는 변경하지 마.
- 화면/HTML/JS 어디에도 `KIS_APP_KEY` / `KIS_APP_SECRET` / `KIS_ACCOUNT_NO` 문자열 0건.
- 임의 shell 명령 입력 UI/API 신설 금지.
- `pip install` 실행 금지.
- 본 작업 범위 외 파일 변경 금지. mvp-001..mvp-020 산출물 변경 금지.
- `app/api/server.py` 변경 금지. `StaticFiles` mount 추가 금지(파일 하나라 endpoint가 직접 읽으면 충분).

## 수정 허용 위치

### 신규

- `projects/paper-trading/app/static/dashboard.html`
- `projects/paper-trading/tests/test_dashboard.py`
- `docs/ai/jobs/mvp-021/patch.md`

### 수정 가능

- `projects/paper-trading/app/api/routes.py` (단일 `GET /dashboard` 핸들러 + 필요 import 추가만, 기존 핸들러 한 줄도 변경 금지)
- `projects/paper-trading/README.md` (mvp-021 단락 추가, 기존 단락 변경 없음)

### 절대 미수정

- `projects/paper-trading/app/api/server.py`
- `projects/paper-trading/app/config.py`, `app/main.py`
- `projects/paper-trading/app/broker/*`, `app/runtime/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*`
- `.env.example`, 프로젝트 `.gitignore`, 루트 `.gitignore`
- mvp-001..mvp-020 산출물, mvp-020 scripts/
- 기존 테스트 중 본 작업이 다루지 않는 것
- `imports/`, `web/`, `prompts/`, 기존 `docs/`(`docs/ai/jobs/mvp-021/` 외)

## 구현 작업

`plan.md` §4 코드를 그대로 따른다. 핵심 요점:

### 1) `app/static/dashboard.html`

`plan.md` §4.2의 마크업 전체를 그대로 사용. 핵심 검증 포인트:

- 외부 CDN/script src 0건.
- 6개 버튼 라벨 정확: `상태 새로고침`, `Dry-run 시작`, `Tick 1회 실행`, `Dry-run 중지`, `리포트 분석`, `최신 리포트 보기`.
- 안전 banner 텍스트: `paper / dry-run only · live trading disabled · market orders disabled · no real orders` (정확히 4개 키워드 포함).
- `ENDPOINTS` 객체의 7개 URL만:
  - `/paper/status`
  - `/paper/dry-run/status`
  - `/paper/dry-run/start`
  - `/paper/dry-run/stop`
  - `/paper/dry-run/tick`
  - `/reports/dry-run/analyze`
  - `/reports/dry-run/latest`
- `/paper/run` 절대 미사용.
- `<form` 절대 미사용.
- `KIS_APP_KEY`/`KIS_APP_SECRET`/`KIS_ACCOUNT_NO` 문자열 절대 부재.
- "Enable live trading"/"live trading 활성화"/"Allow market orders"/"Submit real order"/"Place real order" 같은 위험 라벨 절대 부재.

### 2) `app/api/routes.py` 변경

기존 import에 (없으면) 추가:

```python
from fastapi.responses import HTMLResponse
from pathlib import Path
```

새 핸들러 추가(파일 어디든 OK, 기존 핸들러 보존):

```python
_DASHBOARD_HTML_PATH = Path(__file__).resolve().parents[1] / "static" / "dashboard.html"


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page() -> HTMLResponse:
    text = _DASHBOARD_HTML_PATH.read_text(encoding="utf-8")
    return HTMLResponse(content=text)
```

기존 핸들러(`/healthz`, `/paper/status`, `/paper/run`, `/paper/dry-run/*`, `/reports/dry-run/*`)는 한 줄도 바꾸지 마.

### 3) `tests/test_dashboard.py` (신규)

`plan.md` §4.5 코드 그대로. 다음 시나리오 모두 PASS:

- `test_dashboard_returns_html`
- `test_dashboard_safety_banner_present`
- `test_dashboard_has_required_buttons`
- `test_dashboard_has_no_forbidden_strings`
- `test_dashboard_fetch_urls_are_whitelisted`
- `test_dashboard_does_not_include_form_action`
- `test_dashboard_has_no_paper_run_endpoint`

### 4) `README.md` 변경

`plan.md` §4.4의 mvp-021 단락을 mvp-020 단락 뒤(또는 적절한 위치)에 추가. 기존 단락 변경 없음.

### 5) 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

저장소 루트:

```bash
git diff --stat
git status --short
```

기대: 기존 181 + 신규 7 = ~188 PASS. compileall exit 0. mvp-021 외 변경 없음.

### 6) `docs/ai/jobs/mvp-021/patch.md`

`plan.md` §4.7 템플릿 그대로. 실제 KIS 값 미인용. Implementation Summary 6단락 모두 채움.

## 완료 정의 (Done)

- `app/static/dashboard.html` 신규 — 외부 CDN/framework 0건, inline CSS+JS만.
- `app/api/routes.py`에 `GET /dashboard` 핸들러 추가, 기존 핸들러 미변경.
- HTML이 6개 버튼 라벨, 4개 섹션, 안전 banner 포함.
- HTML이 `KIS_APP_KEY`/`KIS_APP_SECRET`/`KIS_ACCOUNT_NO` / "live trading 활성화" / 시장가 활성화 라벨 / `<form>` / `/paper/run` 호출 0건.
- HTML의 모든 fetch URL이 화이트리스트 7개에 한정.
- `app/api/server.py`, `app/config.py`, `app/main.py`, `app/broker/*`, `app/runtime/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*` 변경 0건.
- `.env.example`, 프로젝트 `.gitignore`, 루트 `.gitignore` 변경 0건.
- mvp-001..mvp-020 산출물 변경 0건.
- 기존 181 회귀 없음.
- mvp-021 신규 7 PASS.
- `OrderType.MARKET` 부재 유지.
- `git diff --stat`에 mvp-021 외 변경 없음.
- `.env` staged/committed 없음.
- `patch.md` 5섹션 + Implementation Summary 6단락 완성.
- commit/push/merge/deploy 자동화 없음.
