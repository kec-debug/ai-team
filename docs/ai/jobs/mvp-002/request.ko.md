# 작업 요청

컨트롤센터 GUI를 기존 5-role AI팀 구조에서 Claude + Codex 2-role 구조로 단순화한다.

## 배경

현재 GUI는 다음 오래된 구조를 기준으로 만들어져 있다.

- Gemini Manager
- Claude Architect
- Codex Implementer
- Claude Reviewer
- Git Shell

하지만 새 MVP 구조는 다음 두 개만 사용한다.

- Claude
- Codex

Claude는 설계, 요구사항 정리, 리뷰를 담당한다.
Codex는 구현, 테스트, 패치 요약을 담당한다.

## 목표

사용자가 GUI에서 여러 AI 창을 관리하지 않고, 다음 흐름만 사용하게 만든다.

1. 한국어 작업 요청 입력
2. Claude 계획 생성
3. Codex 구현 실행
4. Claude 리뷰 실행
5. 사람 최종 확인
6. 필요한 git 명령은 사람이 직접 수행

## GUI 변경 요구사항

1. 화면 문구 변경

기존 제목이나 설명에서 5-role workflow, Gemini, Claude Architect, Claude Reviewer, git-shell 중심 표현을 제거하거나 deprecated 처리한다.

새 표현:
- AI 개발팀 컨트롤 센터
- Claude + Codex Workflow
- Claude: 설계 / 요구사항 정리 / 리뷰
- Codex: 구현 / 테스트 / 패치 요약

2. 메인 버튼 변경

기존 버튼:
- Gemini Manager 전송
- Claude Architect 전송
- Codex Implementer 전송
- Claude Reviewer 전송

새 버튼:
- Claude 계획 생성
- Codex 구현 실행
- Claude 리뷰 실행

3. 전체 파이프라인 버튼 변경

기존:
- 전체 파이프라인 실행

새 이름:
- Claude → Codex → Claude 전체 실행

동작:
- 작업 폴더 생성
- request.ko.md 저장
- Claude 계획 프롬프트 전송
- Codex 구현 프롬프트 전송
- Claude 리뷰 프롬프트 전송
- commit, push, merge는 자동 실행하지 않음

4. 산출물 파일명 변경

새 job 폴더 기준 파일:

- request.ko.md
- plan.md
- codex-task.md
- patch.md
- review.md
- status.md

GUI 산출물 목록도 위 파일들을 우선 표시한다.

기존 파일명 input.ko.md, gemini-plan.en.md, claude-design-review.en.md, codex-summary.en.md, claude-pr-review.en.md는 old workflow compatibility로만 취급한다.

5. 서버 API 정리

가능하면 기존 API는 유지하되, 새 API 또는 내부 mapping을 추가한다.

새 역할 mapping:
- claude-plan → tmux Claude 창
- codex-implement → tmux Codex 창
- claude-review → tmux Claude 창

기존 Gemini 관련 API는 deprecated 처리하거나 GUI에서 숨긴다.

6. tmux 구조 단순화

GUI는 새 구조를 다음처럼 표시한다.

- Claude
- Codex

Git은 AI 역할이 아니라 "수동 확인 도구"로 표시한다.

7. 상태 표시 변경

상태 단계는 다음만 사용한다.

- idle
- claude_planning
- codex_implementing
- claude_reviewing
- manual_review_required
- succeeded
- failed
- blocked
- approval_required

8. 승인 버튼 유지

승인 / 세션 승인 / 거절 / 중단 버튼은 유지한다.
단, 대상 선택은 Claude 또는 Codex만 기본으로 제공한다.

9. 안전 요구사항

절대 자동화하지 않는다.

- git commit
- git push
- PR merge
- 배포
- .env 읽기
- token / secret / API key 읽기
- auth / payment / DB migration / production infra 수정
- 임의 shell command 실행

10. README 업데이트

README.md에 새 GUI 사용법을 추가한다.

내용:
- Claude + Codex 2-role workflow
- GUI에서 작업 요청 입력
- Claude 계획 생성
- Codex 구현
- Claude 리뷰
- 사람이 git status / git diff 확인
- commit / push / merge는 사람이 직접

## 수정 대상

- web/server.js
- web/public/index.html
- web/public/app.js
- web/public/style.css
- README.md
- docs/ai/jobs/mvp-002/patch.md 또는 codex-summary.en.md

## 완료 기준

- GUI에서 Gemini 관련 버튼이 보이지 않는다.
- GUI에서 Claude / Codex 중심으로만 보인다.
- 전체 실행 버튼이 Claude → Codex → Claude 흐름으로 설명된다.
- 산출물 목록이 request.ko.md, plan.md, codex-task.md, patch.md, review.md, status.md 중심으로 보인다.
- git commit / push / merge는 자동화하지 않는다.
