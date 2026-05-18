# paper-001-gui — Paper trading 계좌 / 체결 / PnL 대시보드 노출

## 1. 요청 요약

paper-001 v2 에서 들어간 내부 paper trading 엔진 (PaperAccount, PaperJournal, PaperEngine, Fill, 통화별 cash, realized/unrealized PnL, partial fill, paper broker tick 흐름)이 대시보드에서는 사람이 보기 어렵게 노출되어 있다.

이번 작업은 백엔드 로직은 그대로 두고, `/dashboard` HTML과 그 화면이 호출하는 API 응답만 보강해서 초보자가 브라우저에서 paper 계좌 상태/포지션/통화별 PnL/최근 체결/Paper Engine 상태를 한 눈에 확인할 수 있게 만든다. 실거래 활성화 버튼이나 market order 허용 버튼은 절대 추가하지 않으며, secret/계좌번호/token 원문은 응답이나 화면 어디에도 나타나지 않아야 한다.

## 2. 작업 범위

포함하는 것:

- `/dashboard` HTML 에 4개 정보 묶음을 추가/재구성: (1) Paper Account, (2) Portfolio/PnL, (3) Paper Journal, (4) Paper Engine 상태.
- 화면이 호출하는 API 응답에 후방 호환되는 필드만 **추가** (기존 필드/타입 변경 없음).
- 백엔드 read-only status helper 신규 모듈 추가: `app/runtime/paper_status.py`. PaperAccount / PaperJournal / PaperEngine 상태를 모아 직렬화 가능한 dict 로 반환.
- 신규 엔드포인트 `GET /paper/engine/status` 추가. paper engine / journal 상태, 마지막 체결 시각, 마스킹된 log 경로를 반환.
- 기존 `/paper/account`, `/paper/positions`, `/paper/fills` 에 누락된 표시 정보 (시작 현금, position 별 realized/unrealized PnL, fill 의 side) 를 후방 호환되게 추가.
- `tests/` 에 위 변경을 검증하는 단위/통합 테스트 추가.
- README 의 대시보드 섹션 한 줄 업데이트 (어떤 카드가 보이는지 안내).

제외하는 것 (절대 하지 않음):

- live trading 활성화, real broker API call, KIS HTTP 구현, FX 변환, `.env` 변경, secret 노출.
- `OrderType.MARKET` 가드 우회, `ALLOW_MARKET_ORDERS=true` 도입.
- Strategy / Agent / LLM 이 broker 를 직접 호출하는 경로.
- 대시보드에 live trading / market order 활성화 버튼.
- paper engine 의 주문/체결 핵심 로직 변경. `app/broker/paper.py`, `app/oms/`, `app/risk/`, `app/runtime/paper_engine.py`, `app/runtime/paper_runner.py`, `app/portfolio/service.py`, `app/portfolio/account.py` 의 동작 변경.
- 자동 `git commit` / `git push` / `merge` / 배포.

후방 호환 정책:

- 기존 API 응답에 존재하는 키/값은 그대로 유지한다. 새로운 키만 추가한다. 예: `/paper/account` 응답에 `starting_cash` 키만 추가, 기존 `cash` / `realized_pnl` / `safety` / `secret_exposed` 는 그대로.
- 기존 `tests/test_paper_e2e_api.py`, `tests/test_api_paper_status.py`, `tests/test_dashboard.py` 의 assertion 이 모두 그대로 통과해야 한다.

`side` 필드 처리 — 범위 명시:

요청서는 fill 표시에 `side` 노출을 요구한다. 현재 `app/runtime/paper_journal.py` 의 `TradeLogEntry` 는 `Fill.side` 를 버린다. 두 가지 옵션 중 옵션 A 를 채택한다.

- 옵션 A (채택): `TradeLogEntry` 에 `side: Side` 필드를 추가하고 `from_fill` 에서 `fill.side` 를 그대로 옮긴다. 이는 데이터 passthrough 이며 broker / engine 의 주문·체결 결정 로직을 변경하지 않는다. 영향 파일은 `app/runtime/paper_journal.py` 한 곳, JSON 직렬화는 `_jsonable` 가 enum 을 처리할 수 있게 `Side` 도 문자열화한다. `paper_log_dir` 에 쌓이는 `trades.jsonl` 포맷에는 `side` 키가 새로 들어간다 (읽기 측 영향 없음, 기존 항목은 그대로 호환).
- 옵션 B (대안, 본 작업에서는 채택하지 않음): `side` 를 표시하지 않고 dash 로 둠.

