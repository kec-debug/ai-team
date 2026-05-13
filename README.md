# AI Dev Team Control Center

> 로컬 tmux 기반 AI 개발팀을 시작 / 종료 / 관리하기 위한 컨트롤 센터입니다.
> A control center for managing a local tmux-based AI development team.

## 팀 구성

| tmux 번호 | tmux 창 | 역할 | 하는 일 | 주요 산출물 |
|-----------|---------|------|---------|-----------|
| `0` | `gemini-manager` | Gemini Manager | 한국어 요청을 읽고 영어 작업 계획으로 정리 | `plan.en.md` |
| `1` | `claude-architect` | Claude Architect | 설계, 리스크, 테스트 전략 검토 | `architecture.md` |
| `2` | `codex-implementer` | Codex Implementer | 실제 파일 수정, 테스트 실행, 변경 요약 작성 | 코드 변경 + `patch.md` |
| `3` | `claude-reviewer` | Claude Reviewer | PR diff와 안전 규칙 준수 여부 리뷰 | `review.md` |
| `4` | `git-shell` | Git Shell | 브랜치, 커밋, PR, CI 확인을 사람이 직접 실행 | git / gh 명령 결과 |

## 빠른 시작

처음 실행한다면 아래 순서대로 진행하세요.

1. 스크립트 실행 권한을 확인합니다.

```bash
chmod +x scripts/*.sh
```

2. AI 팀 tmux 세션을 시작합니다. 인자를 생략하면 현재 디렉터리를 작업 디렉터리로 사용합니다.

```bash
./scripts/start-ai-team.sh
```

작업할 프로젝트가 다른 위치에 있으면 경로를 전달합니다.

```bash
./scripts/start-ai-team.sh ~/projects/my-app
```

3. 실제 작업 폴더를 만듭니다.

```bash
./scripts/create-job.sh ~/projects/my-app job-001
```

이 명령은 실제 작업 파일을 `docs/ai/jobs/<JOB_ID>/` 아래에 만듭니다. 예를 들어 `job-001`이면 `docs/ai/jobs/job-001/input.ko.md`를 작성합니다.

4. `gemini-manager` 창에서 `input.ko.md`를 바탕으로 계획을 만들고, 이후 `claude-architect` → `codex-implementer` → `claude-reviewer` 순서로 진행합니다.

5. 세션 상태를 확인하거나 종료할 수 있습니다.

```bash
./scripts/status-ai-team.sh
./scripts/stop-ai-team.sh
```

> **tmux 창 이동**
> `Ctrl-b`를 누른 뒤 손을 떼고 숫자를 누릅니다.
> 예: `Ctrl-b` 다음 `0` = `gemini-manager`, `Ctrl-b` 다음 `2` = `codex-implementer`.
> 분리(detach)는 `Ctrl-b` 다음 `d`입니다. 다시 붙으려면 `tmux attach -t ai-team`을 실행하세요.

## 워크플로 한 줄 요약

한국어 입력 → Gemini 영어 계획 → Claude 아키텍처 검토 → Codex 구현 → GitHub PR → Claude PR 리뷰 → 사람 최종 승인

자세한 내용은 다음 문서들을 참고하세요.

- [docs/setup.md](docs/setup.md) — 처음 설치 / 설정
- [docs/workflow.md](docs/workflow.md) — 단계별 작업 흐름
- [docs/safety-rules.md](docs/safety-rules.md) — 안전 규칙

## 브라우저 GUI v1

PuTTY나 tmux 직접 조작 없이 로컬 브라우저에서 AI 개발팀을 제어할 수 있는 간단한 GUI가 `web/`에 있습니다. 기본 주소는 `http://127.0.0.1:3100`이며 외부 공개용으로 만들지 않았습니다.

처음 실행할 때:

```bash
cd web
npm install
npm start
```

다른 포트나 호스트가 필요하면 환경변수로 지정합니다.

```bash
HOST=127.0.0.1 PORT=3100 npm start
```

GUI에서 할 수 있는 일:

- 프로젝트 경로, 작업 ID, 한국어 작업 요청 입력
- AI 팀 tmux 세션 상태 확인과 시작
- 작업 폴더 생성과 `input.ko.md` 저장
- **전체 파이프라인 실행** 버튼으로 작업 폴더 생성 → 입력 저장 → Gemini Manager → Claude Architect → Codex Implementer → `local-diff.patch` 저장 → Claude Reviewer 순서 진행
- 파이프라인 현재 단계, 성공 / 실패 / 수동 개입 필요 상태 확인
- 선택한 프로젝트 경로와 작업 ID 기준으로 파이프라인 상태 확인 및 `파이프라인 상태 초기화`
- 실시간 tmux 출력 확인, 승인 / 세션 승인 / 거절 / 중단 키 입력 전송
- AI팀 재시작과 GUI 서버 재시작
- 생성된 산출물, git diff 저장 상태, Reviewer decision 요약 확인
- Gemini Manager, Claude Architect, Codex Implementer, Claude Reviewer 창으로 정해진 프롬프트 전송
- `git status`, `git diff` 확인
- `docs/ai/jobs/<JOB_ID>/` 아래 산출물 파일 확인

