## 1. 요청 요약

AI 개발팀 브라우저 GUI(`web/public/`)의 화면 배치를 사용 우선순위에 맞춰 재배열한다. 현재는 왼쪽 큰 컬럼이 `작업 설정`(긴 textarea 포함)으로 채워져 있고 오른쪽에 `파이프라인 상태`가 가장 위에 와서, 실제 작업 중 자주 보는 `승인 / 서비스 제어`와 `실시간 tmux 출력`이 화면 하단으로 밀린다. 새 배치 우선순위는 다음과 같다.

1. 상단: 작업 ID + 한국어 작업 요청 입력 + 주요 실행 버튼(4개)
2. 그 아래: 승인 / 서비스 제어 + 실시간 tmux 출력
3. 그 아래: 파이프라인 상태
4. 그 아래(접기/펼치기): 작업 설정(프로젝트 경로, 역할 안내, hint), 고급 제어, 산출물, 최종 결과, 출력

부가 조건:

- `Claude + Codex` 2-role 구조 유지. 옛 역할(`Gemini Manager`, `Claude Architect`, `Claude Reviewer`, `Git Shell`) 다시 노출 금지.
- 메인 액션 버튼 4개 유지: `Claude → Codex → Claude 전체 실행`, `Claude 계획 생성`, `Codex 구현 실행`, `Claude 리뷰 실행`.
- `git status`, `git diff`는 수동 유틸리티 버튼으로만 유지(`commit`/`push`/`merge` 자동화 금지).
- 반응형 화면이 깨지지 않아야 한다. 작은 화면에서도 실시간 출력과 승인 버튼이 잘 보여야 한다.
- 페이퍼매매 로직(`projects/paper-trading/` 등)·secrets·`.env`·auth·payment·production infra·DB migration은 건드리지 않는다.
- 임의 shell 명령 입력 기능 신설 금지.
- `git commit/push/merge/deploy` 자동화 금지.

검증:
- `node --check web/server.js`
- `node --check web/public/app.js`
- `git diff --stat`

완료 후 `patch.md`에 (i) 어떤 UI 영역을 어디로 옮겼는지, (ii) 작업 설정 영역을 어떻게 줄였는지, (iii) Claude+Codex 구조 유지 여부, (iv) 테스트 결과를 정리한다.

## 2. 작업 범위

### 포함 (In scope)

- `web/public/index.html`의 `<main class="layout">` 안 섹션 순서 재배치 및 `<section class="panel setup">`을 두 부분으로 분리:
  - **핵심 실행 패널**(`<section class="panel quick-actions">`, 신규 클래스): 작업 ID, 한국어 작업 요청(짧은 textarea), 4개 메인 액션 버튼만.
  - **작업 설정 패널**(`<details class="panel job-settings">`, 접기/펼치기): 프로젝트 경로, 역할 안내, 보조 안내 문구. 기본 닫힘.
- 섹션 순서를 다음으로 변경(상단→하단):
  1. `header.topbar` (변경 없음)
  2. `section.panel.quick-actions` (신규, 최상단)
  3. `section.panel.control-panel` (승인/서비스 제어)
  4. `section.panel.tmux-panel` (실시간 tmux 출력)
  5. `section.panel.pipeline-status` (파이프라인 상태)
  6. `details.panel.job-settings` (작업 설정 — 접기/펼치기)
  7. `details.panel.advanced-panel` (고급 제어 — 접기/펼치기, 기존 유지)
  8. `section.panel.artifacts` (산출물)
  9. `section.panel.result-summary` (최종 결과)
  10. `section.panel.output-panel` (출력)
  11. `#approvalModal` (변경 없음)