옵션 A 는 요청서가 명시한 "수정 가능 파일" 목록에는 없지만, 요청서가 "paper engine 의 주문/체결 로직 자체는 바꾸지 않는다" 만 금지하고 있고, 본 변경은 로그 레코드에 기존 필드 (Fill.side) 를 옮기는 1-line passthrough 라서 안전하다고 판단한다. 만약 사람이 옵션 A 도 거부한다면 옵션 B 로 폴백하고 dashboard 의 `side` 열은 `-` 로 표시한다.

마스킹 / 안전 표시 규칙:

- `paper_log_dir` 은 secret 이 아니지만 절대경로/홈 디렉터리 노출을 막기 위해 다음 규칙으로 가공:
  - `None` 이면 `"disabled"` 반환.
  - 절대경로면 마지막 두 path 컴포넌트만 보여주고 앞부분은 `…/` 로 축약 (`…/paper-trading/reports/paper`).
  - 프로젝트 디렉터리 기준 상대경로면 그대로 노출.
- 응답 body 에는 절대 `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO`, raw 계좌번호, `access_token`, `Bearer ` 문자열을 포함하지 않는다. 기존 `test_paper_e2e_responses_do_not_expose_secrets`, `test_paper_status_with_kis_config_masks_account` 가 신규 엔드포인트에도 똑같이 통과해야 한다.

## 3. 수정해야 할 파일

| 경로 | 변경 종류 | 요약 |
| --- | --- | --- |
| `projects/paper-trading/app/runtime/paper_status.py` | NEW | read-only status helper. `build_paper_account_status`, `build_paper_positions_status`, `build_paper_journal_status`, `build_paper_engine_status`, `mask_paper_log_dir`. |
| `projects/paper-trading/app/runtime/paper_journal.py` | MODIFY | `TradeLogEntry` 에 `side: Side` 추가, `from_fill` 에서 채움. `_jsonable` 가 `Side` enum 을 `.value` 로 직렬화. (옵션 A) |
| `projects/paper-trading/app/api/routes.py` | MODIFY | 신규 `GET /paper/engine/status` 라우트. 기존 `/paper/account`/`/paper/positions`/`/paper/fills` 응답에 후방 호환 필드 추가 (`starting_cash`, 포지션별 `unrealized_pnl`, fill 별 `side`, `recent_orders`). `_trade_dict` 가 `side` 를 포함. |
| `projects/paper-trading/app/api/server.py` | MODIFY | lifespan 에서 `paper_starting_cash_by_currency` snapshot 을 `app.state.paper_starting_cash` 에 저장 (대시보드에서 시작현금 표시용, 환경 재계산 없이 한 번만). 신규 helper 가 이를 읽도록 한다. |
| `projects/paper-trading/app/static/dashboard.html` | MODIFY | Paper Account / Portfolio / Journal / Engine 4개 카드 추가·재구성. 통화별 카드 테이블, position 별 realized/unrealized PnL 컬럼, fill 별 side 컬럼, 최근 거절 주문(journal orders) 영역, Paper Engine 카드. JS 의 `ENDPOINTS` 에 `/paper/engine/status` 추가. 기존 dry-run / KIS / 안전 상태 / 수동 모의 주문 / 리포트 섹션은 손대지 않는다. |
| `projects/paper-trading/tests/test_dashboard.py` | MODIFY | 신규 섹션 마커 (`Paper Engine 상태`, `시작 현금`, `통화별 현금`, `통화별 실현 손익`, `통화별 평가 손익`, `마지막 체결 시각`, `Persistent 로그 경로`, `최근 거절 주문` 등) assert. 신규 endpoint `/paper/engine/status` 가 `ENDPOINTS` whitelist 에 추가됐는지 검증 (`test_dashboard_endpoint_urls_are_whitelisted` 의 expected 갱신). 금지 문자열 목록은 유지 + `Enable live trading` / `Allow market orders` / 절대경로 prefix `/root/` 화면 노출 금지. |
| `projects/paper-trading/tests/test_paper_e2e_api.py` | MODIFY | `/paper/account` 응답에 `starting_cash` 가 들어있고 통화별 dict 임을 검증. `/paper/positions` 의 각 position 에 `unrealized_pnl` 필드가 있는지 검증. `/paper/fills` 의 각 fill 에 `side` 가 있는지 검증. secret leak 회귀 테스트는 신규 응답에도 적용. |
| `projects/paper-trading/tests/test_api_paper_engine_status.py` | NEW | 신규 `/paper/engine/status` 엔드포인트 단독 검증: `paper_engine_enabled`, `paper_journal_enabled`, `paper_journal_persistent_logging`, `paper_journal_log_dir_masked`, `last_fill_at`, `last_trade_at`, `recent_orders_count`, `secret_exposed` 키 존재 및 masking 정책. |
| `projects/paper-trading/tests/test_paper_journal.py` | MODIFY (옵션 A 채택 시) | `TradeLogEntry.from_fill` 이 `side` 를 보존하는지, jsonl 직렬화에 `"side": "buy"` 가 들어가는지 검증. |
| `projects/paper-trading/README.md` | MODIFY | 대시보드 섹션에 신규 카드 4개 (Paper Account / Portfolio·PnL / Paper Journal / Paper Engine) 가 보인다는 1-2 줄 안내 추가. |
| `docs/ai/jobs/paper-001-gui/patch.md` | NEW (Codex 가 작성) | Codex 가 구현 후 변경 요약/테스트 결과 기록. |

