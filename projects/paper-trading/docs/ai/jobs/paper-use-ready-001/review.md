# paper-use-ready-001 — Claude Review

## Verdict

APPROVE

## Summary

paper-use-ready-001 은 **앱 코드 무변동 / tooling + docs + scripts + 1 신규 TestClient 회귀** 라는 plan 원칙을 정확히 지켰다. 5 개 신규 스크립트 (`stop_server.sh` / `restart_server.sh` / `use_ready_check.sh` / `safety_grep.sh` + `tests/test_use_ready_smoke.py`) + 2 개 좁은 추가 (`status.sh` / `smoke_check.sh`) + 2 개 신규 한국어 docs (`docs/RUNBOOK.md` / `docs/OPS_AUDIT.md`) + README append. 547 baseline + 10 new = 557 passed. safety_grep ALL OK. `git add -A` 권장 0 (오히려 명시적 prohibition 명시). live trading / market guard / OMS / Risk / KIS adapter 무변동.

## Scope of changes (이번 job 의 in-scope)

**In-scope, intentional (paper-use-ready-001 가 생성/수정)**:

- `scripts/stop_server.sh` (NEW, executable) — uvicorn PID SIGTERM + 5초 후 SIGKILL fallback, idempotent.
- `scripts/restart_server.sh` (NEW, executable) — stop + sleep 1 + exec start wrapper.
- `scripts/use_ready_check.sh` (NEW, executable) — server reachable + smoke + safety + compileall + pytest + git status 마스터 점검.
- `scripts/safety_grep.sh` (NEW, executable) — 9 종 안전 grep helper, OK/FAIL 라인 + nonzero exit on failure.
- `scripts/status.sh` (MODIFY, +6 lines) — `/ops/status` + `/ops/preflight` curl 추가.
- `scripts/smoke_check.sh` (MODIFY, +29 lines) — ops endpoints + paper simulation 예시 + 종료 라인 추가.
- `docs/RUNBOOK.md` (NEW, 한국어 운영 가이드) — PuTTY 안내 + 명령 cheat sheet + 문제 해결.
- `docs/OPS_AUDIT.md` (NEW, 한국어 최종 ops 안전 감사) — 6 단 live trading 차단 / 3 중 market guard / KIS 안전 경계 / Strategy/Agent/LLM 격리 / 운영 체크리스트.
- `README.md` (MODIFY, +99 lines) — append-only "운영 스크립트 명령 정리" + RUNBOOK / OPS_AUDIT 링크 + git 운영 원칙. 기존 섹션 무변동.
- `tests/test_use_ready_smoke.py` (NEW, 10 tests) — TestClient HTTP 스모크 회귀.
- `docs/ai/jobs/paper-use-ready-001/patch.md` + `status.md` (NEW).

**Out-of-scope, pre-existing dirty (NOT from this job — 이전 live-validation-001 의 commit 대기 잔재)**:

- `M app/api/routes.py` / `M app/config.py` / `M app/static/dashboard.html` — live-validation-001 의 `/ops/*` endpoint + settings 필드 + dashboard 섹션 추가 (이전 job).
- `?? app/ops/` — live-validation-001 의 preflight 패키지.
- `?? tests/test_ops_endpoints.py` — live-validation-001 의 endpoint 회귀.
- `?? docs/ai/jobs/live-validation-001/` — live-validation-001 의 job 문서.

patch.md §1 의 "No `app/` file was edited for this job" + §5 의 "Pre-existing live-validation-001 dirty entries" 분류가 정확하다. paper-use-ready-001 단독으로는 `app/` 어떤 파일도 수정하지 않았음을 확인.

## Review focus 항목별 검증

### 1. Server start/stop/status workflow 가 초보자 친화 — OK

- `stop_server.sh` (16:25 의 `pgrep -f "uvicorn app.api.server" || true`) 가 본 프로젝트 uvicorn 만 식별 (다른 uvicorn 영향 없음). SIGTERM 후 5초 graceful, SIGKILL fallback. 미실행 시 exit 0 (idempotent).
- `restart_server.sh` 가 단순 `stop → sleep 1 → exec start` wrapper — 16:19 의 모든 4 개 파일 chmod +x 확인.
- README append (line 99) + RUNBOOK §명령 cheat sheet 가 모든 스크립트 호출법을 한국어로 정리.

