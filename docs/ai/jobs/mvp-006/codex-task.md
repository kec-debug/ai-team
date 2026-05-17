# Codex Task — mvp-006: KIS 모의투자 broker adapter stub + 설정·메타·테스트

> Use `prompts/codex-implementer.md`. Read `docs/ai/jobs/mvp-006/plan.md` and `docs/ai/jobs/mvp-006/request.ko.md` first.

## 작업 컨텍스트

- Project directory: `/root/ai-dev-center/projects/ai-team`
- Job ID: `mvp-006`
- 대상 디렉터리: `projects/paper-trading/` (mvp-005에서 생성됨, 기존 구조 유지)
- 본 작업은 KIS 모의투자 broker adapter **stub** + 설정 + `/paper/status` 메타 + 테스트만 만든다. 실제 HTTP 호출, 새 전략, 시장 데이터 연결은 **하지 않는다**.

## 절대 하지 말 것 (Hard stops)

- `git commit`, `git push`, `git merge`, PR 생성/머지, 배포 자동화 금지.
- `.env`, secrets, credentials, API key, token, account number 류 일체 변경/생성 금지. `.env.example`은 placeholder 빈 값만.
- 실제 시크릿/실제 KIS app key/실제 base URL을 어떤 파일에도 하드코딩 금지(`startswith("https://")` 검증 문자열은 OK).
- live trading 코드 경로/플래그 활성화 금지. `Settings.live_trading_enabled` 기본 False, `load_settings()` env 차단 그대로.
- 실계좌(KIS 실전투자, Alpaca Live 등) 어댑터 작성 금지.
- 시장가(market) 주문 경로 신설 금지. `OrderType`에 MARKET 멤버 추가 금지.
- RiskEngine 우회 코드 경로 신설 금지.
- Strategy 패키지가 `app.oms`, `app.risk`, `app.broker`를 import하면 안 됨. 본 작업은 `app/strategy/`를 **수정하지 않는다**.
- OMS의 `_risk`/`_broker` private 유지. getter 추가 금지.
- `KisPaperBroker`에서 실제 네트워크 호출 시도 금지(HTTP/소켓/외부 라이브러리). 모두 `NotImplementedError`.
- `/paper/status`나 어떤 응답에서도 credentials/URL/account 노출 금지.
- 임의 shell 명령 입력 UI/API 신설 금지.
- 본 작업 범위 외 파일 변경 금지. 특히 mvp-001..mvp-005 산출물, `web/`, `prompts/`, `scripts/`, `examples/`, 기존 `docs/`(mvp-006 job dir 제외) 미변경.
- `pip install` 실행 금지. 의존성 미설치는 `patch.md` Remaining TODOs에만.

## 수정 허용 위치

### 신규 파일

- `projects/paper-trading/app/broker/kis_paper.py`
- `projects/paper-trading/app/domain/krx_session.py`
- `projects/paper-trading/tests/test_kis_paper_stub.py`
- `projects/paper-trading/tests/test_krx_session.py`
- `docs/ai/jobs/mvp-006/patch.md`

### 수정 가능 파일

- `projects/paper-trading/app/config.py` (KIS 필드 추가 + `load_settings` 보강)
- `projects/paper-trading/app/api/server.py` (KIS 인스턴스화 시도 + `configured_brokers` 등록)
- `projects/paper-trading/app/api/routes.py` (`/paper/status`에 `brokers` 추가)
- `projects/paper-trading/.env.example` (KIS placeholder 4줄 추가)
- `projects/paper-trading/tests/test_api_paper_status.py` (`brokers` assertion 추가)
- `projects/paper-trading/tests/conftest.py` (필요 시 KIS env helper fixture)

### 절대 수정 금지 파일

- `projects/paper-trading/app/domain/enums.py` (특히 `OrderType`에 MARKET 추가 금지)
- `projects/paper-trading/app/domain/orders.py`
- `projects/paper-trading/app/domain/market.py`
- `projects/paper-trading/app/broker/base.py`
- `projects/paper-trading/app/broker/paper.py`
- `projects/paper-trading/app/broker/alpaca_paper.py`
- `projects/paper-trading/app/risk/engine.py`
- `projects/paper-trading/app/oms/manager.py`
- `projects/paper-trading/app/strategy/*` 전부
- `projects/paper-trading/app/runtime/paper_runner.py`
- 그 외 `tests/test_config.py`, `tests/test_models.py`, `tests/test_risk_engine.py`, `tests/test_oms.py`, `tests/test_paper_broker.py`, `tests/test_alpaca_paper_stub.py`, `tests/test_flow.py`, `tests/test_paper_runner.py`, `tests/test_strategy_premarket_gap.py` — 회귀 검증에 사용.

## 구현 작업