- `web/public/style.css`에서 레이아웃 단순화:
  - 2-열 그리드(`.layout { grid-template-columns: ... }`)와 `.setup { grid-row: span 4 }`, `.output-panel { grid-column: 2 }`를 단일 컬럼 스택으로 교체. 단순화가 안전성이 가장 높고 반응형도 보장.
  - 최대 폭은 `max-width: 1100px` 정도로 유지(가로로 너무 넓어지지 않도록).
  - textarea 기본 높이를 6 rows 수준(`min-height` 약 140–160px)으로 축소.
  - 신규 클래스 `.quick-actions`, `.job-settings`(details 스타일)에 가벼운 패딩/간격 추가.
  - 기존 `.role-display`, `.role-aside`는 `job-settings` 내부에서도 잘 보이도록 그대로 사용.
  - 모바일(`max-width: 920px`) 미디어 쿼리는 유지하되 단일 컬럼이 기본이라 추가 분기 거의 없음.
- `web/public/app.js`: ID 기반 셀렉터는 모두 그대로이므로 기능 변경 없음. 단, `inputKoEl`의 `rows`가 HTML에서 작아지는 것 외 변경 없음. 임의 shell 입력 핸들러 신설 금지.
- `web/server.js`: 변경 없음(요청 자체가 layout 한정). 단 검증 명령은 그대로 실행.
- 문서: README, CLAUDE_CODEX_WORKFLOW에 시각 배치를 명시적으로 적어둔 부분이 없으므로 변경 불필요. 만약 patch.md 작성 중 표현이 어긋난 부분을 발견하면 한 줄만 보정 — 그 외 적극 수정 금지.

### 제외 (Out of scope; 절대 만지지 않음)

- `projects/paper-trading/`, `app/`, broker adapter, RiskEngine, OMS, Strategy, `/paper/status` API 등 mvp-003 영역.
- `prompts/`, `scripts/`, `docs/` 아래 mvp-004와 무관한 파일.
- `web/server.js`의 라우트, tmux 안전 상수, 파이프라인 로직.
- `.env`, secrets, credentials, API key, token 류.
- 인증/로그인/세션/패스워드/토큰 처리, 결제, DB 마이그레이션, production infra.
- `git commit`, `git push`, PR 생성/머지, 배포 자동화.
- 임의 shell 명령 실행 UI/API.
- 옛 5-역할(`Gemini Manager`, `Claude Architect`, `Claude Reviewer`, `Git Shell`)을 메인 UI에 다시 노출하는 변경.
- 새 API 엔드포인트 추가, 기존 `data-send` 매핑 변경.

### 안전 가드

- 모든 변경은 다음 파일에 한정한다.
  - `web/public/index.html`
  - `web/public/style.css`
  - `web/public/app.js` (변경 없을 가능성이 높음 — 변경한다면 행 수 최소)
  - `docs/ai/jobs/mvp-004/patch.md` (Codex 신규 작성)
- 새 ID/클래스 이름은 충돌하지 않도록 다음만 사용한다: `quick-actions`, `job-settings`. 기존 ID(`#projectDir`, `#jobId`, `#inputKo`, `#runPipeline`, `#tmuxOutput`, `#tmuxWindow`, `#approveOnce`, `#approveSession`, `#rejectAction`, `#interruptAction`, `#refreshTmuxOutput`, `#refreshStatus`, `#pipelineStatus`, `#resetPipeline`, `#startTeam`, `#createJob`, `#saveInput`, `#gitStatus`, `#gitDiff`, `#loadArtifacts`, `#clearOutput`, `#approvalModal`, `[data-send=...]`, `[data-approval-action=...]`)는 그대로 유지.

## 3. 수정해야 할 파일

| 파일 | 변경 내용 |
| --- | --- |
| `web/public/index.html` | `<main class="layout">` 내부 섹션 분리·재배치, 작업 설정 details 패널 신설, textarea `rows` 축소 |
| `web/public/style.css` | `.layout` 단일 컬럼화, `.setup`/`.output-panel` 그리드 규칙 제거, `.quick-actions`/`.job-settings` 스타일 추가, textarea `min-height` 축소 |
| `web/public/app.js` | (기본은 무변경) 만약 textarea의 `rows` 변경이 JS에 영향을 주지 않는다면 손대지 않음 |
| `web/server.js` | 변경 없음. 검증만 |
| `docs/ai/jobs/mvp-004/patch.md` | Codex 변경 요약 |

