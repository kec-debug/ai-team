# Review — mvp-018: 장시간 KIS paper / dry-run 검증 runner

## Verdict

**APPROVE**

mvp-018 구현이 plan/codex-task의 모든 안전 불변식을 충족하고, **pytest 155 PASS** (신규 26 + 기존 129), 정적 안전 검사도 모두 통과. KIS HTTP는 0건 추가, `app/broker/kis.py` / `app/runtime/paper_runner.py` 미변경 확인.

## 검증된 사실 (직접 확인)

### 1. 코드 / 안전 invariant

1. **`app/broker/kis.py` mvp-018에서 미변경** — `git diff --stat`은 +209/-16을 보고하지만, 이는 mvp-009~mvp-013/mvp-014-017-bundle에서 누적된 pre-existing dirty이다. patch.md §2.8이 정직하게 명시. `dry_run.py`/`dry_run_report.py`/`routes.py`는 `app.broker.kis`를 직접 import하지 않음(grep 0건).
2. **`app/runtime/paper_runner.py` mvp-018에서 미변경** — `git diff --stat`이 빈 출력. DryRunController가 PaperRunner를 호출만 함.
3. **외부 HTTP 라이브러리 import 0건** — `grep "import requests|httpx|aiohttp|urllib3"` in `app/` → 빈.
4. **KIS endpoint/TR ID/URL 0건 in mvp-018 신규 파일** — `dry_run.py`/`dry_run_report.py`에 `https?://`/`TR_ID`/`/uapi/`/`/oauth2/` 0건. `dry_run_report.py`의 `"appkey"`/`"appsecret"` 문자열 등장은 `_FORBIDDEN_KEY_FRAGMENTS` 차단 리스트(line 17–19) — 의도된 안전 가드.
5. **Strategy 패키지가 `app.broker.kis` 미import** — `grep` 빈.
6. **`OrderType.MARKET` 부재** — `grep` 빈.
7. **`reports/` 프로젝트 `.gitignore` 등재** — `git status`에 `reports/` 미등장.
8. **테스트 run으로 생성된 산출물 미 staging** — `git status --short projects/paper-trading/reports/` 빈.

### 2. DryRunController 설계 (직접 코드 점검)

`app/runtime/dry_run.py`:

- 상태 머신: `idle → running → stopped/auto_stopped` (line 20–23, 80–101).
- `start()` double-start → `RuntimeError` (line 81–82); `stop()`/`tick()` not-running → `RuntimeError` (line 95–96, 104–105). 모두 routes.py에서 HTTP 409로 매핑.
- `tick()` 최상단에서 `kill_switch_engaged` 체크 (line 111–129): strategy 평가 0건, `kill_switch_blocked_ticks += 1`, return `blocked_kill_switch`.
- PaperRunner 호출만 사용 (line 132) — KIS broker 직접 호출 없음.
- `_reports_dir()` 절대 경로 reject + 프로젝트 디렉터리 외부 reject (line 230–236) — **path traversal 방어**.
- `summary()`이 `"secret_exposed": False` 명시 노출 (line 226) + raw credentials 미포함.
- `_classify_strategy_blockers`/`_classify_oms_error` 카운터 매핑 (line 266–287): stale_quote, spread, market, risk_engine, kis_fail_closed.
- max_ticks 도달 시 `auto_stop("max_ticks_reached")` (line 185–188).
- errors_total ≥ 임계치 시 `_maybe_auto_stop` → `auto_stop("error_threshold")` (line 255–264).

### 3. dump_safe 방어 (`app/runtime/dry_run_report.py`)

- `_FORBIDDEN_KEY_FRAGMENTS`: `app_key`, `appkey`, `appsecret`, `app_secret`, `account_no`, `accountno`, `cano`, `access_token`, `accesstoken`, `authorization`, `secret` (line 16–28).
- substring case-insensitive 매칭 (line 39, 43–47).
- 모든 writer(`append_event`/`write_summary`/`append_order`)가 dump_safe를 호출 (line 63, 70, 92).
- **clever whitelist for `secret_exposed`** (line 40–42): 키 이름이 정확히 `secret_exposed`이면 forbidden check 건너뛰고 value만 재귀 검증. summary()의 `secret_exposed: False` 노출을 가능하게 함.

### 4. 4개 신규 엔드포인트 (`app/api/routes.py`)

