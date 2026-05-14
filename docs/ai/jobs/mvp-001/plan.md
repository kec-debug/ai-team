# Claude 계획

## 1. 요청 요약

기존 5역할 AI 작업 파이프라인을 Claude + Codex 2역할 워크플로로 단순화한다.

## 2. 작업 범위

- 새 Claude + Codex 워크플로 문서를 작성한다.
- Claude 통합 프롬프트를 만든다.
- Codex 구현 프롬프트에서 old multi-agent 참조를 제거한다.
- job 폴더 템플릿을 만든다.
- `mvp-001` job 폴더에 필수 파일을 추가한다.
- 기존 워크플로 문서와 스크립트는 삭제하지 않고 deprecated 안내를 추가한다.

## 3. 수정해야 할 파일

- `docs/ai/CLAUDE_CODEX_WORKFLOW.md`
- `prompts/claude.md`
- `prompts/codex-implementer.md`
- `docs/ai/jobs/_template/*`
- `docs/ai/jobs/mvp-001/*`
- `scripts/create-job.sh`
- `README.md`
- `docs/workflow.md`
- 기존 old role prompt 파일의 deprecation 안내

## 4. Codex 구현 지시문

승인된 문서와 템플릿 범위만 수정한다. trading system logic, secret, `.env`, auth, payment, production infra, database migration은 수정하지 않는다. 기존 job 기록은 삭제하지 않는다.

## 5. 테스트 기준

- 새 템플릿 파일이 모두 존재해야 한다.
- `mvp-001` 필수 파일이 모두 존재해야 한다.
- `scripts/create-job.sh`가 syntax check를 통과해야 한다.
- docs-only 변경이므로 app 전체 테스트는 실행하지 않아도 된다.

## 6. 리뷰 체크리스트

- [ ] 기본 흐름이 Claude -> Codex -> Claude Review로 설명되어 있다.
- [ ] old roles가 deprecated 처리되어 있다.
- [ ] Codex 프롬프트가 commit, push, merge 금지를 유지한다.
- [ ] trading 안전 규칙이 유지되어 있다.
- [ ] beginner-friendly하고 과도한 자동화가 없다.
