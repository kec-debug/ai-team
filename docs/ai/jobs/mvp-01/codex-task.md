# Codex Task — mvp-01: GUI를 Claude + Codex 2-role로 단순화

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-01/plan.md` and `docs/ai/jobs/mvp-01/request.ko.md` first.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-01`
- Job directory: `/root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-01`
- 워크플로 문서: `docs/ai/CLAUDE_CODEX_WORKFLOW.md`
- 현재 GUI는 이미 backend(`web/server.js`) 수준에서는 Claude/Codex 위주로 단순화되어 있지만, 화면 카드(`Manual Shell` 포함)와 고급 패널의 중복 버튼, 기본 작업 ID(`job-002`) 같은 잔여 흔적이 남아 있다. 이번 작업의 목적은 그 잔여 흔적을 정리하고 README/Workflow 문서에 새 GUI 사용법을 반영하는 것이다.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 추가 금지.
- `.env`, secrets, credentials, API key, token 류 변경 금지.
- auth / 로그인 / 세션 / 비밀번호 / 토큰 처리 코드 변경 금지.
- payment / billing / subscription 코드 변경 금지.
- database migration, 데이터 backfill 변경 금지.
- production infra, `.github/workflows/` 변경 금지.
- 임의 shell 명령 입력 UI/API 신설 금지.
- 본 작업 범위 외 파일 변경 금지.

## 수정 허용 파일 (이것만)

- `web/public/index.html`
- `web/public/app.js`
- `web/public/style.css`
- `web/server.js` (확인 위주, 누락이 있을 때만 보정)
- `README.md`
- `docs/ai/CLAUDE_CODEX_WORKFLOW.md`
- `docs/ai/jobs/mvp-01/patch.md` (Codex가 새로 작성)

그 외 파일은 만지지 않는다. `prompts/`, `scripts/`, `examples/`, `docs/safety-rules.md`, `docs/setup.md`, `docs/workflow.md`는 이 작업에서 변경하지 않는다.

## 구현 작업

### 1) `web/public/index.html`

- `.role-display`에서 `Manual Shell` 카드를 제거하고 Claude/Codex 두 카드만 남긴다.
- `.role-display` 바로 아래에 보조 안내문을 추가한다:

  ```html
  <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
  ```

- 기존 `.pipeline-runner` 영역을 다음 구조로 교체한다.

  ```html
  <div class="pipeline-runner">
    <button id="runPipeline" class="primary-action" type="button">Claude → Codex → Claude 전체 실행</button>
    <div class="primary-actions">
      <button data-send="claude-plan" type="button">Claude 계획 생성</button>
      <button data-send="codex-implement" type="button">Codex 구현 실행</button>
      <button data-send="claude-review" type="button">Claude 리뷰 실행</button>
    </div>
  </div>
  ```

- 고급 패널(`<details class="advanced-panel">`)의 버튼 목록을 다음만 남긴다(중복된 `data-send` 버튼 3개 제거).

  ```html
  <div class="actions">
    <button id="startTeam" type="button">AI 팀 시작</button>
    <button id="createJob" type="button">작업 폴더 생성</button>
    <button id="saveInput" type="button">request.ko.md 저장</button>
    <button id="gitStatus" type="button">git status</button>
    <button id="gitDiff" type="button">git diff</button>
  </div>
  ```

- 작업 ID 기본값을 `<input id="jobId" type="text" value="mvp-001" autocomplete="off" spellcheck="false">`로 바꾼다.
- 그 외 구조(헤더, 파이프라인 상태 패널, 승인/서비스 제어, 실시간 tmux 출력, 최종 결과, 산출물, 출력 패널)는 손대지 않는다.

### 2) `web/public/app.js`

- `state.jobId` 기본값을 `'mvp-001'`로 변경한다.
- 그 외 동작은 변경하지 않는다. `[data-send]` 일괄 핸들러가 이미 메인의 새 버튼 3개를 처리한다.
- 임의 shell 명령 실행을 호출하는 새 fetch/handler를 만들지 않는다.

### 3) `web/public/style.css`

