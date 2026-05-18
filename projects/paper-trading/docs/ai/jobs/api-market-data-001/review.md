# api-market-data-001 — Claude 리뷰

## 최종 판정

**APPROVE**

`KisMarketDataClient.get_quote(symbol, exchange="NAS") -> Quote` 가 catalog (`docs/kis/MISSING_MARKET_DATA_VALUES.md`) 의 `Confirmed: yes` 행만 사용해 구현됐다. 모의 도메인 1 개, path 1 개 (`/uapi/overseas-price/v1/quotations/price`), method 1 개 (`GET`), TR ID 1 개 (`HHDFS00000300`) 만 허용하는 host/path/method/TR ID/EXCD allowlist 가 transport 레벨에서 강제된다. 기본 `KIS_API_MODE=mock` 은 네트워크 호출 없이 `mock_mode_no_network` 으로 fail-closed 한다. 주문 / 계좌 / 취소 / replace / fills endpoint 는 모두 `NotImplementedError` 유지. live trading / market order / RiskEngine / OMS / Strategy / Agent / GUI 경계 변동 없음. secret · 계좌번호 · access token · Bearer · raw `Authorization` 헤더가 코드 / repr / exception 메시지 / 응답 어디에도 노출되지 않으며, transport raise 는 short tag (`mock_mode_no_network`, `invalid_exchange`, `paper_market_data_host_required`, `http_<code>`, `transport_error`, `kis_error:<msg_cd>`, `malformed_response`) 만 사용한다. patch.md 의 `337 passed` 와 일치. commit / push / merge / deploy 가 수행되지 않았다.

본 작업은 roadmap 의 mvp-023 (`BLOCKED-BY-DOCS`) 슬롯을 catalog 가 채워진 후 unblock 하는 변경에 정확히 매핑된다 (`MASTER_TRADING_ROADMAP.md:556`, `ROADMAP_STATUS.md:10`).

## Findings (severity 순)

### Critical / Major

없음.

### Minor / 관찰사항

1. **`base_url.rstrip()` 가 빈 인자 호출** (`app/broker/kis.py:268`).
   - 영향: `kis_base_url_paper` 가 trailing whitespace 가 아닌 trailing `/` 를 가지면 URL 에 `//uapi/...` 가 만들어진다. 기본 settings (`https://openapivts.koreainvestment.com:29443`) 는 trailing slash 가 없으므로 본 작업의 테스트 / 운영 영향은 없다.
   - 권장: 후속에서 `base_url.rstrip("/")` 로 좁게 수정. 본 PR 의 블로커는 아님.

2. **`KisBroker.get_quote(self, symbol: str) -> Quote` 가 `exchange` kwarg 를 전달하지 않음** (`app/broker/kis.py:746-747`).
   - 영향: `_market_data.get_quote(symbol)` 호출 시 기본값 `exchange="NAS"` 가 사용된다. `KisBroker` 레벨에서 다른 거래소를 선택할 수 없다.
   - 호출자: 현재 KIS broker 의 `get_quote` 는 외부에서 `broker.get_quote("AAPL")` 처럼 단일 symbol 인자로만 호출된다 (`test_broker_interface.py:143-145`, `test_kis_http_boundaries.py:161-165`). 기능 결손은 없음.
   - 권장: 후속에서 `KisBroker.get_quote(symbol, *, exchange="NAS")` 로 확장. 본 PR 의 블로커는 아님.

3. **`healthcheck_market_data()` 의 `reason` 이 ready 상태에서 `None`** (`app/broker/kis.py:663`).
   - 영향: plan 은 `"ready"` 문자열을 제안했지만 실제는 `None`. `/paper/status` 가 `reason` 을 별도로 노출하지 않으므로 dashboard 영향 없음. 신규 테스트 `test_market_data_healthcheck_available_with_authenticated_transport` 가 `reason is None` 을 명시적으로 검증.
   - 비호환 아님. 단지 plan 과 표현 차이.

4. **mapper 가 `output.rsym` 검증을 생략** (`app/broker/kis_quote_mapper.py`).
   - plan 은 옵션 사항으로 "있으면 파싱, 불일치는 silent" 였다. 구현은 아예 사용하지 않음. catalog 의 `Confirmed: yes` 행은 `rsym` 도 포함하지만 mapper 가 입력 symbol 을 그대로 신뢰하므로 보안/정확성에 손상 없음. 후속에서 rsym 일치 검증을 추가하려면 별 job.