### 1) `app/broker/kis_paper.py` (신규)

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
        self._settings = settings

    def submit(self, broker_order: BrokerOrder) -> OrderAck:
        raise NotImplementedError("KIS Paper network calls are not implemented in this phase")

    def cancel(self, broker_order_id: str) -> None:
        raise NotImplementedError("KIS Paper network calls are not implemented in this phase")

    def open_orders(self) -> list[OrderAck]:
        raise NotImplementedError("KIS Paper network calls are not implemented in this phase")

    def positions(self) -> dict[str, int]:
        raise NotImplementedError("KIS Paper network calls are not implemented in this phase")
```

추가 import 금지(특히 `app.oms`, `app.risk`, `app.strategy`, `app.runtime`, `app.api`).

### 2) `app/config.py` 변경

`Settings` 클래스에 다음 필드 4개를 추가(기본 `None`):

```python
kis_paper_api_base: str | None = None
kis_paper_app_key: str | None = None
kis_paper_app_secret: str | None = None
kis_paper_account: str | None = None
```

`load_settings()`가 `os.environ`(또는 기존 `_str_env` 같은 헬퍼)에서 다음을 읽어 빈 문자열은 `None`으로 정규화하여 `Settings`에 채운다.

- `KIS_PAPER_API_BASE`
- `KIS_PAPER_APP_KEY`
- `KIS_PAPER_APP_SECRET`
- `KIS_PAPER_ACCOUNT`

**파일 로드 단계에서 KIS 키 누락은 에러로 만들지 않는다.** Alpaca-only 사용자가 깨지면 안 된다. 검증은 `KisPaperBroker.__init__`에서만.

기존 paper/live 차단 로직(`TRADING_MODE != paper` → `ValueError`, `LIVE_TRADING_ENABLED` → `ValueError`)은 변경 없음.

### 3) `app/domain/krx_session.py` (신규)

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
    if local.weekday() >= 5:
        return Session.CLOSED
    minutes = local.hour * 60 + local.minute
    if 8 * 60 + 30 <= minutes < 9 * 60:
        return Session.PRE_MARKET
    if 9 * 60 <= minutes < 15 * 60 + 30:
        return Session.REGULAR
    if 16 * 60 <= minutes < 18 * 60:
        return Session.AFTER_HOURS
    return Session.CLOSED
```

`Session` 외 import는 표준 라이브러리만. 어떤 모듈도 이 함수를 import하지 않는다.

### 4) `app/api/server.py` 변경

기존 `create_app()` 와이어링 뒤에 다음 블록을 추가:

```python
configured_brokers: list[str] = []
try:
    from app.broker.kis_paper import KisPaperBroker
    KisPaperBroker(settings)
    configured_brokers.append("KisPaperBroker")
except RuntimeError:
    pass
```

`lifespan` 컨텍스트 내부에서 `app.state.configured_brokers = configured_brokers`를 저장(기존 `app.state.broker` 등 옆에).

- `except RuntimeError`만 catch. `Exception` broad catch 금지.
- `KisPaperBroker` 인스턴스 자체를 `app.state`에 저장하지 않는다. credentials를 보관할 이유 없음.

### 5) `app/api/routes.py` 변경

`/paper/status` 핸들러 응답에 다음 키를 추가(기존 `mode`/`live_enabled`/`strategies`/`safety` 유지):

```python
"brokers": {
    "active": type(request.app.state.broker).__name__,
    "configured": list(request.app.state.configured_brokers),
},
```

`/paper/run` 핸들러는 손대지 않는다.

### 6) `.env.example` 변경

기존 ALPACA_PAPER_* 블록 아래에 다음 4줄을 추가:

```
# KIS 모의투자 (Korea Investment & Securities paper). Base URL은 사용자가 KIS Open API 공식 문서에서 직접 적습니다. 이 저장소는 URL을 추측하지 않습니다.
KIS_PAPER_API_BASE=
KIS_PAPER_APP_KEY=
KIS_PAPER_APP_SECRET=
KIS_PAPER_ACCOUNT=
```

모두 빈 값. 실제 키/account 절대 금지.

### 7) 테스트

#### `tests/test_kis_paper_stub.py` (신규)

`plan.md` §4.8의 4 테스트를 그대로 구현.

#### `tests/test_krx_session.py` (신규)

`plan.md` §4.8의 5 테스트를 그대로 구현. **날짜는 평일/주말이 맞도록** 사용 전 확인(2026-05-14 = 목요일, 2026-05-16 = 토요일).

#### `tests/test_api_paper_status.py` 보정

기존 assertion 유지. 다음을 추가:

```python
assert "brokers" in body
brokers = body["brokers"]
assert brokers["active"] == "PaperBroker"
assert isinstance(brokers["configured"], list)
body_text = response.text
assert "KIS_PAPER_APP_KEY" not in body_text
assert "KIS_PAPER_APP_SECRET" not in body_text
```

#### `tests/conftest.py` (필요 시)

기존 `settings` fixture를 그대로 사용. KIS 필드는 기본 None이므로 별도 fixture 없이도 OK. 필요 시 helper fixture만 추가.

