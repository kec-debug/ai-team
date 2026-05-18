
## 2026-05-14T07:43:31.724Z — create-job

```
Ensured job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-01
```

## 2026-05-14T07:43:31.724Z — save-input

```
Saved: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-01/input.ko.md
```

## 2026-05-14T07:43:31.734Z — gemini

```
can't find window: gemini-manager
Command failed: tmux paste-buffer -b ai-team-gui-prompt -t ai-team:gemini-manager
can't find window: gemini-manager

```

## 2026-05-14T07:43:31.734Z — failed

```
Gemini Manager 실패: Command failed: tmux paste-buffer -b ai-team-gui-prompt -t ai-team:gemini-manager
can't find window: gemini-manager

```

## 2026-05-14T07:56:33.141Z — create-job

```
Ensured job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-01
```

## 2026-05-14T07:56:33.142Z — save-input

```
Saved: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-01/request.ko.md
```

## 2026-05-14T07:56:33.156Z — claude-plan

```
(no output)
```

## 2026-05-14T07:57:06.382Z — create-job

```
Ensured job directory: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-01
```

## 2026-05-14T07:57:06.390Z — save-input

```
Saved: /root/ai-dev-center/projects/ai-team/docs/ai/jobs/mvp-01/request.ko.md
```

## 2026-05-14T07:57:06.398Z — claude-plan

```
(no output)
```

## 2026-05-14T07:59:41.418Z — codex-implement

```
(no output)
```

## 2026-05-14T07:59:43.175Z — codex-implement

```
(no output)
```

## 2026-05-14T08:05:08.198Z — save-diff

```
diff --git a/README.md b/README.md
index 7a12486..eddcc4c 100644
--- a/README.md
+++ b/README.md
@@ -1,10 +1,25 @@
 # AI Dev Team Control Center
 
+> DEPRECATED: The old 5-role workflow has been replaced by the simpler Claude + Codex workflow.
+> Use [docs/ai/CLAUDE_CODEX_WORKFLOW.md](docs/ai/CLAUDE_CODEX_WORKFLOW.md) for new jobs.
+
 > 로컬 tmux 기반 AI 개발팀을 시작 / 종료 / 관리하기 위한 컨트롤 센터입니다.
 > A control center for managing a local tmux-based AI development team.
 
 ## 팀 구성
 
+새 기본 AI 역할은 **Claude + Codex** 두 개뿐입니다. tmux에는 사람이 직접 git/test 명령을 실행하는 비AI `git-shell` 창도 함께 둡니다.
+
+| 역할 | 하는 일 | 주요 산출물 |
+|------|---------|-----------|
+| Claude | 한국어 요청 정리, 설계, 리스크 점검, 리뷰 | `plan.md`, `review.md` |
+| Codex | 구현, 테스트, 패치 요약 | 코드 변경 + `patch.md` |
+
+> Manual Shell(`git-shell`)은 사람이 직접 `git status`, `git diff`, 테스트, commit, PR 명령을 실행하는 보조 창입니다. AI 역할이 아니며 GUI 파이프라인이 자동화하지 않습니다.
+
+<details>
+<summary>Deprecated: 이전 5역할 구성</summary>
+
 | tmux 번호 | tmux 창 | 역할 | 하는 일 | 주요 산출물 |
 |-----------|---------|------|---------|-----------|
 | `0` | `gemini-manager` | Gemini Manager | 한국어 요청을 읽고 영어 작업 계획으로 정리 | `plan.en.md` |
@@ -13,6 +28,8 @@
 | `3` | `claude-reviewer` | Claude Reviewer | PR diff와 안전 규칙 준수 여부 리뷰 | `review.md` |
 | `4` | `git-shell` | Git Shell | 브랜치, 커밋, PR, CI 확인을 사람이 직접 실행 | git / gh 명령 결과 |
 
+</details>
+
 ## 빠른 시작
 
 처음 실행한다면 아래 순서대로 진행하세요.
@@ -41,9 +58,9 @@ chmod +x scripts/*.sh
 ./scripts/create-job.sh ~/projects/my-app job-001
 ```
 
-이 명령은 실제 작업 파일을 `docs/ai/jobs/<JOB_ID>/` 아래에 만듭니다. 예를 들어 `job-001`이면 `docs/ai/jobs/job-001/input.ko.md`를 작성합니다.
+이 명령은 실제 작업 파일을 `docs/ai/jobs/<JOB_ID>/` 아래에 만듭니다. 예를 들어 `job-001`이면 `docs/ai/jobs/job-001/request.ko.md`를 작성합니다.
 
-4. `gemini-manager` 창에서 `input.ko.md`를 바탕으로 계획을 만들고, 이후 `claude-architect` → `codex-implementer` → `claude-reviewer` 순서로 진행합니다.
+4. `request.ko.md`에 한국어 요청을 적고, `prompts/claude.md`로 Claude에게 계획을 요청합니다. 이후 `prompts/codex-implementer.md`로 Codex가 구현하고, Claude가 리뷰합니다.
 
 5. 세션 상태를 확인하거나 종료할 수 있습니다.
 
