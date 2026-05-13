#!/usr/bin/env bash
# Create a new job folder inside a target project.
#
# Usage:
#   ./scripts/create-job.sh PROJECT_DIR JOB_ID
#
# Creates: PROJECT_DIR/docs/ai/jobs/JOB_ID/
#   - input.ko.md  (Korean task template the human fills in)
#   - README.md    (workflow guide for this job)
#
# Does NOT modify any source code in PROJECT_DIR.

set -euo pipefail

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 PROJECT_DIR JOB_ID"
    echo "Example: $0 ~/projects/my-app job-001"
    exit 1
fi

PROJECT_DIR_INPUT="$1"
JOB_ID="$2"

if [ ! -d "$PROJECT_DIR_INPUT" ]; then
    echo "Error: project directory '$PROJECT_DIR_INPUT' does not exist." >&2
    exit 1
fi

PROJECT_DIR="$(cd "$PROJECT_DIR_INPUT" && pwd)"
JOB_DIR="$PROJECT_DIR/docs/ai/jobs/$JOB_ID"

if [ -e "$JOB_DIR" ]; then
    echo "Error: job directory already exists: $JOB_DIR" >&2
    echo "Pick a different JOB_ID or remove the existing directory first." >&2
    exit 1
fi

mkdir -p "$JOB_DIR"

# -----------------------------------------------------------------------------
# input.ko.md — Korean task template (no variable substitution needed)
# -----------------------------------------------------------------------------
cat > "$JOB_DIR/input.ko.md" <<'EOF'
# 작업 입력 (Job Input)

## 한 줄 요약
> 무엇을 만들거나 고치고 싶은지 한 문장으로 적어주세요.

(예시: "로그인 페이지에 비밀번호 표시/숨기기 토글 버튼을 추가하고 싶어요.")

## 배경 (Why)
- 왜 이 작업이 필요한가요?
- 누가 이 기능을 사용하나요?
- 지금은 어떻게 동작하고 있나요?

## 목표 (Done 정의)
- [ ] 목표 1
- [ ] 목표 2
- [ ] 목표 3

## 범위 밖 (Not in scope)
- 이번 작업에서 다루지 않을 항목을 적어주세요.
- (예: "회원가입 페이지 디자인 변경은 별도 작업으로 분리")

## 제약 조건
- 이 작업에서는 다음 영역을 절대 변경하지 않습니다:
  - `.env`, 비밀 키, 자격 증명, API 키, 토큰
  - 인증 / 로그인 / 세션 / 비밀번호 처리 코드
  - 결제 / 빌링 / 구독 로직
  - 데이터베이스 마이그레이션 파일
  - 운영(prod) 인프라
- `main` 브랜치 직접 푸시 금지.
- 자동 머지 금지 — 사람이 직접 머지합니다.

## 참고 자료
- 관련 파일 / 함수 / URL:
- 스크린샷 / 디자인 시안:
- 관련 이슈 / PR 번호:

## 수용 기준 (Acceptance Criteria)
- [ ] 조건 1 — 어떤 입력에 어떤 출력이 나오면 성공인지 구체적으로 적어주세요.
- [ ] 조건 2
- [ ] 모든 기존 테스트가 통과해야 합니다.
- [ ] 새 테스트가 추가되어 있어야 합니다.
EOF

# -----------------------------------------------------------------------------
# README.md — workflow guide (needs JOB_ID substituted)
# -----------------------------------------------------------------------------
cat > "$JOB_DIR/README.md" <<EOF
# Job: $JOB_ID

이 폴더는 AI 팀이 처리하는 작업 단위 하나입니다. 한 작업 = 한 폴더 = 한 PR.

## 단계별 산출 파일
1. \`input.ko.md\` — 사람이 한국어로 작성한 요청서 (지금 작성해야 함)
2. \`plan.en.md\` — Gemini Manager가 영어로 정리한 작업 계획 (다음 단계)
3. \`architecture.md\` — Claude Architect의 설계 / 리스크 / 테스트 전략
4. \`patch.md\` — Codex Implementer의 변경 요약과 PR 링크
5. \`review.md\` — Claude Reviewer의 PR 리뷰 결과

## 워크플로
1. \`input.ko.md\`를 끝까지 채워 넣습니다.
2. AI 팀 tmux 세션을 시작합니다: \`./scripts/start-ai-team.sh <이 프로젝트 경로>\`.
3. **gemini-manager** 창에서 \`input.ko.md\` 내용을 붙여 넣어 영어 계획(\`plan.en.md\`)을 만들도록 요청합니다.
4. **claude-architect** 창에서 계획을 검토받고 \`architecture.md\`를 받습니다. 검토 결과가 \`APPROVE\`일 때만 다음 단계로.
5. **codex-implementer** 창에서 구현을 진행하고 \`patch.md\`로 정리합니다.
6. **git-shell** 창에서 사람이 직접 브랜치 생성 / 커밋 / 푸시 / PR 생성을 실행합니다.
7. **claude-reviewer** 창에서 PR 리뷰를 받고 \`review.md\`로 저장합니다.
8. 사람이 최종 승인 후 머지합니다.

## 금지 사항 (이 작업에서도 동일)
- 자동 커밋 / 자동 푸시 / 자동 머지 금지
- \`.env\`, 비밀 키, 인증, 결제, DB 마이그레이션, 운영 인프라 변경 금지 (사람 승인 시에만)
- \`main\` 직접 푸시 금지
EOF

echo "Created job at: $JOB_DIR"
echo
echo "Files:"
ls -la "$JOB_DIR"
echo
echo "Next steps:"
echo "  1. Edit:  $JOB_DIR/input.ko.md"
echo "  2. Start: ./scripts/start-ai-team.sh $PROJECT_DIR"
