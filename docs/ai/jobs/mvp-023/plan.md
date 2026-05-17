## 1. 요청 요약

KIS 실제 시세 조회 연결을 **준비**한다. KIS Open API 공식 문서값이 저장소에 없고 Codex는 웹 접근이 없으므로 실제 HTTP 구현은 본 작업에서도 보류된다. 대신 mvp-024 후보 생성기가 사용할 **`Quote` 도메인 모델** + **`MISSING_MARKET_DATA_VALUES.md` catalog** + **fail-closed boundary 유지**까지 산출.

### Master roadmap 컨텍스트 (`docs/ai/MASTER_TRADING_ROADMAP.md` §4 mvp-023)

- mvp-022 (`.env` 자동 로딩) → **mvp-023 (KIS 시세 조회 연결)** → mvp-024 (실제 시세 기반 후보 생성).
- 핵심 병목은 KIS 주문이 아니라 **실제 시장 데이터 입력**(roadmap §3). mvp-023이 그 경계를 마련.
- 중복 방지 규칙(roadmap §5): 공식 문서값 없으면 가짜 HTTP 구현 금지. missing-values 정리만.

### 현재 상태 점검 (직접 확인)

- `app/broker/kis.py:KisMarketDataClient.get_quote(symbol)`이 이미 존재 — auth 체크 → `NotImplementedError("KIS get_quote(): TODO — confirm market data endpoint, TR ID, payload, ...")`.
- `KisHttpClient` boundary 존재(`request()` NotImplementedError, HTTP lib import 0건).
- `app/domain/`에 `enums.py`, `orders.py`, `market.py`(StrategyInput) 존재. **`Quote` 모델은 부재** → 신규 추가 필요.
- `docs/kis/MISSING_OFFICIAL_VALUES.md` 존재(mvp-014-017-bundle). §3 "해외주식/미국주식 시세"가 일부 필드 다룸. mvp-023은 더 세밀한 market-data 전용 catalog를 추가하고 cross-reference 한다.
- mvp-005의 `StrategyInput`(`app/domain/market.py`)이 Strategy의 입력 — `Quote`는 그것보다 더 raw한 broker-level 응답 모델로 자리.

### 안전 원칙 (mvp-005~mvp-022 누적 유지)

- live trading 활성화 금지. 5단+1단(`Settings`/`load_settings`/`RiskEngine`/`OMS`/`POST /paper/run`/`KisBroker.__init__`) 차단 모두 유지.
- `OrderType.MARKET` 부재 유지.
- 외부 HTTP 라이브러리 import 금지.
- KIS endpoint URL/TR ID/payload/header 추측 금지.
- 실제 KIS app key/secret/account/token 어떤 파일에도 미포함.
- `KisMarketDataClient`/`get_quote`의 fail-closed 동작 유지 — pre-flight 통과해도 최종 `NotImplementedError`.
- Strategy 패키지가 `app.broker.kis*` import 금지 유지.
- `git commit`/`push`/`merge`/`deploy` 자동화 금지.
- `pip install` 실행 금지.

### 검증

```bash
cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
.venv/bin/python -m compileall app tests
.venv/bin/python -m pytest -p no:cacheprovider
```

기존 193± + 신규 약 8–12개 모두 PASS.

## 2. 작업 범위

### 포함 (In scope)

`projects/paper-trading/` 아래:

- **`app/domain/quote.py` (신규)** — `Quote` frozen dataclass (또는 pydantic BaseModel) + `QuoteFreshness` helper:
  - 필드: `symbol: str`, `last: Decimal`, `bid: Decimal`, `ask: Decimal`, `volume: int`, `timestamp: datetime`, `source: str` (예: `"kis_paper"`, `"manual"`).
  - 메서드/프로퍼티: `spread_pct() -> Decimal` (((ask-bid)/last) 또는 ask가 0이면 0/Decimal("Infinity") 안전 처리), `is_stale(now, max_age_seconds) -> bool`.
  - `__post_init__`/`field_validator`: `symbol == symbol.upper()`, `last > 0`, `bid > 0`, `ask >= bid`, `volume >= 0`, `timestamp` aware datetime.
  - `app.broker.kis` / `app.config` import 0건 (도메인은 독립).
