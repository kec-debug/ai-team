# Review — mvp-019: dry-run 결과 리포트 분석 + 전략 개선 루프 입력 문서

## Verdict

**APPROVE** (한 가지 plan 일탈을 process 노트로 기록)

mvp-019 구현이 plan/codex-task의 안전 불변식을 모두 충족하고, **pytest 172 PASS** (신규 17 + 기존 155), 정적 검사 모두 통과. analyzer 패키지가 구조적으로 broker/config/HTTP 모듈을 import하지 않아 raw credentials 접근 자체가 불가능. plan이 "절대 미수정"으로 지정한 `.gitignore`를 Codex가 한 줄 수정했으나(`reports/` → `/reports/`), 이 변경은 **필수적이고 안전하며 정당화됨** — 자세한 내용은 Findings #1 참조.

## 검증된 사실 (직접 확인)

### 1. 코드 / 안전 invariant

1. **`app/reports/`에 `app.broker.kis` / `app.config` import 0건**. `dry_run_analyzer.py`의 import는 `csv`, `json`, `collections`, `dataclasses`, `pathlib`, `typing`(stdlib only). 구조적 격리로 settings 접근 자체가 불가능.
2. **외부 HTTP 라이브러리 import 0건** in `app/reports/`. `grep "import requests|httpx|aiohttp|urllib3"` 빈.
3. **KIS endpoint URL/TR ID 0건** in `app/reports/`. `appkey`/`appsecret` 문자열 등장은 `_FORBIDDEN_KEY_FRAGMENTS` 차단 리스트(line 20, 22) — 의도된 안전 가드.
4. **`OrderType.MARKET` 부재 유지** in `app/`.
5. **Strategy 패키지가 `app.broker.kis` 미import** (mvp-018 시점 그대로).
6. **mvp-018에서 만든 `app/runtime/dry_run.py`/`dry_run_report.py`/`paper_runner.py` 변경 0줄** (직접 grep 확인).
7. **`app/broker/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/domain/*`, `app/config.py`, `app/api/server.py`, `.env.example` 변경 0건** in mvp-019 scope (patch.md §1과 일치).

### 2. analyzer 동작 (직접 코드 점검)

`app/reports/dry_run_analyzer.py`:

- `dump_safe` substring 매칭 + `secret_exposed` whitelist (mvp-018 패턴과 일관).
- `load_summary`/`load_events`/`load_orders` robust 처리(파일 없음/빈 파일/invalid JSON).
- `analyze_run`이 events에서 symbol stat + top_block_reasons 집계, summary에서 counters 흡수, strategy_pass_rate 계산.
- `compute_suggestions` 휴리스틱: spread 비율 / stale_quote 비율 / market order / OMS 거절 비율 / pass_rate < 5% 등.
- `compute_warnings`가 errors_total / kis_fail_closed_count / kill_switch_blocked_ticks / invalid_event_lines 감지.
- `write_analysis_files`이 3개 파일 모두 `dump_safe` 통과 후 작성.
- `summary_payload["secret_exposed"] = False` 명시.

### 3. CLI + API (`app/reports/__main__.py`, `app/api/routes.py`)

- CLI: `python -m app.reports [--run-dir | --latest] [--reports-dir]`. exit code 0/1/2 분기.
- `POST /reports/dry-run/analyze` (body `AnalyzeRequest{run_dir: str | None}`) + `GET /reports/dry-run/latest`. 기존 mvp-018 라우트 보존.
- `_resolve_run_dir`이 path traversal 거절(`base not in candidate.parents and candidate != base`).
- 응답 dict가 `settings`의 raw 필드 미참조 — `_reports_base`만 `settings.dry_run_reports_dir`(path string) 사용.

### 4. 테스트 결과

자체 재실행:

```
tests/test_dry_run_analyzer.py: 11 PASSED
tests/test_reports_api.py:        6 PASSED
mvp-019 신규 합계: 17 PASSED

전체 suite: 172 passed in 0.38s
```

- 신규 17개 모두 PASS (analyzer 11 + API 6).
- 기존 155개 회귀 0건.
- API 테스트가 `test_response_does_not_leak_credentials`로 raw 미노출 명시 검증.
- `test_analyze_rejects_path_traversal`이 `../../../etc` 같은 입력 거절 검증.
- 테스트 cleanup 정상 — `projects/paper-trading/reports/test_runs_mvp019/` 잔존 없음 확인.

### 5. `.gitignore` 동작 검증

- `git check-ignore projects/paper-trading/reports/dry_run/run_test/foo` → ignored ✓ (런타임 출력 보호)
- `git check-ignore projects/paper-trading/app/reports/dry_run_analyzer.py` → exit 1 (NOT ignored) ✓ (신규 패키지 추적 가능)

### 6. 출력 파일 구조 (`/run_<ts>/` 내부)

- `analysis_summary.json` — `secret_exposed: false` 명시, raw credentials 0건.
- `analysis_report.md` — 사람용 마크다운, safety 단락 포함.
- `claude_review_input.md` — Claude/Codex가 전략 개선 plan을 작성할 때 참고할 입력 문서. **"LLM/Agent가 본 문서를 읽어도 직접 주문을 만들거나 KIS를 직접 호출하지 않습니다"** 명시.

