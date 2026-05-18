## 1. 요청 요약

KIS Open API의 OAuth 인증과 토큰 라이프사이클, 그리고 그 위에서 동작하는 안전한 HTTP 요청 래퍼를 구현한다. **mock 모드 기본, paper 모드 옵션, live 모드는 본 job에서 fail-closed**.

본 job이 land되면 국내주식·해외주식 시세/주문 API를 부르기 위한 공통 기반(인증 + 토큰 캐시 + 안전 요청 래퍼)이 완성되어, 후속 job에서 endpoint별 클라이언트 본문만 추가하면 된다. 본 job은 **시세/주문 본문 구현은 하지 않는다.**

### 사전 자료 (사용자 업로드, 2026-05-15)

- `uploads/3.xlsx` — OAuth: 접근토큰발급(P) `/oauth2/tokenP`, 폐기(P) `/oauth2/revokeP`, 실시간 접속키 `/oauth2/Approval` (웹소켓용, 본 job 범위 외).
- `uploads/4.xlsx`, `5.xlsx` — 국내주식 시세/주문.
- `uploads/1.xlsx`, `2.xlsx`, `6.xlsx` — 해외주식 시세/실시간/주문.

### 안전 원칙 (변경 없음)

- live trading 비활성 유지. `OrderType.MARKET` 부재 유지. `KIS_ORDER_DRY_RUN=true` 기본값 유지.
- `KisBroker`(주문) 도메인은 모의 base URL 유지. 5+1단 차단(`Settings`/`load_settings`/`RiskEngine`/`OMS`/`POST /paper/run`/`KisBroker.__init__`) 변경 없음.
- KIS endpoint/TR ID/payload/header **추측 금지** — 본 job은 업로드 공식 자료 명시 값만 사용.
- `.env` 읽기/수정 금지. 실 app key/app secret/access token/계좌번호를 코드/로그/문서/테스트에 노출 금지(fake 값만 사용).
- 자동 `git commit` / `push` / `merge` / `deploy` 금지.

---

## 2. 작업 범위

본 §2는 사용자가 plan에 포함하도록 명시한 10개 항목을 모두 다룬다.

### 2.1 인증 흐름 (Auth flow)

KIS는 **OAuth 2.0 Client Credentials Grant**를 사용한다.

```
1. Client는 (appkey, appsecret)을 KIS 홈페이지에서 발급받아 .env에 보관.
2. Client → KIS: POST /oauth2/tokenP
     Body (JSON): { "grant_type": "client_credentials", "appkey": ..., "appsecret": ... }
3. KIS → Client: { "access_token": "<jwt>", "token_type": "Bearer",
                   "expires_in": <seconds>, "access_token_token_expired": "YYYY-MM-DD HH:MM:SS" }
4. 이후 모든 시세/주문 호출에 `Authorization: Bearer <access_token>` + `appkey` + `appsecret` 헤더 동봉.
5. 토큰 사용 종료 시 POST /oauth2/revokeP (옵션).
   Body (JSON): { "appkey": ..., "appsecret": ..., "token": ... }
```

### 2.2 토큰 발급 endpoint

| 항목 | 값 | 자료 |
| --- | --- | --- |
| Method | POST | 3.xlsx 접근토큰발급(P) |
| Path | `/oauth2/tokenP` | 동 |
| Paper Base URL | `https://openapivts.koreainvestment.com:29443` | 동 |
| Live Base URL | `https://openapi.koreainvestment.com:9443` | 동 (본 job에선 호출하지 않음) |
| Body fields | `grant_type` = `client_credentials`, `appkey`, `appsecret` (모두 필수) | 동 |
| Content-Type | `application/json; charset=utf-8` | 동 |

폐기(옵션, 본 job에서 코드 추가):

| 항목 | 값 |
| --- | --- |
| Method | POST |
| Path | `/oauth2/revokeP` |
| Body fields | `appkey`, `appsecret`, `token` |
| Response | `{ "code": 200, "message": "..." }` |

웹소켓 접속키 `/oauth2/Approval`는 본 job 범위 외 (후속 job에서 다룸).

### 2.3 토큰 응답 필드

