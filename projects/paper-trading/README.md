# Paper Trading Strategy Runtime

Phase 1 is a paper-only strategy validation runtime. It implements the first strategy, `premarket_gap_volume_breakout`, and keeps the order path fixed:

Strategy -> RiskEngine -> OMS -> BrokerAdapter

## Safety Rules

- Live trading is disabled in Phase 1.
- Market orders are simulated only when the paper-only triple guard passes.
- Strategies create non-executable `OrderIntent` candidates only.
- OMS is the only component that creates broker orders.
- Alpaca Paper is a stub; no network calls are implemented.
- `.env` values are local only. This repository contains `.env.example` placeholders only.

## Paper Simulation

`PaperBroker.tick()` owns quote-driven simulation. It refuses stale quotes, ignores quotes outside the configured sessions, and caps each tick's fills to a floor of quote volume times `PAPER_MAX_FILL_RATIO_OF_VOLUME`. Unfilled quantity remains open.

Supported simulated order types are `LIMIT`, `STOP_LIMIT`, and guarded paper-only `MARKET`. `RiskEngine` approves `MARKET` only when `ALLOW_PAPER_MARKET_ORDERS=true`, `TRADING_MODE=paper`, and live trading is disabled. The existing `ALLOW_MARKET_ORDERS=true` startup rejection remains unchanged.

`PaperAccount` stores cash by currency, and `PortfolioService` reports both legacy aggregate Decimal fields and per-currency realized PnL, market value, and unrealized PnL dictionaries. No exchange-rate conversion is performed.

## Run

```bash
python -m app.main
uvicorn app.api.server:app --reload
```

## Test

```bash
python -m compileall app tests
python -m pytest -p no:cacheprovider
```

## API

```bash
curl http://127.0.0.1:8000/paper/status
```

Open the browser dashboard:

```bash
./scripts/start_server.sh
# then open http://127.0.0.1:8000/dashboard
```

Manual paper order simulation is available from `/dashboard` and never calls a
real broker. The same flow is available by API:

```bash
curl http://127.0.0.1:8000/paper/account
curl http://127.0.0.1:8000/paper/positions
curl http://127.0.0.1:8000/paper/fills
curl http://127.0.0.1:8000/paper/orders
curl -X POST http://127.0.0.1:8000/paper/order/simulate \
  -H 'Content-Type: application/json' \
  -d '{"symbol":"AAPL","side":"buy","quantity":1,"order_type":"limit","limit_price":"100","mock_bid":"99","mock_ask":"100","mock_last":"100","mock_volume":100,"currency":"USD"}'
```

Dashboard quick demo:

- Open `/dashboard`.
- Click `예시 모의 주문 실행`.
- The dashboard should show `모의 주문이 체결되었습니다`, lower cash, a larger TEST position, and a new fill row.
- Raw JSON is available only under `원본 JSON 보기`; the main view uses Korean labels and explanations.

```bash
curl -X POST http://127.0.0.1:8000/paper/run \
  -H 'Content-Type: application/json' \
  -d '{"snapshots":[{"symbol":"AAPL","market":"US","session":"pre_market","previous_close":"100","current_price":"106","premarket_high":"106","premarket_volume":200000,"bid":"105.90","ask":"106.00","timestamp":"2026-05-14T12:00:00Z","relative_volume":"2.0"}]}'
```

## Strategy

`premarket_gap_volume_breakout` passes a candidate when:

- market is US
- session is pre-market
- gap from previous close is at least the configured threshold
- premarket volume is at least the configured threshold
- relative volume passes when present
- price is near or breaking premarket high
- spread is within the configured threshold
- quote is fresh

Blocked candidates never reach OMS.

## KIS Open API (모의투자) 연결 준비

`app/broker/kis.py`의 `KisBroker`는 KIS Open API 모의투자 연결을 위한 **골격**입니다. mvp-007에서는 내부를 세 클라이언트로 분리했습니다.

