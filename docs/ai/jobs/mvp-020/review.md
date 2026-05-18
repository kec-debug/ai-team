# Review — mvp-020: 초보자용 실행 스크립트 추가

## Verdict

**APPROVE**

mvp-020 구현이 plan/codex-task의 모든 안전 불변식을 충족하고, **pytest 181 PASS** (신규 9 + 기존 172), `bash -n` 전 스크립트 PASS, 정적 안전 검사 모두 통과. `app/` 코드 변경 0건 — 순수 shell scripts + 메타 테스트 + README 단락만 추가.

## 검증된 사실 (직접 확인)

### 1. 스크립트 / 안전 invariant

1. **8개 스크립트 모두 존재 + 실행 권한** (`ls -la scripts/`):
   - `_common.sh`, `start_server.sh`, `status.sh`, `start_dry_run.sh`, `tick.sh`, `stop_dry_run.sh`, `analyze.sh`, `smoke_check.sh` — 전부 `-rwxr-xr-x`.

2. **`bash -n scripts/*.sh` 종료코드 0** (8개 syntax 검증 PASS).

3. **`_common.sh`이 4개 안전 env force export**:
   ```bash
   export TRADING_MODE=paper
   export LIVE_TRADING_ENABLED=false
   export ALLOW_MARKET_ORDERS=false
   export KIS_ORDER_DRY_RUN=true
   ```
   `.env`/Settings 값이 무엇이든 shell 단에서 paper 강제. python-dotenv는 기존 env를 override하지 않으므로 이 export가 우선.

4. **`start_server.sh`이 `127.0.0.1`에만 바인딩** (line 13): `exec .venv/bin/uvicorn app.api.server:app --host 127.0.0.1 --port "$PORT"`. `0.0.0.0` grep 0건.

5. **금지 패턴 0건 in 모든 스크립트** (직접 grep):
   - `cat .env`: 0건
   - `KIS_APP_KEY`/`KIS_APP_SECRET`/`KIS_ACCOUNT_NO` (raw echo): 0건
   - `git commit`/`git push`: 0건
   - `pip install`: 0건

6. **`app/` 코드 변경 0건 by mvp-020**: `app/broker/kis.py`의 git diff는 +209/-16이지만 patch.md §103이 정직하게 "Existing unrelated dirty work remains in the wider worktree from previous MVPs"로 명시 — mvp-014-017/018에서 누적된 pre-existing dirty. mvp-020 자체는 scripts/ + tests/test_helper_scripts.py + README.md + patch.md만 변경.

### 2. 메타 테스트 9개 PASS (자체 재실행)

```
tests/test_helper_scripts.py: 9 passed
전체 suite: 181 passed in 0.39s
```

테스트가 검증하는 항목:
- 존재 / 실행 권한 / shebang / bash -n syntax
- `_common.sh`이 4개 안전 env force export
- 금지 패턴(`KIS_APP_KEY`/`KIS_APP_SECRET`/`KIS_ACCOUNT_NO`/`cat .env`/`${KIS_*}`) 부재
- 금지 명령(`git commit/push/merge`, `pip install`) 부재
- `start_server.sh`이 `127.0.0.1`만 바인딩, `0.0.0.0` 부재
- (plan은 7개 추정, 실제 9개 — Codex가 호환 패턴 변형 2개 추가, 모두 동일 카테고리로 안전성 강화)

### 3. 스크립트 별 동작 확인 (소스 직접 점검)

- **`status.sh`**: `/paper/status` + `/paper/dry-run/status` 둘 다 호출.
- **`tick.sh`**: dry-run status 조회 → `.running` 값 추출(jq + grep fallback) → false이면 start 먼저 호출 → tick 호출 (snapshots=[]).
- **`analyze.sh`**: analyze → latest → `.run_dir` 추출 → 로컬 `analysis_report.md` 절대경로 출력.
- **`smoke_check.sh`**: status → start_dry_run → tick → analyze → stop_dry_run 순차 실행, 각 단계 `|| true`로 흡수.

### 4. README 변경

`projects/paper-trading/README.md`에 mvp-020 단락 추가. 8개 스크립트 표 + 사용 예시 + 안전 가드 설명 포함. 기존 단락 변경 없음(patch.md §22).

### 5. 환경 격리

- `.env` 미접촉 (`git status` clean).
- `.env.example` 미변경.
- 프로젝트 `.gitignore` 미변경 (스크립트는 commit 대상이므로 ignored되면 안 됨 — 그대로 추적 가능).
- 루트 `.gitignore` 미변경.