- **`app/broker/kis.py` (수정)** — `KisMarketDataClient` 메서드 시그니처 유지하되 반환 타입 명확화 + Quote 모델 awareness:
  - 기존 `get_quote(symbol) -> dict[str, Any]` → `dict[str, Any]` 유지(공식 문서 부재로 raw 응답 shape 미정).
  - 신규 helper `quote_from_raw(raw: dict) -> Quote`를 같은 모듈에 두지 않고 `app/broker/kis_quote_mapper.py` (신규)로 분리 — sanitize_kis_response 통과 후 raw dict를 도메인 `Quote`로 매핑. 단, **이 매퍼는 공식 문서값 부재 상태에서도 사용 불가능** (raw 응답 shape를 모르므로). 따라서 mvp-023에서는 **mapper 시그니처만 정의**하고 본문은 `NotImplementedError("TODO — confirm KIS quote response field names")`.
  - 기존 `get_quote`/`get_last_price`/`healthcheck_market_data` 동작 보존(fail-closed).
- **`app/broker/kis_quote_mapper.py` (신규)** — `kis_raw_quote_to_domain(raw, symbol, source="kis_paper") -> Quote` skeleton. `NotImplementedError` + 명시적 TODO. KIS 응답 shape 확정 후 별도 mvp에서 본문 구현.
- **`docs/kis/MISSING_MARKET_DATA_VALUES.md` (신규)** — market data 전용 catalog. Cross-reference `MISSING_OFFICIAL_VALUES.md` §3. 4개 항목 그룹 + 응답 필드 매핑 표.
- **테스트** (신규):
  - `tests/test_quote_model.py` — Quote 도메인 모델 단위 테스트 (필드 검증, spread_pct, is_stale, repr 마스킹 없음 — Quote는 secret 미포함).
  - `tests/test_kis_quote_mapper.py` — mapper가 `NotImplementedError` (fail-closed) 반환 확인 + symbol/source/timestamp 인자 검증.
  - `tests/test_missing_market_data_values_doc.py` — `docs/kis/MISSING_MARKET_DATA_VALUES.md` 파일 존재 + 4개 섹션 헤더 + `Confirmed: yes` 부재 + 실제 키 prefix 부재.
- **`tests/test_kis_market_data_client.py` (보정)** — 기존 테스트가 fail-closed 유지를 검증하는지 확인 + 회귀 테스트 추가(mvp-023에서 `get_quote`가 여전히 `NotImplementedError`인지).
- **`projects/paper-trading/README.md` (수정)** — mvp-022 단락 뒤에 `## KIS 시세 조회 준비 (mvp-023)` 단락 추가.
- **`docs/ai/jobs/mvp-023/patch.md` (신규)** — Codex 변경 요약.

### 제외 (Out of scope; 절대 만지지 않음)

- 실제 KIS HTTP 호출 / endpoint URL / TR ID / payload / header 추가.
- 외부 HTTP 라이브러리 import.
- live trading 활성화. 시장가 주문 허용. `OrderType.MARKET` 추가.
- `app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/static/*` 변경.
- `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*`, `app/runtime/*` 변경.
- `app/domain/{enums.py,orders.py,market.py}` 변경(`Quote`는 신규 파일 `quote.py`로 추가).
- `app/broker/{base.py,paper.py,alpaca_paper.py}` 변경.
- `app/broker/kis.py`의 기존 메서드/클래스 본문 변경(추가 helper만 가능). KIS endpoint/TR ID/HTTP 라이브러리 import 금지.
- `Settings`, `app/config.py` 변경. 새 env 변수 추가 금지.
- `.env`, `.env.example`, 프로젝트/루트 `.gitignore` 변경.
- mvp-001..mvp-022 산출물 변경.
- `scripts/`(mvp-020 산출물), `imports/`, `web/`, `prompts/`, 기존 `docs/`(`docs/ai/jobs/mvp-023/` + `docs/kis/MISSING_MARKET_DATA_VALUES.md` 외) 변경.
- 자동 commit/push/merge/deploy.
- 임의 shell 명령 입력 UI/API 신설.
- `pip install` 실행.
- candidate scanner / strategy 후보 생성 (mvp-024 영역).

### 안전 가드