## Findings (severity 순)

### 1. (low — plan deviation) `projects/paper-trading/.gitignore` 한 줄 수정

- 위치: `projects/paper-trading/.gitignore` line 마지막 — `reports/` → `/reports/`.
- 관찰: plan §2 "절대 미수정" 목록에 "프로젝트 `.gitignore`"가 포함되어 있었지만 Codex가 한 줄 수정했다. patch.md §2.8이 사유를 정직하게 명시: 기존 `reports/` 패턴은 새 `app/reports/` 디렉터리도 매칭하여 analyzer 소스 코드 자체가 git에서 사라짐. `/reports/` (leading slash로 루트 상대 패턴화)로 좁히면 `projects/paper-trading/reports/`(런타임 출력)만 무시되고 `app/reports/`(소스)는 추적된다.
- 영향: **이 변경 없이는 mvp-019가 작동할 수 없다.** analyzer 패키지가 git-ignored 되면 신규 코드 + 테스트가 모두 사라진다. 본 검사로 동작 확인:
  - `git check-ignore projects/paper-trading/reports/dry_run/run_test/foo` → ignored (런타임 출력 보호 유지) ✓
  - `git check-ignore projects/paper-trading/app/reports/dry_run_analyzer.py` → not ignored (analyzer 추적 가능) ✓
- 정책 평가: plan이 과도하게 엄격했다(rigorous하게는 plan이 `.gitignore` 수정을 미리 허용했어야 했다 — 또는 `app/reports/` 대신 다른 위치를 선택했어야 했다). Codex가 plan 위반을 인지하지 못한 것이 아니라(patch.md에 명시) **최소 필요 변경 + 사유 문서화**로 처리했다.
- 권장: 본 review에서 변경을 인정. 향후 plan 작성 시 "신규 패키지 이름이 기존 ignore 패턴과 충돌할 수 있는지" 사전 점검을 plan 단계에 포함하는 것이 좋다.
- 안전 영향 평가: 0. 런타임 출력은 여전히 ignored. 분석 산출물도 같은 디렉터리에 떨어지므로 자동 ignored. credentials 노출 위험 변화 없음.

### 2. (informational) analyzer 패키지의 구조적 격리

- 위치: `app/reports/dry_run_analyzer.py`, `app/reports/render.py`, `app/reports/__main__.py`.
- 관찰: analyzer는 `app.broker.kis`/`app.config`/외부 HTTP 라이브러리를 import하지 않으며, settings 객체조차 받지 않는다(`Path`만 받음). API routes.py에서 `settings.dry_run_reports_dir`(path string)만 참조하여 base path 산출.
- 영향: 좋음. 구조적으로 credentials/HTTP/strategy/oms/risk/broker에 닿을 수 없어 안전 표면이 매우 작음. defense-in-depth(`dump_safe`)와 함께 이중 보호.
- 권장: 향후 mvp가 analyzer를 확장할 때 이 격리 원칙 유지.

### 3. (informational) 휴리스틱 suggestions의 한계

- 위치: `dry_run_analyzer.py:compute_suggestions`.
- 관찰: 단순 비율 기반 휴리스틱(스프레드 30% 초과 / stale 30% 초과 / OMS 50% 초과 등). false-positive 가능성 존재.
- 영향: `claude_review_input.md`에 "heuristic — human must validate"가 명시되어 있으므로 사람이 검토하는 한 큰 위험 없음.
- 권장: 사용 누적되면 임계값을 settings로 노출하거나 룰 엔진화 고려(별도 mvp).

### 4. (informational) `app.config` import 0건 검증

- patch.md 검증 결과와 plan §5 §4 모두 통과.
- API routes.py에서만 `request.app.state.settings`를 사용해 `dry_run_reports_dir`(path string) 추출 — credentials 미접근.

## File / line references (요청 ↔ 산출물 매핑)

| 요청 review focus | 위치 | 상태 |
| --- | --- | --- |
| 1. 빈 dry-run 파일 분석 가능 | `tests/test_dry_run_analyzer.py:test_analyze_empty_run` | PASS |
| 2. 정상 events 분석 | `test_analyze_populated_run` | PASS |
| 3. block reason 집계 | `test_analyze_populated_run`이 spread_too_wide=2, stale_quote=1 검증 | PASS |
| 4. symbol별 통계 | `test_analyze_populated_run`이 AAPL(seen=2,passed=1) MSFT(seen=1,blocked=1) | PASS |
| 5. strategy pass rate | `test_analyze_populated_run`이 1/3 검증 | PASS |
| 6. analysis_summary.json 생성 | `test_write_analysis_files_creates_three_outputs` | PASS |
| 7. analysis_report.md 생성 | 동상 | PASS |
| 8. claude_review_input.md 생성 | 동상 | PASS |
| 9. secret/account/token 미노출 | `test_outputs_do_not_leak_fake_credentials`, `test_response_does_not_leak_credentials`, `test_dump_safe_*` | PASS |
| 10. 기존 테스트 계속 통과 | 전체 172/172 PASS, 회귀 0건 | ✓ |

