cd ~/ai-dev-center/projects/ai-team
./scripts/create-job.sh . job-004

cat > docs/ai/jobs/job-004/input.ko.md <<'EOF'
# 작업 요청

GUI v1을 개선해서 버튼 하나로 전체 AI 개발 파이프라인을 실행할 수 있게 만든다.

## 목표

현재 GUI는 Gemini / Claude Architect / Codex / Claude Reviewer 버튼을 사람이 각각 눌러야 한다.
또한 각 CLI가 중간에 명령 실행 승인을 요구하면 작업이 멈춘다.

목표는 다음 흐름이다.

브라우저 접속
→ 프로젝트 선택
→ 작업 ID 입력
→ 한국어 작업 요청 입력
→ [전체 파이프라인 실행] 버튼 클릭
→ Gemini / Claude / Codex / Claude Reviewer 단계 자동 진행
→ 결과 요약 표시
→ 사람은 최종 변경사항 확인
→ 사람은 PR 생성 여부만 최종 승인

## 요구사항

GUI에 다음 기능을 추가한다.

1. 전체 파이프라인 실행 버튼
- 버튼 이름: 전체 파이프라인 실행
- 서버 엔드포인트: POST /api/pipeline/run
- 입력값:
  - projectDir
  - jobId
  - inputKo

2. 파이프라인 상태 확인
- 엔드포인트: GET /api/pipeline/status?projectDir=...&jobId=...
- 현재 단계, 성공/실패, 생성된 산출물 목록을 보여준다.

3. 자동 단계
- 작업 폴더 생성
- input.ko.md 저장
- Gemini 계획 생성
- Claude Architect 리뷰 생성
- Codex 구현 실행
- git diff 저장
- Claude Reviewer 리뷰 생성
- codex-summary.en.md와 claude-pr-review.en.md를 GUI에서 볼 수 있게 한다.

4. 최종 승인만 사람에게 맡김
- commit, push, PR 생성, merge는 자동 실행하지 않는다.
- 대신 변경 파일, diff 요약, Reviewer decision을 GUI에 보여준다.
- PR 생성은 별도 버튼으로 둔다.
- Merge는 GitHub에서 사람이 직접 한다.

5. 안전 정책
- 임의 shell command 입력 기능 금지
- scripts/, prompts/, web/ 밖 임의 명령 실행 금지
- .env, secrets, token, API key 읽기/출력 금지
- auth/payment/db migration/production infra 자동 수정 금지
- rm, sudo, curl | bash, git push, gh pr merge 자동 실행 금지

6. 실행 방식
- 가능하면 Gemini와 Codex는 headless/non-interactive 방식으로 실행한다.
- Codex는 가능하면 codex exec를 사용한다.
- 중간 승인 프롬프트가 필요한 interactive tmux 방식은 최소화한다.
- 자동화가 불가능한 단계는 GUI에 "수동 개입 필요"로 표시한다.

7. README.md 업데이트
- 전체 파이프라인 실행 사용법 추가
- 최종 승인 방식 설명
- 안전상 자동 merge를 하지 않는다고 명시

## 완료 기준

- GUI에서 [전체 파이프라인 실행] 버튼이 보인다.
- 버튼 하나로 가능한 단계가 자동 실행된다.
- 중간 상태와 결과 파일이 GUI에 표시된다.
- 위험 작업은 자동 실행하지 않는다.
- 최종 PR/merge는 사람 승인으로 남아 있다.
EOF