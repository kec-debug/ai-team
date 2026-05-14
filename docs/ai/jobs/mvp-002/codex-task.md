# Codex 작업 지시문

## 작업 대상

- Job ID:
- Project directory:

## 읽어야 할 파일

- `docs/ai/jobs/{JOB_ID}/request.ko.md`
- `docs/ai/jobs/{JOB_ID}/plan.md`

## 구현 지시

Claude가 승인한 범위만 구현합니다. 관련 파일만 수정하고 필요한 테스트를 추가하거나 갱신합니다.

## 금지 사항

- commit, push, merge 금지
- secret, `.env`, auth, payment, production infra, database migration 변경 금지
- vendor endpoint를 지어내지 않기
- live trading 기본 활성화 금지

## 결과 작성

결과는 `patch.md` 형식에 맞춰 정리합니다.