### 2. Dashboard 접속 안내 정확 — OK

- RUNBOOK 의 PuTTY 섹션이 Source port 8000 + Destination 127.0.0.1:8000 + Local 선택 + Add 명시.
- 브라우저 주소 `http://127.0.0.1:8000/dashboard` 명확.

### 3. Dry-run smoke 흐름 동작 — OK

- `smoke_check.sh` 기존 단계 (status / start_dry_run / tick / analyze / latest / stop_dry_run) 그대로 + 신규 ops endpoints + paper simulation 예시 추가.
- `tests/test_use_ready_smoke.py::test_smoke_dry_run_lifecycle` 가 동일 흐름을 TestClient 로 회귀. 557 passed 에 포함.

### 4. Paper order simulation 점검 — OK

- `smoke_check.sh` 의 신규 paper simulation block (line 29 추가) 이 `POST /paper/order/simulate` 호출, 결과 pretty_print.
- `tests/test_use_ready_smoke.py::test_smoke_paper_order_simulate_demo` 가 `accepted=True` + `safety_flags.mode="paper"` + `live_trading_enabled=False` 회귀.

### 5. KIS 상태 read-only 표시 — OK

- `status.sh` 의 신규 `/ops/status` + `/ops/preflight` curl 이 live-validation-001 의 read-only endpoint 사용. paper-use-ready-001 자체는 새 endpoint 추가 0.
- KIS 상태 false 도 fail-closed 표시 — banner_level escalation 은 이전 job 의 `app/ops/preflight.py` 가 처리.

### 6. secret / 계좌번호 / token / Bearer / `.env` 노출 0 — OK

- 새 스크립트 4 개 + 수정 2 개 모두 `.env` 의 raw 값을 echo 하지 않음 (`grep -rn "echo.*KIS_APP_KEY\|echo.*KIS_APP_SECRET" scripts/` → 0).
- patch.md §7 의 safety_grep 결과 `[OK ] JWT-style secret 노출 (Bearer eyJ / access_token=eyJ)` 확인.
- `tests/test_use_ready_smoke.py::test_smoke_no_secrets_in_combined_responses` 가 7 개 endpoint 응답에서 `KIS_APP_KEY` / `KIS_APP_SECRET` / `KIS_ACCOUNT_NO` / `app_secret` / `access_token` / `Bearer ` 6 token 부재 회귀.

### 7. live trading 비활성 유지 — OK

- patch.md §6 의 "live_trading_enabled=True was not introduced" 명시.
- safety_grep 의 `[OK ] live trading 활성화 코드` 확인.
- 새 스크립트 어디서도 `LIVE_TRADING_ENABLED=true` 또는 `KIS_ORDER_DRY_RUN=false` 설정 0.
- `_common.sh` (paper-use-ready-001 이 손대지 않음) 의 안전 default export 그대로 유지.

### 8. Market order guard 유지 — OK

- patch.md §6 "OrderType.STOP was not introduced".
- safety_grep 의 `[OK ] market order guard 우회 (allow_market_orders=True)` + `[OK ] OrderType.STOP 도입` 확인.
- `validate_kis_order_request` / `_validate_paper_settings` 무변동.

### 9. Smoke check 가 실주문 안 보냄 — OK

- 새 paper simulation block 은 `POST /paper/order/simulate` 만 호출 — paper-only path (Risk → OMS → PaperBroker → PaperEngine).
- `KisBroker.place_order` / `cancel_order` / `replace_order` 호출 0 (scripts 어디서도). `tests/test_use_ready_smoke.py::test_smoke_paper_order_simulate_demo` 가 `live_trading_enabled is False` 단언으로 회귀.
- 신규 endpoint 추가 0, KIS endpoint 호출 0.

### 10. 테스트 통과 — OK

```text
$ .venv/bin/python -m pytest -p no:cacheprovider --tb=no -q
557 passed in 0.97s
```

