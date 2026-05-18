# Codex 작업 지시문 — paper-001-gui

## 0. 너의 역할

너는 Codex 구현자다. 이 문서와 `plan.md` 만 따른다. 범위를 임의로 넓히지 않는다. 안전 규칙을 위반하지 않는다. commit / push / merge / deploy 는 절대 하지 않는다. `.env`, secret, API key, token 을 읽지도 쓰지도 않는다.

## 1. 컨텍스트

`projects/paper-trading/` 안에 paper trading runtime 이 이미 들어있다. PaperAccount (cash by currency), PaperJournal (orders / trades), PaperEngine (broker tick → fill → portfolio → journal), Fill (side 포함), PortfolioService (per-currency realized / unrealized / market value) 가 동작한다. `/dashboard` 는 이미 안전 상태 / KIS 상태 / 수동 모의 주문 / 보유 종목 / 체결 내역 / Dry-run / 리포트 카드를 보여주지만, 통화별 cash 가 raw JSON 으로만 나오고, 시작 현금, 포지션별 realized/unrealized PnL, fill 의 side, 최근 거절 주문, Paper Engine 상태가 노출되지 않는다.

이번 작업은 `/dashboard` HTML 과 그 화면이 호출하는 API 응답을 보강해서 초보자가 paper 계좌·체결·PnL·Engine 상태를 한 화면에서 볼 수 있게 만든다.

## 2. 절대 금지

- live trading 활성화. `LIVE_TRADING_ENABLED=true` 도입 금지.
- `ALLOW_MARKET_ORDERS=true`, `OrderType.MARKET` 가드 우회.
- 실제 broker API 호출.
- KIS endpoint / TR ID / payload / header 추측, KIS 주문·시세·계좌 HTTP 구현.
- Strategy / Agent / LLM 이 broker 를 직접 호출하는 경로 추가.
- Agent / LLM 이 executable order 를 만들게 하는 변경.
- FX 변환 함수 / 환율 상수 도입.
- `.env`, secret, API key, token, 계좌번호 raw 값 읽기 / 쓰기 / 응답·HTML 노출.
- `app key`, `app secret`, `계좌번호`, `access_token`, `Bearer ` 문자열이 응답 body 나 HTML 에 등장.
- 대시보드에 live trading / market order / real broker 활성화 버튼·토글·폼.
- `git commit`, `git push`, `git merge`, PR merge, deploy.
- `app/broker/paper.py`, `app/oms/`, `app/risk/`, `app/portfolio/`, `app/runtime/paper_engine.py`, `app/runtime/paper_runner.py`, `app/runtime/dry_run*.py`, `app/strategy/`, `app/config.py`, `app/session/`, `app/main.py`, `app/broker/kis*` 의 변경. (paper_status helper 추가, paper_journal.py 의 `TradeLogEntry.side` passthrough 만 예외로 허용.)
- 기존 `paper/order/simulate`, `paper/run`, `paper/status`, dry-run, reports 응답 스키마 변경.

## 3. 수정·생성 파일

수정·생성 가능한 파일은 다음으로 제한한다.

생성 (NEW):

- `projects/paper-trading/app/runtime/paper_status.py` — read-only status helper.
- `projects/paper-trading/tests/test_api_paper_engine_status.py` — 신규 엔드포인트 검증.
- `docs/ai/jobs/paper-001-gui/patch.md` — 구현 후 너의 요약.

수정 (MODIFY):

