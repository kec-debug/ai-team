# Codex Task — mvp-004: AI 개발팀 GUI 화면 배치 개선

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-004/plan.md` and `docs/ai/jobs/mvp-004/request.ko.md` first.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-004`
- Job directory: `/root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-004`
- 워크플로 문서: `docs/ai/CLAUDE_CODEX_WORKFLOW.md`
- 본 작업은 **GUI 레이아웃 재배치**만 한다. 로직(API, 파이프라인, server.js 라우트, app.js 핸들러) 변경은 하지 않는다.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, API key, token 류 일체 변경/생성 금지.
- 임의 shell 명령 입력 UI/API 신설 금지.
- 새 API 라우트 추가 금지. 기존 `data-send` 매핑(`claude-plan`/`codex-implement`/`claude-review`) 변경 금지.
- 옛 역할(`Gemini Manager`, `Claude Architect`, `Claude Reviewer`, `Git Shell`)을 메인 UI에 재노출하는 마크업 추가 금지.
- `commit`/`push`/`merge`/`deploy` 자동화 버튼/엔드포인트 신설 금지.
- `projects/paper-trading/`, `app/`, broker adapter, RiskEngine, OMS, Strategy 코드 등 mvp-003 영역 변경 금지.
- `prompts/`, `scripts/`, `docs/safety-rules.md`, `docs/setup.md`, `docs/workflow.md`, `docs/ai/CLAUDE_CODEX_WORKFLOW.md`(시각 배치 명시가 없으면 변경 불필요) 등 본 작업과 무관한 파일 변경 금지.
- 본 작업 범위 외 파일 변경 금지.

## 수정 허용 파일

- `web/public/index.html`
- `web/public/style.css`
- `web/public/app.js` (가능한 한 변경하지 않음 — 변경한다면 행 수 최소)
- `docs/ai/jobs/mvp-004/patch.md` (Codex 신규 작성)

그 외 파일은 만지지 않는다. `web/server.js`는 변경하지 않으며 검증만 한다.

## 구현 작업

### 1) `web/public/index.html`

`<main class="layout">` 안을 다음 순서로 다시 구성한다. `<header class="topbar">`, `<script>`, `#approvalModal`은 위치 변경 없이 유지한다. 기존 `<section class="panel setup">`은 완전히 제거하고 아래 구조로 대체한다.

```html
<main class="layout">
  <section class="panel quick-actions">
    <h2>핵심 실행</h2>
    <label>
      작업 ID
      <input id="jobId" type="text" value="mvp-001" autocomplete="off" spellcheck="false">
    </label>
    <label>
      한국어 작업 요청
      <textarea id="inputKo" spellcheck="false" rows="6"></textarea>
    </label>
    <p class="field-hint">여기에는 한국어 작업 요청만 입력하세요. 쉘 설정 명령, 실행 명령, 토큰, 비밀값은 넣지 않습니다.</p>
    <div class="pipeline-runner">
      <button id="runPipeline" class="primary-action" type="button">Claude → Codex → Claude 전체 실행</button>
      <div class="primary-actions">
        <button data-send="claude-plan" type="button">Claude 계획 생성</button>
        <button data-send="codex-implement" type="button">Codex 구현 실행</button>
        <button data-send="claude-review" type="button">Claude 리뷰 실행</button>
      </div>
    </div>
  </section>

  <section class="panel control-panel">
    <!-- 기존 마크업 그대로 이동: h2 "승인 / 서비스 제어", warning-text, 제어할 tmux 창 label, control-actions 6개 버튼 -->
  </section>

  <section class="panel tmux-panel">
    <!-- 기존 마크업 그대로 이동: panel-head + #refreshTmuxOutput, <pre id="tmuxOutput"> -->
  </section>

  <section class="panel pipeline-status">
    <!-- 기존 마크업 그대로 이동: panel-head + #pipelineStatus + #resetPipeline,
         #pipelineState, pipeline-meta dl, #detectedIssueAlert, #pipelineGuidance,
         #approvalInlinePrompt + #reopenApprovalPopup, #pipelineSteps -->
  </section>

  <details class="panel job-settings">
    <summary>작업 설정</summary>
    <label>
      프로젝트 경로
      <input id="projectDir" type="text" autocomplete="off" spellcheck="false">
    </label>
    <div class="role-display" aria-label="역할 안내">
      <div>
        <strong>Claude</strong>
        <span>planning / requirements / review</span>
      </div>
      <div>
        <strong>Codex</strong>
        <span>implementation / tests / patch summary</span>
      </div>
    </div>
    <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
  </details>

  <details class="panel advanced-panel">
    <!-- 기존 마크업 그대로 유지: summary "고급 제어",
         #startTeam, #createJob, #saveInput, #gitStatus, #gitDiff -->
  </details>

  <section class="panel artifacts">
    <!-- 기존 그대로 -->
  </section>

  <section class="panel result-summary">
    <!-- 기존 그대로 -->
  </section>

  <section class="panel output-panel">
    <!-- 기존 그대로 -->
  </section>
</main>
```