- `KisAuthClient`: 인증 토큰 상태 머신(`is_authenticated`, `get_access_token`, `clear_token`)
- `KisAccountClient`: 계좌/포지션/현금 조회 골격과 계좌번호 마스킹
- `KisMarketDataClient`: 시세 조회 골격과 정적 시장 데이터 healthcheck
- `KisBroker`: 위 세 클라이언트를 보유하고 BrokerAdapter 호환 메서드를 유지

본 단계에서는 실제 HTTP 호출이 구현되지 않았습니다 — 다음 메서드는 모두 `NotImplementedError`입니다.

- `authenticate()`, `refresh_token()`
- `get_account()`, `get_positions()`, `get_quote(symbol)`, `get_open_orders()`
- `place_order()`, `cancel_order()`, `replace_order()`
- BrokerAdapter 호환 메서드(`submit`/`cancel`/`open_orders`/`positions`)는 위 KIS-스타일 메서드로 위임만 합니다.

`healthcheck()`와 `healthcheck_market_data()`만 정적 dict를 반환합니다(네트워크 호출 없음). `/paper/status`는 KIS 설정 여부, 인증 여부, 계좌 로드 여부, 시장 데이터 가능 여부, 마스킹된 계좌번호를 보여주지만 key/secret/account/access token 원문은 절대 포함하지 않습니다.

### 환경변수

| 키 | 의미 | 비고 |
| --- | --- | --- |
| `KIS_ENV` | `paper` 만 허용 | live는 본 단계에서 차단 |
| `KIS_ACCOUNT_NO` | 모의투자 계좌번호 | `.env`에서만 |
| `KIS_APP_KEY` | KIS app key | `.env`에서만 |
| `KIS_APP_SECRET` | KIS app secret | `.env`에서만 |
| `ALLOW_MARKET_ORDERS` | 항상 `false` | `true`이면 `load_settings()` 거부 |
| `KILL_SWITCH_ENGAGED` | 주문 kill switch | `true`이면 RiskEngine/KIS pre-flight 거부 |
| `KIS_ORDER_DRY_RUN` | KIS 주문 dry-run | 기본 `true`; false여도 공식 endpoint/TR ID 확인 전에는 fail-closed |

### 주문 흐름 안전 가드와 내부 모델 (mvp-009)

`KisBroker.place_order` / `cancel_order` / `replace_order` 호출 시 다음 pre-flight 가드를 통과해야 합니다(`validate_kis_order_request`):

- `trading_mode == paper`
- `live_trading_enabled is False`
- `allow_market_orders is False`
- `kis_env == "paper"`
- `kill_switch_engaged is False`
- `order_type in (LIMIT, STOP_LIMIT)`
- `quantity > 0`
- `limit_price > 0`

가드 실패 시 `KisOrderRejectedError(reason)`로 즉시 거절합니다. 메시지에는 사유 코드만 들어가며 raw credentials/계좌번호는 포함되지 않습니다.

가드를 통과하더라도 KIS HTTP 전송은 본 단계에서 구현되지 않습니다. 다음 메서드는 항상 `NotImplementedError`로 fail-closed 합니다: `place_order`, `cancel_order`, `replace_order`, `get_open_orders`, `get_fills`, `get_order_status`.

`KisOrderRequest`는 내부 도메인 변환 모델로, KIS HTTP payload로 직렬화되지 않고 단위 테스트 및 향후 mvp 연결 시 입력 모델로만 사용됩니다. 계좌번호는 `account_no_masked`로만 보유합니다.

`kill_switch_engaged=true`로 설정하면 RiskEngine이 모든 주문을 즉시 거절하고, KIS pre-flight도 동일하게 거절합니다. `.env`의 `KILL_SWITCH_ENGAGED=true`로 활성화할 수 있습니다.