| Field | Type | 의미 | 처리 |
| --- | --- | --- | --- |
| `access_token` | string (length ≤ 350) | JWT 형식의 접근토큰 | 모든 API 호출의 `Authorization` 헤더에 `Bearer ${access_token}` 형태로 동봉. 메모리에만 보관. |
| `token_type` | string | `Bearer` 고정 | 헤더 prefix 검증용. |
| `expires_in` | number | 유효기간(초). 일반 ≈ 86400 (24시간). | 만료 epoch 계산: `issued_at + expires_in`. |
| `access_token_token_expired` | string `YYYY-MM-DD HH:MM:SS` | 만료 시각(KST). 보조 검증용. | `expires_in`과 교차 검증; 본 job은 `expires_in` 우선 사용. |

### 2.4 토큰 만료 처리

- 일반 고객 access_token 유효기간 **24시간**, **재발급 주기 6시간**(KIS 정책: 6시간 이내 재호출 시 기존 토큰 반환).
- 본 저장소는 **양보 safety margin 60초**(`KIS_TOKEN_EXPIRY_SAFETY_SECONDS`, 기본 60)를 두고 만료 60초 전부터 만료로 간주 → 사전 갱신.
- `is_authenticated()`은 `datetime.now(UTC) + safety_margin < expires_at` 검사.
- 만료 시 동작:
  - paper 모드: `authenticate()` 자동 호출(1회 시도). 실패 시 `KisAuthError`.
  - mock 모드: 자동 호출 안 함. `KisAuthError("authentication required")` 즉시.
- 토큰은 **메모리 only가 기본**. 선택적으로 파일 캐시(`KIS_TOKEN_CACHE_PATH`)에 저장 가능하되, 파일 쓰기 권한은 0600, 파일 내용은 JSON {access_token, expires_at}. 디스크 캐시는 opt-in이며 paper에서만 허용.
- 강제 폐기: `KisAuthClient.revoke()` 호출 시 `/oauth2/revokeP` POST 후 메모리/디스크 캐시 모두 clear.

### 2.5 필수 헤더 (모든 시세/주문 API 공통)

| Header | Required | 값 | 비고 |
| --- | --- | --- | --- |
| `content-type` | 응답 측 필수, 요청 측 endpoint별 상이 | `application/json; charset=utf-8` | POST는 항상 설정. GET은 일부 선택. |
| `authorization` | Y | `Bearer ${access_token}` | OAuth tokenP 자체 호출에는 미사용. |
| `appkey` | Y | 36자 | 모든 API 호출. |
| `appsecret` | Y | 180자 | 모든 API 호출. |
| `tr_id` | Y | 13자, endpoint별 상이 | 본 job은 OAuth만 호출하므로 사용 안 함. 시세/주문 client가 동봉. |
| `custtype` | endpoint별 상이 (`P` 개인 / `B` 법인) | 본 저장소는 개인 가정 → `P`. | KIS_MARKET_DATA_VALUES.md 1.3과 일치. |
| `tr_cont`, `personalseckey`, `seq_no`, `mac_address`, `phone_number`, `ip_addr`, `gt_uid` | 대부분 N (일부 법인 필수) | 본 job은 미설정 (개인 고객 default) | 후속 job에서 필요 시 도입. |

### 2.6 국내주식 API 인증 요구

- 인증 흐름 동일(OAuth tokenP).
- 헤더 동일(2.5 참고).
- 모의/실전 동일 endpoint 다수 지원(시세 + 주문 둘 다 paper 가능).
- TR_ID prefix:
  - 시세: `FHKST*`, `FHPST*` 등.
  - 주문: 실전 `TTTC*`, 모의 `VTTC*`.
- Path prefix: `/uapi/domestic-stock/v1/*`.

> 본 job은 국내주식 client 본문을 만들지 않는다. 인증 + HTTP 래퍼만 제공.

### 2.7 해외주식 API 인증 요구

- 인증 흐름 동일(OAuth tokenP).
- 헤더 동일(2.5 참고).
- 모의 지원이 endpoint별로 다름: 시세는 `해외주식 현재체결가`만 모의 지원, 현재가상세/현재가 호가는 모의 미지원(KIS_1 land 결과). 주문은 대부분 모의 지원.
- TR_ID prefix:
  - 시세: `HHDFS*`, `FHKST03*` 등.
  - 주문: 실전 `TTTT*`/`TTTS*`, 모의 `VTTT*`/`VTTS*`.