## Findings (severity 순)

### 1. (informational) 테스트 개수가 plan 추정(7개)보다 +2개

- 위치: `tests/test_helper_scripts.py` 9개 PASS.
- 관찰: plan §5 §2가 "신규 약 7개"로 추정했으나 Codex가 9개 작성. 모두 안전 패턴 검증 카테고리. 추가 테스트는 안전성을 더 강화하는 방향(false-positive 위험 없음).
- 영향: 좋음. 테스트 carve-up이 조금 더 세분화된 것.

### 2. (low — process) `app/broker/kis.py` pre-existing dirty가 워크트리에 누적

- 위치: `git diff --stat -- projects/paper-trading/app` → `kis.py | 225 ++++++++++++++++++++++++++++--- 1 file changed, 209 insertions(+), 16 deletions(-)`.
- 관찰: mvp-014-017-bundle / mvp-018 / 이전 mvps에서 누적된 dirty. mvp-020 자체는 `app/`을 0줄 변경. patch.md §103이 정직하게 명시.
- 영향: 안전 위반 없음. commit 시 staging 한정 필요.
- 권장: 아래 액션 아이템 참고.

### 3. (informational) `BASE_URL` env 추가 변형 지원

- 위치: `_common.sh`이 `BASE_URL="${BASE_URL:-http://127.0.0.1:8000}"`.
- 관찰: 사용자가 외부 `BASE_URL=...`을 설정하면 다른 호스트도 가리킬 수 있음.
- 영향: 의도된 동작. README도 이를 설명. 안전 관점에서는 사용자가 의식적으로 override해야 하므로 default-safe.
- 권장: 없음. 좋은 설계.

### 4. (informational) tick.sh의 snapshots=[]

- 위치: `tick.sh` line `-d '{"snapshots":[]}'`.
- 관찰: tick이 빈 snapshots로 호출되므로 `snapshots_evaluated=0`. ticks_total 카운터만 증가.
- 영향: 의도된 smoke-only 동작. README는 "기본 사용 예시"로 명시. 실제 평가 데이터는 외부 cron이나 더 정교한 통합에서 공급.
- 권장: patch.md Remaining TODOs에 이미 명시("Add richer sample snapshots ... in a separate approved MVP"). 본 mvp 범위 적절.

## File / line references (요청 ↔ 산출물 매핑)

| 요청 스크립트 | 위치 | 동작 검증 |
| --- | --- | --- |
| 1. `scripts/start_server.sh` | line 13 | `--host 127.0.0.1 --port "$PORT"`, `0.0.0.0` 부재 ✓ |
| 2. `scripts/status.sh` | 전체 | `/paper/status` + `/paper/dry-run/status` 호출 ✓ |
| 3. `scripts/start_dry_run.sh` | 전체 | `POST /paper/dry-run/start` ✓ |
| 4. `scripts/tick.sh` | 자동 start 분기 + tick | running 체크 → not-running 시 start → tick ✓ |
| 5. `scripts/stop_dry_run.sh` | 전체 | `POST /paper/dry-run/stop` ✓ |
| 6. `scripts/analyze.sh` | analyze + latest + path 출력 | run_dir 추출 + `analysis_report.md` 절대경로 ✓ |
| 7. `scripts/smoke_check.sh` | 순차 실행 + `|| true` | status→start→tick→analyze→stop ✓ |

| 요청 안전 조건 | 결과 |
| --- | --- |
| 실제 주문 실행 안 함 | scripts가 paper-trading API만 호출, API는 mvp-018/019에서 이미 안전 ✓ |
| `KIS_ORDER_DRY_RUN=true` 기본값 강제 | `_common.sh:export KIS_ORDER_DRY_RUN=true` ✓ |
| `LIVE_TRADING_ENABLED=false` 기본값 강제 | `_common.sh:export LIVE_TRADING_ENABLED=false` ✓ |
| `ALLOW_MARKET_ORDERS=false` 기본값 강제 | `_common.sh:export ALLOW_MARKET_ORDERS=false` ✓ |
| 시장가 주문 허용 안 함 | `OrderType.MARKET` 부재 + `ALLOW_MARKET_ORDERS=false` 강제 ✓ |
| `.env` / secret 출력 안 함 | grep 0건 검증 ✓ |
| app key / secret / account / token 출력 안 함 | grep 0건 검증 ✓ |
| live trading 활성화 안 함 | shell export로 차단 ✓ |
| `git commit`/`push`/`merge` 자동화 안 함 | grep 0건 검증 ✓ |