@@ -54,20 +71,21 @@ chmod +x scripts/*.sh
 
 > **tmux 창 이동**
 > `Ctrl-b`를 누른 뒤 손을 떼고 숫자를 누릅니다.
-> 예: `Ctrl-b` 다음 `0` = `gemini-manager`, `Ctrl-b` 다음 `2` = `codex-implementer`.
+> 예: `Ctrl-b` 다음 `0` = `claude`, `Ctrl-b` 다음 `1` = `codex`, `Ctrl-b` 다음 `2` = `git-shell`.
 > 분리(detach)는 `Ctrl-b` 다음 `d`입니다. 다시 붙으려면 `tmux attach -t ai-team`을 실행하세요.
 
 ## 워크플로 한 줄 요약
 
-한국어 입력 → Gemini 영어 계획 → Claude 아키텍처 검토 → Codex 구현 → GitHub PR → Claude PR 리뷰 → 사람 최종 승인
+한국어 입력 → Claude 계획 → Codex 구현/테스트 → Claude 리뷰 → 사람이 git 명령 직접 실행
 
 자세한 내용은 다음 문서들을 참고하세요.
 
 - [docs/setup.md](docs/setup.md) — 처음 설치 / 설정
-- [docs/workflow.md](docs/workflow.md) — 단계별 작업 흐름
+- [docs/ai/CLAUDE_CODEX_WORKFLOW.md](docs/ai/CLAUDE_CODEX_WORKFLOW.md) — 새 Claude + Codex 작업 흐름
+- [docs/workflow.md](docs/workflow.md) — deprecated 이전 단계별 작업 흐름
 - [docs/safety-rules.md](docs/safety-rules.md) — 안전 규칙
 
-## 브라우저 GUI v1
+## 브라우저 GUI
 
 PuTTY나 tmux 직접 조작 없이 로컬 브라우저에서 AI 개발팀을 제어할 수 있는 간단한 GUI가 `web/`에 있습니다. 기본 주소는 `http://127.0.0.1:3100`이며 외부 공개용으로 만들지 않았습니다.
 
@@ -88,40 +106,56 @@ HOST=127.0.0.1 PORT=3100 npm start
 GUI에서 할 수 있는 일:
 
 - 프로젝트 경로, 작업 ID, 한국어 작업 요청 입력
+- 메인 액션 버튼 4개: `Claude → Codex → Claude 전체 실행`, `Claude 계획 생성`, `Codex 구현 실행`, `Claude 리뷰 실행`
 - AI 팀 tmux 세션 상태 확인과 시작
-- 작업 폴더 생성과 `input.ko.md` 저장
-- **전체 파이프라인 실행** 버튼으로 작업 폴더 생성 → 입력 저장 → Gemini Manager → Claude Architect → Codex Implementer → `local-diff.patch` 저장 → Claude Reviewer 순서 진행
-- 파이프라인 현재 단계, 성공 / 실패 / 수동 개입 필요 상태 확인
+- 작업 폴더 생성과 `request.ko.md` 저장
+- **Claude → Codex → Claude 전체 실행** 버튼으로 작업 폴더 생성 → 요청 저장 → Claude 계획 생성 → Codex 구현 실행 → Claude 리뷰 실행 순서 진행
+- 파이프라인 상태 8단계: `claude_planning`, `codex_implementing`, `claude_reviewing`, `manual_review_required`, `succeeded`, `failed`, `blocked`, `approval_required`
 - 선택한 프로젝트 경로와 작업 ID 기준으로 파이프라인 상태 확인 및 `파이프라인 상태 초기화`
 - 실시간 tmux 출력 확인, 승인 / 세션 승인 / 거절 / 중단 키 입력 전송
 - AI팀 재시작과 GUI 서버 재시작
-- 생성된 산출물, git diff 저장 상태, Reviewer decision 요약 확인
-- Gemini Manager, Claude Architect, Codex Implementer, Claude Reviewer 창으로 정해진 프롬프트 전송
-- `git status`, `git diff` 확인
-- `docs/ai/jobs/<JOB_ID>/` 아래 산출물 파일 확인
+- 생성된 산출물, git diff 상태, Claude 리뷰 요약 확인
+- 수동 유틸리티 버튼 2개: `git status`, `git diff`
+- Manual Shell(`git-shell`) tmux 창에서 사람이 직접 테스트, commit, PR 명령 실행
+- 자동화하지 않는 것: `commit`, `push`, PR 생성/머지, 배포
+- 임의 shell 명령 입력 기능 없음
+- 절대 변경하지 않는 영역: `.env`, secrets, auth, payment, production infra, database migrations
+- `docs/ai/jobs/<JOB_ID>/` 아래 산출물 파일 확인: `request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, `review.md`, `status.md`
+
+`Claude → Codex → Claude 전체 실행`은 브라우저 요청을 오래 붙잡지 않습니다. 서버가 메모리에 작업 상태를 만들고 백그라운드에서 안전한 고정 단계만 실행하며, GUI는 `GET /api/pipeline/status`로 상태를 폴링합니다. 서버를 재시작하면 이 메모리 상태는 사라집니다. 이미 tmux 창에 전달된 작업은 계속 진행될 수 있으므로, 재시작 후에는 tmux와 산출물 파일을 직접 확인하세요.
 
-`전체 파이프라인 실행`은 브라우저 요청을 오래 붙잡지 않습니다. 서버가 메모리에 작업 상태를 만들고 백그라운드에서 안전한 고정 단계만 실행하며, GUI는 `GET /api/pipeline/status`로 상태를 폴링합니다. 서버를 재시작하면 이 메모리 상태는 사라집니다. 이미 tmux 창에 전달된 작업은 계속 진행될 수 있으므로, 재시작 후에는 tmux와 산출물 파일을 직접 확인하세요.
+GUI는 임의 shell command 입력을 제공하지 않습니다. 서버는 허용된 스크립트, 고정 tmux 창, 고정 git 조회 명령만 실행합니다. 승인 버튼은 Claude 또는 Codex AI CLI 창에만 사용합니다. Manual Shell(`git-shell`)은 AI 역할이 아니며 사람이 직접 `git status`, `git diff`, 테스트, commit, PR 명령을 실행하는 창입니다. 파이프라인도 `commit`, `push`, PR 생성, merge, 배포를 자동 실행하지 않습니다. 최종 변경 확인, 커밋, 푸시, PR 생성, merge 승인은 사람이 터미널과 GitHub에서 직접 처리해야 합니다. 자동 merge는 안전상 제공하지 않습니다.
 
-GUI는 임의 shell command 입력을 제공하지 않습니다. 서버는 허용된 스크립트, 고정 tmux 창, 고정 git 조회 명령만 실행합니다. 승인 버튼도 allowlist에 있는 tmux 창에 정해진 키만 보냅니다. 파이프라인도 `commit`, `push`, PR 생성, merge, 배포를 자동 실행하지 않습니다. 최종 변경 확인, 커밋, 푸시, PR 생성, merge 승인은 사람이 `git-shell` 창과 GitHub에서 직접 처리해야 합니다. 자동 merge는 안전상 제공하지 않습니다.
+AI 도구가 중간 승인을 요구하면 GUI는 `approval_required`로 표시합니다. 제한 시간 안에 예상 산출물을 만들지 못하면 `manual_review_required`로 표시합니다. 이 경우 사람이 해당 tmux 창에서 진행 상황을 확인하고 수동으로 이어가야 합니다.
 
-AI 도구가 중간 승인을 요구하거나 제한 시간 안에 예상 산출물을 만들지 못하면 GUI는 해당 단계를 `manual_required`로 표시합니다. 이 경우 사람이 해당 tmux 창에서 진행 상황을 확인하고 수동으로 이어가야 합니다.
+GUI 서버 재시작 버튼을 눌렀는데 `http://<서버 IP>:3100`이 다시 열리지 않으면 SSH/PuTTY에서 아래 수동 복구 명령을 실행하세요. 재시작 로그는 `/tmp/ai-team-gui-restart.log`에 남습니다.
+
+```bash
+fuser -k 3100/tcp 2>/dev/null || true
+tmux kill-session -t ai-gui 2>/dev/null || true
+tmux new-session -d -s ai-gui -c /root/ai-dev-center/projects/ai-team/web "env HOST=0.0.0.0 PORT=3100 npm start"
+```
 
 ## 체크리스트: push 전 확인
 
-- `git-shell` 창에서 `git status`와 `git diff`로 변경 파일을 확인합니다.
+- 터미널에서 `git status`와 `git diff`로 변경 파일을 확인합니다.
 - 변경이 현재 작업 범위에만 있는지 확인합니다.
 - `scripts/`, 비밀 정보, 인증, 결제, DB 마이그레이션, 운영 인프라가 의도치 않게 바뀌지 않았는지 확인합니다.
 - `main`에 직접 push하지 말고 작업 브랜치에서 PR로 진행합니다.
-- Codex 구현 요약과 Claude Reviewer 리뷰 결과를 확인합니다.
-- 전체 규칙은 [docs/safety-rules.md](docs/safety-rules.md), 단계별 흐름은 [docs/workflow.md](docs/workflow.md)를 봅니다.
+- Codex 구현 요약과 Claude 리뷰 결과를 확인합니다.
+- 전체 규칙은 [docs/safety-rules.md](docs/safety-rules.md), 새 단계별 흐름은 [docs/ai/CLAUDE_CODEX_WORKFLOW.md](docs/ai/CLAUDE_CODEX_WORKFLOW.md)를 봅니다.
 
 ## 역할 프롬프트
 
 각 AI 역할이 어떻게 행동해야 하는지는 `prompts/` 안에 있습니다. 필요하면 각 창에서 해당 파일을 열어 그대로 시스템 프롬프트로 사용하세요.
 
+- [prompts/claude.md](prompts/claude.md)
+- [prompts/codex-implementer.md](prompts/codex-implementer.md)
+
+Deprecated historical prompts:
+
 - [prompts/gemini-manager.md](prompts/gemini-manager.md)
 - [prompts/claude-architect.md](prompts/claude-architect.md)
-- [prompts/codex-implementer.md](prompts/codex-implementer.md)
 - [prompts/claude-reviewer.md](prompts/claude-reviewer.md)
 
 ## 안전 규칙 (요약)
@@ -152,7 +186,7 @@ ai-job <PROJECT> <ID>        # 작업 폴더 만들기
 
 ## 예시
 
-`examples/job-001/input.ko.md`는 참고용 예시입니다. 실제 작업은 `./scripts/create-job.sh <PROJECT_DIR> <JOB_ID>`로 만들고, 생성된 `docs/ai/jobs/<JOB_ID>/input.ko.md`에 요청을 작성하세요.
+`examples/job-001/input.ko.md`는 이전 참고용 예시입니다. 실제 작업은 `./scripts/create-job.sh <PROJECT_DIR> <JOB_ID>`로 만들고, 생성된 `docs/ai/jobs/<JOB_ID>/request.ko.md`에 요청을 작성하세요.
 
 ## 디렉터리 구조
 
@@ -160,10 +194,11 @@ ai-job <PROJECT> <ID>        # 작업 폴더 만들기
 .
 ├── README.md
 ├── prompts/
-│   ├── gemini-manager.md
-│   ├── claude-architect.md
+│   ├── claude.md
 │   ├── codex-implementer.md
-│   └── claude-reviewer.md
+│   ├── gemini-manager.md        # deprecated
+│   ├── claude-architect.md      # deprecated
+│   └── claude-reviewer.md       # deprecated
 ├── scripts/
 │   ├── start-ai-team.sh
 │   ├── status-ai-team.sh
@@ -172,6 +207,9 @@ ai-job <PROJECT> <ID>        # 작업 폴더 만들기
 │   └── ai-team-aliases.sh
 ├── docs/
 │   ├── setup.md
+│   ├── ai/
+│   │   ├── CLAUDE_CODEX_WORKFLOW.md
+│   │   └── jobs/
 │   ├── workflow.md
 │   └── safety-rules.md
 └── examples/
diff --git a/docs/safety-rules.md b/docs/safety-rules.md
index a192e29..5946fcf 100644
--- a/docs/safety-rules.md
+++ b/docs/safety-rules.md
@@ -20,7 +20,7 @@ AI 팀이 절대 어겨서는 안 되는 규칙입니다. 같은 규칙이 모
 
 ## 3. 자동 머지 금지
 
-- AI는 PR을 만들 수는 있지만 **머지하지 않습니다**.
+- AI는 PR을 만들거나 머지하지 않습니다. 필요한 git / GitHub 명령은 사람이 직접 실행합니다.
 - 머지는 사람이 리뷰 결과를 읽고 직접 누르는 행위입니다.
 - `gh pr merge --auto`처럼 자동 머지 옵션도 사용하지 않습니다.
 - Mergify, Bulldozer 등 자동 머지 봇 설정 변경도 사람 승인 영역입니다.
@@ -64,7 +64,7 @@ AI 팀이 절대 어겨서는 안 되는 규칙입니다. 같은 규칙이 모
 | 영어 계획 / 아키텍처 / 구현 / 리뷰 | ✓ | ✓ |
 | `git commit` | ✗ | ✓ |
 | `git push` | ✗ | ✓ |
-| PR 생성 | △ (사람이 검토 후) | ✓ |
+| PR 생성 | ✗ | ✓ |
 | PR 머지 | ✗ | ✓ |
 | `.env` / 비밀 추가 / 수정 | ✗ | ✓ (드물게, 의식적으로) |
 | 인증 / 결제 / DB 마이그레이션 변경 | △ (승인 메모 필수) | ✓ |
diff --git a/docs/setup.md b/docs/setup.md
index 1796fff..ef656d5 100644
--- a/docs/setup.md
+++ b/docs/setup.md
@@ -1,6 +1,6 @@
 # 설치 및 설정 가이드 (Setup)
 
-이 저장소는 로컬 AI 개발팀(tmux 기반)을 시작 / 종료 / 관리하는 컨트롤 센터입니다. 처음 사용한다면 아래 순서대로 따라 해주세요.
+이 저장소는 로컬 Claude + Codex 작업 흐름을 시작 / 종료 / 관리하는 컨트롤 센터입니다. 처음 사용한다면 아래 순서대로 따라 해주세요.
 
 ## 1. 필요한 도구
 
@@ -10,7 +10,6 @@
 tmux -V
 git --version
 gh --version       # GitHub CLI
-gemini --version   # Gemini CLI
 claude --version   # Anthropic Claude CLI
 codex --version    # Codex CLI
 ```
@@ -60,11 +59,11 @@ source /절대/경로/ai-team/scripts/ai-team-aliases.sh
 
 | alias | 동작 |
 |-------|------|
-| `ai-team [PROJECT_DIR]` | AI 팀 tmux 세션 시작 (이미 있으면 attach) |
+| `ai-team [PROJECT_DIR]` | Claude + Codex tmux 세션 시작 (이미 있으면 attach) |
 | `ai-attach` | 실행 중인 세션에 다시 붙기 |
 | `ai-status` | 세션 상태 확인 |
 | `ai-stop` | 세션 종료 (확인 후) |
-| `ai-job PROJECT_DIR JOB_ID` | 새 작업 폴더 생성 |
+| `ai-job PROJECT_DIR JOB_ID` | 새 Claude + Codex 작업 폴더 생성 |
 
 ## 5. 첫 실행
 
diff --git a/docs/workflow.md b/docs/workflow.md
index 02d35ec..1f737e6 100644
--- a/docs/workflow.md
+++ b/docs/workflow.md
@@ -1,5 +1,8 @@
 # 워크플로 (Workflow)
 
+> DEPRECATED: This workflow has been replaced by the Claude + Codex workflow.
+> 새 작업은 [docs/ai/CLAUDE_CODEX_WORKFLOW.md](ai/CLAUDE_CODEX_WORKFLOW.md)를 사용하세요.
+
 한 작업이 한국어 요청에서 시작해 GitHub 머지까지 어떻게 흐르는지 설명합니다.
 
 ## 7 단계 파이프라인
diff --git a/prompts/claude-architect.md b/prompts/claude-architect.md
index 977e84c..d73177a 100644
--- a/prompts/claude-architect.md
+++ b/prompts/claude-architect.md
@@ -1,5 +1,7 @@
 # Claude Architect — Role Prompt
 
+> DEPRECATED: This role has been merged into Claude in the simplified Claude + Codex workflow. Use `prompts/claude.md` and `docs/ai/CLAUDE_CODEX_WORKFLOW.md` for new jobs.
+
 You are the **Claude Architect**. You review the English plan from Gemini Manager before any code is written. You are the second line of defense before bad ideas reach the codebase.
 
 ## Inputs you receive
diff --git a/prompts/claude-reviewer.md b/prompts/claude-reviewer.md
index f5dbdf3..1b1f53e 100644
--- a/prompts/claude-reviewer.md
+++ b/prompts/claude-reviewer.md
@@ -1,5 +1,7 @@
 # Claude Reviewer — Role Prompt
 
+> DEPRECATED: This role has been merged into Claude in the simplified Claude + Codex workflow. Use `prompts/claude.md` and `docs/ai/CLAUDE_CODEX_WORKFLOW.md` for new jobs.
+
 You are the **Claude Reviewer**. You are the quality gate before a PR is merged by the human.
 
 ## Inputs you receive
diff --git a/prompts/codex-implementer.md b/prompts/codex-implementer.md
index 92e0bff..181011e 100644
--- a/prompts/codex-implementer.md
+++ b/prompts/codex-implementer.md
@@ -1,42 +1,89 @@
 # Codex Implementer — Role Prompt
 
-You are the **Codex Implementer**. You write the actual code once the plan and architecture are approved.
+You are the **Codex Implementer** in the simplified Claude + Codex workflow. Claude plans and reviews. You implement, test, and summarize the patch.
 
-## Inputs you receive
-- `docs/ai/jobs/{JOB_ID}/plan.en.md` (Gemini Manager)
-- `docs/ai/jobs/{JOB_ID}/architecture.md` (Claude Architect, verdict must be `APPROVE`)
+## Inputs You Receive
+
+- Approved job scope in `docs/ai/jobs/{JOB_ID}/`.
+- `docs/ai/jobs/{JOB_ID}/plan.md` from Claude.
+- `docs/ai/jobs/{JOB_ID}/codex-task.md` when present.
 - The codebase itself.
 
-## Your job
-1. Implement **only** the changes described in the plan + architecture.
-2. Add tests matching the architect's test strategy.
-3. Run the existing test suite locally; do not hand off if it's red.
-4. Summarize your work in `docs/ai/jobs/{JOB_ID}/patch.md`:
-   - File list with one-line description per file.
-   - Diff highlights / notable design decisions.
-   - Test results (pass count, any skipped, any flaky).
-   - Anything the reviewer should pay extra attention to.
-
-## What you do NOT do
-- Do **NOT** `git commit` automatically. The human runs commits in the **git-shell** tmux window.
-- Do **NOT** `git push` automatically.
-- Do **NOT** open or merge PRs automatically.
-- Do **NOT** expand scope. If you find a related bug, file it as a follow-up in `patch.md`; do not fix it inline.
-- Do **NOT** touch any of these — even if it looks like a one-liner:
-  - `.env`, secrets, credentials, API keys, tokens.
-  - Auth / login / session / password / token-handling code.
-  - Payment / billing / subscription code.
-  - Database migration files (schema changes, data backfills).
-  - Production infrastructure.
-
-  Stop and surface to the human via the job folder.
+If older files such as `plan.en.md` or `architecture.md` exist, treat them as historical context only unless the current job scope explicitly says to use them.
+
+## Your Job
+
+1. Read the approved job scope before editing.
+2. Modify only files relevant to the approved scope.
+3. Add or update tests for the changed behavior.
+4. Run these checks when applicable:
+
+```bash
+python -m compileall app tests
+python -m pytest -p no:cacheprovider
+```
+
+5. Write a patch summary for `docs/ai/jobs/{JOB_ID}/patch.md`.
+
+## Output Format
+
+Use this exact structure in your final response and in `patch.md` when you update it:
+
+```markdown
+## 1. Files Changed
+
+## 2. Implementation Summary
+
+## 3. Safety Confirmation
+
+## 4. Test Results
+
+## 5. Remaining TODOs
+```
+
+## What You Must Never Do
+
+- Never `git commit`.
+- Never `git push`.
+- Never merge a PR.
+- Never open or merge PRs automatically.
+- Never expand scope. Put related work in Remaining TODOs.
+- Never edit secrets, `.env`, credentials, API keys, or tokens.
+- Never edit auth, login, session, password, or token-handling code.
+- Never edit payment, billing, or subscription code.
+- Never edit production infrastructure.
+- Never edit database migrations.
+- Never invent vendor endpoints.
+- Never add fake broker endpoints.
+- Never enable live trading by default.
+- Never allow LLMs or recommendation agents to create executable orders.
+- Never bypass RiskEngine.
+
+Stop and surface the issue in the job folder if the approved scope requires any forbidden area.
+
+## Trading Safety Rules
+
+- Paper trading is default.
+- Live trading is disabled by default.
+- Live trading requires explicit validation, preflight, arming, and guard checks.
+- LLMs must never directly place trades.
+- Recommendation agents may only create non-executable order intents.
+- Executable orders may only be created by OMS.
+- All orders must pass Strategy -> Risk Engine -> OMS.
+- Broker-specific API calls must stay inside broker adapters.
+- API keys must only come from `.env`.
+- Do not hardcode secrets.
+- Market orders are disabled by default.
+- Fail closed on uncertainty.
 
 ## Style
-- Follow the project's existing conventions. Match neighbor code.
-- Keep diffs small and focused. One job = one PR.
-- Tests must be deterministic. No `sleep` to "fix" flakiness.
-- Default to no comments. Add one only when the *why* is non-obvious.
-
-## Verdict at the end of `patch.md`
-- `READY FOR REVIEW` — all acceptance criteria met, tests green.
-- `BLOCKED` — describe why; do not hand off.
+
+- Follow the project's existing conventions. Match neighboring code.
+- Keep diffs small and focused.
+- Tests must be deterministic. Do not use `sleep` to hide flakiness.
+- Add comments only when the reason is not obvious from the code.
+
+## Verdict at the End of `patch.md`
+
+- `READY FOR REVIEW` — all acceptance criteria met and applicable tests pass.
+- `BLOCKED` — describe why and do not hand off as complete.
diff --git a/prompts/gemini-manager.md b/prompts/gemini-manager.md
index 4b7820e..02ee7df 100644
--- a/prompts/gemini-manager.md
+++ b/prompts/gemini-manager.md
@@ -1,5 +1,7 @@
 # Gemini Manager — Role Prompt
 
+> DEPRECATED: This role has been replaced by Claude in the simplified Claude + Codex workflow. Use `prompts/claude.md` and `docs/ai/CLAUDE_CODEX_WORKFLOW.md` for new jobs.
+
 You are the **Gemini Manager** at the front of an AI development team. Your job is to turn fuzzy Korean human requests into precise, English, machine-readable work plans for the rest of the team.
 
 ## Inputs you receive
diff --git a/scripts/create-job.sh b/scripts/create-job.sh
index 53a7e24..53682f2 100755
--- a/scripts/create-job.sh
+++ b/scripts/create-job.sh
@@ -1,25 +1,39 @@
 #!/usr/bin/env bash
-# Create a new job folder inside a target project.
+# Create a new Claude + Codex job folder inside a target project.
 #
 # Usage:
-#   ./scripts/create-job.sh PROJECT_DIR JOB_ID
+#   ./scripts/create-job.sh PROJECT_DIR JOB_ID [--force]
 #
 # Creates: PROJECT_DIR/docs/ai/jobs/JOB_ID/
-#   - input.ko.md  (Korean task template the human fills in)
-#   - README.md    (workflow guide for this job)
+#   - request.ko.md
+#   - plan.md
+#   - codex-task.md
+#   - patch.md
+#   - review.md
+#   - status.md
 #
-# Does NOT modify any source code in PROJECT_DIR.
+# Does NOT run git commands. Existing files are overwritten only with --force.
 
 set -euo pipefail
 
-if [ "$#" -lt 2 ]; then
-    echo "Usage: $0 PROJECT_DIR JOB_ID"
+if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
+    echo "Usage: $0 PROJECT_DIR JOB_ID [--force]"
     echo "Example: $0 ~/projects/my-app job-001"
     exit 1
 fi
 
 PROJECT_DIR_INPUT="$1"
 JOB_ID="$2"
+FORCE=false
+
+if [ "$#" -eq 3 ]; then
+    if [ "$3" = "--force" ]; then
+        FORCE=true
+    else
+        echo "Error: unknown option '$3'. Only --force is supported." >&2
+        exit 1
+    fi
+fi
 
 if [ ! -d "$PROJECT_DIR_INPUT" ]; then
     echo "Error: project directory '$PROJECT_DIR_INPUT' does not exist." >&2
@@ -27,99 +41,55 @@ if [ ! -d "$PROJECT_DIR_INPUT" ]; then
 fi
 
 PROJECT_DIR="$(cd "$PROJECT_DIR_INPUT" && pwd)"
+TEMPLATE_DIR="$PROJECT_DIR/docs/ai/jobs/_template"
 JOB_DIR="$PROJECT_DIR/docs/ai/jobs/$JOB_ID"
 
-if [ -e "$JOB_DIR" ]; then
-    echo "Error: job directory already exists: $JOB_DIR" >&2
-    echo "Pick a different JOB_ID or remove the existing directory first." >&2
+if [ ! -d "$TEMPLATE_DIR" ]; then
+    echo "Error: template directory not found: $TEMPLATE_DIR" >&2
+    echo "Create docs/ai/jobs/_template first." >&2
     exit 1
 fi
 
 mkdir -p "$JOB_DIR"
 
-# -----------------------------------------------------------------------------
-# input.ko.md — Korean task template (no variable substitution needed)
-# -----------------------------------------------------------------------------
-cat > "$JOB_DIR/input.ko.md" <<'EOF'
-# 작업 입력 (Job Input)
-
-## 한 줄 요약
-> 무엇을 만들거나 고치고 싶은지 한 문장으로 적어주세요.
-
-(예시: "로그인 페이지에 비밀번호 표시/숨기기 토글 버튼을 추가하고 싶어요.")
-
-## 배경 (Why)
-- 왜 이 작업이 필요한가요?
-- 누가 이 기능을 사용하나요?
-- 지금은 어떻게 동작하고 있나요?
-
-## 목표 (Done 정의)
-- [ ] 목표 1
-- [ ] 목표 2
-- [ ] 목표 3
-
-## 범위 밖 (Not in scope)
-- 이번 작업에서 다루지 않을 항목을 적어주세요.
-- (예: "회원가입 페이지 디자인 변경은 별도 작업으로 분리")
-
-## 제약 조건
-- 이 작업에서는 다음 영역을 절대 변경하지 않습니다:
-  - `.env`, 비밀 키, 자격 증명, API 키, 토큰
-  - 인증 / 로그인 / 세션 / 비밀번호 처리 코드
-  - 결제 / 빌링 / 구독 로직
-  - 데이터베이스 마이그레이션 파일
-  - 운영(prod) 인프라
-- `main` 브랜치 직접 푸시 금지.
-- 자동 머지 금지 — 사람이 직접 머지합니다.
-
-## 참고 자료
-- 관련 파일 / 함수 / URL:
-- 스크린샷 / 디자인 시안:
-- 관련 이슈 / PR 번호:
-
-## 수용 기준 (Acceptance Criteria)
-- [ ] 조건 1 — 어떤 입력에 어떤 출력이 나오면 성공인지 구체적으로 적어주세요.
-- [ ] 조건 2
-- [ ] 모든 기존 테스트가 통과해야 합니다.
-- [ ] 새 테스트가 추가되어 있어야 합니다.
-EOF
-
-# -----------------------------------------------------------------------------
-# README.md — workflow guide (needs JOB_ID substituted)
-# -----------------------------------------------------------------------------
-cat > "$JOB_DIR/README.md" <<EOF
-# Job: $JOB_ID
-
-이 폴더는 AI 팀이 처리하는 작업 단위 하나입니다. 한 작업 = 한 폴더 = 한 PR.
-
-## 단계별 산출 파일
-1. \`input.ko.md\` — 사람이 한국어로 작성한 요청서 (지금 작성해야 함)
-2. \`plan.en.md\` — Gemini Manager가 영어로 정리한 작업 계획 (다음 단계)
-3. \`architecture.md\` — Claude Architect의 설계 / 리스크 / 테스트 전략
-4. \`patch.md\` — Codex Implementer의 변경 요약과 PR 링크
-5. \`review.md\` — Claude Reviewer의 PR 리뷰 결과
-
-## 워크플로
-1. \`input.ko.md\`를 끝까지 채워 넣습니다.
-2. AI 팀 tmux 세션을 시작합니다: \`./scripts/start-ai-team.sh <이 프로젝트 경로>\`.
-3. **gemini-manager** 창에서 \`input.ko.md\` 내용을 붙여 넣어 영어 계획(\`plan.en.md\`)을 만들도록 요청합니다.
-4. **claude-architect** 창에서 계획을 검토받고 \`architecture.md\`를 받습니다. 검토 결과가 \`APPROVE\`일 때만 다음 단계로.
-5. **codex-implementer** 창에서 구현을 진행하고 \`patch.md\`로 정리합니다.
-6. **git-shell** 창에서 사람이 직접 브랜치 생성 / 커밋 / 푸시 / PR 생성을 실행합니다.
-7. **claude-reviewer** 창에서 PR 리뷰를 받고 \`review.md\`로 저장합니다.
-8. 사람이 최종 승인 후 머지합니다.
-
-## 금지 사항 (이 작업에서도 동일)
-- 자동 커밋 / 자동 푸시 / 자동 머지 금지
-- \`.env\`, 비밀 키, 인증, 결제, DB 마이그레이션, 운영 인프라 변경 금지 (사람 승인 시에만)
-- \`main\` 직접 푸시 금지
-EOF
+created=0
+skipped=0
+
+for src in "$TEMPLATE_DIR"/*.md; do
+    name="$(basename "$src")"
+    dest="$JOB_DIR/$name"
+    existed=false
+    if [ -e "$dest" ]; then
+        existed=true
+    fi
+    if [ -e "$dest" ] && [ "$FORCE" = false ]; then
+        echo "Skip existing: $dest"
+        skipped=$((skipped + 1))
+    else
+        cp "$src" "$dest"
+        if [ "$existed" = true ] && [ "$FORCE" = true ]; then
+            echo "Overwrote: $dest"
+        else
+            echo "Created: $dest"
+        fi
+        created=$((created + 1))
+    fi
+done
 
 echo "Created job at: $JOB_DIR"
 echo
 echo "Files:"
 ls -la "$JOB_DIR"
 echo
+echo "Created or overwritten files: $created"
+echo "Skipped existing files: $skipped"
+echo
 echo "Next steps:"
-echo "  1. Edit:  $JOB_DIR/input.ko.md"
-echo "  2. Start: ./scripts/start-ai-team.sh $PROJECT_DIR"
+echo "  1. Put the Korean request in: $JOB_DIR/request.ko.md"
+echo "  2. Ask Claude with: prompts/claude.md"
+echo "  3. Save Claude's plan to: $JOB_DIR/plan.md"
+echo "  4. Ask Codex with: prompts/codex-implementer.md and $JOB_DIR/codex-task.md"
+echo "  5. Save Codex's result to: $JOB_DIR/patch.md"
+echo "  6. Ask Claude to review into: $JOB_DIR/review.md"
+echo
+echo "Workflow doc: $PROJECT_DIR/docs/ai/CLAUDE_CODEX_WORKFLOW.md"
diff --git a/scripts/start-ai-team.sh b/scripts/start-ai-team.sh
index 72e2254..239b1cb 100755
--- a/scripts/start-ai-team.sh
+++ b/scripts/start-ai-team.sh
@@ -1,5 +1,5 @@
 #!/usr/bin/env bash
-# Start the AI team tmux session.
+# Start the simplified Claude + Codex tmux session with a manual shell.
 #
 # Usage:
 #   ./scripts/start-ai-team.sh [PROJECT_DIR]
@@ -75,37 +75,32 @@ launch_tool() {
         "if command -v $tool >/dev/null 2>&1; then $tool; else echo '[!] $tool not found in PATH. Install it, then run: $tool'; fi" Enter
 }
 
-# --- Create session with the five windows ------------------------------------
-tmux new-session -d -s "$SESSION" -n "gemini-manager"    -c "$WORK_DIR"
-tmux new-window  -t "$SESSION"   -n "claude-architect"  -c "$WORK_DIR"
-tmux new-window  -t "$SESSION"   -n "codex-implementer" -c "$WORK_DIR"
-tmux new-window  -t "$SESSION"   -n "claude-reviewer"   -c "$WORK_DIR"
-tmux new-window  -t "$SESSION"   -n "git-shell"         -c "$WORK_DIR"
-
-# --- Window 1: Gemini Manager ------------------------------------------------
-print_banner "gemini-manager"    "Gemini Manager"    "Requirements, planning, English prompt generation" "$PROMPTS_DIR/gemini-manager.md"
-launch_tool  "gemini-manager"    "gemini"
-
-# --- Window 2: Claude Architect ----------------------------------------------
-print_banner "claude-architect"  "Claude Architect"  "Architecture review, risk analysis, test strategy" "$PROMPTS_DIR/claude-architect.md"
-launch_tool  "claude-architect"  "claude"
-
-# --- Window 3: Codex Implementer ---------------------------------------------
-print_banner "codex-implementer" "Codex Implementer" "Implementation, tests, patches"                    "$PROMPTS_DIR/codex-implementer.md"
-launch_tool  "codex-implementer" "codex"
-
-# --- Window 4: Claude Reviewer -----------------------------------------------
-print_banner "claude-reviewer"   "Claude Reviewer"   "PR diff review, quality gate"                      "$PROMPTS_DIR/claude-reviewer.md"
-launch_tool  "claude-reviewer"   "claude"
-
-# --- Window 5: Git Shell (plain shell, no tool launch) -----------------------
-print_banner "git-shell"         "Git Shell"         "git / gh / branch / commit / PR / CI checks"       "(no prompt file — plain shell)"
-tmux send-keys -t "$SESSION:git-shell" "echo 'Use this window for: git, gh, branch, commit, PR, CI.'" Enter
-tmux send-keys -t "$SESSION:git-shell" "echo 'Reminder: never push to main directly; never auto-merge.'" Enter
+# --- Create session with two AI windows and one manual shell ------------------
+tmux new-session -d -s "$SESSION" -n "claude" -c "$WORK_DIR"
+tmux new-window  -t "$SESSION"   -n "codex"  -c "$WORK_DIR"
+tmux new-window  -t "$SESSION"   -n "git-shell" -c "$WORK_DIR"
+
+# --- Window 1: Claude ---------------------------------------------------------
+print_banner "claude" "Claude" "Planning, requirements, review" "$PROMPTS_DIR/claude.md"
+launch_tool  "claude" "claude"
+
+# --- Window 2: Codex ----------------------------------------------------------
+print_banner "codex" "Codex" "Implementation, tests, patch summary" "$PROMPTS_DIR/codex-implementer.md"
+launch_tool  "codex" "codex"
+
+# --- Window 3: Manual Shell ---------------------------------------------------
+tmux send-keys -t "$SESSION:git-shell" "clear" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo '======================================================='" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo '  Window        : Manual Shell (git-shell)'" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo '  Responsibility: git status, git diff, tests, human commit/PR commands'" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo '  Work dir      : $WORK_DIR'" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo '======================================================='" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo 'Manual shell only. It is not an AI role and is never automated by the GUI pipeline.'" Enter
 tmux send-keys -t "$SESSION:git-shell" "echo" Enter
 
-# --- Land on the manager window first ----------------------------------------
-tmux select-window -t "$SESSION:gemini-manager"
+# --- Land on Claude first -----------------------------------------------------
+tmux select-window -t "$SESSION:claude"
 
 if [ -t 1 ]; then
     exec tmux attach -t "$SESSION"
diff --git a/web/public/app.js b/web/public/app.js
index 83c578c..968618f 100644
--- a/web/public/app.js
+++ b/web/public/app.js
@@ -1,6 +1,6 @@
 const state = {
   projectDir: localStorage.getItem('aiTeamProjectDir') || '',
-  jobId: localStorage.getItem('aiTeamJobId') || 'job-002'
+  jobId: localStorage.getItem('aiTeamJobId') || 'mvp-001'
 };
 
 const projectDirEl = document.querySelector('#projectDir');
@@ -16,6 +16,7 @@ const pipelineStateNameEl = document.querySelector('#pipelineStateName');
 const pipelineUpdatedAtEl = document.querySelector('#pipelineUpdatedAt');
 const pipelineTargetWindowEl = document.querySelector('#pipelineTargetWindow');
 const pipelineWaitingApprovalEl = document.querySelector('#pipelineWaitingApproval');
+const detectedIssueAlertEl = document.querySelector('#detectedIssueAlert');
 const pipelineGuidanceEl = document.querySelector('#pipelineGuidance');
 const pipelineStepsEl = document.querySelector('#pipelineSteps');
 const summaryArtifactsEl = document.querySelector('#summaryArtifacts');
@@ -24,9 +25,34 @@ const summaryReviewEl = document.querySelector('#summaryReview');
 const summaryNextActionEl = document.querySelector('#summaryNextAction');
 const tmuxWindowEl = document.querySelector('#tmuxWindow');
 const tmuxOutputEl = document.querySelector('#tmuxOutput');
+const aiControlButtons = [
+  document.querySelector('#approveOnce'),
+  document.querySelector('#approveSession'),
+  document.querySelector('#rejectAction'),
+  document.querySelector('#interruptAction')
+];
 let pipelinePollTimer = null;
 let liveRefreshTimer = null;
 const manualRequiredMessage = 'AI CLI 창에서 승인 대기 중일 수 있습니다. 아래 승인 버튼을 누르거나 tmux 출력을 확인하세요.';
+const detectedIssueMessages = {
+  blocked: 'AI가 작업을 차단했습니다. 작업 범위를 줄이거나 금지 항목을 별도 작업으로 분리한 뒤 다시 실행하세요.',
+  approval_required: 'AI CLI가 승인 대기 중일 수 있습니다. 승인/세션 승인/거절/중단 버튼을 사용하세요.',
+  failed: '실행 오류가 감지되었습니다. 로그를 확인하고 인증/명령/서버 상태를 점검하세요.',
+  manual_review_required: manualRequiredMessage
+};
+const activePipelineStates = new Set([
+  'claude_planning',
+  'codex_implementing',
+  'claude_reviewing',
+  'approval_required'
+]);
+const finalPipelineStates = new Set([
+  'succeeded',
+  'failed',
+  'blocked',
+  'manual_review_required',
+  'idle'
+]);
 
 projectDirEl.value = state.projectDir;
 jobIdEl.value = state.jobId;
@@ -132,14 +158,14 @@ document.querySelector('#createJob').addEventListener('click', () => {
 });
 
 document.querySelector('#saveInput').addEventListener('click', () => {
-  runAction('input.ko.md 저장', () => requestJson('/api/save-input', {
+  runAction('request.ko.md 저장', () => requestJson('/api/save-input', {
     method: 'POST',
     body: JSON.stringify(getForm())
   }));
 });
 
 runPipelineButton.addEventListener('click', async () => {
-  const result = await runAction('전체 파이프라인 실행', () => requestJson('/api/pipeline/run', {
+  const result = await runAction('Claude → Codex → Claude 전체 실행', () => requestJson('/api/pipeline/run', {
     method: 'POST',
     body: JSON.stringify(getForm())
   }));
@@ -170,6 +196,7 @@ document.querySelector('#rejectAction').addEventListener('click', () => sendTmux
 document.querySelector('#interruptAction').addEventListener('click', () => sendTmuxControl('중단', '/api/tmux/interrupt'));
 document.querySelector('#refreshTmuxOutput').addEventListener('click', refreshTmuxOutput);
 tmuxWindowEl.addEventListener('change', refreshTmuxOutput);
+tmuxWindowEl.addEventListener('change', updateTmuxControlState);
 
 document.querySelector('#restartAiTeam').addEventListener('click', () => {
   runAction('AI팀 재시작', () => requestJson('/api/service/restart-ai-team', {
@@ -179,11 +206,33 @@ document.querySelector('#restartAiTeam').addEventListener('click', () => {
 });
 
 document.querySelector('#restartGui').addEventListener('click', () => {
-  runAction('GUI 서버 재시작', () => requestJson('/api/service/restart-gui', {
+  restartGuiServer();
+});
+
+async function restartGuiServer() {
+  const result = await runAction('GUI 서버 재시작', () => requestJson('/api/service/restart-gui', {
     method: 'POST',
     body: JSON.stringify(getForm())
   }));
-});
+  if (!result) {
+    return;
+  }
+
+  writeOutput('GUI 서버 재시작 요청 완료', '3~5초 뒤 자동 확인합니다');
+  setTimeout(checkGuiRestartStatus, 5000);
+}
+
+async function checkGuiRestartStatus() {
+  try {
+    const result = await requestJson('/api/status');
+    writeOutput('GUI 서버 재시작 확인', result.output || 'GUI 서버가 다시 응답합니다.');
+  } catch (error) {
+    writeOutput(
+      'GUI 서버 재시작 확인 실패',
+      '아직 서버가 올라오지 않았습니다. 잠시 후 새로고침하거나 수동 복구 명령을 실행하세요.'
+    );
+  }
+}
 
 document.querySelectorAll('[data-send]').forEach((button) => {
   button.addEventListener('click', () => {
@@ -272,7 +321,7 @@ async function refreshPipelineStatus() {
     );
     renderPipelineStatus(status);
     const pipeline = normalizePipelineStatus(status);
-    if (pipelinePollTimer && ['succeeded', 'failed', 'blocked_safety', 'manual_required', 'idle'].includes(pipeline.state)) {
+    if (pipelinePollTimer && finalPipelineStates.has(pipeline.state)) {
       clearInterval(pipelinePollTimer);
       pipelinePollTimer = null;
       loadArtifacts();
@@ -293,6 +342,8 @@ function renderPipelineStatus(status) {
     pipelineUpdatedAtEl.textContent = '-';
     pipelineTargetWindowEl.textContent = '-';
     pipelineWaitingApprovalEl.textContent = '-';
+    detectedIssueAlertEl.hidden = true;
+    detectedIssueAlertEl.textContent = '';
     pipelineGuidanceEl.hidden = true;
     pipelineGuidanceEl.textContent = '';
     pipelineStepsEl.textContent = '';
@@ -308,20 +359,21 @@ function renderPipelineStatus(status) {
   const current = pipeline.step ? ` / 현재 단계: ${pipeline.step}` : '';
   pipelineStateEl.textContent = `${pipeline.state}: ${pipeline.message}${current}`;
   pipelineStateEl.dataset.status = pipeline.state;
-  runPipelineButton.disabled = pipeline.state === 'running';
+  runPipelineButton.disabled = activePipelineStates.has(pipeline.state);
   pipelineJobIdEl.textContent = status.jobId || currentForm.jobId || '-';
   pipelineStageEl.textContent = pipeline.step || '-';
   pipelineStateNameEl.textContent = pipeline.state;
   pipelineUpdatedAtEl.textContent = status.updatedAt ? new Date(status.updatedAt).toLocaleTimeString('ko-KR', { hour12: false }) : '-';
   pipelineTargetWindowEl.textContent = pipeline.targetWindow || '-';
   pipelineWaitingApprovalEl.textContent = pipeline.waitingApproval ? '예' : '아니오';
+  renderDetectedIssue(pipeline.detectedIssue);
 
   if (pipeline.targetWindow && tmuxWindowEl.value !== pipeline.targetWindow) {
     tmuxWindowEl.value = pipeline.targetWindow;
     refreshTmuxOutput();
   }
 
-  if (pipeline.state === 'manual_required' || pipeline.state === 'waiting_approval') {
+  if (pipeline.state === 'manual_review_required' || pipeline.state === 'approval_required') {
     pipelineGuidanceEl.hidden = false;
     pipelineGuidanceEl.textContent = pipeline.message || manualRequiredMessage;
   } else {
@@ -386,6 +438,7 @@ function normalizePipelineStatus(payload) {
       step: payload.status.step || null,
       targetWindow: payload.status.targetWindow || null,
       waitingApproval: Boolean(payload.status.waitingApproval),
+      detectedIssue: payload.status.detectedIssue || null,
       artifacts: payload.status.artifacts || [],
       gitDiff: payload.status.gitDiff || '-',
       reviewStatus: payload.status.reviewStatus || '-',
@@ -399,6 +452,7 @@ function normalizePipelineStatus(payload) {
     step: payload && payload.currentStep ? payload.currentStep : null,
     targetWindow: null,
     waitingApproval: false,
+    detectedIssue: null,
     artifacts: payload && payload.artifacts ? payload.artifacts : [],
     gitDiff: '-',
     reviewStatus: '-',
@@ -406,6 +460,25 @@ function normalizePipelineStatus(payload) {
   };
 }
 
+function renderDetectedIssue(issue) {
+  if (!issue) {
+    detectedIssueAlertEl.hidden = true;
+    detectedIssueAlertEl.textContent = '';
+    detectedIssueAlertEl.dataset.type = '';
+    return;
+  }
+
+  const message = detectedIssueMessages[issue.type] || issue.recommendation || 'AI CLI 출력에서 확인이 필요한 상태가 감지되었습니다.';
+  const parts = [
+    message,
+    issue.window ? `창: ${issue.window}` : '',
+    issue.summary ? `감지 내용: ${issue.summary}` : ''
+  ].filter(Boolean);
+  detectedIssueAlertEl.textContent = parts.join('\n');
+  detectedIssueAlertEl.dataset.type = issue.type || 'manual_review_required';
+  detectedIssueAlertEl.hidden = false;
+}
+
 async function loadTmuxWindows() {
   const result = await runAction('tmux 창 목록', () => requestJson('/api/tmux/windows'));
   tmuxWindowEl.textContent = '';
@@ -413,12 +486,22 @@ async function loadTmuxWindows() {
   windows.forEach((windowInfo) => {
     const option = document.createElement('option');
     option.value = windowInfo.name;
-    option.textContent = `${windowInfo.name}${windowInfo.available ? '' : ' (세션 없음)'}`;
+    option.dataset.aiRole = windowInfo.aiRole ? 'true' : 'false';
+    option.textContent = `${windowInfo.label || windowInfo.name}${windowInfo.available ? '' : ' (세션 없음)'}`;
     tmuxWindowEl.appendChild(option);
   });
   if (!tmuxWindowEl.value && windows.length > 0) {
     tmuxWindowEl.value = windows[0].name;
   }
+  updateTmuxControlState();
+}
+
+function updateTmuxControlState() {
+  const selected = tmuxWindowEl.options[tmuxWindowEl.selectedIndex];
+  const isAiRole = !selected || selected.dataset.aiRole !== 'false';
+  aiControlButtons.forEach((button) => {
+    button.disabled = !isAiRole;
+  });
 }
 
 async function refreshTmuxOutput() {
@@ -443,6 +526,11 @@ async function sendTmuxControl(title, endpoint) {
     writeOutput(`${title} 실패`, '제어할 tmux 창을 선택하세요.');
     return null;
   }
+  const selected = tmuxWindowEl.options[tmuxWindowEl.selectedIndex];
+  if (selected && selected.dataset.aiRole === 'false') {
+    writeOutput(`${title} 실패`, 'Manual Shell(git-shell)은 비AI 창입니다. 승인/거절 키 입력은 Claude 또는 Codex 창에서만 사용하세요.');
+    return null;
+  }
   const result = await runAction(title, () => requestJson(endpoint, {
     method: 'POST',
     body: JSON.stringify({ window: windowName })
diff --git a/web/public/index.html b/web/public/index.html
index 274dd31..110e191 100644
--- a/web/public/index.html
+++ b/web/public/index.html
@@ -9,7 +9,7 @@
   <body>
     <header class="topbar">
       <div>
-        <p class="eyebrow">Local tmux Control</p>
+        <p class="eyebrow">Claude + Codex Workflow</p>
         <h1>AI 개발팀 컨트롤 센터</h1>
       </div>
       <button id="refreshStatus" type="button">상태 확인</button>
@@ -24,15 +24,31 @@
         </label>
         <label>
           작업 ID
-          <input id="jobId" type="text" value="job-002" autocomplete="off" spellcheck="false">
+          <input id="jobId" type="text" value="mvp-001" autocomplete="off" spellcheck="false">
         </label>
         <label>
           한국어 작업 요청
           <textarea id="inputKo" spellcheck="false" rows="14"></textarea>
         </label>
         <p class="field-hint">여기에는 한국어 작업 요청만 입력하세요. 쉘 설정 명령, 실행 명령, 토큰, 비밀값은 넣지 않습니다.</p>
+        <div class="role-display" aria-label="역할 안내">
+          <div>
+            <strong>Claude</strong>
+            <span>planning / requirements / review</span>
+          </div>
+          <div>
+            <strong>Codex</strong>
+            <span>implementation / tests / patch summary</span>
+          </div>
+        </div>
+        <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
         <div class="pipeline-runner">
-          <button id="runPipeline" class="primary-action" type="button">전체 파이프라인 실행</button>
+          <button id="runPipeline" class="primary-action" type="button">Claude → Codex → Claude 전체 실행</button>
+          <div class="primary-actions">
+            <button data-send="claude-plan" type="button">Claude 계획 생성</button>
+            <button data-send="codex-implement" type="button">Codex 구현 실행</button>
+            <button data-send="claude-review" type="button">Claude 리뷰 실행</button>
+          </div>
         </div>
       </section>
 
@@ -71,13 +87,14 @@
             <dd id="pipelineWaitingApproval">-</dd>
           </div>
         </dl>
+        <div id="detectedIssueAlert" class="issue-alert" hidden></div>
         <div id="pipelineGuidance" class="pipeline-guidance" hidden></div>
         <div id="pipelineSteps" class="pipeline-steps"></div>
       </section>
 
       <section class="panel control-panel">
         <h2>승인 / 서비스 제어</h2>
-        <p class="warning-text">승인은 현재 AI CLI 창에 키 입력을 보내는 기능입니다. 위험한 명령은 승인하지 마세요.</p>
+        <p class="warning-text">승인은 Claude 또는 Codex AI CLI 창에만 키 입력을 보내는 기능입니다. Manual Shell(git-shell)은 사람이 직접 git/test 명령을 실행하는 비AI 창입니다.</p>
         <label>
           제어할 tmux 창
           <select id="tmuxWindow"></select>
@@ -127,11 +144,7 @@
         <div class="actions">
           <button id="startTeam" type="button">AI 팀 시작</button>
           <button id="createJob" type="button">작업 폴더 생성</button>
-          <button id="saveInput" type="button">input.ko.md 저장</button>
-          <button data-send="gemini" type="button">Gemini Manager 전송</button>
-          <button data-send="claude-architect" type="button">Claude Architect 전송</button>
-          <button data-send="codex" type="button">Codex Implementer 전송</button>
-          <button data-send="claude-reviewer" type="button">Claude Reviewer 전송</button>
+          <button id="saveInput" type="button">request.ko.md 저장</button>
           <button id="gitStatus" type="button">git status</button>
           <button id="gitDiff" type="button">git diff</button>
         </div>
diff --git a/web/public/style.css b/web/public/style.css
index 4049830..59d8f76 100644
--- a/web/public/style.css
+++ b/web/public/style.css
@@ -119,6 +119,43 @@ label {
   line-height: 1.45;
 }
 
+.role-display {
+  display: grid;
+  grid-template-columns: repeat(2, minmax(0, 1fr));
+  gap: 10px;
+  margin-top: 14px;
+}
+
+.role-display div {
+  display: grid;
+  gap: 4px;
+  padding: 12px;
+  border: 1px solid var(--line);
+  border-radius: 6px;
+  background: #f8fafc;
+}
+
+.role-display strong {
+  font-size: 14px;
+}
+
+.role-display span {
+  color: var(--muted);
+  font-size: 13px;
+  font-weight: 700;
+  line-height: 1.4;
+}
+
+.role-aside {
+  margin: 10px 0 0;
+  padding: 8px 10px;
+  border: 1px dashed var(--line);
+  border-radius: 6px;
+  color: var(--muted);
+  font-size: 12px;
+  line-height: 1.45;
+}
+
 input,
 textarea,
 select {
@@ -193,6 +230,13 @@ button:hover {
   background: #115e59;
 }
 
+.primary-actions {
+  display: grid;
+  grid-template-columns: repeat(3, minmax(0, 1fr));
+  gap: 10px;
+  margin-top: 10px;
+}
+
 button:disabled {
   cursor: not-allowed;
   opacity: 0.6;
@@ -237,13 +281,15 @@ button:disabled {
   font-weight: 800;
 }
 
-.status-line[data-status="running"] {
+.status-line[data-status="claude_planning"],
+.status-line[data-status="codex_implementing"],
+.status-line[data-status="claude_reviewing"] {
   border-color: #93c5fd;
   background: #eff6ff;
   color: #1d4ed8;
 }
 
-.status-line[data-status="waiting_approval"] {
+.status-line[data-status="approval_required"] {
   border-color: #fde68a;
   background: #fffbeb;
   color: #92400e;
@@ -256,8 +302,8 @@ button:disabled {
 }
 
 .status-line[data-status="failed"],
-.status-line[data-status="blocked_safety"],
-.status-line[data-status="manual_required"] {
+.status-line[data-status="blocked"],
+.status-line[data-status="manual_review_required"] {
   border-color: #fecaca;
   background: #fef2f2;
   color: var(--danger);
@@ -298,6 +344,29 @@ button:disabled {
   line-height: 1.45;
 }
 
+.issue-alert {
+  margin-top: 12px;
+  padding: 12px;
+  border: 1px solid #fecaca;
+  border-radius: 6px;
+  background: #fef2f2;
+  color: var(--danger);
+  font-weight: 800;
+  line-height: 1.5;
+  white-space: pre-wrap;
+}
+
+.issue-alert[data-type="approval_required"] {
+  border-color: #fde68a;
+  background: #fffbeb;
+  color: #92400e;
+}
+
+.issue-alert[data-type="blocked"] {
+  border-color: #fb7185;
+  background: #fff1f2;
+}
+
 .warning-text {
   margin: 12px 0 0;
   padding: 10px 12px;
@@ -423,6 +492,14 @@ pre {
     grid-template-columns: 1fr;
   }
 
+  .role-display {
+    grid-template-columns: 1fr;
+  }
+
+  .primary-actions {
+    grid-template-columns: 1fr;
+  }
+
   .pipeline-meta {
     grid-template-columns: 1fr;
   }
diff --git a/web/server.js b/web/server.js
index b6be243..0ce1e5d 100644
--- a/web/server.js
+++ b/web/server.js
@@ -1,42 +1,116 @@
 const express = require('express');
 const fs = require('fs/promises');
 const path = require('path');
-const { execFile } = require('child_process');
+const { execFile, spawn } = require('child_process');
 
 const app = express();
 const HOST = process.env.HOST || '127.0.0.1';
 const PORT = Number(process.env.PORT || 3100);
 const SESSION = 'ai-team';
+const GUI_SESSION = 'ai-gui';
 const ROOT_DIR = path.resolve(__dirname, '..');
 const SCRIPTS_DIR = path.join(ROOT_DIR, 'scripts');
+const WEB_DIR = path.join(ROOT_DIR, 'web');
+const GUI_RESTART_LOG = '/tmp/ai-team-gui-restart.log';
 const SAFE_WINDOWS = {
-  gemini: 'gemini-manager',
-  'claude-architect': 'claude-architect',
-  codex: 'codex-implementer',
-  'claude-reviewer': 'claude-reviewer'
+  'claude-plan': 'claude',
+  'codex-implement': 'codex',
+  'claude-review': 'claude',
+  claude: 'claude',
+  codex: 'codex'
 };
 const ALLOWED_TMUX_WINDOWS = new Set([
-  'gemini-manager',
-  'claude-architect',
-  'codex-implementer',
-  'claude-reviewer',
+  'claude',
+  'codex',
   'git-shell'
 ]);
+const AI_TMUX_WINDOWS = new Set([
+  'claude',
+  'codex'
+]);
+const TMUX_WINDOW_LABELS = {
+  claude: 'Claude - planning, requirements, review',
+  codex: 'Codex - implementation, tests, patch summary',
+  'git-shell': 'Manual Shell - git status, git diff, tests, human commit/PR commands'
+};
 const PIPELINE_STEP_TIMEOUT_MS = Number(process.env.AI_TEAM_PIPELINE_STEP_TIMEOUT_MS || 15 * 60 * 1000);
 const PIPELINE_POLL_MS = Number(process.env.AI_TEAM_PIPELINE_POLL_MS || 5000);
 const MANUAL_REQUIRED_MESSAGE = 'AI CLI 창에서 승인 대기 중일 수 있습니다. 아래 승인 버튼을 누르거나 tmux 출력을 확인하세요.';
+const ISSUE_RECOMMENDATIONS = {
+  blocked: 'AI가 작업을 차단했습니다. 작업 범위를 줄이거나 금지 항목을 별도 작업으로 분리한 뒤 다시 실행하세요.',
+  approval_required: 'AI CLI가 승인 대기 중일 수 있습니다. 승인/세션 승인/거절/중단 버튼을 사용하세요.',
+  failed: '실행 오류가 감지되었습니다. 로그를 확인하고 인증/명령/서버 상태를 점검하세요.',
+  manual_review_required: MANUAL_REQUIRED_MESSAGE
+};
+const ISSUE_PATTERNS = [
+  {
+    type: 'blocked',
+    patterns: [
+      /진행할 수 없습니다/i,
+      /규정 위반/i,
+      /요구사항을 다시 작성/i,
+      /정책상|정책 위반|안전 정책/i,
+      /policy violation|violates policy|disallowed|cannot comply|can't comply|cannot assist/i
+    ]
+  },
+  {
+    type: 'approval_required',
+    patterns: [
+      /approval|approve|allow|continue|proceed|permission/i,
+      /승인|허용|계속 진행|진행하시겠습니까|거절/i,
+      /1\).*(approve|allow|승인|계속)|2\).*(session|세션)|3\).*(reject|거절)/i
+    ]
+  },
+  {
+    type: 'failed',
+    patterns: [
+      /error:|fatal:|exception|traceback|failed|failure/i,
+      /command not found|permission denied|authentication failed|not authenticated/i,
+      /오류|에러|실패|예외|권한.*거부|인증.*실패/i
+    ]
+  },
+  {
+    type: 'manual_review_required',
+    patterns: [
+      /manual intervention|required manual|수동.*필요|직접.*확인|사람.*확인/i
+    ]
+  }
+];
 const pipelineStates = new Map();
 const PIPELINE_STAGES = [
-  { id: 'gemini', label: 'Gemini Manager', role: 'gemini', window: 'gemini-manager', artifacts: ['gemini-plan.en.md', 'codex-prompt.en.md'] },
-  { id: 'claude-architect', label: 'Claude Architect', role: 'claude-architect', window: 'claude-architect', artifacts: ['claude-design-review.en.md', 'architecture.md'] },
-  { id: 'codex', label: 'Codex Implementer', role: 'codex', window: 'codex-implementer', artifacts: ['codex-summary.en.md'] },
-  { id: 'claude-reviewer', label: 'Claude Reviewer', role: 'claude-reviewer', window: 'claude-reviewer', artifacts: ['claude-pr-review.en.md', 'review.md'] }
+  { id: 'claude-plan', state: 'claude_planning', label: 'Claude 계획 생성', role: 'claude-plan', window: 'claude', artifacts: ['plan.md', 'codex-task.md'] },
+  { id: 'codex-implement', state: 'codex_implementing', label: 'Codex 구현 실행', role: 'codex-implement', window: 'codex', artifacts: ['patch.md'] },
+  { id: 'claude-review', state: 'claude_reviewing', label: 'Claude 리뷰 실행', role: 'claude-review', window: 'claude', artifacts: ['review.md'] }
+];
+const ACTIVE_PIPELINE_STATES = new Set([
+  'claude_planning',
+  'codex_implementing',
+  'claude_reviewing',
+  'approval_required'
+]);
+const FINAL_PIPELINE_STATES = new Set([
+  'succeeded',
+  'failed',
+  'blocked',
+  'manual_review_required',
+  'idle'
+]);
+const ARTIFACT_PRIORITY = [
+  'request.ko.md',
+  'plan.md',
+  'codex-task.md',
+  'patch.md',
+  'review.md',
+  'status.md'
 ];
 const ARTIFACT_NAMES = new Set([
   'README.md',
+  'request.ko.md',
   'input.ko.md',
   'input.en.md',
   'plan.en.md',
+  'plan.md',
+  'codex-task.md',
   'gemini-plan.en.md',
   'architecture.md',
   'claude-design-review.en.md',
@@ -45,6 +119,7 @@ const ARTIFACT_NAMES = new Set([
   'codex-summary.en.md',
   'review.md',
   'claude-pr-review.en.md',
+  'status.md',
   'local-diff.patch',
   'pipeline.log.md'
 ]);
@@ -148,6 +223,14 @@ function validateTmuxWindow(windowName) {
   return windowName;
 }
 
+function validateAiTmuxWindow(windowName) {
+  const safeWindow = validateTmuxWindow(windowName);
+  if (!AI_TMUX_WINDOWS.has(safeWindow)) {
+    throw new Error('승인/거절 제어는 Claude 또는 Codex AI 창에서만 사용할 수 있습니다.');
+  }
+  return safeWindow;
+}
+
 function stageById(stageId) {
   return PIPELINE_STAGES.find((stage) => stage.id === stageId) || null;
 }
@@ -171,10 +254,11 @@ function publicIdlePipelineState(projectDir = null, jobId = null) {
       step: null,
       targetWindow: null,
       waitingApproval: false,
+      detectedIssue: null,
       artifacts: [],
       gitDiff: '-',
       reviewStatus: '-',
-      nextAction: '작업 요청을 입력한 뒤 전체 파이프라인 실행을 누르세요.'
+      nextAction: '작업 요청을 입력한 뒤 Claude → Codex → Claude 전체 실행을 누르세요.'
     }
   };
 }
@@ -192,6 +276,7 @@ function publicPipelineState(state) {
   const reviewStatus = review.file
     ? `${review.status}: ${review.file}${review.decision ? ` / ${review.decision}` : ''}`
     : review.status || '-';
+  const detectedIssue = state.detectedIssue || null;
 
   return {
     ok: true,
@@ -207,7 +292,8 @@ function publicPipelineState(state) {
       message: state.error || pipelineMessage(state.status),
       step: state.currentStep,
       targetWindow: currentTargetWindow(state),
-      waitingApproval: state.status === 'waiting_approval' || state.status === 'manual_required',
+      waitingApproval: state.status === 'approval_required' || (detectedIssue && detectedIssue.type === 'approval_required'),
+      detectedIssue,
       artifacts: state.artifacts,
       gitDiff: gitDiffText,
       reviewStatus,
@@ -220,8 +306,14 @@ function publicPipelineState(state) {
 }
 
 function pipelineMessage(status) {
-  if (status === 'running') {
-    return '파이프라인 실행 중입니다.';
+  if (status === 'claude_planning') {
+    return 'Claude가 계획과 Codex 작업 지시문을 작성하는 단계입니다.';
+  }
+  if (status === 'codex_implementing') {
+    return 'Codex가 구현, 테스트, 패치 요약을 진행하는 단계입니다.';
+  }
+  if (status === 'claude_reviewing') {
+    return 'Claude가 현재 diff와 패치 요약을 리뷰하는 단계입니다.';
   }
   if (status === 'succeeded') {
     return '파이프라인이 완료되었습니다.';
@@ -229,13 +321,13 @@ function pipelineMessage(status) {
   if (status === 'failed') {
     return '파이프라인 실행에 실패했습니다.';
   }
-  if (status === 'blocked_safety') {
-    return '안전 정책에 따라 파이프라인이 중단되었습니다.';
+  if (status === 'blocked') {
+    return ISSUE_RECOMMENDATIONS.blocked;
   }
-  if (status === 'waiting_approval') {
+  if (status === 'approval_required') {
     return MANUAL_REQUIRED_MESSAGE;
   }
-  if (status === 'manual_required') {
+  if (status === 'manual_review_required') {
     return MANUAL_REQUIRED_MESSAGE;
   }
   return '아직 실행되지 않았습니다.';
@@ -244,19 +336,22 @@ function pipelineMessage(status) {
 function nextRecommendedAction(state, reviewStatus) {
   if (state.status === 'succeeded') {
     return reviewStatus && reviewStatus !== '-'
-      ? 'Reviewer 결과를 확인한 뒤 사람이 직접 commit, push, PR 생성 여부를 결정하세요.'
+      ? 'Claude 리뷰 결과를 확인한 뒤 사람이 직접 commit, push, PR 생성 여부를 결정하세요.'
       : '산출물과 git diff를 확인한 뒤 사람이 직접 다음 작업을 결정하세요.';
   }
-  if (state.status === 'manual_required' || state.status === 'waiting_approval') {
+  if (state.status === 'manual_review_required' || state.status === 'approval_required') {
     return 'tmux 출력을 확인하고 필요한 경우 승인 / 계속 진행, 세션 승인, 거절, 중단 중 하나를 선택하세요.';
   }
+  if (state.status === 'blocked') {
+    return ISSUE_RECOMMENDATIONS.blocked;
+  }
   if (state.status === 'failed') {
     return '오류 메시지와 tmux 출력을 확인한 뒤 상태 초기화 또는 수동 복구를 진행하세요.';
   }
-  if (state.status === 'running') {
+  if (ACTIVE_PIPELINE_STATES.has(state.status)) {
     return '현재 단계의 tmux 출력을 보면서 진행 상황을 확인하세요.';
   }
-  return '전체 파이프라인 실행을 시작하세요.';
+  return 'Claude → Codex → Claude 전체 실행을 시작하세요.';
 }
 
 function createPipelineState(projectDir, jobId) {
@@ -266,12 +361,13 @@ function createPipelineState(projectDir, jobId) {
     jobKey: key,
     projectDir,
     jobId,
-    status: 'running',
+    status: 'claude_planning',
     currentStep: 'queued',
     startedAt: now,
     finishedAt: null,
     updatedAt: now,
     error: null,
+    detectedIssue: null,
     steps: [],
     artifacts: [],
     summary: {
@@ -295,7 +391,7 @@ function setStep(state, id, label, status, detail = '') {
     step.startedAt = now;
     step.finishedAt = null;
   }
-  if (['succeeded', 'failed', 'blocked_safety', 'manual_required', 'waiting_approval'].includes(status)) {
+  if (['succeeded', 'failed', 'blocked', 'manual_review_required', 'approval_required'].includes(status)) {
     step.finishedAt = now;
   }
   state.currentStep = status === 'running' ? id : state.currentStep;
@@ -324,7 +420,14 @@ async function listArtifacts(projectDir, jobId) {
       const relativePath = path.join('docs', 'ai', 'jobs', jobId, entry.name);
       return { name: entry.name, path: relativePath };
     })
-    .sort((a, b) => a.name.localeCompare(b.name));
+    .sort((a, b) => {
+      const aPriority = ARTIFACT_PRIORITY.indexOf(a.name);
+      const bPriority = ARTIFACT_PRIORITY.indexOf(b.name);
+      if (aPriority !== -1 || bPriority !== -1) {
+        return (aPriority === -1 ? 999 : aPriority) - (bPriority === -1 ? 999 : bPriority);
+      }
+      return a.name.localeCompare(b.name);
+    });
 }
 
 async function refreshPipelineArtifacts(state) {
@@ -344,9 +447,12 @@ async function findFirstExistingArtifact(projectDir, jobId, names) {
   return null;
 }
 
-async function waitForArtifact(projectDir, jobId, names, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
+async function waitForArtifact(projectDir, jobId, names, state = null, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
   const started = Date.now();
   while (Date.now() - started < timeoutMs) {
+    if (state && !ACTIVE_PIPELINE_STATES.has(state.status)) {
+      return null;
+    }
     const artifact = await findFirstExistingArtifact(projectDir, jobId, names);
     if (artifact) {
       return artifact;
@@ -357,15 +463,21 @@ async function waitForArtifact(projectDir, jobId, names, timeoutMs = PIPELINE_ST
 }
 
 function markManualRequired(state, stepId, label) {
-  state.status = 'manual_required';
+  state.status = 'manual_review_required';
   state.finishedAt = new Date().toISOString();
   state.updatedAt = state.finishedAt;
   state.error = MANUAL_REQUIRED_MESSAGE;
-  setStep(state, stepId, label, 'manual_required', MANUAL_REQUIRED_MESSAGE);
+  state.detectedIssue = state.detectedIssue || {
+    type: 'manual_review_required',
+    window: currentTargetWindow(state),
+    summary: MANUAL_REQUIRED_MESSAGE,
+    recommendation: ISSUE_RECOMMENDATIONS.manual_review_required
+  };
+  setStep(state, stepId, label, 'manual_review_required', MANUAL_REQUIRED_MESSAGE);
 }
 
 function markTimedOutRunningStep(state) {
-  if (!['running', 'waiting_approval'].includes(state.status) || !state.currentStep) {
+  if (!ACTIVE_PIPELINE_STATES.has(state.status) || !state.currentStep) {
     return;
   }
   const running = state.steps.find((step) => step.id === state.currentStep && step.status === 'running');
@@ -379,31 +491,77 @@ function markTimedOutRunningStep(state) {
   markManualRequired(state, running.id, running.label);
 }
 
-function looksLikeApprovalPrompt(output) {
-  return /approval|approve|allow|continue|proceed|permission|승인|허용|계속|진행|거절|reject|1\)|2\)|3\)/i.test(output || '');
+function summarizeIssue(output, type) {
+  const lines = String(output || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
+  const matcher = ISSUE_PATTERNS.find((item) => item.type === type);
+  if (matcher) {
+    const matched = lines.find((line) => matcher.patterns.some((pattern) => pattern.test(line)));
+    if (matched) {
+      return matched.slice(0, 220);
+    }
+  }
+  return lines.slice(-3).join(' ').slice(0, 220) || ISSUE_RECOMMENDATIONS[type] || '최근 tmux 출력에서 확인이 필요한 상태를 감지했습니다.';
+}
+
+function detectIssueFromOutput(output, windowName) {
+  const text = String(output || '');
+  for (const category of ISSUE_PATTERNS) {
+    if (category.patterns.some((pattern) => pattern.test(text))) {
+      return {
+        type: category.type,
+        window: windowName,
+        summary: summarizeIssue(text, category.type),
+        recommendation: ISSUE_RECOMMENDATIONS[category.type]
+      };
+    }
+  }
+  return null;
+}
+
+async function captureRecentTmuxOutput(windowName, lines = 120) {
+  const safeWindow = validateTmuxWindow(windowName);
+  const result = await runFile('tmux', ['capture-pane', '-p', '-S', `-${lines}`, '-t', `${SESSION}:${safeWindow}`], {
+    timeout: 10000,
+    maxBuffer: 256 * 1024
+  });
+  return result.ok ? redactedOutput(result.stdout) : '';
 }
 
-async function refreshApprovalState(state) {
-  if (!state || state.status !== 'running') {
+async function refreshDetectedIssue(state) {
+  if (!state || !ACTIVE_PIPELINE_STATES.has(state.status)) {
     return;
   }
   const targetWindow = currentTargetWindow(state);
   if (!targetWindow) {
     return;
   }
-  const result = await runFile('tmux', ['capture-pane', '-p', '-S', '-80', '-t', `${SESSION}:${targetWindow}`], {
-    timeout: 10000,
-    maxBuffer: 256 * 1024
-  });
-  if (result.ok && looksLikeApprovalPrompt(result.stdout)) {
-    state.status = 'waiting_approval';
-    state.error = MANUAL_REQUIRED_MESSAGE;
-    state.updatedAt = new Date().toISOString();
+  const output = await captureRecentTmuxOutput(targetWindow, 120);
+  const issue = detectIssueFromOutput(output, targetWindow);
+  if (!issue) {
+    return;
+  }
+
+  state.detectedIssue = issue;
+  state.error = issue.recommendation;
+  state.updatedAt = new Date().toISOString();
+
+  if (issue.type === 'blocked') {
+    state.status = 'blocked';
+    state.finishedAt = state.updatedAt;
+    setStep(state, state.currentStep, stageById(state.currentStep)?.label || state.currentStep, 'blocked', issue.summary);
+  } else if (issue.type === 'failed') {
+    state.status = 'failed';
+    state.finishedAt = state.updatedAt;
+    setStep(state, state.currentStep, stageById(state.currentStep)?.label || state.currentStep, 'failed', issue.summary);
+  } else if (issue.type === 'approval_required') {
+    state.status = 'approval_required';
+  } else if (issue.type === 'manual_review_required') {
+    markManualRequired(state, state.currentStep, stageById(state.currentStep)?.label || state.currentStep);
   }
 }
 
 async function applyArtifactProgress(state) {
-  if (!state || !['running', 'waiting_approval'].includes(state.status)) {
+  if (!state || !ACTIVE_PIPELINE_STATES.has(state.status)) {
     return;
   }
 
@@ -411,8 +569,9 @@ async function applyArtifactProgress(state) {
     const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, stage.artifacts);
     const step = state.steps.find((item) => item.id === stage.id);
     if (artifact && step && step.status === 'running') {
-      state.status = 'running';
+      state.status = stage.state;
       state.error = null;
+      state.detectedIssue = null;
       setStep(state, stage.id, stage.label, 'succeeded', artifact.name);
     }
   }
@@ -421,8 +580,9 @@ async function applyArtifactProgress(state) {
   if (current) {
     const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, current.artifacts);
     if (artifact) {
-      state.status = 'running';
+      state.status = current.state;
       state.error = null;
+      state.detectedIssue = null;
       setStep(state, current.id, current.label, 'succeeded', artifact.name);
     }
   }
@@ -480,7 +640,7 @@ async function updateGitDiffSummary(projectDir, jobId, state) {
 }
 
 async function updateReviewSummary(projectDir, jobId, state) {
-  const artifact = await findFirstExistingArtifact(projectDir, jobId, ['claude-pr-review.en.md', 'review.md']);
+  const artifact = await findFirstExistingArtifact(projectDir, jobId, ['review.md', 'claude-pr-review.en.md']);
   if (!artifact) {
     state.summary.review = { status: 'not_found', file: null, decision: null };
     return;
@@ -503,15 +663,15 @@ async function runPipeline(state, inputKo) {
     await appendPipelineLog(projectDir, jobId, 'create-job', `Ensured job directory: ${jobDir}`);
     setStep(state, 'create-job', '작업 폴더 생성', 'succeeded', jobDir);
 
-    setStep(state, 'save-input', 'input.ko.md 저장', 'running');
-    const inputPath = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'input.ko.md'));
+    setStep(state, 'save-input', 'request.ko.md 저장', 'running');
+    const inputPath = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'request.ko.md'));
     await fs.writeFile(inputPath, inputKo, 'utf8');
     await appendPipelineLog(projectDir, jobId, 'save-input', `Saved: ${inputPath}`);
-    setStep(state, 'save-input', 'input.ko.md 저장', 'succeeded', inputPath);
+    setStep(state, 'save-input', 'request.ko.md 저장', 'succeeded', inputPath);
     await refreshPipelineArtifacts(state);
 
-    for (const step of PIPELINE_STAGES.slice(0, 3)) {
-      state.status = 'running';
+    for (const step of PIPELINE_STAGES.slice(0, 2)) {
+      state.status = step.state;
       state.error = null;
       setStep(state, step.id, step.label, 'running');
       const sent = await sendToWindow(step.role, projectDir, jobId, inputKo);
@@ -519,24 +679,28 @@ async function runPipeline(state, inputKo) {
       if (!sent.ok) {
         throw new Error(`${step.label} 실패: ${sent.message || sent.stderr || 'tmux 전송 실패'}`);
       }
-      const artifact = await waitForArtifact(projectDir, jobId, step.artifacts);
+      const artifact = await waitForArtifact(projectDir, jobId, step.artifacts, state);
+      if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
+        return;
+      }
       if (!artifact) {
         markManualRequired(state, step.id, step.label);
         await refreshPipelineArtifacts(state);
         return;
       }
-      state.status = 'running';
+      state.status = step.state;
       state.error = null;
+      state.detectedIssue = null;
       setStep(state, step.id, step.label, 'succeeded', artifact.name);
       await refreshPipelineArtifacts(state);
 
-      if (step.id === 'codex') {
+      if (step.id === 'codex-implement') {
         const denied = (await changedFiles(projectDir)).filter(isDeniedSafetyPath);
         if (denied.length > 0) {
-          state.status = 'blocked_safety';
+          state.status = 'blocked';
           state.finishedAt = new Date().toISOString();
           state.error = `안전 차단 경로 변경 감지: ${denied.join(', ')}`;
-          setStep(state, 'safety-check', '안전 경로 확인', 'blocked_safety', state.error);
+          setStep(state, 'safety-check', '안전 경로 확인', 'blocked', state.error);
           await appendPipelineLog(projectDir, jobId, 'safety-check', state.error);
           await refreshPipelineArtifacts(state);
           return;
@@ -550,24 +714,28 @@ async function runPipeline(state, inputKo) {
     setStep(state, 'save-diff', 'git diff 저장', 'succeeded', state.summary.gitDiff.saved ? 'local-diff.patch' : '변경 없음');
     await refreshPipelineArtifacts(state);
 
-    const reviewerStep = PIPELINE_STAGES[3];
-    state.status = 'running';
+    const reviewerStep = PIPELINE_STAGES[2];
+    state.status = reviewerStep.state;
     state.error = null;
     setStep(state, reviewerStep.id, reviewerStep.label, 'running');
     const reviewed = await sendToWindow(reviewerStep.role, projectDir, jobId, inputKo);
-    await appendPipelineLog(projectDir, jobId, 'claude-reviewer', `${reviewed.stdout || ''}${reviewed.stderr || ''}${reviewed.message || ''}`);
+    await appendPipelineLog(projectDir, jobId, 'claude-review', `${reviewed.stdout || ''}${reviewed.stderr || ''}${reviewed.message || ''}`);
     if (!reviewed.ok) {
-      throw new Error(`Claude Reviewer 전송 실패: ${reviewed.message || reviewed.stderr || 'tmux 전송 실패'}`);
+      throw new Error(`Claude 리뷰 전송 실패: ${reviewed.message || reviewed.stderr || 'tmux 전송 실패'}`);
+    }
+    const reviewArtifact = await waitForArtifact(projectDir, jobId, reviewerStep.artifacts, state);
+    if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
+      return;
     }
-    const reviewArtifact = await waitForArtifact(projectDir, jobId, reviewerStep.artifacts);
     if (!reviewArtifact) {
       markManualRequired(state, reviewerStep.id, reviewerStep.label);
       await updateReviewSummary(projectDir, jobId, state);
       await refreshPipelineArtifacts(state);
       return;
     }
-    state.status = 'running';
+    state.status = reviewerStep.state;
     state.error = null;
+    state.detectedIssue = null;
     setStep(state, reviewerStep.id, reviewerStep.label, 'succeeded', reviewArtifact.name);
     await updateReviewSummary(projectDir, jobId, state);
     await refreshPipelineArtifacts(state);
@@ -598,41 +766,42 @@ function buildPrompt(role, projectDir, jobId, inputKo) {
     `Job directory: ${jobDir}`
   ].join('\n');
 
-  if (role === 'gemini') {
+  if (role === 'claude-plan') {
     return [
-      'Use prompts/gemini-manager.md.',
+      'Use prompts/claude.md.',
       common,
       '',
-      'Read the Korean job input below and write the English plan into the job directory.',
+      `Read docs/ai/CLAUDE_CODEX_WORKFLOW.md and ${path.join(jobDir, 'request.ko.md')}.`,
+      `Create the implementation plan in ${path.join(jobDir, 'plan.md')} and the Codex task in ${path.join(jobDir, 'codex-task.md')}.`,
+      'Use the Claude planning output format from prompts/claude.md. Do not commit, push, merge, deploy, or touch secrets.',
       '',
-      inputKo || `(Read from ${path.join(jobDir, 'input.ko.md')})`
+      inputKo || `(Read from ${path.join(jobDir, 'request.ko.md')})`
     ].join('\n');
   }
 
-  if (role === 'claude-architect') {
+  if (role === 'codex-implement') {
     return [
-      'Use prompts/claude-architect.md.',
+      'Use prompts/codex-implementer.md.',
       common,
       '',
-      'Review the plan and write the architecture review into the job directory. Only approve if the design is safe and scoped.'
+      `Read ${path.join(jobDir, 'plan.md')} and ${path.join(jobDir, 'codex-task.md')}. Use ${path.join(jobDir, 'request.ko.md')} as scope context only.`,
+      `Implement only the approved job scope, run applicable checks, and write ${path.join(jobDir, 'patch.md')}.`,
+      'Do not commit, push, merge, deploy, or change secrets, .env, auth, payment, production infra, or database migrations.'
     ].join('\n');
   }
 
-  if (role === 'codex') {
+  if (role === 'claude-review') {
     return [
-      'Use prompts/codex-implementer.md.',
+      'Use prompts/claude.md.',
       common,
       '',
-      'Implement only the approved job scope. Do not commit, push, merge, or change secrets, .env, auth, payment, production infra, or database migrations.'
+      `Review the git diff saved at ${path.join(jobDir, 'local-diff.patch')} when present, ${path.join(jobDir, 'patch.md')}, and the approved request/plan.`,
+      `Write the review into ${path.join(jobDir, 'review.md')} using the Claude review output format.`,
+      'Do not commit, push, merge, deploy, or run arbitrary shell commands.'
     ].join('\n');
   }
 
-  return [
-    'Use prompts/claude-reviewer.md.',
-    common,
-    '',
-    'Review the current diff for this job and write the review into the job directory. Do not commit, push, or merge.'
-  ].join('\n');
+  throw new Error('허용되지 않은 대상입니다.');
 }
 
 async function sendToWindow(role, projectDir, jobId, inputKo) {
@@ -655,7 +824,7 @@ async function sendToWindow(role, projectDir, jobId, inputKo) {
 }
 
 async function sendKeysToWindow(windowName, keys) {
-  const safeWindow = validateTmuxWindow(windowName);
+  const safeWindow = validateAiTmuxWindow(windowName);
   return runFile('tmux', ['send-keys', '-t', `${SESSION}:${safeWindow}`, ...keys]);
 }
 
@@ -668,6 +837,48 @@ function shellQuote(value) {
   return `'${String(value).replace(/'/g, `'\\''`)}'`;
 }
 
+function buildGuiRestartScript() {
+  const quotedLog = shellQuote(GUI_RESTART_LOG);
+  const quotedWebDir = shellQuote(WEB_DIR);
+  const quotedSession = shellQuote(GUI_SESSION);
+  const npmCommand = `env HOST=0.0.0.0 PORT=3100 npm start >> ${quotedLog} 2>&1`;
+  return [
+    `LOG=${quotedLog}`,
+    `echo "===== GUI restart requested: $(date -Is) =====" >> "$LOG"`,
+    'sleep 1',
+    `echo "[1] kill old tmux session ${GUI_SESSION}" >> "$LOG"`,
+    `tmux kill-session -t ${quotedSession} >> "$LOG" 2>&1 || true`,
+    'echo "[2] free port 3100" >> "$LOG"',
+    'if command -v fuser >/dev/null 2>&1; then',
+    '  fuser -k 3100/tcp >> "$LOG" 2>&1 || true',
+    'elif command -v lsof >/dev/null 2>&1; then',
+    '  pids="$(lsof -ti tcp:3100 2>>"$LOG" || true)"',
+    '  if [ -n "$pids" ]; then kill $pids >> "$LOG" 2>&1 || true; fi',
+    'else',
+    '  echo "No fuser or lsof available; port cleanup skipped." >> "$LOG"',
+    'fi',
+    'sleep 1',
+    `echo "[3] create tmux session ${GUI_SESSION}" >> "$LOG"`,
+    `tmux new-session -d -s ${quotedSession} -c ${quotedWebDir} ${shellQuote(npmCommand)} >> "$LOG" 2>&1`,
+    'status=$?',
+    'echo "[4] tmux session creation result: $status" >> "$LOG"',
+    'sleep 2',
+    'echo "[5] port 3100 status" >> "$LOG"',
+    '(command -v ss >/dev/null 2>&1 && ss -ltnp "sport = :3100" >> "$LOG" 2>&1) || true',
+    'echo "===== GUI restart script finished: $(date -Is) =====" >> "$LOG"'
+  ].join('\n');
+}
+
+function scheduleGuiRestart() {
+  const child = spawn('sh', ['-lc', buildGuiRestartScript()], {
+    detached: true,
+    stdio: 'ignore',
+    cwd: ROOT_DIR,
+    env: { ...process.env, TERM: process.env.TERM || 'xterm-256color' }
+  });
+  child.unref();
+}
+
 function handleError(res, error) {
   res.status(400).json({ ok: false, error: error.message || '요청을 처리할 수 없습니다.' });
 }
@@ -707,7 +918,7 @@ app.post('/api/save-input', async (req, res) => {
     const jobId = validateJobId(req.body.jobId);
     const inputKo = typeof req.body.inputKo === 'string' ? req.body.inputKo : '';
     const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
-    const target = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'input.ko.md'));
+    const target = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'request.ko.md'));
     await fs.mkdir(jobDir, { recursive: true });
     await fs.writeFile(target, inputKo, 'utf8');
     res.json({ ok: true, output: `저장됨: ${target}` });
@@ -723,13 +934,13 @@ app.post('/api/pipeline/run', async (req, res) => {
     const inputKo = typeof req.body.inputKo === 'string' ? req.body.inputKo : '';
     const key = pipelineKey(projectDir, jobId);
     const existing = pipelineStates.get(key);
-    if (existing && existing.status === 'running') {
+    if (existing && ACTIVE_PIPELINE_STATES.has(existing.status)) {
       res.status(409).json({ ok: false, error: '이 작업의 파이프라인이 이미 실행 중입니다.' });
       return;
     }
 
     const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
-    const inputPath = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'input.ko.md'));
+    const inputPath = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'request.ko.md'));
     await fs.mkdir(jobDir, { recursive: true });
     await fs.writeFile(inputPath, inputKo, 'utf8');
 
@@ -742,8 +953,9 @@ app.post('/api/pipeline/run', async (req, res) => {
       startedAt: state.startedAt,
       status: {
         state: state.status,
-        message: '파이프라인을 시작했습니다.',
+        message: 'Claude → Codex → Claude 전체 실행을 시작했습니다.',
         step: state.currentStep,
+        detectedIssue: null,
         artifacts: [],
         gitDiff: '-',
         reviewStatus: '-'
@@ -767,6 +979,7 @@ app.post('/api/pipeline/reset', async (req, res) => {
         state: 'idle',
         message: '선택한 작업의 파이프라인 상태를 초기화했습니다.',
         step: null,
+        detectedIssue: null,
         artifacts: [],
         gitDiff: '-',
         reviewStatus: '-'
@@ -785,10 +998,10 @@ app.get('/api/pipeline/status', async (req, res) => {
     const state = pipelineStates.get(key);
     if (state) {
       await applyArtifactProgress(state);
-      await refreshApprovalState(state);
+      await refreshDetectedIssue(state);
       markTimedOutRunningStep(state);
       await refreshPipelineArtifacts(state);
-      if (state.status !== 'running') {
+      if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
         await updateReviewSummary(projectDir, jobId, state);
       }
       res.json(publicPipelineState(state));
@@ -809,6 +1022,8 @@ app.get('/api/tmux/windows', async (req, res) => {
       : [];
     const windows = [...ALLOWED_TMUX_WINDOWS].map((name) => ({
       name,
+      label: TMUX_WINDOW_LABELS[name] || name,
+      aiRole: name === 'claude' || name === 'codex',
       available: existing.includes(name)
     }));
     res.json({ ok: true, windows });
@@ -895,28 +1110,21 @@ app.post('/api/service/restart-ai-team', async (req, res) => {
 
 app.post('/api/service/restart-gui', async (req, res) => {
   try {
-    const restartSession = `ai-gui-restart-${Date.now()}`;
-    const serverPath = path.join(__dirname, 'server.js');
-    const command = `sleep 1; exec node ${shellQuote(serverPath)}`;
-    const started = await runFile('tmux', ['new-session', '-d', '-s', restartSession, '-c', ROOT_DIR, command], {
-      timeout: 10000
+    res.json({
+      ok: true,
+      output: 'GUI 서버 재시작 요청 완료\n3~5초 뒤 자동 확인합니다.',
+      logPath: GUI_RESTART_LOG
     });
-    if (!started.ok) {
-      res.status(500).json(cleanOutput(started));
-      return;
-    }
-    res.json({ ok: true, output: 'GUI 서버 재시작을 예약했습니다.' });
-    setTimeout(() => process.exit(0), 250);
+    setImmediate(scheduleGuiRestart);
   } catch (error) {
     handleError(res, error);
   }
 });
 
 for (const [endpoint, role] of [
-  ['/api/send/gemini', 'gemini'],
-  ['/api/send/claude-architect', 'claude-architect'],
-  ['/api/send/codex', 'codex'],
-  ['/api/send/claude-reviewer', 'claude-reviewer']
+  ['/api/send/claude-plan', 'claude-plan'],
+  ['/api/send/codex-implement', 'codex-implement'],
+  ['/api/send/claude-review', 'claude-review']
 ]) {
   app.post(endpoint, async (req, res) => {
     try {

```

## 2026-05-14T08:05:08.205Z — claude-review

```
(no output)
```

## 2026-05-14T08:05:11.469Z — save-diff

```
diff --git a/README.md b/README.md
index 7a12486..eddcc4c 100644
--- a/README.md
+++ b/README.md
@@ -1,10 +1,25 @@
 # AI Dev Team Control Center
 
+> DEPRECATED: The old 5-role workflow has been replaced by the simpler Claude + Codex workflow.
+> Use [docs/ai/CLAUDE_CODEX_WORKFLOW.md](docs/ai/CLAUDE_CODEX_WORKFLOW.md) for new jobs.
+
 > 로컬 tmux 기반 AI 개발팀을 시작 / 종료 / 관리하기 위한 컨트롤 센터입니다.
 > A control center for managing a local tmux-based AI development team.
 
 ## 팀 구성
 
+새 기본 AI 역할은 **Claude + Codex** 두 개뿐입니다. tmux에는 사람이 직접 git/test 명령을 실행하는 비AI `git-shell` 창도 함께 둡니다.
+
+| 역할 | 하는 일 | 주요 산출물 |
+|------|---------|-----------|
+| Claude | 한국어 요청 정리, 설계, 리스크 점검, 리뷰 | `plan.md`, `review.md` |
+| Codex | 구현, 테스트, 패치 요약 | 코드 변경 + `patch.md` |
+
+> Manual Shell(`git-shell`)은 사람이 직접 `git status`, `git diff`, 테스트, commit, PR 명령을 실행하는 보조 창입니다. AI 역할이 아니며 GUI 파이프라인이 자동화하지 않습니다.
+
+<details>
+<summary>Deprecated: 이전 5역할 구성</summary>
+
 | tmux 번호 | tmux 창 | 역할 | 하는 일 | 주요 산출물 |
 |-----------|---------|------|---------|-----------|
 | `0` | `gemini-manager` | Gemini Manager | 한국어 요청을 읽고 영어 작업 계획으로 정리 | `plan.en.md` |
@@ -13,6 +28,8 @@
 | `3` | `claude-reviewer` | Claude Reviewer | PR diff와 안전 규칙 준수 여부 리뷰 | `review.md` |
 | `4` | `git-shell` | Git Shell | 브랜치, 커밋, PR, CI 확인을 사람이 직접 실행 | git / gh 명령 결과 |
 
+</details>
+
 ## 빠른 시작
 
 처음 실행한다면 아래 순서대로 진행하세요.
@@ -41,9 +58,9 @@ chmod +x scripts/*.sh
 ./scripts/create-job.sh ~/projects/my-app job-001
 ```
 
-이 명령은 실제 작업 파일을 `docs/ai/jobs/<JOB_ID>/` 아래에 만듭니다. 예를 들어 `job-001`이면 `docs/ai/jobs/job-001/input.ko.md`를 작성합니다.
+이 명령은 실제 작업 파일을 `docs/ai/jobs/<JOB_ID>/` 아래에 만듭니다. 예를 들어 `job-001`이면 `docs/ai/jobs/job-001/request.ko.md`를 작성합니다.
 
-4. `gemini-manager` 창에서 `input.ko.md`를 바탕으로 계획을 만들고, 이후 `claude-architect` → `codex-implementer` → `claude-reviewer` 순서로 진행합니다.
+4. `request.ko.md`에 한국어 요청을 적고, `prompts/claude.md`로 Claude에게 계획을 요청합니다. 이후 `prompts/codex-implementer.md`로 Codex가 구현하고, Claude가 리뷰합니다.
 
 5. 세션 상태를 확인하거나 종료할 수 있습니다.
 
@@ -54,20 +71,21 @@ chmod +x scripts/*.sh
 
 > **tmux 창 이동**
 > `Ctrl-b`를 누른 뒤 손을 떼고 숫자를 누릅니다.
-> 예: `Ctrl-b` 다음 `0` = `gemini-manager`, `Ctrl-b` 다음 `2` = `codex-implementer`.
+> 예: `Ctrl-b` 다음 `0` = `claude`, `Ctrl-b` 다음 `1` = `codex`, `Ctrl-b` 다음 `2` = `git-shell`.
 > 분리(detach)는 `Ctrl-b` 다음 `d`입니다. 다시 붙으려면 `tmux attach -t ai-team`을 실행하세요.
 
 ## 워크플로 한 줄 요약
 
-한국어 입력 → Gemini 영어 계획 → Claude 아키텍처 검토 → Codex 구현 → GitHub PR → Claude PR 리뷰 → 사람 최종 승인
+한국어 입력 → Claude 계획 → Codex 구현/테스트 → Claude 리뷰 → 사람이 git 명령 직접 실행
 
 자세한 내용은 다음 문서들을 참고하세요.
 
 - [docs/setup.md](docs/setup.md) — 처음 설치 / 설정
-- [docs/workflow.md](docs/workflow.md) — 단계별 작업 흐름
+- [docs/ai/CLAUDE_CODEX_WORKFLOW.md](docs/ai/CLAUDE_CODEX_WORKFLOW.md) — 새 Claude + Codex 작업 흐름
+- [docs/workflow.md](docs/workflow.md) — deprecated 이전 단계별 작업 흐름
 - [docs/safety-rules.md](docs/safety-rules.md) — 안전 규칙
 
-## 브라우저 GUI v1
+## 브라우저 GUI
 
 PuTTY나 tmux 직접 조작 없이 로컬 브라우저에서 AI 개발팀을 제어할 수 있는 간단한 GUI가 `web/`에 있습니다. 기본 주소는 `http://127.0.0.1:3100`이며 외부 공개용으로 만들지 않았습니다.
 
@@ -88,40 +106,56 @@ HOST=127.0.0.1 PORT=3100 npm start
 GUI에서 할 수 있는 일:
 
 - 프로젝트 경로, 작업 ID, 한국어 작업 요청 입력
+- 메인 액션 버튼 4개: `Claude → Codex → Claude 전체 실행`, `Claude 계획 생성`, `Codex 구현 실행`, `Claude 리뷰 실행`
 - AI 팀 tmux 세션 상태 확인과 시작
-- 작업 폴더 생성과 `input.ko.md` 저장
-- **전체 파이프라인 실행** 버튼으로 작업 폴더 생성 → 입력 저장 → Gemini Manager → Claude Architect → Codex Implementer → `local-diff.patch` 저장 → Claude Reviewer 순서 진행
-- 파이프라인 현재 단계, 성공 / 실패 / 수동 개입 필요 상태 확인
+- 작업 폴더 생성과 `request.ko.md` 저장
+- **Claude → Codex → Claude 전체 실행** 버튼으로 작업 폴더 생성 → 요청 저장 → Claude 계획 생성 → Codex 구현 실행 → Claude 리뷰 실행 순서 진행
+- 파이프라인 상태 8단계: `claude_planning`, `codex_implementing`, `claude_reviewing`, `manual_review_required`, `succeeded`, `failed`, `blocked`, `approval_required`
 - 선택한 프로젝트 경로와 작업 ID 기준으로 파이프라인 상태 확인 및 `파이프라인 상태 초기화`
 - 실시간 tmux 출력 확인, 승인 / 세션 승인 / 거절 / 중단 키 입력 전송
 - AI팀 재시작과 GUI 서버 재시작
-- 생성된 산출물, git diff 저장 상태, Reviewer decision 요약 확인
-- Gemini Manager, Claude Architect, Codex Implementer, Claude Reviewer 창으로 정해진 프롬프트 전송
-- `git status`, `git diff` 확인
-- `docs/ai/jobs/<JOB_ID>/` 아래 산출물 파일 확인
+- 생성된 산출물, git diff 상태, Claude 리뷰 요약 확인
+- 수동 유틸리티 버튼 2개: `git status`, `git diff`
+- Manual Shell(`git-shell`) tmux 창에서 사람이 직접 테스트, commit, PR 명령 실행
+- 자동화하지 않는 것: `commit`, `push`, PR 생성/머지, 배포
+- 임의 shell 명령 입력 기능 없음
+- 절대 변경하지 않는 영역: `.env`, secrets, auth, payment, production infra, database migrations
+- `docs/ai/jobs/<JOB_ID>/` 아래 산출물 파일 확인: `request.ko.md`, `plan.md`, `codex-task.md`, `patch.md`, `review.md`, `status.md`
+
+`Claude → Codex → Claude 전체 실행`은 브라우저 요청을 오래 붙잡지 않습니다. 서버가 메모리에 작업 상태를 만들고 백그라운드에서 안전한 고정 단계만 실행하며, GUI는 `GET /api/pipeline/status`로 상태를 폴링합니다. 서버를 재시작하면 이 메모리 상태는 사라집니다. 이미 tmux 창에 전달된 작업은 계속 진행될 수 있으므로, 재시작 후에는 tmux와 산출물 파일을 직접 확인하세요.
 
-`전체 파이프라인 실행`은 브라우저 요청을 오래 붙잡지 않습니다. 서버가 메모리에 작업 상태를 만들고 백그라운드에서 안전한 고정 단계만 실행하며, GUI는 `GET /api/pipeline/status`로 상태를 폴링합니다. 서버를 재시작하면 이 메모리 상태는 사라집니다. 이미 tmux 창에 전달된 작업은 계속 진행될 수 있으므로, 재시작 후에는 tmux와 산출물 파일을 직접 확인하세요.
+GUI는 임의 shell command 입력을 제공하지 않습니다. 서버는 허용된 스크립트, 고정 tmux 창, 고정 git 조회 명령만 실행합니다. 승인 버튼은 Claude 또는 Codex AI CLI 창에만 사용합니다. Manual Shell(`git-shell`)은 AI 역할이 아니며 사람이 직접 `git status`, `git diff`, 테스트, commit, PR 명령을 실행하는 창입니다. 파이프라인도 `commit`, `push`, PR 생성, merge, 배포를 자동 실행하지 않습니다. 최종 변경 확인, 커밋, 푸시, PR 생성, merge 승인은 사람이 터미널과 GitHub에서 직접 처리해야 합니다. 자동 merge는 안전상 제공하지 않습니다.
 
-GUI는 임의 shell command 입력을 제공하지 않습니다. 서버는 허용된 스크립트, 고정 tmux 창, 고정 git 조회 명령만 실행합니다. 승인 버튼도 allowlist에 있는 tmux 창에 정해진 키만 보냅니다. 파이프라인도 `commit`, `push`, PR 생성, merge, 배포를 자동 실행하지 않습니다. 최종 변경 확인, 커밋, 푸시, PR 생성, merge 승인은 사람이 `git-shell` 창과 GitHub에서 직접 처리해야 합니다. 자동 merge는 안전상 제공하지 않습니다.
+AI 도구가 중간 승인을 요구하면 GUI는 `approval_required`로 표시합니다. 제한 시간 안에 예상 산출물을 만들지 못하면 `manual_review_required`로 표시합니다. 이 경우 사람이 해당 tmux 창에서 진행 상황을 확인하고 수동으로 이어가야 합니다.
 
-AI 도구가 중간 승인을 요구하거나 제한 시간 안에 예상 산출물을 만들지 못하면 GUI는 해당 단계를 `manual_required`로 표시합니다. 이 경우 사람이 해당 tmux 창에서 진행 상황을 확인하고 수동으로 이어가야 합니다.
+GUI 서버 재시작 버튼을 눌렀는데 `http://<서버 IP>:3100`이 다시 열리지 않으면 SSH/PuTTY에서 아래 수동 복구 명령을 실행하세요. 재시작 로그는 `/tmp/ai-team-gui-restart.log`에 남습니다.
+
+```bash
+fuser -k 3100/tcp 2>/dev/null || true
+tmux kill-session -t ai-gui 2>/dev/null || true
+tmux new-session -d -s ai-gui -c /root/ai-dev-center/projects/ai-team/web "env HOST=0.0.0.0 PORT=3100 npm start"
+```
 
 ## 체크리스트: push 전 확인
 
-- `git-shell` 창에서 `git status`와 `git diff`로 변경 파일을 확인합니다.
+- 터미널에서 `git status`와 `git diff`로 변경 파일을 확인합니다.
 - 변경이 현재 작업 범위에만 있는지 확인합니다.
 - `scripts/`, 비밀 정보, 인증, 결제, DB 마이그레이션, 운영 인프라가 의도치 않게 바뀌지 않았는지 확인합니다.
 - `main`에 직접 push하지 말고 작업 브랜치에서 PR로 진행합니다.
-- Codex 구현 요약과 Claude Reviewer 리뷰 결과를 확인합니다.
-- 전체 규칙은 [docs/safety-rules.md](docs/safety-rules.md), 단계별 흐름은 [docs/workflow.md](docs/workflow.md)를 봅니다.
+- Codex 구현 요약과 Claude 리뷰 결과를 확인합니다.
+- 전체 규칙은 [docs/safety-rules.md](docs/safety-rules.md), 새 단계별 흐름은 [docs/ai/CLAUDE_CODEX_WORKFLOW.md](docs/ai/CLAUDE_CODEX_WORKFLOW.md)를 봅니다.
 
 ## 역할 프롬프트
 
 각 AI 역할이 어떻게 행동해야 하는지는 `prompts/` 안에 있습니다. 필요하면 각 창에서 해당 파일을 열어 그대로 시스템 프롬프트로 사용하세요.
 
+- [prompts/claude.md](prompts/claude.md)
+- [prompts/codex-implementer.md](prompts/codex-implementer.md)
+
+Deprecated historical prompts:
+
 - [prompts/gemini-manager.md](prompts/gemini-manager.md)
 - [prompts/claude-architect.md](prompts/claude-architect.md)
-- [prompts/codex-implementer.md](prompts/codex-implementer.md)
 - [prompts/claude-reviewer.md](prompts/claude-reviewer.md)
 
 ## 안전 규칙 (요약)
@@ -152,7 +186,7 @@ ai-job <PROJECT> <ID>        # 작업 폴더 만들기
 
 ## 예시
 
-`examples/job-001/input.ko.md`는 참고용 예시입니다. 실제 작업은 `./scripts/create-job.sh <PROJECT_DIR> <JOB_ID>`로 만들고, 생성된 `docs/ai/jobs/<JOB_ID>/input.ko.md`에 요청을 작성하세요.
+`examples/job-001/input.ko.md`는 이전 참고용 예시입니다. 실제 작업은 `./scripts/create-job.sh <PROJECT_DIR> <JOB_ID>`로 만들고, 생성된 `docs/ai/jobs/<JOB_ID>/request.ko.md`에 요청을 작성하세요.
 
 ## 디렉터리 구조
 
@@ -160,10 +194,11 @@ ai-job <PROJECT> <ID>        # 작업 폴더 만들기
 .
 ├── README.md
 ├── prompts/
-│   ├── gemini-manager.md
-│   ├── claude-architect.md
+│   ├── claude.md
 │   ├── codex-implementer.md
-│   └── claude-reviewer.md
+│   ├── gemini-manager.md        # deprecated
+│   ├── claude-architect.md      # deprecated
+│   └── claude-reviewer.md       # deprecated
 ├── scripts/
 │   ├── start-ai-team.sh
 │   ├── status-ai-team.sh
@@ -172,6 +207,9 @@ ai-job <PROJECT> <ID>        # 작업 폴더 만들기
 │   └── ai-team-aliases.sh
 ├── docs/
 │   ├── setup.md
+│   ├── ai/
+│   │   ├── CLAUDE_CODEX_WORKFLOW.md
+│   │   └── jobs/
 │   ├── workflow.md
 │   └── safety-rules.md
 └── examples/
diff --git a/docs/safety-rules.md b/docs/safety-rules.md
index a192e29..5946fcf 100644
--- a/docs/safety-rules.md
+++ b/docs/safety-rules.md
@@ -20,7 +20,7 @@ AI 팀이 절대 어겨서는 안 되는 규칙입니다. 같은 규칙이 모
 
 ## 3. 자동 머지 금지
 
-- AI는 PR을 만들 수는 있지만 **머지하지 않습니다**.
+- AI는 PR을 만들거나 머지하지 않습니다. 필요한 git / GitHub 명령은 사람이 직접 실행합니다.
 - 머지는 사람이 리뷰 결과를 읽고 직접 누르는 행위입니다.
 - `gh pr merge --auto`처럼 자동 머지 옵션도 사용하지 않습니다.
 - Mergify, Bulldozer 등 자동 머지 봇 설정 변경도 사람 승인 영역입니다.
@@ -64,7 +64,7 @@ AI 팀이 절대 어겨서는 안 되는 규칙입니다. 같은 규칙이 모
 | 영어 계획 / 아키텍처 / 구현 / 리뷰 | ✓ | ✓ |
 | `git commit` | ✗ | ✓ |
 | `git push` | ✗ | ✓ |
-| PR 생성 | △ (사람이 검토 후) | ✓ |
+| PR 생성 | ✗ | ✓ |
 | PR 머지 | ✗ | ✓ |
 | `.env` / 비밀 추가 / 수정 | ✗ | ✓ (드물게, 의식적으로) |
 | 인증 / 결제 / DB 마이그레이션 변경 | △ (승인 메모 필수) | ✓ |
diff --git a/docs/setup.md b/docs/setup.md
index 1796fff..ef656d5 100644
--- a/docs/setup.md
+++ b/docs/setup.md
@@ -1,6 +1,6 @@
 # 설치 및 설정 가이드 (Setup)
 
-이 저장소는 로컬 AI 개발팀(tmux 기반)을 시작 / 종료 / 관리하는 컨트롤 센터입니다. 처음 사용한다면 아래 순서대로 따라 해주세요.
+이 저장소는 로컬 Claude + Codex 작업 흐름을 시작 / 종료 / 관리하는 컨트롤 센터입니다. 처음 사용한다면 아래 순서대로 따라 해주세요.
 
 ## 1. 필요한 도구
 
@@ -10,7 +10,6 @@
 tmux -V
 git --version
 gh --version       # GitHub CLI
-gemini --version   # Gemini CLI
 claude --version   # Anthropic Claude CLI
 codex --version    # Codex CLI
 ```
@@ -60,11 +59,11 @@ source /절대/경로/ai-team/scripts/ai-team-aliases.sh
 
 | alias | 동작 |
 |-------|------|
-| `ai-team [PROJECT_DIR]` | AI 팀 tmux 세션 시작 (이미 있으면 attach) |
+| `ai-team [PROJECT_DIR]` | Claude + Codex tmux 세션 시작 (이미 있으면 attach) |
 | `ai-attach` | 실행 중인 세션에 다시 붙기 |
 | `ai-status` | 세션 상태 확인 |
 | `ai-stop` | 세션 종료 (확인 후) |
-| `ai-job PROJECT_DIR JOB_ID` | 새 작업 폴더 생성 |
+| `ai-job PROJECT_DIR JOB_ID` | 새 Claude + Codex 작업 폴더 생성 |
 
 ## 5. 첫 실행
 
diff --git a/docs/workflow.md b/docs/workflow.md
index 02d35ec..1f737e6 100644
--- a/docs/workflow.md
+++ b/docs/workflow.md
@@ -1,5 +1,8 @@
 # 워크플로 (Workflow)
 
+> DEPRECATED: This workflow has been replaced by the Claude + Codex workflow.
+> 새 작업은 [docs/ai/CLAUDE_CODEX_WORKFLOW.md](ai/CLAUDE_CODEX_WORKFLOW.md)를 사용하세요.
+
 한 작업이 한국어 요청에서 시작해 GitHub 머지까지 어떻게 흐르는지 설명합니다.
 
 ## 7 단계 파이프라인
diff --git a/prompts/claude-architect.md b/prompts/claude-architect.md
index 977e84c..d73177a 100644
--- a/prompts/claude-architect.md
+++ b/prompts/claude-architect.md
@@ -1,5 +1,7 @@
 # Claude Architect — Role Prompt
 
+> DEPRECATED: This role has been merged into Claude in the simplified Claude + Codex workflow. Use `prompts/claude.md` and `docs/ai/CLAUDE_CODEX_WORKFLOW.md` for new jobs.
+
 You are the **Claude Architect**. You review the English plan from Gemini Manager before any code is written. You are the second line of defense before bad ideas reach the codebase.
 
 ## Inputs you receive
diff --git a/prompts/claude-reviewer.md b/prompts/claude-reviewer.md
index f5dbdf3..1b1f53e 100644
--- a/prompts/claude-reviewer.md
+++ b/prompts/claude-reviewer.md
@@ -1,5 +1,7 @@
 # Claude Reviewer — Role Prompt
 
+> DEPRECATED: This role has been merged into Claude in the simplified Claude + Codex workflow. Use `prompts/claude.md` and `docs/ai/CLAUDE_CODEX_WORKFLOW.md` for new jobs.
+
 You are the **Claude Reviewer**. You are the quality gate before a PR is merged by the human.
 
 ## Inputs you receive
diff --git a/prompts/codex-implementer.md b/prompts/codex-implementer.md
index 92e0bff..181011e 100644
--- a/prompts/codex-implementer.md
+++ b/prompts/codex-implementer.md
@@ -1,42 +1,89 @@
 # Codex Implementer — Role Prompt
 
-You are the **Codex Implementer**. You write the actual code once the plan and architecture are approved.
+You are the **Codex Implementer** in the simplified Claude + Codex workflow. Claude plans and reviews. You implement, test, and summarize the patch.
 
-## Inputs you receive
-- `docs/ai/jobs/{JOB_ID}/plan.en.md` (Gemini Manager)
-- `docs/ai/jobs/{JOB_ID}/architecture.md` (Claude Architect, verdict must be `APPROVE`)
+## Inputs You Receive
+
+- Approved job scope in `docs/ai/jobs/{JOB_ID}/`.
+- `docs/ai/jobs/{JOB_ID}/plan.md` from Claude.
+- `docs/ai/jobs/{JOB_ID}/codex-task.md` when present.
 - The codebase itself.
 
-## Your job
-1. Implement **only** the changes described in the plan + architecture.
-2. Add tests matching the architect's test strategy.
-3. Run the existing test suite locally; do not hand off if it's red.
-4. Summarize your work in `docs/ai/jobs/{JOB_ID}/patch.md`:
-   - File list with one-line description per file.
-   - Diff highlights / notable design decisions.
-   - Test results (pass count, any skipped, any flaky).
-   - Anything the reviewer should pay extra attention to.
-
-## What you do NOT do
-- Do **NOT** `git commit` automatically. The human runs commits in the **git-shell** tmux window.
-- Do **NOT** `git push` automatically.
-- Do **NOT** open or merge PRs automatically.
-- Do **NOT** expand scope. If you find a related bug, file it as a follow-up in `patch.md`; do not fix it inline.
-- Do **NOT** touch any of these — even if it looks like a one-liner:
-  - `.env`, secrets, credentials, API keys, tokens.
-  - Auth / login / session / password / token-handling code.
-  - Payment / billing / subscription code.
-  - Database migration files (schema changes, data backfills).
-  - Production infrastructure.
-
-  Stop and surface to the human via the job folder.
+If older files such as `plan.en.md` or `architecture.md` exist, treat them as historical context only unless the current job scope explicitly says to use them.
+
+## Your Job
+
+1. Read the approved job scope before editing.
+2. Modify only files relevant to the approved scope.
+3. Add or update tests for the changed behavior.
+4. Run these checks when applicable:
+
+```bash
+python -m compileall app tests
+python -m pytest -p no:cacheprovider
+```
+
+5. Write a patch summary for `docs/ai/jobs/{JOB_ID}/patch.md`.
+
+## Output Format
+
+Use this exact structure in your final response and in `patch.md` when you update it:
+
+```markdown
+## 1. Files Changed
+
+## 2. Implementation Summary
+
+## 3. Safety Confirmation
+
+## 4. Test Results
+
+## 5. Remaining TODOs
+```
+
+## What You Must Never Do
+
+- Never `git commit`.
+- Never `git push`.
+- Never merge a PR.
+- Never open or merge PRs automatically.
+- Never expand scope. Put related work in Remaining TODOs.
+- Never edit secrets, `.env`, credentials, API keys, or tokens.
+- Never edit auth, login, session, password, or token-handling code.
+- Never edit payment, billing, or subscription code.
+- Never edit production infrastructure.
+- Never edit database migrations.
+- Never invent vendor endpoints.
+- Never add fake broker endpoints.
+- Never enable live trading by default.
+- Never allow LLMs or recommendation agents to create executable orders.
+- Never bypass RiskEngine.
+
+Stop and surface the issue in the job folder if the approved scope requires any forbidden area.
+
+## Trading Safety Rules
+
+- Paper trading is default.
+- Live trading is disabled by default.
+- Live trading requires explicit validation, preflight, arming, and guard checks.
+- LLMs must never directly place trades.
+- Recommendation agents may only create non-executable order intents.
+- Executable orders may only be created by OMS.
+- All orders must pass Strategy -> Risk Engine -> OMS.
+- Broker-specific API calls must stay inside broker adapters.
+- API keys must only come from `.env`.
+- Do not hardcode secrets.
+- Market orders are disabled by default.
+- Fail closed on uncertainty.
 
 ## Style
-- Follow the project's existing conventions. Match neighbor code.
-- Keep diffs small and focused. One job = one PR.
-- Tests must be deterministic. No `sleep` to "fix" flakiness.
-- Default to no comments. Add one only when the *why* is non-obvious.
-
-## Verdict at the end of `patch.md`
-- `READY FOR REVIEW` — all acceptance criteria met, tests green.
-- `BLOCKED` — describe why; do not hand off.
+
+- Follow the project's existing conventions. Match neighboring code.
+- Keep diffs small and focused.
+- Tests must be deterministic. Do not use `sleep` to hide flakiness.
+- Add comments only when the reason is not obvious from the code.
+
+## Verdict at the End of `patch.md`
+
+- `READY FOR REVIEW` — all acceptance criteria met and applicable tests pass.
+- `BLOCKED` — describe why and do not hand off as complete.
diff --git a/prompts/gemini-manager.md b/prompts/gemini-manager.md
index 4b7820e..02ee7df 100644
--- a/prompts/gemini-manager.md
+++ b/prompts/gemini-manager.md
@@ -1,5 +1,7 @@
 # Gemini Manager — Role Prompt
 
+> DEPRECATED: This role has been replaced by Claude in the simplified Claude + Codex workflow. Use `prompts/claude.md` and `docs/ai/CLAUDE_CODEX_WORKFLOW.md` for new jobs.
+
 You are the **Gemini Manager** at the front of an AI development team. Your job is to turn fuzzy Korean human requests into precise, English, machine-readable work plans for the rest of the team.
 
 ## Inputs you receive
diff --git a/scripts/create-job.sh b/scripts/create-job.sh
index 53a7e24..53682f2 100755
--- a/scripts/create-job.sh
+++ b/scripts/create-job.sh
@@ -1,25 +1,39 @@
 #!/usr/bin/env bash
-# Create a new job folder inside a target project.
+# Create a new Claude + Codex job folder inside a target project.
 #
 # Usage:
-#   ./scripts/create-job.sh PROJECT_DIR JOB_ID
+#   ./scripts/create-job.sh PROJECT_DIR JOB_ID [--force]
 #
 # Creates: PROJECT_DIR/docs/ai/jobs/JOB_ID/
-#   - input.ko.md  (Korean task template the human fills in)
-#   - README.md    (workflow guide for this job)
+#   - request.ko.md
+#   - plan.md
+#   - codex-task.md
+#   - patch.md
+#   - review.md
+#   - status.md
 #
-# Does NOT modify any source code in PROJECT_DIR.
+# Does NOT run git commands. Existing files are overwritten only with --force.
 
 set -euo pipefail
 
-if [ "$#" -lt 2 ]; then
-    echo "Usage: $0 PROJECT_DIR JOB_ID"
+if [ "$#" -lt 2 ] || [ "$#" -gt 3 ]; then
+    echo "Usage: $0 PROJECT_DIR JOB_ID [--force]"
     echo "Example: $0 ~/projects/my-app job-001"
     exit 1
 fi
 
 PROJECT_DIR_INPUT="$1"
 JOB_ID="$2"
+FORCE=false
+
+if [ "$#" -eq 3 ]; then
+    if [ "$3" = "--force" ]; then
+        FORCE=true
+    else
+        echo "Error: unknown option '$3'. Only --force is supported." >&2
+        exit 1
+    fi
+fi
 
 if [ ! -d "$PROJECT_DIR_INPUT" ]; then
     echo "Error: project directory '$PROJECT_DIR_INPUT' does not exist." >&2
@@ -27,99 +41,55 @@ if [ ! -d "$PROJECT_DIR_INPUT" ]; then
 fi
 
 PROJECT_DIR="$(cd "$PROJECT_DIR_INPUT" && pwd)"
+TEMPLATE_DIR="$PROJECT_DIR/docs/ai/jobs/_template"
 JOB_DIR="$PROJECT_DIR/docs/ai/jobs/$JOB_ID"
 
-if [ -e "$JOB_DIR" ]; then
-    echo "Error: job directory already exists: $JOB_DIR" >&2
-    echo "Pick a different JOB_ID or remove the existing directory first." >&2
+if [ ! -d "$TEMPLATE_DIR" ]; then
+    echo "Error: template directory not found: $TEMPLATE_DIR" >&2
+    echo "Create docs/ai/jobs/_template first." >&2
     exit 1
 fi
 
 mkdir -p "$JOB_DIR"
 
-# -----------------------------------------------------------------------------
-# input.ko.md — Korean task template (no variable substitution needed)
-# -----------------------------------------------------------------------------
-cat > "$JOB_DIR/input.ko.md" <<'EOF'
-# 작업 입력 (Job Input)
-
-## 한 줄 요약
-> 무엇을 만들거나 고치고 싶은지 한 문장으로 적어주세요.
-
-(예시: "로그인 페이지에 비밀번호 표시/숨기기 토글 버튼을 추가하고 싶어요.")
-
-## 배경 (Why)
-- 왜 이 작업이 필요한가요?
-- 누가 이 기능을 사용하나요?
-- 지금은 어떻게 동작하고 있나요?
-
-## 목표 (Done 정의)
-- [ ] 목표 1
-- [ ] 목표 2
-- [ ] 목표 3
-
-## 범위 밖 (Not in scope)
-- 이번 작업에서 다루지 않을 항목을 적어주세요.
-- (예: "회원가입 페이지 디자인 변경은 별도 작업으로 분리")
-
-## 제약 조건
-- 이 작업에서는 다음 영역을 절대 변경하지 않습니다:
-  - `.env`, 비밀 키, 자격 증명, API 키, 토큰
-  - 인증 / 로그인 / 세션 / 비밀번호 처리 코드
-  - 결제 / 빌링 / 구독 로직
-  - 데이터베이스 마이그레이션 파일
-  - 운영(prod) 인프라
-- `main` 브랜치 직접 푸시 금지.
-- 자동 머지 금지 — 사람이 직접 머지합니다.
-
-## 참고 자료
-- 관련 파일 / 함수 / URL:
-- 스크린샷 / 디자인 시안:
-- 관련 이슈 / PR 번호:
-
-## 수용 기준 (Acceptance Criteria)
-- [ ] 조건 1 — 어떤 입력에 어떤 출력이 나오면 성공인지 구체적으로 적어주세요.
-- [ ] 조건 2
-- [ ] 모든 기존 테스트가 통과해야 합니다.
-- [ ] 새 테스트가 추가되어 있어야 합니다.
-EOF
-
-# -----------------------------------------------------------------------------
-# README.md — workflow guide (needs JOB_ID substituted)
-# -----------------------------------------------------------------------------
-cat > "$JOB_DIR/README.md" <<EOF
-# Job: $JOB_ID
-
-이 폴더는 AI 팀이 처리하는 작업 단위 하나입니다. 한 작업 = 한 폴더 = 한 PR.
-
-## 단계별 산출 파일
-1. \`input.ko.md\` — 사람이 한국어로 작성한 요청서 (지금 작성해야 함)
-2. \`plan.en.md\` — Gemini Manager가 영어로 정리한 작업 계획 (다음 단계)
-3. \`architecture.md\` — Claude Architect의 설계 / 리스크 / 테스트 전략
-4. \`patch.md\` — Codex Implementer의 변경 요약과 PR 링크
-5. \`review.md\` — Claude Reviewer의 PR 리뷰 결과
-
-## 워크플로
-1. \`input.ko.md\`를 끝까지 채워 넣습니다.
-2. AI 팀 tmux 세션을 시작합니다: \`./scripts/start-ai-team.sh <이 프로젝트 경로>\`.
-3. **gemini-manager** 창에서 \`input.ko.md\` 내용을 붙여 넣어 영어 계획(\`plan.en.md\`)을 만들도록 요청합니다.
-4. **claude-architect** 창에서 계획을 검토받고 \`architecture.md\`를 받습니다. 검토 결과가 \`APPROVE\`일 때만 다음 단계로.
-5. **codex-implementer** 창에서 구현을 진행하고 \`patch.md\`로 정리합니다.
-6. **git-shell** 창에서 사람이 직접 브랜치 생성 / 커밋 / 푸시 / PR 생성을 실행합니다.
-7. **claude-reviewer** 창에서 PR 리뷰를 받고 \`review.md\`로 저장합니다.
-8. 사람이 최종 승인 후 머지합니다.
-
-## 금지 사항 (이 작업에서도 동일)
-- 자동 커밋 / 자동 푸시 / 자동 머지 금지
-- \`.env\`, 비밀 키, 인증, 결제, DB 마이그레이션, 운영 인프라 변경 금지 (사람 승인 시에만)
-- \`main\` 직접 푸시 금지
-EOF
+created=0
+skipped=0
+
+for src in "$TEMPLATE_DIR"/*.md; do
+    name="$(basename "$src")"
+    dest="$JOB_DIR/$name"
+    existed=false
+    if [ -e "$dest" ]; then
+        existed=true
+    fi
+    if [ -e "$dest" ] && [ "$FORCE" = false ]; then
+        echo "Skip existing: $dest"
+        skipped=$((skipped + 1))
+    else
+        cp "$src" "$dest"
+        if [ "$existed" = true ] && [ "$FORCE" = true ]; then
+            echo "Overwrote: $dest"
+        else
+            echo "Created: $dest"
+        fi
+        created=$((created + 1))
+    fi
+done
 
 echo "Created job at: $JOB_DIR"
 echo
 echo "Files:"
 ls -la "$JOB_DIR"
 echo
+echo "Created or overwritten files: $created"
+echo "Skipped existing files: $skipped"
+echo
 echo "Next steps:"
-echo "  1. Edit:  $JOB_DIR/input.ko.md"
-echo "  2. Start: ./scripts/start-ai-team.sh $PROJECT_DIR"
+echo "  1. Put the Korean request in: $JOB_DIR/request.ko.md"
+echo "  2. Ask Claude with: prompts/claude.md"
+echo "  3. Save Claude's plan to: $JOB_DIR/plan.md"
+echo "  4. Ask Codex with: prompts/codex-implementer.md and $JOB_DIR/codex-task.md"
+echo "  5. Save Codex's result to: $JOB_DIR/patch.md"
+echo "  6. Ask Claude to review into: $JOB_DIR/review.md"
+echo
+echo "Workflow doc: $PROJECT_DIR/docs/ai/CLAUDE_CODEX_WORKFLOW.md"
diff --git a/scripts/start-ai-team.sh b/scripts/start-ai-team.sh
index 72e2254..239b1cb 100755
--- a/scripts/start-ai-team.sh
+++ b/scripts/start-ai-team.sh
@@ -1,5 +1,5 @@
 #!/usr/bin/env bash
-# Start the AI team tmux session.
+# Start the simplified Claude + Codex tmux session with a manual shell.
 #
 # Usage:
 #   ./scripts/start-ai-team.sh [PROJECT_DIR]
@@ -75,37 +75,32 @@ launch_tool() {
         "if command -v $tool >/dev/null 2>&1; then $tool; else echo '[!] $tool not found in PATH. Install it, then run: $tool'; fi" Enter
 }
 
-# --- Create session with the five windows ------------------------------------
-tmux new-session -d -s "$SESSION" -n "gemini-manager"    -c "$WORK_DIR"
-tmux new-window  -t "$SESSION"   -n "claude-architect"  -c "$WORK_DIR"
-tmux new-window  -t "$SESSION"   -n "codex-implementer" -c "$WORK_DIR"
-tmux new-window  -t "$SESSION"   -n "claude-reviewer"   -c "$WORK_DIR"
-tmux new-window  -t "$SESSION"   -n "git-shell"         -c "$WORK_DIR"
-
-# --- Window 1: Gemini Manager ------------------------------------------------
-print_banner "gemini-manager"    "Gemini Manager"    "Requirements, planning, English prompt generation" "$PROMPTS_DIR/gemini-manager.md"
-launch_tool  "gemini-manager"    "gemini"
-
-# --- Window 2: Claude Architect ----------------------------------------------
-print_banner "claude-architect"  "Claude Architect"  "Architecture review, risk analysis, test strategy" "$PROMPTS_DIR/claude-architect.md"
-launch_tool  "claude-architect"  "claude"
-
-# --- Window 3: Codex Implementer ---------------------------------------------
-print_banner "codex-implementer" "Codex Implementer" "Implementation, tests, patches"                    "$PROMPTS_DIR/codex-implementer.md"
-launch_tool  "codex-implementer" "codex"
-
-# --- Window 4: Claude Reviewer -----------------------------------------------
-print_banner "claude-reviewer"   "Claude Reviewer"   "PR diff review, quality gate"                      "$PROMPTS_DIR/claude-reviewer.md"
-launch_tool  "claude-reviewer"   "claude"
-
-# --- Window 5: Git Shell (plain shell, no tool launch) -----------------------
-print_banner "git-shell"         "Git Shell"         "git / gh / branch / commit / PR / CI checks"       "(no prompt file — plain shell)"
-tmux send-keys -t "$SESSION:git-shell" "echo 'Use this window for: git, gh, branch, commit, PR, CI.'" Enter
-tmux send-keys -t "$SESSION:git-shell" "echo 'Reminder: never push to main directly; never auto-merge.'" Enter
+# --- Create session with two AI windows and one manual shell ------------------
+tmux new-session -d -s "$SESSION" -n "claude" -c "$WORK_DIR"
+tmux new-window  -t "$SESSION"   -n "codex"  -c "$WORK_DIR"
+tmux new-window  -t "$SESSION"   -n "git-shell" -c "$WORK_DIR"
+
+# --- Window 1: Claude ---------------------------------------------------------
+print_banner "claude" "Claude" "Planning, requirements, review" "$PROMPTS_DIR/claude.md"
+launch_tool  "claude" "claude"
+
+# --- Window 2: Codex ----------------------------------------------------------
+print_banner "codex" "Codex" "Implementation, tests, patch summary" "$PROMPTS_DIR/codex-implementer.md"
+launch_tool  "codex" "codex"
+
+# --- Window 3: Manual Shell ---------------------------------------------------
+tmux send-keys -t "$SESSION:git-shell" "clear" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo '======================================================='" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo '  Window        : Manual Shell (git-shell)'" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo '  Responsibility: git status, git diff, tests, human commit/PR commands'" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo '  Work dir      : $WORK_DIR'" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo '======================================================='" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo" Enter
+tmux send-keys -t "$SESSION:git-shell" "echo 'Manual shell only. It is not an AI role and is never automated by the GUI pipeline.'" Enter
 tmux send-keys -t "$SESSION:git-shell" "echo" Enter
 
-# --- Land on the manager window first ----------------------------------------
-tmux select-window -t "$SESSION:gemini-manager"
+# --- Land on Claude first -----------------------------------------------------
+tmux select-window -t "$SESSION:claude"
 
 if [ -t 1 ]; then
     exec tmux attach -t "$SESSION"
diff --git a/web/public/app.js b/web/public/app.js
index 83c578c..968618f 100644
--- a/web/public/app.js
+++ b/web/public/app.js
@@ -1,6 +1,6 @@
 const state = {
   projectDir: localStorage.getItem('aiTeamProjectDir') || '',
-  jobId: localStorage.getItem('aiTeamJobId') || 'job-002'
+  jobId: localStorage.getItem('aiTeamJobId') || 'mvp-001'
 };
 
 const projectDirEl = document.querySelector('#projectDir');
@@ -16,6 +16,7 @@ const pipelineStateNameEl = document.querySelector('#pipelineStateName');
 const pipelineUpdatedAtEl = document.querySelector('#pipelineUpdatedAt');
 const pipelineTargetWindowEl = document.querySelector('#pipelineTargetWindow');
 const pipelineWaitingApprovalEl = document.querySelector('#pipelineWaitingApproval');
+const detectedIssueAlertEl = document.querySelector('#detectedIssueAlert');
 const pipelineGuidanceEl = document.querySelector('#pipelineGuidance');
 const pipelineStepsEl = document.querySelector('#pipelineSteps');
 const summaryArtifactsEl = document.querySelector('#summaryArtifacts');
@@ -24,9 +25,34 @@ const summaryReviewEl = document.querySelector('#summaryReview');
 const summaryNextActionEl = document.querySelector('#summaryNextAction');
 const tmuxWindowEl = document.querySelector('#tmuxWindow');
 const tmuxOutputEl = document.querySelector('#tmuxOutput');
+const aiControlButtons = [
+  document.querySelector('#approveOnce'),
+  document.querySelector('#approveSession'),
+  document.querySelector('#rejectAction'),
+  document.querySelector('#interruptAction')
+];
 let pipelinePollTimer = null;
 let liveRefreshTimer = null;
 const manualRequiredMessage = 'AI CLI 창에서 승인 대기 중일 수 있습니다. 아래 승인 버튼을 누르거나 tmux 출력을 확인하세요.';
+const detectedIssueMessages = {
+  blocked: 'AI가 작업을 차단했습니다. 작업 범위를 줄이거나 금지 항목을 별도 작업으로 분리한 뒤 다시 실행하세요.',
+  approval_required: 'AI CLI가 승인 대기 중일 수 있습니다. 승인/세션 승인/거절/중단 버튼을 사용하세요.',
+  failed: '실행 오류가 감지되었습니다. 로그를 확인하고 인증/명령/서버 상태를 점검하세요.',
+  manual_review_required: manualRequiredMessage
+};
+const activePipelineStates = new Set([
+  'claude_planning',
+  'codex_implementing',
+  'claude_reviewing',
+  'approval_required'
+]);
+const finalPipelineStates = new Set([
+  'succeeded',
+  'failed',
+  'blocked',
+  'manual_review_required',
+  'idle'
+]);
 
 projectDirEl.value = state.projectDir;
 jobIdEl.value = state.jobId;
@@ -132,14 +158,14 @@ document.querySelector('#createJob').addEventListener('click', () => {
 });
 
 document.querySelector('#saveInput').addEventListener('click', () => {
-  runAction('input.ko.md 저장', () => requestJson('/api/save-input', {
+  runAction('request.ko.md 저장', () => requestJson('/api/save-input', {
     method: 'POST',
     body: JSON.stringify(getForm())
   }));
 });
 
 runPipelineButton.addEventListener('click', async () => {
-  const result = await runAction('전체 파이프라인 실행', () => requestJson('/api/pipeline/run', {
+  const result = await runAction('Claude → Codex → Claude 전체 실행', () => requestJson('/api/pipeline/run', {
     method: 'POST',
     body: JSON.stringify(getForm())
   }));
@@ -170,6 +196,7 @@ document.querySelector('#rejectAction').addEventListener('click', () => sendTmux
 document.querySelector('#interruptAction').addEventListener('click', () => sendTmuxControl('중단', '/api/tmux/interrupt'));
 document.querySelector('#refreshTmuxOutput').addEventListener('click', refreshTmuxOutput);
 tmuxWindowEl.addEventListener('change', refreshTmuxOutput);
+tmuxWindowEl.addEventListener('change', updateTmuxControlState);
 
 document.querySelector('#restartAiTeam').addEventListener('click', () => {
   runAction('AI팀 재시작', () => requestJson('/api/service/restart-ai-team', {
@@ -179,11 +206,33 @@ document.querySelector('#restartAiTeam').addEventListener('click', () => {
 });
 
 document.querySelector('#restartGui').addEventListener('click', () => {
-  runAction('GUI 서버 재시작', () => requestJson('/api/service/restart-gui', {
+  restartGuiServer();
+});
+
+async function restartGuiServer() {
+  const result = await runAction('GUI 서버 재시작', () => requestJson('/api/service/restart-gui', {
     method: 'POST',
     body: JSON.stringify(getForm())
   }));
-});
+  if (!result) {
+    return;
+  }
+
+  writeOutput('GUI 서버 재시작 요청 완료', '3~5초 뒤 자동 확인합니다');
+  setTimeout(checkGuiRestartStatus, 5000);
+}
+
+async function checkGuiRestartStatus() {
+  try {
+    const result = await requestJson('/api/status');
+    writeOutput('GUI 서버 재시작 확인', result.output || 'GUI 서버가 다시 응답합니다.');
+  } catch (error) {
+    writeOutput(
+      'GUI 서버 재시작 확인 실패',
+      '아직 서버가 올라오지 않았습니다. 잠시 후 새로고침하거나 수동 복구 명령을 실행하세요.'
+    );
+  }
+}
 
 document.querySelectorAll('[data-send]').forEach((button) => {
   button.addEventListener('click', () => {
@@ -272,7 +321,7 @@ async function refreshPipelineStatus() {
     );
     renderPipelineStatus(status);
     const pipeline = normalizePipelineStatus(status);
-    if (pipelinePollTimer && ['succeeded', 'failed', 'blocked_safety', 'manual_required', 'idle'].includes(pipeline.state)) {
+    if (pipelinePollTimer && finalPipelineStates.has(pipeline.state)) {
       clearInterval(pipelinePollTimer);
       pipelinePollTimer = null;
       loadArtifacts();
@@ -293,6 +342,8 @@ function renderPipelineStatus(status) {
     pipelineUpdatedAtEl.textContent = '-';
     pipelineTargetWindowEl.textContent = '-';
     pipelineWaitingApprovalEl.textContent = '-';
+    detectedIssueAlertEl.hidden = true;
+    detectedIssueAlertEl.textContent = '';
     pipelineGuidanceEl.hidden = true;
     pipelineGuidanceEl.textContent = '';
     pipelineStepsEl.textContent = '';
@@ -308,20 +359,21 @@ function renderPipelineStatus(status) {
   const current = pipeline.step ? ` / 현재 단계: ${pipeline.step}` : '';
   pipelineStateEl.textContent = `${pipeline.state}: ${pipeline.message}${current}`;
   pipelineStateEl.dataset.status = pipeline.state;
-  runPipelineButton.disabled = pipeline.state === 'running';
+  runPipelineButton.disabled = activePipelineStates.has(pipeline.state);
   pipelineJobIdEl.textContent = status.jobId || currentForm.jobId || '-';
   pipelineStageEl.textContent = pipeline.step || '-';
   pipelineStateNameEl.textContent = pipeline.state;
   pipelineUpdatedAtEl.textContent = status.updatedAt ? new Date(status.updatedAt).toLocaleTimeString('ko-KR', { hour12: false }) : '-';
   pipelineTargetWindowEl.textContent = pipeline.targetWindow || '-';
   pipelineWaitingApprovalEl.textContent = pipeline.waitingApproval ? '예' : '아니오';
+  renderDetectedIssue(pipeline.detectedIssue);
 
   if (pipeline.targetWindow && tmuxWindowEl.value !== pipeline.targetWindow) {
     tmuxWindowEl.value = pipeline.targetWindow;
     refreshTmuxOutput();
   }
 
-  if (pipeline.state === 'manual_required' || pipeline.state === 'waiting_approval') {
+  if (pipeline.state === 'manual_review_required' || pipeline.state === 'approval_required') {
     pipelineGuidanceEl.hidden = false;
     pipelineGuidanceEl.textContent = pipeline.message || manualRequiredMessage;
   } else {
@@ -386,6 +438,7 @@ function normalizePipelineStatus(payload) {
       step: payload.status.step || null,
       targetWindow: payload.status.targetWindow || null,
       waitingApproval: Boolean(payload.status.waitingApproval),
+      detectedIssue: payload.status.detectedIssue || null,
       artifacts: payload.status.artifacts || [],
       gitDiff: payload.status.gitDiff || '-',
       reviewStatus: payload.status.reviewStatus || '-',
@@ -399,6 +452,7 @@ function normalizePipelineStatus(payload) {
     step: payload && payload.currentStep ? payload.currentStep : null,
     targetWindow: null,
     waitingApproval: false,
+    detectedIssue: null,
     artifacts: payload && payload.artifacts ? payload.artifacts : [],
     gitDiff: '-',
     reviewStatus: '-',
@@ -406,6 +460,25 @@ function normalizePipelineStatus(payload) {
   };
 }
 
+function renderDetectedIssue(issue) {
+  if (!issue) {
+    detectedIssueAlertEl.hidden = true;
+    detectedIssueAlertEl.textContent = '';
+    detectedIssueAlertEl.dataset.type = '';
+    return;
+  }
+
+  const message = detectedIssueMessages[issue.type] || issue.recommendation || 'AI CLI 출력에서 확인이 필요한 상태가 감지되었습니다.';
+  const parts = [
+    message,
+    issue.window ? `창: ${issue.window}` : '',
+    issue.summary ? `감지 내용: ${issue.summary}` : ''
+  ].filter(Boolean);
+  detectedIssueAlertEl.textContent = parts.join('\n');
+  detectedIssueAlertEl.dataset.type = issue.type || 'manual_review_required';
+  detectedIssueAlertEl.hidden = false;
+}
+
 async function loadTmuxWindows() {
   const result = await runAction('tmux 창 목록', () => requestJson('/api/tmux/windows'));
   tmuxWindowEl.textContent = '';
@@ -413,12 +486,22 @@ async function loadTmuxWindows() {
   windows.forEach((windowInfo) => {
     const option = document.createElement('option');
     option.value = windowInfo.name;
-    option.textContent = `${windowInfo.name}${windowInfo.available ? '' : ' (세션 없음)'}`;
+    option.dataset.aiRole = windowInfo.aiRole ? 'true' : 'false';
+    option.textContent = `${windowInfo.label || windowInfo.name}${windowInfo.available ? '' : ' (세션 없음)'}`;
     tmuxWindowEl.appendChild(option);
   });
   if (!tmuxWindowEl.value && windows.length > 0) {
     tmuxWindowEl.value = windows[0].name;
   }
+  updateTmuxControlState();
+}
+
+function updateTmuxControlState() {
+  const selected = tmuxWindowEl.options[tmuxWindowEl.selectedIndex];
+  const isAiRole = !selected || selected.dataset.aiRole !== 'false';
+  aiControlButtons.forEach((button) => {
+    button.disabled = !isAiRole;
+  });
 }
 
 async function refreshTmuxOutput() {
@@ -443,6 +526,11 @@ async function sendTmuxControl(title, endpoint) {
     writeOutput(`${title} 실패`, '제어할 tmux 창을 선택하세요.');
     return null;
   }
+  const selected = tmuxWindowEl.options[tmuxWindowEl.selectedIndex];
+  if (selected && selected.dataset.aiRole === 'false') {
+    writeOutput(`${title} 실패`, 'Manual Shell(git-shell)은 비AI 창입니다. 승인/거절 키 입력은 Claude 또는 Codex 창에서만 사용하세요.');
+    return null;
+  }
   const result = await runAction(title, () => requestJson(endpoint, {
     method: 'POST',
     body: JSON.stringify({ window: windowName })
diff --git a/web/public/index.html b/web/public/index.html
index 274dd31..110e191 100644
--- a/web/public/index.html
+++ b/web/public/index.html
@@ -9,7 +9,7 @@
   <body>
     <header class="topbar">
       <div>
-        <p class="eyebrow">Local tmux Control</p>
+        <p class="eyebrow">Claude + Codex Workflow</p>
         <h1>AI 개발팀 컨트롤 센터</h1>
       </div>
       <button id="refreshStatus" type="button">상태 확인</button>
@@ -24,15 +24,31 @@
         </label>
         <label>
           작업 ID
-          <input id="jobId" type="text" value="job-002" autocomplete="off" spellcheck="false">
+          <input id="jobId" type="text" value="mvp-001" autocomplete="off" spellcheck="false">
         </label>
         <label>
           한국어 작업 요청
           <textarea id="inputKo" spellcheck="false" rows="14"></textarea>
         </label>
         <p class="field-hint">여기에는 한국어 작업 요청만 입력하세요. 쉘 설정 명령, 실행 명령, 토큰, 비밀값은 넣지 않습니다.</p>
+        <div class="role-display" aria-label="역할 안내">
+          <div>
+            <strong>Claude</strong>
+            <span>planning / requirements / review</span>
+          </div>
+          <div>
+            <strong>Codex</strong>
+            <span>implementation / tests / patch summary</span>
+          </div>
+        </div>
+        <p class="role-aside">Manual Shell(git-shell)은 비AI 보조 창입니다. 사람이 직접 git status / git diff / 테스트 / commit / PR 명령을 실행합니다.</p>
         <div class="pipeline-runner">
-          <button id="runPipeline" class="primary-action" type="button">전체 파이프라인 실행</button>
+          <button id="runPipeline" class="primary-action" type="button">Claude → Codex → Claude 전체 실행</button>
+          <div class="primary-actions">
+            <button data-send="claude-plan" type="button">Claude 계획 생성</button>
+            <button data-send="codex-implement" type="button">Codex 구현 실행</button>
+            <button data-send="claude-review" type="button">Claude 리뷰 실행</button>
+          </div>
         </div>
       </section>
 
@@ -71,13 +87,14 @@
             <dd id="pipelineWaitingApproval">-</dd>
           </div>
         </dl>
+        <div id="detectedIssueAlert" class="issue-alert" hidden></div>
         <div id="pipelineGuidance" class="pipeline-guidance" hidden></div>
         <div id="pipelineSteps" class="pipeline-steps"></div>
       </section>
 
       <section class="panel control-panel">
         <h2>승인 / 서비스 제어</h2>
-        <p class="warning-text">승인은 현재 AI CLI 창에 키 입력을 보내는 기능입니다. 위험한 명령은 승인하지 마세요.</p>
+        <p class="warning-text">승인은 Claude 또는 Codex AI CLI 창에만 키 입력을 보내는 기능입니다. Manual Shell(git-shell)은 사람이 직접 git/test 명령을 실행하는 비AI 창입니다.</p>
         <label>
           제어할 tmux 창
           <select id="tmuxWindow"></select>
@@ -127,11 +144,7 @@
         <div class="actions">
           <button id="startTeam" type="button">AI 팀 시작</button>
           <button id="createJob" type="button">작업 폴더 생성</button>
-          <button id="saveInput" type="button">input.ko.md 저장</button>
-          <button data-send="gemini" type="button">Gemini Manager 전송</button>
-          <button data-send="claude-architect" type="button">Claude Architect 전송</button>
-          <button data-send="codex" type="button">Codex Implementer 전송</button>
-          <button data-send="claude-reviewer" type="button">Claude Reviewer 전송</button>
+          <button id="saveInput" type="button">request.ko.md 저장</button>
           <button id="gitStatus" type="button">git status</button>
           <button id="gitDiff" type="button">git diff</button>
         </div>
diff --git a/web/public/style.css b/web/public/style.css
index 4049830..59d8f76 100644
--- a/web/public/style.css
+++ b/web/public/style.css
@@ -119,6 +119,43 @@ label {
   line-height: 1.45;
 }
 
+.role-display {
+  display: grid;
+  grid-template-columns: repeat(2, minmax(0, 1fr));
+  gap: 10px;
+  margin-top: 14px;
+}
+
+.role-display div {
+  display: grid;
+  gap: 4px;
+  padding: 12px;
+  border: 1px solid var(--line);
+  border-radius: 6px;
+  background: #f8fafc;
+}
+
+.role-display strong {
+  font-size: 14px;
+}
+
+.role-display span {
+  color: var(--muted);
+  font-size: 13px;
+  font-weight: 700;
+  line-height: 1.4;
+}
+
+.role-aside {
+  margin: 10px 0 0;
+  padding: 8px 10px;
+  border: 1px dashed var(--line);
+  border-radius: 6px;
+  color: var(--muted);
+  font-size: 12px;
+  line-height: 1.45;
+}
+
 input,
 textarea,
 select {
@@ -193,6 +230,13 @@ button:hover {
   background: #115e59;
 }
 
+.primary-actions {
+  display: grid;
+  grid-template-columns: repeat(3, minmax(0, 1fr));
+  gap: 10px;
+  margin-top: 10px;
+}
+
 button:disabled {
   cursor: not-allowed;
   opacity: 0.6;
@@ -237,13 +281,15 @@ button:disabled {
   font-weight: 800;
 }
 
-.status-line[data-status="running"] {
+.status-line[data-status="claude_planning"],
+.status-line[data-status="codex_implementing"],
+.status-line[data-status="claude_reviewing"] {
   border-color: #93c5fd;
   background: #eff6ff;
   color: #1d4ed8;
 }
 
-.status-line[data-status="waiting_approval"] {
+.status-line[data-status="approval_required"] {
   border-color: #fde68a;
   background: #fffbeb;
   color: #92400e;
@@ -256,8 +302,8 @@ button:disabled {
 }
 
 .status-line[data-status="failed"],
-.status-line[data-status="blocked_safety"],
-.status-line[data-status="manual_required"] {
+.status-line[data-status="blocked"],
+.status-line[data-status="manual_review_required"] {
   border-color: #fecaca;
   background: #fef2f2;
   color: var(--danger);
@@ -298,6 +344,29 @@ button:disabled {
   line-height: 1.45;
 }
 
+.issue-alert {
+  margin-top: 12px;
+  padding: 12px;
+  border: 1px solid #fecaca;
+  border-radius: 6px;
+  background: #fef2f2;
+  color: var(--danger);
+  font-weight: 800;
+  line-height: 1.5;
+  white-space: pre-wrap;
+}
+
+.issue-alert[data-type="approval_required"] {
+  border-color: #fde68a;
+  background: #fffbeb;
+  color: #92400e;
+}
+
+.issue-alert[data-type="blocked"] {
+  border-color: #fb7185;
+  background: #fff1f2;
+}
+
 .warning-text {
   margin: 12px 0 0;
   padding: 10px 12px;
@@ -423,6 +492,14 @@ pre {
     grid-template-columns: 1fr;
   }
 
+  .role-display {
+    grid-template-columns: 1fr;
+  }
+
+  .primary-actions {
+    grid-template-columns: 1fr;
+  }
+
   .pipeline-meta {
     grid-template-columns: 1fr;
   }
diff --git a/web/server.js b/web/server.js
index b6be243..0ce1e5d 100644
--- a/web/server.js
+++ b/web/server.js
@@ -1,42 +1,116 @@
 const express = require('express');
 const fs = require('fs/promises');
 const path = require('path');
-const { execFile } = require('child_process');
+const { execFile, spawn } = require('child_process');
 
 const app = express();
 const HOST = process.env.HOST || '127.0.0.1';
 const PORT = Number(process.env.PORT || 3100);
 const SESSION = 'ai-team';
+const GUI_SESSION = 'ai-gui';
 const ROOT_DIR = path.resolve(__dirname, '..');
 const SCRIPTS_DIR = path.join(ROOT_DIR, 'scripts');
+const WEB_DIR = path.join(ROOT_DIR, 'web');
+const GUI_RESTART_LOG = '/tmp/ai-team-gui-restart.log';
 const SAFE_WINDOWS = {
-  gemini: 'gemini-manager',
-  'claude-architect': 'claude-architect',
-  codex: 'codex-implementer',
-  'claude-reviewer': 'claude-reviewer'
+  'claude-plan': 'claude',
+  'codex-implement': 'codex',
+  'claude-review': 'claude',
+  claude: 'claude',
+  codex: 'codex'
 };
 const ALLOWED_TMUX_WINDOWS = new Set([
-  'gemini-manager',
-  'claude-architect',
-  'codex-implementer',
-  'claude-reviewer',
+  'claude',
+  'codex',
   'git-shell'
 ]);
+const AI_TMUX_WINDOWS = new Set([
+  'claude',
+  'codex'
+]);
+const TMUX_WINDOW_LABELS = {
+  claude: 'Claude - planning, requirements, review',
+  codex: 'Codex - implementation, tests, patch summary',
+  'git-shell': 'Manual Shell - git status, git diff, tests, human commit/PR commands'
+};
 const PIPELINE_STEP_TIMEOUT_MS = Number(process.env.AI_TEAM_PIPELINE_STEP_TIMEOUT_MS || 15 * 60 * 1000);
 const PIPELINE_POLL_MS = Number(process.env.AI_TEAM_PIPELINE_POLL_MS || 5000);
 const MANUAL_REQUIRED_MESSAGE = 'AI CLI 창에서 승인 대기 중일 수 있습니다. 아래 승인 버튼을 누르거나 tmux 출력을 확인하세요.';
+const ISSUE_RECOMMENDATIONS = {
+  blocked: 'AI가 작업을 차단했습니다. 작업 범위를 줄이거나 금지 항목을 별도 작업으로 분리한 뒤 다시 실행하세요.',
+  approval_required: 'AI CLI가 승인 대기 중일 수 있습니다. 승인/세션 승인/거절/중단 버튼을 사용하세요.',
+  failed: '실행 오류가 감지되었습니다. 로그를 확인하고 인증/명령/서버 상태를 점검하세요.',
+  manual_review_required: MANUAL_REQUIRED_MESSAGE
+};
+const ISSUE_PATTERNS = [
+  {
+    type: 'blocked',
+    patterns: [
+      /진행할 수 없습니다/i,
+      /규정 위반/i,
+      /요구사항을 다시 작성/i,
+      /정책상|정책 위반|안전 정책/i,
+      /policy violation|violates policy|disallowed|cannot comply|can't comply|cannot assist/i
+    ]
+  },
+  {
+    type: 'approval_required',
+    patterns: [
+      /approval|approve|allow|continue|proceed|permission/i,
+      /승인|허용|계속 진행|진행하시겠습니까|거절/i,
+      /1\).*(approve|allow|승인|계속)|2\).*(session|세션)|3\).*(reject|거절)/i
+    ]
+  },
+  {
+    type: 'failed',
+    patterns: [
+      /error:|fatal:|exception|traceback|failed|failure/i,
+      /command not found|permission denied|authentication failed|not authenticated/i,
+      /오류|에러|실패|예외|권한.*거부|인증.*실패/i
+    ]
+  },
+  {
+    type: 'manual_review_required',
+    patterns: [
+      /manual intervention|required manual|수동.*필요|직접.*확인|사람.*확인/i
+    ]
+  }
+];
 const pipelineStates = new Map();
 const PIPELINE_STAGES = [
-  { id: 'gemini', label: 'Gemini Manager', role: 'gemini', window: 'gemini-manager', artifacts: ['gemini-plan.en.md', 'codex-prompt.en.md'] },
-  { id: 'claude-architect', label: 'Claude Architect', role: 'claude-architect', window: 'claude-architect', artifacts: ['claude-design-review.en.md', 'architecture.md'] },
-  { id: 'codex', label: 'Codex Implementer', role: 'codex', window: 'codex-implementer', artifacts: ['codex-summary.en.md'] },
-  { id: 'claude-reviewer', label: 'Claude Reviewer', role: 'claude-reviewer', window: 'claude-reviewer', artifacts: ['claude-pr-review.en.md', 'review.md'] }
+  { id: 'claude-plan', state: 'claude_planning', label: 'Claude 계획 생성', role: 'claude-plan', window: 'claude', artifacts: ['plan.md', 'codex-task.md'] },
+  { id: 'codex-implement', state: 'codex_implementing', label: 'Codex 구현 실행', role: 'codex-implement', window: 'codex', artifacts: ['patch.md'] },
+  { id: 'claude-review', state: 'claude_reviewing', label: 'Claude 리뷰 실행', role: 'claude-review', window: 'claude', artifacts: ['review.md'] }
+];
+const ACTIVE_PIPELINE_STATES = new Set([
+  'claude_planning',
+  'codex_implementing',
+  'claude_reviewing',
+  'approval_required'
+]);
+const FINAL_PIPELINE_STATES = new Set([
+  'succeeded',
+  'failed',
+  'blocked',
+  'manual_review_required',
+  'idle'
+]);
+const ARTIFACT_PRIORITY = [
+  'request.ko.md',
+  'plan.md',
+  'codex-task.md',
+  'patch.md',
+  'review.md',
+  'status.md'
 ];
 const ARTIFACT_NAMES = new Set([
   'README.md',
+  'request.ko.md',
   'input.ko.md',
   'input.en.md',
   'plan.en.md',
+  'plan.md',
+  'codex-task.md',
   'gemini-plan.en.md',
   'architecture.md',
   'claude-design-review.en.md',
@@ -45,6 +119,7 @@ const ARTIFACT_NAMES = new Set([
   'codex-summary.en.md',
   'review.md',
   'claude-pr-review.en.md',
+  'status.md',
   'local-diff.patch',
   'pipeline.log.md'
 ]);
@@ -148,6 +223,14 @@ function validateTmuxWindow(windowName) {
   return windowName;
 }
 
+function validateAiTmuxWindow(windowName) {
+  const safeWindow = validateTmuxWindow(windowName);
+  if (!AI_TMUX_WINDOWS.has(safeWindow)) {
+    throw new Error('승인/거절 제어는 Claude 또는 Codex AI 창에서만 사용할 수 있습니다.');
+  }
+  return safeWindow;
+}
+
 function stageById(stageId) {
   return PIPELINE_STAGES.find((stage) => stage.id === stageId) || null;
 }
@@ -171,10 +254,11 @@ function publicIdlePipelineState(projectDir = null, jobId = null) {
       step: null,
       targetWindow: null,
       waitingApproval: false,
+      detectedIssue: null,
       artifacts: [],
       gitDiff: '-',
       reviewStatus: '-',
-      nextAction: '작업 요청을 입력한 뒤 전체 파이프라인 실행을 누르세요.'
+      nextAction: '작업 요청을 입력한 뒤 Claude → Codex → Claude 전체 실행을 누르세요.'
     }
   };
 }
@@ -192,6 +276,7 @@ function publicPipelineState(state) {
   const reviewStatus = review.file
     ? `${review.status}: ${review.file}${review.decision ? ` / ${review.decision}` : ''}`
     : review.status || '-';
+  const detectedIssue = state.detectedIssue || null;
 
   return {
     ok: true,
@@ -207,7 +292,8 @@ function publicPipelineState(state) {
       message: state.error || pipelineMessage(state.status),
       step: state.currentStep,
       targetWindow: currentTargetWindow(state),
-      waitingApproval: state.status === 'waiting_approval' || state.status === 'manual_required',
+      waitingApproval: state.status === 'approval_required' || (detectedIssue && detectedIssue.type === 'approval_required'),
+      detectedIssue,
       artifacts: state.artifacts,
       gitDiff: gitDiffText,
       reviewStatus,
@@ -220,8 +306,14 @@ function publicPipelineState(state) {
 }
 
 function pipelineMessage(status) {
-  if (status === 'running') {
-    return '파이프라인 실행 중입니다.';
+  if (status === 'claude_planning') {
+    return 'Claude가 계획과 Codex 작업 지시문을 작성하는 단계입니다.';
+  }
+  if (status === 'codex_implementing') {
+    return 'Codex가 구현, 테스트, 패치 요약을 진행하는 단계입니다.';
+  }
+  if (status === 'claude_reviewing') {
+    return 'Claude가 현재 diff와 패치 요약을 리뷰하는 단계입니다.';
   }
   if (status === 'succeeded') {
     return '파이프라인이 완료되었습니다.';
@@ -229,13 +321,13 @@ function pipelineMessage(status) {
   if (status === 'failed') {
     return '파이프라인 실행에 실패했습니다.';
   }
-  if (status === 'blocked_safety') {
-    return '안전 정책에 따라 파이프라인이 중단되었습니다.';
+  if (status === 'blocked') {
+    return ISSUE_RECOMMENDATIONS.blocked;
   }
-  if (status === 'waiting_approval') {
+  if (status === 'approval_required') {
     return MANUAL_REQUIRED_MESSAGE;
   }
-  if (status === 'manual_required') {
+  if (status === 'manual_review_required') {
     return MANUAL_REQUIRED_MESSAGE;
   }
   return '아직 실행되지 않았습니다.';
@@ -244,19 +336,22 @@ function pipelineMessage(status) {
 function nextRecommendedAction(state, reviewStatus) {
   if (state.status === 'succeeded') {
     return reviewStatus && reviewStatus !== '-'
-      ? 'Reviewer 결과를 확인한 뒤 사람이 직접 commit, push, PR 생성 여부를 결정하세요.'
+      ? 'Claude 리뷰 결과를 확인한 뒤 사람이 직접 commit, push, PR 생성 여부를 결정하세요.'
       : '산출물과 git diff를 확인한 뒤 사람이 직접 다음 작업을 결정하세요.';
   }
-  if (state.status === 'manual_required' || state.status === 'waiting_approval') {
+  if (state.status === 'manual_review_required' || state.status === 'approval_required') {
     return 'tmux 출력을 확인하고 필요한 경우 승인 / 계속 진행, 세션 승인, 거절, 중단 중 하나를 선택하세요.';
   }
+  if (state.status === 'blocked') {
+    return ISSUE_RECOMMENDATIONS.blocked;
+  }
   if (state.status === 'failed') {
     return '오류 메시지와 tmux 출력을 확인한 뒤 상태 초기화 또는 수동 복구를 진행하세요.';
   }
-  if (state.status === 'running') {
+  if (ACTIVE_PIPELINE_STATES.has(state.status)) {
     return '현재 단계의 tmux 출력을 보면서 진행 상황을 확인하세요.';
   }
-  return '전체 파이프라인 실행을 시작하세요.';
+  return 'Claude → Codex → Claude 전체 실행을 시작하세요.';
 }
 
 function createPipelineState(projectDir, jobId) {
@@ -266,12 +361,13 @@ function createPipelineState(projectDir, jobId) {
     jobKey: key,
     projectDir,
     jobId,
-    status: 'running',
+    status: 'claude_planning',
     currentStep: 'queued',
     startedAt: now,
     finishedAt: null,
     updatedAt: now,
     error: null,
+    detectedIssue: null,
     steps: [],
     artifacts: [],
     summary: {
@@ -295,7 +391,7 @@ function setStep(state, id, label, status, detail = '') {
     step.startedAt = now;
     step.finishedAt = null;
   }
-  if (['succeeded', 'failed', 'blocked_safety', 'manual_required', 'waiting_approval'].includes(status)) {
+  if (['succeeded', 'failed', 'blocked', 'manual_review_required', 'approval_required'].includes(status)) {
     step.finishedAt = now;
   }
   state.currentStep = status === 'running' ? id : state.currentStep;
@@ -324,7 +420,14 @@ async function listArtifacts(projectDir, jobId) {
       const relativePath = path.join('docs', 'ai', 'jobs', jobId, entry.name);
       return { name: entry.name, path: relativePath };
     })
-    .sort((a, b) => a.name.localeCompare(b.name));
+    .sort((a, b) => {
+      const aPriority = ARTIFACT_PRIORITY.indexOf(a.name);
+      const bPriority = ARTIFACT_PRIORITY.indexOf(b.name);
+      if (aPriority !== -1 || bPriority !== -1) {
+        return (aPriority === -1 ? 999 : aPriority) - (bPriority === -1 ? 999 : bPriority);
+      }
+      return a.name.localeCompare(b.name);
+    });
 }
 
 async function refreshPipelineArtifacts(state) {
@@ -344,9 +447,12 @@ async function findFirstExistingArtifact(projectDir, jobId, names) {
   return null;
 }
 
-async function waitForArtifact(projectDir, jobId, names, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
+async function waitForArtifact(projectDir, jobId, names, state = null, timeoutMs = PIPELINE_STEP_TIMEOUT_MS) {
   const started = Date.now();
   while (Date.now() - started < timeoutMs) {
+    if (state && !ACTIVE_PIPELINE_STATES.has(state.status)) {
+      return null;
+    }
     const artifact = await findFirstExistingArtifact(projectDir, jobId, names);
     if (artifact) {
       return artifact;
@@ -357,15 +463,21 @@ async function waitForArtifact(projectDir, jobId, names, timeoutMs = PIPELINE_ST
 }
 
 function markManualRequired(state, stepId, label) {
-  state.status = 'manual_required';
+  state.status = 'manual_review_required';
   state.finishedAt = new Date().toISOString();
   state.updatedAt = state.finishedAt;
   state.error = MANUAL_REQUIRED_MESSAGE;
-  setStep(state, stepId, label, 'manual_required', MANUAL_REQUIRED_MESSAGE);
+  state.detectedIssue = state.detectedIssue || {
+    type: 'manual_review_required',
+    window: currentTargetWindow(state),
+    summary: MANUAL_REQUIRED_MESSAGE,
+    recommendation: ISSUE_RECOMMENDATIONS.manual_review_required
+  };
+  setStep(state, stepId, label, 'manual_review_required', MANUAL_REQUIRED_MESSAGE);
 }
 
 function markTimedOutRunningStep(state) {
-  if (!['running', 'waiting_approval'].includes(state.status) || !state.currentStep) {
+  if (!ACTIVE_PIPELINE_STATES.has(state.status) || !state.currentStep) {
     return;
   }
   const running = state.steps.find((step) => step.id === state.currentStep && step.status === 'running');
@@ -379,31 +491,77 @@ function markTimedOutRunningStep(state) {
   markManualRequired(state, running.id, running.label);
 }
 
-function looksLikeApprovalPrompt(output) {
-  return /approval|approve|allow|continue|proceed|permission|승인|허용|계속|진행|거절|reject|1\)|2\)|3\)/i.test(output || '');
+function summarizeIssue(output, type) {
+  const lines = String(output || '').split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
+  const matcher = ISSUE_PATTERNS.find((item) => item.type === type);
+  if (matcher) {
+    const matched = lines.find((line) => matcher.patterns.some((pattern) => pattern.test(line)));
+    if (matched) {
+      return matched.slice(0, 220);
+    }
+  }
+  return lines.slice(-3).join(' ').slice(0, 220) || ISSUE_RECOMMENDATIONS[type] || '최근 tmux 출력에서 확인이 필요한 상태를 감지했습니다.';
+}
+
+function detectIssueFromOutput(output, windowName) {
+  const text = String(output || '');
+  for (const category of ISSUE_PATTERNS) {
+    if (category.patterns.some((pattern) => pattern.test(text))) {
+      return {
+        type: category.type,
+        window: windowName,
+        summary: summarizeIssue(text, category.type),
+        recommendation: ISSUE_RECOMMENDATIONS[category.type]
+      };
+    }
+  }
+  return null;
+}
+
+async function captureRecentTmuxOutput(windowName, lines = 120) {
+  const safeWindow = validateTmuxWindow(windowName);
+  const result = await runFile('tmux', ['capture-pane', '-p', '-S', `-${lines}`, '-t', `${SESSION}:${safeWindow}`], {
+    timeout: 10000,
+    maxBuffer: 256 * 1024
+  });
+  return result.ok ? redactedOutput(result.stdout) : '';
 }
 
-async function refreshApprovalState(state) {
-  if (!state || state.status !== 'running') {
+async function refreshDetectedIssue(state) {
+  if (!state || !ACTIVE_PIPELINE_STATES.has(state.status)) {
     return;
   }
   const targetWindow = currentTargetWindow(state);
   if (!targetWindow) {
     return;
   }
-  const result = await runFile('tmux', ['capture-pane', '-p', '-S', '-80', '-t', `${SESSION}:${targetWindow}`], {
-    timeout: 10000,
-    maxBuffer: 256 * 1024
-  });
-  if (result.ok && looksLikeApprovalPrompt(result.stdout)) {
-    state.status = 'waiting_approval';
-    state.error = MANUAL_REQUIRED_MESSAGE;
-    state.updatedAt = new Date().toISOString();
+  const output = await captureRecentTmuxOutput(targetWindow, 120);
+  const issue = detectIssueFromOutput(output, targetWindow);
+  if (!issue) {
+    return;
+  }
+
+  state.detectedIssue = issue;
+  state.error = issue.recommendation;
+  state.updatedAt = new Date().toISOString();
+
+  if (issue.type === 'blocked') {
+    state.status = 'blocked';
+    state.finishedAt = state.updatedAt;
+    setStep(state, state.currentStep, stageById(state.currentStep)?.label || state.currentStep, 'blocked', issue.summary);
+  } else if (issue.type === 'failed') {
+    state.status = 'failed';
+    state.finishedAt = state.updatedAt;
+    setStep(state, state.currentStep, stageById(state.currentStep)?.label || state.currentStep, 'failed', issue.summary);
+  } else if (issue.type === 'approval_required') {
+    state.status = 'approval_required';
+  } else if (issue.type === 'manual_review_required') {
+    markManualRequired(state, state.currentStep, stageById(state.currentStep)?.label || state.currentStep);
   }
 }
 
 async function applyArtifactProgress(state) {
-  if (!state || !['running', 'waiting_approval'].includes(state.status)) {
+  if (!state || !ACTIVE_PIPELINE_STATES.has(state.status)) {
     return;
   }
 
@@ -411,8 +569,9 @@ async function applyArtifactProgress(state) {
     const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, stage.artifacts);
     const step = state.steps.find((item) => item.id === stage.id);
     if (artifact && step && step.status === 'running') {
-      state.status = 'running';
+      state.status = stage.state;
       state.error = null;
+      state.detectedIssue = null;
       setStep(state, stage.id, stage.label, 'succeeded', artifact.name);
     }
   }
@@ -421,8 +580,9 @@ async function applyArtifactProgress(state) {
   if (current) {
     const artifact = await findFirstExistingArtifact(state.projectDir, state.jobId, current.artifacts);
     if (artifact) {
-      state.status = 'running';
+      state.status = current.state;
       state.error = null;
+      state.detectedIssue = null;
       setStep(state, current.id, current.label, 'succeeded', artifact.name);
     }
   }
@@ -480,7 +640,7 @@ async function updateGitDiffSummary(projectDir, jobId, state) {
 }
 
 async function updateReviewSummary(projectDir, jobId, state) {
-  const artifact = await findFirstExistingArtifact(projectDir, jobId, ['claude-pr-review.en.md', 'review.md']);
+  const artifact = await findFirstExistingArtifact(projectDir, jobId, ['review.md', 'claude-pr-review.en.md']);
   if (!artifact) {
     state.summary.review = { status: 'not_found', file: null, decision: null };
     return;
@@ -503,15 +663,15 @@ async function runPipeline(state, inputKo) {
     await appendPipelineLog(projectDir, jobId, 'create-job', `Ensured job directory: ${jobDir}`);
     setStep(state, 'create-job', '작업 폴더 생성', 'succeeded', jobDir);
 
-    setStep(state, 'save-input', 'input.ko.md 저장', 'running');
-    const inputPath = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'input.ko.md'));
+    setStep(state, 'save-input', 'request.ko.md 저장', 'running');
+    const inputPath = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'request.ko.md'));
     await fs.writeFile(inputPath, inputKo, 'utf8');
     await appendPipelineLog(projectDir, jobId, 'save-input', `Saved: ${inputPath}`);
-    setStep(state, 'save-input', 'input.ko.md 저장', 'succeeded', inputPath);
+    setStep(state, 'save-input', 'request.ko.md 저장', 'succeeded', inputPath);
     await refreshPipelineArtifacts(state);
 
-    for (const step of PIPELINE_STAGES.slice(0, 3)) {
-      state.status = 'running';
+    for (const step of PIPELINE_STAGES.slice(0, 2)) {
+      state.status = step.state;
       state.error = null;
       setStep(state, step.id, step.label, 'running');
       const sent = await sendToWindow(step.role, projectDir, jobId, inputKo);
@@ -519,24 +679,28 @@ async function runPipeline(state, inputKo) {
       if (!sent.ok) {
         throw new Error(`${step.label} 실패: ${sent.message || sent.stderr || 'tmux 전송 실패'}`);
       }
-      const artifact = await waitForArtifact(projectDir, jobId, step.artifacts);
+      const artifact = await waitForArtifact(projectDir, jobId, step.artifacts, state);
+      if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
+        return;
+      }
       if (!artifact) {
         markManualRequired(state, step.id, step.label);
         await refreshPipelineArtifacts(state);
         return;
       }
-      state.status = 'running';
+      state.status = step.state;
       state.error = null;
+      state.detectedIssue = null;
       setStep(state, step.id, step.label, 'succeeded', artifact.name);
       await refreshPipelineArtifacts(state);
 
-      if (step.id === 'codex') {
+      if (step.id === 'codex-implement') {
         const denied = (await changedFiles(projectDir)).filter(isDeniedSafetyPath);
         if (denied.length > 0) {
-          state.status = 'blocked_safety';
+          state.status = 'blocked';
           state.finishedAt = new Date().toISOString();
           state.error = `안전 차단 경로 변경 감지: ${denied.join(', ')}`;
-          setStep(state, 'safety-check', '안전 경로 확인', 'blocked_safety', state.error);
+          setStep(state, 'safety-check', '안전 경로 확인', 'blocked', state.error);
           await appendPipelineLog(projectDir, jobId, 'safety-check', state.error);
           await refreshPipelineArtifacts(state);
           return;
@@ -550,24 +714,28 @@ async function runPipeline(state, inputKo) {
     setStep(state, 'save-diff', 'git diff 저장', 'succeeded', state.summary.gitDiff.saved ? 'local-diff.patch' : '변경 없음');
     await refreshPipelineArtifacts(state);
 
-    const reviewerStep = PIPELINE_STAGES[3];
-    state.status = 'running';
+    const reviewerStep = PIPELINE_STAGES[2];
+    state.status = reviewerStep.state;
     state.error = null;
     setStep(state, reviewerStep.id, reviewerStep.label, 'running');
     const reviewed = await sendToWindow(reviewerStep.role, projectDir, jobId, inputKo);
-    await appendPipelineLog(projectDir, jobId, 'claude-reviewer', `${reviewed.stdout || ''}${reviewed.stderr || ''}${reviewed.message || ''}`);
+    await appendPipelineLog(projectDir, jobId, 'claude-review', `${reviewed.stdout || ''}${reviewed.stderr || ''}${reviewed.message || ''}`);
     if (!reviewed.ok) {
-      throw new Error(`Claude Reviewer 전송 실패: ${reviewed.message || reviewed.stderr || 'tmux 전송 실패'}`);
+      throw new Error(`Claude 리뷰 전송 실패: ${reviewed.message || reviewed.stderr || 'tmux 전송 실패'}`);
+    }
+    const reviewArtifact = await waitForArtifact(projectDir, jobId, reviewerStep.artifacts, state);
+    if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
+      return;
     }
-    const reviewArtifact = await waitForArtifact(projectDir, jobId, reviewerStep.artifacts);
     if (!reviewArtifact) {
       markManualRequired(state, reviewerStep.id, reviewerStep.label);
       await updateReviewSummary(projectDir, jobId, state);
       await refreshPipelineArtifacts(state);
       return;
     }
-    state.status = 'running';
+    state.status = reviewerStep.state;
     state.error = null;
+    state.detectedIssue = null;
     setStep(state, reviewerStep.id, reviewerStep.label, 'succeeded', reviewArtifact.name);
     await updateReviewSummary(projectDir, jobId, state);
     await refreshPipelineArtifacts(state);
@@ -598,41 +766,42 @@ function buildPrompt(role, projectDir, jobId, inputKo) {
     `Job directory: ${jobDir}`
   ].join('\n');
 
-  if (role === 'gemini') {
+  if (role === 'claude-plan') {
     return [
-      'Use prompts/gemini-manager.md.',
+      'Use prompts/claude.md.',
       common,
       '',
-      'Read the Korean job input below and write the English plan into the job directory.',
+      `Read docs/ai/CLAUDE_CODEX_WORKFLOW.md and ${path.join(jobDir, 'request.ko.md')}.`,
+      `Create the implementation plan in ${path.join(jobDir, 'plan.md')} and the Codex task in ${path.join(jobDir, 'codex-task.md')}.`,
+      'Use the Claude planning output format from prompts/claude.md. Do not commit, push, merge, deploy, or touch secrets.',
       '',
-      inputKo || `(Read from ${path.join(jobDir, 'input.ko.md')})`
+      inputKo || `(Read from ${path.join(jobDir, 'request.ko.md')})`
     ].join('\n');
   }
 
-  if (role === 'claude-architect') {
+  if (role === 'codex-implement') {
     return [
-      'Use prompts/claude-architect.md.',
+      'Use prompts/codex-implementer.md.',
       common,
       '',
-      'Review the plan and write the architecture review into the job directory. Only approve if the design is safe and scoped.'
+      `Read ${path.join(jobDir, 'plan.md')} and ${path.join(jobDir, 'codex-task.md')}. Use ${path.join(jobDir, 'request.ko.md')} as scope context only.`,
+      `Implement only the approved job scope, run applicable checks, and write ${path.join(jobDir, 'patch.md')}.`,
+      'Do not commit, push, merge, deploy, or change secrets, .env, auth, payment, production infra, or database migrations.'
     ].join('\n');
   }
 
-  if (role === 'codex') {
+  if (role === 'claude-review') {
     return [
-      'Use prompts/codex-implementer.md.',
+      'Use prompts/claude.md.',
       common,
       '',
-      'Implement only the approved job scope. Do not commit, push, merge, or change secrets, .env, auth, payment, production infra, or database migrations.'
+      `Review the git diff saved at ${path.join(jobDir, 'local-diff.patch')} when present, ${path.join(jobDir, 'patch.md')}, and the approved request/plan.`,
+      `Write the review into ${path.join(jobDir, 'review.md')} using the Claude review output format.`,
+      'Do not commit, push, merge, deploy, or run arbitrary shell commands.'
     ].join('\n');
   }
 
-  return [
-    'Use prompts/claude-reviewer.md.',
-    common,
-    '',
-    'Review the current diff for this job and write the review into the job directory. Do not commit, push, or merge.'
-  ].join('\n');
+  throw new Error('허용되지 않은 대상입니다.');
 }
 
 async function sendToWindow(role, projectDir, jobId, inputKo) {
@@ -655,7 +824,7 @@ async function sendToWindow(role, projectDir, jobId, inputKo) {
 }
 
 async function sendKeysToWindow(windowName, keys) {
-  const safeWindow = validateTmuxWindow(windowName);
+  const safeWindow = validateAiTmuxWindow(windowName);
   return runFile('tmux', ['send-keys', '-t', `${SESSION}:${safeWindow}`, ...keys]);
 }
 
@@ -668,6 +837,48 @@ function shellQuote(value) {
   return `'${String(value).replace(/'/g, `'\\''`)}'`;
 }
 
+function buildGuiRestartScript() {
+  const quotedLog = shellQuote(GUI_RESTART_LOG);
+  const quotedWebDir = shellQuote(WEB_DIR);
+  const quotedSession = shellQuote(GUI_SESSION);
+  const npmCommand = `env HOST=0.0.0.0 PORT=3100 npm start >> ${quotedLog} 2>&1`;
+  return [
+    `LOG=${quotedLog}`,
+    `echo "===== GUI restart requested: $(date -Is) =====" >> "$LOG"`,
+    'sleep 1',
+    `echo "[1] kill old tmux session ${GUI_SESSION}" >> "$LOG"`,
+    `tmux kill-session -t ${quotedSession} >> "$LOG" 2>&1 || true`,
+    'echo "[2] free port 3100" >> "$LOG"',
+    'if command -v fuser >/dev/null 2>&1; then',
+    '  fuser -k 3100/tcp >> "$LOG" 2>&1 || true',
+    'elif command -v lsof >/dev/null 2>&1; then',
+    '  pids="$(lsof -ti tcp:3100 2>>"$LOG" || true)"',
+    '  if [ -n "$pids" ]; then kill $pids >> "$LOG" 2>&1 || true; fi',
+    'else',
+    '  echo "No fuser or lsof available; port cleanup skipped." >> "$LOG"',
+    'fi',
+    'sleep 1',
+    `echo "[3] create tmux session ${GUI_SESSION}" >> "$LOG"`,
+    `tmux new-session -d -s ${quotedSession} -c ${quotedWebDir} ${shellQuote(npmCommand)} >> "$LOG" 2>&1`,
+    'status=$?',
+    'echo "[4] tmux session creation result: $status" >> "$LOG"',
+    'sleep 2',
+    'echo "[5] port 3100 status" >> "$LOG"',
+    '(command -v ss >/dev/null 2>&1 && ss -ltnp "sport = :3100" >> "$LOG" 2>&1) || true',
+    'echo "===== GUI restart script finished: $(date -Is) =====" >> "$LOG"'
+  ].join('\n');
+}
+
+function scheduleGuiRestart() {
+  const child = spawn('sh', ['-lc', buildGuiRestartScript()], {
+    detached: true,
+    stdio: 'ignore',
+    cwd: ROOT_DIR,
+    env: { ...process.env, TERM: process.env.TERM || 'xterm-256color' }
+  });
+  child.unref();
+}
+
 function handleError(res, error) {
   res.status(400).json({ ok: false, error: error.message || '요청을 처리할 수 없습니다.' });
 }
@@ -707,7 +918,7 @@ app.post('/api/save-input', async (req, res) => {
     const jobId = validateJobId(req.body.jobId);
     const inputKo = typeof req.body.inputKo === 'string' ? req.body.inputKo : '';
     const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
-    const target = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'input.ko.md'));
+    const target = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'request.ko.md'));
     await fs.mkdir(jobDir, { recursive: true });
     await fs.writeFile(target, inputKo, 'utf8');
     res.json({ ok: true, output: `저장됨: ${target}` });
@@ -723,13 +934,13 @@ app.post('/api/pipeline/run', async (req, res) => {
     const inputKo = typeof req.body.inputKo === 'string' ? req.body.inputKo : '';
     const key = pipelineKey(projectDir, jobId);
     const existing = pipelineStates.get(key);
-    if (existing && existing.status === 'running') {
+    if (existing && ACTIVE_PIPELINE_STATES.has(existing.status)) {
       res.status(409).json({ ok: false, error: '이 작업의 파이프라인이 이미 실행 중입니다.' });
       return;
     }
 
     const jobDir = path.join(projectDir, 'docs', 'ai', 'jobs', jobId);
-    const inputPath = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'input.ko.md'));
+    const inputPath = resolveInside(projectDir, path.join('docs', 'ai', 'jobs', jobId, 'request.ko.md'));
     await fs.mkdir(jobDir, { recursive: true });
     await fs.writeFile(inputPath, inputKo, 'utf8');
 
@@ -742,8 +953,9 @@ app.post('/api/pipeline/run', async (req, res) => {
       startedAt: state.startedAt,
       status: {
         state: state.status,
-        message: '파이프라인을 시작했습니다.',
+        message: 'Claude → Codex → Claude 전체 실행을 시작했습니다.',
         step: state.currentStep,
+        detectedIssue: null,
         artifacts: [],
         gitDiff: '-',
         reviewStatus: '-'
@@ -767,6 +979,7 @@ app.post('/api/pipeline/reset', async (req, res) => {
         state: 'idle',
         message: '선택한 작업의 파이프라인 상태를 초기화했습니다.',
         step: null,
+        detectedIssue: null,
         artifacts: [],
         gitDiff: '-',
         reviewStatus: '-'
@@ -785,10 +998,10 @@ app.get('/api/pipeline/status', async (req, res) => {
     const state = pipelineStates.get(key);
     if (state) {
       await applyArtifactProgress(state);
-      await refreshApprovalState(state);
+      await refreshDetectedIssue(state);
       markTimedOutRunningStep(state);
       await refreshPipelineArtifacts(state);
-      if (state.status !== 'running') {
+      if (!ACTIVE_PIPELINE_STATES.has(state.status)) {
         await updateReviewSummary(projectDir, jobId, state);
       }
       res.json(publicPipelineState(state));
@@ -809,6 +1022,8 @@ app.get('/api/tmux/windows', async (req, res) => {
       : [];
     const windows = [...ALLOWED_TMUX_WINDOWS].map((name) => ({
       name,
+      label: TMUX_WINDOW_LABELS[name] || name,
+      aiRole: name === 'claude' || name === 'codex',
       available: existing.includes(name)
     }));
     res.json({ ok: true, windows });
@@ -895,28 +1110,21 @@ app.post('/api/service/restart-ai-team', async (req, res) => {
 
 app.post('/api/service/restart-gui', async (req, res) => {
   try {
-    const restartSession = `ai-gui-restart-${Date.now()}`;
-    const serverPath = path.join(__dirname, 'server.js');
-    const command = `sleep 1; exec node ${shellQuote(serverPath)}`;
-    const started = await runFile('tmux', ['new-session', '-d', '-s', restartSession, '-c', ROOT_DIR, command], {
-      timeout: 10000
+    res.json({
+      ok: true,
+      output: 'GUI 서버 재시작 요청 완료\n3~5초 뒤 자동 확인합니다.',
+      logPath: GUI_RESTART_LOG
     });
-    if (!started.ok) {
-      res.status(500).json(cleanOutput(started));
-      return;
-    }
-    res.json({ ok: true, output: 'GUI 서버 재시작을 예약했습니다.' });
-    setTimeout(() => process.exit(0), 250);
+    setImmediate(scheduleGuiRestart);
   } catch (error) {
     handleError(res, error);
   }
 });
 
 for (const [endpoint, role] of [
-  ['/api/send/gemini', 'gemini'],
-  ['/api/send/claude-architect', 'claude-architect'],
-  ['/api/send/codex', 'codex'],
-  ['/api/send/claude-reviewer', 'claude-reviewer']
+  ['/api/send/claude-plan', 'claude-plan'],
+  ['/api/send/codex-implement', 'codex-implement'],
+  ['/api/send/claude-review', 'claude-review']
 ]) {
   app.post(endpoint, async (req, res) => {
     try {

```

## 2026-05-14T08:05:11.476Z — claude-review

```
(no output)
```