- Path prefix: `/uapi/overseas-price/v1/*` (시세), `/uapi/overseas-stock/v1/*` (주문/계좌).

> 본 job은 해외주식 client 본문도 만들지 않는다.

### 2.8 국내 / 해외 endpoint 차이 요약

| 축 | 국내주식 | 해외주식 |
| --- | --- | --- |
| Path prefix (시세) | `/uapi/domestic-stock/v1/quotations/*` | `/uapi/overseas-price/v1/quotations/*` |
| Path prefix (주문/계좌) | `/uapi/domestic-stock/v1/trading/*` | `/uapi/overseas-stock/v1/trading/*` |
| TR_ID prefix (시세) | `FHKST*`, `FHPST*` | `HHDFS*`, `FHKST03*` |
| TR_ID prefix (주문) | 실전 `TTTC*` / 모의 `VTTC*` | 실전 `TTTT*`/`TTTS*` / 모의 `VTTT*`/`VTTS*` |
| 모의 지원 범위 (시세) | 대부분 지원 | 일부만 지원 (현재체결가만 paper) |
| 모의 지원 범위 (주문) | 대부분 지원 | 대부분 지원 |
| Base URL (paper) | `https://openapivts.koreainvestment.com:29443` | 동일 |
| Base URL (live) | `https://openapi.koreainvestment.com:9443` | 동일 |
| OAuth tokenP | 동일 endpoint | 동일 endpoint (앱키 1쌍으로 양쪽 모두 호출 가능) |
| 거래소 코드 파라미터 | `FID_COND_MRKT_DIV_CODE` (J:KRX, NX:NXT, UN:통합) | `EXCD` (NAS/NYS/AMS/HKS/TSE/SHS/SZS/HSX/HNX 등) |

**핵심 결론**: OAuth 흐름과 인증 헤더 구조가 동일하므로 **단일 `KisAuthClient` + 단일 `KisHttpClient`**가 양쪽을 모두 커버. 차이는 endpoint별 path/TR_ID/payload에 국한되어 후속 client(KisDomesticMarketDataClient, KisOverseasMarketDataClient 등)에서만 처리.

### 2.9 필수 환경변수 (값 없이 이름만)

기존 (그대로 사용):

- `KIS_ENV` — `paper` / `live`. 본 job은 `paper` 또는 미설정만 허용.
- `KIS_APP_KEY` — 36자.
- `KIS_APP_SECRET` — 180자.
- `KIS_ACCOUNT_NO` — 본 job 직접 미사용(인증 자체에는 불필요). 기존 필드 보존.

본 job 신설:

- `KIS_API_MODE` — `mock` (기본, 네트워크 미사용) / `paper` (실 HTTP, 모의 도메인 한정) / `live` (본 job에서 fail-closed).
- `KIS_BASE_URL_PAPER` — 옵션. 기본 상수 `https://openapivts.koreainvestment.com:29443` override.
- `KIS_BASE_URL_LIVE` — 옵션. 기본 상수 `https://openapi.koreainvestment.com:9443` override. 본 job에서는 reader만 두고 사용 경로 fail-closed.
- `KIS_OAUTH_TIMEOUT_SECONDS` — 옵션. 기본 5.0초.
- `KIS_OAUTH_MAX_RETRIES` — 옵션. 기본 1회. 408/5xx에 한해 backoff retry.
- `KIS_TOKEN_EXPIRY_SAFETY_SECONDS` — 옵션. 기본 60초. 사전 갱신 margin.
- `KIS_TOKEN_CACHE_PATH` — 옵션. 미설정 시 메모리 only.

`.env.example`에 위 신설 변수의 **이름과 한 줄 설명만** 추가(값 또는 placeholder 금지).

### 2.10 안전 모듈 설계 (Codex가 따를 골격)

#### 2.10.1 파일 구성

신규 파일:

