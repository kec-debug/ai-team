## 1. 요청 요약

mvp-014 + mvp-015 + mvp-016 + mvp-017 4건을 한 번에 묶어 진행한다. 그러나 사용자가 명시한 안전 정책("공식 KIS 문서값이 repo 안에 없거나 확인할 수 없으면 해당 HTTP 기능은 구현하지 않는다")을 적용한 결과, **실제 HTTP 연결 작업(mvp-015/016/017)은 모두 보류**된다. Codex가 본 작업에서 만들 수 있는 것은 mvp-014 산출물(공식 문서값 갭 분석) + 작은 status 보강 + 테스트뿐이다.

### 현재 상태 점검 (verified)

본 세션에서 직접 확인한 결과:

- `pytest -p no:cacheprovider --co` → **126 tests collected** (요청문의 "테스트 126 passed 상태"와 일치).
- 다음 KIS 구조는 이미 구현되어 있음(mvp-007/008/009/10–13에서 누적):
  - `Settings.kis_env`, `kis_account_no(repr=False)`, `kis_app_key(repr=False)`, `kis_app_secret(repr=False)`, `allow_market_orders`, `kill_switch_engaged`, `kis_order_dry_run: bool = True`.
  - `load_settings()`가 `KIS_*` + `KILL_SWITCH_ENGAGED` + `KIS_ORDER_DRY_RUN` 모두 env 로딩.
  - `KisError` 계층(`KisConfigError`, `KisAuthError`, `KisDataUnavailableError`, `KisOrderRejectedError`).
  - `KisAuthClient`, `KisAccountClient`, `KisMarketDataClient` (mvp-007).
  - `KisOrderRequest`(10개 필드, raw account 부재) / `KisOrderResponse`(10개 필드) / `KisDryRunPreview` / `sanitize_kis_response`.
  - `KisHttpClient`(HTTP boundary, `request()` NotImplementedError, HTTP 라이브러리 import 0건).
  - `KisBroker.capabilities()` 6개 키, 모두 False.
  - `validate_kis_order_request` reject 사유: paper/live/market/env/kill_switch/order_type/quantity/limit_price/stale_quote.
  - `KisBroker.place_order`: pre-flight → `_to_kis_request` → `kis_order_dry_run` True이면 `OrderAck(status="dry_run")` 반환, False면 `NotImplementedError`(공식 endpoint 필요 메시지).
  - `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status` 모두 fail-closed.
  - `/paper/status`에 mvp-005~mvp-009 KIS 메타 필드 다수(`broker_type`, `kis_authenticated`, `kis_token_expires_at_masked_or_relative`, `kis_account_loaded`, `kis_positions_loaded`, `kis_cash_balance_loaded`, `kis_market_data_available`, `account_no_masked`, `secret_exposed: False`, `kis_order_entry_*`, `kis_*_available` etc.).
- `.env.example`에 `KIS_ORDER_DRY_RUN=true` 이미 포함.
- 저장소 내 KIS 공식 문서: **없음**. `docs/kis/` 디렉터리 자체 부재. `imports/local-mvp/mvp/app/adapters/brokers/kis.py`는 stub("Do not add guessed endpoint paths or unofficial request fields").
- 본 세션에서 Codex는 외부 웹/공식 문서 접근 불가. 학습 데이터에 KIS Open API endpoint 정보가 있더라도 사용자의 "추측 금지" 정책에 따라 사용 금지.

### 결론

mvp-014–017 통합 작업에서 실제 코드로 연결되는 KIS HTTP는 0건이다. 본 작업의 실질 산출물:

1. **mvp-014 산출물**: `docs/kis/MISSING_OFFICIAL_VALUES.md` 신규 작성 — 사용자가 공식 KIS Open API 문서에서 채워 넣을 수 있는 체크리스트.
2. **/paper/status 작은 보강**: `kis_order_dry_run: bool` 필드 노출(현재 `app/api/routes.py`의 `/paper/status` 응답에 누락. healthcheck에는 들어가 있음).
3. **README 보강**: MISSING_OFFICIAL_VALUES.md 참조 + 본 작업의 의도된 fail-closed 상태 설명.
4. **테스트 추가**: MISSING_OFFICIAL_VALUES.md 파일 존재 + 핵심 섹션 헤더 존재 검증; `/paper/status`에 `kis_order_dry_run` 노출 검증; 모든 KIS HTTP 메서드가 여전히 fail-closed.
5. **patch.md**: mvp-015/016/017 보류 사유와 다음 단계 명확히 정리.

