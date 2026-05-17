# Codex Task — mvp-023: Quote 도메인 모델 + KIS quote mapper skeleton + MISSING_MARKET_DATA_VALUES catalog

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-023/plan.md` and `docs/ai/jobs/mvp-023/request.ko.md` first.
>
> **중요**: 본 작업은 mvp-007/008 KIS HTTP 시도와 같은 패턴을 반복하지 않는다. 저장소에 KIS 공식 endpoint/TR ID/payload 정보가 없으므로 실제 HTTP 코드 추가 금지. 대신 broker-agnostic `Quote` 도메인 모델 + 매퍼 skeleton(`NotImplementedError`) + `docs/kis/MISSING_MARKET_DATA_VALUES.md` catalog만 만든다.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-023`
- 대상: `projects/paper-trading/app/domain/quote.py` (신규) + `app/broker/kis_quote_mapper.py` (신규) + `docs/kis/MISSING_MARKET_DATA_VALUES.md` (신규) + 테스트 3개 신규 + 회귀 테스트 1개 추가 + README 단락 + patch.md.
- 핵심: Quote 모델은 broker-agnostic. mapper는 fail-closed. KIS endpoint는 추측 금지.

## 사전 점검 (Codex 첫 단계)

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m pytest -p no:cacheprovider --co -q 2>&1 | tail -3
# expect: 193+ tests collected