- `Quote` 모델은 **broker 출처를 source 필드로 명시**해 LLM/Agent/Strategy가 임의로 fake quote를 만들지 못하게 한다. mvp-024가 이 source를 검증.
- `kis_quote_mapper.py`는 `Quote`로 변환 전 입력 dict에 `sanitize_kis_response` 적용 권장(매핑 본문이 구현될 때). 본 mvp에서는 시그니처만 정의이므로 구현 불필요.
- `MISSING_MARKET_DATA_VALUES.md`에는 실제 endpoint URL/TR ID/path/실 키/계좌번호 **0건**. `<TBD>` placeholder만.
- `Quote`는 KIS broker와 무관하게 정의 → mvp-024가 다른 source(예: 합성 데이터, 다른 broker)에서도 동일 인터페이스로 사용 가능.

## 3. 수정해야 할 파일

### 신규

| 파일 | 목적 |
| --- | --- |
| `app/domain/quote.py` | Quote 도메인 모델 |
| `app/broker/kis_quote_mapper.py` | KIS raw → Quote 매퍼 skeleton (NotImplementedError) |
| `docs/kis/MISSING_MARKET_DATA_VALUES.md` | market data 전용 missing-values catalog |
| `tests/test_quote_model.py` | Quote 단위 테스트 |
| `tests/test_kis_quote_mapper.py` | 매퍼 fail-closed 검증 |
| `tests/test_missing_market_data_values_doc.py` | 문서 존재/구조 검증 |
| `docs/ai/jobs/mvp-023/patch.md` | Codex 변경 요약 |

### 수정

| 파일 | 변경 내용 |
| --- | --- |
| `projects/paper-trading/README.md` | mvp-023 단락 추가 |
| `tests/test_kis_market_data_client.py` | (옵션) get_quote가 여전히 NotImplementedError 회귀 검증 추가 |

### 절대 미수정

- `app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/static/*`
- `app/config.py`, `app/domain/{enums.py,orders.py,market.py}`
- `app/broker/{base.py,paper.py,alpaca_paper.py}`, `app/broker/kis.py` (본문 변경 금지; 새 파일만 추가)
- `app/oms/*`, `app/risk/*`, `app/strategy/*`, `app/portfolio/*`, `app/session/*`, `app/reports/*`, `app/runtime/*`
- `.env`, `.env.example`, 프로젝트 `.gitignore`, 루트 `.gitignore`
- mvp-001..mvp-022 산출물
- `scripts/` (mvp-020), `imports/`, `web/`, `prompts/`, 기존 `docs/`(예외: `docs/kis/MISSING_MARKET_DATA_VALUES.md` 신규)

## 4. Codex 구현 지시문

### 4.1 사전 점검

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

### 4.2 `app/domain/quote.py` (신규)

```python
"""Quote domain model — broker-agnostic market data snapshot.

Used as the canonical input shape for candidate scanners and strategies.
Does not depend on app.config, app.broker, or any HTTP library — keeps the
domain layer independent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal


@dataclass(frozen=True)
class Quote:
    symbol: str
    last: Decimal
    bid: Decimal
    ask: Decimal
    volume: int
    timestamp: datetime
    source: str  # e.g. "kis_paper", "alpaca_paper", "synthetic"

    def __post_init__(self) -> None:
        if not self.symbol or self.symbol != self.symbol.upper():
            raise ValueError("symbol must be non-empty uppercase")
        if self.last <= 0:
            raise ValueError("last must be > 0")
        if self.bid <= 0:
            raise ValueError("bid must be > 0")
        if self.ask < self.bid:
            raise ValueError("ask must be >= bid")
        if self.volume < 0:
            raise ValueError("volume must be >= 0")
        if self.timestamp.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        if not self.source:
            raise ValueError("source must be non-empty")

    @property
    def spread_pct(self) -> Decimal:
        """(ask - bid) / last as a Decimal fraction (e.g. 0.005 = 0.5%)."""
        if self.last == 0:
            return Decimal("0")
        return (self.ask - self.bid) / self.last

    def is_stale(self, now: datetime, max_age_seconds: int) -> bool:
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        age = (now - self.timestamp).total_seconds()
        return age > max_age_seconds or age < 0
```

핵심 불변식:

- import 0건 (`app.config`, `app.broker.kis`, HTTP 라이브러리 미import).
- frozen dataclass — 외부에서 수정 불가능.
- `__post_init__`이 모든 invariant 검증.
- `source` 필드로 출처 추적 — LLM/Agent가 임의로 만든 quote를 mvp-024 scanner가 식별 가능.

### 4.3 `app/broker/kis_quote_mapper.py` (신규)

