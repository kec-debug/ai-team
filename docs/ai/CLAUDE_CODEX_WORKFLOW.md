# Claude + Codex 워크플로

이 문서는 AI 작업 파이프라인의 기본 운영 방식입니다. 이전의 여러 역할 기반 흐름은 초보자가 창과 산출물을 계속 추적해야 해서 부담이 컸습니다. 이제 AI 역할은 Claude와 Codex 두 개만 사용합니다. tmux에는 사람이 직접 git/test 명령을 실행하는 비AI `git-shell` 창을 함께 둘 수 있습니다.

## 왜 단순화했나

기존 파이프라인은 역할이 많아 설계, 구현, 리뷰의 책임은 분명했지만 실제 사용이 복잡했습니다. 사용자는 매번 여러 tmux 창을 오가며 `gemini-manager`, `claude-architect`, `codex-implementer`, `claude-reviewer`, `git-shell`의 순서를 기억해야 했습니다.

새 방식은 같은 안전 규칙을 유지하면서 작업 흐름을 다음 하나로 고정합니다.

1. 사용자가 한국어 요청을 쓴다.
2. Claude가 구현 계획으로 정리한다.
3. Codex가 구현하고 테스트한다.
4. Claude가 diff를 리뷰한다.
5. 필요한 git/test/commit/PR 명령은 사용자가 Manual Shell 또는 별도 터미널에서 직접 실행한다.

## 이전 5역할 워크플로

이전 구조는 deprecated 되었습니다.

| 이전 역할 | 상태 | 새 역할 |
| --- | --- | --- |
| `gemini-manager` | deprecated | Claude가 한국어 요청 해석과 계획 작성 |
| `claude-architect` | deprecated | Claude로 통합 |
| `codex-implementer` | 유지 | Codex |
| `claude-reviewer` | deprecated | Claude로 통합 |
| `git-shell` | AI 역할 아님 | Manual Shell 또는 사람이 직접 터미널에서 실행 |

## 새 역할 모델

| 역할 | 책임 | 산출물 |
| --- | --- | --- |
| Claude | 요청 정리, 설계, 리스크 점검, 리뷰 | `plan.md`, `review.md` |
| Codex | 구현, 테스트, 패치 요약 | 코드 변경, `patch.md` |
| Manual Shell (`git-shell`) | 사람이 직접 `git status`, `git diff`, 테스트, commit/PR 명령 실행 | 수동 확인과 수동 git 작업 |

## Claude 역할

Claude는 Planner, Architect, Reviewer, Risk Checker, Korean request interpreter입니다.

- 한국어 요청을 읽고 모호한 점을 정리합니다.
- 구현 범위와 수정 파일 후보를 명확히 합니다.
- Codex에게 전달할 구현 지시문을 만듭니다.
- 테스트 기준과 리뷰 체크리스트를 작성합니다.
- Codex 구현 후 diff를 검토하고 `APPROVE`, `REQUEST CHANGES`, `BLOCK` 중 하나로 리뷰합니다.
- 명시적으로 요청받지 않는 한 큰 패치를 직접 구현하지 않습니다.

## Codex 역할

Codex는 Implementer입니다.

- 승인된 job scope만 읽고 구현합니다.
- 관련 파일만 수정합니다.
- 필요한 테스트를 추가하거나 갱신합니다.
- 가능한 경우 아래 검사를 실행합니다.

```bash
python -m compileall app tests
python -m pytest -p no:cacheprovider
```

- 결과를 `patch.md`에 요약합니다.
- commit, push, merge, PR merge를 하지 않습니다.

## Human 역할

사람은 최종 책임자입니다.

- 한국어 요청을 작성합니다.
- Claude 계획을 읽고 범위를 확인합니다.
- Codex 결과와 Claude 리뷰를 확인합니다.
- Manual Shell 또는 별도 터미널에서 `git status`, `git diff`, 테스트, `git add`, `git commit`, `git push`, `gh pr create`, merge를 필요할 때 직접 실행합니다.

## Job 디렉터리 구조

모든 작업은 `docs/ai/jobs/{JOB_ID}/` 아래에서 진행합니다.

```text
docs/ai/jobs/{JOB_ID}/
├── request.ko.md   # 사용자의 원본 한국어 요청
├── plan.md         # Claude의 구현 계획
├── codex-task.md   # Codex에게 전달할 최종 작업 지시문
├── patch.md        # Codex의 구현 요약과 테스트 결과
├── review.md       # Claude의 리뷰 결과
└── status.md       # 현재 작업 상태
```

## 새 작업 시작하기

권장 방법:

```bash
./scripts/create-job.sh /path/to/project JOB_ID
```

예시:

```bash
./scripts/create-job.sh /root/ai-dev-center/projects/ai-team mvp-001
```

