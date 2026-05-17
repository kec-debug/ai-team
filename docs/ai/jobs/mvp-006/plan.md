## 1. 요청 요약

`projects/paper-trading/`에 KIS(한국투자증권) 모의투자 broker adapter **stub**과 그것을 지탱하는 설정·메타 응답·테스트를 추가한다. 새 전략은 추가하지 않는다. 실제 KIS Open API HTTP 호출은 본 작업이 아닌 후속 mvp에서 구현한다.

핵심 절대 조건(요청 + `prompts/claude.md` + mvp-005 안전 불변식):

- live trading 코드 경로/플래그 활성화 금지. 5단 차단(`Settings` 기본 False / `load_settings` env 차단 / `RiskEngine` reject / `OMS.place` 차단 / `POST /paper/run` 503) 그대로 유지.
- 시장가(market) 주문 금지. `OrderType`에 MARKET 멤버 추가 금지.
- `OMS.place`만 broker.submit 호출. RiskEngine 우회 경로 없음.
- Strategy 패키지가 `app.oms`, `app.risk`, `app.broker` import 금지(grep 0건 유지).
- KIS endpoint URL 코드 하드코딩 금지. `.env`에서만 로드. 미설정/형식 오류 → `RuntimeError` (fail closed).
- API key/secret 코드 하드코딩 금지. `.env.example`은 placeholder만.
- `/paper/status` 응답에 credentials 노출 금지(class name과 mode만).
- `git commit`/`push`/`merge`/`deploy` 자동화 금지.
- 신규 의존성 추가 없음. `pip install` 실행 금지.

검증:

```bash
# projects/paper-trading 내에서
python -m compileall app tests
python -m pytest -p no:cacheprovider
# 저장소 루트에서
git diff --stat
git status --short
```

mvp-005 기존 테스트(19개)가 그대로 통과해야 한다. 신규 KIS 테스트는 추가분.

## 2. 작업 범위

### 포함 (In scope)

`projects/paper-trading/` 아래:

- 신규 `app/broker/kis_paper.py` — `KisPaperBroker` (Phase 1 stub, network NotImplementedError).
- 수정 `app/config.py` — `Settings`에 KIS 필드 4개 추가, `load_settings()`가 env에서 로드(누락 시 `None`). 파일 로드 단계에서 KIS 키 검증을 강제하지 않는다.
- 신규 `app/domain/krx_session.py` — `kst_session_for(ts: datetime) -> Session` helper (KRX 시간 → Session 매핑). 본 작업의 어떤 모듈도 호출하지 않는 future hook.
- 수정 `app/api/server.py` — `KisPaperBroker(settings)` 인스턴스화를 try/except로 시도하여 `app.state.configured_brokers`에 등록(성공 시만). 활성 broker는 `PaperBroker` 그대로.
- 수정 `app/api/routes.py` — `/paper/status` 응답에 `brokers` 객체 추가. credentials/URL 미노출.
- 수정 `.env.example` — `KIS_PAPER_API_BASE`, `KIS_PAPER_APP_KEY`, `KIS_PAPER_APP_SECRET`, `KIS_PAPER_ACCOUNT` placeholder 4줄 추가. URL 주석: "KIS Open API 공식 paper trading base URL을 사용자가 .env에 적습니다. 이 저장소는 URL을 추측하지 않습니다."
- 신규 `tests/test_kis_paper_stub.py` — KIS adapter fail-closed/NotImplementedError 검증.
- 신규 `tests/test_krx_session.py` — KRX 시간 helper 매핑 검증(작음).
- 수정 `tests/test_api_paper_status.py` — `brokers` 필드 존재/모양 assertion 추가. credentials 미노출 검증.
- (필요 시) 수정 `tests/conftest.py` — KIS env helper fixture.
- 수정 `docs/ai/jobs/mvp-006/patch.md` — Codex 변경 요약.

기존 파일 변경은 위 5개(`config.py`, `server.py`, `routes.py`, `.env.example`, `test_api_paper_status.py`) + conftest 한정. **`app/oms/`, `app/risk/`, `app/strategy/`, `app/domain/enums.py`, `app/domain/orders.py`, `app/domain/market.py`, `app/runtime/paper_runner.py`, `app/broker/base.py`, `app/broker/paper.py`, `app/broker/alpaca_paper.py`는 손대지 않는다.**

### 제외 (Out of scope; 절대 만지지 않음)