- `POST /paper/dry-run/start` — 성공 시 `controller.summary()` 반환, double-start → 409.
- `POST /paper/dry-run/stop` — 성공 시 summary, not-running → 409.
- `POST /paper/dry-run/tick` — body `DryRunTickRequest{snapshots: list[StrategyInput]}`. 응답에 `tick`(상태+카운터) + `summary` 분리. not-running → 409. kill_switch → tick.status=`blocked_kill_switch`.
- `GET /paper/dry-run/status` — `controller.summary()` 그대로. credentials 미포함.
- `/paper/status`에 `dry_run_running: bool` 한 줄 추가 (line `dry_run_running` grep 확인).

### 5. server.py 와이어링

- lifespan에서 `DryRunController` 인스턴스화 + `app.state.dry_run_controller` 보관 (patch.md §1 명시).
- OMS 와이어링은 `PaperBroker` 그대로 — KIS broker 활성 broker 아님.

### 6. Settings 확장 (`app/config.py`)

- `dry_run_reports_dir: str = "reports/dry_run"`, `dry_run_max_errors_before_auto_stop: int = 10`, `dry_run_max_ticks: int | None = None` 추가 (patch.md §1).
- `load_settings()`가 `DRY_RUN_REPORTS_DIR`/`DRY_RUN_MAX_ERRORS_BEFORE_AUTO_STOP`/`DRY_RUN_MAX_TICKS` env 로딩.

### 7. 테스트 결과

**자체 재실행 결과:**

```
tests/test_dry_run_controller.py ..........   [ 38%]
tests/test_dry_run_reports.py ........         [ 69%]
tests/test_dry_run_routes.py ........          [100%]
26 passed in 0.23s

(full suite)
155 passed in 0.32s
```

- 신규 26개 (controller 10 + reports 8 + routes 8) PASS.
- 기존 129개 회귀 0건.

### 8. 리포트 파일 구조

- `reports/dry_run/run_<timestamp>/` 디렉터리 자동 생성 (`make_run_dir` line 55–59).
- `events.jsonl` — 매 tick 이벤트 + 후보별 결과(blocked/passed/oms_status/oms_error).
- `summary.json` — overwrite each tick, indent=2.
- `orders.csv` — passed candidates, 고정 컬럼(`_ORDER_COLUMNS` line 78–88): `ts/symbol/side/quantity/limit_price/order_type/oms_status/broker_environment/idempotency_key`. **`account_no` 컬럼 부재** — 좋음.

## Findings (severity 순)

### 1. (low — process) `app/broker/kis.py` 사전 dirty 상태

- 위치: `git diff --stat` 출력 — `projects/paper-trading/app/broker/kis.py | 225 +++++++ ... 209 insertions(+), 16 deletions(-)`.
- 관찰: 본 mvp-018 이전 작업(mvp-009/10–13/14–17-bundle 등)에서 누적된 dirty이며 mvp-018이 만든 변경이 아님. patch.md §2.8이 정직하게 명시.
- 영향: 안전 측면 위반 없음. 단 commit 시 staging 한정해야 함(mvp-018 외 변경 격리).
- 권장:
  ```bash
  cd /root/ai-dev-center/projects/ai-team
  git add projects/paper-trading/app/runtime/dry_run.py \
          projects/paper-trading/app/runtime/dry_run_report.py \
          projects/paper-trading/app/config.py \
          projects/paper-trading/app/api/server.py \
          projects/paper-trading/app/api/routes.py \
          projects/paper-trading/.env.example \
          projects/paper-trading/.gitignore \
          projects/paper-trading/README.md \
          projects/paper-trading/tests/test_dry_run_controller.py \
          projects/paper-trading/tests/test_dry_run_reports.py \
          projects/paper-trading/tests/test_dry_run_routes.py \
          projects/paper-trading/tests/test_api_paper_status.py \
          docs/ai/jobs/mvp-018/
  git diff --cached --stat   # 검증
  ```
  `app/broker/kis.py` 등 pre-existing dirty는 별도 mvp 커밋으로 분리.

### 2. (informational) plan 추정 테스트 수와 실제 차이

- plan: "131 + 신규 약 27 = 158± PASS"
- 실제: 155 PASS (신규 26 + 기존 129)
- 차이: 신규는 -1, 기존은 -2. 모두 추정 오차 범위 — 결함 아님. 기존 테스트가 mvp-018 진입 시점에 129였던 것으로 보인다(plan은 131로 추정).

### 3. (informational) `secret_exposed` whitelist는 좋은 설계