`KisOrderRequest`는 `symbol`, `market`, `side`, `quantity`, `order_type`, `limit_price`, `extended_hours`,
`account_no_masked`, `broker_environment`, `idempotency_key`를 보유합니다. `idempotency_key`는
`kis-paper-{oms_id}` 형식으로 결정적으로 생성되며, raw 계좌번호는 포함하지 않습니다.

`KisOrderResponse`는 향후 KIS 응답을 내부 모델로 보관하기 위한 구조입니다. `raw_response_sanitized`는
`sanitize_kis_response()`를 통과한 dict만 저장해야 하며, app key/secret/account/access token으로 보이는
키 또는 값은 `<redacted>`로 치환됩니다.

`KisHttpClient`는 timeout/retry 설정과 sanitized preview만 제공하는 공통 HTTP 경계입니다. 현재 repo 안에
공식 KIS endpoint/path/TR ID/payload 값이 없으므로 실제 HTTP 호출 메서드는 `NotImplementedError`로 남아
있습니다. 인증, 계좌/잔고/포지션, 시세, 주문 전송 모두 공식 문서값이 확인될 때까지 fail-closed입니다.

`KIS_ORDER_DRY_RUN=true`(기본값)에서는 `place_order()`가 HTTP 전송 없이 sanitized payload preview를 만들고
`OrderAck(status="dry_run")`만 반환합니다. `KIS_ORDER_DRY_RUN=false`로 바꿔도 공식 KIS 모의투자 주문
endpoint/TR ID/payload가 확인되지 않았으므로 실제 전송은 하지 않고 fail-closed 됩니다.

`KisBroker.capabilities()`는 현재 모든 주문 관련 기능을 `false`로 반환합니다. 공식 KIS 모의투자 주문 문서로
endpoint/TR ID/payload를 확인하기 전까지 submission/cancel/replace/open_orders/fills/order_status는 모두
사용 불가 상태이며 fail-closed입니다.

`/paper/status`는 `kis_order_entry_ready`, `kis_order_entry_mode`(`disabled | paper_guarded | not_implemented`),
`kis_order_methods_fail_closed`, `kill_switch_engaged`와 함께 `kis_order_submission_available`,
`kis_cancel_available`, `kis_replace_available`, `kis_open_orders_available`, `kis_fills_available`를 노출합니다.
현 단계에서 가용성 필드는 모두 `false`입니다.

`.env`는 Git에 올라가지 않습니다(루트 `.gitignore` + 프로젝트 `.gitignore` 양쪽에서 ignore). `.env.example`은 placeholder만 보관합니다.

### 안전 가드

- live trading 5단 차단(Settings 기본 False / load_settings / RiskEngine / OMS / `/paper/run`) 유지.
- `OrderType`에 MARKET 없음.
- `Strategy` 패키지는 `app.broker.kis`를 import하지 않는다.
- `Settings`/`KisBroker`의 `__repr__`가 key/secret/account를 노출하지 않는다.
- `KisAuthClient`/`KisAccountClient`/`KisMarketDataClient`의 `__repr__`도 key/secret/account/token을 노출하지 않는다.
- KIS endpoint URL, TR ID는 코드에 하드코딩하지 않는다. 추후 mvp에서 KIS 공식 문서 기반으로 구현한다.

### 무엇이 TODO인가

KIS Open API 공식 문서를 확인하기 전까지 다음은 구현하지 않습니다.

- OAuth/token endpoint, payload, response shape
- 계좌/포지션/현금 조회 endpoint, TR ID, payload
- 해외주식/미국주식 시세 endpoint, TR ID, payload
- 주문 전송, 취소, 정정, 주문 조회 endpoint

실제 주문 연결은 별도 mvp에서 OMS-only 실행 경로와 RiskEngine guard를 재검증한 뒤에만 진행합니다.

## Phase 2 Candidates

- Real paper broker adapter implementation after explicit review.
- Market data ingestion.
- More strategies and portfolio controls.
- Implement KIS Open API HTTP calls (`authenticate`, `refresh_token`, account/quote queries) once endpoints/TR IDs are confirmed from official documentation.