## 4. Codex 구현 지시문

> Codex는 다음 지시를 그대로 따른다. 범위 확장 금지. 안전 규칙 우선.

### 4.1 사전 조건

- 작업 루트: `/root/ai-dev-center/projects/ai-team`.
- 대상 파일: `web/public/index.html`, `web/public/style.css` (필요 시 `web/public/app.js`). 그 외는 만지지 않는다.
- 기존 ID/data 속성/JS 이벤트 바인딩이 깨지지 않도록 유지한다.
- `git commit`, `git push`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, API key, token, auth, payment, DB migration, production infra, `projects/paper-trading/` 등은 절대 만지지 않는다.

### 4.2 `web/public/index.html` 변경

`<main class="layout">` 안을 다음 순서로 다시 구성한다(기존 `<header class="topbar">`와 `<script>`, `#approvalModal`은 위치 변경 없이 유지).

1. **핵심 실행 패널** — 기존 `.setup` 섹션을 분해하여 다음 마크업을 최상단에 둔다.

   ```html
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
   ```

2. **승인 / 서비스 제어 패널** — 기존 `<section class="panel control-panel">` 마크업을 위 핵심 실행 바로 아래로 이동(내용 변경 없음).

3. **실시간 tmux 출력 패널** — 기존 `<section class="panel tmux-panel">` 마크업을 그 아래로 이동(내용 변경 없음).

4. **파이프라인 상태 패널** — 기존 `<section class="panel pipeline-status">` 마크업을 그 아래로 이동(내용 변경 없음).

5. **작업 설정 패널(접기/펼치기, 기본 닫힘)** — 신규.

   ```html
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
   ```

6. **고급 제어 패널** — 기존 `<details class="panel advanced-panel">` 마크업을 그 아래로 이동(내용 변경 없음, `startTeam`/`createJob`/`saveInput`/`gitStatus`/`gitDiff`만 유지).

7. **산출물 패널** — 기존 `<section class="panel artifacts">` 그대로.

8. **최종 결과 패널** — 기존 `<section class="panel result-summary">` 그대로.

9. **출력 패널** — 기존 `<section class="panel output-panel">` 그대로.

`#approvalModal` div는 `<main>` 닫힘 뒤 위치를 그대로 유지한다. `<script src="/app.js"></script>`도 위치 유지.

추가 주의:

- 기존 `<section class="panel setup">`은 완전히 제거하고 위 구조로 대체한다.
- `setup` 클래스를 더 이상 사용하지 않으므로 HTML에서 어디에도 나타나면 안 된다.
- 새로 도입한 `quick-actions`, `job-settings` 외에 다른 신규 클래스/ID를 만들지 않는다.
- 옛 역할(`Gemini Manager`, `Claude Architect`, `Claude Reviewer`, `Git Shell`)을 다시 노출하는 마크업을 추가하지 않는다.
- `Claude + Codex` 2-role 안내(`.role-display`, `.role-aside`)는 `job-settings` details 안에서만 유지한다.

### 4.3 `web/public/style.css` 변경

다음만 수정한다(다른 색상 토큰/컴포넌트 스타일은 보존).

1. `.layout` 규칙을 단일 컬럼으로 변경한다.

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

2. 다음 두 규칙은 완전히 제거한다(더 이상 사용되지 않음).

   ```css
   .setup { grid-row: span 4; }
   .output-panel { grid-column: 2; }
   ```

3. `textarea` 기본 높이를 줄인다.

   ```css
   textarea {
     min-height: 140px;
     resize: vertical;
     padding: 12px;
     line-height: 1.5;
   }
   ```

   기존 `min-height: 330px;`을 `140px`으로 교체한다.

4. 신규 컴포넌트 스타일을 적절한 위치(예: `.panel` 규칙 부근)에 추가한다.

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