```python
"""KIS raw quote → domain Quote mapper (skeleton).

Network call is not implemented in this phase. The exact KIS overseas/US-stock
quote response field names are not available in this repository. See
docs/kis/MISSING_MARKET_DATA_VALUES.md for the required values.

Once official documentation is confirmed, populate the mapping below and call
sanitize_kis_response() on raw input before extraction.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.domain.quote import Quote


def kis_raw_quote_to_domain(
    raw: dict[str, Any] | None,
    symbol: str,
    source: str = "kis_paper",
) -> Quote:
    """Convert a raw KIS quote response dict into a domain Quote.

    Raises NotImplementedError until KIS official response field names are
    confirmed (see docs/kis/MISSING_MARKET_DATA_VALUES.md).
    """
    if raw is None:
        raise ValueError("raw quote payload is None")
    if not symbol:
        raise ValueError("symbol must be non-empty")
    raise NotImplementedError(
        "KIS quote response field mapping is not implemented. "
        "Confirm field names (last/bid/ask/volume/timestamp) from KIS Open API "
        "official documentation and update docs/kis/MISSING_MARKET_DATA_VALUES.md "
        "before wiring this mapper."
    )
```

핵심:

- `app.broker.kis` import 0건 (반환 타입은 `Quote` 도메인만). 매퍼는 broker-agnostic.
- 외부 HTTP 라이브러리 import 0건.
- 입력 검증(None, 빈 symbol)은 즉시 raise. 나머지는 NotImplementedError로 fail-closed.

### 4.4 `docs/kis/MISSING_MARKET_DATA_VALUES.md` (신규)

```markdown
# KIS Open API — Missing Market Data Values

본 문서는 KIS Open API 미국주식/해외주식 시세 조회 HTTP 연결을 구현하기 위해 필요한 공식 문서값을 정리합니다. 본 저장소는 KIS endpoint, TR ID, header, payload를 추측하지 않습니다. 아래 항목이 KIS 공식 Open API 문서에서 확인된 뒤에만 별도 mvp에서 HTTP 연결을 진행합니다.

본 문서는 `docs/kis/MISSING_OFFICIAL_VALUES.md` §3 "해외주식/미국주식 시세"를 보강하는 시세 전용 catalog입니다. 두 문서를 모두 채워야 합니다.

## 정책

- 본 표의 모든 `<TBD>` 항목은 KIS 공식 Open API 개발자 포털 문서에서 직접 확인해 채워 넣어야 합니다.
- 실전투자(live) endpoint는 본 저장소에 추가하지 않습니다. 모의투자(paper) endpoint만 다룹니다.
- 실제 app key, app secret, 계좌번호, access token 값은 본 문서/저장소 어디에도 기록하지 않습니다.
- 항목별로 `Confirmed: no`인 한 해당 HTTP 기능은 `NotImplementedError` 상태를 유지합니다.

## 1. 해외주식/미국주식 현재가(Quote) endpoint

| 항목 | 설명 | 값 | Confirmed |
| --- | --- | --- | --- |
| Paper trading base URL | 모의투자 환경 base | `<TBD>` | no |
| Quote endpoint path | 현재가 path | `<TBD>` | no |
| HTTP method | GET/POST | `<TBD>` | no |
| Required headers | `content-type`, `authorization`, `tr_id` 등 | `<TBD>` | no |
| TR ID (모의투자) | 시세 조회용 TR ID | `<TBD>` | no |
| Query/body fields | 종목코드, 거래소 코드, 시장 구분 등 | `<TBD>` | no |
| Symbol code format | KIS에서 받는 심볼 표기 (예: AAPL vs AAPL.O) | `<TBD>` | no |

→ 충족 시 `app/broker/kis_quote_mapper.py:kis_raw_quote_to_domain` 본문 구현 가능.

## 2. Quote 응답 필드 매핑

KIS 응답 dict에서 다음 필드 이름을 확인해야 도메인 `Quote`로 매핑 가능.

| Domain field | KIS response field | Confirmed |
| --- | --- | --- |
| `symbol` | 응답에 echo되는지 또는 요청값 사용 | `<TBD>` | no |
| `last` | 현재가 | `<TBD>` | no |
| `bid` | 매수호가 | `<TBD>` | no |
| `ask` | 매도호가 | `<TBD>` | no |
| `volume` | 누적 거래량 | `<TBD>` | no |
| `timestamp` | 응답 시각 (timezone-aware) | `<TBD>` | no |
| `is_stale` 판단 기준 | 거래소 시간/응답 시각 차이 단위 | `<TBD>` | no |

## 3. 호가단위 / 거래소 시간

| 항목 | 설명 | 값 | Confirmed |
| --- | --- | --- | --- |
| 거래소 코드 | NYSE / NASDAQ / AMEX 등 | `<TBD>` | no |
| 호가단위 (tick size) | 미국주식 일반 0.01 USD | `<TBD>` | no |
| 거래소 timezone | 미국 동부(ET, UTC-5/UTC-4) | `<TBD>` | no |
| 응답 timestamp 포맷 | ISO8601 / epoch / KIS 고유 | `<TBD>` | no |

## 4. 시세 종류 / 권한

| 항목 | 설명 | 값 | Confirmed |
| --- | --- | --- | --- |
| 실시간 시세 권한 | 모의투자 환경에서 가능 여부 | `<TBD>` | no |
| 지연 시세 / 스냅샷 차이 | KIS API가 제공하는 시세의 신선도 | `<TBD>` | no |
| Rate limit | 초당/분당 요청 한도 | `<TBD>` | no |
| 동시 심볼 수 제한 | 단일 요청당 최대 심볼 수 | `<TBD>` | no |

## 다음 작업 가이드

1. 사용자가 KIS Open API 공식 개발자 포털에서 위 `<TBD>` 항목을 직접 확인합니다.
2. 항목별로 `Confirmed: yes`로 변경하고 값을 채워 넣습니다.
3. 모든 항목이 `Confirmed: yes`가 된 뒤에만 별도 mvp에서 `kis_quote_mapper.py`와 `KisMarketDataClient.get_quote`를 실제 HTTP로 연결합니다.
4. 본 저장소는 사용자가 확인하지 않은 값은 절대 사용하지 않습니다.

## 보안

- 실제 app key, app secret, 계좌번호, access token, refresh token은 이 문서에 절대 기록하지 않습니다. 모두 `.env`(gitignored)에만 둡니다.
- 본 문서가 커밋된 형태로 git에 들어가도 자격증명 누출이 없도록 합니다.

## 관련 문서

- `docs/kis/MISSING_OFFICIAL_VALUES.md` — KIS 전반(OAuth/계좌/시세/주문) 누락 값. 본 문서와 §3에서 일부 겹침.
- `docs/ai/MASTER_TRADING_ROADMAP.md` — 전체 로드맵.
```