## 공식 KIS 문서값 진행 상황 (mvp-014)

KIS Open API 모의투자 HTTP 연결을 구현하기 위해 필요한 공식 문서값의 갭은 [`docs/kis/MISSING_OFFICIAL_VALUES.md`](../../docs/kis/MISSING_OFFICIAL_VALUES.md)에 정리되어 있습니다.

본 저장소는 endpoint URL, TR ID, header, payload를 추측하지 않습니다. `MISSING_OFFICIAL_VALUES.md`의 항목이 사용자에 의해 `Confirmed` 값 `yes`로 변경되기 전까지 다음 KIS HTTP 기능은 모두 `NotImplementedError` 또는 dry-run 상태로 유지됩니다.

- OAuth 인증, 토큰 갱신
- 해외주식 잔고/포지션/현금 조회
- 해외주식 시세 조회
- 모의투자 지정가 주문, 취소, 정정
- 미체결/체결/주문 상태 조회

기본값 `KIS_ORDER_DRY_RUN=true`가 유지되는 한 KIS 주문 메서드는 HTTP를 전송하지 않으며, dry-run preview를 반환합니다(또는 NotImplementedError로 fail-closed). `/paper/status`에서 `kis_order_dry_run: true` 필드로 확인할 수 있습니다.

## 장시간 KIS dry-run 검증 (mvp-018)

`DryRunController`는 paper-trading 시스템을 장시간 안정성 검증할 수 있는 stateful runner입니다. KIS HTTP는 호출하지 않으며, 명시적 tick 호출로만 한 사이클씩 실행합니다.

엔드포인트:

| 메서드 | 경로 | 설명 |
| --- | --- | --- |
| `POST` | `/paper/dry-run/start` | 새 run 시작. 이미 running이면 409. `reports/dry_run/run_<timestamp>/` 디렉터리 생성. |
| `POST` | `/paper/dry-run/tick` | snapshots 1개 사이클 처리. running이 아니면 409. kill switch면 `blocked_kill_switch`. |
| `POST` | `/paper/dry-run/stop` | 정지. running이 아니면 409. |
| `GET` | `/paper/dry-run/status` | 현재 state, counters, summary. credentials 미포함. |

리포트 파일은 프로젝트 `.gitignore`로 제외됩니다.

- `reports/dry_run/run_<timestamp>/events.jsonl` - tick 이벤트와 후보별 결과
- `reports/dry_run/run_<timestamp>/summary.json` - 누적 summary
- `reports/dry_run/run_<timestamp>/orders.csv` - OMS ack가 생성된 후보

안전 동작:

- 모든 리포트 dict는 `dump_safe()`로 검사되며, credential-like key가 포함되면 쓰기를 거절합니다.
- `kill_switch_engaged=true`이면 tick이 strategy 평가 없이 `blocked_kill_switch`로 종료됩니다.
- `errors_total >= DRY_RUN_MAX_ERRORS_BEFORE_AUTO_STOP`이면 `auto_stopped`로 전환합니다.
- `DRY_RUN_MAX_TICKS`에 도달해도 `auto_stopped`로 전환합니다.

```bash
curl -X POST http://127.0.0.1:8000/paper/dry-run/start
curl -X POST http://127.0.0.1:8000/paper/dry-run/tick -H 'content-type: application/json' \
  -d '{"snapshots":[]}'
curl -X GET http://127.0.0.1:8000/paper/dry-run/status
curl -X POST http://127.0.0.1:8000/paper/dry-run/stop
```

## dry-run 리포트 분석 (mvp-019)

mvp-018에서 만든 dry-run 산출물(`reports/dry_run/run_<ts>/{events.jsonl, summary.json, orders.csv}`)을 읽어 분석 리포트를 생성합니다. read-only이며 전략, OMS, broker 설정을 변경하지 않습니다.

