# Review — mvp-003: Paper Trading Phase 1 스캐폴딩

## Verdict

**BLOCK** — mvp-003 작업이 실제로 수행되지 않았다. `patch.md`는 다른 작업의 결과로 보이는 내용을 잘못 기록하고 있어 사실과 다르다. Codex가 mvp-003 작업을 다시 수행해야 한다.

## 핵심 사실 (검증된 관찰)

1. **신규 프로젝트 디렉터리가 존재하지 않는다.**
   - `ls /root/ai-dev-center/projects/ai-team/projects/paper-trading/` → `No such file or directory`.
   - `plan.md` §3과 `codex-task.md` "디렉터리 구조"가 요구한 `app/`, `tests/`, `pyproject.toml`, `.env.example`, `README.md` 등 어느 것도 만들어지지 않았다.
2. **저장소에 mvp-003 관련 코드 변경이 0건이다.**
   - `git -C ... diff --stat` 결과: (empty). 추적 파일 수정 없음.
   - `git -C ... status --short` 결과:
     ```
     ?? docs/ai/jobs/mvp-003/codex-task.md
     ?? docs/ai/jobs/mvp-003/pipeline.log.md
     ?? docs/ai/jobs/mvp-003/plan.md
     ?? docs/ai/jobs/mvp-003/request.ko.md
     ```
     mvp-003 job 메타파일 외에는 변경/추가가 없다. `projects/paper-trading/...` 어떤 경로도 untracked로 나타나지 않는다.
3. **`local-diff.patch`가 존재하지 않는다.**
   - 파이프라인의 `save-diff` 단계가 변경이 없어서 저장하지 않았다 (`server.js`의 `saveLocalDiff`는 diff가 비어있으면 파일을 쓰지 않음).
4. **`patch.md`가 mvp-003 작업과 무관한 내용을 기록하고 있다.**
   - `patch.md` line 5–11 "Files Changed"는 `web/server.js`, `web/public/app.js`, `web/public/index.html`, `README.md`, `docs/ai/CLAUDE_CODEX_WORKFLOW.md`, `scripts/start-ai-team.sh`를 나열한다. 이는 mvp-003 범위(`projects/paper-trading/` 신규 생성)와 전혀 일치하지 않는다. 또한 `git status` 결과에 해당 파일들은 modified로도 나오지 않는다 — 즉, **claim된 변경 자체가 실제로 디스크에 존재하지 않는다**.
   - `patch.md` line 38의 `git diff --stat: 14 files changed, 723 insertions(+), 306 deletions(-)`도 현재 워크트리 상태와 일치하지 않는다(현재는 0 files changed).
   - 내용상 mvp-01(GUI 단순화) 잔여 작업처럼 보이지만, 그것조차 디스크에는 반영되어 있지 않다.
5. **파이프라인 로그가 단계는 진행됐음을 보여주지만 실제 산출물이 없다.**
   - `pipeline.log.md`: `create-job` → `save-input` → `claude-plan (no output)` → `codex-implement (no output)` → `save-diff (no output)` → `claude-review (no output)` 순으로 호출됨.
   - 각 단계의 stdout이 비어 있으며, Codex 단계에서 실제 파일 생성이 일어나지 않았다.

## Findings (severity 순)

### 1. (BLOCK / correctness) mvp-003 구현이 전혀 이루어지지 않았다

- 위치: `projects/paper-trading/` (없음).
- 영향: 요청 1–9번 항목 모두 미이행. paper-only config, broker 인터페이스, RiskEngine, OMS, Strategy 추상, Alpaca Paper stub, `/paper/status` API, 테스트 모두 부재. live trading 차단이나 시장가 차단을 강제할 코드 자체가 없다.
- 권장: Codex에 `docs/ai/jobs/mvp-003/codex-task.md`를 정확히 전달하여 다시 실행한다. Codex가 이 단계를 시작하기 전에 다음을 확인하게 한다.
  - 작업 루트가 `/root/ai-dev-center/projects/ai-team`이다.
  - 신규 디렉터리는 `projects/paper-trading/`이며 현재 존재하지 않는다.
  - 이전 mvp-01/mvp-002 결과나 GUI 관련 작업과 혼동하지 않는다.

### 2. (BLOCK / integrity) `patch.md`가 사실과 다른 변경을 보고하고 있다