- 실제 KIS HTTP 호출(인증, 주문, 잔고, 호가 등).
- KRX 한국 종목용 새 전략. `app/strategy/` 미수정.
- 매매 전략 변경, 시장 데이터 연결.
- live trading 활성화. `Settings.live_trading_enabled` 기본 False 그대로.
- 실계좌(KIS 실전투자) 어댑터.
- mvp-005의 OMS/RiskEngine/PaperBroker/AlpacaPaperBroker/Strategy/PaperRunner 로직.
- `OrderType` enum 변경(특히 MARKET 추가 금지).
- `web/`, `prompts/`, `scripts/`, `examples/`, `docs/` (mvp-006 job dir 제외), `docs/ai/jobs/mvp-001..mvp-005/` 변경.
- `.env`, secrets, credentials.
- auth, payment, DB migration, production infra, `.github/workflows/`.
- `git commit`, `git push`, PR 생성/머지, 배포 자동화.
- 임의 shell 실행 기능.
- `pip install` 실행.

### 안전 가드

- 모든 신규 파일은 `projects/paper-trading/` 아래에만.
- `KisPaperBroker`는 `submit`/`cancel`/`open_orders`/`positions` 어디에서도 실제 네트워크 호출을 시도하지 않는다. 모두 `NotImplementedError`.
- `KisPaperBroker.__init__`에서 `https://`로 시작하지 않거나 credentials/account가 비어있으면 `RuntimeError`(fail closed).
- `/paper/status`의 `brokers` 응답에는 **class name과 mode만** 포함. URL, key, secret, account number 일체 미노출.
- `app/api/server.py`의 KIS 인스턴스화 try/except는 **broad** 예외 catch(`Exception`) 하지 않는다. `RuntimeError`만 catch — 그 외 예외(예: ImportError)는 propagate.

## 3. 수정해야 할 파일

### 신규

| 파일 | 목적 |
| --- | --- |
| `app/broker/kis_paper.py` | `KisPaperBroker` stub |
| `app/domain/krx_session.py` | KRX 시간→Session helper (future hook) |
| `tests/test_kis_paper_stub.py` | adapter fail-closed/NotImplementedError 검증 |
| `tests/test_krx_session.py` | KRX 시간 매핑 검증 |
| `docs/ai/jobs/mvp-006/patch.md` | Codex 변경 요약 |

### 수정

| 파일 | 변경 내용 |
| --- | --- |
| `app/config.py` | `Settings`에 KIS 4필드 추가, `load_settings()`에서 env 로드, validator는 broker `__init__`로 위임 |
| `app/api/server.py` | KIS 인스턴스화 시도 → `app.state.configured_brokers`에 등록 |
| `app/api/routes.py` | `/paper/status`에 `brokers` 객체 추가 |
| `.env.example` | KIS_PAPER_* placeholder 4줄 추가 |
| `tests/test_api_paper_status.py` | `brokers` 필드 모양 + credentials 미노출 assertion 추가 |
| `tests/conftest.py` | (필요 시) KIS env helper fixture |

## 4. Codex 구현 지시문

### 4.1 사전 조건

- 작업 루트: `/root/ai-dev-center/projects/ai-team`. 신규 코드는 `projects/paper-trading/` 안에만.
- mvp-005 산출물(`app/strategy/`, `app/oms/`, `app/risk/`, `app/broker/{base.py,paper.py,alpaca_paper.py}`, `app/domain/{enums.py,orders.py,market.py}`, `app/runtime/`, 기존 테스트)은 수정 금지.
- `git commit`/`push`/`merge`/`deploy` 절대 금지. `.env`, secrets, credentials 절대 만지지 않는다.
- `pip install` 실행 금지(호스트 의존성 미설치는 patch.md Remaining TODOs).

### 4.2 `app/broker/kis_paper.py` (신규)

