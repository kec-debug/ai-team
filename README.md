# AI Dev Team Control Center

> 로컬 tmux 기반 AI 개발팀을 시작 / 종료 / 관리하기 위한 컨트롤 센터입니다.
> A control center for managing a local tmux-based AI development team.

## 팀 구성

| tmux 창 | 역할 | 책임 | 실행 도구 |
|---------|------|------|-----------|
| 1. `gemini-manager` | Gemini Manager | 한국어 요청 → 영어 작업 계획 | `gemini` |
| 2. `claude-architect` | Claude Architect | 아키텍처 검토, 리스크, 테스트 전략 | `claude` |
| 3. `codex-implementer` | Codex Implementer | 실제 구현, 테스트, 패치 | `codex` |
| 4. `claude-reviewer` | Claude Reviewer | PR diff 리뷰, 품질 게이트 | `claude` |
| 5. `git-shell` | Git Shell | git / gh / 브랜치 / 커밋 / PR / CI | 일반 셸 |

## 빠른 시작

```bash
# 1) 스크립트 실행 권한 확인
chmod +x scripts/*.sh

# 2) AI 팀 시작 — 현재 디렉터리를 작업 디렉터리로 사용
./scripts/start-ai-team.sh

# 또는, 작업할 프로젝트 경로를 인자로 전달
./scripts/start-ai-team.sh ~/projects/my-app

# 3) 첫 작업 폴더 만들기
./scripts/create-job.sh ~/projects/my-app job-001

# 4) 세션 상태 확인
./scripts/status-ai-team.sh

# 5) 세션 종료
./scripts/stop-ai-team.sh
```

tmux 창 전환은 `Ctrl-b` + 숫자(0~4), 분리(detach)는 `Ctrl-b` + `d`.

## 워크플로 한 줄 요약

한국어 입력 → Gemini 영어 계획 → Claude 아키텍처 검토 → Codex 구현 → GitHub PR → Claude PR 리뷰 → 사람 최종 승인

자세한 내용은 다음 문서들을 참고하세요.

- [docs/setup.md](docs/setup.md) — 처음 설치 / 설정
- [docs/workflow.md](docs/workflow.md) — 단계별 작업 흐름
- [docs/safety-rules.md](docs/safety-rules.md) — 안전 규칙

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

`examples/job-001/input.ko.md` — 한국어 작업 요청서가 채워진 모습의 예시입니다.

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