### 8) 검증

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

`compileall`과 `pytest`는 종료코드 0. mvp-005 기존 19개 + 신규 9개 안팎(`test_kis_paper_stub.py` 4 + `test_krx_session.py` 5)이 모두 PASS여야 한다.

호스트에 `pytest` 등이 미설치라 실패한 경우 작업을 멈추고 `patch.md` Remaining TODOs에 사람이 실행할 `pip install` 명령을 적은 뒤 종료한다. `pip install`을 Codex가 직접 실행하지 않는다.

### 9) `docs/ai/jobs/mvp-006/patch.md`

```markdown
## 1. Files Changed
(신규/수정 파일 전체)

## 2. Implementation Summary

### 2.1 변경 파일
(목록 + 한 줄 설명)

### 2.2 KIS_PAPER_* 로드 경로
- .env → load_settings() → Settings.kis_paper_* (누락은 None)
- 검증은 KisPaperBroker.__init__에서만 (fail closed)
- 어떤 모듈도 credentials 외부 노출 안 함

### 2.3 KisPaperBroker fail-closed 차단 조건
- KIS_PAPER_API_BASE 빈 값 또는 https:// 미시작 → RuntimeError
- KIS_PAPER_APP_KEY/SECRET/ACCOUNT 누락 → RuntimeError
- submit/cancel/open_orders/positions → NotImplementedError (네트워크 호출 없음)

### 2.4 live trading 5단 차단 유지
- Settings.live_trading_enabled 기본 False
- load_settings() env 차단
- RiskEngine.evaluate reject
- OMS.place 시작부 차단
- /paper/run 503
모두 본 작업에서 변경 없음.

### 2.5 시장가 주문 차단 유지
- OrderType에 MARKET 멤버 추가 없음
- RiskEngine, PaperBroker, Strategy 모두 변경 없음

### 2.6 mvp-005 기존 테스트 회귀
- 19개 PASS (또는 실패 사유 명시)
- 신규 테스트 결과

### 2.7 다음 단계
- KIS HTTP 호출 실제 구현 (별도 mvp)
- Alpaca HTTP 호출 실제 구현 (별도 mvp)
- KRX 한국 시장 전략 (premarket gap 한국형 변형 등) (별도 mvp)

## 3. Safety Confirmation
- live trading 코드 경로/플래그 활성화 없음
- 실계좌 어댑터 없음 (KIS도 paper만)
- 시장가 주문 차단 유지 (OrderType에 MARKET 없음)
- 모든 주문은 OMS만 broker.submit 호출 (mvp-005 OMS 미변경)
- OMS가 외부 호출자에게 RiskEngine/Broker 노출하지 않음 (mvp-005 미변경)
- Strategy는 OMS/Broker/RiskEngine 직접 호출 없음 (mvp-005 미변경, grep 0건 확인)
- /paper/run은 caller-provided OrderIntent 미수용 (mvp-005 미변경)
- secrets/.env/auth/payment/migration/infra 미변경
- broker endpoint URL 하드코딩 없음 (KIS도 env에서만)
- /paper/status 응답에 credentials/URL/account 미노출
- git commit/push/merge/deploy 자동화 없음

## 4. Test Results
- python -m compileall app tests: <결과>
- python -m pytest -p no:cacheprovider: <결과>
- git diff --stat: <결과>
- git status --short: <결과>

## 5. Remaining TODOs
- 없음 (또는 의존성 미설치 시 pip install 명령 / Phase 2 후보 명시)
```

## 완료 정의 (Done)

- `app/broker/kis_paper.py`, `app/domain/krx_session.py`, `tests/test_kis_paper_stub.py`, `tests/test_krx_session.py` 신규 생성됨.
- `app/config.py`, `app/api/server.py`, `app/api/routes.py`, `.env.example`, `tests/test_api_paper_status.py` 수정.
- 그 외 `projects/paper-trading/` 파일은 모두 미변경(특히 `app/domain/enums.py`, `app/strategy/*`, `app/oms/`, `app/risk/`, `app/runtime/`, `app/broker/{base.py,paper.py,alpaca_paper.py}`).
- `mvp-005` 기존 19개 테스트가 그대로 PASS(회귀 없음).
- 신규 KIS/KRX 테스트(약 9개)가 PASS.
- `/paper/status` 응답에 `brokers.active="PaperBroker"`, `brokers.configured=list` 추가. credentials 미노출.
- `OrderType`에 MARKET 멤버 없음(grep 확인).
- Strategy 패키지가 OMS/Risk/Broker import 0건(grep 확인).
- `KisPaperBroker`가 fail closed로 동작하며 네트워크 호출 없음.
- `git diff --stat`에 mvp-006 외 변경 없음.
- `.env`가 staged/committed되지 않음.
- `patch.md`가 5섹션 + Implementation Summary 7단락으로 작성됨.
- commit/push/merge/deploy 자동화 없음.