- `projects/paper-trading/app/runtime/paper_journal.py` — `TradeLogEntry` 에 `side` 추가 + `_jsonable` 가 Enum 처리. 그 외 동작 변경 금지.
- `projects/paper-trading/app/api/routes.py` — 신규 `/paper/engine/status` 라우트 + 기존 응답에 후방 호환 필드 추가. 기존 키 / 타입 / 동작 보존.
- `projects/paper-trading/app/api/server.py` — lifespan 에서 `app.state.paper_starting_cash`, `app.state.project_dir` 채움. 그 외 변경 금지.
- `projects/paper-trading/app/static/dashboard.html` — 4개 카드 추가/재구성. 기존 섹션/JS 유틸/`safety-banner`/`button-row` 손상 금지.
- `projects/paper-trading/tests/test_dashboard.py` — 신규 마커 / endpoint whitelist 갱신. 기존 assert 보존.
- `projects/paper-trading/tests/test_paper_e2e_api.py` — `starting_cash`, position 별 `unrealized_pnl`, fill 별 `side`, `recent_orders` 검증 추가. 기존 assert 보존.
- `projects/paper-trading/tests/test_paper_journal.py` — `TradeLogEntry.side` 보존 + jsonl 직렬화 검증.
- `projects/paper-trading/README.md` — 대시보드 카드 안내 1-2 줄 추가.

