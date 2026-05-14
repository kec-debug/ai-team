## 1. 요청 요약

AI 개발팀 컨트롤 센터(브라우저 GUI)에 아직 남아 있는 deprecated 5역할 UI 흔적을 정리하고, 현재 운영되는 **Claude + Codex 2-role** 워크플로만 보이도록 단순화한다.

핵심 요구:

1. GUI에서 `Gemini Manager`, `Claude Architect`, `Claude Reviewer`, `Git Shell`을 핵심 AI 역할에서 제거하거나 숨긴다.
2. 메인 액션 버튼을 다음 4개로 정렬한다.
   - Claude 계획 생성
   - Codex 구현 실행
   - Claude 리뷰 실행
   - Claude → Codex → Claude 전체 실행
3. tmux 대상은 `ai-team` 세션의 `claude`, `codex` 창만 기본 대상으로 사용한다.
4. `gemini-manager`, `claude-architect`, `claude-reviewer`, `git-shell` 창은 기본 대상에서 빠진다. `git-shell`은 사람이 직접 git 명령을 실행하는 보조 창으로만 표시하고, GUI 파이프라인은 절대 자동화하지 않는다.
5. 작업 산출물은 다음 6개 파일을 기준으로 정렬한다.
   - `request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, `review.md`, `status.md`
6. 상태 단계는 다음 8개로 단순화한다.
   - `claude_planning`, `codex_implementing`, `claude_reviewing`, `manual_review_required`, `succeeded`, `failed`, `blocked`, `approval_required`
7. `git status`, `git diff`는 수동 유틸리티 버튼으로만 노출한다.
8. `commit`, `push`, `merge`, `deploy`는 자동화하지 않는다.
9. 임의 shell 명령 입력 기능은 만들지 않는다.
10. secrets, `.env`, auth, payment, production infra, database migrations는 건드리지 않는다.
11. `README.md`, `docs/ai/CLAUDE_CODEX_WORKFLOW.md`에 새 사용법을 반영한다.

검증 명령:

- `node --check web/server.js`
- `node --check web/public/app.js`
- `git diff --stat`

완료 후 `patch.md`에 변경 요약을 남긴다.

## 2. 작업 범위

### 포함 (In scope)

- `web/public/index.html`의 역할/버튼/안내 문구 정리. 메인 액션 버튼 4개를 1번 패널에 노출하고, 고급 패널에서는 동일 버튼을 중복 노출하지 않는다.
- `web/public/app.js`의 이벤트 바인딩과 상태 모델을 단순화. 기존 동작은 유지하되 메인 버튼 4개가 한 곳에서 작동하도록 핸들러 정리.
- `web/public/style.css`에서 역할 그리드(`.role-display`)를 3열 → 2열로 줄이고 보조 안내 영역을 분리.
- `web/server.js`의 GUI 표면(SAFE_WINDOWS, ALLOWED_TMUX_WINDOWS, AI_TMUX_WINDOWS, TMUX_WINDOW_LABELS)에서 `gemini-manager`, `claude-architect`, `claude-reviewer`는 이미 제거되어 있는지 확인. (현재 코드 기준 이미 정리되어 있으므로 추가 정리할 항목이 없으면 손대지 않는다.)
- `README.md`에서 deprecated 5역할 표를 historical 한 줄 안내로 축소하거나 별도 섹션으로 더 명확히 분리, 그리고 새 GUI 버튼 4개 설명을 보강.
- `docs/ai/CLAUDE_CODEX_WORKFLOW.md`에 GUI의 새 버튼 4개와 상태 단계 8개, 수동 유틸리티 버튼(`git status`, `git diff`) 안내를 추가.
- 작업 종료 시 `docs/ai/jobs/mvp-01/patch.md` 작성.

### 제외 (Out of scope, 절대 건드리지 않음)

- `.env`, secrets, credentials, API key, token 류 일체.
- 인증/로그인/세션/패스워드/토큰 처리 코드.
- payment / billing / subscription 코드.
- database migration, 데이터 backfill.
- production infra, `.github/workflows/`.
- `git commit`, `git push`, PR 생성/머지, 배포 자동화.
- 임의 shell command 실행 API/UI 신설.
- tmux 세션 시작 스크립트(`scripts/start-ai-team.sh`)에서 `git-shell` 창 자체를 제거하는 것. (사람이 쓰는 수동 창이므로 유지)
- 기존 deprecated 프롬프트 파일(`prompts/gemini-manager.md`, `prompts/claude-architect.md`, `prompts/claude-reviewer.md`) 삭제. (historical 참조용으로 README에서만 안내)

### 안전 가드

- 변경 파일은 모두 `web/public/`, `web/server.js`, `README.md`, `docs/ai/CLAUDE_CODEX_WORKFLOW.md`로 한정한다.
- 파이프라인 자동화가 `commit/push/merge/deploy`로 확장되지 않도록 server.js의 안전 차단 패턴(`SAFETY_DENY_PATTERNS`)과 라우트 화이트리스트는 그대로 둔다.
- 임의 명령 입력 필드는 만들지 않는다.

## 3. 수정해야 할 파일

| 파일 | 변경 내용 |
| --- | --- |
| `web/public/index.html` | 역할 안내 카드에서 `Manual Shell` 항목 제거(보조 안내문으로 이동), 메인 패널에 액션 버튼 4개(`Claude 계획 생성`, `Codex 구현 실행`, `Claude 리뷰 실행`, `Claude → Codex → Claude 전체 실행`) 노출, 고급 패널에서는 동일 버튼 중복 제거하고 `git status`/`git diff`만 수동 유틸리티로 유지, 헤더 부제와 작업 ID 기본값을 `mvp-001` 같이 새 명명에 맞게 정리 |
| `web/public/app.js` | 새 버튼 ID에 대한 이벤트 바인딩 정리(`data-send` 기반 일괄 처리 유지), 기본 작업 ID(`job-002`)를 새 흐름과 일관된 값(`mvp-001`)으로 갱신, 임의 shell 입력/명령 추가 금지, 기존 상태 매핑(`activePipelineStates`, `finalPipelineStates`)이 8단계와 정확히 일치하는지 확인 |
| `web/public/style.css` | `.role-display`를 2열 그리드로 변경, 새 메인 액션 그리드(`.primary-actions`) 스타일 추가, 보조 안내문(Manual Shell) 영역용 작은 스타일 추가 |
| `web/server.js` | (확인 위주) `SAFE_WINDOWS`, `ALLOWED_TMUX_WINDOWS`, `AI_TMUX_WINDOWS`, `TMUX_WINDOW_LABELS`, `ACTIVE_PIPELINE_STATES`, `FINAL_PIPELINE_STATES`가 이미 `claude`/`codex`/`git-shell`만 사용하고 상태 8단계를 반영하는지 확인. 누락 시 보정. `commit/push/merge/deploy` 라우트가 신설되지 않도록 그대로 유지 |
| `README.md` | "팀 구성" 표를 Claude/Codex 2행 + Manual Shell 보조 행만 표시하도록 정리, deprecated 5역할 표를 별도 `<details>` 또는 명시 섹션으로 강등, GUI 섹션에서 4개 메인 버튼과 8개 상태, 수동 유틸리티(`git status`, `git diff`)를 명확히 기술 |
| `docs/ai/CLAUDE_CODEX_WORKFLOW.md` | "브라우저 GUI" 섹션을 추가하거나 보강해 4개 메인 버튼, 8개 상태, 수동 유틸리티, 자동화 금지 항목(`commit/push/merge/deploy`)을 한 곳에 정리 |
| `docs/ai/jobs/mvp-01/patch.md` | Codex가 변경 요약(파일 목록, 구현 요약, 안전 확인, 테스트 결과, 남은 TODO)을 기록 |

## 4. Codex 구현 지시문

> 아래는 Codex에게 그대로 전달할 구현 작업이다. 범위를 임의로 늘리지 말고, 안전 규칙은 항상 우선한다.

### 4.1 사전 조건

- 작업 루트: `/root/ai-dev-center/projects/ai-team`
- 작업 ID: `mvp-01`
- 모든 변경은 위 6개 파일에 한정한다. 그 외 파일은 만지지 않는다.
- 이 작업에서 `commit`, `push`, PR 생성/머지, 배포, secrets 수정은 절대 하지 않는다.
- 임의 shell 명령 입력 UI/API를 새로 만들지 않는다.

### 4.2 `web/public/index.html` 변경

1. 헤더 부제(eyebrow) 텍스트는 `Claude + Codex Workflow`로 유지한다.
2. `.role-display`에서 `Manual Shell` 카드를 제거하고, 그 자리 바로 아래에 작은 보조 안내 문단(`<p class="role-aside">`)을 추가한다. 안내 문구는 다음 한 줄: `Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.`
3. `.pipeline-runner` 영역을 다음 4개 버튼이 들어가는 그리드로 교체한다. 가장 먼저 풀폭으로 `Claude → Codex → Claude 전체 실행`이 오고, 그 아래 줄에 `Claude 계획 생성`, `Codex 구현 실행`, `Claude 리뷰 실행`을 같은 크기로 배치한다.
   - 버튼은 `data-send="claude-plan"`, `data-send="codex-implement"`, `data-send="claude-review"` 속성을 사용한다(이미 `app.js`의 핸들러가 처리한다).
   - 풀폭 전체 실행 버튼은 기존 `id="runPipeline"`를 유지한다.
4. 고급 패널(`<details class="advanced-panel">`)에서 중복된 `data-send` 버튼 3개를 제거하고, 다음 보조 버튼만 남긴다.
   - `AI 팀 시작`(`#startTeam`)
   - `작업 폴더 생성`(`#createJob`)
   - `request.ko.md 저장`(`#saveInput`)
   - 수동 유틸리티 그룹으로 `git status`(`#gitStatus`), `git diff`(`#gitDiff`).