grep -q "class KisMarketDataClient" app/broker/kis.py && echo "OK KisMarketDataClient"
grep -q "class KisHttpClient" app/broker/kis.py && echo "OK KisHttpClient"
grep -q "_project_dir" app/config.py && echo "OK mvp-022 .env auto-load"
test -f ../../docs/kis/MISSING_OFFICIAL_VALUES.md && echo "OK MISSING_OFFICIAL_VALUES.md"
test -d .venv && echo "OK venv"
```

위 5개 OK → 진행.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, KIS app key/secret/account/token 변경/생성/읽기/노출 금지.
- 외부 HTTP 라이브러리(`requests`, `httpx`, `aiohttp`, `urllib3` 등) 어떤 파일에도 import 금지.
- 실주문 코드, 실제 KIS HTTP 호출 코드 신설 금지.
- **KIS endpoint URL, path, TR ID, header 값, payload 형식, response 필드 이름을 어떤 파일에도 추가하지 마.** `MISSING_MARKET_DATA_VALUES.md` 포함. `<TBD>` placeholder만.
- `app/broker/kis.py` 본문 변경 금지. 새 helper 파일(`kis_quote_mapper.py`)로 분리.
- `KisMarketDataClient.get_quote` 동작 변경 금지 — 여전히 `NotImplementedError`.
- live trading 활성화 금지. 시장가 주문 허용 금지. `OrderType.MARKET` 추가 금지.
- RiskEngine/OMS 우회 코드 경로 신설 금지.
- Strategy 패키지가 `app.broker.kis*` import 금지(기존 상태 유지).
- 임의 shell 명령 입력 UI/API 신설 금지.
- 본 작업 범위 외 파일 변경 금지. mvp-001..mvp-022 산출물 미변경.
- `pip install` 실행 금지.
- `app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/static/*` 변경 금지.
- `app/oms/`, `app/risk/`, `app/strategy/`, `app/runtime/`, `app/portfolio/`, `app/session/`, `app/reports/` 변경 금지.
- `app/domain/{enums.py,orders.py,market.py}` 변경 금지(`Quote`는 신규 파일 `quote.py`로만 추가).
- `app/config.py`, `Settings` 변경 금지. 새 env 변수 추가 금지.
- `.env`, `.env.example`, 프로젝트 `.gitignore`, 루트 `.gitignore` 변경 금지.

## 수정 허용 위치

### 신규

- `projects/paper-trading/app/domain/quote.py`
- `projects/paper-trading/app/broker/kis_quote_mapper.py`
- `docs/kis/MISSING_MARKET_DATA_VALUES.md`
- `projects/paper-trading/tests/test_quote_model.py`
- `projects/paper-trading/tests/test_kis_quote_mapper.py`
- `projects/paper-trading/tests/test_missing_market_data_values_doc.py`
- `docs/ai/jobs/mvp-023/patch.md`

### 수정 가능

- `projects/paper-trading/tests/test_kis_market_data_client.py` (회귀 테스트 1개 추가만, 기존 테스트 변경 없음)
- `projects/paper-trading/README.md` (mvp-023 단락 추가, 기존 단락 변경 없음)

### 절대 미수정

- `projects/paper-trading/app/broker/kis.py` (본문 변경 금지)
- `projects/paper-trading/app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/static/*`
- `projects/paper-trading/app/config.py`, `app/domain/{enums,orders,market}.py`
- `projects/paper-trading/app/broker/{base,paper,alpaca_paper}.py`
- `projects/paper-trading/app/oms/`, `app/risk/`, `app/strategy/`, `app/runtime/`, `app/portfolio/`, `app/session/`, `app/reports/`
- `.env`, `.env.example`, 프로젝트 `.gitignore`, 루트 `.gitignore`
- mvp-001..mvp-022 산출물
- `scripts/`(mvp-020), `imports/`, `web/`, `prompts/`, 기존 `docs/`(`docs/ai/jobs/mvp-023/` + `docs/kis/MISSING_MARKET_DATA_VALUES.md` 외)
- 기존 테스트 중 본 작업이 다루지 않는 것

## 구현 작업

`plan.md` §4 코드를 그대로 따른다. 다음은 빠뜨리기 쉬운 항목.

### 1) `app/domain/quote.py` (신규)

`plan.md` §4.2 코드 그대로. 핵심 불변식:

- import: `dataclasses.dataclass`, `datetime`, `decimal.Decimal`만. `app.config`, `app.broker.*`, 외부 HTTP 라이브러리 import 0건.
- `@dataclass(frozen=True)` — 외부 수정 불가.
- `__post_init__`이 모든 invariant 검증(uppercase, 양수, ask>=bid, timezone-aware, non-empty source).
- `spread_pct` property는 `Decimal` 반환.
- `is_stale(now, max_age_seconds)` — naive `now`는 거절.

### 2) `app/broker/kis_quote_mapper.py` (신규)

`plan.md` §4.3 코드 그대로. 핵심:

- import: `datetime`, `typing`, `app.domain.quote.Quote`만.
- `app.broker.kis` 모듈 import 0건(매퍼는 broker-agnostic; KIS broker 클래스에 의존하지 않음).
- 외부 HTTP 라이브러리 import 0건.
- `kis_raw_quote_to_domain(raw, symbol, source="kis_paper") -> Quote`:
  - `raw is None` → `ValueError`.
  - `not symbol` → `ValueError`.
  - 그 외 → `NotImplementedError`(메시지에 "official documentation" 포함).

### 3) `docs/kis/MISSING_MARKET_DATA_VALUES.md` (신규)

`plan.md` §4.4의 마크다운 템플릿 그대로. 핵심:

- 4개 섹션(현재가 endpoint / Quote 응답 매핑 / 호가단위·거래소 시간 / 시세 종류·권한).
- 모든 값 `<TBD>`, 모든 Confirmed `no`.
- 실제 endpoint URL/TR ID/path/key/secret 0건.
- `MISSING_OFFICIAL_VALUES.md`와 cross-reference.

### 4) 테스트 (`plan.md` §4.5)

#### `tests/test_quote_model.py` (신규)

12개 테스트 — happy path / 7개 invariant 거절 / spread_pct / is_stale 2개 / naive now 거절 / frozen 검증.

#### `tests/test_kis_quote_mapper.py` (신규)

3개 테스트 — valid input에 NotImplementedError / None raw 거절 / 빈 symbol 거절.

#### `tests/test_missing_market_data_values_doc.py` (신규)

4개 테스트 — 파일 존재 / 필수 marker 존재(현재가, Quote, 응답 필드, 호가단위, Confirmed, `<TBD>`) / `Confirmed: yes` 부재 / 실 키 prefix 부재.

#### `tests/test_kis_market_data_client.py` 보정 (1개 추가)

기존 테스트 모두 유지. 다음 하나 추가:

```python
def test_kis_get_quote_still_fail_closed_after_mvp023(settings):
    s = replace(settings, kis_env="paper", kis_account_no="x",
                kis_app_key="k", kis_app_secret="s")
    md = KisMarketDataClient(s, KisAuthClient(s))
    with pytest.raises(NotImplementedError, match="official documentation"):
        md.get_quote("AAPL")
```

(import는 기존 파일과 일치. `replace`, `KisMarketDataClient`, `KisAuthClient`, `pytest` 등 이미 사용 중.)

### 5) README 변경

`plan.md` §4.6의 "## KIS 시세 조회 준비 (mvp-023)" 단락을 mvp-022 단락 뒤에 추가. 기존 단락 변경 없음.

### 6) 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

저장소 루트:

```bash
git diff --stat
git status --short
```

기대: 기존 193± + 신규 ~20 ≈ 213 PASS. compileall exit 0. mvp-023 외 변경 없음.

### 7) `docs/ai/jobs/mvp-023/patch.md`

`plan.md` §4.8 템플릿 그대로 채운다. 실제 KIS 값 미인용. Implementation Summary 8단락 모두 채움.

## 완료 정의 (Done)

- `app/domain/quote.py` 신규 — frozen dataclass, broker-agnostic, app.config/app.broker import 0건, 외부 HTTP 라이브러리 import 0건.
- `app/broker/kis_quote_mapper.py` 신규 — NotImplementedError + 입력 검증, app.broker.kis import 0건, HTTP 라이브러리 import 0건.
- `docs/kis/MISSING_MARKET_DATA_VALUES.md` 신규 — 4섹션 × 다수 `<TBD>` × 모두 `Confirmed: no`. 실제 endpoint/TR ID/key/secret 0건.
- `Quote` invariants 12개 테스트 PASS.
- `kis_quote_mapper` fail-closed 3개 테스트 PASS.
- 문서 검증 4개 테스트 PASS.
- `test_kis_market_data_client.py`에 회귀 테스트 1개 추가, PASS.
- 기존 193± 회귀 0건.
- `app/broker/kis.py` 본문 변경 0건.
- `app/api/server.py`/`routes.py`, `app/main.py`, `app/config.py`, `app/domain/{enums,orders,market}.py`, `app/broker/{base,paper,alpaca_paper}.py`, `app/oms/`, `app/risk/`, `app/strategy/`, `app/runtime/`, `app/portfolio/`, `app/session/`, `app/reports/`, `app/static/` 변경 0건.
- `.env`, `.env.example`, 프로젝트/루트 `.gitignore` 변경 0건.
- mvp-001..mvp-022 산출물 미변경.
- `OrderType.MARKET` 부재 유지.
- 외부 HTTP 라이브러리 import 0건 전저장소.
- KIS endpoint URL/TR ID 코드/문서 0건 추가.
- `git diff --stat`에 mvp-023 외 변경 없음.
- `.env` staged/committed 없음.
- `patch.md` 5섹션 + Implementation Summary 8단락 완성, 보류 사유 명확.
- commit/push/merge/deploy 자동화 없음.
