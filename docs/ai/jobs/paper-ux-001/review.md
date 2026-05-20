# paper-ux-001 — Claude Review

## Verdict

APPROVE

## Summary

paper-ux-001 의 한국어 우선 paper trading dashboard UX 가 이미 commit `a549454 expose paper trading account dashboard` 로 land 된 상태에서 review 가 진행됐다. `/dashboard` 가 한국어 라벨과 예시 모의 주문 버튼, 한글 해석/제안을 제공하고, 모든 paper 주문은 `RiskEngine → OMS → PaperBroker → PaperEngine` 경로를 지킨다. dashboard 의 fetch 호출은 전부 로컬 FastAPI 의 `/paper/*` / `/reports/*` 엔드포인트로만 향하며 KIS HTTP 호출 0 건. live trading / 실주문 / KIS endpoint 모두 차단 상태 유지.

본 turn 의 untracked 파일은 docs 디렉터리 (`docs/ai/jobs/paper-ux-001/`) 만이며, 본 review 가 거기에 review.md 추가.

## Review focus 항목별 검증

### 1. Dashboard 한국어 우선 + 초보 친화 — OK

`projects/paper-trading/app/static/dashboard.html` 의 주요 한국어 라벨:

- `dashboard.html:37` — `모의 주문 실행` 버튼
- `:69` — `수동 모의 주문` 섹션 헤더
- `:96` — `아직 실행한 모의 주문이 없습니다.` 안내 메시지
- `:106` — `바로 모의테스트 해보기` 섹션
- `:108` — `예시 모의 주문 실행` 버튼 (demo)
- `:178` — `한글 해석` 헤더 (report)

### 2. Raw JSON 은 "원본 JSON 보기" 뒤로 숨김 — OK

- `dashboard.html:102` — `<details><summary>원본 JSON 보기</summary><pre id="paper-order-result">{}</pre></details>` (paper order 결과)
- `dashboard.html:182` — `<details><summary>원본 JSON 보기</summary><pre id="report-content">{}</pre></details>` (report)

기본 상태는 collapsed, 사용자 click 시에만 펼침.

### 3. Paper simulation 버튼이 safe paper-only path 사용 — OK

- dashboard `ENDPOINTS` map (`:190-204`) 의 `paperOrderSimulate: "/paper/order/simulate"` — 로컬 FastAPI 경로.
- `dashboard.html:429` — `fetchJson(ENDPOINTS.paperOrderSimulate, { method: "POST", ... })` 만 호출. KIS URL 호출 없음.

### 4. POST /paper/order/simulate 가 RiskEngine → OMS → PaperBroker → PaperEngine 경로 통과 — OK

`projects/paper-trading/app/api/routes.py` 의 `paper_order_simulate` 함수 (라인 230-361) 실행 순서:

- `:235-246` — `settings.trading_mode != "paper"` 또는 `live_trading_enabled` 면 `paper_trading_required` 로 거절.
- `:287` — `decision = request.app.state.risk.evaluate(intent)` (RiskEngine).
- `:294-305` — `decision.approved is False` 면 거절 + 한글 사유 반환.
- `:322` — `ack = request.app.state.oms.place(intent)` (OMS).
- `:348` — `trades = engine.on_quote(quote)` (PaperEngine → PaperBroker.tick → Fill → PaperAccount/PortfolioService/PaperJournal).

OMS / RiskEngine 우회 없음. 모든 paper 주문이 동일 경로.

### 5. 실 broker API 호출 추가 없음 — OK

`grep -n "import requests\|import httpx\|import aiohttp\|KisBroker\|kis_broker.place_order\|kis_broker.cancel" projects/paper-trading/app/api/routes.py projects/paper-trading/app/static/dashboard.html` → 0 lines. dashboard / routes 의 simulate flow 에서 KisBroker 객체가 호출되지 않음.

### 6. Dashboard 에서 KIS endpoint 호출 없음 — OK

dashboard `ENDPOINTS` map (`:190-204`) 의 14 개 URL 모두 로컬 FastAPI 경로:

```
/paper/status, /paper/account, /paper/positions, /paper/fills, /paper/orders,
/paper/order/simulate, /paper/engine/status, /paper/report/summary,
/paper/dry-run/status, /paper/dry-run/start, /paper/dry-run/stop, /paper/dry-run/tick,
/reports/dry-run/analyze, /reports/dry-run/latest
```