- `.role-display`의 `grid-template-columns`를 `repeat(2, minmax(0, 1fr))`로 변경한다.
- 다음 두 블록을 파일 끝(또는 적절한 인접 위치)에 추가한다.

  ```css
  .role-aside {
    margin: 10px 0 0;
    padding: 8px 10px;
    border: 1px dashed var(--line);
    border-radius: 6px;
    color: var(--muted);
    font-size: 12px;
    line-height: 1.45;
  }

  .primary-actions {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
    margin-top: 10px;
  }
  ```

- `@media (max-width: 920px) { ... }` 블록 안에 다음 한 줄을 추가한다(2열 → 1열로 줄이는 기존 패턴과 동일):

  ```css
  .primary-actions {
    grid-template-columns: 1fr;
  }
  ```

- 색상 토큰, 폰트, 다른 컴포넌트 스타일은 변경하지 않는다.

### 4) `web/server.js`

- 다음 상수가 그대로인지 확인만 한다. 일치하면 이 파일은 수정하지 않는다.
  - `SAFE_WINDOWS`: `claude-plan`, `codex-implement`, `claude-review`, `claude`, `codex` 키만 존재.
  - `ALLOWED_TMUX_WINDOWS`: `claude`, `codex`, `git-shell`만 포함.
  - `AI_TMUX_WINDOWS`: `claude`, `codex`만 포함.
  - `ACTIVE_PIPELINE_STATES`: `claude_planning`, `codex_implementing`, `claude_reviewing`, `approval_required`.
  - `FINAL_PIPELINE_STATES`: `succeeded`, `failed`, `blocked`, `manual_review_required`, `idle`.
  - `ARTIFACT_PRIORITY`: `request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, `review.md`, `status.md` 순.
- 누락된 항목이 있을 때만 추가한다. 새 라우트(`commit`, `push`, `merge`, `deploy`, 임의 shell)는 추가하지 않는다.

### 5) `README.md`

- "팀 구성" 표의 본문을 다음 2행으로만 남긴다(기존 3행 중 Manual Shell 행 제거).

  | 역할 | 하는 일 | 주요 산출물 |
  |------|---------|-----------|
  | Claude | 한국어 요청 정리, 설계, 리스크 점검, 리뷰 | `plan.md`, `review.md` |
  | Codex | 구현, 테스트, 패치 요약 | 코드 변경 + `patch.md` |

- 표 바로 아래에 한 줄을 추가한다.

  > Manual Shell(`git-shell`)은 사람이 직접 `git status`, `git diff`, 테스트, commit, PR 명령을 실행하는 보조 창입니다. AI 역할이 아니며 GUI 파이프라인이 자동화하지 않습니다.

- "Deprecated: 이전 5역할 구성" 블록 전체(제목 + 표)를 `<details>` 안으로 감싼다.

  ```markdown
  <details>
  <summary>Deprecated: 이전 5역할 구성</summary>

  ... (기존 표 그대로 유지) ...

  </details>
  ```

- "브라우저 GUI" 섹션의 불릿 목록을 정리해 다음 항목을 명시적으로 포함시킨다(겹치는 줄은 통합하고, 새 항목은 추가).
  - 메인 액션 버튼 4개: `Claude → Codex → Claude 전체 실행`, `Claude 계획 생성`, `Codex 구현 실행`, `Claude 리뷰 실행`.
  - 파이프라인 상태 8단계: `claude_planning`, `codex_implementing`, `claude_reviewing`, `manual_review_required`, `succeeded`, `failed`, `blocked`, `approval_required`.
  - 수동 유틸리티 버튼 2개: `git status`, `git diff`.
  - 자동화하지 않는 것: `commit`, `push`, PR 생성/머지, 배포.
  - 임의 shell 명령 입력 기능 없음.
  - 절대 변경하지 않는 영역: `.env`, secrets, auth, payment, production infra, database migrations.
- 디렉터리 구조 트리, alias 설명, push 전 체크리스트, "안전 규칙(요약)" 섹션은 그대로 둔다.

### 6) `docs/ai/CLAUDE_CODEX_WORKFLOW.md`

- "Codex에게 요청하는 방법" 섹션 다음, "결과 리뷰 방법" 앞에 새 섹션 `## 브라우저 GUI`를 추가한다. (이미 비슷한 섹션이 있다면 항목만 보강한다.)
- 섹션 본문에 다음을 모두 포함한다.
  - 기본 주소: `http://127.0.0.1:3100` (외부 공개용 아님)
  - 메인 액션 버튼 4개와 매핑되는 API:
    - `Claude → Codex → Claude 전체 실행` → `POST /api/pipeline/run`
    - `Claude 계획 생성` → `POST /api/send/claude-plan`
    - `Codex 구현 실행` → `POST /api/send/codex-implement`
    - `Claude 리뷰 실행` → `POST /api/send/claude-review`
  - 상태 단계 8개 목록(`claude_planning`, `codex_implementing`, `claude_reviewing`, `manual_review_required`, `succeeded`, `failed`, `blocked`, `approval_required`).
  - tmux 기본 대상은 `ai-team:claude`, `ai-team:codex` 두 창. `gemini-manager`, `claude-architect`, `claude-reviewer`, `git-shell`은 기본 자동화 대상이 아님. `git-shell`은 사람이 직접 git/test 명령을 실행하는 비AI 보조 창.
  - 수동 유틸리티 버튼 2개: `git status`, `git diff`. 자동 `commit`/`push`/`merge`/`deploy` 없음.
  - 임의 shell 명령 입력 기능은 GUI에서 제공하지 않음.
  - 절대 자동화하지 않는 것: `commit`, `push`, PR merge, production 배포, `.env`/secrets/auth/payment/production infra/database migrations 변경.
