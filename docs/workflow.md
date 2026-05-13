# 워크플로 (Workflow)

한 작업이 한국어 요청에서 시작해 GitHub 머지까지 어떻게 흐르는지 설명합니다.

## 7 단계 파이프라인

### 1. 한국어 입력
사람이 `docs/ai/jobs/{JOB_ID}/input.ko.md`를 작성합니다.

- **무엇을** — 한 줄 요약
- **왜** — 배경과 사용자
- **어디까지** — 목표(Done 정의)와 범위 밖(Not in scope)
- **제약 조건**과 **수용 기준**

`./scripts/create-job.sh <PROJECT_DIR> <JOB_ID>`로 템플릿을 만들 수 있습니다.

### 2. Gemini 영어 계획
**gemini-manager** 창에서 `input.ko.md`를 읽고 영어 작업 계획 `plan.en.md`를 만듭니다.

- 모호한 부분은 **한국어로 사람에게 다시 질문**합니다.
- 충분한 정보가 모이면 영어 계획을 출력합니다.
- 산출물: `docs/ai/jobs/{JOB_ID}/plan.en.md`

### 3. Claude 아키텍처 검토
**claude-architect** 창에서 `plan.en.md`와 실제 코드를 함께 보고 `architecture.md`를 만듭니다.

- 영향 받는 파일, 리스크, 테스트 전략을 정리합니다.
- 마지막에 명시적 평결(`APPROVE` / `REQUEST CHANGES` / `BLOCK`)을 남깁니다.
- `APPROVE`가 아니면 2단계로 되돌아갑니다.
- 산출물: `docs/ai/jobs/{JOB_ID}/architecture.md`

### 4. Codex 구현
**codex-implementer** 창에서 계획 + 아키텍처에 따라 실제 코드를 작성합니다.

- 테스트를 함께 작성합니다.
- **자동 커밋 / 자동 푸시를 하지 않습니다.**
- 변경 요약을 `patch.md`에 남깁니다.
- 산출물: 코드 변경 + `docs/ai/jobs/{JOB_ID}/patch.md`

### 5. GitHub PR (사람이 직접)
**git-shell** 창에서 사람이 직접 실행합니다. AI는 손대지 않습니다.

```bash
git checkout -b feat/job-001-short-description
git add <변경된-파일들>
git diff --cached            # 마지막으로 한 번 확인
git commit -m "feat: ..."    # 메시지는 사람이 검토
git push -u origin HEAD
gh pr create --base main --head HEAD --title "..." --body "..."
```

### 6. Claude PR 리뷰
**claude-reviewer** 창에서 PR diff를 받아 검토합니다.

- 계획 / 아키텍처와 일치하는지, 안전 규칙을 지켰는지 확인합니다.
- 평결(`APPROVE` / `REQUEST CHANGES` / `BLOCK`)을 남깁니다.
- 산출물: `docs/ai/jobs/{JOB_ID}/review.md`

### 7. 사람 최종 승인
- 사람이 리뷰 결과를 읽고 머지 여부를 결정합니다.
- **자동 머지는 하지 않습니다.** 직접 `gh pr merge` 또는 GitHub UI에서 머지하세요.
- `gh pr merge --auto`도 사용하지 않습니다.

## 흐름 다이어그램

```
한국어 입력 (사람)
   │
   ▼
Gemini Manager  ─►  plan.en.md
   │
   ▼
Claude Architect  ─►  architecture.md   (APPROVE 시에만 진행)
   │
   ▼
Codex Implementer  ─►  코드 변경 + patch.md
   │
   ▼
Git Shell (사람)  ─►  브랜치 / 커밋 / 푸시 / PR
   │
   ▼
Claude Reviewer  ─►  review.md
   │
   ▼
사람 최종 승인  ─►  머지
```

## 각 단계 산출물 요약

| 단계 | 산출물 | 담당 | 위치 |
|------|--------|------|------|
| 1 | `input.ko.md` | 사람 | `docs/ai/jobs/{JOB_ID}/` |
| 2 | `plan.en.md` | Gemini Manager | `docs/ai/jobs/{JOB_ID}/` |
| 3 | `architecture.md` | Claude Architect | `docs/ai/jobs/{JOB_ID}/` |
| 4 | `patch.md` + 코드 | Codex Implementer | `docs/ai/jobs/{JOB_ID}/` + 소스 |
| 5 | PR | 사람 | GitHub |
| 6 | `review.md` | Claude Reviewer | `docs/ai/jobs/{JOB_ID}/` |
| 7 | 머지 커밋 | 사람 | GitHub |

## 단계 건너뛰기에 대해

- 2단계(영어 계획) 없이 바로 4단계(구현)로 가는 것은 권장하지 않습니다 — 작은 작업이라도 한 번 정리하는 과정이 사고를 줄여줍니다.
- 3단계(아키텍처 검토)는 README 수정처럼 진짜 사소한 작업에서는 "스킵 합의"를 `plan.en.md`에 적고 넘어갈 수 있습니다.
- 6단계(리뷰)는 **절대 건너뛰지 않습니다**. 사람이 직접 봐도 좋고, Claude Reviewer가 봐도 좋지만, 둘 중 하나는 반드시 합니다.
