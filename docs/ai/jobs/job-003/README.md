# Job: job-003

이 폴더는 AI 팀이 처리하는 작업 단위 하나입니다. 한 작업 = 한 폴더 = 한 PR.

## 단계별 산출 파일
1. `input.ko.md` — 사람이 한국어로 작성한 요청서 (지금 작성해야 함)
2. `plan.en.md` — Gemini Manager가 영어로 정리한 작업 계획 (다음 단계)
3. `architecture.md` — Claude Architect의 설계 / 리스크 / 테스트 전략
4. `patch.md` — Codex Implementer의 변경 요약과 PR 링크
5. `review.md` — Claude Reviewer의 PR 리뷰 결과

## 워크플로
1. `input.ko.md`를 끝까지 채워 넣습니다.
2. AI 팀 tmux 세션을 시작합니다: `./scripts/start-ai-team.sh <이 프로젝트 경로>`.
3. **gemini-manager** 창에서 `input.ko.md` 내용을 붙여 넣어 영어 계획(`plan.en.md`)을 만들도록 요청합니다.
4. **claude-architect** 창에서 계획을 검토받고 `architecture.md`를 받습니다. 검토 결과가 `APPROVE`일 때만 다음 단계로.
5. **codex-implementer** 창에서 구현을 진행하고 `patch.md`로 정리합니다.
6. **git-shell** 창에서 사람이 직접 브랜치 생성 / 커밋 / 푸시 / PR 생성을 실행합니다.
7. **claude-reviewer** 창에서 PR 리뷰를 받고 `review.md`로 저장합니다.
8. 사람이 최종 승인 후 머지합니다.

## 금지 사항 (이 작업에서도 동일)
- 자동 커밋 / 자동 푸시 / 자동 머지 금지
- `.env`, 비밀 키, 인증, 결제, DB 마이그레이션, 운영 인프라 변경 금지 (사람 승인 시에만)
- `main` 직접 푸시 금지