- `app/broker/kis_token_cache.py` — `TokenRecord` dataclass + `InMemoryTokenCache` + `FileTokenCache` (opt-in).
- `app/broker/kis_http.py` — `KisApiMode` enum, `KisHttpTransport` Protocol, `MockTransport`, `UrllibTransport` (paper-only 가드 포함), `SafeKisHttpClient`(`request()` 본문).

기존 파일 수정:

- `app/config.py` — 위 §2.9 신설 환경변수 7개 추가. 기본값은 모두 안전(mock/None).
- `app/broker/kis.py` — `KisAuthClient.authenticate()` / `refresh_token()` / 신규 `revoke()` 본문 구현.
  - `__init__`에 token cache + http client 주입(생성자 인자로). 기본값은 in-memory cache + mode-aware http.
  - 기존 메서드 시그니처와 외부 동작(state machine, `_store_token`, `is_authenticated`, `get_access_token`, `clear_token`, `last_error`)은 변경 금지.
  - `KisAccountClient`/`KisMarketDataClient`/`KisBroker` 본문은 미변경.
- `app/broker/__init__.py` — 필요시 새 export만.

신규 테스트 파일:

- `tests/test_kis_api_mode.py`
- `tests/test_kis_http_transport.py`
- `tests/test_kis_token_cache.py`
- `tests/test_kis_auth_client_http.py` (기존 `test_kis_auth_client.py`는 보존 + 신규 케이스 추가, 또는 별 파일)
- `tests/test_kis_config_api_mode.py`

#### 2.10.2 의존성 / Transport 주입

- Transport는 **Protocol**(또는 Callable)로 정의 → 단위 테스트가 fake 주입 가능.
- 기본 `MockTransport`: 모든 호출에서 `KisAuthError("mock_mode_no_network")` 즉시 발생.
- `UrllibTransport`: 표준 라이브러리 `urllib.request`만 사용(추가 의존성 0건). `https://openapivts.koreainvestment.com:29443`만 허용; 다른 host 호출 시 `KisAuthError("disallowed_host")`. 타임아웃 강제.
- `LiveTransport`: 본 job에서는 정의하지 않음(클래스 자체 미존재). live 모드 진입 시 `SafeKisHttpClient.__init__`에서 `NotImplementedError("live mode not supported by api-auth-001")` raise.

#### 2.10.3 안전 요청 래퍼 책무

`SafeKisHttpClient.request(method, path, headers, payload)`:

1. mode 검사 — mock이면 transport가 즉시 reject. live면 진입 자체 차단.
2. URL 조립 — `base_url + path`. base_url은 mode + Settings에서 결정. host allowlist 검증.
3. 헤더 sanitize — 사용자가 넘긴 헤더에서 `authorization`/`appkey`/`appsecret`/`token`/`personalseckey`를 trace/디버그 로그에 노출하지 않음 (`SENSITIVE_RESPONSE_KEYS`에 추가).
4. payload 검증 — POST면 JSON 직렬화. 그 외 body 금지.
5. 호출 — timeout + 1회 retry on 408/5xx (exponential backoff 2초).
6. 응답 파싱 — JSON 디코딩. 실패 시 `KisHttpError` raise(응답 body는 sanitize 후 일부만 로깅, full body 노출 금지).
7. 에러 매핑 — KIS 응답에 `rt_cd != "0"`이면 `KisHttpError`로 매핑. `msg_cd`/`msg1` 보존하되 잠재 secret 마스킹.
8. 반환 — sanitized dict.

#### 2.10.4 KisAuthClient.authenticate 본문 골격 (Codex 구현용 의사코드)