### 4.5 테스트

#### `tests/test_quote_model.py` (신규)

```python
from datetime import datetime, timezone, timedelta
from decimal import Decimal

import pytest

from app.domain.quote import Quote


def _q(**overrides) -> Quote:
    data = {
        "symbol": "AAPL",
        "last": Decimal("100"),
        "bid": Decimal("99.95"),
        "ask": Decimal("100.05"),
        "volume": 1_000_000,
        "timestamp": datetime.now(timezone.utc),
        "source": "synthetic",
    }
    data.update(overrides)
    return Quote(**data)


def test_quote_happy_path():
    q = _q()
    assert q.symbol == "AAPL"
    assert q.source == "synthetic"


def test_quote_rejects_lowercase_symbol():
    with pytest.raises(ValueError, match="uppercase"):
        _q(symbol="aapl")


def test_quote_rejects_non_positive_last():
    with pytest.raises(ValueError, match="last"):
        _q(last=Decimal("0"))


def test_quote_rejects_ask_lower_than_bid():
    with pytest.raises(ValueError, match="ask"):
        _q(bid=Decimal("100"), ask=Decimal("99"))


def test_quote_rejects_negative_volume():
    with pytest.raises(ValueError, match="volume"):
        _q(volume=-1)


def test_quote_rejects_naive_timestamp():
    with pytest.raises(ValueError, match="timezone-aware"):
        _q(timestamp=datetime(2026, 5, 15, 9, 0, 0))


def test_quote_rejects_empty_source():
    with pytest.raises(ValueError, match="source"):
        _q(source="")


def test_quote_spread_pct():
    q = _q(last=Decimal("100"), bid=Decimal("99.5"), ask=Decimal("100.5"))
    # (100.5 - 99.5) / 100 = 0.01 (1%)
    assert q.spread_pct == Decimal("0.01")


def test_quote_is_stale_old():
    old = datetime.now(timezone.utc) - timedelta(seconds=120)
    q = _q(timestamp=old)
    assert q.is_stale(datetime.now(timezone.utc), max_age_seconds=60) is True


def test_quote_is_fresh_recent():
    recent = datetime.now(timezone.utc) - timedelta(seconds=5)
    q = _q(timestamp=recent)
    assert q.is_stale(datetime.now(timezone.utc), max_age_seconds=60) is False


def test_quote_is_stale_rejects_naive_now():
    q = _q()
    with pytest.raises(ValueError, match="timezone-aware"):
        q.is_stale(datetime(2026, 5, 15, 9, 0, 0), max_age_seconds=60)


def test_quote_frozen_dataclass_immutable():
    q = _q()
    with pytest.raises(Exception):  # FrozenInstanceError
        q.last = Decimal("999")  # type: ignore[misc]
```