### CLI

```bash
cd projects/paper-trading
.venv/bin/python -m app.reports --latest
.venv/bin/python -m app.reports --run-dir reports/dry_run/run_2026-05-14T08-00-00
```

### API

```bash
curl -X POST http://127.0.0.1:8000/reports/dry-run/analyze \
  -H 'content-type: application/json' \
  -d '{}'
curl http://127.0.0.1:8000/reports/dry-run/latest
```

### 산출물

분석 결과는 같은 run directory 안에 생성됩니다.

- `analysis_summary.json` - 카운터, top block reasons, 심볼 통계, pass rate, 제안, 경고
- `analysis_report.md` - 사람용 마크다운 리포트
- `claude_review_input.md` - Claude/Codex가 전략 개선 plan을 작성할 때 참고할 입력 문서

`reports/`는 프로젝트 `.gitignore`로 무시되므로 분석 산출물도 commit되지 않습니다. 응답/리포트에 KIS app key/secret/account 원문은 포함하지 않으며 `dump_safe` 가드가 credential-like key를 차단합니다.

## 초보자용 실행 방법 (mvp-020)

`scripts/` 아래 helper는 paper trading 안전 기본값을 shell에서 강제합니다. `.env`에 다른 값이 있어도 스크립트 실행 환경에서는 `TRADING_MODE=paper`, `LIVE_TRADING_ENABLED=false`, `ALLOW_MARKET_ORDERS=false`, `KIS_ORDER_DRY_RUN=true`가 우선합니다.

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
./scripts/start_server.sh
```

다른 터미널에서:

```bash
./scripts/status.sh
./scripts/start_dry_run.sh
./scripts/tick.sh
./scripts/analyze.sh
./scripts/stop_dry_run.sh
```

한 번에 기본 흐름을 확인하려면:

```bash
./scripts/smoke_check.sh
```

| 스크립트 | 설명 |
| --- | --- |
| `scripts/start_server.sh` | `127.0.0.1`에서 FastAPI 서버를 실행합니다. |
| `scripts/status.sh` | `/paper/status`와 `/paper/dry-run/status`를 조회합니다. |
| `scripts/start_dry_run.sh` | dry-run run을 시작합니다. |
| `scripts/tick.sh` | dry-run이 멈춰 있으면 먼저 시작하고 빈 snapshot tick을 실행합니다. |
| `scripts/stop_dry_run.sh` | dry-run run을 정지합니다. |
| `scripts/analyze.sh` | 최신 dry-run 리포트를 분석하고 `analysis_report.md` 경로를 출력합니다. |
| `scripts/smoke_check.sh` | status, start, tick, analyze, latest, stop 순서로 빠른 확인을 실행합니다. |

스크립트는 `.env`를 출력하지 않고, KIS app key/secret/account/token 원문을 echo하지 않습니다. 서버 응답도 기존 API의 sanitized 상태값만 표시합니다.

## 브라우저 대시보드 (mvp-021)

서버 실행 후 브라우저에서 `http://127.0.0.1:8000/dashboard`를 열면 paper trading 상태, KIS 상태, dry-run 상태, 최신 분석 리포트를 한 화면에서 확인할 수 있습니다. 대시보드는 동일 origin의 안전 endpoint만 호출하며, live trading 활성화 버튼, 시장가 주문 버튼, 실제 주문 버튼은 제공하지 않습니다.

`/dashboard`는 안전 상태, KIS 상태, 수동 모의 주문, 계좌·통화별 PnL, 보유 종목, 최근 체결, 최근 거절 주문, Paper Engine 상태, Dry-run 상태, 최신 리포트 해석을 보여줍니다.

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
./scripts/start_server.sh
# then open:
# http://127.0.0.1:8000/dashboard
```

표시되는 credential 관련 값은 서버가 이미 sanitize한 상태 필드와 masked account뿐이며, KIS app key/secret/account/token 원문은 HTML/JS에 포함하지 않습니다.

## .env 자동 로딩 (mvp-022)

`load_settings()`는 현재 작업 디렉터리와 무관하게 `projects/paper-trading/.env`를 명시적으로 찾습니다. 서버를 어디서 실행하더라도 paper-trading 프로젝트의 `.env`만 자동 로딩 대상이며, 파일이 없으면 기존 shell 환경값과 기본값으로 동작합니다.

권장 실행 방법:

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
./scripts/start_server.sh
```

