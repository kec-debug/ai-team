# Paper Trading Strategy Runtime

Phase 1 is a paper-only strategy validation runtime. It implements the first strategy, `premarket_gap_volume_breakout`, and keeps the order path fixed:

Strategy -> RiskEngine -> OMS -> BrokerAdapter

## Safety Rules

- Live trading is disabled in Phase 1.
- Market orders are not modeled or allowed.
- Strategies create non-executable `OrderIntent` candidates only.
- OMS is the only component that creates broker orders.
- Alpaca Paper is a stub; no network calls are implemented.
- `.env` values are local only. This repository contains `.env.example` placeholders only.

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