```python
from app.config import Settings
from app.domain.enums import TradingMode
from app.domain.orders import BrokerOrder, OrderAck


class KisPaperBroker:
    mode = TradingMode.PAPER

    def __init__(self, settings: Settings) -> None:
        base = settings.kis_paper_api_base
        if not base or not base.startswith("https://"):
            raise RuntimeError("KIS_PAPER_API_BASE must be a non-empty https:// URL from .env")
        if not settings.kis_paper_app_key:
            raise RuntimeError("KIS_PAPER_APP_KEY missing in .env")
        if not settings.kis_paper_app_secret:
            raise RuntimeError("KIS_PAPER_APP_SECRET missing in .env")
        if not settings.kis_paper_account:
            raise RuntimeError("KIS_PAPER_ACCOUNT missing in .env")
        self._settings = settings  # private; never expose externally

    def submit(self, broker_order: BrokerOrder) -> OrderAck:
        raise NotImplementedError("KIS Paper network calls are not implemented in this phase")

    def cancel(self, broker_order_id: str) -> None:
        raise NotImplementedError("KIS Paper network calls are not implemented in this phase")

    def open_orders(self) -> list[OrderAck]:
        raise NotImplementedError("KIS Paper network calls are not implemented in this phase")

    def positions(self) -> dict[str, int]:
        raise NotImplementedError("KIS Paper network calls are not implemented in this phase")
```

- 다른 모듈을 더 import하지 않는다(특히 `app.oms`, `app.risk`, `app.strategy` import 금지).
- URL/키/account를 어떤 외부 인터페이스로도 노출하지 않는다.

### 4.3 `app/config.py` 변경

`Settings`에 다음 필드를 추가(기본 None):

```python
kis_paper_api_base: str | None = None
kis_paper_app_key: str | None = None
kis_paper_app_secret: str | None = None
kis_paper_account: str | None = None
```

`load_settings()`가 `os.environ`에서 다음 키들을 읽어 빈 문자열은 `None`으로 정규화:

- `KIS_PAPER_API_BASE`
- `KIS_PAPER_APP_KEY`
- `KIS_PAPER_APP_SECRET`
- `KIS_PAPER_ACCOUNT`

**파일 로드 단계에서 KIS 키 누락은 에러로 만들지 않는다**(미국 Alpaca만 쓰는 시나리오를 깨지 않기 위해). 검증은 `KisPaperBroker.__init__`에서만.

기존 paper/live 차단 로직(`TRADING_MODE != paper`, `LIVE_TRADING_ENABLED`)은 변경 없음.

### 4.4 `app/domain/krx_session.py` (신규)

```python
from datetime import datetime, timezone, timedelta

from app.domain.enums import Session

KST = timezone(timedelta(hours=9))


def kst_session_for(ts: datetime) -> Session:
    """Map a timestamp to the KRX market session.

    Pure helper. Not invoked by any current module. Provided for future
    KRX strategies. Returns Session.CLOSED on weekends.
    """
    local = ts.astimezone(KST)
    if local.weekday() >= 5:  # Sat/Sun
        return Session.CLOSED
    h, m = local.hour, local.minute
    minutes = h * 60 + m
    pre_open = 8 * 60 + 30
    open_ = 9 * 60
    close = 15 * 60 + 30
    after_open = 16 * 60
    after_close = 18 * 60
    if pre_open <= minutes < open_:
        return Session.PRE_MARKET
    if open_ <= minutes < close:
        return Session.REGULAR
    if after_open <= minutes < after_close:
        return Session.AFTER_HOURS
    return Session.CLOSED
```

- 어떤 다른 모듈도 이 함수를 import하지 않는다.
- `Session` enum 외 import는 표준 라이브러리만.

### 4.5 `app/api/server.py` 변경

`create_app()`에서, 기존 와이어링 뒤에 다음을 추가:

```python
configured_brokers: list[str] = []
try:
    from app.broker.kis_paper import KisPaperBroker
    KisPaperBroker(settings)
    configured_brokers.append("KisPaperBroker")
except RuntimeError:
    pass
```

그리고 lifespan 안에서 `app.state.configured_brokers = configured_brokers`로 저장.

- `except RuntimeError` 외 다른 예외(예: ImportError, AttributeError)는 catch하지 않는다.
- KIS 인스턴스 자체는 `app.state`에 저장하지 않는다(활성 broker는 PaperBroker 그대로). credentials를 들고 있을 이유가 없다.

### 4.6 `app/api/routes.py` 변경

`/paper/status` 응답에 다음 키를 추가:

```python
"brokers": {
    "active": type(request.app.state.broker).__name__,
    "configured": list(request.app.state.configured_brokers),
},
```

- credentials/URL/account 미노출.
- 기존 `mode`/`live_enabled`/`strategies`/`safety` 키는 유지.
- 기존 `/paper/run` 핸들러는 손대지 않는다.

### 4.7 `.env.example` 변경

기존 ALPACA_PAPER_* 블록 아래 또는 적절한 위치에 다음 4줄을 추가:

