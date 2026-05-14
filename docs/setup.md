# 설치 및 설정 가이드 (Setup)

이 저장소는 로컬 Claude + Codex 작업 흐름을 시작 / 종료 / 관리하는 컨트롤 센터입니다. 처음 사용한다면 아래 순서대로 따라 해주세요.

## 1. 필요한 도구

다음 명령이 모두 동작해야 합니다. 한 줄씩 실행해서 버전이 나오는지 확인하세요.

```bash
tmux -V
git --version
gh --version       # GitHub CLI
claude --version   # Anthropic Claude CLI
codex --version    # Codex CLI
```

없는 도구가 있다면 각 도구의 **공식 설치 가이드**를 참고해서 먼저 설치해주세요.
이 저장소는 패키지를 자동 설치하지 않으며, `sudo`도 사용하지 않습니다.

## 2. 저장소 가져오기

```bash
git clone <your-fork-url> ai-team
cd ai-team
```

## 3. 스크립트 실행 권한 확인

```bash
ls -l scripts/*.sh
```

만약 `x`(실행) 권한이 없다면:

```bash
chmod +x scripts/*.sh
```

## 4. 별칭(alias) 등록 — 선택 사항

매번 긴 경로를 치기 싫다면 alias를 등록할 수 있습니다.

### 한 번만 쓸 때 (현재 셸에만 적용)

```bash
source ./scripts/ai-team-aliases.sh
```

### 영구 등록 (직접 추가해주세요)

`~/.bashrc` 또는 `~/.zshrc`에 아래 줄을 **직접** 추가하세요.
**이 저장소는 `~/.bashrc`를 자동으로 수정하지 않습니다.**

```bash
source /절대/경로/ai-team/scripts/ai-team-aliases.sh
```

등록되는 alias:

| alias | 동작 |
|-------|------|
| `ai-team [PROJECT_DIR]` | Claude + Codex tmux 세션 시작 (이미 있으면 attach) |
| `ai-attach` | 실행 중인 세션에 다시 붙기 |
| `ai-status` | 세션 상태 확인 |
| `ai-stop` | 세션 종료 (확인 후) |
| `ai-job PROJECT_DIR JOB_ID` | 새 Claude + Codex 작업 폴더 생성 |

## 5. 첫 실행

작업할 프로젝트 디렉터리에서 실행하거나, 인자로 경로를 직접 넘길 수 있습니다.

```bash
# 방법 A — 현재 디렉터리를 작업 디렉터리로 사용
cd ~/projects/내가-작업할-앱
~/ai-team/scripts/start-ai-team.sh

# 방법 B — 경로를 인자로 전달
~/ai-team/scripts/start-ai-team.sh ~/projects/내가-작업할-앱
```

tmux가 켜지면:

- `Ctrl-b` 누르고 숫자(0~4) — 창 전환
- `Ctrl-b` 누르고 `d` — 세션에서 분리(detach), 백그라운드 유지
- `tmux attach -t ai-team` — 다시 붙기

## 6. 첫 작업 만들기

```bash
./scripts/create-job.sh ~/projects/내가-작업할-앱 job-001
```

생기는 위치: `~/projects/내가-작업할-앱/docs/ai/jobs/job-001/`

그 안의 `input.ko.md`를 채워 넣은 뒤 AI 팀 작업을 시작합니다.

## 7. 자주 묻는 질문

**Q. 세션이 이미 떠 있는데 다시 시작하면 어떻게 되나요?**
A. `start-ai-team.sh`는 idempotent입니다. 이미 있으면 새로 만들지 않고 attach만 합니다.

**Q. 어느 창에서 어떤 AI가 뜨나요?**
A. 창 1 = gemini, 창 2 = claude (architect), 창 3 = codex, 창 4 = claude (reviewer), 창 5 = 일반 셸.

**Q. AI 도구 중 하나가 설치되어 있지 않으면?**
A. 해당 창에 경고 메시지가 뜨고 일반 셸이 남습니다. 다른 창은 정상 동작합니다.