직접 uvicorn을 실행해야 하면 외부 노출을 피하기 위해 loopback 주소를 사용합니다.

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
uvicorn app.api.server:app --host 127.0.0.1 --port 8000
```

`.env` 로딩은 `override=False`로 수행됩니다. 따라서 shell에서 안전 기본값을 export한 경우 shell 값이 `.env`보다 우선합니다.

```bash
export TRADING_MODE=paper
export LIVE_TRADING_ENABLED=false
export ALLOW_MARKET_ORDERS=false
export KIS_ORDER_DRY_RUN=true
```

서버를 `0.0.0.0`에 바인딩하는 방식은 로컬 검증 기본값으로 권장하지 않습니다. 과거 `KIS_PAPER_*` 이름을 쓰던 로컬 설정은 채팅이나 로그에 값을 붙여 넣지 말고, 로컬 환경에서 `KIS_*` 이름으로 별도 매핑한 뒤 사용합니다.

## KIS 시세 조회 준비 (mvp-023)

전략 후보 생성(mvp-024)에 사용할 broker-agnostic `Quote` 도메인 모델이 `app/domain/quote.py`에 추가되었습니다.

- 필드: `symbol`, `last`, `bid`, `ask`, `volume`, `timestamp`, `source`
- 속성/메서드: `spread_pct` (Decimal 분율), `is_stale(now, max_age_seconds)`
- `__post_init__`이 모든 invariant를 검증합니다(uppercase symbol, 양수 가격, `ask >= bid`, timezone-aware timestamp).
- `source` 필드로 출처를 추적합니다(예: `"kis_paper"`, `"alpaca_paper"`, `"synthetic"`).

`app/broker/kis_quote_mapper.py`는 KIS raw 응답을 `Quote`로 변환하는 매퍼 skeleton입니다. KIS Open API 공식 문서값이 부재하므로 본 단계에서는 `NotImplementedError`로 fail-closed 상태를 유지합니다.

필요한 공식 문서값은 [`docs/kis/MISSING_MARKET_DATA_VALUES.md`](../../docs/kis/MISSING_MARKET_DATA_VALUES.md)에 catalog로 정리되어 있습니다. 사용자가 KIS 공식 개발자 포털에서 항목별 `<TBD>`를 채우고 확인 완료 상태로 표시한 뒤에만 별도 mvp에서 매퍼 본문과 `KisMarketDataClient.get_quote` HTTP 호출을 구현합니다.

## API 인증 (api-auth-001)

KIS Open API의 OAuth 토큰 발급/폐기와 안전 HTTP 래퍼를 제공합니다.

- 기본 모드 `KIS_API_MODE=mock`: 네트워크 호출 없음. `KisAuthClient.authenticate()`는 즉시 `KisAuthError`.
- `KIS_API_MODE=paper`로 설정하고 `KIS_APP_KEY`/`KIS_APP_SECRET`을 `.env`에 두면 `https://openapivts.koreainvestment.com:29443`의 `/oauth2/tokenP`만 호출 가능.
- `KIS_API_MODE=live`는 api-auth-001 범위에서 fail-closed (`KisConfigError`).
- 토큰은 메모리 캐시가 기본. `KIS_TOKEN_CACHE_PATH`를 설정하면 0600 권한 JSON 파일로 캐시 (paper 한정).
- 본 작업은 시세/주문 호출 본문을 추가하지 않습니다. 후속 job 참고.