- 기존 "이전 5역할 워크플로", "새 역할 모델", "안전 규칙", "절대 자동화하지 않는 것" 섹션은 손대지 않는다.

### 7) `docs/ai/jobs/mvp-01/patch.md`

작업이 끝난 뒤 다음 형식으로 작성한다.

```markdown
## 1. Files Changed

- web/public/index.html
- web/public/app.js
- web/public/style.css
- README.md
- docs/ai/CLAUDE_CODEX_WORKFLOW.md
(서버 보정이 있었다면 web/server.js 추가)

## 2. Implementation Summary

각 파일에서 한 일 요약. 메인 액션 버튼 4개 노출, Manual Shell 카드 제거, 작업 ID 기본값 변경, 보조 안내 문구 추가, README/Workflow 문서에 새 GUI 사용법 반영 등.

## 3. Safety Confirmation

- secrets / .env / auth / payment / migration / infra 변경 없음.
- commit / push / merge / deploy 자동화 추가 없음.
- 임의 shell 명령 입력 UI/API 신설 없음.
- tmux 기본 대상은 ai-team:claude, ai-team:codex 두 창만 사용.

## 4. Test Results

- node --check web/server.js: <결과>
- node --check web/public/app.js: <결과>
- git diff --stat: <결과>

## 5. Remaining TODOs

- 없음 (또는 있으면 명시)
```

## 검증 명령

작업 디렉터리(`/root/ai-dev-center/projects/ai-team`)에서 실행한다.

```bash
node --check web/server.js
node --check web/public/app.js
git diff --stat
```

세 명령 결과를 `patch.md`의 "Test Results"에 그대로 인용한다. `node --check` 두 개는 종료코드 0이어야 한다. 실패하면 작업을 중단하고 원인 메시지를 `patch.md`에 남긴 뒤 멈춘다.

## 완료 정의 (Done)

- 위 6개(또는 5개) 파일이 변경되었고, 그 외 파일은 변경되지 않았다(`git diff --stat`로 확인).
- 메인 패널에 액션 버튼 4개가 노출된다.
- 고급 패널에 중복된 `data-send` 버튼이 없고, `git status`, `git diff`만 수동 유틸리티로 남아 있다.
- README와 CLAUDE_CODEX_WORKFLOW가 새 GUI 사용법(4개 버튼, 8개 상태, 2개 수동 유틸리티, 자동화 금지 항목, 임의 shell 없음, 변경 금지 영역)을 모두 반영한다.
- `node --check` 두 명령 모두 통과.
- `patch.md`가 작성되어 있다.
- 사람이 `commit`/`push`/`merge`/`deploy`를 직접 실행해야 한다는 점이 변경 산출물에 반영되어 있다.
