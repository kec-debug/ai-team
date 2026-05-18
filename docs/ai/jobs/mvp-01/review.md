# Review — mvp-01: GUI Claude + Codex 단순화

## Verdict

**APPROVE** (사람이 commit 전에 워크트리 격리 한 가지를 반드시 확인할 것)

mvp-01 범위에서 Codex가 변경한 다섯 개 소스 파일(`web/public/index.html`, `web/public/app.js`, `web/public/style.css`, `README.md`, `docs/ai/CLAUDE_CODEX_WORKFLOW.md`)과 `patch.md`는 모두 계획서(`plan.md`)와 사용자 요청(`request.ko.md`)에 일치합니다. 안전 규칙 위반은 없습니다. 단, 동일 워크트리에 mvp-01과 무관한 prior dirty changes(scripts/, prompts/, docs/safety-rules.md, docs/setup.md, docs/workflow.md, web/server.js)가 섞여 있으므로 commit 단계에서 사람이 파일을 선별해 staging 해야 합니다.

## Findings (severity 순)

### 1. (medium / process) 워크트리에 mvp-01 외 prior dirty changes가 같이 들어있다

- 위치: `docs/ai/jobs/mvp-01/local-diff.patch` line 1–1887, `docs/ai/jobs/mvp-01/patch.md` 4. Test Results.
- 관찰: `git diff --stat`은 14개 파일 변경을 보여주는데, Codex가 mvp-01에서 의도적으로 수정한 파일은 `patch.md`가 명시한 다섯 개뿐이다. `web/server.js`(+412 / -...), `scripts/start-ai-team.sh`, `scripts/create-job.sh`, `prompts/codex-implementer.md`, `prompts/claude-architect.md`, `prompts/claude-reviewer.md`, `prompts/gemini-manager.md`, `docs/workflow.md`, `docs/setup.md`, `docs/safety-rules.md`의 변경은 세션 시작 시점에 이미 존재한 dirty work이다. (세션 시작 시점의 `git status`에 동일 파일들이 `M`으로 표시되어 있었음.)
- 영향: 작업 자체에는 결함 없음. 하지만 사람이 그대로 `git add -A && git commit` 하면 mvp-01에 무관한 변경이 같이 커밋되어 PR 리뷰 범위와 안전 가드가 흐려질 수 있다.
- 권장: commit 시 `git add` 대상을 다음 파일로만 한정한다.
  - `README.md`
  - `web/public/index.html`
  - `web/public/app.js`
  - `web/public/style.css`
  - `docs/ai/CLAUDE_CODEX_WORKFLOW.md`(아래 #2 참고)
  - `docs/ai/jobs/mvp-01/` 산출물(`request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, `review.md`, 필요 시 `local-diff.patch`, `pipeline.log.md`, `status.md`)
- 나머지 dirty 변경은 별도 커밋 / 별도 작업으로 분리한다.

### 2. (low / process) `docs/ai/CLAUDE_CODEX_WORKFLOW.md`가 git에 untracked 상태다

- 위치: 세션 시작 `git status` 출력 — `?? docs/ai/CLAUDE_CODEX_WORKFLOW.md`. `git ls-files --error-unmatch` 확인 결과 미추적.
- 영향: `git diff`는 이 파일을 보여주지 않는다(`local-diff.patch` 안에도 없음). `patch.md` 1. Files Changed에는 포함되어 있지만, 사람이 `git add docs/ai/CLAUDE_CODEX_WORKFLOW.md`를 명시적으로 하지 않으면 커밋에 누락된다.
- 권장: 위 #1의 한정 staging 목록에 포함시키고, 커밋 후 `git log -1 --name-only`로 포함 여부를 확인한다.

### 3. (low / consistency) `patch.md` Test Results의 `git diff --stat`이 mvp-01 외 변경까지 포함

- 위치: `docs/ai/jobs/mvp-01/patch.md` lines 32–52.
- 관찰: stat 자체는 사실에 부합하고, 마지막 한 줄(`The stat includes pre-existing dirty worktree changes outside the mvp-01 files. For this mvp-01 implementation, I edited only the files listed in section 1.`)이 분명히 디스클레이머를 제공한다.
- 영향: 안전 측면 문제 없음. 단 향후 같은 워크트리에서 잘못 해석될 여지가 있다. 다음 작업부터는 `git diff -- web/public README.md docs/ai/CLAUDE_CODEX_WORKFLOW.md docs/ai/jobs/mvp-01` 같이 경로 필터로 격리한 stat을 함께 첨부하면 더 명확하다. 이번에는 그대로 통과.

## File / line references (in-scope changes)

- `web/public/index.html`
  - `+        <p class="eyebrow">Claude + Codex Workflow</p>` (HEAD에서 `Local tmux Control`, 이 줄 자체는 pre-existing dirty)
  - `+          <input id="jobId" type="text" value="mvp-001" ...>` — 작업 ID 기본값 변경 ✓ (요청 5번, 계획 4.2.5)
  - `+        <div class="role-display" aria-label="역할 안내">` 내 카드 2개(Claude, Codex)만 노출 ✓ (요청 1번)
  - `+        <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. ...` ✓ (계획 4.2.2)
  - `+          <button id="runPipeline" class="primary-action" type="button">Claude → Codex → Claude 전체 실행</button>` + `+          <div class="primary-actions">` 내 `data-send="claude-plan"`, `data-send="codex-implement"`, `data-send="claude-review"` ✓ (요청 2번, 계획 4.2.3)
  - 고급 패널: `Gemini Manager 전송`, `Claude Architect 전송`, `Codex Implementer 전송`, `Claude Reviewer 전송` 4개 모두 제거. 남은 항목은 `AI 팀 시작`, `작업 폴더 생성`, `request.ko.md 저장`, `git status`, `git diff` ✓ (요청 1번, 7번, 계획 4.2.4)

- `web/public/app.js`
  - `-  jobId: localStorage.getItem('aiTeamJobId') || 'job-002'` → `+  jobId: localStorage.getItem('aiTeamJobId') || 'mvp-001'` ✓ (계획 4.3.1)
  - `+const activePipelineStates = new Set([...])` / `+const finalPipelineStates = new Set([...])`가 요청 6번의 8-state(중 idle은 finalPipelineStates 전용)와 일치 ✓
  - `runPipelineButton.disabled = activePipelineStates.has(pipeline.state);`, `finalPipelineStates.has(pipeline.state)` 등 상태 매핑이 8-state 명명으로 정합 ✓
  - 임의 shell 명령 입력 핸들러 추가 없음 ✓ (요청 9번)

- `web/public/style.css`
  - `+.role-display { ... grid-template-columns: repeat(2, minmax(0, 1fr)); ... }` ✓ (계획 4.4.1)
  - `+.role-aside { ... }` ✓ (계획 4.4.2)
  - `+.primary-actions { ... grid-template-columns: repeat(3, minmax(0, 1fr)); ... }` ✓ (계획 4.4.3)
  - 미디어 쿼리 안에 `+  .role-display { grid-template-columns: 1fr; }`, `+  .primary-actions { grid-template-columns: 1fr; }` ✓
  - `+.status-line[data-status="claude_planning"], ... "codex_implementing", ... "claude_reviewing"`, `+...[data-status="approval_required"]`, `+...[data-status="blocked"]`, `+...[data-status="manual_review_required"]`로 8-state 색상 매핑 ✓
  - 보안/색상/폰트 토큰 변경 없음 ✓

- `README.md`
  - `## 팀 구성` 아래 2행 표(Claude, Codex)와 Manual Shell 1-line 주석 추가 ✓ (계획 4.6.2)
  - `<details><summary>Deprecated: 이전 5역할 구성</summary> ... </details>`로 5-role 표 강등 ✓ (계획 4.6.3)
  - 브라우저 GUI 섹션에 메인 액션 4개, 8-state 목록, 수동 유틸리티 2개, 자동화 금지 목록, 임의 shell 입력 없음, 변경 금지 영역, 6개 산출물 모두 명시 ✓ (계획 4.6.4, 요청 11번)

- `docs/ai/CLAUDE_CODEX_WORKFLOW.md` (untracked, `git diff`에 미포함)
  - `## 브라우저 GUI` 섹션 (line 130–164) 신설 ✓ (계획 4.7)
  - 4-button → API 매핑 표 ✓
  - 8-state 목록 ✓
  - tmux 기본 대상 `claude`, `codex`만 사용, `git-shell`은 비AI 보조 창 명시 ✓ (요청 3, 4번)
  - 수동 유틸리티 `git status`, `git diff`, 자동 commit/push/merge/deploy 없음 ✓ (요청 7, 8번)
  - 임의 shell 명령 입력 없음 ✓ (요청 9번)
  - 변경 금지 영역(`.env`, secrets, auth, payment, production infra, database migrations) 명시 ✓ (요청 10번)

- `web/server.js`
  - mvp-01에서 의도된 추가 변경 없음(plan §4.5는 verify-only). 세션 시작 시점 코드 기준으로 `SAFE_WINDOWS`, `ALLOWED_TMUX_WINDOWS`(`claude`, `codex`, `git-shell`), `AI_TMUX_WINDOWS`(`claude`, `codex`), `ACTIVE_PIPELINE_STATES`, `FINAL_PIPELINE_STATES`(8-state 정합), `ARTIFACT_PRIORITY`(6 file 순서) 모두 기준치와 일치한다.
  - `SAFETY_DENY_PATTERNS`이 그대로 유지되어 `.env`, secrets, migrations, auth, payment, infra, `.github/workflows` 차단 ✓
  - 새 라우트(commit/push/merge/deploy/임의 shell) 추가 없음 ✓

## Missing tests / residual risk

- Codex 자체 테스트는 `node --check` 두 개로 한정되어 있고, 둘 다 PASS. UI 동작(버튼 클릭 → API 호출 → 상태 전이)에 대한 자동 테스트는 본 작업 범위에 없다. mvp-01 범위 내에서는 적절. UI를 신뢰성 있게 검증하고 싶다면 후속 작업으로 Playwright/Cypress 같은 brower test를 별도 job으로 분리하는 것을 권장하지만, 이번 작업에서 요구되지 않았으므로 보류.
- README의 `브라우저 GUI` 섹션이 더 길고 워크플로 문서의 `브라우저 GUI` 섹션과 일부 중복된다. 의도된 중복(README는 사용 안내, 워크플로 문서는 정식 레퍼런스)이며, 일치하지 않는 항목은 없다. 향후 한 곳을 표준 소스로 두고 다른 한 곳에서 링크로 참조하는 리팩터링이 가능하지만 이번 범위 밖.
- 워크트리에 섞인 prior dirty changes는 위 Findings #1 참고. 사람이 staging을 한정하지 않으면 mvp-01과 무관한 변경이 같은 커밋에 묻어들어갈 수 있다.

## Final checklist (approved scope + safety rules)

- [x] 메인 패널에 액션 버튼 4개(`Claude → Codex → Claude 전체 실행`, `Claude 계획 생성`, `Codex 구현 실행`, `Claude 리뷰 실행`)가 노출된다. (`web/public/index.html` line ~50–58)
- [x] 고급 패널에서 동일한 `data-send` 버튼이 중복 노출되지 않는다. (`web/public/index.html` line ~143–149)
- [x] `Manual Shell` / `git-shell`이 핵심 AI 역할 카드에서 빠져 있고, 보조 안내 문구로만 남아 있다. (`web/public/index.html` `.role-display` + `.role-aside`)
- [x] tmux 기본 자동화 대상은 `claude`, `codex`만이다. (`web/server.js` `AI_TMUX_WINDOWS`, `SAFE_WINDOWS`)
- [x] 상태 단계가 8개와 일치한다. (`web/server.js` `ACTIVE_PIPELINE_STATES` + `FINAL_PIPELINE_STATES`, `web/public/app.js` 동일 두 Set, `web/public/style.css` data-status 셀렉터)
- [x] `git status`, `git diff`만 수동 유틸리티 버튼으로 남아 있다. 자동 `commit`/`push`/`merge`/`deploy` 버튼·라우트 신설 없음.
- [x] 임의 shell 명령 입력 UI/API 신설 없음.
- [x] `.env`, secrets, auth, payment, production infra, database migration 관련 파일 변경 없음. (`patch.md` §3 Safety Confirmation과 일치)
- [x] `README.md`와 `docs/ai/CLAUDE_CODEX_WORKFLOW.md`에 새 GUI 사용법이 반영되어 있다.
- [x] `node --check web/server.js`, `node --check web/public/app.js` PASS (patch.md §4).
- [x] `patch.md`에 Files Changed / Implementation Summary / Safety Confirmation / Test Results / Remaining TODOs가 모두 포함되어 있다.
- [ ] **사람이 commit 전 staging을 mvp-01 파일로 한정해야 함** — 워크트리에 prior dirty changes가 섞여 있어 자동으로 보장되지 않는다. Findings #1, #2 참고.

## 사람에게 남기는 액션 아이템

1. 다음 파일만 `git add`로 staging 한다(나머지 dirty 파일은 별도 작업/별도 커밋으로 분리).
   - `README.md`
   - `web/public/index.html`
   - `web/public/app.js`
   - `web/public/style.css`
   - `docs/ai/CLAUDE_CODEX_WORKFLOW.md` (untracked → 명시적으로 add 필요)
   - `docs/ai/jobs/mvp-01/` 작업 산출물(`request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, `review.md`, 필요 시 `local-diff.patch`, `pipeline.log.md`, `status.md`)
2. `git diff --cached --stat`으로 staging 범위를 한 번 더 확인한다.
3. 커밋 메시지에 mvp-01 / GUI 단순화 컨텍스트를 명시한다(머지/푸시는 사람이 직접 결정).
4. PR 머지·푸시·배포는 자동화하지 않는다.