```python
def authenticate(self) -> None:
    # 1. settings 검증 — paper 모드 외 거절 (live는 KisApiMode에서 차단)
    _validate_paper_settings(self._settings)
    # 2. mock 모드면 즉시 fail-closed
    if self._settings.kis_api_mode == "mock":
        self._last_error = "mock_mode_no_network"
        raise KisAuthError("mock_mode_no_network")
    # 3. 캐시 hit 검사 — 6시간 이내 재호출 정책 활용
    cached = self._cache.get()
    if cached is not None and not cached.is_expiring_soon(self._safety_seconds):
        self._store_token(cached.access_token, cached.expires_in_seconds)
        return
    # 4. 실 HTTP — POST /oauth2/tokenP
    body = {"grant_type": "client_credentials",
            "appkey": self._settings.kis_app_key,
            "appsecret": self._settings.kis_app_secret}
    headers = {"content-type": "application/json; charset=utf-8"}
    resp = self._http.request("POST", "/oauth2/tokenP", headers=headers, payload=body)
    # 5. 응답 필수 필드 검증
    access_token = resp.get("access_token")
    token_type = resp.get("token_type")
    expires_in = resp.get("expires_in")
    if not access_token or token_type != "Bearer" or not isinstance(expires_in, int):
        raise KisAuthError("invalid_token_response")
    # 6. 메모리 저장 + (옵션) 캐시 저장
    self._store_token(access_token, int(expires_in))
    self._cache.set(TokenRecord(access_token=access_token,
                                expires_at=self._expires_at,
                                issued_at=datetime.now(timezone.utc)))
```

`refresh_token()` = `clear_token()` + `authenticate()`.

`revoke()`:
```python
def revoke(self) -> None:
    token = self._access_token
    if not token:
        return
    body = {"appkey": self._settings.kis_app_key,
            "appsecret": self._settings.kis_app_secret,
            "token": token}
    headers = {"content-type": "application/json; charset=utf-8"}
    try:
        self._http.request("POST", "/oauth2/revokeP", headers=headers, payload=body)
    finally:
        self.clear_token()
        self._cache.clear()
```

#### 2.10.5 안전 invariant (구현 후 grep 검증)

- 본 job이 추가/수정한 모든 파일에 대해:
  - 실 host literal: `openapivts.koreainvestment.com:29443`만 허용. `openapi.koreainvestment.com:9443`은 상수에 두되 사용 경로에서 fail-closed.
  - 외부 HTTP 라이브러리 import: `httpx`, `requests`, `aiohttp`, `urllib3` 0건. `urllib.request`만 허용.
  - 실 키/시크릿/토큰 패턴 0건 (`PSNFD`, `PKID`, `AKIA`, `sk-`, `ghp_`, `Bearer eyJ`, `appkey=`, `appsecret=`, 10자리 연속 숫자).
  - `print`로 헤더/페이로드 dump 0건.
  - `LiveTransport` 또는 실전 base URL을 사용 경로에서 활용 0건.

### 포함 (In scope) — 요약

- 위 2.10 모듈 골격에 따른 신규/수정 파일.
- 인증 흐름의 mock + paper 동작.
- 토큰 캐시 추상화(메모리 default, 파일 opt-in).
- 안전 HTTP 요청 래퍼(timeout, retry, sanitize, mode guard, host allowlist).
- 단위 테스트(fake transport).

### 제외 (Out of scope; 절대 만지지 않음)

- `KisMarketDataClient`/`KisAccountClient`/`KisBroker`의 endpoint 본문(여전히 `NotImplementedError`).
- 시세/주문 호출 자체.
- 웹소켓 접속키 발급(`/oauth2/Approval`) 및 실시간 통신.
- 시장가 주문, RiskEngine 우회, OMS 우회, Strategy의 broker 직접 호출.
- `OrderType.MARKET` 도입.
- `.env`, `.env.example`에 실 값/placeholder 작성(이름과 한 줄 설명만).
- `docs/kis/MISSING_*` 파일 변경.
- 자동 `git commit` / `push` / `merge` / `deploy`.

---

## 3. 수정해야 할 파일