5. **`Accept` / `custtype` 헤더 미전송** (`app/broker/kis.py:271-277`).
   - catalog 는 `content-type` 을 응답 측 필수 / 요청 측 옵션, `custtype` 을 현재체결가에서 옵션으로 분류. 둘 다 옵션이므로 미전송은 catalog 정책과 충돌하지 않는다. `content-type: application/json; charset=utf-8` 는 요청에 포함되어 있다.

## 안전 / 정책 회귀 체크리스트

- [x] **공식 catalog `Confirmed: yes` 항목만 사용** — Base URL (모의), path, method, TR ID, EXCD allowlist (14 개), 요청 헤더 (`content-type`/`authorization`/`appkey`/`appsecret`/`tr_id`), query (`AUTH=&EXCD=&SYMB=`), 응답 필드 (`rt_cd`/`output.last`/`output.tvol`) 모두 catalog 행과 정확히 일치 (`app/broker/kis.py:40-45,267-277`, `app/broker/kis_quote_mapper.py:42-58`).
- [x] **KIS endpoint / TR ID / 요청·응답 필드 추측 없음** — `HHDFS76200100`, `HHDFS76200200`, `HHDFS76220000` 또는 주문 TR ID 가 `app/broker/*` 에 등장하지 않는다. `price-detail`, `inquire-asking-price` path 도 없다 (grep 검증).
- [x] **Quote 매핑이 broker-agnostic** — mapper 는 KIS 전용 필드명만 입력으로 받고 도메인 `Quote` 만 반환. `Quote` 는 `app/domain/quote.py` 의 broker 비특정 모델. `bid_ask_present` 필드 한 개 추가 (default True) 로 후방 호환 유지.
- [x] **`bid_ask_present` 가 synthetic bid/ask 를 안전하게 표현** — 현재체결가 응답에 bid/ask 가 없으므로 mapper 가 `bid = ask = last`, `bid_ask_present=False` 로 채운다 (`app/broker/kis_quote_mapper.py:60-71`). `Quote.__post_init__` invariant (`bid > 0`, `ask >= bid`) 통과. `spread_pct == 0`. `test_quote_synthetic_bid_ask_marker` 와 `test_mapper_converts_confirmed_overseas_price_response` 가 검증.
- [x] **`KIS_API_MODE=mock` 이 네트워크 호출 없이 fail-closed** — `KisMarketDataClient.__init__` 가 mock 모드에서 `MockMarketDataTransport()` 를 선택하고 `MockMarketDataTransport.get_quote` 는 즉시 `KisDataUnavailableError("mock_mode_no_network")` 를 raise (`app/broker/kis.py:586-595,226-239`). 인증 토큰이 있어도 동일. `test_market_data_healthcheck_mock_mode_no_network`, `test_market_data_requires_auth_before_unimplemented_endpoint` (갱신된 두 번째 assertion) 가 검증.
- [x] **paper-mode transport guard 가 모의 host / 현재체결가 path / TR / query 만 허용** — `UrllibMarketDataTransport.get_quote` 가 EXCD 를 `KIS_ALLOWED_EXCHANGES` 14 개로 제한 (`invalid_exchange`), host 를 `openapivts.koreainvestment.com:29443` 한 개로 제한 (`paper_market_data_host_required`). path 는 `KIS_OVERSEAS_PRICE_PATH` 상수 단 1 개를 사용. method 는 GET 만. TR ID 는 `HHDFS00000300` 한 개만. `test_urllib_transport_rejects_unconfirmed_exchange_without_network`, `test_urllib_transport_rejects_non_paper_host_without_network` 가 네트워크 호출 없이 검증.
- [x] **주문 endpoint / TR / payload 추가 없음** — `KisBroker.place_order` 는 dry-run 외에서 `NotImplementedError("...order endpoint...")` 유지. `cancel_order`, `replace_order`, `get_open_orders`, `get_fills`, `get_order_status`, `get_account`, `get_positions`, `get_cash_balance` 모두 `NotImplementedError` 유지. `test_kis_place_cancel_replace_not_implemented`, `test_kis_data_methods_not_implemented`, `test_cancel_replace_queries_fail_closed`, `test_kis_broker_has_get_fills_and_get_order_status` 통과.
- [x] **live trading 비활성 유지** — `validate_kis_order_request` 의 `LIVE_TRADING_ENABLED` 가드 변동 없음 (`app/broker/kis.py:308-330`). `KisBroker.__init__` 의 `kis_env != "paper"` 차단 유지. `test_kis_broker_live_env_rejected` 통과.
- [x] **market orders 차단 유지** — `validate_kis_order_request` 의 `allow_market_orders` / `order_type not in (LIMIT, STOP_LIMIT)` 가드 변동 없음. `PaperBroker` / `RiskEngine` / `OMS` 변경 없음. 기존 `test_kis_order_*` / `paper_e2e` 통과.
- [x] **외부 HTTP 라이브러리 미사용** — `app/` 와 `tests/` 에 `import requests`, `import httpx`, `import aiohttp`, `import urllib3`, `from requests/httpx/aiohttp …` 가 등장하지 않는다 (forbidden 리터럴 자체는 회귀 테스트의 forbidden 목록에만 존재). 본 작업은 stdlib `urllib.request`, `urllib.parse.urlsplit`, `urllib.parse.quote`, `urllib.error` 만 사용. `test_kis_modules_do_not_import_third_party_http_libs`, `test_kis_module_does_not_import_http_libraries` 통과.
- [x] **secret / 계좌번호 / token / Bearer 노출 없음** —
  - `__repr__`: `KisMarketDataClient(<mock>)` 또는 `KisMarketDataClient(<paper>)` 만. `KisBroker.__repr__` 은 `app_key=<set>`, `app_secret=<set>` masked. `KisAuthClient.__repr__` 도 token `<set>`/`<unset>` masked.
  - exception 메시지: 단축 tag 만 (`mock_mode_no_network`, `http_<code>`, `kis_error:<msg_cd>`, `transport_error`, `malformed_response`, `invalid_exchange`, `paper_market_data_host_required`, `invalid_symbol`, `authentication_required`).
  - `Authorization: Bearer ${access_token}`, `appkey`, `appsecret` 헤더 값이 코드에서 직접 만들어지지만, urllib `Request` 의 `headers` dict 에만 들어가고 stdout / stderr / 응답 본문 / log 로 흘러나가지 않는다.
  - `test_market_data_repr_does_not_expose_secrets`, `test_kis_broker_repr_masks_secrets` 통과.