#### `tests/test_kis_quote_mapper.py` (신규)

```python
import pytest

from app.broker.kis_quote_mapper import kis_raw_quote_to_domain


def test_mapper_raises_not_implemented_with_valid_input():
    with pytest.raises(NotImplementedError, match="official documentation"):
        kis_raw_quote_to_domain({"any": "shape"}, symbol="AAPL")


def test_mapper_rejects_none_raw():
    with pytest.raises(ValueError, match="None"):
        kis_raw_quote_to_domain(None, symbol="AAPL")  # type: ignore[arg-type]


def test_mapper_rejects_empty_symbol():
    with pytest.raises(ValueError, match="symbol"):
        kis_raw_quote_to_domain({"any": "shape"}, symbol="")
```

#### `tests/test_missing_market_data_values_doc.py` (신규)

```python
import pathlib


DOC_PATH = pathlib.Path(__file__).resolve().parents[2] / "docs" / "kis" / "MISSING_MARKET_DATA_VALUES.md"


def test_doc_exists():
    assert DOC_PATH.is_file(), f"missing: {DOC_PATH}"


def test_doc_has_required_sections():
    text = DOC_PATH.read_text(encoding="utf-8")
    for marker in (
        "현재가",
        "Quote",
        "응답 필드",
        "호가단위",
        "Confirmed",
        "<TBD>",
    ):
        assert marker in text, f"missing marker: {marker}"


def test_doc_has_no_confirmed_yes_entries():
    text = DOC_PATH.read_text(encoding="utf-8")
    assert "Confirmed: yes" not in text


def test_doc_does_not_leak_real_secrets():
    text = DOC_PATH.read_text(encoding="utf-8")
    for forbidden in ("PSNFD", "PKID", "AKIA", "sk-", "ghp_"):
        assert forbidden not in text
```

#### `tests/test_kis_market_data_client.py` (기존 보존, 회귀 1개 추가)

기존 테스트 모두 유지. 다음 한 개 추가:

```python
def test_kis_get_quote_still_fail_closed_after_mvp023(settings):
    """mvp-023 adds Quote model + mapper skeleton but does NOT enable get_quote."""
    s = replace(settings, kis_env="paper", kis_account_no="x",
                kis_app_key="k", kis_app_secret="s")
    md = KisMarketDataClient(s, KisAuthClient(s))
    with pytest.raises(NotImplementedError, match="official documentation"):
        md.get_quote("AAPL")
```

(기존 import/패턴에 맞춰 작성 — `KisAuthClient`, `KisMarketDataClient`, `replace`, `pytest` 등 이미 사용 중.)

### 4.6 README 변경

mvp-022 단락 뒤에 다음 단락 추가. 기존 단락 변경 없음.

```markdown
## KIS 시세 조회 준비 (mvp-023)

전략 후보 생성(mvp-024)에 사용할 broker-agnostic `Quote` 도메인 모델이 `app/domain/quote.py`에 추가되었습니다.

- 필드: `symbol`, `last`, `bid`, `ask`, `volume`, `timestamp`, `source`
- 속성/메서드: `spread_pct` (Decimal 분율), `is_stale(now, max_age_seconds)`
- `__post_init__`이 모든 invariant 검증 (uppercase symbol, 양수 가격, `ask >= bid`, timezone-aware timestamp).
- `source` 필드로 출처 추적 (예: `"kis_paper"`, `"alpaca_paper"`, `"synthetic"`) — 임의의 quote 주입 방지.

`app/broker/kis_quote_mapper.py`는 KIS raw 응답을 `Quote`로 변환하는 매퍼의 **skeleton**입니다. KIS Open API 공식 문서값이 부재하므로 본 단계에서는 `NotImplementedError`로 fail-closed.

필요한 공식 문서값은 [`docs/kis/MISSING_MARKET_DATA_VALUES.md`](../../docs/kis/MISSING_MARKET_DATA_VALUES.md)에 catalog로 정리되어 있습니다. 사용자가 KIS 공식 개발자 포털에서 항목별 `<TBD>`를 채우고 `Confirmed: yes`로 표시한 뒤에만 별도 mvp에서 매퍼 본문과 `KisMarketDataClient.get_quote` HTTP 호출을 구현합니다.
```