### 핵심 절대 조건

- live trading 활성화 금지. 모든 기존 차단 단(Settings/load_settings/RiskEngine/OMS/`/paper/run`/KisBroker pre-flight) 유지.
- KIS endpoint URL/TR ID/header/payload **절대 추측 금지**. 본 작업에서 코드/문서에 새 URL/TR ID 추가 0건.
- 외부 HTTP 라이브러리(`requests`/`httpx`/`aiohttp`/`urllib3`) `app/broker/kis.py`에 import 금지.
- 실제 KIS app key/secret/account 어떤 파일에도 미포함. `.env.example` placeholder만.
- `MISSING_OFFICIAL_VALUES.md`에도 실제 값 미인용 — 필드 이름/설명/`<TBD>` placeholder만.
- `git commit`/`push`/`merge`/`deploy` 자동화 금지.
- `pip install` 실행 금지.
- mvp-001..mvp-013/현재 paper-trading 코드의 안전 불변식(OrderType MARKET 부재, Strategy 격리, OMS private 등) 모두 유지.

### 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기존 126 + 본 작업 신규 약 6–10개 모두 PASS.

## 2. 작업 범위

### 포함 (In scope)

신규 파일:

- `docs/kis/MISSING_OFFICIAL_VALUES.md` — 공식 KIS 문서값 갭 체크리스트(아래 §4.3 템플릿).
- `projects/paper-trading/tests/test_missing_official_values_doc.py` — `MISSING_OFFICIAL_VALUES.md` 파일 존재 + 필수 섹션 헤더 존재 + 실제 secret 미포함 검증.
- `docs/ai/jobs/mvp-014-017-bundle/patch.md` — Codex 변경 요약.

수정:

- `projects/paper-trading/app/api/routes.py` — `/paper/status` 응답에 `kis_order_dry_run: bool` 한 줄 추가(`settings.kis_order_dry_run` 또는 `kis_health.get("order_dry_run")`에서 산출).
- `projects/paper-trading/tests/test_api_paper_status.py` — `kis_order_dry_run` 필드 assertion 추가(KIS configured / 미configured 양쪽 시나리오).
- `projects/paper-trading/README.md` — "KIS Open API 연결 준비" 섹션 끝에 `## 공식 문서값 진행 상황` 단락 추가(MISSING_OFFICIAL_VALUES.md 참조 + 본 mvp 보류 사유).
- (선택) `projects/paper-trading/tests/test_kis_http_boundaries.py` — `KisHttpClient.request()`가 여전히 NotImplementedError + 외부 HTTP 라이브러리 import 0건을 검증하는 회귀 테스트 추가(이미 비슷한 테스트가 있을 가능성 — 중복이면 추가 안 함).

### 제외 (Out of scope; 절대 만지지 않음)