- [x] **`.env` 미접근 / 미수정** — `app/config.py` 변경 없음. `load_dotenv` 호출 추가 없음. 새 env 변수 (`KIS_MARKET_DATA_APP_KEY` 등) 추가 없음. patch.md 의 "No .env file was read, edited, or added" 와 일치.
- [x] **Strategy / Agent / LLM 이 KIS 를 직접 호출하지 않음** — `app/strategy/`, `app/agents/` (존재 시) 의 import 가 `app.broker.kis` 또는 `app.broker.kis_quote_mapper` 를 포함하지 않는다. `test_strategy_package_does_not_import_kis`, `test_agent_package_does_not_import_kis_if_present` 통과.
- [x] **OMS / RiskEngine 경계 약화 없음** — `app/oms/*`, `app/risk/*`, `app/portfolio/*`, `app/runtime/paper_engine.py`, `app/runtime/paper_runner.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`, `app/broker/kis_http.py`, `app/broker/kis_token_cache.py`, `app/main.py`, `app/api/*`, `app/static/*` 변경 없음. `KisBroker` 가 OMS 에 wiring 되지 않는 상태도 유지.
- [x] **테스트 통과** — patch.md: `337 passed in 0.69s`. `compileall: OK`. safety-grep: clean.
- [x] **api-market-data-001 범위 내 유지** — 실제 변경된 파일은 다음 9 개로 plan §3 의 화이트리스트 + 좁은 범위 확장 2 개 (`test_kis_http_boundaries.py`, `test_broker_interface.py`) 와 일치:
  - `app/domain/quote.py` (+1 필드)
  - `app/broker/kis_quote_mapper.py` (본문 구현)
  - `app/broker/kis.py` (transport + 클라이언트 본문)
  - `tests/test_kis_market_data_client.py` (재작성)
  - `tests/test_kis_quote_mapper.py` (재작성)
  - `tests/test_quote_model.py` (`bid_ask_present` 테스트 추가)
  - `tests/test_kis_http_boundaries.py` (1 줄 assertion 만 갱신, 그 외 모두 그대로)
  - `tests/test_broker_interface.py` (1 줄 assertion 만 갱신, 그 외 모두 그대로)
  - `README.md` (3 줄 안내)
  - `docs/ai/jobs/api-market-data-001/patch.md` (NEW)
- [x] **사전 unstaged 변경분 보존** — `app/api/server.py`, `app/runtime/paper_journal.py`, `scripts/_common.sh`, `scripts/start_server.sh`, `docs/ai/jobs/mvp-002/request.ko.md` 는 본 작업 시작 전부터 working tree 에 존재했고, Codex 가 추가로 건드린 흔적이 없다. patch.md 의 "Pre-existing unrelated dirty files were left untouched" 와 일치.

## 산출물 vs 계획 대조

| Plan 항목 | 구현 위치 | 결과 |
| --- | --- | --- |
| `Quote.bid_ask_present: bool = True` 필드 추가, invariant 변동 없음 | `app/domain/quote.py:27` | OK. docstring 1 줄 보강. `__post_init__` 그대로. |
| `kis_raw_quote_to_domain(raw, symbol, *, received_at, ...)` 본문 | `app/broker/kis_quote_mapper.py:22-71` | OK. `rt_cd`/`output.last`/`output.tvol` 만 사용. 쉼표 포함 가격 처리. 모든 실패 경로 ValueError. |
| `KIS_OVERSEAS_PRICE_PATH`, `KIS_OVERSEAS_PRICE_TR_ID`, `KIS_PAPER_MARKET_DATA_HOSTS`, `KIS_ALLOWED_EXCHANGES` 상수 | `app/broker/kis.py:40-45` | OK. allowlist 4 개 모두 catalog 값과 일치. |
| `KisMarketDataTransport` Protocol + Mock + Urllib transport | `app/broker/kis.py:211-305` | OK. method/host/path/exchange/TR ID allowlist 강제. 5xx 및 transport 에러에서 1 회 retry. JSON 파싱 / `rt_cd != "0"` 검증. exception 메시지 short tag 만. |
| `KisMarketDataClient.__init__(transport=None)` 자동 모드 분기 | `app/broker/kis.py:578-595` | OK. mock 모드 → MockMarketDataTransport, 그 외 → UrllibMarketDataTransport. |
| `get_quote(symbol, *, exchange="NAS") -> Quote` | `app/broker/kis.py:602-634` | OK. 인증 게이트 → transport → mapper → Quote. 모든 실패 `KisAuthError` 또는 `KisDataUnavailableError`. `last_error` 갱신. |
| `get_last_price(...) -> Decimal` | `app/broker/kis.py:636-637` | OK. `quote.last` 반환. |
| `healthcheck_market_data()` 3 상태 분기 | `app/broker/kis.py:639-667` | OK. mock → mock_mode_no_network, paper+no-auth → authentication_required, paper+auth → ready (reason=None). `connected = (not mock) and auth_present` 정의 충족, `/paper/status` 회귀 OK. |
| `__repr__` 가 mock/paper 마커만 노출 | `app/broker/kis.py:598-600` | OK. secret 없음. |
| `KisBroker.get_quote -> Quote` | `app/broker/kis.py:746-747` | OK (단, exchange kwarg 미전달 — minor 관찰사항 #2). |
| 테스트 재작성 (mapper / market data / quote / boundaries 좁은 갱신) | `tests/test_kis_*.py`, `tests/test_quote_model.py`, `tests/test_kis_http_boundaries.py`, `tests/test_broker_interface.py` | OK. happy / 실패 / healthcheck / repr / transport guard 회귀 모두 검증. |
| README 1-2 줄 안내 | `README.md:366-369` | OK. 새 env 변수 안내 없음. mock fail-closed 와 confirmed-only 정책 명시. |

## 후속 작업 후보 (블로커 아님)

- `base_url.rstrip("/")` 좁은 수정 (관찰사항 #1).
- `KisBroker.get_quote` 가 `exchange` kwarg 를 클라이언트로 전달하도록 확장 (관찰사항 #2).
- `output.rsym` 일치 검증을 mapper 에 추가 (catalog 가 명시한 옵션 필드).
- `mvp-024` (real market data 기반 candidate generation) — `MASTER_TRADING_ROADMAP.md:557` 의 다음 슬롯.
- catalog 의 별 job (`mvp-023b`) 항목: 호가 endpoint + 실전 도메인 bid/ask, 그리고 `KIS_MARKET_DATA_APP_KEY` 분리. 본 작업은 모의 도메인 + 현재체결가 단일 endpoint 범위 유지.

## 결론

요청서의 모든 완료 기준 (공식 catalog 기반 구현, `HHDFS00000300` 단일 TR ID, bid/ask 부재 안전 처리, 응답 수신 시각 timestamp, fail-closed, secret 비노출, Strategy/Agent KIS 직접 import 없음, 전체 pytest 통과, 안전 grep clean) 을 충족했다. plan / codex-task 의 안전 가드 (host/path/method/TR ID/EXCD allowlist, mock fail-closed, RiskEngine/OMS/GUI 경계 유지) 가 transport 와 테스트에 명시적으로 박혀 있다. 위 Minor 관찰사항은 후속 job 에서 다루면 충분하다.

**APPROVE**. commit / push / merge 는 사람이 직접 수행한다.
