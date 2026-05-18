# paper-001-gui — Claude 리뷰

## 최종 판정

**APPROVE**

`/dashboard` 노출 4 종 (Paper Account / Portfolio·PnL / Paper Journal / Paper Engine) 가 plan 과 codex-task 대로 추가됐고, 안전 회귀 (live trading / market order / 실거래 broker / KIS HTTP / FX / `.env` / secret) 가 모두 유지되며, 신규 `/paper/engine/status` 는 read-only 이고, 후방 호환 (`/paper/account`, `/paper/positions`, `/paper/fills`) 이 유지된다. 신규/갱신 테스트는 secret 마스킹과 leak 회귀를 검증하고, 보고된 `320 passed` 와 일치한다. commit / push / merge / deploy 가 수행되지 않았다.

## Findings (severity 순)

### Critical

없음.

### Major

없음.

### Minor / 관찰사항

1. **`/paper/fills.recent_orders` 와 기존 `rejected_orders` 가 사실상 동일한 데이터** — `recent_orders` 는 `reversed(journal.orders[-50:])`, `rejected_orders` 는 `journal.orders` 전체. 호출자는 두 키가 어떻게 다른지 알기 어렵다. 의도된 후방 호환 패턴이라 BLOCK 사유는 아니지만, 후속 작업에서 `rejected_orders` 를 deprecate 하거나 docstring/README 한 줄 추가를 권장한다 (`app/api/routes.py:197-205`).

2. **`/paper/account.realized_pnl` 는 항상 `{}` 에 가깝다** — `PaperAccount.apply_fill` 가 매도 시 `self.realized_pnl[currency] = self.realized_pnl.get(currency, Decimal("0"))` 만 실행하고 실제 PnL 을 누적하지 않는다 (`app/portfolio/account.py:48-50`). 실제 실현 손익은 `PortfolioService.realized_pnl_by_currency` 에 들어 있다. paper-001-gui 가 만든 회귀가 아니며 후방 호환 정책 (기존 키 변경 금지) 때문에 그대로 둔 것이 맞다. 대시보드 카드 "통화별 실현 손익" 은 portfolio snapshot 을 읽으므로 사용자에게 보이는 값은 정확하다. 후속 정리 후보로 기록만 한다.

3. **`paper-account-section` 의 `<span id="acct-cash">`, `<span id="acct-realized">`, `<span id="acct-unrealized">` 잔류** — 신규 통화별 sub-table 옆에 raw JSON span 도 함께 렌더된다 (`app/static/dashboard.html:115-117`, `app/static/dashboard.html:357-362`). 기존 테스트 (`현재 현금`, `실현 손익`, `평가 손익` 마커) 를 보존하기 위한 의도된 선택. 사용자 화면에서 약간의 중복이 있지만 잘못된 정보는 아니며, 후속 UX 개선 때 라벨/레이아웃 정리 후보.

4. **`build_paper_engine_status` 가 `engine.journal._log_dir` private 속성을 직접 읽음** (`app/runtime/paper_status.py:118-119`). Plan 이 명시적으로 채택한 접근이고 paper_journal.py 의 동작은 바꾸지 않았다. 후속에서 `PaperJournal.log_dir` 같은 read-only property 를 노출하는 게 더 깔끔하지만 본 작업 범위에서는 허용된 절충이다.

5. **`last_trade_at` 와 `last_fill_at` 가 동일 출처** (`app/runtime/paper_status.py:120-121`). 이 코드베이스에서 trade == fill 이므로 의도된 결정이고 `test_paper_engine_status_after_fill` 가 명시적으로 동일성을 검증한다. 요청서가 두 시각을 구분해 표시하라고 한 점은 충족했다.

6. **`scripts/_common.sh` / `scripts/start_server.sh` 변경분이 git status 에 잡혀 있음** — 이 변경은 paper-001-gui 작업이 시작되기 전부터 unstaged 였고 (`git log` 상 마지막 commit `df5fe7f` 이후 working tree 에 이미 있었음), Codex 가 추가로 건드린 흔적이 없다. 본 작업 scope 외 변경이므로 paper-001-gui 책임 범위 밖.

## 안전 / 정책 회귀 체크리스트