| 파일 | 동작 | 비고 |
| --- | --- | --- |
| `projects/paper-trading/app/config.py` | §2.9 신설 env var 7개 추가 + load 로직 + 검증 | `Settings` dataclass에 새 필드 + `load_settings()` 분기 |
| `projects/paper-trading/app/broker/kis.py` | `KisAuthClient.authenticate`/`refresh_token`/`revoke` 본문 구현, `__init__`에 token cache + http client 의존성 주입 추가 | 기존 외부 시그니처/state machine 보존 |
| `projects/paper-trading/app/broker/kis_http.py` | 신규: `KisApiMode`, `KisHttpTransport` Protocol, `MockTransport`, `UrllibTransport`, `SafeKisHttpClient` | stdlib only(`urllib.request`) |
| `projects/paper-trading/app/broker/kis_token_cache.py` | 신규: `TokenRecord`, `InMemoryTokenCache`, `FileTokenCache`(opt-in, 0600) | stdlib only |
| `projects/paper-trading/app/broker/__init__.py` | 필요 시 export 추가 | 신규 심볼이 외부에서 import 되어야 하는 경우만 |
| `projects/paper-trading/tests/test_kis_api_mode.py` | 신규: KisApiMode enum + load_settings 검증 | |
| `projects/paper-trading/tests/test_kis_http_transport.py` | 신규: MockTransport / UrllibTransport host allowlist / sanitize / timeout / retry | UrllibTransport 테스트는 fake socket 또는 `monkeypatch`로 외부 호출 차단 |
| `projects/paper-trading/tests/test_kis_token_cache.py` | 신규: InMemory + File 캐시, 파일 권한 0600, expiry, clear | tmp_path 사용 |
| `projects/paper-trading/tests/test_kis_auth_client_http.py` | 신규: mock/paper 흐름, 응답 파싱, 만료 갱신, revoke, fail-closed | fake transport 주입 |
| `projects/paper-trading/tests/test_kis_config.py` | 기존 + 신설 env var 케이스 추가 | tmp_path 격리 유지(KIS_1 회고) |
| `projects/paper-trading/tests/test_kis_auth_client.py` | 기존 보존 + `_validate_paper_settings` 케이스 회귀 추가 | |
| `projects/paper-trading/.env.example` | 신설 env var 이름 + 한 줄 설명 추가 (값/placeholder 금지) | |
| `projects/paper-trading/README.md` | `## API 인증 (api-auth-001)` 단락 추가 | 기존 단락 변경 금지 |
| `docs/ai/jobs/api-auth-001/patch.md` | 신규: Codex 적용 요약 | Codex가 작성 |

**미변경 (절대)**:
`app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/static/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/runtime/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*`, `app/domain/*`, `app/broker/{base.py, paper.py, alpaca_paper.py, kis_quote_mapper.py}`, `.env`, `.gitignore`, `docs/kis/MISSING_*`, `docs/ai/MASTER_TRADING_ROADMAP.md`, `prompts/*`, `scripts/*`, mvp-001..KIS_1 산출물.

---

## 4. Codex 구현 지시문

상세 본문은 `docs/ai/jobs/api-auth-001/codex-task.md` 참고. 요점:

1. **§3 파일 목록만 변경.** 그 외 파일 변경 0건.
2. **Mock 기본**: Settings 기본값 `KIS_API_MODE="mock"`, FileTokenCache 미사용, OAuth 자동 호출 안 함.
3. **Paper 옵션**: Settings에 `KIS_API_MODE="paper"` + 유효한 `KIS_APP_KEY`/`KIS_APP_SECRET` 모두 있을 때만 실 HTTP 활성.
4. **Live는 fail-closed**: `KIS_API_MODE="live"` 또는 `KIS_ENV="live"` 시 `SafeKisHttpClient.__init__`에서 `KisConfigError("live_mode_not_supported_yet")` raise. `KisAuthClient` 생성 자체는 가능하되 mode 검사로 fail-closed.
5. **OAuth만 호출**. 본 job은 `/oauth2/tokenP`와 `/oauth2/revokeP`만 호출 경로를 만든다. 그 외 path를 `SafeKisHttpClient.request`에 넘기면 `KisHttpError("path_not_allowed_by_api_auth_001")` 거절(allowlist).
6. **외부 HTTP lib 금지** — `urllib.request`만. `requests`/`httpx`/`aiohttp` import 시 빌드 실패하도록 테스트에 grep 단정 추가.
7. **Secrets/tokens 노출 금지** — repr/로그/sanitize 패스를 모두 통과한 후에만 값 외부 노출. fake transport 테스트에서 실 키 패턴 grep 0건 단정.
8. **테스트** — pytest 전체 PASS 유지(기존 ~214 + 신규 약 20+). 새 테스트는 외부 네트워크 호출 0건(소켓 차단 또는 fake transport).
9. **`.env`/`.env.example`** — 본 job은 `.env`를 읽거나 수정하지 않는다. `.env.example`에는 신설 변수의 **이름과 한 줄 설명**만(값/placeholder 금지).
10. **commit/push/merge/deploy 금지**. Codex는 변경만 작성. 사람이 별도로 staging/commit.

