# Review — mvp-021: paper trading 브라우저 대시보드 (`GET /dashboard`)

## Verdict

**APPROVE**

mvp-021 구현이 plan/codex-task의 모든 안전 불변식을 충족하고, **pytest 189 PASS** (신규 8 + 기존 181), 정적 안전 검사 모두 통과. `app/` 코드 변경은 `routes.py`에 `GET /dashboard` 핸들러 +8줄만 — 기존 핸들러/도메인 코드/`server.py`/`config.py` 모두 미변경.

## 검증된 사실 (직접 확인)

### 1. 코드 / 안전 invariant

1. **`GET /dashboard` 200 + text/html** (`test_dashboard_returns_html` PASS).
2. **8개 신규 테스트 모두 PASS**:
   - `test_dashboard_returns_html`
   - `test_dashboard_safety_banner_present`
   - `test_dashboard_has_required_sections_and_buttons`
   - `test_dashboard_has_no_forbidden_strings`
   - `test_dashboard_endpoint_urls_are_whitelisted`
   - `test_dashboard_does_not_include_form_action`
   - `test_dashboard_has_no_paper_run_endpoint`
   - `test_dashboard_has_no_external_assets_or_frameworks` (plan 추정 7개 + Codex 자체 추가 1개)

3. **`dashboard.html`의 forbidden pattern grep 결과 0건** (직접 확인):
   - `KIS_APP_KEY`/`KIS_APP_SECRET`/`KIS_ACCOUNT_NO` → 0
   - `<form` → 0
   - `/paper/run` → 0
   - `Enable live trading` / `live trading 활성화` / `Allow market orders` → 0
   - `http://` / `https://` → 0 (외부 URL 부재)
   - `cdn.` / `unpkg.` / `jsdelivr` → 0 (외부 CDN/framework 부재)

4. **`routes.py` 변경 8줄만** — `GET /dashboard` 핸들러 추가, 기존 `/healthz`/`/paper/status`/`/paper/run`/`/paper/dry-run/*`/`/reports/dry-run/*` 핸들러 보존.

5. **`app/api/server.py` 변경 0건** (StaticFiles mount 추가 없음 — 핸들러가 파일을 직접 읽음).

6. **`OrderType.MARKET` 부재 유지** (mvp-021이 도메인 코드 미접촉).

7. **mvp-001..mvp-020 산출물 미변경**.

### 2. dashboard.html 구조 (직접 inspection 결과)

- **4개 섹션 헤더**: "Paper trading 상태" / "KIS 상태" / "Dry-run 상태" / "최신 리포트".
- **6개 버튼 라벨**: "상태 새로고침" / "Dry-run 시작" / "Tick 1회 실행" / "Dry-run 중지" / "리포트 분석" / "최신 리포트 보기".
- **안전 banner**: "paper / dry-run only · live trading disabled · market orders disabled · no real orders".
- **`ENDPOINTS` 객체**: 7개 화이트리스트 URL만(`/paper/status`, `/paper/dry-run/{status,start,stop,tick}`, `/reports/dry-run/{analyze,latest}`).
- **외부 자산 0건**: `<link>`/`<script src>`/CDN/외부 URL 모두 부재.

### 3. `app/api/routes.py` 변경 (8줄)

```python
@router.get("/dashboard", response_class=HTMLResponse)
def dashboard_page() -> HTMLResponse:
    return HTMLResponse(content=_DASHBOARD_HTML_PATH.read_text(encoding="utf-8"))
```

깔끔하고 최소한. `HTMLResponse` 와 `Path` import 추가만.

### 4. 테스트 결과 (자체 재실행)

```
tests/test_dashboard.py: 8 passed
전체 suite: 189 passed in 0.41s
```

신규 8개 모두 PASS. 회귀 0건.

## Findings (severity 순)

### 1. (informational) 추가 테스트 1개 (plan 추정보다 +1)

- 위치: `tests/test_dashboard.py:test_dashboard_has_no_external_assets_or_frameworks`.
- 관찰: plan은 7개 추정, Codex가 8개 작성. 추가 테스트는 외부 자산(CDN/framework) 부재 검증 — 안전성 강화 방향. 좋음.
- 영향: 좋음. 추가 카테고리 보호.

### 2. (low — process) `app/broker/kis.py` pre-existing dirty가 워크트리에 누적

- 위치: `git diff --stat -- projects/paper-trading/app` → `kis.py | 225 ... 209 insertions(+), 16 deletions(-)`.
- 관찰: mvp-014-017-bundle / mvp-018 / 이전 mvps에서 누적된 dirty. mvp-021 자체는 `app/api/routes.py`만 +8줄. patch.md §2.6 "Worktree Note"가 정직하게 명시.
- 영향: 안전 위반 없음. commit 시 staging 한정 필요.
- 권장: 액션 아이템 참고.

## File / line references (요청 ↔ 산출물 매핑)

| 요청 요소 | 구현 | 상태 |
| --- | --- | --- |
| `GET /dashboard` 200 + HTML | `routes.py:dashboard_page` + `app/static/dashboard.html` | ✓ |
| Paper trading 상태 5개 필드 | `paper-status-section` 표 | ✓ (mode, live_enabled, market_orders_allowed, kis_order_dry_run, secret_exposed) |
| KIS 상태 6개 필드 | `kis-status-section` 표 | ✓ |
| Dry-run 상태 9개 필드 | `dry-run-status-section` 표 + counters dict | ✓ |
| 버튼 6개 | `button-row`의 6개 button | ✓ |
| 최신 리포트 | `report-section`의 `<pre>` + run_dir meta | ✓ |
| 외부 framework 미추가 | dashboard.html에 `<script src>`/`<link href>` 0건 | ✓ |
| HTMLResponse 사용 | `from fastapi.responses import HTMLResponse` | ✓ |

| 요청 안전 조건 | 결과 |
| --- | --- |
| 실주문 버튼 미존재 | grep "Submit"/"Place"/"real order" 0건 ✓ |
| live trading 활성화 버튼 미존재 | "Enable live trading"/"live trading 활성화" 0건 ✓ |
| 시장가 버튼 미존재 | "Allow market orders"/"market order submit" 0건 ✓ |
| KIS app key/secret/account/token 미노출 | `KIS_APP_KEY`/`KIS_APP_SECRET`/`KIS_ACCOUNT_NO` 0건 ✓ |
| `.env` 내용 미표시 | 파일 미참조 ✓ |
| 안전 endpoint만 호출 | `ENDPOINTS` 객체 7개 화이트리스트 ✓ |
| `KIS_ORDER_DRY_RUN=true` 기본 유지 | 대시보드 read-only 표시, 변경 버튼 없음 ✓ |

## Missing tests / residual risk

- 8개 테스트가 정적 safety 패턴 + endpoint whitelist + 외부 자산 부재까지 모두 검증. 추가 필요 없음.
- 실제 브라우저에서 동작 확인은 메타 테스트로 보장되지 않음. 운영자가 `./scripts/start_server.sh` 후 `http://127.0.0.1:8000/dashboard`를 열어 시각 확인 필요 (patch.md §5 명시).
- analysis_report.md 마크다운 본문 직접 표시는 본 mvp에 없음(summary JSON만 표시) — patch.md Remaining TODOs에 명시.

## Final checklist (요청 + scope)

- [x] **`GET /dashboard` 200 + text/html**.
- [x] **단일 자가 완결 HTML** — 외부 CDN/framework 0건 (전용 테스트로 검증).
- [x] **4개 섹션 + 6개 버튼 라벨** 정확.
- [x] **안전 banner 4개 키워드** ("paper / dry-run only", "live trading disabled", "market orders disabled", "no real orders").
- [x] **KIS credentials 0건** in HTML/JS.
- [x] **`<form>` 0건, `/paper/run` 0건, live/market 활성화 버튼 0건**.
- [x] **fetch URL 화이트리스트** 7개에 한정.
- [x] **`app/api/routes.py` 변경 +8줄, 기존 핸들러 미변경**.
- [x] **`app/api/server.py`, `app/config.py`, `app/main.py` 변경 0건**.
- [x] **`app/broker/*`, `app/runtime/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*` 변경 0건** (mvp-021 scope).
- [x] **`.env.example`, 프로젝트 `.gitignore`, 루트 `.gitignore` 변경 0건**.
- [x] **mvp-001..mvp-020 산출물 미변경**.
- [x] **기존 181 회귀 0건**.
- [x] **mvp-021 신규 8 PASS**.
- [x] **`OrderType.MARKET` 부재 유지**.
- [x] **commit/push/merge/deploy 자동화 0건**.
- [x] **patch.md 5섹션 + Implementation Summary 6단락 완성**.
- [ ] **commit staging 한정 — 사람 액션** (Findings #2 pre-existing kis.py dirty 격리).

## 사람에게 남기는 액션 아이템

1. **mvp-021 commit staging 한정** (필수):

   ```bash
   cd /root/ai-dev-center/projects/ai-team
   git add projects/paper-trading/app/static/dashboard.html \
           projects/paper-trading/app/api/routes.py \
           projects/paper-trading/tests/test_dashboard.py \
           projects/paper-trading/README.md \
           docs/ai/jobs/mvp-021/
   git diff --cached --stat
   ```

   `app/broker/kis.py` 등 pre-existing dirty(mvp-014-017/018 잔재)는 별도 commit으로 분리.

2. **commit/push/merge/deploy는 사람이 직접.** 본 작업은 자동화하지 않는다.

3. **브라우저 시각 확인** (선택, 권장):

   ```bash
   cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
   ./scripts/start_server.sh   # 터미널 A
   # 터미널 B 또는 브라우저:
   # http://127.0.0.1:8000/dashboard
   ```

   각 버튼이 의도된 endpoint를 호출하는지, 4개 섹션이 채워지는지, 안전 banner가 보이는지 1분 시각 확인.

4. **다음 mvp 후보**:
   - **mvp-022 (자연스러운 다음)**: mvp-019의 `claude_review_input.md` 기반 Claude/Codex가 전략 개선안 plan/codex-task 작성 후 별도 mvp로 임계값 조정.
   - **mvp-022 또는 별도**: `analysis_report.md` 마크다운 본문을 대시보드에서 렌더링(현재는 summary JSON만 표시).
   - **mvp-023**: 백그라운드 polling 또는 SSE로 자동 상태 새로고침.
   - **계속 보류**: KIS 공식 문서값(`docs/kis/MISSING_OFFICIAL_VALUES.md`)이 채워지기 전까지 실제 KIS HTTP 연결.