KIS host (`openapi*.koreainvestment.com`) / 외부 API URL 0 건. dashboard 의 KIS 섹션은 `/paper/status` 응답에서 받은 read-only 플래그 (`kis_config_loaded`, `kis_authenticated`, `kis_account_loaded`, `kis_market_data_available`, `kis_order_entry_ready`, `kis_last_error`) 만 표시 — 호출 아님.

### 7. live trading 비활성 유지 — OK

- `routes.py:91-92` — `kis_order_entry_mode` 가 `paper` 모드 + `live_trading_enabled=False` 일 때만 `not_implemented`, 아니면 `disabled`.
- `:116` — `/paper/status` 가 `live_enabled: settings.live_trading_enabled` 노출 (현재 False).
- `:235-238` — simulate 가 `live_trading_enabled=True` 면 `paper_trading_required` 로 fail-closed.
- `:455-459` — `_safety_flags` 가 `real_broker_orders_enabled: False` 명시.

### 8. Dashboard 에서 실 주문 불가 — OK

dashboard 의 모든 주문 경로는 `/paper/order/simulate` 또는 `/paper/dry-run/tick` 만. 실 broker (`KisBroker.place_order` / `cancel_order` / `replace_order`) 를 직접 호출하는 endpoint 가 routes.py 에 노출 안 됨. simulate 자체가 PaperBroker (paper fill simulator) 만 호출.

### 9. Market orders 기본 비활성 (paper-only 가드 한정) — OK

- `routes.py:537` — `paper_market_orders_disabled` 한글 사유: "시장가 모의 주문은 기본값에서 비활성화되어 있습니다".
- 기존 RiskEngine + PaperBroker 의 MARKET 3중 가드 (settings.allow_paper_market_orders + trading_mode + live_trading_enabled) 무변동.
- dashboard 의 `_order_payload` 기본값은 `order_type: "limit"` (안전).

### 10. `.env` / app key / app secret / token / refresh token / 계좌번호 노출 없음 — OK

- `routes.py:142, 177, 193, 204, 217, 226, 516` — 모든 `/paper/*` 응답에 `secret_exposed: False` 강제.
- `routes.py:141` — `account_no_masked: kis_broker.account.masked_account_no()` (`***xxxx` 형태) 또는 `<unset>`.
- `dashboard.html:344` — `setText("ps-secret-exposed", boolKo(paper.secret_exposed, "노출", "노출 없음"))` 가 사용자에게 명시.
- 기존 `tests/test_paper_e2e_api.py::test_paper_e2e_responses_do_not_expose_secrets` 가 6 개 endpoint 응답에서 `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO`, `app_secret`, `access_token` 부재를 회귀로 강제.

### 11. commit / push / merge / deploy 수행 없음 — OK

paper-ux-001 의 code 변경은 사용자가 이전 단계에서 commit `a549454 expose paper trading account dashboard` 로 직접 land. 본 review turn 은 docs/ai/jobs/paper-ux-001/review.md 추가만이며, **본 review turn 도 commit / push / merge / deploy 수행 안 함**.

### 12. Tests passed: 316 — partial confirmation

patch.md 의 "316 passed in 0.60s" 는 paper-ux-001 구현 시점의 베이스라인. 그 이후 다음 commit 들이 추가되며 누적 테스트 수가 증가:

- a549454 직후 → 316 passed (paper-ux-001 시점)
- 후속 mvp-014..api-auth-001 / api-account-001 / api-market-data-001 / api-orders-paper-001 / api-orders-paper-002-cancel-replace / paper-e2e-001 / runtime-002 → 458 passed
- 본 시리즈 Phase 1 (api-orders-paper-003-query) → 488
- Phase 2 (paper-002) → 501
- Phase 3 (strategy-002) → 520

**현재 working tree pytest: 520 passed in 0.78s** (재실행 검증). paper-ux-001 시점의 316 baseline 은 historical record 로 정확. paper-ux-001 의 좁은 test_dashboard.py + test_paper_e2e_api.py 대상 실행:

```text
$ .venv/bin/python -m pytest -p no:cacheprovider tests/test_dashboard.py tests/test_paper_e2e_api.py
21 passed in 0.29s
```

dashboard / e2e API 회귀 모두 정상.

## Safety regression (전체 OK)