이 스크립트는 `docs/ai/jobs/_template/`의 파일을 새 job 폴더로 복사합니다. 기존 파일은 덮어쓰지 않습니다. 의도적으로 다시 만들 때만 `--force`를 붙입니다.

```bash
./scripts/create-job.sh /path/to/project JOB_ID --force
```

수동으로 만들 때:

```bash
mkdir -p docs/ai/jobs/JOB_ID
cp docs/ai/jobs/_template/* docs/ai/jobs/JOB_ID/
```

## Claude에게 요청하는 방법

1. `docs/ai/jobs/{JOB_ID}/request.ko.md`에 한국어 요청을 작성합니다.
2. Claude에 `prompts/claude.md`를 적용합니다.
3. Claude에게 job 폴더와 요청 파일을 알려줍니다.
4. Claude 결과를 `docs/ai/jobs/{JOB_ID}/plan.md`에 저장합니다.
5. Claude가 만든 Codex 구현 지시문을 `codex-task.md`에 저장합니다.

## Codex에게 요청하는 방법

1. Codex에 `prompts/codex-implementer.md`를 적용합니다.
2. Codex에게 job scope, `plan.md`, `codex-task.md`를 읽게 합니다.
3. Codex는 구현, 테스트, 패치 요약까지만 수행합니다.
4. Codex 결과를 `docs/ai/jobs/{JOB_ID}/patch.md`에 저장합니다.

## 브라우저 GUI

GUI 기본 주소는 `http://127.0.0.1:3100`입니다. 외부 공개용으로 만들지 않았습니다.

메인 액션 버튼은 네 개입니다.

| 버튼 | API |
| --- | --- |
| `Claude → Codex → Claude 전체 실행` | `POST /api/pipeline/run` |
| `Claude 계획 생성` | `POST /api/send/claude-plan` |
| `Codex 구현 실행` | `POST /api/send/codex-implement` |
| `Claude 리뷰 실행` | `POST /api/send/claude-review` |

파이프라인 상태 단계는 다음 여덟 개만 사용합니다.

- `claude_planning`
- `codex_implementing`
- `claude_reviewing`
- `manual_review_required`
- `succeeded`
- `failed`
- `blocked`
- `approval_required`

tmux 기본 자동화 대상은 `ai-team:claude`, `ai-team:codex` 두 창입니다. `gemini-manager`, `claude-architect`, `claude-reviewer`, `git-shell`은 기본 자동화 대상이 아닙니다. `git-shell`은 사람이 직접 git/test 명령을 실행하는 비AI 보조 창입니다.

수동 유틸리티 버튼은 `git status`, `git diff` 두 개입니다. GUI는 자동 `commit`, `push`, `merge`, `deploy`를 제공하지 않습니다. 임의 shell 명령 입력 기능도 제공하지 않습니다.

절대 자동화하지 않는 것:

- `commit`
- `push`
- PR merge
- production 배포
- `.env`, secrets, auth, payment, production infra, database migrations 변경

## 결과 리뷰 방법

1. 사용자가 `git status`와 `git diff`로 변경 범위를 확인합니다.
2. Claude에 `prompts/claude.md`를 적용하고 diff와 `patch.md`를 전달합니다.
3. Claude는 `docs/ai/jobs/{JOB_ID}/review.md`에 리뷰 결과를 작성합니다.
4. `REQUEST CHANGES` 또는 `BLOCK`이면 Codex에게 수정 작업을 다시 요청합니다.
5. `APPROVE`여도 commit, push, merge는 사람이 직접 실행합니다.

## 안전 규칙

- Paper trading이 기본입니다.
- Live trading은 기본 비활성화입니다.
- Live trading은 명시적 validation, preflight, arming, guard check가 모두 필요합니다.
- LLM은 절대 직접 주문을 넣지 않습니다.
- 추천 agent는 non-executable order intent만 만들 수 있습니다.
- Executable broker order는 OMS만 만들 수 있습니다.
- 모든 주문은 Strategy -> Risk Engine -> OMS 순서를 반드시 통과해야 합니다.
- RiskEngine을 우회하면 안 됩니다.
- Broker별 API 호출은 broker adapter 안에만 있어야 합니다.
- API key는 `.env`에서만 읽습니다.
- secret을 하드코딩하지 않습니다.
- vendor endpoint를 지어내지 않습니다.
- market order는 기본 비활성화입니다.
- 불확실하면 fail closed 합니다.

## 절대 자동화하지 않는 것

- `git commit`
- `git push`
- PR merge
- production 배포
- secret 또는 `.env` 수정
- auth, payment, production infrastructure 변경
- database migration 작성 또는 실행
- live trading 활성화
- broker 실주문 생성
