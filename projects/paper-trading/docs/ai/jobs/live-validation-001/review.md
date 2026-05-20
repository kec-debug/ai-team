# live-validation-001 — Claude Review

## Verdict

APPROVE

## Summary

live-validation-001 은 master plan §6 Phase 5 슬롯의 **준비 단계만** 다뤘다. request body 의 "이번 작업은 실거래를 시작하는 작업이 아니다" 선언과 모든 absolute prohibitions 가 그대로 honor 됐다. read-only `/ops/status` + `/ops/preflight` 두 GET endpoint, 14 항 preflight checklist, 3 단 escalating safety banner, 한국어 운영자 README 가 추가됐고, **live 활성화 / live arm / live order / dry-run disable / market allow toggle 0 건**. 547 passed (520 baseline + 27 new), 회귀 0.

## Scope of changes (이번 turn 의 in-scope)

**In-scope, intentional**:

- `app/ops/__init__.py` (NEW) — 패키지 마커 + `compute_live_validation_status` re-export.
- `app/ops/preflight.py` (NEW) — pure-function preflight 평가, `PreflightItem` / `LiveValidationStatus` dataclass, 12 flags + 14 checklist items + 3-level banner escalation.
- `app/api/routes.py` (MODIFY, +59 lines) — `_serialize_preflight_item` / `_serialize_live_validation_status` helper + `GET /ops/status` + `GET /ops/preflight`. 기존 endpoint 무변동.
- `app/config.py` (MODIFY, +28 lines) — `live_validation_daily_loss_limit_usd: Decimal | None = None` + `live_validation_max_orders_per_day: int | None = None` settings 추가, `_optional_decimal_env` / `_optional_int_env` 헬퍼, `load_settings()` 에서 옵트인 로딩. **두 settings 모두 코드 어디서도 enforcement 게이트로 소비되지 않음** — 별도 grep 으로 검증.
- `app/static/dashboard.html` (MODIFY, +81 lines) — top safety banner + "🛡️ Live Validation 준비 상태" 섹션 + "✅ Preflight Checklist" 섹션 + CSS + `refreshOpsStatus` / `renderChecklist` JS. 기존 섹션 무변동.
- `projects/paper-trading/README.md` (MODIFY, +68 lines) — "운영자 가이드 (live-validation-001 준비 상태)" 섹션 추가. 필수 문장 `본 시스템은 \`live_validation_ready=READY\` 가 표시되어도 실제 live 주문을 전송할 코드 경로를 보유하지 않습니다.` 포함 (README.md:448 확인).
- `tests/test_ops_preflight.py` (NEW) — pure-function preflight 회귀.
- `tests/test_ops_endpoints.py` (NEW) — TestClient endpoint + GET-only + secret leak + mutating route 부재 회귀.
- `tests/test_dashboard.py` (MODIFY, +33 lines) — 신규 섹션 + 배너 + 금지 버튼 부재 회귀 4 함수 추가, 기존 단언 무변동.
- `docs/ai/jobs/live-validation-001/patch.md` (NEW) — Codex 의 patch 보고.

**Out-of-scope, untouched (요구 사항 그대로)**:

- `app/broker/*`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*`, `app/strategy/*`, `app/session/*`, `app/domain/*`, `app/api/server.py`, `app/main.py` 무변동.
- `.env`, `.env.example`, `docs/kis/MISSING_OFFICIAL_VALUES.md` 무변동.
- `KisBroker.place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` 본문 무변동.
- `validate_kis_order_request` / `_validate_paper_settings` / `OrderType.MARKET` 가드 / `OrderType.STOP` 무도입 / FX 미도입.
- `capabilities()` 의 모든 플래그 `False` 유지. `order_execution_implemented` `False` 유지.

## Review focus 항목별 검증

### 1. live trading 활성화 0 — OK

- `grep "live_trading_enabled = True\|live_trading_enabled=True" app/ops app/api app/static` → 0 lines.
- `app/ops/preflight.py:55-79` 의 `compute_live_validation_status` 가 `paper_status_payload["live_trading_enabled"]` 를 **read** 만 하고 set 하지 않음.
- README:448 의 explicit 문장: "본 시스템은 `live_validation_ready=READY` 가 표시되어도 실제 live 주문을 전송할 코드 경로를 보유하지 않습니다."

### 2. `/ops/*` GET-only — OK

`grep "@router\.(get|post|put|delete|patch)\(\"/ops/" app/api/routes.py` 결과:

```text
256:@router.get("/ops/status")
268:@router.get("/ops/preflight")
```

POST/PUT/DELETE/PATCH 0 건. `tests/test_ops_endpoints.py::test_ops_endpoints_are_get_only` 가 `client.post("/ops/status")` / `client.put("/ops/status")` / `client.delete("/ops/preflight")` 가 405 임을 회귀로 강제 (patch.md 의 verbatim grep 결과 `@router.(post|put|delete|patch)("/ops/` 부재 확인).

### 3. 새 settings 가 어디서도 enforcement 게이트로 소비되지 않음 — OK

`grep -rn "live_validation_daily_loss_limit_usd\|live_validation_max_orders_per_day\|live_validation_ready" app/ --include="*.py"` 결과:

- `app/ops/preflight.py` — 정의 + checklist 항목 표시 (read).
- `app/api/routes.py` — `_serialize_live_validation_status` 의 dict key (read).
- `app/config.py` — Settings 필드 + load_settings 호출 (define).

`app/broker/*`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/*` 어디서도 이 settings/필드를 읽고 차단/허용하는 코드 0 건. 즉 **status-reporting only** 약속이 유지됨.

### 4. live_validation_ready 가 UX 신호일 뿐 — OK

`live_validation_ready` 가 코드에서 사용되는 위치:

- `app/ops/preflight.py:80-89` — 계산.
- `app/api/routes.py` `_serialize_live_validation_status` — 응답 dict 에 포함.
- `app/static/dashboard.html` — UI 표시 ("READY" / "NOT READY").

`KisBroker.place_order` / OMS / RiskEngine / 어떤 가드 로직도 이 값을 읽지 않음. `True` 가 표시되어도 실제 live 코드 경로 0 줄.

### 5. Dashboard 에 금지 버튼 부재 — OK

`grep -nE "btn-arm-live|btn-enable-live|btn-disable-dry-run|btn-allow-market|btn-toggle-kill-switch" app/static/dashboard.html` → 0 lines.

`tests/test_dashboard.py::test_dashboard_has_no_live_arm_or_enable_buttons` 가 5 개 forbidden id 의 부재를 회귀로 강제.

### 6. Banner escalation rules 정합 — OK

`app/ops/preflight.py:46-51` 의 5 개 한국어 banner 문자열:

- `_BANNER_DANGER_LIVE` — "위험: live trading 값이 true 입니다."
- `_BANNER_DANGER_MARKET` — "위험: 시장가 주문 허용 값이 true 입니다."
- `_BANNER_DANGER_SECRET` — "위험: secret 노출 가능성이 감지되었습니다."
- `_BANNER_WARN_KILL` — "주의: kill switch 가 engaged 입니다."
- `_BANNER_WARN_AUTH` — "주의: KIS config 는 로드됐으나 인증 토큰이 없습니다."

`compute_live_validation_status` 의 escalation 분기:

- `danger` ← `live_trading_enabled` / `market_orders_allowed` / `secret_exposed` 중 하나라도 True
- `warning` ← `kill_switch_engaged` 또는 (KIS config 로드 + 인증 미존재)
- `info` ← 기본 안전 상태

request §"사고 방지 경고 배너" 와 일치.

### 7. 14 개 preflight checklist item — OK

`grep -c "PreflightItem(" app/ops/preflight.py` → **14**.

request §2 의 14 항 ("paper mode 확인" ~ "최근 테스트 통과 여부 수동 확인 항목") 모두 대응. `recent_test_passed_manual` 은 default `passed=False` + label "수동 확인 필요" 로 운영자에게 명시 (`tests/test_ops_preflight.py::test_recent_test_passed_manual_item_default_false` 회귀).

### 8. secret / 계좌번호 / token / Bearer 노출 0 — OK

- patch.md §3 의 verbatim grep: `grep "Bearer eyJ\|access_token=eyJ\|appkey=PS" app/ops app/api app/static` → 0 lines.
- `tests/test_ops_endpoints.py::test_ops_endpoints_do_not_expose_secrets` 가 `KIS_APP_KEY` / `KIS_APP_SECRET` / `KIS_ACCOUNT_NO` / `app_secret` / `access_token` / `Bearer ` 6 개 token 부재를 회귀로 강제.
- 응답 dict 에 always `secret_exposed: False` 포함.

### 9. README 필수 문장 포함 — OK

`README.md:448` — "본 시스템은 `live_validation_ready=READY` 가 표시되어도 실제 live 주문을 전송할 코드 경로를 보유하지 않습니다."

운영자 guide 섹션 (README.md:384) 이 paper simulation / dry-run / report / live 전 확인 사항 / 실거래 전 필요 조건 모두 한국어로 정리.

### 10. 외부 HTTP 라이브러리 0 — OK

`grep "^(from|import) (requests|httpx|aiohttp|urllib3|openpyxl|pandas)" app/ops app/api tests/test_ops_*` → 0 lines.

### 11. KIS endpoint / TR ID / payload 추측 0 — OK

본 job 의 모든 ops 코드는 in-process pure-Python. 외부 KIS 호출 0. KIS endpoint / TR_ID 코드/테스트 추가 0.

### 12. Strategy / Agent / LLM 의 broker 직접 호출 추가 0 — OK

`app/ops/preflight.py` 가 `paper_engine` 과 `kis_broker` 인자를 받지만 **read-only** 로 `journal.trades` 길이 + 일반 attribute 만 점검 (호출 X). `kis_broker.place_order` / `cancel_order` 등 호출 부재 (`grep "kis_broker.place_order\|kis_broker.cancel_order" app/ops app/api app/static` → 0).

## Safety regression (전체 OK)

| 항목 | 결과 |
| --- | --- |
| live trading 활성화 코드 / live arm UI / live order 버튼 / dry-run disable toggle / market allow toggle 0 | OK |
| `/ops/*` GET only | OK (POST/PUT/DELETE/PATCH 0) |
| 새 settings 가 enforcement 게이트로 소비 안 됨 | OK (grep 으로 확인) |
| `live_validation_ready` 가 코드 단의 게이트 풀기에 사용 안 됨 | OK (UI 표시만) |
| 14 개 preflight checklist item | OK |
| Banner 3 단 escalation (info/warning/danger) + 한국어 텍스트 | OK |
| Dashboard 금지 버튼 부재 | OK (회귀 테스트로 강제) |
| `KisBroker.*` 본문 무변동 | OK |
| `validate_kis_order_request` / `_validate_paper_settings` 무변동 | OK |
| `OrderType.MARKET` 가드 / `OrderType.STOP` 미도입 / FX 미도입 | OK |
| `capabilities()` 모든 플래그 `False` 유지 | OK |
| `order_execution_implemented` `False` 유지 | OK |
| `app/broker/*` / `app/oms/*` / `app/risk/*` / `app/portfolio/*` / `app/runtime/*` / `app/strategy/*` / `app/session/*` / `app/domain/*` / `app/api/server.py` / `app/main.py` 무변동 | OK |
| `.env` / `.env.example` 무변동 | OK |
| `docs/kis/MISSING_OFFICIAL_VALUES.md` 무변동 | OK |
| 외부 HTTP 라이브러리 import 0 | OK |
| secret / 계좌번호 / token / Bearer 노출 0 | OK |
| README 필수 문장 ("live_validation_ready=READY 가 표시되어도 실제 live 주문을 전송할 코드 경로를 보유하지 않습니다") 포함 | OK |
| commit / push / merge / deploy 수행 0 | OK |

## 테스트 검증 (재실행 결과)

```text
$ cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
$ .venv/bin/python -m pytest -p no:cacheprovider --tb=no -q
547 passed in 0.88s
```

520 baseline + 27 new = 547. 회귀 0 건. patch.md 의 547 카운트와 정확히 일치.

`tests/test_ops_preflight.py` + `tests/test_ops_endpoints.py` + `tests/test_dashboard.py` 좁은 추가 = 35 passed (patch.md §4 의 35 와 일치).

## Findings (severity 순)

### F1 (INFO) — patch.md 의 후속 prompt 가 master plan §10 의 "동시 2 개 이상 Codex 구현 지시 금지" 원칙과 정합

`docs/ai/jobs/live-validation-001/patch.md` 의 follow-up Codex prompt 규칙이 명시적으로 "Apply only the specific review-requested fix" + "Do not change broker/OMS/risk/runtime/strategy/domain files, secrets, .env, auth, payment, infra, migrations, KIS endpoints/TR IDs/payloads/headers, or live trading behavior" 를 못 박음. 본 review 가 추가로 강제할 사항 없음.

### F2 (INFO) — Phase 5 미진입 명시적 보존

`README.md:448` 의 explicit 문장 외에도 `README.md:384` 의 운영자 guide 섹션이 "실거래 전 필요한 조건" 을 별도 future job 으로 분리. master plan §6 Phase 5 의 "manual arm + actual live transmission with separate explicit user approval + Phase 5 condition recheck" 원칙 정합. **본 review 는 어떤 future activation 작업도 승인하지 않음**.

### F3 (INFO) — 새 settings 의 enforcement 미연결은 의도된 design

`live_validation_daily_loss_limit_usd` / `live_validation_max_orders_per_day` 가 코드 어디서도 차단 게이트로 쓰이지 않음. plan §4.5 의 명시적 결정 — "status-reporting only / Future job 에서 enforce 추가 시까지 operator-side reminder". 본 review 는 enforcement 도입을 강제하지 않음 (별 future job).

## Final Checklist

| 항목 | 결과 |
| --- | --- |
| 1. live trading 비활성 유지 | OK |
| 2. `/ops/*` GET only (POST/PUT/DELETE/PATCH 0) | OK |
| 3. live arm / live enable / dry-run disable / market allow toggle 부재 | OK |
| 4. `KisBroker.place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` 본문 무변동 | OK |
| 5. `validate_kis_order_request` / `_validate_paper_settings` / `OrderType.MARKET` 가드 / `OrderType.STOP` 미도입 / FX 미도입 | OK |
| 6. KIS endpoint / TR ID / payload / header / response field 추측 0 | OK |
| 7. 외부 HTTP 라이브러리 import 0 | OK |
| 8. `app/broker/*` / `app/oms/*` / `app/risk/*` / `app/portfolio/*` / `app/runtime/*` / `app/strategy/*` / `app/session/*` / `app/domain/*` / `app/api/server.py` / `app/main.py` 무변동 | OK |
| 9. `.env` / `.env.example` / `docs/kis/MISSING_OFFICIAL_VALUES.md` 무변동 | OK |
| 10. Strategy / Agent / LLM 의 broker 직접 호출 추가 0 | OK |
| 11. OMS / RiskEngine 우회 0 | OK |
| 12. `capabilities()` / `order_execution_implemented` 무변동 | OK |
| 13. 14 개 preflight checklist item | OK |
| 14. Banner 3 단 escalation 한국어 텍스트 | OK |
| 15. README 필수 문장 포함 | OK |
| 16. `live_validation_ready` UI hint only, 코드 게이트 소비 0 | OK |
| 17. 새 settings (daily_loss_limit / max_orders_per_day) enforcement 소비 0 | OK |
| 18. pytest 547 passed (520 baseline + 27 new) | OK |
| 19. compileall PASS | OK |
| 20. secret / 계좌번호 / token / Bearer 노출 0 | OK |
| 21. 안전 grep 모두 clean | OK |
| 22. commit / push / merge / deploy 수행 0 | OK |

## Follow-up Codex prompt

없음. APPROVE.

다음 단계는 사용자가 직접:

1. (선택) `git diff` / `git status` 로 변경 범위 검토.
2. logical commit 분리 권고:
   ```bash
   # Commit 1 — backend (ops package + endpoints + config)
   git add projects/paper-trading/app/ops/ \
           projects/paper-trading/app/api/routes.py \
           projects/paper-trading/app/config.py
   git commit -m "feat(ops): live validation preflight readiness (read-only GET endpoints)"

   # Commit 2 — frontend (dashboard banner + sections)
   git add projects/paper-trading/app/static/dashboard.html
   git commit -m "feat(ui): live validation readiness banner + preflight checklist sections"

   # Commit 3 — docs (operator guide)
   git add projects/paper-trading/README.md
   git commit -m "docs: Korean operator guide for live validation preparation"

   # Commit 4 — tests (preflight + ops endpoints + dashboard narrow update)
   git add projects/paper-trading/tests/test_ops_preflight.py \
           projects/paper-trading/tests/test_ops_endpoints.py \
           projects/paper-trading/tests/test_dashboard.py
   git commit -m "test: live validation preparation regression (27 new tests)"

   # Commit 5 — job docs
   git add projects/paper-trading/docs/ai/jobs/live-validation-001/
   git commit -m "docs: record live-validation-001 plan/codex-task/patch/review"
   ```
3. push / PR / merge / deploy 는 **명시적 사용자 승인 후 수동**. live activation 은 본 시리즈에서 절대 진입하지 않음.

**중요**: master plan §6 Phase 5 의 진입 조건 (Phase 4 누적 soak 결과 + 명시적 사용자 승인 + master plan §1 안전 원칙 재확인 + 별도 plan-only audit job) 이 모두 충족된 별 future job 으로만 실제 live activation 가능. 본 review 는 그 future activation 을 승인하지 않음.

본 review 자체는 코드 / catalog 본문 / `.env` / GUI 어떤 파일도 수정하지 않음. commit / push / merge / deploy 수행 없음.