5. 작업 ID 기본값(`<input id="jobId" value="...">`)을 `mvp-001`로 변경한다.
6. 헤더 우측 `상태 확인` 버튼 옆이나 위쪽 어딘가에 임의 shell 입력 UI가 없는지 확인한다. 있다면 도입하지 않는다(현재 없음).

### 4.3 `web/public/app.js` 변경

1. `state.jobId` 기본값을 `'mvp-001'`로 변경한다(localStorage 키 이름은 그대로).
2. 새 메인 영역에서도 기존 `[data-send]` 일괄 핸들러가 동작하도록, 추가 셀렉터 변경은 하지 않는다. (HTML에서 `data-send` 속성을 그대로 사용)
3. `activePipelineStates`와 `finalPipelineStates`가 8단계와 정합한지 확인하고, 누락된 상태는 추가하지 않는다(현재 코드가 이미 정합. 변경 불필요).
4. 임의 shell 명령 실행 API 호출이나 입력 핸들러를 새로 만들지 않는다.

### 4.4 `web/public/style.css` 변경

1. `.role-display`의 `grid-template-columns`를 `repeat(2, minmax(0, 1fr))`로 줄인다.
2. 보조 안내 문단용 작은 스타일을 추가한다:

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
   ```

3. 메인 액션 그리드용 스타일을 추가한다:

   ```css
   .primary-actions {
     display: grid;
     grid-template-columns: repeat(3, minmax(0, 1fr));
     gap: 10px;
     margin-top: 10px;
   }

   @media (max-width: 920px) {
     .primary-actions {
       grid-template-columns: 1fr;
     }
   }
   ```

4. 다른 색상/폰트/레이아웃 토큰은 변경하지 않는다.

### 4.5 `web/server.js` 변경

1. 다음 상수가 현재 정의와 일치하는지 확인만 한다(변경 없음 권장):
   - `SAFE_WINDOWS`는 `claude-plan`, `codex-implement`, `claude-review`, `claude`, `codex`만 허용.
   - `ALLOWED_TMUX_WINDOWS`는 `claude`, `codex`, `git-shell`만 포함.
   - `AI_TMUX_WINDOWS`는 `claude`, `codex`만 포함.
   - `ACTIVE_PIPELINE_STATES`는 `claude_planning`, `codex_implementing`, `claude_reviewing`, `approval_required`.
   - `FINAL_PIPELINE_STATES`는 `succeeded`, `failed`, `blocked`, `manual_review_required`, `idle`.
   - `ARTIFACT_PRIORITY`는 `request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, `review.md`, `status.md` 순.