추가 주의:

- `<section class="panel setup">`이라는 마크업은 새 HTML 어디에도 남아 있어서는 안 된다.
- 기존 ID와 `data-` 속성은 한 글자도 바꾸지 않는다. JS 셀렉터가 모두 살아 있어야 한다.
- `#approvalModal`은 `</main>` 바로 뒤, `<script>` 앞 위치 유지.
- `Gemini Manager`, `Claude Architect`, `Claude Reviewer`, `Git Shell`을 노출하는 마크업을 추가하지 않는다.
- 새 클래스는 `quick-actions`, `job-settings` 두 개만 도입한다.

### 2) `web/public/style.css`

다음만 수정한다. 색상 토큰/폰트/기타 컴포넌트 스타일은 보존한다.

1. `.layout` 규칙 교체:

   ```css
   .layout {
     display: flex;
     flex-direction: column;
     gap: 18px;
     padding: 22px;
     max-width: 1100px;
     margin: 0 auto;
   }
   ```

2. 다음 두 규칙을 제거한다(존재하지 않으면 무시).

   ```css
   .setup { grid-row: span 4; }
   .output-panel { grid-column: 2; }
   ```

3. `textarea` 규칙의 `min-height: 330px;`를 `min-height: 140px;`로 교체한다(나머지 속성은 유지).

4. 다음 규칙을 추가한다.

   ```css
   .quick-actions {
     display: grid;
     gap: 12px;
   }

   .job-settings {
     padding: 14px 18px;
   }

   .job-settings > summary {
     cursor: pointer;
     font-size: 18px;
     font-weight: 800;
     padding: 4px 0;
   }

   .job-settings[open] {
     padding-bottom: 18px;
   }
   ```

5. `@media (max-width: 920px)` 블록 내부에서 다음을 정리한다.
   - `.layout { grid-template-columns: 1fr; padding: 14px; }` 같이 그리드 컬럼을 지정하는 분기는 `flex-direction: column`이 이미 기본이므로 `.layout { padding: 14px; }`만 남긴다.
   - `.setup, .output-panel { grid-row: auto; grid-column: auto; }` 같은 분기가 있다면 제거한다.
   - `.step-grid`, `.role-display`, `.pipeline-meta`, `.primary-actions`의 1-column 분기는 그대로 유지한다.

다른 곳에서 `.setup` 클래스를 참조하는 셀렉터가 있으면 같이 제거한다.

### 3) `web/public/app.js`

- 가능한 한 변경하지 않는다. 기존 셀렉터(`#projectDir`, `#jobId`, `#inputKo`, `#runPipeline`, `[data-send]`, `#tmuxOutput`, `#tmuxWindow`, `#approveOnce`, `#approveSession`, `#rejectAction`, `#interruptAction`, `#refreshTmuxOutput`, `#refreshStatus`, `#pipelineStatus`, `#resetPipeline`, `#startTeam`, `#createJob`, `#saveInput`, `#gitStatus`, `#gitDiff`, `#loadArtifacts`, `#clearOutput`, `#approvalModal` 등)는 그대로 살아 있다.
- 새 fetch 호출/핸들러 추가 금지.
- 옛 5-역할 관련 로직 추가 금지.
- `grep -n "rows" web/public/app.js` 결과가 비어 있으면 이 파일은 손대지 않는다.

### 4) `web/server.js`

- 변경하지 않는다. `node --check web/server.js`로 검증만 수행한다.

### 5) 문서

- README, `docs/ai/CLAUDE_CODEX_WORKFLOW.md`에 "왼쪽 컬럼", "오른쪽 컬럼" 같은 시각 배치 표현이 있는지 확인한다.
  - `grep -nE "왼쪽 컬럼|오른쪽 컬럼|좌측|우측|좌우 분할" README.md docs/ai/CLAUDE_CODEX_WORKFLOW.md`
  - 결과가 없으면 두 파일 모두 손대지 않는다.
  - 결과가 있으면 한 줄만 보정(예: "단일 컬럼으로 위에서 아래로 배치"). 그 외 적극 수정 금지.

