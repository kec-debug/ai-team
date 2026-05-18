AI 개발팀 GUI를 기존 5-role 구조에서 Claude + Codex 2-role 구조로 단순화해줘.

현재 GUI는 예전 역할을 보여주고 있다:
- Gemini Manager
- Claude Architect
- Codex Implementer
- Claude Reviewer
- Git Shell

이제는 아래 두 역할만 사용한다:
- Claude: 설계 / 요구사항 정리 / 리뷰
- Codex: 구현 / 테스트 / 패치 요약

원하는 변경사항:
1. Gemini Manager, Claude Architect, Claude Reviewer, Git Shell을 핵심 AI 역할에서 제거하거나 숨겨줘.
2. 버튼을 아래처럼 바꿔줘.
   - Claude 계획 생성
   - Codex 구현 실행
   - Claude 리뷰 실행
   - Claude → Codex → Claude 전체 실행
3. tmux 대상은 ai-team 세션의 claude, codex 창만 사용하게 해줘.
4. 기존 gemini-manager, claude-architect, claude-reviewer, git-shell 창을 기본 대상으로 쓰지 않게 해줘.
5. 작업 산출물은 아래 파일을 기준으로 해줘.
   - request.ko.md
   - plan.md
   - codex-task.md
   - patch.md
   - review.md
   - status.md
6. 상태 단계는 아래처럼 단순화해줘.
   - claude_planning
   - codex_implementing
   - claude_reviewing
   - manual_review_required
   - succeeded
   - failed
   - blocked
   - approval_required
7. git status와 git diff는 수동 유틸리티 버튼으로만 남겨줘.
8. commit, push, merge, deploy는 자동화하지 마.
9. 임의 shell 명령 입력 기능은 만들지 마.
10. secrets, .env, auth, payment, production infra, database migrations는 건드리지 마.
11. README와 docs/ai/CLAUDE_CODEX_WORKFLOW.md에 새 Claude + Codex 사용법을 반영해줘.

검증:
- node --check web/server.js
- node --check web/public/app.js
- git diff --stat

완료 후 patch.md에 변경 요약을 남겨줘.