5. `@media (max-width: 920px)` 블록 안에 있는 `.layout { grid-template-columns: 1fr; ... }` 같은 규칙은 더 이상 의미가 없으므로 제거하거나 단순화한다(예: `.layout { padding: 14px; }`만 남기기). `.setup, .output-panel { grid-row: auto; grid-column: auto; }`도 제거. `.step-grid`, `.role-display`, `.pipeline-meta`, `.primary-actions`의 1-column 분기는 유지한다.

6. `pre`(출력/실시간 tmux) 기본 `min-height`는 그대로 두되, 화면 가로폭이 좁아질 때 가독성이 깨지지 않는지 확인. (수정 불필요시 그대로.)

### 4.4 `web/public/app.js` 변경

- 가능한 한 손대지 않는다. 기존 ID(`#projectDir`, `#jobId`, `#inputKo`, `#runPipeline`, ...)는 그대로이므로 셀렉터가 깨지지 않는다.
- `#approvalInlinePrompt`, `#reopenApprovalPopup` 등 모달 관련 ID도 그대로 유지된다.
- 새 핸들러, 새 fetch 호출을 추가하지 않는다.
- 만약 textarea의 `rows="14"`가 JS에서 직접 참조되지 않는다면 — `grep -n "rows" web/public/app.js` 결과가 없다면 — 이 파일은 변경하지 않는다.

### 4.5 `web/server.js`

- 변경하지 않는다. `node --check web/server.js`를 검증만 수행한다.

### 4.6 문서

- README와 `docs/ai/CLAUDE_CODEX_WORKFLOW.md`는 layout 시각 배치를 명시적으로 적어두지 않았으므로 변경하지 않는다.
- 만약 문서 안에 "왼쪽 컬럼"·"오른쪽 컬럼" 같은 시각적 표현이 있다면 한 줄만 보정. 발견되지 않으면 손대지 않는다.

### 4.7 검증 명령

작업 디렉터리 `/root/ai-dev-center/projects/ai-team`에서 실행한다.

```bash
node --check web/server.js
node --check web/public/app.js
git diff --stat
git status --short
```

네 명령 결과를 `docs/ai/jobs/mvp-004/patch.md`의 Test Results에 그대로 인용한다. `node --check` 두 개는 종료코드 0이어야 한다. 실패하면 작업을 멈추고 원인을 `patch.md`에 남긴다.

### 4.8 `docs/ai/jobs/mvp-004/patch.md`

`prompts/codex-implementer.md`의 형식을 따른다. Implementation Summary는 요청의 "완료 후" 항목과 1:1로 대응하도록 다음 4개 단락을 분리해서 적는다.

```markdown
## 1. Files Changed
## 2. Implementation Summary
### 2.1 옮긴 UI 영역
- 핵심 실행(작업 ID + 한국어 요청 + 메인 버튼 4개) → 최상단
- 승인 / 서비스 제어 → 그 아래
- 실시간 tmux 출력 → 그 아래
- 파이프라인 상태 → 그 아래
- 작업 설정 (프로젝트 경로, 역할 안내, role-aside) → 접기/펼치기 details로 그 아래
- 고급 제어 / 산출물 / 최종 결과 / 출력 → 그 아래

### 2.2 작업 설정 영역 축소
- 프로젝트 경로/역할 안내/보조 문구를 `<details class="panel job-settings">`로 이동
- textarea rows 14 → 6, CSS `min-height` 330px → 140px

### 2.3 Claude + Codex 구조 유지 여부
- 메인 액션 버튼 4개 유지
- Gemini Manager / Claude Architect / Claude Reviewer / Git Shell 마크업 재노출 없음
- `data-send` 매핑 (claude-plan / codex-implement / claude-review) 유지
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
- 임의 shell 입력 UI/API 신설 없음
- 옛 5-역할 재노출 없음

## 4. Test Results
(위 2.4와 동일하게 인용)

## 5. Remaining TODOs
- 없음 (또는 명시)
```