### 4.7 검증 명령

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

기대: 기존 193± + 신규 약 18 (Quote 12 + mapper 3 + doc 4 + regression 1) ≈ 211 PASS. mvp-023 외 변경 없음.

### 4.8 `docs/ai/jobs/mvp-023/patch.md`

```markdown
## 1. Files Changed
- app/domain/quote.py (신규)
- app/broker/kis_quote_mapper.py (신규)
- docs/kis/MISSING_MARKET_DATA_VALUES.md (신규)
- tests/test_quote_model.py (신규)
- tests/test_kis_quote_mapper.py (신규)
- tests/test_missing_market_data_values_doc.py (신규)
- tests/test_kis_market_data_client.py (회귀 테스트 1개 추가)
- projects/paper-trading/README.md (mvp-023 단락)
- docs/ai/jobs/mvp-023/patch.md (본 요약)

## 2. Implementation Summary

### 2.1 Quote 도메인 모델
- frozen dataclass, broker-agnostic
- 필드: symbol/last/bid/ask/volume/timestamp/source
- spread_pct property, is_stale 메서드
- __post_init__ 검증

### 2.2 KIS quote mapper skeleton
- kis_raw_quote_to_domain(raw, symbol, source)
- 입력 검증(None, 빈 symbol) 후 NotImplementedError
- KIS endpoint/TR ID/응답 shape 미정으로 fail-closed

### 2.3 MISSING_MARKET_DATA_VALUES.md
- 4개 섹션: 현재가 endpoint / Quote 응답 매핑 / 호가단위·거래소 시간 / 시세 종류·권한
- 모든 값 <TBD> + Confirmed: no
- 실제 endpoint/TR ID/key/secret 0건

### 2.4 KIS HTTP 미구현 유지
- KisMarketDataClient.get_quote 그대로 NotImplementedError
- 외부 HTTP 라이브러리 import 0건
- KIS endpoint URL/TR ID 코드 0건

### 2.5 안전 가드 유지
- live trading 비활성
- 시장가 주문 금지 (OrderType MARKET 부재)
- KIS_ORDER_DRY_RUN=true 기본
- Strategy 패키지가 app.broker.kis* 미import
- /paper/status 응답에 raw credentials 미포함

### 2.6 mvp-024 준비
- Quote 모델이 mvp-024 candidate scanner의 입력 인터페이스
- source 필드로 출처 추적 (LLM/Agent 주입 방지)

### 2.7 실행한 테스트
- compileall PASS
- pytest 193+ → 211± PASS (신규 ~18)
- 기존 회귀 0건

### 2.8 공식 문서 부재로 보류된 작업
- KIS 시세 endpoint URL, TR ID, payload, 응답 필드 매핑
- 사용자가 MISSING_MARKET_DATA_VALUES.md를 채운 뒤 별도 mvp에서 진행

## 3. Safety Confirmation
- 실주문 코드 0건. KIS HTTP 호출 0건.
- KIS endpoint URL/TR ID/payload 추가 0건. 외부 HTTP 라이브러리 import 0건.
- raw key/secret/account/token 코드/문서/.env.example/응답/log/patch 미노출.
- Quote는 broker-agnostic, source 필드로 출처 추적.
- live trading 비활성 + 5+1단 차단 유지.
- 시장가 차단 유지 (OrderType MARKET 부재).
- mvp-005~mvp-022 안전 불변식 모두 유지.
- Strategy 패키지가 app.broker.kis* import 0건 유지.
- OMS는 PaperBroker만 사용.
- /paper/status raw credentials 미노출.
- .env staged/committed 없음.
- commit/push/merge/deploy 자동화 없음.

## 4. Test Results
- compileall: PASS
- pytest: 신규 ~18 PASS, 기존 회귀 0건

## 5. Remaining TODOs
- 사용자가 docs/kis/MISSING_MARKET_DATA_VALUES.md의 <TBD> 항목을 채워야 mvp-024+에서 실제 HTTP 호출 가능.
- mvp-024: 실제 시세(또는 mock 데이터)를 사용해 candidate scanner 구현.
```