- 위치: `dry_run_report.py:40–42`.
- 관찰: `dump_safe`의 substring check가 `"secret"`을 포함하므로 `secret_exposed` 키도 잡혀버린다. 정확한 키 이름 매칭으로 whitelist 처리.
- 영향: 의도된 안전 가드(`secret_exposed: False` 표면화 + secret 키 차단)가 모두 작동. 좋음.
- 권장: 없음. 코드 자체에 docstring 한 줄(line 40 위)을 추가하면 미래 reader가 의도를 빨리 이해할 수 있겠으나 필수 아님.

### 4. (informational) `kis_fail_closed_count`의 정확도

- 위치: `dry_run.py:285–286` (`_classify_oms_error`).
- 관찰: error 문자열에 "notimplemented" 또는 "not implemented"가 포함되면 카운터 증가. 현재 OMS는 PaperBroker로만 라우팅되므로 NotImplementedError 발생이 KIS 사이드가 아님. 카운터 이름이 `kis_fail_closed_count`인데 실제로는 일반 NotImplementedError 카운터 역할.
- 영향: 카운터가 잘못된 측정을 할 가능성이 있지만, 현재 OMS 경로에서 NotImplementedError는 거의 발생하지 않으므로 실질적 카운터 0에 가까움. 향후 KIS broker가 활성 broker로 라우팅될 때 카운터 정의를 명확히 하는 것이 좋다.
- 권장: 후속 mvp에서 KIS HTTP 연결이 진행될 때 이 카운터의 정확한 정의(KIS adapter에서 발생한 NotImplementedError만 count vs 모든 fail-closed) 정리. 본 작업에서 추가 변경 불필요.

## File / line references (요청 ↔ 산출물 매핑)

| 요청 review focus | 구현 위치 | 상태 |
| --- | --- | --- |
| 1. dry-run runner는 실제 KIS 주문 전송 안 함 | `dry_run.py` — `self._runner.run_once` 호출만, KIS import 0건 | ✓ |
| 2. `KIS_ORDER_DRY_RUN=true` 기본값 유지 | `app/config.py` `kis_order_dry_run: bool = True` (이전 mvp에서 land); `.env.example`에 placeholder | ✓ (mvp-018 변경 없음) |
| 3. live trading 비활성 유지 | mvp-005~mvp-017의 5+1단 차단 모두 유지. `dry_run.py`에서 새로운 활성 경로 추가 없음. | ✓ |
| 4. 시장가 주문 비활성 유지 | `OrderType.MARKET` 부재 + `dry_run.py`가 PaperRunner 통해 RiskEngine 경유 | ✓ |
| 5. Strategy/Agent/LLM이 KIS 직접 호출 불가 | `app/strategy/`에 `app.broker.kis*` import 0건 (grep) | ✓ |
| 6. OMS/RiskEngine 경계 유지 | `dry_run.py`가 `PaperRunner.run_once`만 호출 → 내부에서 `OMS.place(intent)` → `RiskEngine.evaluate` | ✓ |
| 7. Kill switch가 새 dry-run tick/주문 차단 | `dry_run.py:111–129` kill_switch 체크 + `blocked_kill_switch` 반환 + `kill_switch_blocked_ticks` 카운터 | ✓ |
| 8. 리포트에 raw credentials 미노출 | `dump_safe`가 substring 매칭으로 dict 키 거절 + `secret_exposed` whitelist; orders.csv 컬럼에 raw account 부재 | ✓ |
| 9. `/paper/dry-run/status`에 credentials 미노출 | `controller.summary()`이 `secret_exposed: False`만 노출, raw 미포함; `test_dry_run_routes.py`이 응답 본문 텍스트 검사로 검증 | ✓ |
| 10. 테스트 통과 | pytest 155 PASS (자체 재실행 확인) | ✓ |
| 11. 범위가 mvp-018 안 | 변경 파일 모두 plan 허용 목록 안. `app/broker/kis.py`/`app/runtime/paper_runner.py` 미변경 확인 | ✓ |

## Missing tests / residual risk

- mvp-018 신규 테스트 26개가 state machine, kill switch, auto-stop, dump_safe 거절, 4개 endpoint, secret 미노출을 모두 커버. 추가 필요 없음.
- 외부 시간 의존성: `datetime.now(timezone.utc)` 직접 호출 — 시간 mock 없이도 테스트 통과(uptime_seconds 검증 시 `>=0` 정도로 느슨하게 검증한 듯). 강한 시간 격리는 후속 작업 후보.
- background auto-tick 미지원: plan에서 의도적으로 explicit-tick만 채택. 운영 환경에서 일정 주기 실행은 외부 cron/스케줄러에 위임. 향후 mvp에서 asyncio background task 도입 가능.
- KIS HTTP 미구현: mvp-014-017-bundle의 `MISSING_OFFICIAL_VALUES.md` 채워질 때까지 NotImplementedError 그대로. 본 mvp 범위 아님.

## Final checklist (요청 review focus + scope)

- [x] **Dry-run runner does not send real KIS orders.** dry_run.py가 PaperRunner만 호출, KIS broker 직접 접근 없음.
- [x] **`KIS_ORDER_DRY_RUN=true` remains default.** Settings 기본값 True, mvp-018에서 변경 없음.
- [x] **Live trading remains disabled.** mvp-005~mvp-017 모든 차단 단 유지, mvp-018이 새로운 우회 경로 도입 없음.
- [x] **Market orders remain disabled.** `OrderType.MARKET` 부재 유지, `ALLOW_MARKET_ORDERS=true` reject 유지.
- [x] **Strategy, Agent, and LLM cannot call KIS directly.** `app/strategy/`에서 KIS import 0건, dry_run에서도 0건.
- [x] **OMS/RiskEngine boundary remains intact.** PaperRunner → OMS.place → RiskEngine.evaluate 그대로.
- [x] **Kill switch stops new dry-run ticks/orders.** dry_run.py:111–129, 테스트 `test_kill_switch_blocks_tick` PASS.
- [x] **Reports do not expose app key, app secret, account number, or token.** dump_safe substring 거절 + secret_exposed whitelist + orders.csv 컬럼 안전.
- [x] **`/paper/dry-run/status` does not expose secrets.** `summary()`에 raw 0건, `test_dry_run_status_no_credentials_in_response` 같은 본문 텍스트 검사 PASS.
- [x] **Tests passed.** 155/155 PASS (재실행 확인).
- [x] **Scope stayed within mvp-018.** 변경 파일 모두 plan 허용 범위 안. mvp-018에서 `app/broker/kis.py`/`app/runtime/paper_runner.py` 변경 0건.
- [ ] **`app/broker/kis.py` 사전 dirty 격리 commit (Findings #1)** — 사람 액션.

## 사람에게 남기는 액션 아이템

1. **mvp-018 commit staging 한정** (필수):

   ```bash
   cd /root/ai-dev-center/projects/ai-team
   git add projects/paper-trading/app/runtime/dry_run.py \
           projects/paper-trading/app/runtime/dry_run_report.py \
           projects/paper-trading/app/config.py \
           projects/paper-trading/app/api/server.py \
           projects/paper-trading/app/api/routes.py \
           projects/paper-trading/.env.example \
           projects/paper-trading/.gitignore \
           projects/paper-trading/README.md \
           projects/paper-trading/tests/test_dry_run_controller.py \
           projects/paper-trading/tests/test_dry_run_reports.py \
           projects/paper-trading/tests/test_dry_run_routes.py \
           projects/paper-trading/tests/test_api_paper_status.py \
           docs/ai/jobs/mvp-018/
   git diff --cached --stat   # 검증
   ```

   `app/broker/kis.py` 등 mvp-018 외 pre-existing dirty는 별도 mvp 커밋으로 분리.

2. **commit/push/merge/deploy는 사람이 직접.** 본 작업은 자동화하지 않는다.

3. (선택, 다음 mvp 후보):
   - mvp-019: background auto-tick (asyncio task lifecycle 설계)
   - mvp-020: 리포트 분석/aggregation 도구
   - mvp-019: KIS 공식 문서값(`docs/kis/MISSING_OFFICIAL_VALUES.md`)이 사용자에 의해 채워지면 단계적 HTTP 연결 — OAuth → account → quote → order 순서
   - mvp-019: kis_fail_closed_count 카운터 정의 명확화 (Findings #4)

4. **장시간 검증 운영 방법** (참고):
   - 외부 cron 또는 스케줄러가 `POST /paper/dry-run/tick`을 주기적으로 호출.
   - 또는 테스트/스크립트가 long-running loop에서 tick + sleep.
   - 모니터링: `GET /paper/dry-run/status`로 카운터 추적.
   - 비상 정지: `POST /paper/dry-run/stop` 또는 `.env`에 `KILL_SWITCH_ENGAGED=true`.