위 목록 외 파일은 절대 수정하지 않는다. 특히 `app/broker/*`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/paper_engine.py`, `app/runtime/paper_runner.py`, `app/runtime/dry_run*.py`, `app/strategy/*`, `app/config.py`, `app/main.py`, `.env*`.

## 4. 단계별 작업

### 4.1 `app/runtime/paper_journal.py` — TradeLogEntry.side 추가

- `from app.domain.enums import Side` 를 import 한다.
- `TradeLogEntry` frozen dataclass 에 `side: Side` 필드를 기존 필드들 사이 적절한 위치 (예: `symbol` 뒤) 에 추가한다.
- `TradeLogEntry.from_fill(cls, fill)` 에서 `side=fill.side` 를 전달하도록 갱신한다.
- `_jsonable` 헬퍼가 enum 인스턴스를 `.value` 로 직렬화하도록 분기 추가 (`from enum import Enum`, `isinstance(value, Enum)`).
- 기존 함수 시그니처 / 동작은 그대로 둔다. `record_order`, `record_trade`, `rejected_order`, `_append`, `OrderLogEntry`, log dir 처리 모두 변경 없음.

### 4.2 `app/runtime/paper_status.py` — 신규 helper

다음 시그니처로 구현한다 (정확한 키 이름은 plan 의 "Codex 구현 지시문" 절을 참고).

```python
from decimal import Decimal
from pathlib import Path

from app.runtime.paper_engine import PaperEngine


def mask_paper_log_dir(log_dir, project_dir: Path) -> str:
    ...


def build_paper_account_status(engine: PaperEngine, starting_cash: dict[str, Decimal]) -> dict:
    ...


def build_paper_positions_status(engine: PaperEngine) -> dict:
    ...


def build_paper_journal_status(engine: PaperEngine, *, limit: int = 50) -> dict:
    ...


def build_paper_engine_status(engine: PaperEngine, *, project_dir: Path) -> dict:
    ...
```

요구사항:

- `mask_paper_log_dir`:
  - `None` 이면 `"disabled"`.
  - `Path` 또는 `str` 이고 절대경로면, `project_dir` 하위 경로일 때 `Path(p).resolve().relative_to(project_dir.resolve()).as_posix()` 반환.
  - 그 외 절대경로는 마지막 두 segment 만 `"…/<parent>/<last>"` 형태로 노출. `/root/secret/path/reports/paper` → `"…/reports/paper"`.
  - 절대경로 prefix `/root`, `/home`, 사용자명, `app key`, `app secret` 등이 결과 문자열에 절대 포함되지 않아야 한다.
  - 상대경로면 그대로 `as_posix()`.
- `build_paper_account_status`:
  - `starting_cash`: 통화 → 문자열 dict.
  - `cash`: `engine.cash_by_currency()` 통화 → 문자열 dict.
  - `realized_pnl_by_currency`: portfolio snapshot 기준. `engine.portfolio.get_snapshot().realized_pnl_by_currency` 를 문자열 dict 로.
  - `currencies`: 위 세 map 의 키 합집합 (정렬된 list).
  - `secret_exposed`: False.
- `build_paper_positions_status`:
  - `positions_count`: `len(snapshot.positions)`.
  - `positions`: list of dict. 각 항목: `symbol/quantity/avg_price/last_price/market_value/currency/realized_pnl/unrealized_pnl/updated_at`. `unrealized_pnl = quantity * ((last_price or avg_price) - avg_price)` 문자열.
  - `market_value_by_currency`, `realized_pnl_by_currency`, `unrealized_pnl_by_currency` 문자열 dict.
  - `secret_exposed`: False.
- `build_paper_journal_status`:
  - `recent_fills`: 마지막 `limit` 개를 최신 우선으로. 각 항목: `broker_order_id/oms_id/symbol/side/quantity/price/currency/commission/filled_at` 문자열. `side` 는 `entry.side.value`.
  - `recent_orders`: 마지막 `limit` 개를 최신 우선으로. `broker_order_id/oms_id/symbol/status/reason/created_at`.
  - `fills_count`, `orders_count` 전체 합계.
  - `secret_exposed`: False.
- `build_paper_engine_status`:
  - `paper_engine_enabled`: True.
  - `paper_journal_enabled`: True if `engine.journal is not None` else False.
  - `paper_journal_persistent_logging`: `bool(engine.journal._log_dir)`.
  - `paper_journal_log_dir_masked`: `mask_paper_log_dir(engine.journal._log_dir, project_dir)`.
  - `last_fill_at`: `engine.journal.trades[-1].filled_at.isoformat()` or `None`.
  - `last_trade_at`: same source (이 코드베이스에서 trade == fill).
  - `last_journal_entry_at`: max(orders[-1].created_at, trades[-1].filled_at) or `None`.
  - `secret_exposed`: False.

모든 반환 값은 JSON 직렬화 가능한 기본 타입 (`str`, `int`, `bool`, `None`, `list`, `dict`) 만 사용한다. `Decimal` 은 `str(...)` 로 직렬화한다.

### 4.3 `app/api/server.py` — lifespan 보강

`load_settings()` 호출 직후, 다음을 추가한다:

```python
starting_cash = dict(
    settings.paper_starting_cash_by_currency
    or {settings.paper_base_currency: settings.paper_starting_cash}
)
project_dir = Path(__file__).resolve().parents[2]
```

`app.state.paper_engine = paper_engine` 다음에 다음 줄을 추가한다:

```python
app.state.paper_starting_cash = starting_cash
app.state.project_dir = project_dir
```

기존 `project_dir` 계산은 dry_run_controller 생성 직전에 있으니, 한 줄로 통합해도 좋다 (단, dry_run 동작이 변하지 않아야 한다).

PaperEngine, OMS, Strategy, Risk, broker, runner, dry_run_controller, session_router, portfolio, kis_broker, configured_brokers 의 생성/등록 로직은 변경 금지.

### 4.4 `app/api/routes.py` — 응답 보강 + 신규 endpoint

- 파일 상단에 `from app.runtime.paper_status import (build_paper_account_status, build_paper_positions_status, build_paper_journal_status, build_paper_engine_status)` 추가.
- `_trade_dict(entry)` 에 `"side": entry.side.value` 키를 추가한다 (`TradeLogEntry.side` 가 추가됐으므로 직접 접근 가능).
- `_position_dict(position)` 에 `"unrealized_pnl": str(position.quantity * ((position.last_price if position.last_price is not None else position.avg_price) - position.avg_price))` 키를 추가한다. 기존 키는 보존.
- `paper_account(request)` 응답에 `"starting_cash": _decimal_map(request.app.state.paper_starting_cash)` 키를 추가한다. 기존 키 / 값 / 순서 보존.
- `paper_fills(request)` 응답에 `"recent_orders": [_order_log_dict(entry) for entry in reversed(journal.orders)]` 키를 추가한다 (최신 우선, 최대 50개로 잘라도 됨). 기존 `fills`, `rejected_orders` 보존.
- 신규 라우트:

  ```python
  @router.get("/paper/engine/status")
  def paper_engine_status(request: Request) -> dict[str, Any]:
      engine = _paper_engine(request)
      project_dir = request.app.state.project_dir
      starting_cash = request.app.state.paper_starting_cash
      return {
          "account": build_paper_account_status(engine, starting_cash),
          "portfolio": build_paper_positions_status(engine),
          "journal": build_paper_journal_status(engine, limit=50),
          "engine": build_paper_engine_status(engine, project_dir=project_dir),
          "safety": _safety_flags(request),
          "secret_exposed": False,
      }
  ```

- `/paper/run`, `/paper/order/simulate`, `/paper/status`, `/paper/orders`, `/paper/positions`, dry-run, reports 라우트의 응답 스키마는 절대 변경하지 않는다 (위에 명시된 후방 호환 키 추가만 예외).

### 4.5 `app/static/dashboard.html` — UI 보강

전제: 기존 `safety-banner`, `button-row`, `paper-status-section`, `kis-status-section`, `manual-order-section`, `quick-demo-section`, `dry-run-status-section`, `report-section`, `<details>` JSON 보기, `<style>` 의 selector 들은 손대지 않는다. JS 의 `ENDPOINTS` 객체에는 새 키 하나만 추가한다.

추가/재구성:

1. `paper-account-section`:
   - 제목 "계좌 / 손익".
   - 행 1: "시작 현금" — 통화별 sub-table `<table id="acct-starting-cash">` (열: 통화 / 금액).
   - 행 2: "현재 현금" — 통화별 sub-table `<table id="acct-cash-by-currency">` (열: 통화 / 잔액). 기존 `<td id="acct-cash">` 도 raw JSON 으로 같은 정보를 유지해도 되고 제거해도 된다. 단, `test_dashboard.py` 의 마커 "현재 현금" 은 살아야 한다.
   - 행 3: "통화별 실현 손익" — `<table id="acct-realized-by-currency">`.
   - 행 4: "통화별 평가 손익" — `<table id="acct-unrealized-by-currency">`.
   - 행 5: "마지막 오류" — 기존 `<td id="paper-last-error">` 유지.
   - "실현 손익" / "평가 손익" 라벨 (기존 마커) 도 사라지지 않게 유지.
2. `paper-positions-section`:
   - 제목 "보유 종목" 유지.
   - 상단 부제: `<div id="positions-count">보유 종목 수: 0</div>`.
   - 테이블 컬럼: 종목 / 수량 / 평균가 / 현재가 / 평가금액 / 실현 손익 / 평가 손익 / 통화. JS `renderPositions` 에서 `p.realized_pnl`, `p.unrealized_pnl` 컬럼 추가. 비어 있으면 기존 "보유 종목이 없습니다." 메시지 유지.
3. `paper-fills-section`:
   - 제목 "체결 내역" 유지.
   - 테이블 컬럼: 종목 / 매수·매도 / 수량 / 체결가 / 수수료 / 통화 / 시간. `renderFills` 에서 `f.side === "buy" ? "매수" : "매도"` 로 렌더링.
4. 신규 `paper-journal-section`:
   - 제목 `<h2>최근 거절 주문</h2>` (마커: "최근 거절 주문").
   - `<table id="paper-rejected-orders">` 컬럼: 종목 / 상태 / 사유 / 시간. 비어 있으면 "거절된 주문이 없습니다.".
   - `paper-fills-section` 뒤에 배치.
5. 신규 `paper-engine-section`:
   - 제목 `<h2>Paper Engine 상태</h2>` (마커: "Paper Engine 상태").
   - 표 행:
     - `<tr><th>Paper Engine 활성</th><td id="eng-engine-enabled">-</td></tr>`
     - `<tr><th>Journal 활성</th><td id="eng-journal-enabled">-</td></tr>`
     - `<tr><th>Persistent 로그 경로</th><td id="eng-journal-log">-</td></tr>`
     - `<tr><th>마지막 체결 시각</th><td id="eng-last-fill">-</td></tr>`
     - `<tr><th>마지막 거래 시각</th><td id="eng-last-trade">-</td></tr>`
   - dry-run section 위 또는 paper-journal-section 뒤에 배치.

JS:

- `const ENDPOINTS = { ..., paperEngineStatus: "/paper/engine/status" };`.
- `renderCurrencyMap(tableId, map)` 신규 helper. 입력이 비어 있으면 `<tbody><tr><td>-</td><td>-</td></tr></tbody>`.
- `refreshAll` 끝에 추가:

  ```js
  try {
    const engineStatus = await fetchJson(ENDPOINTS.paperEngineStatus);
    renderCurrencyMap("acct-starting-cash", (engineStatus.account || {}).starting_cash || {});
    renderCurrencyMap("acct-cash-by-currency", (engineStatus.account || {}).cash || {});
    renderCurrencyMap("acct-realized-by-currency", (engineStatus.account || {}).realized_pnl_by_currency || {});
    renderCurrencyMap("acct-unrealized-by-currency", (engineStatus.portfolio || {}).unrealized_pnl_by_currency || {});
    setText("positions-count", "보유 종목 수: " + ((engineStatus.portfolio || {}).positions_count || 0));
    renderRejectedOrders((engineStatus.journal || {}).recent_orders || []);
    const eng = engineStatus.engine || {};
    setText("eng-engine-enabled", eng.paper_engine_enabled);
    setText("eng-journal-enabled", eng.paper_journal_enabled);
    setText("eng-journal-log", eng.paper_journal_log_dir_masked || "disabled");
    setText("eng-last-fill", eng.last_fill_at || "-");
    setText("eng-last-trade", eng.last_trade_at || "-");
  } catch (e) { logMsg("paper/engine/status error: " + e.message); }
  ```

- `renderRejectedOrders(rows)` 신규 helper: 컬럼 종목 / 상태 / 사유 / 시간. 비어 있으면 "거절된 주문이 없습니다.".
- `renderPositions(data)` 의 헤더와 row 에 "실현 손익" / "평가 손익" 컬럼 추가, 값은 `p.realized_pnl` / `p.unrealized_pnl`.
- `renderFills(data)` 의 헤더에 "매수/매도", row 에 `(f.side === "buy" ? "매수" : f.side === "sell" ? "매도" : "-")` 추가.

금지:

- 외부 script / stylesheet / `http://` / `https://` 추가.
- `<form action=...>` / `<form method=...>` 추가.
- live trading / market order / "Submit real order" / "Place real order" / "Enable live trading" 문자열 또는 버튼 추가.
- secret 입력란 / 토큰 입력란 / API key 표시 element 추가.

### 4.6 `README.md` — 1-2 줄 안내

이미 GUI/대시보드 안내가 있다면, 새 카드 4개 (Paper Account / Portfolio·PnL / Paper Journal / Paper Engine) 가 보인다는 1-2 줄을 추가한다. 안내가 아예 없으면 간단한 한 문장으로 추가한다. live trading / market order 활성화 안내는 추가하지 않는다.

### 4.7 테스트

`tests/test_paper_journal.py`:

- 새 테스트 추가: `TradeLogEntry.from_fill(fill)` 가 `side` 를 보존. 로깅 활성화된 PaperJournal 로 trade 기록 후, `trades.jsonl` 라인이 `"side": "buy"` (또는 `"sell"`) 을 포함.

`tests/test_paper_e2e_api.py`:

- 기존 테스트 보존. 다음 assertion 을 적절한 위치에 추가:
  - `body["starting_cash"]["USD"] == "100000"` — `/paper/account` 응답.
  - 매수 후 `positions["positions"][0]["unrealized_pnl"]` 가 문자열로 존재.
  - `fills["fills"][0]["side"] in ("buy", "sell")`.
  - `fills["recent_orders"]` 가 list (초기 빈 list).
  - 모든 신규 응답에서 secret leak 회귀 (기존 `test_paper_e2e_responses_do_not_expose_secrets` 의 forbidden 목록을 갱신해 `/paper/engine/status` 도 포함).

`tests/test_api_paper_engine_status.py` (신규):

- `/paper/engine/status` 200, `account / portfolio / journal / engine / safety / secret_exposed` 키 존재.
- 초기 상태:
  - `engine.paper_engine_enabled is True`.
  - `engine.paper_journal_enabled is True`.
  - `engine.last_fill_at is None`.
  - `journal.fills_count == 0`.
  - `journal.recent_fills == []`.
  - `journal.recent_orders == []`.
  - `account.starting_cash` 가 dict 이며 USD 키.
- 모의 주문 1건 (`_order_payload` 동일) 체결 후 GET:
  - `journal.recent_fills[0]["side"] in ("buy", "sell")`.
  - `engine.last_fill_at` 가 ISO 문자열.
  - `portfolio.positions_count == 1`.
  - `portfolio.unrealized_pnl_by_currency` 에 USD 키 존재.
- masking 검증:
  - 응답 본문에 `/root/`, `/home/`, `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO`, `Bearer `, `access_token`, raw 계좌번호 `12345678` 가 등장하지 않는다.
  - `paper_journal_log_dir_masked` 가 `"disabled"` 거나 `…/` prefix 또는 상대경로 패턴 (`reports/`) 중 하나.

`tests/test_dashboard.py`:

- `test_dashboard_has_required_sections_and_buttons` 의 마커 set 에 다음을 추가:
  - `시작 현금`, `통화별 현금`, `통화별 실현 손익`, `통화별 평가 손익`, `보유 종목 수`, `매수`, `매도`, `최근 거절 주문`, `Paper Engine 상태`, `Paper Engine 활성`, `Journal 활성`, `Persistent 로그 경로`, `마지막 체결 시각`, `마지막 거래 시각`.
- `test_dashboard_endpoint_urls_are_whitelisted` 의 `expected` set 에 `"/paper/engine/status"` 추가.
- 기존 forbidden / 외부 자원 / form action / `/paper/run` 회귀 테스트는 그대로 유지.

### 4.8 검증

다음 명령을 순서대로 실행하고 모두 성공해야 한다.

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

마지막에 `docs/ai/jobs/paper-001-gui/patch.md` 를 작성한다. 다음 형식:

```markdown
# paper-001-gui — Codex 구현 요약

## 변경된 파일
- ...

## 새 endpoint / API 응답 변화
- ...

## 테스트 결과
- compileall: OK
- pytest: N passed (전체 카운트)
- 신규 / 갱신된 테스트 목록

## 안전 회귀 확인
- live trading / market order 비활성 상태 유지
- KIS endpoint / TR ID / payload 추가 없음
- secret / 계좌번호 / token 노출 없음
- 자동 git commit / push / merge / deploy 수행 안 함

## 알려진 한계 / 후속 작업
- ...
```

## 5. 자가 점검 (PR 전)

- [ ] live trading / market order 활성화 코드 / 버튼이 추가되지 않았다.
- [ ] real broker API 호출, KIS HTTP 호출, FX 변환이 추가되지 않았다.
- [ ] `.env` 가 수정되지 않았다. secret / API key / token / 계좌번호가 응답·HTML 에 노출되지 않는다.
- [ ] `app/broker/*`, `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/paper_engine.py`, `app/runtime/paper_runner.py`, `app/runtime/dry_run*.py`, `app/strategy/*`, `app/config.py`, `app/main.py` 가 수정되지 않았다.
- [ ] 기존 `/paper/account`, `/paper/positions`, `/paper/fills`, `/paper/orders`, `/paper/status`, `/paper/order/simulate`, `/paper/run`, dry-run, reports 응답의 기존 키가 모두 살아있다.
- [ ] 신규 `/paper/engine/status` 가 dashboard JS 의 `ENDPOINTS` 에 등록됐고, 화면이 새 카드 4개를 채운다.
- [ ] `python -m compileall app tests` 통과.
- [ ] `python -m pytest -p no:cacheprovider` 전부 통과.
- [ ] `patch.md` 작성 완료.
- [ ] commit / push / merge / deploy 를 직접 실행하지 않았다.