547 baseline (live-validation-001) + 10 new = 557. 회귀 0. compileall PASS.

### 11. Git status guidance 가 `git add -A` 권장 안 함 — OK

`grep "git add -A\|git add \-A" docs/RUNBOOK.md docs/OPS_AUDIT.md README.md scripts/*.sh` 결과:

```text
docs/RUNBOOK.md:227:`git status --short`로 파일을 확인하고, job별 logical commit으로 분리합니다. `git add -A`는 사용하지 않습니다.
```

유일한 매치가 **prohibition** ("사용하지 않습니다"). README append 의 "Git 운영 원칙" 절도 동일 원칙 명시. 권고 0.

### 12. Scope 가 paper-use-ready-001 안에 머묾 — OK

paper-use-ready-001 의 실제 변경 파일 (patch.md §1 + §5 분류 그대로):

- `scripts/stop_server.sh` / `restart_server.sh` / `use_ready_check.sh` / `safety_grep.sh` (4 NEW)
- `scripts/status.sh` / `smoke_check.sh` (2 narrow MODIFY)
- `docs/RUNBOOK.md` / `docs/OPS_AUDIT.md` (2 NEW)
- `README.md` (append only)
- `tests/test_use_ready_smoke.py` (1 NEW)
- `docs/ai/jobs/paper-use-ready-001/patch.md` + `status.md` (2 NEW)

`app/` 어떤 파일도 modify/create 하지 않음 (patch.md §1 명시 + git status 의 `M app/*` 는 pre-existing live-validation-001 dirty 로 정확히 분류됨). 다른 job 디렉터리 / `.env` / `.env.example` / `docs/kis/MISSING_OFFICIAL_VALUES.md` 무변동.

## Safety regression (전체 OK)

| 항목 | 결과 |
| --- | --- |
| `app/` 무변동 (paper-use-ready-001 한정) | OK |
| 새 endpoint 추가 0 | OK |
| dashboard.html 무변동 (paper-use-ready-001 한정) | OK |
| live trading 활성화 / market allow / dry-run disable toggle 0 | OK |
| `OrderType.STOP` / FX 변환 도입 0 | OK |
| KIS endpoint / TR ID / payload / header 추측 0 | OK |
| 외부 HTTP 라이브러리 import 0 (bash 는 `curl` + builtin 만) | OK |
| `.env` / `.env.example` 무변동 | OK |
| `docs/kis/MISSING_OFFICIAL_VALUES.md` 무변동 | OK |
| `git add -A` 권장 0 (RUNBOOK 의 prohibition 만 매치) | OK |
| 자동 git commit / push / merge / deploy 수행 0 | OK |
| Strategy / Agent / LLM 의 broker 직접 호출 추가 0 | OK |
| OMS / RiskEngine 우회 0 | OK |
| secret / 계좌번호 / token / Bearer 노출 0 (회귀 테스트 + safety_grep) | OK |
| 새 settings 필드 추가 0 | OK |
| 기존 test 변경 0 | OK |
| `_common.sh` 무변동 | OK |
| pytest 557 passed (547 baseline + 10 new) | OK |
| compileall PASS | OK |
| safety_grep.sh ALL OK | OK |

## Findings (severity 순)

### F1 (INFO) — patch.md 의 git status 분류가 정확

`git status` 의 6 개 modified + 11 개 untracked 중 paper-use-ready-001 변경은 11 entries, live-validation-001 잔재는 6 entries. patch.md §5 가 두 영역을 명확히 분류 — 사용자가 logical commit 시 혼동 방지.

### F2 (INFO) — safety_grep 의 JWT 제외 패턴이 OPS_AUDIT.md 자기참조 방지

patch.md §4 의 implementation note: "the JWT-style grep excludes `docs/OPS_AUDIT.md` so the audit's expected-output template does not self-match." OPS_AUDIT 에 안전 grep 예시가 들어 있어 self-match 를 피하기 위한 정당한 제외. safety_grep.sh 가 실제 코드 / 다른 docs 의 JWT 누출은 여전히 검출.