2. 누락이 있을 때만 보정한다. 새 라우트(`commit`, `push`, `merge`, `deploy`, 임의 shell)는 추가하지 않는다.
3. 코드 변경이 없으면 이 파일은 수정하지 않은 채로 둔다.

### 4.6 `README.md` 변경

1. "팀 구성" 표 위쪽의 새 워크플로 단락은 유지한다.
2. "팀 구성" 표 본문은 **Claude / Codex 2행만** 노출하고, 그 아래에 별도 줄로 "Manual Shell(`git-shell`)은 사람이 직접 git/test 명령을 실행하는 보조 창이며 AI 역할이 아닙니다."를 1줄로 적는다.
3. "Deprecated: 이전 5역할 구성" 표는 `<details><summary>Deprecated: 이전 5역할 구성</summary> ... </details>` 블록 안으로 옮긴다.
4. "브라우저 GUI" 섹션 안의 불릿 목록을 다음 항목을 포함하도록 다시 정리한다(기존 줄을 무리하게 지우지 않고 의미가 겹치면 통합).
   - 프로젝트 경로, 작업 ID, 한국어 요청 입력
   - 메인 액션 버튼 4개: `Claude → Codex → Claude 전체 실행`, `Claude 계획 생성`, `Codex 구현 실행`, `Claude 리뷰 실행`
   - 파이프라인 상태 8단계 (`claude_planning`, `codex_implementing`, `claude_reviewing`, `manual_review_required`, `succeeded`, `failed`, `blocked`, `approval_required`)
   - 수동 유틸리티 버튼 2개: `git status`, `git diff`
   - 자동화하지 않는 항목: `commit`, `push`, PR 생성/머지, 배포
   - 임의 shell 명령 입력 기능 없음
   - 절대 건드리지 않는 항목: `.env`, secrets, auth, payment, production infra, database migrations
