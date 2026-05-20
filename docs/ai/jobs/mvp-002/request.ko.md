# 작업 요청

컨트롤센터 GUI를 Claude + Codex 2-role 구조로 단순화한다.

## 목표

기존 5-role 구조를 사용하지 않는다.

기존 구조:
- Gemini Manager
- Claude Architect
- Codex Implementer
- Claude Reviewer
- Git Shell

새 구조:
- Claude
- Codex
- Manual Shell

Claude는 계획, 요구사항 정리, 리뷰를 담당한다.
Codex는 구현, 테스트, 패치 요약을 담당한다.
Manual Shell은 사람이 git status, git diff, commit, PR 확인에만 사용한다.

## GUI 요구사항

- Gemini 관련 버튼 제거
- Claude Architect / Claude Reviewer 분리 표시 제거
- Claude 계획 생성 버튼 추가
- Codex 구현 실행 버튼 추가
- Claude 리뷰 실행 버튼 추가
- git status / git diff는 수동 확인 도구로 유지
- commit / push / merge는 자동화하지 않는다

## 산출물

새 job 폴더는 다음 파일을 기준으로 한다.

- request.ko.md
- plan.md
- codex-task.md
- patch.md
- review.md
- status.md

## 안전 규칙

- 자동 commit 금지
- 자동 push 금지
- 자동 merge 금지
- 배포 자동화 금지
- .env, token, secret, API key 읽기 금지
- auth, payment, DB migration, production infra 수정 금지