- **mvp-015 (KIS OAuth HTTP 구현)** — 공식 문서값 부재로 보류. `KisAuthClient.authenticate`/`refresh_token`은 그대로 `NotImplementedError`.
- **mvp-016 (KIS 계좌/시세 HTTP 구현)** — 공식 문서값 부재로 보류. `KisAccountClient.get_account/get_positions/get_cash_balance`, `KisMarketDataClient.get_quote/get_last_price` 모두 그대로 `NotImplementedError`.
- **mvp-017 (KIS 모의투자 주문 HTTP)** — 공식 문서값 부재로 보류. `KisBroker.place_order` dry-run 시 `OrderAck(status="dry_run")`, dry-run=false 시 `NotImplementedError` 그대로. `cancel_order`/`replace_order`/`get_open_orders`/`get_fills`/`get_order_status` 모두 `NotImplementedError` 그대로.
- `app/broker/kis.py`의 어떤 KIS endpoint URL/TR ID/header/payload 추가도 금지.
- `app/broker/kis.py`에 외부 HTTP 라이브러리 import 추가 금지.
- `OrderType`에 MARKET 추가 금지.
- `Settings`, `RiskEngine`, `OMS`, `Strategy`, `PaperRunner`, `PaperBroker`, `AlpacaPaperBroker`, `BrokerAdapter` Protocol 변경 금지.
- mvp-001..mvp-013 산출물 + 본 작업 외 `docs/ai/jobs/` 변경 금지.
- `.env`, secrets, credentials 변경/생성/읽기 금지.
- `app/api/server.py`, `app/main.py`, `app/domain/*`, `app/oms/*`, `app/risk/*`, `app/runtime/*`, `app/strategy/*` 변경 금지.
- `web/`, `prompts/`, `scripts/`, `examples/`, 기존 `docs/`(`docs/kis/` 신규 + 본 mvp job dir 제외) 변경 금지.
- 인증/결제/DB migration/production infra/`.github/workflows/` 변경 금지.
- 자동 commit/push/merge/deploy 신설 금지.
- 임의 shell 명령 입력 UI/API 신설 금지.
- `pip install` 실행 금지.

### 안전 가드

- `docs/kis/MISSING_OFFICIAL_VALUES.md`에 실제 endpoint URL, TR ID, app key, secret, account no 일체 미포함. `<TBD>` placeholder + 필드 이름 + 어디서 찾을지 안내만.
- `/paper/status`의 `kis_order_dry_run` 필드는 `bool`만. 다른 raw 정보 추가 금지.
- README 추가 단락에도 실제 KIS endpoint/TR ID/payload 미포함.

## 3. 수정해야 할 파일

### 신규

| 파일 | 목적 |
| --- | --- |
| `docs/kis/MISSING_OFFICIAL_VALUES.md` | 공식 문서값 갭 체크리스트(4개 섹션) |
| `projects/paper-trading/tests/test_missing_official_values_doc.py` | 문서 파일 검증 |
| `docs/ai/jobs/mvp-014-017-bundle/patch.md` | Codex 변경 요약 |

### 수정

| 파일 | 변경 내용 |
| --- | --- |
| `projects/paper-trading/app/api/routes.py` | `/paper/status` 응답에 `"kis_order_dry_run": bool(...)` 한 줄 추가 |
| `projects/paper-trading/tests/test_api_paper_status.py` | `kis_order_dry_run` 필드 assertion 추가(양 시나리오) |
| `projects/paper-trading/README.md` | 공식 문서값 진행 상황 단락 추가 |

### 절대 미수정

- `projects/paper-trading/app/broker/kis.py` (KIS endpoint/TR ID/payload 추가 금지, HTTP 라이브러리 import 금지, 기존 fail-closed 동작 유지)
- `projects/paper-trading/app/config.py`
- `projects/paper-trading/app/risk/`, `app/oms/`, `app/runtime/`, `app/strategy/`, `app/domain/`
- `projects/paper-trading/app/broker/{base,paper,alpaca_paper}.py`
- `projects/paper-trading/app/api/server.py`
- `projects/paper-trading/app/main.py`
- `projects/paper-trading/.env.example` (이미 `KIS_ORDER_DRY_RUN=true` 포함)
- 루트 `.gitignore`, 프로젝트 `.gitignore`
- 기존 테스트 파일(`test_alpaca_paper_stub.py`, `test_broker_interface.py`, `test_config.py`, `test_flow.py`, `test_kill_switch.py`, `test_kis_*`(`test_api_paper_status.py` 외), `test_models.py`, `test_oms.py`, `test_paper_broker.py`, `test_paper_runner.py`, `test_risk_engine.py`, `test_strategy_premarket_gap.py`)
- `imports/local-mvp/`(reference stub, 본 작업과 무관)
- mvp-001..mvp-013 산출물

## 4. Codex 구현 지시문

### 4.1 사전 점검

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m pytest -p no:cacheprovider --co -q 2>&1 | tail -3
# expect: "126 tests collected" (or higher)

