# 작업 요청

PuTTY 없이 브라우저에서 AI 개발팀을 조작할 수 있는 웹 GUI v1을 만든다.

## 목표

현재 ai-team repo는 tmux 기반 CLI 관제센터다.
이제 사용자가 브라우저에서 한국어로 작업을 입력하고, 버튼으로 Gemini / Claude / Codex / Git Shell 단계를 실행할 수 있는 간단한 웹 GUI를 추가한다.

## 요구사항

- Node.js + Express 기반의 간단한 웹 서버를 만든다.
- 위치는 web/ 폴더로 한다.
- 브라우저에서 접속 가능한 단일 페이지 GUI를 만든다.
- 사용자는 다음 값을 입력할 수 있어야 한다:
  - 프로젝트 경로
  - 작업 ID
  - 한국어 작업 요청
- GUI에서 버튼으로 다음 기능을 실행할 수 있어야 한다:
  - AI 팀 tmux 세션 상태 확인
  - AI 팀 시작
  - 작업 폴더 생성
  - input.ko.md 저장
  - Gemini Manager에 프롬프트 전송
  - Claude Architect에 프롬프트 전송
  - Codex Implementer에 프롬프트 전송
  - Claude Reviewer에 프롬프트 전송
  - git status 보기
  - git diff 보기
- 서버는 child_process를 사용해 기존 scripts/*.sh와 tmux 명령을 호출한다.
- 산출물 파일을 GUI에서 읽어볼 수 있게 한다.
- README.md에 GUI 실행 방법을 추가한다.

## 보안 요구사항

- 기본 바인딩은 127.0.0.1 또는 환경변수 HOST로 제어한다.
- 포트는 기본 3100으로 한다.
- 외부 공개를 전제로 만들지 않는다.
- API key, token, secret, .env 값을 읽거나 출력하지 않는다.
- 임의 shell command 입력 기능은 만들지 않는다.
- 허용된 명령만 실행한다.
- main 브랜치에 자동 push/merge하지 않는다.
- commit/push/merge는 사람이 Git Shell에서 직접 하도록 한다.

## 기술 스택

- Node.js
- Express
- vanilla HTML/CSS/JS
- 별도 데이터베이스는 사용하지 않는다.

## 산출물

- web/package.json
- web/server.js
- web/public/index.html
- web/public/app.js
- web/public/style.css
- docs/ai/jobs/job-002/codex-summary.en.md
- README.md 업데이트

## 금지

- scripts/start-ai-team.sh의 기존 동작을 깨지 않는다.
- 기존 tmux 구조를 바꾸지 않는다.
- secrets, token, .env 관련 값을 저장하지 않는다.
- 자동 merge 기능을 만들지 않는다.