- 위치: `docs/ai/jobs/mvp-003/patch.md` line 3–11(Files Changed), 13–20(Implementation Summary), 28–39(Test Results).
- 관찰:
  - `Files Changed`에 나열된 6개 파일은 `git status`에서 modified 상태가 아니며, 실제 워크트리에 해당 변경이 존재하지 않는다.
  - `Implementation Summary`는 paper trading이 아닌 GUI/pipeline mapping에 대한 설명이다. mvp-003 요청과 일치하지 않는다.
  - `Test Results` 의 `git diff --stat: 14 files changed, 723 insertions(+), 306 deletions(-)`는 현재 워크트리 상태(0 changes)와 모순된다.
  - "READY FOR REVIEW" verdict는 부정확하다.
- 영향: patch.md를 사람이 신뢰하면 사실과 다른 변경이 적용되었다고 오해할 수 있다. 또한 `git diff --stat` 인용은 이전 세션의 출력으로 보이며, 안전 가드(변경 범위 격리)가 깨지는 위험을 낳는다.
- 권장: 다시 작업할 때 `patch.md`를 빈 상태에서 시작하고, Test Results는 현재 워크트리에서 직접 실행한 명령의 stdout/exit code를 그대로 인용하게 한다.

### 3. (high / safety prerequisite) 안전 가드가 작동할 코드 경로 자체가 존재하지 않는다

- 요청과 `prompts/claude.md` 안전 규칙의 핵심(live 차단, 시장가 차단, RiskEngine 필수, OMS-only execution, agent/LLM 직접 주문 금지, `.env`-only secrets, broker URL 추측 금지)은 mvp-003에서 코드로 구체화되어야 한다. 현재는 그 어떤 코드도 없으므로 안전 가드를 "충족"이라고 말할 수 없다. (위반은 없다 — 아무것도 만들지 않았으므로 — 하지만 "안전이 보장된다"고도 말할 수 없다.)
- 권장: 재실행 시 `plan.md` §6 리뷰 체크리스트의 모든 항목이 코드와 테스트로 검증되도록 한다.

## File / line references (요청 ↔ 산출물 매핑)

| 요청 항목 | 산출물 위치 | 상태 |
| --- | --- | --- |
| 1. paper trading 전용 기본 설정 구조 | `projects/paper-trading/app/config.py` | 미생성 |
| 2. live trading 기본 비활성 상태 확인 | `Settings.live_trading_enabled=False`, `load_settings()` 가드 | 미생성 |
| 3. 브로커 인터페이스 구조 점검 | `app/broker/base.py` | 미생성 |
| 4. Alpaca Paper / paper broker adapter 연결 준비 | `app/broker/paper.py`, `app/broker/alpaca_paper.py` (stub) | 미생성 |
| 5. RiskEngine 기본 규칙 점검 | `app/risk_engine.py` | 미생성 |
| 6. Strategy → RiskEngine → OMS → Broker 흐름 확인 | `app/strategy.py` + `app/oms.py` + 통합 테스트 | 미생성 |
| 7. /paper/status API 점검 | `app/api/server.py` | 미생성 |
| 8. 없는 경우 최소 paper status API 추가 | 위와 동일 | 미생성 |
| 9. 테스트 추가 | `tests/test_*.py` 8개 | 미생성 |

## Missing tests / residual risk

- 테스트는 모두 미작성. `python -m compileall app tests`, `python -m pytest -p no:cacheprovider` 모두 실행할 수 없다.
- `git diff --stat`은 현재 0 files를 보고하므로 `patch.md`의 stat 인용이 사실과 다르다. 다음 실행에서는 인용 출처를 명시한다.
- 호스트에 `fastapi`/`pytest`/`pydantic`/`httpx` 가 설치되어 있는지 검증되지 않았다. 재실행 시 미설치라면 Codex가 직접 `pip install` 하지 말고 `patch.md`의 Remaining TODOs에 사람이 실행할 명령을 명시한다 (`codex-task.md`의 가드 그대로).

## Final checklist (approved scope + safety rules)