### 6) 검증

작업 디렉터리 `/root/ai-dev-center/projects/ai-team`에서 실행한다.

```bash
node --check web/server.js
node --check web/public/app.js
git diff --stat
git status --short
```

네 명령 결과를 `docs/ai/jobs/mvp-004/patch.md`의 Test Results에 그대로 인용한다. `node --check` 두 개는 종료코드 0이어야 한다. 실패하면 작업을 멈추고 원인을 `patch.md`의 Remaining TODOs에 적은 뒤 멈춘다.

### 7) `docs/ai/jobs/mvp-004/patch.md`

`prompts/codex-implementer.md` 형식을 따른다. Implementation Summary는 요청의 "완료 후" 4개 항목과 1:1 대응하도록 다음 단락으로 작성한다.

```markdown
## 1. Files Changed

(실제로 수정/추가된 파일 목록. web/public/index.html, web/public/style.css, (필요 시) web/public/app.js, docs/ai/jobs/mvp-004/patch.md 등)

## 2. Implementation Summary

### 2.1 옮긴 UI 영역
- 최상단: 핵심 실행(작업 ID + 한국어 요청 + 메인 액션 버튼 4개)
- 그 아래: 승인 / 서비스 제어
- 그 아래: 실시간 tmux 출력
- 그 아래: 파이프라인 상태
- 그 아래: 작업 설정(접기/펼치기 details, 기본 닫힘)
- 그 아래: 고급 제어 / 산출물 / 최종 결과 / 출력

### 2.2 작업 설정 영역 축소
- 프로젝트 경로/역할 안내/보조 문구를 `<details class="panel job-settings">`로 이동(기본 닫힘)
- textarea rows 14 → 6
- CSS `textarea min-height` 330px → 140px

### 2.3 Claude + Codex 구조 유지 여부
- 메인 액션 버튼 4개 유지
- 옛 역할(Gemini Manager / Claude Architect / Claude Reviewer / Git Shell) 마크업 재노출 없음
- `data-send` 매핑(claude-plan / codex-implement / claude-review) 그대로
- `git status`, `git diff`는 고급 제어 details에 수동 유틸리티로 유지
- commit/push/merge 자동화 신설 없음

### 2.4 테스트 결과
- `node --check web/server.js`: <결과>
- `node --check web/public/app.js`: <결과>
- `git diff --stat`: <결과>
- `git status --short`: <결과>

## 3. Safety Confirmation

- secrets/.env/auth/payment/migration/infra 미변경
- projects/paper-trading 미변경
- commit/push/merge/deploy 자동화 신설 없음
- 임의 shell 명령 입력 UI/API 신설 없음
- 옛 5-역할 재노출 없음
- 새 API 라우트 추가 없음

## 4. Test Results

(2.4와 동일한 내용 인용)

## 5. Remaining TODOs

- 없음 (또는 명시)
```

## 완료 정의 (Done)

- HTML DOM 순서가 다음과 일치한다.
  `quick-actions` < `control-panel` < `tmux-panel` < `pipeline-status` < `job-settings` < `advanced-panel` < `artifacts` < `result-summary` < `output-panel`.
- `<section class="panel setup">`이 HTML에 존재하지 않는다.
- `<details class="panel job-settings">`가 존재하고 그 안에 `#projectDir`, `.role-display`, `.role-aside`가 들어 있다.
- `<textarea id="inputKo" ... rows="6">`(또는 6–8 사이) 존재.
- CSS `.setup { grid-row: span 4; }`, `.output-panel { grid-column: 2; }` 제거.
- CSS `.layout`이 `flex-direction: column` 단일 컬럼.
- CSS `textarea` `min-height`가 140px 수준.
- `Gemini Manager`/`Claude Architect`/`Claude Reviewer`/`Git Shell` 라벨/버튼이 메인 마크업에 없다.
- `commit`/`push`/`merge`/`deploy` 자동화 버튼/엔드포인트 신설 없음.
- 임의 shell 입력 UI/API 신설 없음.
- `projects/paper-trading/`, `.env`, secrets, auth, payment, migration, infra 미변경.
- `node --check web/server.js`와 `node --check web/public/app.js` 둘 다 종료코드 0.
- `git diff --stat`이 보고하는 변경 파일이 mvp-004 허용 범위 안에만 있다.
- `git status --short`에 `.env`가 등장하지 않는다.
- `patch.md`가 5섹션으로 채워져 있다.