```
# KIS 모의투자 (Korea Investment & Securities paper). Base URL은 사용자가 KIS Open API 공식 문서에서 직접 적습니다. 이 저장소는 URL을 추측하지 않습니다.
KIS_PAPER_API_BASE=
KIS_PAPER_APP_KEY=
KIS_PAPER_APP_SECRET=
KIS_PAPER_ACCOUNT=
```

placeholder는 모두 빈 값. 실제 키/계좌번호 금지.

### 4.8 테스트 (`tests/`)

#### `tests/test_kis_paper_stub.py` (신규)

```python
from dataclasses import replace
import pytest
from app.broker.kis_paper import KisPaperBroker
from app.domain.enums import TradingMode


def test_kis_paper_missing_base_url_fails_closed(settings):
    with pytest.raises(RuntimeError, match="KIS_PAPER_API_BASE"):
        KisPaperBroker(settings)


def test_kis_paper_non_https_base_url_fails_closed(settings):
    bad = replace(settings, kis_paper_api_base="http://example.com",
                  kis_paper_app_key="k", kis_paper_app_secret="s", kis_paper_account="1")
    with pytest.raises(RuntimeError, match="https://"):
        KisPaperBroker(bad)


def test_kis_paper_missing_credentials_fails_closed(settings):
    s = replace(settings, kis_paper_api_base="https://example.com")
    with pytest.raises(RuntimeError):
        KisPaperBroker(s)


def test_kis_paper_valid_init_then_methods_not_implemented(settings):
    s = replace(settings, kis_paper_api_base="https://example.com",
                kis_paper_app_key="k", kis_paper_app_secret="s", kis_paper_account="1")
    broker = KisPaperBroker(s)
    assert broker.mode == TradingMode.PAPER
    with pytest.raises(NotImplementedError):
        broker.submit(None)  # type: ignore[arg-type]
    with pytest.raises(NotImplementedError):
        broker.cancel("x")
    with pytest.raises(NotImplementedError):
        broker.open_orders()
    with pytest.raises(NotImplementedError):
        broker.positions()
```

(필요 시 `settings` fixture를 `tests/conftest.py`에서 그대로 사용.)

#### `tests/test_krx_session.py` (신규)

```python
from datetime import datetime, timezone, timedelta
from app.domain.enums import Session
from app.domain.krx_session import kst_session_for, KST


def at(year, month, day, hour, minute):
    return datetime(year, month, day, hour, minute, tzinfo=KST)


def test_premarket_window():
    assert kst_session_for(at(2026, 5, 14, 8, 45)) == Session.PRE_MARKET


def test_regular_window():
    assert kst_session_for(at(2026, 5, 14, 10, 0)) == Session.REGULAR


def test_after_hours_window():
    assert kst_session_for(at(2026, 5, 14, 17, 0)) == Session.AFTER_HOURS


def test_closed_weekend():
    assert kst_session_for(at(2026, 5, 16, 10, 0)) == Session.CLOSED  # Saturday


def test_closed_late_night():
    assert kst_session_for(at(2026, 5, 14, 23, 0)) == Session.CLOSED
```

(날짜는 평일·주말이 맞도록 calendar 확인. 2026-05-14는 목요일, 2026-05-16은 토요일.)

#### `tests/test_api_paper_status.py` 보정

기존 assertion은 그대로 두고, 다음을 추가:

```python
assert "brokers" in body
brokers = body["brokers"]
assert brokers["active"] == "PaperBroker"
assert isinstance(brokers["configured"], list)
# credentials must never leak in the response
body_text = response.text
assert "KIS_PAPER_APP_KEY" not in body_text
assert "KIS_PAPER_APP_SECRET" not in body_text
```

기존 테스트가 `safety.market_orders_disabled` 등을 확인하는 부분은 그대로 두어 회귀 검증.

### 4.9 검증 명령

`projects/paper-trading`에서:

```bash
python -m compileall app tests
python -m pytest -p no:cacheprovider
```

저장소 루트에서:

```bash
git diff --stat
git status --short
```

`compileall`과 `pytest`는 종료코드 0. mvp-005 기존 테스트 19개 + 신규 KIS/KRX 테스트가 모두 통과해야 한다.

호스트에 `pytest`/`fastapi`/`pydantic`/`httpx`/`python-dotenv` 미설치라 실패한 경우 작업을 멈추고 `patch.md` Remaining TODOs에 사람이 실행할 `pip install` 명령을 적은 뒤 종료한다. `pip install`을 Codex가 직접 실행하지 않는다.

