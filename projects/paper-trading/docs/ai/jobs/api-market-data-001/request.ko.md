# 작업 ID
api-market-data-001

# 작업명
KIS 해외주식 현재체결가 기반 Quote 조회 구현

KIS 공식 문서값이 `docs/kis/MISSING_MARKET_DATA_VALUES.md`에 채워졌다.

현재 확인된 공식값:
- 모의 도메인: `https://openapivts.koreainvestment.com:29443`
- endpoint: `/uapi/overseas-price/v1/quotations/price`
- method: GET
- TR ID: `HHDFS00000300`
- 대상: 해외주식 현재체결가
- 현재체결가는 모의/실전 둘 다 가능
- 현재체결가는 bid/ask와 거래소 timestamp를 제공하지 않으므로, 응답 수신 시각을 timestamp로 사용한다.

이번 작업의 목표는 `KisMarketDataClient.get_quote()` 본문을 구현해서 KIS 현재체결가 API 응답을 도메인 `Quote` 모델로 매핑하는 것이다.

## 목표

- `KisMarketDataClient.get_quote(symbol)` 본문을 구현한다.
- KIS 현재체결가 endpoint를 stdlib `urllib.request` 기반 HTTP client로 호출한다.
- `HHDFS00000300` TR ID만 사용한다.
- 공식 문서값이 확인된 request field와 response field만 사용한다.
- KIS 응답을 broker-agnostic `Quote` 도메인 모델로 변환한다.
- 현재체결가에 bid/ask가 없으면 Quote 모델에서 안전하게 처리한다.
- timestamp는 응답 수신 시각을 사용한다.
- quote unavailable / malformed response / KIS error는 fail-closed 처리한다.
- `/paper/status` 또는 dashboard에서 `kis_market_data_available` 상태가 안전하게 표시되게 한다.
- 기존 dry-run / paper trading 안전 경계를 유지한다.

## 절대 하지 말 것

- live trading 활성화 금지
- 실전 주문 기능 구현 금지
- 주문 endpoint 구현 금지
- KIS 주문 TR ID 구현 금지
- KIS endpoint/TR ID/payload/header 추측 금지
- `HHDFS00000300` 외 임의 TR ID 사용 금지
- 외부 HTTP 라이브러리 사용 금지 (`requests`, `httpx`, `aiohttp`, `urllib3` 금지)
- stdlib `urllib.request`만 사용
- Strategy/Agent/LLM이 KIS를 직접 호출하는 경로 추가 금지
- executable order를 Agent나 LLM이 만들게 하지 말 것
- `ALLOW_MARKET_ORDERS=true` 허용 금지
- `OrderType.MARKET` 3중 가드 우회 금지
- `.env` 읽기/수정 금지
- 실제 app key, app secret, access token, 계좌번호, Bearer token을 코드/문서/테스트/patch에 기록 금지
- FX 변환 함수나 환율 상수 도입 금지
- GUI 파일(`app/api/`, `app/static/`, `app/main.py`) 수정 금지. 단, status helper가 이미 존재하고 API 변경이 필수라면 read-only 최소 변경만 계획에서 명시할 것.
- 자동 git commit / push / merge / deploy 금지

## 완료 기준

- `KisMarketDataClient.get_quote(symbol)`이 공식 catalog 기반으로 구현된다.
- 공식 endpoint `/uapi/overseas-price/v1/quotations/price`만 사용한다.
- 공식 TR ID `HHDFS00000300`만 사용한다.
- 요청 header/query는 `docs/kis/MISSING_MARKET_DATA_VALUES.md`에서 `Confirmed: yes`인 항목만 사용한다.
- KIS raw response는 `kis_quote_mapper`를 통해 `Quote`로 변환된다.
- bid/ask 부재는 명확하게 처리된다.
- timestamp는 응답 수신 시각으로 보수적으로 설정된다.
- malformed response와 KIS error는 fail-closed 된다.
- secret/account/token이 status/log/test output에 노출되지 않는다.
- Strategy/Agent/LLM이 KIS를 직접 import하지 않는다.
- 전체 pytest 통과.
- 안전 grep clean.

## 수정 가능 파일

- `projects/paper-trading/app/broker/kis.py`
- `projects/paper-trading/app/broker/kis_quote_mapper.py`
- `projects/paper-trading/app/domain/quote.py`
- `projects/paper-trading/tests/test_kis_market_data_client.py`
- `projects/paper-trading/tests/test_kis_quote_mapper.py`
- `projects/paper-trading/tests/test_quote_model.py`
- `projects/paper-trading/README.md`
- `docs/ai/jobs/api-market-data-001/patch.md`

## 검증

아래를 실행한다.

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider