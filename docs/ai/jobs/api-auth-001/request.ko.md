# 작업 ID
api-auth-001

# 작업명
KIS Open API OAuth 인증/토큰/HTTP 안전 래퍼 (mock/paper 기본)

원문 요청은 채팅 메시지에 포함되어 있어 본 파일에 옮겨 둔다. 이 문서는 사람이 작성한 한국어 요청의 자리이고, 구현 지시는 `plan.md`/`codex-task.md`에서 다룬다.

## 목표

KIS Open API의 인증 흐름과 토큰 라이프사이클, 그리고 그 위에서 동작하는 안전한 HTTP 요청 래퍼를 구현해, 국내주식·해외주식 시세/주문 API를 호출할 수 있는 공통 기반을 마련한다. 단, 본 작업에서는 실제 주문(실주문/모의주문) 호출은 구현하지 않는다.

## 자료 (사용자 업로드, 2026-05-15)

- **인증 API**: `uploads/3.xlsx` — 접근토큰발급(P), 접근토큰폐기(P), 실시간(웹소켓) 접속키 발급
- **국내주식 API**: `uploads/4.xlsx` (시세), `uploads/5.xlsx` (주문/계좌)
- **해외주식 API**: `uploads/1.xlsx` (기본시세), `uploads/2.xlsx` (실시간), `uploads/6.xlsx` (주문/계좌)

본 작업의 catalog는 `docs/kis/MISSING_OFFICIAL_VALUES.md` §1 OAuth와 `docs/kis/MISSING_MARKET_DATA_VALUES.md` §5 OAuth(KIS_1 land 완료)를 참고.

## 절대 하지 말 것

- `.env` 읽기 또는 수정.
- 실 app key / app secret / access token / 계좌번호 / 기타 자격증명 print, 로그, 문서에 기록.
- KIS endpoint / TR ID / 헤더 / payload 추측. 본 작업은 업로드된 공식 자료에 명시된 값만 사용.
- 실주문 또는 실거래(live trading) 동작 구현.
- LLM/Agent가 broker API를 직접 호출하는 경로 추가.
- 시장가 주문 활성화. `OrderType.MARKET` 도입.
- 자동 `git commit` / `push` / `merge` / `deploy`.

## 산출물

- `docs/ai/jobs/api-auth-001/plan.md` — Claude의 구현 계획 (인증 흐름 + 모듈 설계 + Codex 지시).
- `docs/ai/jobs/api-auth-001/codex-task.md` — Codex에게 전달할 작업 지시문.
- `docs/ai/jobs/api-auth-001/status.md` — 현재 작업 상태.
- (Codex 단계 이후) `docs/ai/jobs/api-auth-001/patch.md` — 구현 요약 + 테스트 결과.
- (Claude 리뷰 이후) `docs/ai/jobs/api-auth-001/review.md` — APPROVE / REQUEST CHANGES / BLOCK.

## 사전 컨텍스트

- 기존 `app/broker/kis.py`에 `KisAuthClient`/`KisHttpClient`/`KisAccountClient`/`KisMarketDataClient`/`KisBroker` skeleton이 존재하며, 모두 `NotImplementedError` 또는 fail-closed 상태로 유지되어 있다.
- 기존 `Settings`(`app/config.py`)에 `KIS_ENV`, `KIS_APP_KEY`, `KIS_APP_SECRET`, `KIS_ACCOUNT_NO`, `KIS_ORDER_DRY_RUN` 환경변수가 정의되어 있다.
- KIS_1으로 시세 catalog가 land되어, OAuth `/oauth2/tokenP` 모의 endpoint와 토큰 응답 필드가 `Confirmed: yes`로 확정되어 있다.
- 본 작업은 mvp-014-017에서 도입한 KIS skeleton 위에 **실 HTTP 호출까지는 구현**하되, 호출 범위를 OAuth 토큰 발급/폐기 + 안전 요청 래퍼까지로 제한한다. 시세/주문 호출은 본 작업의 후속 job에서 다룬다.

## 모드

- `mock` (기본): 네트워크 호출 없음. 모든 HTTP는 in-memory fake transport로 처리. 단위 테스트가 사용.
- `paper`: 모의투자 도메인(`https://openapivts.koreainvestment.com:29443`)으로만 실 HTTP. OAuth tokenP/revokeP에 한정.
- `live`: 본 작업에서는 **fail-closed로 거절**(`NotImplementedError` 또는 `KisAuthError`). 별 후속 job에서만 단계적 도입 검토.