| 항목 | 결과 |
| --- | --- |
| Korean-first + beginner-friendly dashboard | OK (`바로 모의테스트 해보기` + `한글 해석` + `원본 JSON 보기`) |
| Raw JSON behind details/summary | OK (`dashboard.html:102, 182`) |
| Simulation 버튼이 paper-only path | OK (`ENDPOINTS.paperOrderSimulate`) |
| `/paper/order/simulate` 가 Risk→OMS→PaperBroker→PaperEngine 통과 | OK (`routes.py:287, 322, 348`) |
| 실 broker API 추가 없음 | OK (KIS imports / fetch 0) |
| Dashboard 에서 KIS endpoint 호출 없음 | OK (모든 fetch 가 로컬 `/paper/*`) |
| live trading 비활성 유지 | OK (`settings.live_trading_enabled` False, gated) |
| Dashboard 에서 실 주문 불가 | OK (no real-broker endpoint 노출) |
| Market orders 기본 비활성 | OK (`paper_market_orders_disabled` 사유 + RiskEngine MARKET 3중 가드 무변동) |
| secret / 계좌번호 / token / refresh token 노출 없음 | OK (`secret_exposed: False` + `account_no_masked` + 회귀 테스트) |
| commit / push / merge / deploy 수행 없음 (본 review turn) | OK |
| Tests: paper-ux-001 시점 316, 본 review 시점 520 | OK |

## Findings (severity 순)

### F1 (INFO) — patch.md 의 316 passed 는 historical, 현재 베이스라인은 520

paper-ux-001 구현 시점의 정확한 baseline 이며 후속 작업이 추가된 결과 현재 520. patch.md 의 숫자는 historical record 로 보존되어 무방. 본 review 의 결정에 영향 없음.

### F2 (INFO) — paper-ux-001 의 code 변경은 이미 committed

git log 에서 `a549454 expose paper trading account dashboard` 가 routes.py / server.py / dashboard.html / scripts/_common.sh / README.md / tests/test_dashboard.py / tests/test_paper_e2e_api.py 의 paper-ux-001 변경을 모두 포함. 즉 본 review 의 시점에서 사용자가 이미 작업을 머지했고, `docs/ai/jobs/paper-ux-001/` 디렉터리 (patch.md / status.md / 본 review.md) 만 untracked. 사용자가 docs 디렉터리 commit 여부 결정.

### F3 (INFO / observation) — patch.md §5 의 후속 TODO 가 본 review 의 결정에 영향 없음

patch.md 가 다음 후속을 명시했고 본 review 는 이들을 강제하지 않음:

- "Add a reset button only if a future job explicitly approves state reset semantics" — UI state reset 은 별 job.
- "Improve dashboard table formatting for large portfolios and long fill histories" — 별 job.
- "Add browser-level screenshot tests if Playwright becomes part of the accepted checks" — 별 job (현재 회귀 인프라에 Playwright 없음).

## Final Checklist

| 항목 | 결과 |
| --- | --- |
| 1. Dashboard Korean-first / beginner friendly | OK |
| 2. Raw JSON behind `원본 JSON 보기` | OK |
| 3. Paper simulation uses safe paper-only path | OK |
| 4. `/paper/order/simulate` traverses RiskEngine → OMS → PaperBroker → PaperEngine | OK |
| 5. No real broker API call added | OK |
| 6. No KIS endpoint called from dashboard | OK |
| 7. Live trading disabled | OK |
| 8. Real orders impossible from dashboard | OK |
| 9. Market orders default off (paper-only guard preserved) | OK |
| 10. `.env` / app key / app secret / token / refresh token / account number not exposed | OK |
| 11. commit / push / merge / deploy 수행 없음 (본 review turn) | OK |
| 12. Tests passed: 316 (paper-ux-001 시점) / 520 (현재) | OK |

## Follow-up Codex prompt

없음. APPROVE.

다음 단계는 사용자가 직접:

1. `docs/ai/jobs/paper-ux-001/` 디렉터리 (patch.md / status.md / 본 review.md) commit 여부 결정. 권고: `git add docs/ai/jobs/paper-ux-001/ && git commit -m "docs: record paper-ux-001 review"`.
2. 본 review 는 push / PR / merge / deploy 수행하지 않음.
3. paper-ux-001 의 후속 TODO (reset button / table formatting / Playwright screenshot test) 는 별도 job 으로 사용자 결정.

본 review 자체는 코드 / catalog 본문 / `.env` / GUI 어떤 파일도 수정하지 않음. commit / push / merge / deploy 수행 없음.