- [ ] 신규 파일이 모두 `projects/paper-trading/` 아래에 존재한다. — **FAIL** (디렉터리 없음)
- [ ] `Settings.live_trading_enabled` 기본 False, `TradingMode.PAPER` 기본. — **FAIL** (코드 없음)
- [ ] `load_settings()`가 `TRADING_MODE != paper` 또는 `LIVE_TRADING_ENABLED=true`에서 fail closed. — **FAIL**
- [ ] `OrderType` 열거형에 MARKET 없음. — N/A (`OrderType` 자체가 없음)
- [ ] RiskEngine이 paper 강제 / live 차단 / 시장가 거부 / 한도 / allowlist를 모두 검사. — **FAIL**
- [ ] OMS가 외부 호출자에게 RiskEngine을 노출하지 않고 내부 호출. — **FAIL**
- [ ] OMS.place 시작부에서 live 차단, non-paper broker 차단. — **FAIL**
- [ ] PaperBroker.submit이 LIMIT/STOP_LIMIT만 허용 (이중 가드). — **FAIL**
- [ ] AlpacaPaperBroker는 env 미설정 시 fail closed, 네트워크 미구현. — **FAIL**
- [ ] Strategy는 OrderIntent만 반환, OMS/Broker/RiskEngine 직접 호출 없음. — **FAIL**
- [ ] `/paper/status` read-only, `live_enabled=false` 반환. — **FAIL**
- [ ] `.env.example` placeholder만, `.env`는 무시. — **FAIL**
- [ ] broker URL이 코드 상수 아닌 env에서 로드. — N/A (어댑터 없음)
- [ ] 테스트 8개 통과. — **FAIL**
- [ ] `patch.md` Implementation Summary에 (i) 변경 파일, (ii) paper 경로, (iii) live 차단, (iv) 테스트 결과 모두 포함. — **FAIL** (다른 작업 내용 기록)
- [ ] `git diff --stat`에 mvp-003 외 변경 없음. — PASS (현재 0 changes)
- [ ] commit/push/merge/deploy 자동화 없음. — PASS

## 사람에게 남기는 액션 아이템

1. **Codex 단계를 다시 실행한다.** GUI의 `Codex 구현 실행` 버튼을 사용하거나, `codex` tmux 창에서 다음 프롬프트를 그대로 전달한다(이 프롬프트는 `codex-task.md`에 정의된 그대로다).

   ```
   Use prompts/codex-implementer.md.
   Project directory: /root/ai-dev-center/projects/ai-team
   Job ID: mvp-003
   Job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-003

   Read /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-003/plan.md and /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-003/codex-task.md. Use /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-003/request.ko.md as scope context only.
   Implement only the approved job scope, run applicable checks, and write /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-003/patch.md.
   Do not commit, push, merge, deploy, or change secrets, .env, auth, payment, production infra, or database migrations.
   ```

2. **재실행 전에 `patch.md`를 빈 상태로 되돌린다.** 현재 `patch.md`는 잘못된 내용을 담고 있어 Codex가 그 위에 잘못 누적할 수 있다. 빈 파일 또는 codex-task.md 안의 템플릿만 남긴 채 시작하게 한다.

3. **재실행 후 검증:**
   - `ls projects/paper-trading/app projects/paper-trading/tests` 가 비어있지 않은지 확인.
   - `cd projects/paper-trading && python -m compileall app tests && python -m pytest -p no:cacheprovider` 종료코드 0.
   - `grep -RIn "MARKET\|live_trading_enabled.*True\|TRADING_MODE.*live" projects/paper-trading/app` 에 허용 코드 경로가 없음을 확인.
   - `grep -RIn "https://" projects/paper-trading/app` 결과에 broker URL 하드코딩 없음.
   - `git status --short` 에 `.env` 미포함.

4. **commit/push/merge/deploy는 사람만 수행한다.** 본 작업은 그 단계에 아직 도달하지 않았다.

## 참고: 이 실패의 가능한 원인 (Codex 재실행 전 점검)

- Codex tmux 창에 이전 작업(mvp-01 등)의 컨텍스트나 출력이 남아 새 프롬프트가 그 위에 섞였을 가능성 — 재실행 전에 `codex` 창을 `clear` 하거나 새 세션으로 재시작.
- 파이프라인이 Codex 출력이 도달하기 전에 `save-diff`로 넘어가 변경이 0인 채로 종료되었을 가능성 — `pipeline.log.md` 타임스탬프가 `08:20:38` → `08:27:38`로 7분 간격이라 시간은 충분했지만, Codex가 실제로 파일을 쓰지 않고 텍스트만 출력했을 수 있음. Codex가 응답을 출력만 하고 파일 IO를 하지 않은 경우, `codex-task.md`의 "Implement" 지시를 다시 강조해서 보낸다.
- `patch.md`가 사전 채워진 상태로 시작된 경우 Codex가 새 작업의 내용을 적지 않고 기존 내용을 그대로 둔 가능성 — 위 액션 아이템 2 참고.