grep -q "kis_order_dry_run" app/config.py && echo "OK config.kis_order_dry_run"
grep -q "class KisHttpClient" app/broker/kis.py && echo "OK KisHttpClient"
grep -q "sanitize_kis_response" app/broker/kis.py && echo "OK sanitize_kis_response"
grep -q "KisOrderRejectedError" app/broker/kis.py && echo "OK KisOrderRejectedError"
grep -q "KIS_ORDER_DRY_RUN" .env.example && echo "OK .env.example dry_run"

test -d ../docs/kis && echo "WARN: docs/kis already exists" || echo "OK docs/kis absent (will be created)"
```

기대: 모두 OK. 누락이 있으면 mvp-009 이전 단계가 빠진 것 — 작업을 중단하고 `patch.md` Remaining TODOs에 명시.

### 4.2 `docs/kis/MISSING_OFFICIAL_VALUES.md` (신규)

다음 구조로 만든다. **실제 endpoint, TR ID, header 값, payload 형식 일체 미포함.** 필드 이름과 placeholder(`<TBD>`)만.

```markdown
# KIS Open API — Missing Official Values

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

→ 충족 시 후속 mvp가 `KisAuthClient.authenticate()` / `refresh_token()`을 실제 HTTP로 연결합니다.

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

→ 충족 시 후속 mvp가 `KisAccountClient.get_account()` / `get_positions()` / `get_cash_balance()`를 실제 HTTP로 연결합니다.

## 3. 해외주식/미국주식 시세

| 항목 | 설명 | 값 | Confirmed |
| --- | --- | --- | --- |
| 해외주식 현재가 endpoint | path | `<TBD>` | no |
| 해외주식 현재가 TR ID | 모의투자용 TR ID(시세는 실전과 공유될 수 있음 — 공식 문서 확인 필요) | `<TBD>` | no |
| Request fields | 종목코드, 거래소 코드 등 | `<TBD>` | no |
| Response bid/ask/last 필드 | `<TBD>` | `<TBD>` | no |
| Response quote timestamp 필드 | `<TBD>` | `<TBD>` | no |
| Stale quote 판단 기준 | 초/밀리초 등 단위 | `<TBD>` | no |

→ 충족 시 후속 mvp가 `KisMarketDataClient.get_quote()` / `get_last_price()`를 실제 HTTP로 연결합니다.

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

→ 모든 항목 충족 시 후속 mvp가 `KisBroker.place_order` / `cancel_order` / `replace_order` / `get_open_orders` / `get_fills` / `get_order_status`를 단계적으로 실제 HTTP로 연결합니다. 그 단계에서도 `KIS_ORDER_DRY_RUN=true` 기본값과 `validate_kis_order_request` pre-flight는 유지됩니다.

## 다음 작업 가이드

1. 사용자가 KIS Open API 공식 개발자 포털(또는 신뢰 가능한 KIS 공식 문서)에서 위 `<TBD>` 항목을 직접 확인합니다.
2. 항목별로 `Confirmed: yes`로 변경하고 값을 채워 넣습니다.
3. `Confirmed: yes` 항목만 별도 mvp에서 `app/broker/kis.py`에 HTTP로 연결합니다.
4. 본 저장소는 사용자가 확인하지 않은 값은 절대 사용하지 않습니다.

## 보안

- 실제 app key, app secret, 계좌번호, access token, refresh token은 이 문서에 절대 기록하지 않습니다. 모두 `.env`(gitignored)에만 둡니다.
- 본 문서가 커밋된 형태로 git에 들어가도 자격증명 누출이 없도록 합니다.
```

### 4.3 `app/api/routes.py` 변경

`/paper/status` 응답 dict에 한 줄 추가(필드 순서는 `kill_switch_engaged` 부근):

```python
"kis_order_dry_run": bool(settings.kis_order_dry_run),
```

기존 응답 필드(20+개) 모두 그대로 유지. 다른 KIS-관련 raw 정보 추가 금지.

### 4.4 `projects/paper-trading/README.md`

KIS 섹션 뒤(또는 적절한 위치)에 다음 단락 추가:

```markdown
## 공식 KIS 문서값 진행 상황 (mvp-014)

KIS Open API 모의투자 HTTP 연결을 구현하기 위해 필요한 공식 문서값의 갭은 [`docs/kis/MISSING_OFFICIAL_VALUES.md`](../../docs/kis/MISSING_OFFICIAL_VALUES.md)에 정리되어 있습니다.

본 저장소는 endpoint URL, TR ID, header, payload를 추측하지 않습니다. `MISSING_OFFICIAL_VALUES.md`의 항목이 사용자에 의해 `Confirmed: yes`로 변경되기 전까지 다음 KIS HTTP 기능은 모두 `NotImplementedError` 또는 dry-run 상태로 유지됩니다.

- OAuth 인증, 토큰 갱신
- 해외주식 잔고/포지션/현금 조회
- 해외주식 시세 조회
- 모의투자 지정가 주문, 취소, 정정
- 미체결/체결/주문 상태 조회

기본값 `KIS_ORDER_DRY_RUN=true`가 유지되는 한 KIS 주문 메서드는 HTTP를 전송하지 않으며, dry-run preview를 반환합니다(또는 NotImplementedError로 fail-closed). `/paper/status`에서 `kis_order_dry_run: true` 필드로 확인할 수 있습니다.
```

기존 단락은 변경 없음.

### 4.5 `tests/test_missing_official_values_doc.py` (신규)

```python
"""mvp-014: verify the official-values gap document exists and is safe."""
import pathlib


DOC_PATH = pathlib.Path(__file__).resolve().parents[2] / "docs" / "kis" / "MISSING_OFFICIAL_VALUES.md"


def test_missing_official_values_file_exists():
    assert DOC_PATH.is_file(), f"expected {DOC_PATH} to exist"


def test_missing_official_values_has_required_sections():
    text = DOC_PATH.read_text(encoding="utf-8")
    for header in (
        "OAuth",
        "해외주식",
        "모의투자 주문",
        "Confirmed",
    ):
        assert header in text, f"missing required marker: {header}"


def test_missing_official_values_does_not_leak_real_secrets():
    text = DOC_PATH.read_text(encoding="utf-8")
    # Reject patterns that look like real KIS app keys / account numbers.
    for forbidden in ("PSNFD", "PKID", "AKIA", "sk-", "ghp_"):
        assert forbidden not in text, f"forbidden token found: {forbidden}"
    # Should clearly mark values as TBD/not confirmed.
    assert "<TBD>" in text
    assert "Confirmed: yes" not in text  # all entries must remain unconfirmed in repo
```

### 4.6 `tests/test_api_paper_status.py` 보정

기존 두 시나리오(`test_paper_status_kis_metadata_fields` / `test_paper_status_with_kis_config_masks_account`)에 추가:

```python
assert "kis_order_dry_run" in body
assert body["kis_order_dry_run"] is True
```

(`settings.kis_order_dry_run` 기본값 True이므로 양 시나리오 모두 True여야 함.)

### 4.7 검증 명령

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기대: 종료코드 0. 기존 126 + 신규 5(test_missing_official_values_doc 3 + test_api_paper_status_kis_metadata_dry_run 2) ≈ 131 PASS.

저장소 루트:

```bash
git diff --stat
git status --short
```

### 4.8 `docs/ai/jobs/mvp-014-017-bundle/patch.md`

```markdown
## 1. Files Changed
- docs/kis/MISSING_OFFICIAL_VALUES.md (신규)
- projects/paper-trading/app/api/routes.py
- projects/paper-trading/README.md
- projects/paper-trading/tests/test_missing_official_values_doc.py (신규)
- projects/paper-trading/tests/test_api_paper_status.py
- docs/ai/jobs/mvp-014-017-bundle/patch.md (신규)

## 2. Implementation Summary

### 2.1 mvp-014 — KIS 공식 문서값 갭 정리
- docs/kis/MISSING_OFFICIAL_VALUES.md 신규. 4개 섹션(OAuth/계좌/시세/주문)에 30+ 필드.
- 모든 항목 `<TBD>` + `Confirmed: no`. 실제 endpoint/TR ID/payload/key/secret 일체 미포함.

### 2.2 mvp-015 — KIS OAuth HTTP — **보류**
- 공식 KIS Open API 문서값 부재로 실제 HTTP 연결 보류.
- KisAuthClient.authenticate / refresh_token 기존 NotImplementedError 유지.
- 본 작업에서 endpoint URL, TR ID, payload 추가 0건.

### 2.3 mvp-016 — KIS 계좌/시세 HTTP — **보류**
- 공식 KIS Open API 문서값 부재로 실제 HTTP 연결 보류.
- KisAccountClient / KisMarketDataClient 모든 메서드 기존 NotImplementedError 유지.

### 2.4 mvp-017 — KIS 모의투자 주문 HTTP — **보류**
- 공식 KIS Open API 문서값 부재로 실제 HTTP 연결 보류.
- KisBroker.place_order는 KIS_ORDER_DRY_RUN=true 기본값에서 dry-run preview 반환(기존 동작), false에서 NotImplementedError(기존 동작).
- cancel/replace/get_open_orders/get_fills/get_order_status 모두 NotImplementedError 유지.

### 2.5 /paper/status 보강
- `kis_order_dry_run: bool` 필드 신설. settings.kis_order_dry_run을 그대로 노출.
- 기타 raw KIS 정보 추가 없음.

### 2.6 테스트
- compileall: PASS
- pytest 126(기존) + 5(신규) = 131 PASS
- 신규: MISSING_OFFICIAL_VALUES.md 존재/섹션/no-real-secrets + /paper/status kis_order_dry_run

### 2.7 공식 KIS 문서값 부족으로 실제 HTTP 연결 보류

본 작업은 사용자의 안전 정책("공식 KIS 문서값이 repo 안에 없거나 확인할 수 없으면 해당 HTTP 기능은 구현하지 않는다")을 적용한 결과입니다. Codex는 외부 웹/공식 문서 접근이 없으며, 본 저장소 내부에도 KIS 공식 endpoint/TR ID/payload 정보가 없습니다(`imports/local-mvp/.../kis.py`는 stub 클래스, 실제 값 없음).

다음 단계 안내(MISSING_OFFICIAL_VALUES.md 참고):
1. 사용자가 KIS Open API 공식 개발자 포털에서 30+ 필드 값을 직접 확인 후 docs/kis/MISSING_OFFICIAL_VALUES.md에 채워 넣습니다.
2. `Confirmed: yes`로 표시된 항목에 한해 별도 mvp에서 HTTP 연결을 진행합니다.
3. 그 단계에서도 KIS_ORDER_DRY_RUN=true 기본값과 validate_kis_order_request pre-flight는 유지됩니다.

### 2.8 다음 mvp 후보
- mvp-018: docs/kis/MISSING_OFFICIAL_VALUES.md의 OAuth 섹션 Confirmed 후 KisAuthClient HTTP 연결.
- 또는 워크트리 GUI dirty 정리(별도 cleanup mvp).
- 또는 Alpaca Paper HTTP 실제 구현.

## 3. Safety Confirmation
- KIS endpoint/TR ID/payload 추측 0건.
- 외부 HTTP 라이브러리 import 0건(`app/broker/kis.py` 변경 없음).
- 실제 KIS key/secret/account 값 코드/문서/.env.example/응답/log/patch 미노출.
- MISSING_OFFICIAL_VALUES.md에 `<TBD>` placeholder만, 실제 값 없음.
- OrderType MARKET 부재 유지.
- live trading 차단 단 모두 유지.
- Strategy 패키지가 KIS import 0건 유지.
- OMS는 PaperBroker만 사용.
- /paper/status raw credentials 미노출.
- .env staged/committed 없음.
- commit/push/merge/deploy 자동화 없음.

## 4. Test Results
- compileall: PASS
- pytest: <pytest 출력>

## 5. Remaining TODOs
- 사용자가 KIS 공식 문서에서 MISSING_OFFICIAL_VALUES.md의 `<TBD>` 항목 확인 + Confirmed: yes로 변경.
- 그 후 별도 mvp(예: mvp-018+)에서 단계적으로 HTTP 연결.
- 워크트리에 mvp-008/009/10–13 외 dirty가 있다면 별도 cleanup mvp.

