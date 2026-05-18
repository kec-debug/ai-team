# Status — api-auth-001

| Field | Value |
| --- | --- |
| Job ID | api-auth-001 |
| Title | KIS Open API OAuth 인증 + 토큰 캐시 + 안전 HTTP 래퍼 (mock/paper 기본) |
| Stage | `claude_planning` → **`codex_implementing`** (Codex 호출 대기) |
| Created (Claude planning) | 2026-05-17 |
| Last update | 2026-05-17 |
| Owner (human) | kec |
| Depends on | KIS_1 (시세 catalog) — land 완료. mvp-014-017 (KIS skeleton) — land 완료. |
| Blocks | `api-market-data-001` (시세 본문), `api-orders-paper-001` (모의 주문 본문), `KIS_2` (주문/계좌 catalog) |

## 산출물

| 파일 | 상태 | 비고 |
| --- | --- | --- |
| `docs/ai/jobs/api-auth-001/request.ko.md` | done | Claude가 사용자 메시지에서 도출해 작성 |
| `docs/ai/jobs/api-auth-001/plan.md` | done | 6-섹션 표준 + 10개 인증 명세 항목 모두 포함 |
| `docs/ai/jobs/api-auth-001/codex-task.md` | done | §A~§J 본문 박힘. Codex가 byte-level 따름 |
| `docs/ai/jobs/api-auth-001/status.md` | done | 본 파일 |
| `docs/ai/jobs/api-auth-001/patch.md` | **pending** | Codex가 작성 |
| `docs/ai/jobs/api-auth-001/review.md` | **pending** | Codex 종료 후 Claude가 작성 |

## 안전 invariant (계획 단계 검증)

- KIS endpoint / TR ID / 헤더 / payload 추측 0건. 모든 값은 업로드 공식 자료(1/3/4/5/6.xlsx) 또는 KIS_1 land 결과에서만 인용.
- 실 app key / secret / token / 계좌번호: plan/codex-task 본문 0건. 테스트도 `"fake-*"` 또는 8자리 이하 fake 숫자.
- live trading 활성 변경 0건. `OrderType.MARKET` 부재 유지. `KIS_ORDER_DRY_RUN=true` 기본 유지.
- 외부 HTTP lib import 지시 0건 (`urllib.request`만).
- `.env` 읽기/수정 0건. `.env.example`은 이름 + 한 줄 설명만.
- LLM/Agent의 broker 직접 호출 경로 0건.
- 자동 commit / push / merge / deploy 0건.

## 다음 단계

1. **Codex 호출** — GUI `Codex 구현 실행` 또는 tmux `ai-team:codex`에 `prompts/codex-implementer.md` 적용 후 본 폴더의 `plan.md` + `codex-task.md` 읽게 함.
2. Codex가 `patch.md` 작성.
3. **Claude 리뷰** — `git diff` + `patch.md` 검토 → `review.md` 작성 (`APPROVE` / `REQUEST CHANGES` / `BLOCK`).
4. **사람** — `git status` / `git diff` 직접 확인 후 staging/commit. commit 시 `app/`, `tests/`, `.env.example`, `README.md`, `docs/ai/jobs/api-auth-001/` 만 staging.

## 사람 액션 아이템 (계획 단계에서 미리)

- [ ] KIS 포털에서 실 app key/secret 발급(아직 미보유 시). paper용 발급으로 시작. live용은 별 단계.
  - 발급 후 `.env`에 `KIS_APP_KEY`/`KIS_APP_SECRET` 추가는 본 job 후 **사람이 직접**(코드/Codex 미접촉).
  - 본 job land 후 실제 검증은 paper 모드로 한 번 수동 호출하여 토큰 발급 성공 여부 확인.
- [ ] (지난 채팅에서 노출된 KIS Developers 포털 로그인이 아직 비밀번호 변경 전이라면) **포털 비밀번호 변경**.
- [ ] 본 job land 후 후속 job 우선순위 결정 — 시세 본문(`api-market-data-001`) vs 주문/계좌 catalog(`KIS_2`).