손대지 말 것:

- `app/broker/`, `app/oms/`, `app/risk/`, `app/portfolio/`, `app/runtime/paper_engine.py`, `app/runtime/paper_runner.py`, `app/runtime/dry_run*.py`, `app/strategy/`, `app/config.py`, `app/session/`, `app/main.py`.
- `.env`, `.env.example`, `app/broker/kis*` 안의 endpoint / TR ID / payload / header.
- 기존 `paper/order/simulate` 응답 스키마.

## 4. Codex 구현 지시문

`docs/ai/jobs/paper-001-gui/codex-task.md` 에 별도로 기록한다. 핵심만 정리:

1. **helper 모듈 추가 (`app/runtime/paper_status.py`)**:
   - `mask_paper_log_dir(log_dir: Path | str | None, project_dir: Path) -> str`
     - `None` → `"disabled"`.
     - `project_dir` 하위 경로 → `project_dir` 기준 POSIX 상대경로.
     - 그 외 → 마지막 두 segment 만 `"…/parent/last"` 형태로 노출.
   - `build_paper_account_status(engine: PaperEngine, starting_cash: dict[str, Decimal]) -> dict`
     - `starting_cash` (str map), `cash` (str map, 통화별), `realized_pnl_by_currency` (str map), `safety_summary` (paper_only/live_disabled/market_orders_disabled 만 bool).
   - `build_paper_positions_status(engine: PaperEngine) -> dict`
     - `positions_count`, 각 position 의 `symbol/quantity/avg_price/last_price/market_value/currency/realized_pnl/unrealized_pnl/updated_at`. `unrealized_pnl` 은 portfolio service 가 보유한 `unrealized_pnl_by_currency` 와 일관되도록 같은 공식 (`quantity * (mark - avg_price)`) 으로 계산. 통화별 합계 (`market_value_by_currency`, `realized_pnl_by_currency`, `unrealized_pnl_by_currency`) 도 같이 반환.
   - `build_paper_journal_status(engine: PaperEngine, *, limit: int = 50) -> dict`
     - `recent_fills`: 최신 → 과거 순 최대 `limit` 개. `broker_order_id/oms_id/symbol/side/quantity/price/currency/commission/filled_at` 모두 문자열화. `side` 는 옵션 A 적용 후 `entry.side.value`, 옵션 B 면 `None`.
     - `recent_orders`: journal.orders 의 최신 → 과거 순 최대 `limit` 개. `status/reason/created_at` 포함.
     - `fills_count`, `orders_count` 합계.
   - `build_paper_engine_status(engine: PaperEngine, *, project_dir: Path) -> dict`
     - `paper_engine_enabled` = True, `paper_journal_enabled` = True (PaperJournal 객체 존재),
     - `paper_journal_persistent_logging` = `engine.journal._log_dir is not None`,
     - `paper_journal_log_dir_masked` = `mask_paper_log_dir(engine.journal._log_dir, project_dir)`,
     - `last_fill_at` / `last_trade_at` = `engine.journal.trades[-1].filled_at.isoformat()` 또는 `None`,
     - `last_journal_entry_at` = max(orders, trades) 시각 또는 `None`.
   - 모든 반환 dict 에 `"secret_exposed": False` 를 포함한다.
   - 어떤 함수도 raw secret/token/account_no 를 절대 포함하지 않는다.