5. 디렉터리 구조 트리는 큰 변경 없으면 그대로 둔다.

### 4.7 `docs/ai/CLAUDE_CODEX_WORKFLOW.md` 변경

1. 문서 끝부분 또는 "Codex에게 요청하는 방법" 다음에 `## 브라우저 GUI` 섹션을 추가한다(이미 있으면 항목만 보강).
2. 섹션 본문에 다음 내용을 포함한다.
   - GUI 기본 주소: `http://127.0.0.1:3100` (외부 공개용 아님)
   - 메인 액션 버튼 4개와 각 버튼이 트리거하는 API:
     - `Claude → Codex → Claude 전체 실행` → `POST /api/pipeline/run`
     - `Claude 계획 생성` → `POST /api/send/claude-plan`
     - `Codex 구현 실행` → `POST /api/send/codex-implement`
     - `Claude 리뷰 실행` → `POST /api/send/claude-review`
   - 상태 단계 8개 목록(`claude_planning`, `codex_implementing`, `claude_reviewing`, `manual_review_required`, `succeeded`, `failed`, `blocked`, `approval_required`)
   - tmux 기본 대상은 `ai-team:claude`, `ai-team:codex` 두 창
   - `gemini-manager`, `claude-architect`, `claude-reviewer`, `git-shell`은 기본 자동화 대상이 아님. `git-shell`은 사람이 직접 git/test 명령을 실행하는 비AI 창.
   - 수동 유틸리티 버튼: `git status`, `git diff` (자동 commit/push/merge/deploy 없음)
   - 절대 자동화하지 않는 것: `commit`, `push`, PR merge, production 배포, `.env`/secrets/auth/payment/production infra/database migrations 변경
   - 임의 shell 명령 입력 기능은 GUI에서 제공하지 않음
3. 안전 규칙 섹션은 기존 그대로 유지한다.

### 4.8 `docs/ai/jobs/mvp-01/patch.md` 작성

Codex 출력 형식(`## 1. Files Changed` … `## 5. Remaining TODOs`)을 따른다. 다음 내용을 포함한다.

- Files Changed: 위 6개 파일 중 실제로 수정된 파일 목록
- Implementation Summary: 각 파일에서 한 일 요약
- Safety Confirmation: secrets/.env/auth/payment/migration/infra 미변경, `commit/push/merge/deploy` 자동화 없음, 임의 shell 입력 없음, tmux 대상 `claude`/`codex`만 사용 확인
- Test Results: 아래 검증 명령의 결과
  - `node --check web/server.js`
  - `node --check web/public/app.js`
  - `git diff --stat`
