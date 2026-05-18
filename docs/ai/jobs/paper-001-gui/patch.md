# paper-001-gui — Codex 구현 요약

## 변경된 파일

- `projects/paper-trading/app/runtime/paper_status.py`
- `projects/paper-trading/app/runtime/paper_journal.py`
- `projects/paper-trading/app/api/routes.py`
- `projects/paper-trading/app/api/server.py`
- `projects/paper-trading/app/static/dashboard.html`
- `projects/paper-trading/tests/test_api_paper_engine_status.py`
- `projects/paper-trading/tests/test_dashboard.py`
- `projects/paper-trading/tests/test_paper_e2e_api.py`
- `projects/paper-trading/tests/test_paper_journal.py`
- `projects/paper-trading/README.md`
- `docs/ai/jobs/paper-001-gui/patch.md`

## 새 endpoint / API 응답 변화

- 신규 `GET /paper/engine/status`
  - `account`: 시작 현금, 현재 현금, 통화별 실현 손익, 통화 목록.
  - `portfolio`: 포지션 수, 포지션별 실현/평가 손익, 통화별 평가금액/손익.
  - `journal`: 최신 체결, 최신 거절 주문, 전체 fill/order 수.
  - `engine`: Paper Engine/Journaling 활성 상태, masked journal log 경로, 마지막 체결/거래 시각.
  - `safety`, `secret_exposed`.
- `/paper/account`
  - 기존 키 유지.
  - `starting_cash` 추가.
- `/paper/positions`
  - 기존 키 유지.
  - `positions_count` 추가.
  - 각 position에 `unrealized_pnl` 추가.
- `/paper/fills`
  - 기존 `fills`, `rejected_orders`, `secret_exposed` 유지.
  - 각 fill에 `side` 추가.
  - `recent_orders` 추가.
- Dashboard
  - 시작 현금, 통화별 현금, 통화별 실현/평가 손익 카드 보강.
  - 포지션별 실현/평가 손익 컬럼 추가.
  - 체결 내역에 매수/매도 컬럼 추가.
  - 최근 거절 주문 카드 추가.
  - Paper Engine 상태 카드 추가.

## 테스트 결과

- compileall: OK
- pytest: `320 passed in 0.66s`
- 신규 / 갱신된 테스트 목록
  - `tests/test_api_paper_engine_status.py`
  - `tests/test_dashboard.py`
  - `tests/test_paper_e2e_api.py`
  - `tests/test_paper_journal.py`

## 안전 회귀 확인

- live trading / market order 비활성 상태 유지.
- KIS endpoint / TR ID / payload 추가 없음.
- 실제 broker API 호출 추가 없음.
- FX 변환 / 환율 상수 / 통합 base currency 계산 추가 없음.
- secret / 계좌번호 / token 노출 없음.
- 신규 `/paper/engine/status` 응답은 secret masking 테스트를 통과.
- 금지 파일 diff 확인: `app/broker/*`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/paper_engine.py`, `app/runtime/paper_runner.py`, `app/runtime/dry_run*.py`, `app/strategy/*`, `app/config.py`, `app/main.py`, `app/session/*` 변경 없음.
- 자동 git commit / push / merge / deploy 수행 안 함.

## 알려진 한계 / 후속 작업

- Paper journal은 현재 in-memory 상태가 기본이며, persistent logging이 설정되지 않으면 log path는 `disabled`로 표시된다.
- 대시보드 테이블이 커질 경우 paging/filtering은 후속 UX 작업에서 다룬다.

READY FOR REVIEW