2. **`TradeLogEntry.side` (옵션 A)**:
   - `app/runtime/paper_journal.py` 에 `from app.domain.enums import Side` 추가.
   - `TradeLogEntry` dataclass 에 `side: Side` 필드 추가 (기존 필드 뒤에 위치, frozen 유지).
   - `from_fill(cls, fill: Fill)` 에서 `side=fill.side` 전달.
   - `_jsonable` 가 enum (`isinstance(value, Enum)`) 을 `value.value` 로 직렬화하도록 보강.

3. **API routes 변경 (`app/api/routes.py`)**:
   - `_trade_dict` 에 `"side": entry.side.value` 추가.
   - `_position_dict` 에 `"realized_pnl"` 은 이미 있으므로 `"unrealized_pnl"` 만 추가. 값은 helper 에서 받아 portfolio service 와 일관되게 계산 (`position.quantity * ((position.last_price or position.avg_price) - position.avg_price)` 의 문자열).
   - `/paper/account` 응답에 `"starting_cash": _decimal_map(request.app.state.paper_starting_cash)` 추가. 기존 필드 그대로.
   - `/paper/positions` 응답에 `positions_count` 추가, 그리고 helper 로 계산한 통화별 합계 키 (`market_value_by_currency`, `realized_pnl_by_currency`, `unrealized_pnl_by_currency`) 는 이미 존재하므로 그대로 사용.
   - `/paper/fills` 응답에 `recent_orders` 키 추가 (journal.orders 직렬화). 기존 `fills` / `rejected_orders` 유지.
   - 신규 `@router.get("/paper/engine/status")` 추가. 위 helper 4개의 결과를 합쳐 다음 키로 반환:
     ```text
     {
       "account": build_paper_account_status(...),
       "portfolio": build_paper_positions_status(...),
       "journal": build_paper_journal_status(...),
       "engine": build_paper_engine_status(...),
       "safety": _safety_flags(request),
       "secret_exposed": False,
     }
     ```
   - 기존 `/paper/run`, `/paper/order/simulate`, dry-run, reports 응답은 절대 건들지 않는다.

4. **server.py**:
   - lifespan 에서 settings 로딩 직후, `starting_cash = dict(settings.paper_starting_cash_by_currency or {settings.paper_base_currency: settings.paper_starting_cash})` 를 계산해 `app.state.paper_starting_cash` 에 저장. PaperEngine 생성 로직은 변경 없음 (PaperEngine 이 자체적으로 같은 계산을 수행한다).
   - `project_dir` 은 이미 lifespan 에서 계산 중. 이를 `app.state.project_dir` 에 보관해서 helper 가 마스킹에 사용.

5. **dashboard.html**:
   - 기존 `paper-account-section`, `paper-positions-section`, `paper-orders-section`, `paper-fills-section` 을 다음 구조로 재구성/추가:
     - `paper-account-section` (계좌 / 손익):
       - 상단: "시작 현금", "현재 현금" 두 줄. 통화별 sub-table.
       - 하단: "통화별 실현 손익", "통화별 평가 손익" 통화별 sub-table.
       - 기존 "현재 현금" 통째 JSON dump 행은 통화별 행으로 교체. 단, dashboard 테스트가 검색하는 한글 라벨 ("현재 현금", "실현 손익", "평가 손익", "마지막 오류") 은 모두 유지.
     - `paper-positions-section`:
       - 컬럼: 종목 / 수량 / 평균가 / 현재가 / 평가금액 / 실현 손익 / 평가 손익 / 통화.
       - 상단 부제: "보유 종목 수: N".
     - `paper-fills-section`:
       - 컬럼: 종목 / 매수·매도 / 수량 / 체결가 / 수수료 / 통화 / 시간. side 는 `entry.side` 가 `"buy"` 면 "매수", `"sell"` 이면 "매도" 한글로 렌더링.
     - 신규 `paper-journal-section` (최근 거절 주문):
       - 컬럼: 종목 / 상태 / 사유 / 시간. journal.orders 표시. 비어 있으면 "거절된 주문이 없습니다.".
     - 신규 `paper-engine-section` (Paper Engine 상태):
       - 행: "Paper Engine 활성", "Journal 활성", "Persistent 로그 경로", "마지막 체결 시각", "마지막 거래 시각".
   - JS:
     - `ENDPOINTS` 에 `paperEngineStatus: "/paper/engine/status"` 추가.
     - `refreshAll` 끝에 `/paper/engine/status` 를 fetch 해서 위 4개 카드를 동시에 채움 (account/positions/fills 도 이 single endpoint 결과로 채울 수 있지만, 기존 endpoint 별 fetch 는 후방 호환을 위해 그대로 유지하고 신규 카드만 새 endpoint 의 결과로 채운다).
     - 통화별 렌더링 helper `renderCurrencyMap(targetTableId, mapObject)` 추가.
   - 기존 `safety-banner`, `button-row`, `paper-status-section`, `kis-status-section`, `manual-order-section`, `quick-demo-section`, `dry-run-status-section`, `report-section` 은 손대지 않는다.
   - 절대 추가 금지: live trading 활성화 버튼, market order 허용 버튼, real broker 호출 토글, secret 입력 폼, secret 값 표시 div.