---

## 5. 테스트 기준

### 5.1 신규 테스트 카테고리

| 카테고리 | 파일 | 핵심 단정 |
| --- | --- | --- |
| Settings 로드 | `test_kis_config.py` (확장) | `KIS_API_MODE` 기본값 = `mock`, 유효값 mock/paper/live만 허용, 그 외 raise. `KIS_BASE_URL_*` 옵션 override, 기본 상수 일치. `KIS_TOKEN_EXPIRY_SAFETY_SECONDS` 기본 60. |
| Mode enum | `test_kis_api_mode.py` | enum 멤버 3개. `KisApiMode.LIVE`는 본 job에서 SafeKisHttpClient에 들어오면 `KisConfigError`. |
| Transport — Mock | `test_kis_http_transport.py` | `MockTransport.request()` 어떤 path든 즉시 `KisAuthError("mock_mode_no_network")`. |
| Transport — Urllib host allowlist | 동 | 비허용 host 호출 시 `KisAuthError("disallowed_host")`. |
| Transport — Urllib timeout | 동 | `KIS_OAUTH_TIMEOUT_SECONDS` 적용, fake socket로 검증. |
| Transport — Urllib retry | 동 | 5xx 응답 시 1회 retry, 2회 연속 실패 시 `KisHttpError`. |
| Transport — sanitize 응답 | 동 | 응답 dict의 `access_token`/`appkey`/`appsecret` 등이 logger 외 외부로 노출되지 않음(여기서는 transport는 raw dict 반환, sanitize는 SafeKisHttpClient에서). |
| Token cache — InMemory | `test_kis_token_cache.py` | set/get/expiring_soon/clear. 만료 후 get → None. |
| Token cache — File | 동 | tmp_path에 파일 생성, mode 0o600, JSON {access_token, expires_at, issued_at}. 다른 프로세스에서 read 가능, 잘못된 JSON은 clear. |
| AuthClient — mock | `test_kis_auth_client_http.py` | mock 모드에서 `authenticate()` 즉시 `KisAuthError`. |
| AuthClient — paper 정상 | 동 | fake transport가 정상 토큰 응답 시 `is_authenticated()=True`, `get_access_token()` 비공개로 반환, `expires_at` ≈ now + expires_in. |
| AuthClient — 응답 검증 | 동 | `token_type != "Bearer"` → reject. `expires_in` 누락 → reject. `access_token` 누락 → reject. |
| AuthClient — 캐시 reuse | 동 | 6시간 이내 재호출 시 transport 호출 1회만 발생(첫 호출). 두 번째는 cache hit. |
| AuthClient — 만료 사전 갱신 | 동 | safety_seconds 이내 진입 시 자동 refresh. |
| AuthClient — revoke | 동 | revoke 후 메모리/캐시 clear. transport에 `/oauth2/revokeP` 1회 POST. |
| AuthClient — live 모드 거절 | 동 | `KIS_API_MODE=live` 또는 `KIS_ENV=live`로 만든 Settings로 SafeKisHttpClient 생성 시 `KisConfigError`. |
| 정합성 회귀 | `test_kis_auth_client.py` (기존 보존) | 기존 5개 테스트 PASS 유지. `_store_token` 동작 변경 없음. |
| 외부 HTTP lib grep | `test_kis_http_boundaries.py` (확장) | `app/broker/kis*.py`에 `requests`/`httpx`/`aiohttp`/`urllib3` import 0건. |
| Sanitize | `test_kis_http_transport.py` | SafeKisHttpClient가 반환하는 dict에 `access_token`/`appkey` 등이 값 그대로 살아 있되 별도 로깅 패스에서는 sanitize 거침(여기서는 sanitize 패스의 단위 테스트만). |

### 5.2 통합

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

- 기존 약 214 + 신규 약 20+ 모두 PASS.
- 외부 네트워크 호출 0건(테스트 환경에서 검증).
- 회귀 0건.

### 5.3 안전 grep 단정 (Codex가 patch.md에 기록)