| 요청 안전 조건 | 결과 |
| --- | --- |
| live trading 비활성 | analyzer가 settings 미접근, mvp-018 차단 단 그대로 유지 ✓ |
| `KIS_ORDER_DRY_RUN=true` 기본값 | 미변경 ✓ |
| 시장가 주문 금지 | `OrderType.MARKET` 부재 유지 ✓ |
| 실제 주문 전송 금지 | analyzer는 read-only, OMS/Broker 미호출 ✓ |
| Strategy가 KIS 직접 호출 금지 | 변경 없음 ✓ |
| Agent/LLM이 직접 주문 금지 | claude_review_input.md가 명시적으로 advisory only 선언 ✓ |
| OMS/RiskEngine 우회 금지 | analyzer가 도메인 코드에 닿지 않음 ✓ |
| KIS app key/secret/account/token 리포트 노출 금지 | `dump_safe` 차단 + 본문 텍스트 검사 테스트 ✓ |

## Missing tests / residual risk

- 17개 신규 테스트가 happy path + edge case + path traversal + secret 미노출 + dump_safe 거절을 모두 커버. 추가 필요 없음.
- 잠재적 corner case (analyzer 사용 시 동시 dry-run 진행 중 write race) — 본 mvp 범위 밖. 단일 run_dir에 dry-run write + analyzer write가 시간적으로 분리되면 안전. plan에서도 명시적으로 다루지 않음. 운영 환경에서 사용자가 stop 후 analyze하는 패턴 권장.
- 휴리스틱 false-positive 가능성 — Findings #3 참조.

## Final checklist (요청 review focus + scope)

- [x] **빈 dry-run 파일 분석 가능** — `test_analyze_empty_run` PASS.
- [x] **정상 events 분석 가능** — `test_analyze_populated_run` PASS.
- [x] **block reason 집계 가능** — `top_block_reasons` 검증.
- [x] **symbol별 통계 가능** — `SymbolStat` 누적.
- [x] **strategy pass rate 계산 가능** — `1/3` 검증.
- [x] **analysis_summary.json 생성** — `secret_exposed: false` 포함.
- [x] **analysis_report.md 생성** — safety 단락 포함.
- [x] **claude_review_input.md 생성** — advisory only 명시.
- [x] **secret/account/token 미노출** — `dump_safe` + 본문 검사 테스트.
- [x] **기존 테스트 계속 통과** — 155개 회귀 0건.
- [x] **Scope stayed within mvp-019** — `app/broker/`, `app/runtime/`, `app/oms/`, `app/risk/`, `app/strategy/`, `app/domain/`, `app/config.py`, `app/api/server.py`, `.env.example`, 루트 `.gitignore` 모두 미변경. 단 프로젝트 `.gitignore` 한 줄 변경(Findings #1).
- [ ] **워크트리 staging 격리 — 사람 액션** (Findings #1 변경 포함하여 commit).

## 사람에게 남기는 액션 아이템

1. **mvp-019 commit staging 한정** (필수):

   ```bash
   cd /root/ai-dev-center/projects/ai-team
   git add projects/paper-trading/app/reports/ \
           projects/paper-trading/app/api/routes.py \
           projects/paper-trading/README.md \
           projects/paper-trading/.gitignore \
           projects/paper-trading/tests/test_dry_run_analyzer.py \
           projects/paper-trading/tests/test_reports_api.py \
           docs/ai/jobs/mvp-019/
   git diff --cached --stat
   ```

   `projects/paper-trading/.gitignore`는 mvp-019의 의도된 한 줄 변경(`reports/` → `/reports/`) 포함. 그 외 워크트리 pre-existing dirty는 별도 commit으로 분리.

2. **commit/push/merge/deploy는 사람이 직접.** 본 작업은 자동화하지 않는다.

3. **다음 단계 후보**:
   - **mvp-020 (가장 자연스러운 다음 단계)**: 생성된 `claude_review_input.md`를 Claude에게 입력으로 주어 전략 개선안 plan/codex-task를 작성하게 한다. 이 mvp에서는 `app/strategy/premarket_gap.py` 또는 `app/config.py`의 임계값을 사람 검토 하에 조정.
   - **mvp-021**: multi-run trend 분석(여러 run_dir 비교).
   - **mvp-022**: 분석 결과 시각화/대시보드.
   - **계속 보류**: KIS 공식 문서값(`docs/kis/MISSING_OFFICIAL_VALUES.md`)이 사용자에 의해 채워지기 전까지 KIS HTTP 연결.

4. **장시간 검증 사이클 운영 방법** (mvp-018 + mvp-019 결합):
   - `POST /paper/dry-run/start` → 외부 cron이 일정 간격으로 `POST /paper/dry-run/tick` → `POST /paper/dry-run/stop`.
   - 정지 후 `POST /reports/dry-run/analyze` 호출하여 분석 산출물 생성.
   - 또는 CLI `.venv/bin/python -m app.reports --latest`.
   - 사람이 `claude_review_input.md` 검토 후 다음 mvp의 plan 작성.
