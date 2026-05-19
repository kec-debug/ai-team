# 작업 ID
api-account-001

# 작업명
KIS 모의 계좌 / 잔고 / 포지션 조회 구현

KIS_2에서 계좌 / 잔고 / 포지션 조회에 필요한 공식 문서값 catalog가 정리되었다.

현재 `KisAccountClient.get_account()`, `get_positions()`, `get_cash_balance()`는 공식 endpoint, TR ID, request field, response field 값이 부족해서 fail-closed 상태였다. 이제 KIS_2에서 확인된 공식값만 사용해서 KIS 모의투자 계좌 조회 기능을 구현한다.

이번 작업은 실전거래가 아니라 paper trading 상태 확인과 포트폴리오 검증을 위한 계좌 / 잔고 / 포지션 read-only 조회 구현이다. 주문 기능은 구현하지 않는다.

## 목표

- `KisAccountClient.get_account()` 본문을 구현한다.
- `KisAccountClient.get_positions()` 본문을 구현한다.
- `KisAccountClient.get_cash_balance()` 본문을 구현한다.
- KIS_2에서 `Confirmed: yes`로 정리된 공식 endpoint, TR ID, headers, request fields, response fields만 사용한다.
- KIS 모의투자 지원 endpoint만 사용한다.
- 실전 계좌 endpoint는 사용하지 않는다.
- stdlib `urllib.request` 기반 기존 HTTP 경계를 사용한다.
- 외부 HTTP 라이브러리를 추가하지 않는다.
- 계좌번호는 항상 마스킹한다.
- raw response는 sanitized 형태로만 다룬다.
- `/paper/status` 또는 기존 status에서 계좌 / 잔고 / 포지션 로드 상태를 안전하게 표시한다.
- 계좌 / 잔고 / 포지션 조회 실패 시 주문 가능 상태로 전환하지 않는다.
- 테스트를 추가한다.

## 절대 하지 말 것

- live trading 활성화 금지.
- 실전 계좌 endpoint 사용 금지.
- 실전 주문 기능 구현 금지.
- 주문 endpoint 구현 금지.
- KIS endpoint, TR ID, payload, header 추측 금지.
- KIS_2 또는 공식 catalog에서 확인되지 않은 값을 사용하지 말 것.
- 외부 HTTP 라이브러리(`requests`, `httpx`, `aiohttp`, `urllib3`) import 금지.
- stdlib `urllib.request` 외 HTTP client 추가 금지.
- Strategy, Agent, LLM이 broker를 직접 호출하는 경로 추가 금지.
- executable order를 Agent나 LLM이 생성하게 만들지 말 것.
- 모든 주문은 Strategy → RiskEngine → OMS → PaperBroker 경로를 통과해야 한다는 안전 원칙을 변경하지 말 것.
- `ALLOW_MARKET_ORDERS=true` 허용 금지.
- `OrderType.MARKET` 3중 가드 우회 금지.
- FX 변환 함수나 환율 상수 도입 금지.
- multi-currency 값은 통화별로 분리 보고만 한다.
- `.env` 읽기/수정 금지.
- `.env.example`에 실제 값 추가 금지.
- 실제 app key, app secret, access token, Bearer token, 계좌번호를 코드/문서/테스트/patch에 기록 금지.
- GUI 파일(`app/api/`, `app/static/`, `app/main.py`) 수정 금지. 단, 기존 status helper가 이미 계좌 상태를 노출하는 구조라면 read-only 최소 변경만 허용한다.
- 자동 git commit / push / merge / production deploy 금지.

## 완료 기준

- `KisAccountClient.get_account()`가 KIS_2의 공식 catalog 기반으로 구현된다.
- `KisAccountClient.get_positions()`가 KIS_2의 공식 catalog 기반으로 구현된다.
- `KisAccountClient.get_cash_balance()`가 KIS_2의 공식 catalog 기반으로 구현된다.
- 모의투자 지원 endpoint만 사용한다.
- 공식값이 부족한 항목은 계속 fail-closed 상태를 유지한다.
- 계좌번호 원문은 status, log, test output, patch 어디에도 노출되지 않는다.
- app key, app secret, token, Bearer token이 노출되지 않는다.
- 응답 parser는 KIS 공식 response field만 사용한다.
- 잔고 / 포지션 / 현금 값은 내부 모델로 변환된다.
- FX 변환은 하지 않는다.
- 통화별 값은 통화별로 분리 보고한다.
- 인증 토큰이 없거나 인증 실패 상태면 계좌 조회를 fail-closed 처리한다.
- KIS_ENV가 paper가 아니면 조회를 차단한다.
- live trading이 true이면 조회 또는 trading-ready 상태를 차단한다.
- `/paper/status`에서 `kis_account_loaded`, `kis_positions_loaded`, `kis_cash_balance_loaded` 상태가 안전하게 표시된다.
- Strategy 패키지에서 KIS 직접 import가 없어야 한다.
- Agent/LLM 경로에서 KIS 직접 호출이 없어야 한다.
- 주문 관련 메서드는 이번 작업에서 구현하지 않는다.
- 전체 pytest 회귀 0건.
- 안전 grep이 clean이어야 한다.
- patch.md에 다음 항목을 포함한다.
  - 수정 파일 목록
  - 사용한 공식 endpoint / TR ID 출처
  - 구현된 계좌 / 잔고 / 포지션 조회 범위
  - fail-closed로 남긴 항목
  - secret/account/token 노출 없음 확인
  - live trading 비활성 유지 확인
  - market order guard 유지 확인
  - 테스트 결과
  - Claude 검증 요청 프롬프트
  - Claude 리뷰가 REQUEST CHANGES/BLOCK일 때만 사용할 follow-up Codex 수정 프롬프트 작성 규칙