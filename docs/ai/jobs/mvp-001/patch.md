# Codex 패치 요약

## 1. Files Changed

- `docs/ai/CLAUDE_CODEX_WORKFLOW.md` — 새 Claude + Codex 워크플로 문서.
- `prompts/claude.md` — Claude 통합 역할 프롬프트.
- `prompts/codex-implementer.md` — Codex 구현 프롬프트를 2역할 흐름에 맞게 단순화.
- `docs/ai/jobs/_template/request.ko.md` — 한국어 요청 템플릿.
- `docs/ai/jobs/_template/plan.md` — Claude 계획 템플릿.
- `docs/ai/jobs/_template/codex-task.md` — Codex 작업 지시 템플릿.
- `docs/ai/jobs/_template/patch.md` — Codex 패치 요약 템플릿.
- `docs/ai/jobs/_template/review.md` — Claude 리뷰 템플릿.
- `docs/ai/jobs/_template/status.md` — job 상태 템플릿.
- `docs/ai/jobs/mvp-001/request.ko.md` — 현재 job 요청 파일.
- `docs/ai/jobs/mvp-001/plan.md` — 현재 job 계획 파일.
- `docs/ai/jobs/mvp-001/codex-task.md` — 현재 job Codex 지시문.
- `docs/ai/jobs/mvp-001/patch.md` — 현재 패치 요약.
- `docs/ai/jobs/mvp-001/review.md` — 현재 job 리뷰 placeholder.
- `docs/ai/jobs/mvp-001/status.md` — 현재 job 상태.
- `scripts/create-job.sh` — 새 템플릿 복사 방식으로 job 생성, 기본 no-overwrite, `--force` 지원.
- `scripts/start-ai-team.sh` — tmux 창을 Claude + Codex 두 개로 단순화.
- `README.md` — 새 흐름 안내와 old flow deprecation 표시.
- `docs/workflow.md` — 이전 workflow 문서 deprecation 표시.
- `docs/setup.md` — 필요 도구와 alias 설명을 Claude + Codex 기준으로 갱신.
- `docs/safety-rules.md` — PR 생성도 사람이 직접 실행하도록 명확화.
- `prompts/gemini-manager.md` — deprecated 안내 추가.
- `prompts/claude-architect.md` — deprecated 안내 추가.
- `prompts/claude-reviewer.md` — deprecated 안내 추가.

## 2. Implementation Summary

기본 AI 작업 흐름을 Claude + Codex only로 정리했습니다. Claude는 한국어 요청 해석, 계획, 리스크 점검, 리뷰를 맡고 Codex는 구현, 테스트, 패치 요약만 맡습니다. 기존 Gemini Manager, Claude Architect, Claude Reviewer, Git Shell 역할은 새 작업 기준 deprecated 처리했습니다.

## 3. Safety Confirmation

- commit, push, merge는 수행하지 않았습니다.
- secret, `.env`, auth, payment, production infra, database migration은 변경하지 않았습니다.
- trading system logic은 변경하지 않았습니다.
- live trading을 활성화하지 않았습니다.

## 4. Test Results

- `bash -n scripts/create-job.sh` 통과.
- `bash -n scripts/start-ai-team.sh` 통과.
- `find docs/ai/jobs/_template -maxdepth 1 -type f | sort`로 6개 템플릿 파일 존재 확인.
- `find docs/ai/jobs/mvp-001 -maxdepth 1 -type f | sort`로 현재 job 필수 파일 존재 확인.
- docs/prompts/scripts 범위 변경이므로 `python -m compileall app tests`와 `python -m pytest -p no:cacheprovider`는 실행하지 않았습니다.

## 5. Remaining TODOs

- Claude가 최종 diff를 리뷰해 `review.md`를 채웁니다.