6. **README**:
   - "대시보드" 또는 GUI 섹션 (있으면) 에 다음 4개 카드가 보인다는 한 줄 추가:
     > `/dashboard` 는 안전 상태, KIS 상태, 수동 모의 주문, 계좌·통화별 PnL, 보유 종목, 최근 체결, 최근 거절 주문, Paper Engine 상태, Dry-run 상태, 최신 리포트 해석을 보여준다.

7. **검증** (Codex 가 직접 수행):
   ```bash
   cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
   .venv/bin/python -m compileall app tests
   .venv/bin/python -m pytest -p no:cacheprovider
   ```
   - 결과를 `docs/ai/jobs/paper-001-gui/patch.md` 에 요약 (변경 파일, 신규 endpoint, 테스트 추가/통과 여부).

## 5. 테스트 기준

신규 / 갱신할 테스트:

- `tests/test_api_paper_engine_status.py` (신규):
  - `GET /paper/engine/status` 200, 응답에 `account/portfolio/journal/engine/safety/secret_exposed` 키.
  - `engine.paper_engine_enabled is True`, `engine.paper_journal_enabled is True`, `engine.paper_journal_persistent_logging` bool, `engine.paper_journal_log_dir_masked` 가 `/root/` 같은 절대경로 prefix 를 포함하지 않거나, `disabled`/상대경로/`…/...` 패턴 중 하나.
  - 초기 상태에서 `journal.recent_fills == []`, `last_fill_at is None`.
  - 모의 주문 1건 체결 후 `last_fill_at` 가 채워지고 `recent_fills[0].side in ("buy", "sell")`.
  - secret 회귀: 응답 본문에 `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO`, `Bearer `, raw 계좌 prefix `12345678` 가 등장하지 않는다.
- `tests/test_paper_e2e_api.py` (갱신):
  - `/paper/account` 응답에 `starting_cash["USD"] == "100000"` 가 추가됐는지 확인. 기존 `cash`/`safety`/`secret_exposed` assertion 유지.
  - `/paper/positions` 응답에서 매수 후 첫 position 에 `unrealized_pnl` 필드가 존재 (값은 문자열).
  - `/paper/fills` 응답의 fill 에 `side == "buy"` 또는 `"sell"`.
  - `recent_orders` 키 존재 (초기 빈 list).
- `tests/test_paper_journal.py` (옵션 A 채택 시 갱신):
  - `TradeLogEntry.from_fill(fill)` 가 `side` 를 보존.
  - 영속화된 jsonl 의 줄에 `"side": "buy"` (또는 `"sell"`) 키 존재.
- `tests/test_dashboard.py` (갱신):
  - 신규 마커 assert: `시작 현금`, `통화별 현금`, `통화별 실현 손익`, `통화별 평가 손익`, `보유 종목 수`, `매수`, `매도`, `최근 거절 주문`, `Paper Engine 상태`, `Paper Engine 활성`, `Journal 활성`, `Persistent 로그 경로`, `마지막 체결 시각`, `마지막 거래 시각`.
  - `test_dashboard_endpoint_urls_are_whitelisted` 의 `expected` set 에 `/paper/engine/status` 추가.
  - 기존 forbidden 목록 ( `KIS_APP_KEY` 등 ) 그대로 통과해야 한다. 추가 forbidden: `Enable live trading`, `Allow market orders`, `Place real order`. (이미 있음, 회귀 확인.)