- Remaining TODOs: 없음. 있으면 명시.

### 4.9 검증 명령

작업 디렉터리(`/root/ai-dev-center/projects/ai-team`)에서 다음을 실행한다.

```bash
node --check web/server.js
node --check web/public/app.js
git diff --stat
```

세 명령 모두 결과를 `patch.md`의 Test Results에 그대로 인용한다. `node --check` 두 개는 종료코드 0이어야 한다. 실패하면 작업을 멈추고 원인 메시지를 `patch.md`에 남긴다.

## 5. 테스트 기준

1. `node --check web/server.js` 종료코드 0.
2. `node --check web/public/app.js` 종료코드 0.
3. `git diff --stat` 결과에 다음 외 파일이 포함되어 있지 않다.
   - `web/public/index.html`
   - `web/public/app.js`
   - `web/public/style.css`
   - `web/server.js` (변경된 경우)
   - `README.md`
   - `docs/ai/CLAUDE_CODEX_WORKFLOW.md`
   - `docs/ai/jobs/mvp-01/patch.md`
4. `web/public/index.html`에 다음 텍스트/속성이 모두 존재한다.
   - `Claude → Codex → Claude 전체 실행`
   - `Claude 계획 생성`, `Codex 구현 실행`, `Claude 리뷰 실행`
   - `data-send="claude-plan"`, `data-send="codex-implement"`, `data-send="claude-review"`
   - `id="gitStatus"`, `id="gitDiff"`
5. `web/public/index.html`에서 `Gemini Manager`, `Claude Architect`, `Claude Reviewer` 같은 옛 역할 라벨이 메인 UI 영역에 노출되지 않는다. (Deprecated 안내용 텍스트로만 등장하는 것은 허용)
6. `README.md`에 새 워크플로 표(Claude/Codex 2행)와 GUI 버튼 4개, 상태 8단계, 수동 유틸리티 2개 설명이 모두 존재한다.
7. `docs/ai/CLAUDE_CODEX_WORKFLOW.md`에 `브라우저 GUI` 안내, 메인 버튼 4개 + API 경로, 상태 8단계, tmux 대상 `claude`/`codex` 안내가 모두 존재한다.

## 6. 리뷰 체크리스트

- [ ] 메인 패널에 4개 액션 버튼(`전체 실행`, `Claude 계획 생성`, `Codex 구현 실행`, `Claude 리뷰 실행`)이 명시적으로 노출되어 있다.
- [ ] 고급 패널에서 동일한 `data-send` 버튼이 중복 노출되지 않는다(`AI 팀 시작`, `작업 폴더 생성`, `request.ko.md 저장`, `git status`, `git diff`만 남아 있다).
- [ ] `Manual Shell` / `git-shell`이 핵심 AI 역할 카드에서 빠져 있고, 보조 안내 문구로만 남아 있다.
- [ ] tmux 기본 대상(`AI_TMUX_WINDOWS`)이 `claude`, `codex`로만 구성되어 있고, `gemini-manager`, `claude-architect`, `claude-reviewer`, `git-shell`을 기본 대상으로 쓰는 코드 경로가 없다.
- [ ] 상태 단계가 8개(`claude_planning`, `codex_implementing`, `claude_reviewing`, `manual_review_required`, `succeeded`, `failed`, `blocked`, `approval_required`)와 일치한다.
- [ ] `git status`, `git diff`만 수동 유틸리티 버튼으로 남아 있고, `commit`, `push`, `merge`, `deploy` 자동화 버튼이나 라우트가 새로 추가되지 않았다.
- [ ] 임의 shell 명령 입력 UI/API가 신설되지 않았다.
- [ ] secrets, `.env`, auth, payment, production infra, database migration 관련 파일 변경이 없다.
- [ ] `README.md`와 `docs/ai/CLAUDE_CODEX_WORKFLOW.md`에 새 GUI 사용법이 반영되어 있다.
- [ ] `node --check web/server.js`와 `node --check web/public/app.js`가 모두 통과한다.
- [ ] `docs/ai/jobs/mvp-01/patch.md`에 변경 요약, 안전 확인, 테스트 결과, 남은 TODO가 모두 포함되어 있다.