| 패턴 | 검색 범위 | 기대 |
| --- | --- | --- |
| `PSNFD`, `PKID`, `AKIA`, `sk-`, `ghp_`, `Bearer eyJ`, `appkey=`, `appsecret=` | 신설/수정 파일 전부 | 0건 |
| 10자리 이상 연속 숫자 (계좌번호 패턴) | 동 | 0건 (fake 값 8자리 이하만 허용) |
| `import requests`, `import httpx`, `import aiohttp`, `import urllib3` | `app/broker/kis*.py` | 0건 |
| `openapi.koreainvestment.com:9443` 사용 경로 (호출 흐름) | live transport 부재 + SafeKisHttpClient.live 분기 fail-closed로 검증 | 사용 경로 0건 |
| `LiveTransport` 또는 `class.*Live.*Transport` | 본 job 신설 파일 | 클래스 자체 부재 |

---

## 6. 리뷰 체크리스트

### 콘텐츠

- [ ] `KIS_API_MODE` 기본값 = `mock`. `KisAuthClient.authenticate()`가 mock 모드에서 즉시 fail-closed.
- [ ] paper 모드에서 fake transport로 토큰 응답이 정상 파싱·저장됨.
- [ ] 6시간 캐시 hit + safety margin 사전 갱신 동작 확인.
- [ ] `/oauth2/tokenP` / `/oauth2/revokeP` 외 path가 `SafeKisHttpClient`에 들어오면 fail-closed.
- [ ] 모든 신설 모듈이 stdlib only (`urllib.request` 외 추가 의존성 0건).
- [ ] live 모드 진입 시 `KisConfigError` 즉시(클라이언트 생성 자체 차단).

### 안전

- [ ] 신설/수정 파일 어디에도 실 app key / app secret / access token / 계좌번호 0건.
- [ ] `.env` 읽기/수정 0건. `.env.example`은 변수 이름 + 한 줄 설명만 추가(값/placeholder 0건).
- [ ] `KisBroker`(주문) / `KisMarketDataClient` / `KisAccountClient` 본문 변경 0건. 여전히 `NotImplementedError`.
- [ ] `OrderType.MARKET` 부재 유지. `KIS_ORDER_DRY_RUN=true` 기본값 유지. 5+1단 차단 유지.
- [ ] Strategy / Agent / LLM이 broker API를 직접 호출하는 경로 추가 0건.
- [ ] 외부 HTTP 라이브러리 import 0건.
- [ ] `LiveTransport` 클래스 부재.

### 테스트 / 프로세스

- [ ] 신규 테스트 약 20+ PASS, 기존 약 214 PASS 유지.
- [ ] 테스트 중 외부 네트워크 호출 0건.
- [ ] `compileall` 무오류.
- [ ] `patch.md`에 변경 파일 목록 + 안전 grep 결과 + 테스트 결과 + commit-skip 확인 기록.
- [ ] commit / push / merge / 배포 자동화 0건.

### 사람이 직접 해야 할 후속 액션

1. `git status` / `git diff`로 변경 범위 검증.
2. commit 시 `app/config.py`, `app/broker/kis.py`, `app/broker/kis_http.py`, `app/broker/kis_token_cache.py`, `app/broker/__init__.py`, 새/수정 테스트, `.env.example`, `README.md`, `docs/ai/jobs/api-auth-001/`만 staging.
3. **`.env`에 실 키를 채우는 작업은 별도 단계**(본 job은 안 함). 키를 넣은 뒤 paper 모드로 `python -m app.main healthcheck-auth`(또는 동등 진입점) 같은 도구로 1회 수동 검증 권장 — 단, 그 도구도 본 job에서는 추가하지 않는다(후속 job).
4. 후속 job 후보:
   - `api-market-data-001` — `KisMarketDataClient.get_quote()` 본문 (현재체결가 paper)
   - `api-domestic-quote-001` — 국내주식 시세 client 추가
   - `api-orders-paper-001` — 모의 주문 path 본문 (해외/국내 분리 가능)
   - `KIS_2` — `MISSING_OFFICIAL_VALUES.md` §2 계좌 + §4 주문 catalog 채우기 (자료 6.xlsx 기반)