- [x] `LIVE_TRADING_ENABLED`, `ALLOW_MARKET_ORDERS`, `ALLOW_PAPER_MARKET_ORDERS`, `KILL_SWITCH_ENGAGED` 기본값/가드 변동 없음. `/paper/status` 응답 스키마에 신규 키 (`last_error` 외엔) 추가 없음. `OrderType.MARKET` 가드 우회 없음.
- [x] 대시보드에 live trading 활성화 버튼이 추가되지 않았다. `test_dashboard_has_no_forbidden_strings` 가 `Enable live trading`, `live trading 활성화`, `Allow market orders`, `Submit real order`, `Place real order` 부재를 회귀 검증.
- [x] 대시보드에 market order 허용 버튼이 추가되지 않았다.
- [x] KIS endpoint / TR ID / payload / header 가 새로 추가되지 않았다. `app/broker/kis*` 변경 없음.
- [x] 실제 broker API 호출이 추가되지 않았다. PaperBroker / OMS / RiskEngine 변경 없음.
- [x] `.env` 가 수정되지 않았다. secret / API key / token / 계좌번호 raw 값이 응답이나 HTML 에 등장하지 않는다. `test_paper_engine_status_masks_sensitive_values` 가 `/root/`, `/home/`, `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO`, `Bearer `, `access_token`, raw 계좌번호 `12345678` 부재를 검증한다.
- [x] FX 변환 함수 / 환율 상수 / 통화 통합 합계가 도입되지 않았다. 모든 PnL / cash 가 통화별로만 노출된다.
- [x] 기존 dry-run 대시보드 섹션 (`dry-run-status-section`) 및 관련 API (`/paper/dry-run/start|stop|tick|status`) 가 그대로 동작한다. `test_dashboard_has_required_sections_and_buttons` 에서 `Dry-run 상태`, `상태 새로고침`, `Tick 1회 실행`, `Dry-run 시작`, `Dry-run 중지`, `리포트 분석`, `최신 리포트 보기` 마커 유지.
- [x] 기존 API 응답 후방 호환: `/paper/account` 의 `cash`/`realized_pnl`/`safety`/`secret_exposed` 유지 + `starting_cash` 만 추가. `/paper/positions` 의 모든 기존 키 유지 + `positions_count` 와 position 별 `unrealized_pnl` 만 추가. `/paper/fills` 의 `fills`/`rejected_orders`/`secret_exposed` 유지 + `recent_orders` 만 추가. 각 fill 의 `side` 키 추가. 기존 `_paper_e2e` 테스트가 그대로 통과한다.
- [x] `/paper/engine/status` 가 read-only. 4 개 helper (`build_paper_account_status`, `build_paper_positions_status`, `build_paper_journal_status`, `build_paper_engine_status`) 가 portfolio snapshot / journal list / cash dict 를 읽기만 하고 mutate 하지 않는다.
- [x] 자동 git commit / push / merge / deploy 가 수행되지 않았다 (working tree 가 unstaged, `df5fe7f` 이후 추가 commit 없음).

## 산출물 vs 계획 대조

| Plan 항목 | 구현 위치 | 결과 |
| --- | --- | --- |
| `app/runtime/paper_status.py` 신규 helper 4 종 | `app/runtime/paper_status.py:13-128` | OK. `mask_paper_log_dir` 가 None→`disabled`, project 하위→relative, 그 외 절대경로→`…/{parent}/{last}` 처리. |
| `TradeLogEntry.side` 옵션 A | `app/runtime/paper_journal.py:28,41-46,86-87` | OK. `_jsonable` 가 Enum 처리. |
| `/paper/account.starting_cash` | `app/api/routes.py:169-178` | OK. 기존 키 유지. |
| `/paper/positions.positions_count`, position 별 `unrealized_pnl` | `app/api/routes.py:181-194`, `app/api/routes.py:375-388` | OK. 통화별 합계 키도 그대로 유지. |
| `/paper/fills.recent_orders`, fill 별 `side` | `app/api/routes.py:197-205`, `app/api/routes.py:391-402` | OK. 기존 `rejected_orders` 도 유지. |
| 신규 `/paper/engine/status` | `app/api/routes.py:208-218` | OK. `account/portfolio/journal/engine/safety/secret_exposed` 6 키. |
| `server.py` lifespan 보강 | `app/api/server.py:22-27`, `app/api/server.py:62-63` | OK. `app.state.paper_starting_cash`, `app.state.project_dir` 노출. 기존 객체 생성 순서/동작 변동 없음. |
| Dashboard 4 카드 추가 + currency map 렌더링 | `app/static/dashboard.html:111-152`, `app/static/dashboard.html:246-308`, `app/static/dashboard.html:389-406` | OK. `paper-journal-section`, `paper-engine-section` 신규. `renderCurrencyMap`, `renderRejectedOrders` 신규. fill side 한글 매핑. positions 컬럼 확장. |
| Dashboard `ENDPOINTS` 추가 | `app/static/dashboard.html:190-205` | OK. `paperEngineStatus: "/paper/engine/status"`. `test_dashboard_endpoint_urls_are_whitelisted` whitelist 갱신. |
| 테스트 추가/갱신 | `tests/test_api_paper_engine_status.py` (NEW), `tests/test_dashboard.py`, `tests/test_paper_e2e_api.py`, `tests/test_paper_journal.py` | OK. patch.md 가 `320 passed` 보고. |
| README 안내 1 줄 | `README.md:317` | OK. |

## 누락 / 후속 작업 후보 (블로커 아님)

- `rejected_orders` 키와 `recent_orders` 키의 의미 차이 1 줄 docstring/README 보완.
- `PaperJournal.log_dir` read-only property 노출 (현재는 helper 가 private 속성 직접 접근).
- `PaperAccount.realized_pnl` 가 실제 PnL 을 누적하도록 수정할지, 아니면 키 자체를 deprecate 할지 결정 (별도 job 권장).
- `paper-account-section` 의 raw JSON span 잔류 정리 (UX 개선 후속).
- 대시보드 테이블 paging/filtering (patch.md 가 후속 작업으로 기록).

## 결론

요청서 (`request.ko.md`) 의 목표와 절대 하지 말 것 항목, plan 의 범위와 codex-task 의 단계별 지시문을 모두 충족했다. 안전 회귀와 후방 호환이 보장되고, 신규 테스트가 masking·leak 회귀를 명시적으로 검증한다. 위 Minor 관찰사항은 사용자가 다음 GUI/리팩토링 job 에서 다루면 충분하다.

**APPROVE**. 이후 commit / push / merge 는 사람이 직접 수행한다.
