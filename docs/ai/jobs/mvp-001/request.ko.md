# 요청 원문

## 한국어 요청

현재 AI 작업 파이프라인이 너무 복잡하다.

기존 구조:

- gemini-manager
- claude-architect
- codex-implementer
- claude-reviewer
- git-shell

새 구조:

- Claude
- Codex

Claude는 설계, 리뷰, 요구사항 정리를 담당한다.
Codex는 구현, 테스트, 패치 요약을 담당한다.

`docs/ai/jobs/{JOB_ID}` 기준의 자동 작업 폴더와 템플릿을 만들고, Claude -> Codex -> Claude Review 흐름을 단순화한다.

## 완료 기준

- [ ] `docs/ai/CLAUDE_CODEX_WORKFLOW.md` 작성
- [ ] `prompts/claude.md` 작성
- [ ] `prompts/codex-implementer.md` 단순화
- [ ] `docs/ai/jobs/_template/` 템플릿 작성
- [ ] `docs/ai/jobs/mvp-001/` 필수 파일 보장
- [ ] 기존 5역할 흐름은 deprecated 처리
- [ ] commit, push, merge 자동화 없음

## 안전 메모

- secret, `.env`, auth, payment, production infra, database migration은 변경하지 않는다.
- AI는 commit, push, merge를 수행하지 않는다.
