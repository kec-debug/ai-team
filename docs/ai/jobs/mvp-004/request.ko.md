# 작업 ID
mvp-004

# 작업명
AI 개발팀 GUI 화면 배치 개선

현재 AI 개발팀 브라우저 GUI에서 화면 배치가 불편하다.

문제점:
1. 파이프라인 상태 영역이 너무 위에 있어서 핵심 제어 버튼과 시선 흐름이 맞지 않는다.
2. 승인 / 서비스 제어 / 실시간 출력 영역이 아래쪽에 있어 잘 안 보인다.
3. 작업 설정 칸이 너무 길어서 화면을 많이 차지한다.
4. 실제 작업 중에는 승인 버튼, 서비스 제어, 실시간 출력이 더 중요하므로 위쪽에서 바로 보여야 한다.

원하는 변경사항:

1. “파이프라인 상태” 영역을 “Claude → Codex → Claude 전체 실행” 버튼 아래로 내려줘.

2. 아래 영역들을 상단 쪽으로 올려줘.
   - 승인 / 계속 진행
   - 거절
   - 중단
   - 서비스 제어
   - 실시간 출력

3. 작업 설정 영역을 더 짧고 컴팩트하게 만들어줘.
   - 입력칸 높이를 줄여줘.
   - 필요하면 접기/펼치기 형태로 만들어줘.
   - 화면에서 너무 많은 공간을 차지하지 않게 해줘.

4. 화면 우선순위를 아래 순서로 재배치해줘.
   - 상단: 작업 ID / 작업 요청 입력 / 주요 실행 버튼
   - 그 아래: 승인 / 서비스 제어 / 실시간 출력
   - 그 아래: 파이프라인 상태
   - 그 아래: 작업 설정 / 고급 설정 / 산출물 목록

5. Claude + Codex 2-role 구조는 유지해줘.
   - Gemini Manager, Claude Architect, Claude Reviewer, Git Shell을 다시 노출하지 마.
   - Claude 계획 생성
   - Codex 구현 실행
   - Claude 리뷰 실행
   - Claude → Codex → Claude 전체 실행
   이 버튼 구조는 유지해줘.

6. git status와 git diff는 수동 유틸리티 버튼으로만 유지해줘.
   - commit, push, merge는 자동화하지 마.

7. 반응형 화면도 깨지지 않게 해줘.
   - 작은 화면에서도 실시간 출력과 승인 버튼이 잘 보여야 한다.

수정 대상:
- web/public/index.html
- web/public/app.js
- web/public/style.css
- 필요하면 web/server.js
- README.md 또는 docs/ai/CLAUDE_CODEX_WORKFLOW.md는 변경 내용이 있으면 최소한만 업데이트

금지:
- 주식 페이퍼매매 로직은 건드리지 마.
- secrets, .env, auth, payment, production infra, database migrations는 건드리지 마.
- 임의 shell 명령 입력 기능은 만들지 마.
- git commit, push, merge는 자동화하지 마.

검증:
- node --check web/server.js
- node --check web/public/app.js
- git diff --stat

완료 후:
- 어떤 UI 영역을 어디로 옮겼는지
- 작업 설정 영역을 어떻게 줄였는지
- Claude + Codex 구조가 유지되는지
- 테스트 결과가 무엇인지
patch.md에 정리해줘.