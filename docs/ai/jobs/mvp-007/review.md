# Review — mvp-007: KIS Open API 인증 / 계좌 / 시세 구조 (HTTP 없음)

## Verdict

**APPROVE** (단, commit 전 한 가지 권고가 있음 — Findings #1)

mvp-007 구현이 plan/codex-task의 핵심 불변식을 모두 충족하고, pytest **74개 모두 PASS**, 정적 안전 검사도 모두 통과. 이전 BLOCK 보고는 deprecated, 본 review가 최종 결과를 기록한다.

## 검증된 사실 (직접 확인)

### 코드 / 안전 invariant

1. **mvp-006-1 사전 점검 통과** — `patch.md` §4 Precheck 결과 `kis.py OK / config.py KIS fields OK / routes.py KIS status OK / env.example OK` 모두 PASS.
2. **`app/broker/kis.py`에 HTTP 라이브러리 import 0건.** `grep "requests|httpx|aiohttp|urllib"` 결과 빈.
3. **`app/broker/kis.py`에 KIS endpoint URL 코드 0건.** `grep "https?://"` 결과 빈.
4. **TR ID / endpoint path / appkey/appsecret 키워드 0건.** `grep "TR_ID|tr_id|/uapi/|/oauth2/|/api/v1/|appsecret|appkey"` 결과 빈.
5. **`app/strategy/`가 `app.broker.kis` 미import.** `grep "from app\\.broker\\.kis|import app\\.broker\\.kis" app/strategy/` 결과 빈.
6. **`kis_secret_exposed` 이름 통일 완료(`secret_exposed`만 존재).** `grep "kis_secret_exposed"` 결과 빈.
7. **`OrderType.MARKET` 부재.** 유일한 `MARKET` 매칭은 `Session.PRE_MARKET`(별개 enum 멤버).
8. **`live_trading_enabled = True`는 negative test에서만.** `tests/test_oms.py:28`, `tests/test_risk_engine.py:26` — 둘 다 reject 동작 검증.

### 클래스 구조 (`app/broker/kis.py`)

9. **예외 계층 4단**: `KisError → KisConfigError / KisAuthError / KisDataUnavailableError` (line 17–30).
10. **`KisAuthClient`** (line 33–80):
    - `__init__`: `kis_app_key`/`kis_app_secret` 누락 시 `KisConfigError`.
    - 상태 머신: `is_authenticated()`은 `_access_token`+`_expires_at` 비교(line 52–55).
    - `get_access_token()`이 만료 시 `None` 반환(line 57–60).
    - `clear_token()` 즉시 비움.
    - `authenticate()`/`refresh_token()` `NotImplementedError` with "official documentation" 메시지(line 66–76).
    - `__repr__`이 `KisAuthClient(env=..., token=<set>|<unset>)`로 마스킹(line 48–50). key/secret 노출 없음.
11. **`KisAccountClient`** (line 83–126):
    - `__init__`: `kis_account_no` 누락 시 `KisConfigError`.
    - `masked_account_no()`: 길이 ≤4면 `***`, 아니면 `***xxxx`(line 97–101).
    - `is_loaded()` 초기 False.
    - `get_account/get_positions/get_cash_balance` `NotImplementedError` with "official documentation" TODO.
    - `__repr__`이 masked account만 노출(line 94–95). raw account 노출 없음.
12. **`KisMarketDataClient`** (line 129–162):
    - `get_quote/get_last_price` `NotImplementedError` with "official documentation" TODO.
    - `healthcheck_market_data()`은 정적 disconnected dict(`connected: False`, `auth_required: True`, `auth_present: ...`)(line 152–158). 네트워크 호출 없음.
    - `__repr__`이 `<disconnected>`만 노출(line 137–138).
13. **`KisBroker` 컴포지션** (line 165–271):
    - mvp-006-1의 fail-closed init 검증 보존: `KIS_ENV != "paper"`, account/key/secret 누락 → `RuntimeError`.
    - `auth`/`account`/`market_data`/`last_error` 4개 `@property` 노출(line 200–214).
    - `authenticate`/`refresh_token`/`get_account`/`get_positions`/`get_quote`이 sub-client로 위임(line 216–229).
    - `get_open_orders`/`place_order`/`cancel_order`/`replace_order` `NotImplementedError` 유지(line 231–246). `place_order/cancel_order/replace_order` 메시지에 "DO NOT WIRE without OMS-only execution + RiskEngine guard" 명시.
    - `healthcheck()`이 sub-component 상태(`authenticated`/`account_loaded`/`market_data`/`last_error`/`order_execution_implemented: False`)를 모아 반환(line 248–259).
    - BrokerAdapter 호환(`submit/cancel/open_orders/positions`)이 KIS-스타일로 위임(line 261–271).
    - `__repr__`이 `account=***xxxx, app_key=<set>, app_secret=<set>`로 마스킹(line 194–198).

### `app/api/server.py` (`app.state.kis_broker` 보관)

14. `KisBroker(settings)` 인스턴스화 시도 → 성공 시 `app.state.kis_broker = kis_broker`, 실패 시 `None`(line 27–42).
15. `except RuntimeError`만 catch — broad `Exception` 미사용.
16. OMS는 여전히 `PaperBroker`로 와이어링(line 19–20). KIS는 OMS 경로에 없음.

### `app/api/routes.py` (`/paper/status` 확장)

17. 신규 필드 추가: `broker_type`, `broker_environment`, `live_trading_enabled`, `market_orders_allowed`, `kis_config_loaded`, `kis_authenticated`, `kis_account_loaded`, `kis_market_data_available`, `last_broker_error`, `account_no_masked`, `secret_exposed: False`, `configured_brokers`.
18. `account_no_masked`은 `kis_broker.account.masked_account_no()` 결과(없으면 `<unset>`). raw `settings.kis_account_no` 직접 참조 없음(line 60).
19. `kis_secret_exposed`는 제거, `secret_exposed`로 통일.
20. credentials는 응답 어디에도 미포함(테스트가 본문 텍스트 검사로 검증).

### 테스트

21. **pytest 결과: 74 passed, 0 failed.** `.venv/bin/python -m pytest -p no:cacheprovider`:
    - 기존 mvp-005 19개 + mvp-006-1 17개 + mvp-007 신규 (auth 6 + account 7 + market_data 3 + broker_interface 확장 + api_status 확장) = 74 PASS.
    - `tests/test_kis_auth_client.py`: 6 PASS (credentials 검증, 초기 상태, 토큰 상태 머신, 만료 토큰 거부, 네트워크 fail-closed, repr 마스킹).
    - `tests/test_kis_account_client.py`: 7 PASS (parametrized 마스킹 3 case + credentials/state/fail-closed/repr).
    - `tests/test_kis_market_data_client.py`: 3 PASS (fail-closed/healthcheck/repr).
    - `tests/test_broker_interface.py`: 15 PASS (sub-client 노출 + healthcheck 확장 + 모든 NotImplementedError).
    - `tests/test_api_paper_status.py`: 4 PASS (healthz/safety/kis_metadata/with_kis_config_masks_account).
22. **본문 텍스트 검사 명시적**: `test_paper_status_with_kis_config_masks_account` (line 62–87)이 `"50187996"`, `"fake-key"`, `"fake-secret"`, `"KIS_APP_KEY"`, `"KIS_APP_SECRET"` 모두 response.text에 미포함을 단언.

## Findings (severity 순)

### 1. (low — privacy) 테스트 코드에 실제 KIS 모의투자 계좌번호가 하드코딩되어 있음

- 위치: `tests/test_kis_auth_client.py:13`, `tests/test_kis_account_client.py:8, 30, 54`, `tests/test_kis_market_data_client.py:12`, `tests/test_api_paper_status.py:67, 82, 86`.
- 관찰: 모든 테스트가 `kis_account_no="50187996"` 또는 `"50187996"` 리터럴을 사용한다. 이는 이전 세션에서 사용자가 chat에 노출한 실제 KIS 모의투자 계좌번호다.
- 영향: 
  - 안전 측면: 계좌번호 단독으로는 거래 불가(app_key+app_secret이 필요). 키 자체는 코드/git에 없으므로 즉각적 위협은 낮음.
  - 프라이버시 측면: 테스트 파일이 commit되면 계좌번호가 git 히스토리에 영구 기록됨. 이는 이미 chat 히스토리에 노출된 정보와 중복이지만, 디스크/git의 추가 공개 표면을 만든다.
  - 테스트 의도: parametrized 마스킹 테스트(`("50187996", "***7996")`)는 실제 형태(8자리)의 값으로 검증하려는 의도로 보임. 가짜 8자리 숫자로 대체해도 검증 의미는 동일.
- 권장: commit 전에 다음을 한 번 sed로 치환:
  ```bash
  cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
  sed -i 's/50187996/12345678/g' tests/test_kis_*.py tests/test_api_paper_status.py
  .venv/bin/python -m pytest -p no:cacheprovider   # 재검증
  ```
  `12345678`(또는 다른 명백히 가짜인 8자리)로 바꾸면 마스킹 검증(`***5678`)이 동일하게 작동하고, git에 실제 계좌번호가 들어가지 않는다.
- 우선순위: low — 본 review가 APPROVE인 이유는 (a) 키/secret은 노출 없음, (b) 코드 안전성에 영향 없음, (c) 사용자가 paper-only credentials 노출 risk를 이미 수용한 입장. 다만 깔끔히 정리하는 것이 좋다.

### 2. (informational — process) 워크트리에 mvp-007 외 dirty 변경이 누적되어 있음

- 위치: `git diff --stat`(patch.md §4):
  ```
  docs/ai/jobs/mvp-004/request.ko.md |  78
  web/public/app.js                  | 141
  web/public/index.html              | 144
  web/public/style.css               |  74
  web/server.js                      | 527
  ```
- 관찰: `projects/paper-trading/`(전체 untracked)에 들어 있는 mvp-007 변경은 `git diff --stat`에 안 보임. 위 5개 modified는 mvp-004 잔재 + 별도 GUI 작업.
- 영향: 안전 위반 아님. commit 시 staging 범위를 mvp-007/paper-trading으로 한정해야 함.
- 권장:
  ```bash
  git add projects/paper-trading docs/ai/jobs/mvp-007
  git diff --cached --stat   # 검증
  ```

### 3. (informational) `.gitignore`가 untracked 상태

- 관찰: `git status`에 `?? .gitignore` — 본 세션에서 추가된 루트 `.gitignore`(이번 patch.md에선 변경 없음, 이전 작업에서 생성).
- 영향: 없음. commit 시 같이 staging 권장(`.env*` 보호 룰 보존을 위해).

## File / line references (요청 ↔ 산출물 매핑)

| 요청 항목 | 위치 | 상태 |
| --- | --- | --- |
| 1. KIS 모의투자 인증 토큰 발급 연결 | `KisAuthClient.authenticate()` line 66 | NotImplementedError + TODO ✓ |
| 2. 토큰 refresh / 만료 처리 구조 | `is_authenticated`/`get_access_token`/`clear_token` line 52–64 | 구현됨 + 테스트 통과 ✓ |
| 3. KIS 모의투자 계좌 정보 조회 | `KisAccountClient.get_account()` line 106 | NotImplementedError + TODO ✓ |
| 4. KIS 해외/미국주식 시세 조회 구조 | `KisMarketDataClient.get_quote()` line 140 | NotImplementedError + TODO ✓ |
| 5. Broker healthcheck 강화 | `KisBroker.healthcheck()` line 248–259 | 7-field dict 구현 ✓ |
| 6. `/paper/status`에 KIS 연결 상태 표시 | `routes.py` line 27–63 | 12개 필드 추가, raw 미노출 ✓ |
| 7. 실제 주문은 아직 연결하지 않음 | `place_order/cancel_order/replace_order` line 237–246 | NotImplementedError + "DO NOT WIRE" 메시지 ✓ |

| 요청 안전 조건 | 결과 |
| --- | --- |
| live trading false | `Settings.live_trading_enabled=False` 기본 + 5+1단 차단 유지 ✓ |
| TRADING_MODE paper | `load_settings`이 비paper에서 `ValueError` ✓ |
| 시장가 주문 금지 | `OrderType.MARKET` 부재 + `ALLOW_MARKET_ORDERS=true` reject ✓ |
| 실주문 전송 금지 | KIS 주문 메서드 전부 NotImplementedError ✓ |
| Strategy가 KIS Adapter 직접 호출 금지 | grep 0건 ✓ |
| OMS 우회 금지 | OMS는 PaperBroker만 사용 ✓ |
| RiskEngine 우회 금지 | mvp-005 OMS 로직 미변경 ✓ |
| secrets 노출 금지 | `Settings.kis_*` `repr=False` + 모든 client `__repr__` 마스킹 + 응답 미노출 ✓ |
| .env Git 추가 금지 | 루트+프로젝트 .gitignore 보호, `git status`에 .env 미등장 ✓ |
| KIS endpoint 추측 금지 | URL/TR ID 코드 0건 (grep 확인) ✓ |

## Missing tests / residual risk

- **테스트 자체는 매우 견고하다.** 74 PASS, 마스킹 본문 검사 명시적, 토큰 상태 머신 만료 케이스 포함, parametrized credentials/account 검증.
- 테스트의 fake 값으로 사용된 계좌번호(`50187996`)는 실제 사용자 계좌번호. Findings #1 참고 — commit 전 치환 권장.
- 실제 KIS Open API 호출이 미구현이라 "정상 응답 처리 / 토큰 expiry 처리 / 네트워크 오류 처리" 같은 실제 통합 테스트는 없음. 이는 의도된 범위(공식 문서 미확인 단계). 다음 mvp에서 추가.
- 호스트 의존성이 venv(`.venv/`)에 설치되어 있어 pytest 실행 환경이 이제 안정. patch.md Remaining TODOs에 해당 명령은 백업 안내로 두면 됨.

## Final checklist (요청 review focus + scope)

- [x] **KIS secrets are not exposed.** Settings field `repr=False`, 모든 client `__repr__` 마스킹, `/paper/status` 응답 미포함, 테스트가 본문 검사로 확정.
- [x] **.env is not added to git.** 루트 + 프로젝트 `.gitignore` 보호 확인. `git status`에 미등장.
- [x] **No KIS endpoint, TR ID, or payload was invented.** grep 0건 (URL, TR ID, endpoint path, appkey/appsecret 키워드).
- [x] **Live trading remains disabled.** mvp-005 5단 차단 + KIS 6단째(`KIS_ENV != "paper"` reject) 모두 유지.
- [x] **Market orders remain disabled.** `OrderType.MARKET` 부재, `ALLOW_MARKET_ORDERS=true` reject 유지.
- [x] **KIS order methods are fail-closed or NotImplemented.** `place_order`/`cancel_order`/`replace_order`/`submit`/`cancel` 모두 `NotImplementedError`.
- [x] **OMS still uses PaperBroker.** `app/api/server.py` line 19–20.
- [x] **/paper/status does not expose secrets.** 응답 텍스트 검사 테스트 통과(`KIS_APP_KEY`/`KIS_APP_SECRET`/`50187996`/`fake-key`/`fake-secret` 미포함).
- [x] **Tests passed.** 74/74 PASS.
- [x] **Scope stayed within mvp-007.** 변경 파일 10개 모두 plan/codex-task의 허용 범위 내. 미수정 파일(mvp-005 도메인/OMS/Risk/Strategy/Runtime, mvp-001..mvp-006, web, prompts, scripts) 그대로.
- [ ] **테스트 코드의 실제 계좌번호를 가짜로 치환 (Findings #1)** — commit 전 사람 액션.
- [ ] **mvp-007 외 dirty GUI 변경 staging 격리 (Findings #2)** — commit 전 사람 액션.

## 사람에게 남기는 액션 아이템

1. **테스트의 실제 계좌번호 치환** (권장, low priority but cleaner):
   ```bash
   cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
   sed -i 's/50187996/12345678/g' tests/test_kis_*.py tests/test_api_paper_status.py
   .venv/bin/python -m pytest -p no:cacheprovider   # 재검증
   ```

2. **commit 시 staging 한정**:
   ```bash
   cd /root/ai-dev-center/projects/ai-team
   git add projects/paper-trading docs/ai/jobs/mvp-006-1 docs/ai/jobs/mvp-007 .gitignore
   git diff --cached --stat   # 검증, mvp-006-1+mvp-007 + paper-trading만 포함되는지
   ```
   mvp-004 dirty + 미정체 GUI 변경(web/server.js +527 등)은 별도 commit으로 분리.

3. **commit/push/merge/deploy는 사람이 직접.** 본 작업은 자동화하지 않는다.

4. (선택, 다음 mvp 후보):
   - mvp-008: KIS HTTP 호출 실제 구현 — KIS 공식 문서에서 endpoint/TR ID/payload 직접 확인 후, OAuth → token 캐싱 → get_account/get_quote 순서로 단계 분리.
   - 또는 Alpaca Paper HTTP 호출 실제 구현.
   - 어느 쪽이든 시작 전 plan/codex-task 작성 + 사용자 명시 승인.