`전체 파이프라인 실행`은 브라우저 요청을 오래 붙잡지 않습니다. 서버가 메모리에 작업 상태를 만들고 백그라운드에서 안전한 고정 단계만 실행하며, GUI는 `GET /api/pipeline/status`로 상태를 폴링합니다. 서버를 재시작하면 이 메모리 상태는 사라집니다. 이미 tmux 창에 전달된 작업은 계속 진행될 수 있으므로, 재시작 후에는 tmux와 산출물 파일을 직접 확인하세요.

GUI는 임의 shell command 입력을 제공하지 않습니다. 서버는 허용된 스크립트, 고정 tmux 창, 고정 git 조회 명령만 실행합니다. 승인 버튼도 allowlist에 있는 tmux 창에 정해진 키만 보냅니다. 파이프라인도 `commit`, `push`, PR 생성, merge, 배포를 자동 실행하지 않습니다. 최종 변경 확인, 커밋, 푸시, PR 생성, merge 승인은 사람이 `git-shell` 창과 GitHub에서 직접 처리해야 합니다. 자동 merge는 안전상 제공하지 않습니다.

AI 도구가 중간 승인을 요구하거나 제한 시간 안에 예상 산출물을 만들지 못하면 GUI는 해당 단계를 `manual_required`로 표시합니다. 이 경우 사람이 해당 tmux 창에서 진행 상황을 확인하고 수동으로 이어가야 합니다.

## 체크리스트: push 전 확인

- `git-shell` 창에서 `git status`와 `git diff`로 변경 파일을 확인합니다.
- 변경이 현재 작업 범위에만 있는지 확인합니다.
- `scripts/`, 비밀 정보, 인증, 결제, DB 마이그레이션, 운영 인프라가 의도치 않게 바뀌지 않았는지 확인합니다.
- `main`에 직접 push하지 말고 작업 브랜치에서 PR로 진행합니다.
- Codex 구현 요약과 Claude Reviewer 리뷰 결과를 확인합니다.
- 전체 규칙은 [docs/safety-rules.md](docs/safety-rules.md), 단계별 흐름은 [docs/workflow.md](docs/workflow.md)를 봅니다.

## 역할 프롬프트

각 AI 역할이 어떻게 행동해야 하는지는 `prompts/` 안에 있습니다. 필요하면 각 창에서 해당 파일을 열어 그대로 시스템 프롬프트로 사용하세요.

- [prompts/gemini-manager.md](prompts/gemini-manager.md)
- [prompts/claude-architect.md](prompts/claude-architect.md)
- [prompts/codex-implementer.md](prompts/codex-implementer.md)
- [prompts/claude-reviewer.md](prompts/claude-reviewer.md)

## 안전 규칙 (요약)

- 비밀 / 자격 증명 / `.env`는 저장소에 두지 않습니다.
- `main` 브랜치에 직접 푸시하지 않습니다.
- 자동 머지하지 않습니다 — 머지는 사람이 합니다.
- 인증 / 결제 / DB 마이그레이션 / 운영 인프라는 사람 승인 없이 변경하지 않습니다.

전체 규칙: [docs/safety-rules.md](docs/safety-rules.md)

## 별칭(alias)

`scripts/ai-team-aliases.sh`를 `source` 하면 짧은 명령으로 쓸 수 있습니다.

```bash
source ./scripts/ai-team-aliases.sh
# 이후:
ai-team                      # 시작 (현재 디렉터리)
ai-team /path/to/project     # 시작 (프로젝트 경로 전달)
ai-attach                    # 다시 붙기
ai-status                    # 상태
ai-stop                      # 종료
ai-job <PROJECT> <ID>        # 작업 폴더 만들기
```

> **이 저장소는 `~/.bashrc`를 자동으로 수정하지 않습니다.** 영구 등록은 직접 `~/.bashrc` 또는 `~/.zshrc`에 `source` 한 줄을 추가하세요.

## 예시

`examples/job-001/input.ko.md`는 참고용 예시입니다. 실제 작업은 `./scripts/create-job.sh <PROJECT_DIR> <JOB_ID>`로 만들고, 생성된 `docs/ai/jobs/<JOB_ID>/input.ko.md`에 요청을 작성하세요.

## 디렉터리 구조

```
.
├── README.md
├── prompts/
│   ├── gemini-manager.md
│   ├── claude-architect.md
│   ├── codex-implementer.md
│   └── claude-reviewer.md
├── scripts/
│   ├── start-ai-team.sh
│   ├── status-ai-team.sh
│   ├── stop-ai-team.sh
│   ├── create-job.sh
│   └── ai-team-aliases.sh
├── docs/
│   ├── setup.md
│   ├── workflow.md
│   └── safety-rules.md
└── examples/
    └── job-001/
        └── input.ko.md
```
