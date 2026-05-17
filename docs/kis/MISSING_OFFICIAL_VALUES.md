# KIS Open API - Missing Official Values

본 문서는 KIS Open API 모의투자 HTTP 연결을 구현하기 위해 필요한 공식 문서값의 갭을 정리합니다. 본 저장소는 KIS endpoint, TR ID, header, payload를 추측하지 않습니다. 아래 항목이 KIS 공식 Open API 문서에서 확인된 뒤에만 별도 mvp에서 HTTP 연결을 진행합니다.

## 정책

- 본 표의 모든 `<TBD>` 항목은 KIS 공식 Open API 개발자 포털 문서에서 직접 확인해 채워 넣어야 합니다.
- 실전투자(live) endpoint는 본 저장소에 추가하지 않습니다. 모의투자(paper) endpoint만 다룹니다.
- 실제 app key, app secret, 계좌번호, access token 값은 본 문서/저장소 어디에도 기록하지 않습니다.
- 항목별로 `Confirmed: no`인 한 해당 HTTP 기능은 `NotImplementedError` 또는 dry-run 상태를 유지합니다.

## 1. OAuth 인증

| 항목 | 설명 | 값 | Confirmed |
| --- | --- | --- | --- |
| Paper trading base URL | 모의투자 환경 base URL | `<TBD>` | no |
| OAuth token endpoint | 토큰 발급 path | `<TBD>` | no |
| OAuth token HTTP method | `POST`/`GET` 등 | `<TBD>` | no |
| Token refresh endpoint (있으면) | 갱신 path | `<TBD>` | no |
| Required request headers | `content-type` 등 | `<TBD>` | no |
| Request body fields | `grant_type`, `appkey`, `appsecret`, ... | `<TBD>` | no |
| Response token field name | `access_token`/`token` 등 | `<TBD>` | no |
| Response token expiry field | `expires_in`/`expires_at` 등 | `<TBD>` | no |
| Token type field (있으면) | `Bearer` 등 | `<TBD>` | no |

충족 시 후속 mvp가 `KisAuthClient.authenticate()` / `refresh_token()`을 실제 HTTP로 연결합니다.

## 2. 해외주식/미국주식 계좌

| 항목 | 설명 | 값 | Confirmed |
| --- | --- | --- | --- |
| 해외주식 잔고 endpoint | path | `<TBD>` | no |
| 해외주식 잔고 TR ID | 모의투자용 TR ID | `<TBD>` | no |
| 포지션 조회 TR ID | 모의투자용 TR ID | `<TBD>` | no |
| 현금/예수금 조회 TR ID | 모의투자용 TR ID | `<TBD>` | no |
| Request query/body fields | 계좌번호, 통화, 거래소 등 | `<TBD>` | no |
| Response 잔고 field | 잔고 dict key | `<TBD>` | no |
| Response 포지션 list field | 포지션 list key | `<TBD>` | no |
| Response 현금 field | 현금 dict key | `<TBD>` | no |

충족 시 후속 mvp가 `KisAccountClient.get_account()` / `get_positions()` / `get_cash_balance()`를 실제 HTTP로 연결합니다.

## 3. 해외주식/미국주식 시세

| 항목 | 설명 | 값 | Confirmed |
| --- | --- | --- | --- |
| 해외주식 현재가 endpoint | path | `<TBD>` | no |
| 해외주식 현재가 TR ID | 모의투자용 TR ID(시세는 실전과 공유될 수 있음 - 공식 문서 확인 필요) | `<TBD>` | no |
| Request fields | 종목코드, 거래소 코드 등 | `<TBD>` | no |
| Response bid/ask/last 필드 | `<TBD>` | `<TBD>` | no |
| Response quote timestamp 필드 | `<TBD>` | `<TBD>` | no |
| Stale quote 판단 기준 | 초/밀리초 등 단위 | `<TBD>` | no |

충족 시 후속 mvp가 `KisMarketDataClient.get_quote()` / `get_last_price()`를 실제 HTTP로 연결합니다.

## 4. 모의투자 주문

| 항목 | 설명 | 값 | Confirmed |
| --- | --- | --- | --- |
| 모의투자 해외주식 주문 endpoint | path | `<TBD>` | no |
| 모의투자 해외주식 주문 TR ID | TR ID | `<TBD>` | no |
| 지정가 주문 payload fields | 종목코드, 주문수량, 주문단가, 매수/매도, 거래소, ... | `<TBD>` | no |
| Response broker_order_id 필드 | 주문번호 key | `<TBD>` | no |
| 주문 취소 endpoint | path | `<TBD>` | no |
| 주문 취소 TR ID | TR ID | `<TBD>` | no |
| 주문 정정 endpoint | path | `<TBD>` | no |
| 주문 정정 TR ID | TR ID | `<TBD>` | no |
| 미체결 조회 endpoint | path | `<TBD>` | no |
| 미체결 조회 TR ID | TR ID | `<TBD>` | no |
| 체결 조회 endpoint | path | `<TBD>` | no |
| 체결 조회 TR ID | TR ID | `<TBD>` | no |
| 주문 상태 조회 endpoint | path | `<TBD>` | no |
| 주문 상태 조회 TR ID | TR ID | `<TBD>` | no |

모든 항목 충족 시 후속 mvp가 `KisBroker.place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status`를 단계적으로 실제 HTTP로 연결합니다. 그 단계에서도 `KIS_ORDER_DRY_RUN=true` 기본값과 `validate_kis_order_request` pre-flight는 유지됩니다.

## 다음 작업 가이드

1. 사용자가 KIS Open API 공식 개발자 포털 또는 신뢰 가능한 KIS 공식 문서에서 위 `<TBD>` 항목을 직접 확인합니다.
2. 항목별로 `Confirmed` 값을 `yes`로 변경하고 값을 채워 넣습니다.
3. `Confirmed` 값이 `yes`인 항목만 별도 mvp에서 `app/broker/kis.py`에 HTTP로 연결합니다.
4. 본 저장소는 사용자가 확인하지 않은 값은 절대 사용하지 않습니다.

## 보안

- 실제 app key, app secret, 계좌번호, access token, refresh token은 이 문서에 절대 기록하지 않습니다. 모두 `.env`(gitignored)에만 둡니다.
- 본 문서가 커밋된 형태로 git에 들어가도 자격증명 누출이 없도록 합니다.