## Missing tests / residual risk

- 9개 메타 테스트가 정적 안전성을 잘 커버. 추가 필요 없음.
- 실제 스크립트 실행 테스트(end-to-end)는 본 mvp에 없음. 이유: 실 server 기동 + curl 등 외부 의존이 pytest와 잘 안 맞음. 메타 테스트(syntax + 안전 패턴 검증)만으로 충분 — Codex가 의도적으로 이 트레이드오프를 선택.
- `tick.sh`의 빈 snapshots는 의도된 smoke-only 동작. 실 데이터 흐름이 필요할 경우 별도 mvp 후보(Findings #4).
- 사용자 외부 환경(`BASE_URL` override, 다른 PORT)에서의 동작은 메타 테스트가 보장하지 않음 — 운영자가 README 따라 실행하면 자동 안전.

## Final checklist (요청 + scope)

- [x] **8개 스크립트 모두 존재 + 실행 권한**.
- [x] **`bash -n` 8개 모두 PASS**.
- [x] **`_common.sh`이 4개 안전 env force export**.
- [x] **`start_server.sh`이 `127.0.0.1`에만 바인딩, `0.0.0.0` 부재**.
- [x] **`tick.sh`이 not-running 자동 start 로직 보유**.
- [x] **`analyze.sh`이 `analysis_report.md` 로컬 경로 출력**.
- [x] **`smoke_check.sh`이 6단계를 `|| true`로 순차 실행**.
- [x] **금지 패턴(KIS_APP_KEY/SECRET/ACCOUNT raw echo, cat .env, ${KIS_*}) 0건**.
- [x] **금지 명령(git commit/push/merge, pip install) 0건**.
- [x] **메타 테스트 9개 PASS**.
- [x] **기존 172 회귀 0건 (전체 181 PASS)**.
- [x] **README에 mvp-020 단락 추가, 기존 단락 변경 없음**.
- [x] **`app/`, `app/config.py`, `app/api/*`, `.env.example`, 프로젝트/루트 `.gitignore` 변경 0건 (mvp-020 scope)**.
- [x] **mvp-001..mvp-019 산출물 변경 0건**.
- [x] **commit/push/merge/deploy 자동화 없음**.
- [x] **`patch.md` 5섹션 + Implementation Summary 6단락 완성**.
- [ ] **commit staging 한정 — 사람 액션** (Findings #2 pre-existing dirty 격리).

## 사람에게 남기는 액션 아이템

1. **mvp-020 commit staging 한정** (필수):

   ```bash
   cd /root/ai-dev-center/projects/ai-team
   git add projects/paper-trading/scripts/ \
           projects/paper-trading/tests/test_helper_scripts.py \
           projects/paper-trading/README.md \
           docs/ai/jobs/mvp-020/
   git diff --cached --stat
   ```

   `app/broker/kis.py` 등 pre-existing dirty(mvp-014-017/018 잔재)는 별도 commit으로 분리.

2. **commit/push/merge/deploy는 사람이 직접.** 본 작업은 자동화하지 않는다.

3. **운영 사용 예시** (mvp-018 + mvp-019 + mvp-020 결합):

   ```bash
   cd /root/ai-dev-center/projects/ai-team/projects/paper-trading

   # 터미널 A: 서버 실행
   ./scripts/start_server.sh

   # 터미널 B: 상태 확인
   ./scripts/status.sh

   # 단발 smoke
   ./scripts/smoke_check.sh

   # 또는 운영 중 일정 주기로 tick (예: 5분마다)
   while true; do
       ./scripts/tick.sh
       sleep 300
   done

   # 종료 시
   ./scripts/stop_dry_run.sh
   ./scripts/analyze.sh
   ```

4. **다음 mvp 후보**:
   - **mvp-021 (자연스러운 다음)**: `claude_review_input.md` 기반 Claude/Codex 전략 개선안 plan/codex-task 작성 (사람 검토 후 별도 mvp).
   - **mvp-022**: `tick.sh`이 실제 snapshots 파일(JSON)을 받는 옵션 추가 — long-run 데이터 흐름.
   - **mvp-023**: ai-team web GUI(`/root/ai-dev-center/projects/ai-team/web/`)에 paper-trading 서버 제어 패널 추가 — GUI에서도 같은 helper API를 호출.
   - **계속 보류**: KIS 공식 문서값(`docs/kis/MISSING_OFFICIAL_VALUES.md`)이 채워지기 전까지 실제 KIS HTTP 연결.