## 5. 테스트 기준

1. `node --check web/server.js` 종료코드 0.
2. `node --check web/public/app.js` 종료코드 0.
3. `git diff --stat` 결과에 다음 외 파일이 포함되어 있지 않다.
   - `web/public/index.html`
   - `web/public/style.css`
   - (선택) `web/public/app.js`
   - `docs/ai/jobs/mvp-004/patch.md`
4. `git status --short`에 `.env` 또는 secrets가 staged/untracked로 등장하지 않는다.
5. `web/public/index.html`에서 다음이 모두 동시에 만족한다.
   - DOM 순서: `.quick-actions` < `.control-panel` < `.tmux-panel` < `.pipeline-status` < `.job-settings` < `.advanced-panel` < `.artifacts` < `.result-summary` < `.output-panel`.
   - `<section class="panel setup">` 마크업이 존재하지 않는다.
   - `<details class="panel job-settings">`가 존재하고 그 안에 `#projectDir`, `.role-display`, `.role-aside`가 있다.
   - `id="jobId"`, `id="inputKo"`, `id="runPipeline"`, `data-send="claude-plan"`, `data-send="codex-implement"`, `data-send="claude-review"`가 모두 존재한다.
   - `<textarea id="inputKo" ... rows="6">` (또는 6–8 사이) 가 존재한다.
   - `Gemini Manager`, `Claude Architect`, `Claude Reviewer`, `Git Shell` 라벨/버튼이 메인 마크업에 존재하지 않는다.
6. `web/public/style.css`에서 `.setup { grid-row: span 4; }`와 `.output-panel { grid-column: 2; }` 규칙이 존재하지 않는다. 새 `.layout` 규칙이 `flex-direction: column`을 사용한다.
7. 작은 화면(예: 480px) 가정 시 `pre#tmuxOutput`과 `.control-actions`가 잘리지 않는다(시각 검증은 사람이 수행, 코드 측에서는 1-column flow를 깨지 않음).

## 6. 리뷰 체크리스트

- [ ] DOM 순서가 요청의 우선순위(상단→하단)와 정확히 일치한다.
- [ ] `핵심 실행` 패널이 최상단이며 `작업 ID`, `한국어 작업 요청`, 4개 메인 버튼만 포함한다.
- [ ] `승인 / 서비스 제어`, `실시간 tmux 출력`이 그 바로 아래에 노출된다.
- [ ] `파이프라인 상태`가 그 아래로 이동했다.
- [ ] `작업 설정`이 `<details>` 접기/펼치기 패널로 분리되었고 기본 닫힘이다.
- [ ] textarea가 `rows="6"` 수준으로 축소되었고 CSS `min-height`도 축소되었다.
- [ ] `.setup` 그리드 규칙이 CSS에서 제거되었다.
- [ ] `.layout`이 단일 컬럼 flex/grid로 단순화되었다.
- [ ] 모든 기존 ID와 `data-send`/`data-approval-action` 속성이 보존되어 JS 핸들러가 깨지지 않는다.
- [ ] 옛 5-역할(Gemini Manager / Claude Architect / Claude Reviewer / Git Shell)이 메인 UI에 재노출되지 않는다.
- [ ] `git status`, `git diff`만 수동 유틸리티 버튼으로 남아 있다. `commit`/`push`/`merge` 자동화 신설 없음.
- [ ] 임의 shell 입력 UI/API 신설 없음.
- [ ] `projects/paper-trading/`, `.env`, secrets, auth, payment, migration, infra 미변경.
- [ ] `node --check web/server.js`, `node --check web/public/app.js`가 모두 통과한다.
- [ ] `patch.md`에 (i) 옮긴 영역, (ii) 작업 설정 축소 방법, (iii) Claude+Codex 구조 유지, (iv) 테스트 결과가 모두 들어 있다.
- [ ] `git diff --stat`에 mvp-004 외 변경 없음.