## 5. 테스트 기준

1. `.venv/bin/python -m compileall app tests` 종료코드 0.
2. `.venv/bin/python -m pytest -p no:cacheprovider` 종료코드 0. 기존 193± + 신규 ~18 PASS.
3. `grep -RnE "from app\.config|import app\.config" projects/paper-trading/app/domain/quote.py` 결과 0건(도메인 격리).
4. `grep -RnE "from app\.broker|import app\.broker|import requests|import httpx|import aiohttp" projects/paper-trading/app/domain/quote.py` 결과 0건.
5. `grep -RnE "import requests|import httpx|import aiohttp|import urllib3" projects/paper-trading/app/broker/kis_quote_mapper.py` 결과 0건.
6. `grep -RnE "https?://" projects/paper-trading/app/broker/kis_quote_mapper.py projects/paper-trading/app/domain/quote.py docs/kis/MISSING_MARKET_DATA_VALUES.md` 결과 0건.
7. `grep -RnE "TR_ID|tr_id|/uapi/|/oauth2/" projects/paper-trading/app/broker/kis_quote_mapper.py docs/kis/MISSING_MARKET_DATA_VALUES.md` 결과 0건.
8. `grep -RIn "PSNFD\|PKID\|AKIA\|sk-\|ghp_" projects/paper-trading/ docs/kis/` 결과 0건.
9. `MISSING_MARKET_DATA_VALUES.md`에 `Confirmed: yes` 부재, `<TBD>` 다수 존재.
10. `OrderType.MARKET` 부재 유지.
11. `git diff --stat`에 mvp-023 외 변경 없음.
12. `.env` staged/committed 없음.

## 6. 리뷰 체크리스트

- [ ] `app/domain/quote.py` 신규: frozen dataclass, broker-agnostic, app.config/app.broker import 0건.
- [ ] `Quote.spread_pct` Decimal 분율 정확 (`(ask-bid)/last`).
- [ ] `Quote.is_stale` timezone-aware check + 양방향 검증.
- [ ] `Quote.__post_init__`이 모든 invariant 검증.
- [ ] `app/broker/kis_quote_mapper.py` 신규: NotImplementedError + 입력 검증.
- [ ] `kis_quote_mapper.py`에 KIS URL/TR ID/HTTP 라이브러리 0건.
- [ ] `app/broker/kis.py` 본문 변경 0건 (새 파일만 추가).
- [ ] `docs/kis/MISSING_MARKET_DATA_VALUES.md` 신규: 4섹션, 모두 `<TBD>` + `Confirmed: no`, 실제 endpoint/키 0건.
- [ ] `Confirmed: yes` 부재 (사용자가 채울 자리).
- [ ] Quote 단위 테스트 12+ PASS.
- [ ] mapper fail-closed 테스트 3 PASS.
- [ ] 문서 검증 테스트 4 PASS.
- [ ] KIS get_quote 회귀 테스트 PASS (여전히 NotImplementedError).
- [ ] mvp-005~mvp-022 기존 테스트 회귀 0건.
- [ ] `app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/config.py`, `app/domain/{enums,orders,market}.py`, `app/broker/{base,paper,alpaca_paper,kis}.py`, `app/oms/`, `app/risk/`, `app/strategy/`, `app/runtime/`, `app/portfolio/`, `app/session/`, `app/reports/`, `app/static/`, `.env`, `.env.example`, 프로젝트/루트 `.gitignore` 변경 0건.
- [ ] mvp-001..mvp-022 산출물 미변경.
- [ ] `OrderType.MARKET` 부재 유지.
- [ ] live trading + market orders + KIS_ORDER_DRY_RUN 기본값 모두 유지.
- [ ] README에 mvp-023 단락 추가, 기존 단락 변경 없음.
- [ ] `git diff --stat`에 mvp-023 외 변경 없음.
- [ ] `.env` staged/committed 없음.
- [ ] commit/push/merge/deploy 자동화 없음.
- [ ] `patch.md` 5섹션 + Implementation Summary 8단락 완성, 보류 사유 명확.
