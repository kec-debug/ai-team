## 1. 현재 변경사항 전체 요약

현재 워크트리는 GUI 변경, `projects/paper-trading` 변경, `docs/ai/jobs` 산출물 변경, `.gitignore` 변경이 섞여 있다. `git add`, commit, push, merge, 삭제 작업은 수행하지 않았다.

`git diff --stat` 기준 tracked 변경:

- `.gitignore`: `imports/` ignore 추가.
- `web/`: 4개 파일, 752 insertions / 134 deletions.
- `projects/paper-trading/`: 14개 tracked 파일, 386 insertions / 7 deletions.
- `docs/ai/jobs`: 4개 tracked 파일, 2445 insertions / 185 deletions.

주요 untracked 변경:

- `docs/ai/jobs/mvp-003/`, `mvp-004/`, `mvp-005/`, `mvp-006/`, `mvp-008/`, `mvp-008-import/`, `mvp-009/`, `mvp-010/`
- `projects/paper-trading/app/portfolio/`
- `projects/paper-trading/app/session/`
- `projects/paper-trading/tests/test_kill_switch.py`
- `projects/paper-trading/tests/test_kis_capabilities.py`
- `projects/paper-trading/tests/test_kis_order_preflight.py`
- `projects/paper-trading/tests/test_kis_order_request_model.py`
- `projects/paper-trading/tests/test_kis_order_response_model.py`
- `projects/paper-trading/tests/test_portfolio_service.py`
- `projects/paper-trading/tests/test_session_router.py`
- `projects/paper-trading/tests/test_status_modules.py`

## 2. GUI 변경 파일 목록

GUI dirty로 분리해야 할 파일:

- `web/server.js`
- `web/public/app.js`
- `web/public/index.html`
- `web/public/style.css`

이 4개는 `projects/paper-trading` KIS 작업과 별도 커밋 단위로 분리해야 한다.

## 3. paper-trading 변경 파일 목록

Tracked:

- `projects/paper-trading/.env.example`
- `projects/paper-trading/README.md`
- `projects/paper-trading/app/api/routes.py`
- `projects/paper-trading/app/api/server.py`
- `projects/paper-trading/app/broker/kis.py`
- `projects/paper-trading/app/config.py`
- `projects/paper-trading/app/domain/orders.py`
- `projects/paper-trading/app/oms/manager.py`
- `projects/paper-trading/app/risk/engine.py`
- `projects/paper-trading/app/strategy/premarket_gap.py`
- `projects/paper-trading/tests/test_api_paper_status.py`
- `projects/paper-trading/tests/test_broker_interface.py`
- `projects/paper-trading/tests/test_risk_engine.py`
- `projects/paper-trading/tests/test_strategy_premarket_gap.py`

Untracked:

- `projects/paper-trading/app/portfolio/__init__.py`
- `projects/paper-trading/app/portfolio/service.py`
- `projects/paper-trading/app/session/__init__.py`
- `projects/paper-trading/app/session/router.py`
- `projects/paper-trading/tests/test_kill_switch.py`
- `projects/paper-trading/tests/test_kis_capabilities.py`
- `projects/paper-trading/tests/test_kis_order_preflight.py`
- `projects/paper-trading/tests/test_kis_order_request_model.py`
- `projects/paper-trading/tests/test_kis_order_response_model.py`
- `projects/paper-trading/tests/test_portfolio_service.py`
- `projects/paper-trading/tests/test_session_router.py`
- `projects/paper-trading/tests/test_status_modules.py`

이 묶음은 mvp-008-import와 mvp-009가 섞여 있다. 커밋 전에는 최소 두 커밋으로 나누는 것이 좋다:

- session/portfolio/status import 커밋
- KIS order boundary/sanitization/capabilities 커밋

## 4. docs/jobs 변경 파일 목록

Tracked:

- `docs/ai/jobs/mvp-004/request.ko.md`
- `docs/ai/jobs/mvp-007/local-diff.patch`
- `docs/ai/jobs/mvp-007/pipeline.log.md`
- `docs/ai/jobs/mvp-007/request.ko.md`

Untracked:

- `docs/ai/jobs/mvp-003/*`
- `docs/ai/jobs/mvp-004/codex-task.md`
- `docs/ai/jobs/mvp-004/local-diff.patch`
- `docs/ai/jobs/mvp-004/patch.md`
- `docs/ai/jobs/mvp-004/pipeline.log.md`
- `docs/ai/jobs/mvp-004/plan.md`
- `docs/ai/jobs/mvp-004/review.md`
- `docs/ai/jobs/mvp-005/*`
- `docs/ai/jobs/mvp-006/*`
- `docs/ai/jobs/mvp-008/*`
- `docs/ai/jobs/mvp-008-import/*`
- `docs/ai/jobs/mvp-009/*`
- `docs/ai/jobs/mvp-010/*`

주의: `docs/ai/jobs/mvp-006`에는 plan/codex-task/request만 있고 기존 patch/review가 없었다. 현재 최신 구현은 `mvp-006-1`, `mvp-008`, `mvp-009` 흐름으로 대체되어 있으므로 옛 mvp-006 구현을 새로 커밋하지 않는 것이 안전하다.

## 5. 지금 커밋 가능한 파일 목록

조건부로 커밋 가능한 묶음:

1. `.gitignore`
   - `imports/` ignore 추가만 포함한다.
   - 독립 커밋 가능.

2. `projects/paper-trading` session/portfolio import 묶음
   - `app/session/*`
   - `app/portfolio/*`
   - 관련 `app/api/server.py`, `app/api/routes.py` 일부
   - `tests/test_session_router.py`
   - `tests/test_portfolio_service.py`
   - `tests/test_status_modules.py`
   - 단, `app/api/routes.py`와 `app/api/server.py`는 KIS/status 변경도 섞여 있으므로 hunk 단위 분리 필요.

3. `projects/paper-trading` KIS order boundary 묶음
   - `app/broker/kis.py`
   - `app/config.py`
   - `app/domain/orders.py`
   - `app/oms/manager.py`
   - `app/risk/engine.py`
   - `app/strategy/premarket_gap.py`
   - `tests/test_kill_switch.py`
   - `tests/test_kis_capabilities.py`
   - `tests/test_kis_order_preflight.py`
   - `tests/test_kis_order_request_model.py`
   - `tests/test_kis_order_response_model.py`
   - 관련 기존 테스트 보강 파일
   - 이 묶음은 전체 pytest `111 passed` 확인 완료.

4. 현재 job 산출물
   - `docs/ai/jobs/mvp-008-import/patch.md`
   - `docs/ai/jobs/mvp-009/*`
   - `docs/ai/jobs/mvp-010/*`
   - 각 구현 커밋과 함께 또는 별도 docs 커밋으로 분리 가능.

## 6. 커밋하면 안 되는 파일 목록

현재 바로 커밋하지 않는 것이 안전한 묶음:

- `web/server.js`
- `web/public/app.js`
- `web/public/index.html`
- `web/public/style.css`

이 GUI 변경은 KIS/paper-trading 작업과 무관하고 별도 리뷰가 필요하다.

- `docs/ai/jobs/mvp-004/request.ko.md`
- `docs/ai/jobs/mvp-007/local-diff.patch`
- `docs/ai/jobs/mvp-007/pipeline.log.md`
- `docs/ai/jobs/mvp-007/request.ko.md`

이 tracked docs 변경은 이전 작업 산출물/로그로 보이며 현재 커밋 단위와 섞으면 안 된다.

- `docs/ai/jobs/mvp-003/*`, `mvp-004/*`, `mvp-005/*`, `mvp-006/*`

이 untracked job 산출물은 별도 검토 후 커밋 여부를 결정해야 한다. 특히 `mvp-006`은 최신 KIS 구조와 중복되는 구 계획이다.

- `.env` 또는 `.env.*`

현재 status에 보이지는 않지만, 발견되더라도 절대 커밋하면 안 된다.

## 7. 권장 커밋 순서

1. `.gitignore`: `imports/` ignore 추가.
2. `projects/paper-trading` KIS safety/order-boundary changes: mvp-009 중심. 테스트 결과를 커밋 메시지에 포함.
3. `projects/paper-trading` session/portfolio/status import changes: mvp-008-import 중심. `app/api/routes.py`/`server.py`는 hunk 분리 필요.
4. 관련 job docs: `mvp-008-import`, `mvp-009`, `mvp-010` patch/pipeline/request 등 현재 작업 산출물.
5. GUI 변경: `web/*`는 별도 리뷰 후 별도 커밋.
6. 오래된 docs/job 변경: `mvp-003`~`mvp-007` dirty는 생성 출처 확인 후 별도 처리.

## 8. 다음 작업 권장 A/B/C/D

A. 권장: `projects/paper-trading` 변경을 hunk 단위로 두 커밋으로 분리한다.

B. 그 다음: GUI 변경(`web/*`)을 별도 리뷰하고, 필요한 경우 별도 커밋으로 정리한다.

C. 그 다음: `docs/ai/jobs`의 오래된 untracked/modified 산출물을 보존할지 폐기할지 결정한다. 삭제는 자동으로 하지 않는다.

D. 마지막: `mvp-010` 이후 새 기능 작업을 시작한다. 현재 상태에서는 기능 추가보다 커밋 단위 분리가 먼저다.

Verdict: READY FOR REVIEW