### 4.10 `docs/ai/jobs/mvp-006/patch.md`

`prompts/codex-implementer.md` 형식. Implementation Summary는 요청 "완료 후 정리" 7개 항목과 1:1 대응하도록 단락 분리:

```markdown
## 1. Files Changed
## 2. Implementation Summary
### 2.1 변경 파일
### 2.2 KIS_PAPER_* 로드 경로
### 2.3 KisPaperBroker fail-closed 차단 조건
### 2.4 live trading 5단 차단 유지 여부
### 2.5 시장가 주문 차단 유지 (OrderType MARKET 없음)
### 2.6 mvp-005 기존 테스트 회귀 결과
### 2.7 다음 단계
## 3. Safety Confirmation
## 4. Test Results
## 5. Remaining TODOs
```

## 5. 테스트 기준

1. `python -m compileall app tests` 종료코드 0.
2. `python -m pytest -p no:cacheprovider` 종료코드 0. 기존 19개 + 신규 9개 안팎 모두 PASS(또는 미설치 사유 Remaining TODOs).
3. `grep -RIn "MARKET" projects/paper-trading/app` 결과 mvp-005와 동일(MARKET enum 멤버 미추가 확인).
4. `grep -RIn "from app\.(oms|risk|broker)|import app\.(oms|risk|broker)" projects/paper-trading/app/strategy` 결과 0건(Strategy 격리 유지).
5. `grep -RIn "https://" projects/paper-trading/app/broker/kis_paper.py` 결과는 prefix 검증 문자열만(`startswith("https://")`).
6. `grep -RIn "KIS_PAPER_APP_KEY\|KIS_PAPER_APP_SECRET\|kis_paper_app_key\s*=\s*['\"]\|kis_paper_app_secret\s*=\s*['\"]" projects/paper-trading/app projects/paper-trading/tests` 결과에 실제 시크릿 하드코딩 0건(env 이름과 placeholder만).
7. `git status --short`에 `.env` 미등장(`projects/paper-trading/.gitignore`로 이미 ignore됨).
8. `git diff --stat`에 mvp-006 외 변경 없음.
9. `/paper/status` 응답에 `brokers.active == "PaperBroker"`, `brokers.configured`는 list, credentials 미노출.

## 6. 리뷰 체크리스트

- [ ] `app/broker/kis_paper.py` 신규. `mode == TradingMode.PAPER`. URL/credentials/account 검증으로 fail-closed.
- [ ] `submit`/`cancel`/`open_orders`/`positions` 모두 `NotImplementedError`.
- [ ] `app/config.py`에 KIS 4필드 추가, `load_settings()`가 env에서 정규화하여 로드(누락은 None).
- [ ] `app/config.py`의 paper/live 차단 로직 변경 없음.
- [ ] `app/domain/krx_session.py` 신규, `kst_session_for` 함수만. `Session` 외 import 표준 라이브러리만.
- [ ] `app/api/server.py`가 `KisPaperBroker(settings)`를 `try/except RuntimeError`로 시도, 성공 시 `configured_brokers`에 등록. 활성 broker는 `PaperBroker` 그대로.
- [ ] `app/api/routes.py`의 `/paper/status`에 `brokers.active`, `brokers.configured` 추가. credentials/URL 미노출.
- [ ] `.env.example`에 KIS_PAPER_* placeholder 4줄 추가. 실제 키 없음.
- [ ] `tests/test_kis_paper_stub.py` 4 테스트 PASS.
- [ ] `tests/test_krx_session.py` 5 테스트 PASS(평일/주말/시간대별).
- [ ] `tests/test_api_paper_status.py`에 `brokers` 모양 + credentials 미노출 assertion 추가.
- [ ] mvp-005 기존 19개 테스트가 그대로 PASS(회귀 없음).
- [ ] `OrderType`에 MARKET 멤버 미추가.
- [ ] Strategy 패키지가 OMS/Risk/Broker import 0건.
- [ ] OMS의 `_risk`/`_broker` private 그대로.
- [ ] live 5단 차단 그대로.
- [ ] mvp-001..mvp-005 산출물 및 `web/`/`prompts/`/`scripts/`/기존 `docs/` 미변경.
- [ ] `.env` staged/committed 없음.
- [ ] commit/push/merge/deploy 자동화 없음.
- [ ] `patch.md` 5섹션 + Implementation Summary 7단락 모두 채움.