## Verdict
READY FOR REVIEW
```

## 5. 테스트 기준

1. `.venv/bin/python -m compileall app tests` 종료코드 0.
2. `.venv/bin/python -m pytest -p no:cacheprovider` 종료코드 0, 기존 126 + 신규 5 ≈ 131 PASS.
3. `docs/kis/MISSING_OFFICIAL_VALUES.md` 파일 존재 + OAuth/해외주식/모의투자 주문/Confirmed 섹션 헤더 존재 + `<TBD>` 등장 + `Confirmed: yes` 부재.
4. `grep -RIn "OrderType\.MARKET" projects/paper-trading/app` 0건 유지.
5. `grep -RIn "https?://" projects/paper-trading/app/broker/kis.py` 0건 유지.
6. `grep -RInE "import requests|import httpx|import aiohttp|import urllib" projects/paper-trading/app/broker/kis.py` 0건 유지.
7. `grep -RIn "TR_ID|tr_id|/uapi/|/oauth2/" projects/paper-trading/app/broker/kis.py docs/kis/MISSING_OFFICIAL_VALUES.md` 0건 (placeholder도 미포함; 필드 이름은 `Required` 같은 영문 설명으로 표기, 실제 path 형태 미포함).
8. `grep -RIn "PSNFD\|PKID\|AKIA\|sk-\|ghp_" projects/paper-trading/ docs/kis/` 0건.
9. `/paper/status` 응답에 `kis_order_dry_run: true` 포함, 기존 mvp-005~mvp-013 필드 모두 보존.
10. `git diff --stat`에 본 작업 외 변경 없음.
11. `.env` staged/committed 없음.

## 6. 리뷰 체크리스트

- [ ] `docs/kis/MISSING_OFFICIAL_VALUES.md` 신규 작성, 4섹션 × 필드 30+, 모두 `<TBD>`/`Confirmed: no`.
- [ ] MISSING_OFFICIAL_VALUES.md에 실제 endpoint URL/TR ID/path/payload format 0건.
- [ ] MISSING_OFFICIAL_VALUES.md에 실제 KIS app key/secret/account 0건.
- [ ] `app/api/routes.py`의 `/paper/status` 응답에 `kis_order_dry_run: bool` 추가, 기존 필드 모두 보존.
- [ ] `app/broker/kis.py` 미변경 (HTTP 미추가, 외부 라이브러리 import 미추가).
- [ ] `app/config.py` 미변경 (KIS_ORDER_DRY_RUN은 이미 mvp-009 이전에 land됨).
- [ ] `.env.example` 미변경 (KIS_ORDER_DRY_RUN=true는 이미 포함).
- [ ] README에 공식 문서값 진행 상황 단락 추가, MISSING_OFFICIAL_VALUES.md 참조.
- [ ] `tests/test_missing_official_values_doc.py` 3개 테스트 PASS(존재/섹션/no-real-secrets).
- [ ] `tests/test_api_paper_status.py`에 `kis_order_dry_run` assertion 추가, 양 시나리오 PASS.
- [ ] 기존 126 테스트 회귀 없음.
- [ ] 외부 HTTP 라이브러리 import 0건(grep 확인).
- [ ] KIS endpoint URL/TR ID 코드 0건(grep 확인).
- [ ] Strategy 패키지가 `app.broker.kis*` import 0건.
- [ ] `OrderType`에 MARKET 부재.
- [ ] `app/domain/`, `app/broker/{base,paper,alpaca_paper}.py`, `app/oms/`, `app/risk/`, `app/runtime/`, `app/strategy/`, `app/api/server.py`, `app/main.py` 미변경.
- [ ] mvp-001..mvp-013 산출물, `web/`, `prompts/`, `scripts/`, 기존 `docs/`(docs/kis/ + mvp-014-017-bundle 외) 미변경.
- [ ] `.env` staged/committed 없음.
- [ ] commit/push/merge/deploy 자동화 없음.
- [ ] `patch.md` 5섹션 + Implementation Summary 8단락 완성. 보류 사유 명확.
