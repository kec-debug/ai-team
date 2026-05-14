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