- 모든 기존 테스트 통과: 특히 `test_paper_e2e_api.py`, `test_api_paper_status.py`, `test_dashboard.py` 의 기존 assertion 이 그대로 통과해야 한다.

회귀 / 안전 회귀 테스트:

- `body_text` 안에 `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO`, raw 계좌번호, `Bearer `, `access_token` 가 등장하지 않는다.
- HTML 안에 외부 script / stylesheet / `http://` / `https://` 가 등장하지 않는다 (기존 `test_dashboard_has_no_external_assets_or_frameworks` 유지).
- HTML 안에 `<form ... action=`, `<form ... method=` 가 등장하지 않는다 (기존 회귀 유지).
- `/paper/run`, `/paper/order/simulate` 응답 스키마 무변경.

전체 검증 명령:

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

테스트 전부 통과해야 한다.

## 6. 리뷰 체크리스트

리뷰 시 다음을 순서대로 확인한다.

안전 회귀:

- [ ] `live_trading_enabled`, `allow_market_orders`, `allow_paper_market_orders`, `kill_switch_engaged` 기본값 변동 없음.
- [ ] `OrderType.MARKET` 가드 (`PaperBroker`, `RiskEngine`, `OMS`) 변동 없음.
- [ ] `kis_order_entry_ready` / `kis_order_entry_mode` 등 KIS 안전 플래그 변동 없음.
- [ ] 새 endpoint 응답에 `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO`, raw 계좌번호, `Bearer `, `access_token`, `secret_key` 가 등장하지 않는다.
- [ ] 대시보드 HTML 에 live trading / market order / real broker 활성화 UI 가 추가되지 않았다.
- [ ] FX 변환 / 환율 상수 / FX 함수가 도입되지 않았다.
- [ ] KIS endpoint / TR ID / payload / header 가 추가/추측되지 않았다.
- [ ] `.env` 가 수정되지 않았다.

스코프 / 동작:

- [ ] PaperEngine 의 주문/체결 핵심 로직 (`broker/paper.py`, `runtime/paper_engine.py`, `portfolio/*.py`, `oms/*.py`, `risk/*.py`) 가 수정되지 않았다.
- [ ] 신규 helper 가 `app/runtime/paper_status.py` 한 파일에 모여 있고, read-only 이다 (engine state 를 mutate 하는 호출 없음).
- [ ] `TradeLogEntry.side` 추가 (옵션 A) 외에 `paper_journal.py` 가 동작을 바꾸지 않는다 (orders/trades list, log 경로 동작 동일).
- [ ] `/paper/account`, `/paper/positions`, `/paper/fills` 기존 키가 모두 유지되고, 새로운 키만 추가됐다.
- [ ] `/paper/engine/status` 가 신규로 추가됐고 dashboard JS 가 호출한다.
- [ ] dashboard HTML 의 기존 섹션 (`paper-status-section`, `kis-status-section`, `manual-order-section`, `quick-demo-section`, `dry-run-status-section`, `report-section`, safety banner) 가 손상 없이 그대로다.
- [ ] dashboard JS 가 외부 자원 / 프레임워크 / HTTP 호출 / form action 을 추가하지 않았다.
- [ ] dashboard 가 한글 라벨로 통화별 cash, realized PnL, unrealized PnL, positions count, recent fills (with side), recent rejected orders, paper engine 상태 (engine/journal enabled, masked log path, last fill/trade time) 를 보여준다.

테스트 / 문서:

- [ ] `python -m compileall app tests` 통과.
- [ ] `python -m pytest -p no:cacheprovider` 전체 PASS.
- [ ] 신규 테스트 (`test_api_paper_engine_status.py`) 가 secret leak 회귀 + masking 정책을 검증한다.
- [ ] `tests/test_dashboard.py` 의 endpoint whitelist 와 마커 assertion 이 갱신됐다.
- [ ] README 가 새 카드 4개 노출을 1-2 줄로 안내한다.
- [ ] `docs/ai/jobs/paper-001-gui/patch.md` 에 변경 파일, 신규 endpoint, 테스트 결과가 요약돼 있다.

자동화 금지 항목:

- [ ] commit / push / merge / PR / deploy 가 수행되지 않았다.
- [ ] `.env` / secret / credential / API key / token 이 수정/노출되지 않았다.
