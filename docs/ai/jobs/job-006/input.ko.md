# 작업 요청

GUI를 실시간 AI 개발팀 관제센터로 개선한다.

## 현재 문제

현재 GUI는 전체 파이프라인 실행 버튼이 있지만 운영성이 부족하다.

문제:
- AI팀 재시작 버튼이 없다.
- GUI 서버 재시작 버튼이 없다.
- Gemini / Claude / Codex 승인 대기 시 GUI에서 승인할 방법이 없다.
- Claude Reviewer 이후 다음 액션이 없다.
- 파이프라인 실행 중 어디까지 진행됐는지 실시간으로 확인하기 어렵다.
- Gemini 단계에서 상태가 running으로 고정되는 문제가 있다.
- job ID가 바뀌어도 이전 job 상태가 남아 헷갈릴 수 있다.
- 버튼이 너무 많고 중요하지 않은 버튼이 화면을 복잡하게 만든다.
- 사용자는 GUI에서 최대한 모든 컨트롤을 하고 싶다.

## 목표

브라우저 GUI를 진짜 관제센터처럼 만든다.

사용자는 GUI에서 다음을 할 수 있어야 한다.

- 전체 파이프라인 실행
- 현재 단계 실시간 확인
- Gemini / Claude / Codex / Reviewer 창 출력 확인
- 승인 대기 상태 확인
- 승인 버튼 클릭
- 거절 버튼 클릭
- 중단 버튼 클릭
- AI팀 재시작
- GUI 서버 재시작
- 파이프라인 상태 초기화
- 생성된 산출물 확인
- git status / git diff 확인
- Reviewer 결과 확인
- 최종 PR 생성은 사람 승인으로 진행

## UI 요구사항

기존 GUI를 정리한다.

메인 버튼:
- 전체 파이프라인 실행
- 승인 / 계속 진행
- 세션 승인
- 거절
- 중단
- 상태 초기화
- AI팀 재시작
- GUI 서버 재시작

고급 버튼 영역:
- Gemini Manager 전송
- Claude Architect 전송
- Codex Implementer 전송
- Claude Reviewer 전송
- git status
- git diff

고급 버튼은 접기/펼치기 형태로 숨긴다.

상태 영역:
- 현재 Job ID
- 현재 단계
- 현재 상태
- 마지막 업데이트 시간
- 현재 tmux 대상 창
- 승인 대기 추정 여부
- Reviewer decision
- 생성된 산출물 목록
- git diff 요약

실시간 로그 영역:
- Gemini Manager 출력
- Claude Architect 출력
- Codex Implementer 출력
- Claude Reviewer 출력
- Git Shell 출력

각 로그는 tmux capture-pane 기반으로 최신 내용을 보여준다.
GUI는 2초마다 상태와 로그를 자동 새로고침한다.

## 서버 API 요구사항

다음 API를 추가하거나 보완한다.

상태:
- GET /api/pipeline/status
- POST /api/pipeline/reset

실시간 tmux 출력:
- GET /api/tmux/windows
- GET /api/tmux/output?window=gemini-manager
- GET /api/tmux/output?window=claude-architect
- GET /api/tmux/output?window=codex-implementer
- GET /api/tmux/output?window=claude-reviewer
- GET /api/tmux/output?window=git-shell

승인/제어:
- POST /api/tmux/approve-once
- POST /api/tmux/approve-session
- POST /api/tmux/reject
- POST /api/tmux/interrupt

대상 window는 반드시 allowlist로 제한한다.
허용 대상:
- gemini-manager
- claude-architect
- codex-implementer
- claude-reviewer
- git-shell

서비스 제어:
- POST /api/service/restart-ai-team
- POST /api/service/restart-gui
- GET /api/service/status

주의:
restart-gui는 현재 Node 프로세스를 바로 죽이면 응답이 끊길 수 있으므로 detached shell/tmux 방식으로 안전하게 재시작한다.

## 파이프라인 상태 감지 요구사항

artifact 기반으로 단계 완료를 추정한다.

Gemini 완료:
- docs/ai/jobs/<JOB_ID>/gemini-plan.en.md 존재
또는
- docs/ai/jobs/<JOB_ID>/codex-prompt.en.md 존재

Claude Architect 완료:
- docs/ai/jobs/<JOB_ID>/claude-design-review.en.md 존재
또는
- docs/ai/jobs/<JOB_ID>/architecture.md 존재

Codex 완료:
- docs/ai/jobs/<JOB_ID>/codex-summary.en.md 존재

Reviewer 완료:
- docs/ai/jobs/<JOB_ID>/claude-pr-review.en.md 존재
또는
- docs/ai/jobs/<JOB_ID>/review.md 존재

running 상태가 오래 지속되면 manual_required로 바꾼다.

manual_required 메시지:
"AI CLI 창에서 승인 대기 중일 수 있습니다. 아래 승인 버튼을 누르거나 tmux 출력을 확인하세요."

## 승인 버튼 요구사항

GUI에서 승인 버튼을 누르면 선택된 단계의 tmux 창에 안전한 입력만 보낸다.

예:
- 승인 / 계속 진행: "1" + Enter
- 세션 승인: "2" + Enter
- 거절: "3" + Enter
- 중단: Ctrl+C

단, 이 기능은 Gemini / Claude / Codex CLI의 승인 화면을 대신 조작하는 것이므로, GUI에 경고 문구를 표시한다.

경고:
"승인은 현재 AI CLI 창에 키 입력을 보내는 기능입니다. 위험한 명령은 승인하지 마세요."

## 안전 요구사항

금지:
- 임의 shell command 입력 기능
- rm -rf 자동 실행
- sudo 자동 실행
- curl | bash 자동 실행
- git push 자동 실행
- gh pr merge 자동 실행
- 배포 자동 실행
- .env 읽기/출력
- token, secret, API key 읽기/출력
- auth/payment/db migration/production infra 자동 수정

허용:
- scripts/start-ai-team.sh 실행
- scripts/status-ai-team.sh 실행
- scripts/create-job.sh 실행
- tmux capture-pane
- tmux send-keys allowlist 입력
- git status
- git diff
- node --check

## 완료 기준

- GUI에서 현재 단계가 실시간으로 보인다.
- Gemini 단계에서 무한 running으로 고정되지 않는다.
- 승인 대기 상황을 manual_required로 표시한다.
- GUI에서 승인/거절/중단 버튼을 사용할 수 있다.
- AI팀 재시작 버튼이 동작한다.
- GUI 서버 재시작 버튼이 동작한다.
- 중요 버튼 중심으로 화면이 정리된다.
- 고급 버튼은 접기/펼치기로 숨겨진다.
- Reviewer 완료 후 결과와 다음 액션이 보인다.
- commit, push, merge는 자동화하지 않는다.