### F3 (INFO) — `use_ready_check.sh` 는 본 turn 에서 미실행 (의도)

patch.md §3 의 "I did not run `use_ready_check.sh` in this turn because it expects the server to be running" — Codex 가 서버를 자동 시작/중지하지 않은 것은 안전 정직 처리. 운영자가 server 시작 후 직접 실행하면 됨. 본 review 의 결정에 영향 없음.

### F4 (INFO) — paper-use-ready-001 자체 commit 은 사용자 결정

paper-use-ready-001 의 새 파일 (4 scripts + 2 docs + 1 test + 2 job docs) 과 좁은 modify (status.sh / smoke_check.sh / README.md) 가 모두 working tree 에. 사용자가 logical commit 으로 분리하면 됨. patch.md / RUNBOOK / README 모두 `git add -A` 금지 명시 — file-by-file 만 안내.

## Final Checklist

| 항목 | 결과 |
| --- | --- |
| 1. Server start/stop/status workflow beginner friendly | OK |
| 2. Dashboard access instructions correct (PuTTY + URL) | OK |
| 3. Dry-run smoke flow works | OK |
| 4. Paper order simulation check works | OK |
| 5. KIS status read-only display | OK |
| 6. secret / 계좌번호 / token / Bearer / `.env` 노출 0 | OK |
| 7. Live trading disabled | OK |
| 8. Market order guard intact | OK |
| 9. Smoke check 실주문 안 보냄 | OK |
| 10. pytest 557 passed | OK |
| 11. Git status guidance prohibits `git add -A` | OK |
| 12. Scope inside paper-use-ready-001 (no `app/` modification) | OK |
| compileall PASS | OK |
| safety_grep ALL OK | OK |
| commit / push / merge / deploy 수행 0 | OK |

## Follow-up Codex prompt

없음. APPROVE.

다음 단계는 사용자가 직접:

1. (선택) `git diff` / `git status` 로 변경 범위 검토.
2. logical commit 분리 권고 (paper-use-ready-001 의 변경은 4 그룹으로 나눌 수 있음 — README+RUNBOOK+OPS_AUDIT docs commit / scripts commit / test commit / job docs commit). RUNBOOK 의 git 운영 원칙대로 **file-by-file `git add <path>`**.
3. pre-existing live-validation-001 잔재 (`M app/api/routes.py` 등 6 entries) 는 별도 commit 으로 분리 권고 (paper-use-ready-001 과 섞지 말 것).
4. push / PR / merge / deploy 는 **명시적 사용자 승인 후 수동**.

권고 commit 분할 (5 그룹):

```bash
# Group 1 — paper-use-ready-001 scripts
git add projects/paper-trading/scripts/stop_server.sh
git add projects/paper-trading/scripts/restart_server.sh
git add projects/paper-trading/scripts/use_ready_check.sh
git add projects/paper-trading/scripts/safety_grep.sh
git add projects/paper-trading/scripts/status.sh
git add projects/paper-trading/scripts/smoke_check.sh
git commit -m "ops(scripts): server lifecycle + smoke + safety grep + use-ready check"

# Group 2 — paper-use-ready-001 docs
git add projects/paper-trading/docs/RUNBOOK.md
git add projects/paper-trading/docs/OPS_AUDIT.md
git add projects/paper-trading/README.md
git commit -m "docs: Korean operator RUNBOOK + final OPS_AUDIT + README operations cheat sheet"

# Group 3 — paper-use-ready-001 test
git add projects/paper-trading/tests/test_use_ready_smoke.py
git commit -m "test: TestClient smoke regression for paper-use-ready operations"

# Group 4 — paper-use-ready-001 job docs
git add projects/paper-trading/docs/ai/jobs/paper-use-ready-001/
git commit -m "docs: record paper-use-ready-001 plan/codex-task/patch/status/review"

# Group 5 — pre-existing live-validation-001 (별 commit, 본 review 와 무관)
# 이전 review.md 의 commit 권고 참조
```

본 review 자체는 코드 / catalog / `.env` / GUI 어떤 파일도 수정하지 않음. commit / push / merge / deploy 수행 없음.
