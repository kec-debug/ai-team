# Codex Task — api-auth-001: KIS OAuth 인증 + 토큰 캐시 + 안전 HTTP 래퍼 (mock/paper 기본)

## 0. 전제

- 상위 plan: `docs/ai/jobs/api-auth-001/plan.md` (모든 결정의 근거. 모호하면 plan 본문 인용).
- 자료: `uploads/3.xlsx` (OAuth 인증), `uploads/1.xlsx`, `4.xlsx`, `5.xlsx`, `6.xlsx`(국내/해외 헤더 구조). **본 codex-task에 필요한 모든 KIS 값은 본문에 박혀 있다. xlsx 재파싱 불요.**
- 사전 land: KIS_1 (시세 catalog) 완료. mvp-014-017 (KIS skeleton) 완료. 기존 ≈ 214 PASS.

### Hard rules (위반 시 BLOCK)

- KIS endpoint / TR ID / 헤더 / 응답 필드 **추측 금지**. 본 codex-task와 plan §2에 명시된 값만 사용.
- 실 app key / app secret / access token / 계좌번호 / refresh token **기록 금지**. 테스트에는 `"fake-key"`, `"fake-secret"`, `"fake-token"`, 계좌번호 8자리 이하 fake 숫자만.
- 외부 HTTP 라이브러리(`requests`, `httpx`, `aiohttp`, `urllib3`) import **금지**. `urllib.request`만 허용.
- `.env` 읽기/수정 **금지**. `.env.example`에는 변수 이름 + 한 줄 설명만 추가(값/placeholder 0건).
- `KisBroker`/`KisAccountClient`/`KisMarketDataClient` 본문 **변경 금지**. 여전히 `NotImplementedError`.
- live 모드 활성화 / 실주문 / 시장가 주문 / LLM 직접 호출 / RiskEngine 우회 **금지**.
- 자동 `git commit` / `push` / `merge` / `deploy` **금지**.
- 본 codex-task에서 허용하지 않은 path를 `SafeKisHttpClient.request`가 받으면 **거절**.

---

## §A. 신설 — `projects/paper-trading/app/broker/kis_token_cache.py`

```python
"""KIS access token cache abstractions.

Two implementations:
- ``InMemoryTokenCache``: per-process state, default.
- ``FileTokenCache``: opt-in, stores ``access_token`` + ``expires_at`` on disk
  with mode 0o600. Used only in paper mode and only when
  ``Settings.kis_token_cache_path`` is set.

No network calls. No third-party deps. stdlib only.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class TokenRecord:
    access_token: str
    expires_at: datetime
    issued_at: datetime

    def is_expiring_soon(self, safety_seconds: int) -> bool:
        threshold = datetime.now(timezone.utc).timestamp() + max(0, safety_seconds)
        return self.expires_at.timestamp() <= threshold

    def expires_in_seconds(self) -> int:
        remaining = int(self.expires_at.timestamp() - datetime.now(timezone.utc).timestamp())
        return max(0, remaining)


class TokenCache(Protocol):
    def get(self) -> TokenRecord | None: ...
    def set(self, record: TokenRecord) -> None: ...
    def clear(self) -> None: ...


@dataclass
class InMemoryTokenCache:
    _record: TokenRecord | None = field(default=None)

    def get(self) -> TokenRecord | None:
        if self._record is None:
            return None
        if self._record.is_expiring_soon(0):
            return None
        return self._record

    def set(self, record: TokenRecord) -> None:
        self._record = record

    def clear(self) -> None:
        self._record = None


class FileTokenCache:
    """Opt-in on-disk cache. Permission 0o600. paper mode only."""

    def __init__(self, path: str | os.PathLike[str]) -> None:
        self._path = Path(path)

    def get(self) -> TokenRecord | None:
        try:
            text = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        try:
            data = json.loads(text)
            access_token = str(data["access_token"])
            expires_at = datetime.fromisoformat(data["expires_at"])
            issued_at = datetime.fromisoformat(data["issued_at"])
        except (json.JSONDecodeError, KeyError, ValueError, TypeError):
            self.clear()
            return None
        record = TokenRecord(access_token=access_token, expires_at=expires_at, issued_at=issued_at)
        if record.is_expiring_soon(0):
            return None
        return record

    def set(self, record: TokenRecord) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "access_token": record.access_token,
            "expires_at": record.expires_at.isoformat(),
            "issued_at": record.issued_at.isoformat(),
        }
        # Write with 0600 from the start to avoid a window with broader perms.
        fd = os.open(str(self._path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh)
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass
            raise
        # Re-assert perms in case umask altered them (defensive).
        try:
            os.chmod(self._path, 0o600)
        except OSError:
            pass

    def clear(self) -> None:
        try:
            self._path.unlink()
        except FileNotFoundError:
            pass
```

---

## §B. 신설 — `projects/paper-trading/app/broker/kis_http.py`

```python
"""KIS HTTP safe wrapper.

- Mode-aware: ``mock`` (no network), ``paper`` (real HTTP to paper host
  allowlist only), ``live`` (rejected at construction by api-auth-001).
- Path allowlist: only ``/oauth2/tokenP`` and ``/oauth2/revokeP`` in this job.
  Other paths are rejected to keep api-auth-001 scope tight; later jobs widen
  this list per their plans.
- Host allowlist: paper base URL only.
- No third-party deps. stdlib ``urllib.request`` only.
- Sanitizes outgoing header trace + parses JSON safely.
"""

from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from app.config import Settings
from app.broker.kis_token_cache import TokenCache


class KisApiMode(str, Enum):
    MOCK = "mock"
    PAPER = "paper"
    LIVE = "live"

    @classmethod
    def parse(cls, raw: str | None) -> "KisApiMode":
        if raw is None or raw == "":
            return cls.MOCK
        try:
            return cls(raw)
        except ValueError as exc:
            raise ValueError(f"invalid KIS_API_MODE: {raw!r}") from exc


PAPER_HOST_ALLOWLIST: frozenset[str] = frozenset({
    "openapivts.koreainvestment.com:29443",
})

ALLOWED_PATHS_API_AUTH_001: frozenset[str] = frozenset({
    "/oauth2/tokenP",
    "/oauth2/revokeP",
})


class KisHttpError(Exception):
    """Safe wrapper for KIS HTTP failures."""


class KisAuthError(Exception):
    """Authentication / token error."""


class KisHttpTransport(Protocol):
    def request(self, method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None) -> dict[str, Any]: ...


@dataclass
class MockTransport:
    """Mock-mode transport: any request raises immediately."""

    def request(self, method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None) -> dict[str, Any]:
        raise KisAuthError("mock_mode_no_network")


@dataclass
class UrllibTransport:
    """Paper-only transport using stdlib urllib.

    Host allowlist enforced. Timeout enforced.
    Retries on 5xx / connection errors per ``max_retries``.
    """

    timeout_seconds: float = 5.0
    max_retries: int = 1
    backoff_seconds: float = 2.0

    def request(self, method: str, url: str, headers: dict[str, str], payload: dict[str, Any] | None) -> dict[str, Any]:
        host = _extract_host(url)
        if host not in PAPER_HOST_ALLOWLIST:
            raise KisAuthError("disallowed_host")
        data: bytes | None = None
        if payload is not None:
            if method != "POST":
                raise KisHttpError("body_only_allowed_on_post")
            data = json.dumps(payload).encode("utf-8")
        attempts = 0
        last_error: Exception | None = None
        while attempts <= self.max_retries:
            attempts += 1
            try:
                req = Request(url=url, data=data, headers=headers, method=method)
                with urlopen(req, timeout=self.timeout_seconds) as resp:
                    body = resp.read()
                try:
                    return json.loads(body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    raise KisHttpError("invalid_response_body") from exc
            except HTTPError as exc:
                if exc.code >= 500 and attempts <= self.max_retries:
                    last_error = exc
                    time.sleep(self.backoff_seconds)
                    continue
                raise KisHttpError(f"http_{exc.code}") from exc
            except (URLError, TimeoutError, socket.timeout) as exc:
                if attempts <= self.max_retries:
                    last_error = exc
                    time.sleep(self.backoff_seconds)
                    continue
                raise KisHttpError("transport_error") from exc
        raise KisHttpError("transport_error_after_retries") from last_error


def _extract_host(url: str) -> str:
    if "://" not in url:
        return ""
    rest = url.split("://", 1)[1]
    host = rest.split("/", 1)[0]
    return host


class SafeKisHttpClient:
    """Mode-aware safe wrapper. Constructed per Settings."""

    def __init__(
        self,
        settings: Settings,
        token_cache: TokenCache,
        transport: KisHttpTransport | None = None,
    ) -> None:
        mode = KisApiMode.parse(settings.kis_api_mode)
        if mode is KisApiMode.LIVE:
            raise KisConfigError("live_mode_not_supported_yet")
        if (settings.kis_env or "").lower() == "live":
            raise KisConfigError("live_mode_not_supported_yet")
        self._settings = settings
        self._cache = token_cache
        self._mode = mode
        if transport is not None:
            self._transport = transport
        elif mode is KisApiMode.MOCK:
            self._transport = MockTransport()
        else:
            self._transport = UrllibTransport(
                timeout_seconds=settings.kis_oauth_timeout_seconds,
                max_retries=settings.kis_oauth_max_retries,
            )

    @property
    def mode(self) -> KisApiMode:
        return self._mode

    def request(self, method: str, path: str, headers: dict[str, str], payload: dict[str, Any] | None) -> dict[str, Any]:
        if path not in ALLOWED_PATHS_API_AUTH_001:
            raise KisHttpError("path_not_allowed_by_api_auth_001")
        url = self._base_url() + path
        safe_headers = dict(headers)
        return self._transport.request(method=method, url=url, headers=safe_headers, payload=payload)

    def _base_url(self) -> str:
        return self._settings.kis_base_url_paper


class KisConfigError(Exception):
    """Configuration missing or invalid."""
```

> 참고: `KisConfigError`는 기존 `app/broker/kis.py`에도 같은 이름이 있다. 본 모듈에서는 **재정의 대신 import**가 깔끔하다. Codex는 위 코드의 `KisConfigError` 클래스 정의를 **삭제**하고 파일 상단에 `from app.broker.kis import KisConfigError, KisAuthError, KisHttpError` 형태로 변경해도 좋다. 단, `KisAuthError`/`KisHttpError`를 본 파일에서 사용 중이라 import로 옮기면 양쪽 파일의 정의가 충돌하지 않게 한쪽만 정본이어야 한다. 권장: **kis_http.py의 `KisAuthError`/`KisHttpError`/`KisConfigError` 정의를 모두 삭제하고 `from app.broker.kis import ...`로 import**. (kis.py 쪽 정의가 더 오래된 정본.)

---

## §C. 수정 — `projects/paper-trading/app/broker/kis.py`

다음 변경만 적용. 다른 라인은 손대지 말 것.

### C.1 import 추가 (파일 상단)

```python
from app.broker.kis_http import (
    ALLOWED_PATHS_API_AUTH_001,
    KisApiMode,
    SafeKisHttpClient,
)
from app.broker.kis_token_cache import (
    FileTokenCache,
    InMemoryTokenCache,
    TokenCache,
    TokenRecord,
)
```

### C.2 `KisAuthClient.__init__` 교체

기존 시그니처 보존(`settings: Settings`)하되 옵셔널 인자 2개 추가. 외부 호출자(기존 테스트)는 영향 없음.

```python
def __init__(
    self,
    settings: Settings,
    http: SafeKisHttpClient | None = None,
    token_cache: TokenCache | None = None,
) -> None:
    if not settings.kis_app_key or not settings.kis_app_secret:
        raise KisConfigError("KIS_APP_KEY / KIS_APP_SECRET missing in .env")
    self._settings = settings
    if token_cache is None:
        if settings.kis_token_cache_path:
            token_cache = FileTokenCache(settings.kis_token_cache_path)
        else:
            token_cache = InMemoryTokenCache()
    self._cache: TokenCache = token_cache
    if http is None:
        http = SafeKisHttpClient(settings=settings, token_cache=token_cache)
    self._http = http
    self._access_token: str | None = None
    self._expires_at: datetime | None = None
    self._last_error: str | None = None
```

> 기존 `self._http = KisHttpClient(settings)` 라인은 위 블록으로 대체. `KisHttpClient`(기존 클래스)는 그대로 두되, 본 KisAuthClient는 더 이상 사용하지 않는다.

### C.3 `authenticate()` 본문 교체

```python
def authenticate(self) -> None:
    try:
        _validate_paper_settings(self._settings)
    except KisOrderRejectedError as exc:
        self._last_error = exc.reason
        raise KisAuthError(exc.reason) from exc
    mode = KisApiMode.parse(self._settings.kis_api_mode)
    if mode is KisApiMode.MOCK:
        self._last_error = "mock_mode_no_network"
        raise KisAuthError("mock_mode_no_network")
    cached = self._cache.get()
    safety = max(0, self._settings.kis_token_expiry_safety_seconds)
    if cached is not None and not cached.is_expiring_soon(safety):
        self._store_token(cached.access_token, cached.expires_in_seconds())
        return
    body = {
        "grant_type": "client_credentials",
        "appkey": self._settings.kis_app_key,
        "appsecret": self._settings.kis_app_secret,
    }
    headers = {"content-type": "application/json; charset=utf-8"}
    try:
        response = self._http.request("POST", "/oauth2/tokenP", headers=headers, payload=body)
    except (KisAuthError, KisHttpError) as exc:
        self._last_error = str(exc)
        raise
    access_token = response.get("access_token")
    token_type = response.get("token_type")
    expires_in = response.get("expires_in")
    if not isinstance(access_token, str) or not access_token:
        self._last_error = "invalid_token_response"
        raise KisAuthError("invalid_token_response")
    if token_type != "Bearer":
        self._last_error = "invalid_token_type"
        raise KisAuthError("invalid_token_type")
    if not isinstance(expires_in, int) or expires_in <= 0:
        self._last_error = "invalid_expires_in"
        raise KisAuthError("invalid_expires_in")
    self._store_token(access_token, int(expires_in))
    now = datetime.now(timezone.utc)
    assert self._expires_at is not None
    self._cache.set(TokenRecord(access_token=access_token, expires_at=self._expires_at, issued_at=now))
```

### C.4 `refresh_token()` 본문 교체

```python
def refresh_token(self) -> None:
    try:
        _validate_paper_settings(self._settings)
    except KisOrderRejectedError as exc:
        self._last_error = exc.reason
        raise KisAuthError(exc.reason) from exc
    self.clear_token()
    self._cache.clear()
    self.authenticate()
```

### C.5 새 메서드 `revoke()` 추가

```python
def revoke(self) -> None:
    try:
        _validate_paper_settings(self._settings)
    except KisOrderRejectedError as exc:
        self._last_error = exc.reason
        raise KisAuthError(exc.reason) from exc
    token = self._access_token
    if not token:
        self._cache.clear()
        return
    body = {
        "appkey": self._settings.kis_app_key,
        "appsecret": self._settings.kis_app_secret,
        "token": token,
    }
    headers = {"content-type": "application/json; charset=utf-8"}
    try:
        self._http.request("POST", "/oauth2/revokeP", headers=headers, payload=body)
    finally:
        self.clear_token()
        self._cache.clear()
```

### C.6 다른 함수/클래스 변경 금지

`sanitize_kis_response`, `validate_kis_order_request`, `KisAccountClient`, `KisMarketDataClient`, `KisBroker`, `KisHttpClient`(기존), 모든 dataclass: **본문 라인 단 하나도 수정 금지.** SENSITIVE_RESPONSE_KEYS 집합도 변경 금지(이미 충분).

---

## §D. 수정 — `projects/paper-trading/app/config.py`

`Settings` dataclass에 다음 필드 추가(기존 필드 뒤에). 모두 안전 기본값.

```python
kis_api_mode: str = "mock"
kis_base_url_paper: str = "https://openapivts.koreainvestment.com:29443"
kis_base_url_live: str = "https://openapi.koreainvestment.com:9443"
kis_oauth_timeout_seconds: float = 5.0
kis_oauth_max_retries: int = 1
kis_token_expiry_safety_seconds: int = 60
kis_token_cache_path: str | None = field(default=None, repr=False)
```

`load_settings()`에 다음 read 라인 추가:

```python
kis_api_mode=_str_env("KIS_API_MODE") or "mock",
kis_base_url_paper=_str_env("KIS_BASE_URL_PAPER") or "https://openapivts.koreainvestment.com:29443",
kis_base_url_live=_str_env("KIS_BASE_URL_LIVE") or "https://openapi.koreainvestment.com:9443",
kis_oauth_timeout_seconds=float(_str_env("KIS_OAUTH_TIMEOUT_SECONDS") or "5.0"),
kis_oauth_max_retries=int(_str_env("KIS_OAUTH_MAX_RETRIES") or "1"),
kis_token_expiry_safety_seconds=int(_str_env("KIS_TOKEN_EXPIRY_SAFETY_SECONDS") or "60"),
kis_token_cache_path=_str_env("KIS_TOKEN_CACHE_PATH"),
```

`KIS_API_MODE` 값 검증을 `load_settings()` 직후에 추가:

```python
if kis_api_mode not in {"mock", "paper", "live"}:
    raise ValueError(f"invalid KIS_API_MODE: {kis_api_mode!r}")
```

(코드 흐름에 맞게 변수 캡처 후 검증. 라인 추가만, 기존 라인 삭제 금지.)

---

## §E. 수정 — `.env.example`

다음 블록을 파일 끝에 추가. **값/placeholder 0건**. 이름과 한 줄 설명만.

```
# --- KIS Open API (api-auth-001) ---
# KIS_API_MODE      one of: mock | paper | live (default mock; live blocked in api-auth-001)
# KIS_APP_KEY       KIS Open API app key (issued at KIS Developers portal)
# KIS_APP_SECRET    KIS Open API app secret (issued at KIS Developers portal)
# KIS_BASE_URL_PAPER     optional override (default: official paper host)
# KIS_BASE_URL_LIVE      optional override (default: official live host; not used by api-auth-001)
# KIS_OAUTH_TIMEOUT_SECONDS         optional, default 5.0
# KIS_OAUTH_MAX_RETRIES             optional, default 1
# KIS_TOKEN_EXPIRY_SAFETY_SECONDS   optional, default 60
# KIS_TOKEN_CACHE_PATH              optional; when set, on-disk token cache (0600). paper mode only.
```

기존 라인은 변경 금지.

---

## §F. 신설 테스트 — 본문 골격

### F.1 `tests/test_kis_api_mode.py`

```python
import pytest

from app.broker.kis_http import KisApiMode


def test_default_is_mock():
    assert KisApiMode.parse(None) is KisApiMode.MOCK
    assert KisApiMode.parse("") is KisApiMode.MOCK


def test_valid_modes():
    assert KisApiMode.parse("mock") is KisApiMode.MOCK
    assert KisApiMode.parse("paper") is KisApiMode.PAPER
    assert KisApiMode.parse("live") is KisApiMode.LIVE


def test_invalid_mode_raises():
    with pytest.raises(ValueError):
        KisApiMode.parse("production")
```

### F.2 `tests/test_kis_token_cache.py`

```python
import json
import os
import stat
from datetime import datetime, timedelta, timezone

import pytest

from app.broker.kis_token_cache import (
    FileTokenCache,
    InMemoryTokenCache,
    TokenRecord,
)


def _record(offset_seconds: int = 3600) -> TokenRecord:
    now = datetime.now(timezone.utc)
    return TokenRecord(
        access_token="fake-token",
        expires_at=now + timedelta(seconds=offset_seconds),
        issued_at=now,
    )


def test_in_memory_set_get_clear():
    cache = InMemoryTokenCache()
    assert cache.get() is None
    rec = _record()
    cache.set(rec)
    assert cache.get() == rec
    cache.clear()
    assert cache.get() is None


def test_in_memory_returns_none_for_expired():
    cache = InMemoryTokenCache()
    cache.set(_record(offset_seconds=-10))
    assert cache.get() is None


def test_file_cache_writes_with_0600_perms(tmp_path):
    path = tmp_path / "token.json"
    cache = FileTokenCache(path)
    cache.set(_record())
    perms = stat.S_IMODE(os.stat(path).st_mode)
    assert perms == 0o600


def test_file_cache_roundtrip(tmp_path):
    path = tmp_path / "token.json"
    cache = FileTokenCache(path)
    rec = _record()
    cache.set(rec)
    got = cache.get()
    assert got is not None
    assert got.access_token == rec.access_token


def test_file_cache_invalid_json_self_heals(tmp_path):
    path = tmp_path / "token.json"
    path.write_text("not json", encoding="utf-8")
    cache = FileTokenCache(path)
    assert cache.get() is None
    assert not path.exists()


def test_file_cache_clear(tmp_path):
    path = tmp_path / "token.json"
    cache = FileTokenCache(path)
    cache.set(_record())
    cache.clear()
    assert not path.exists()
```

### F.3 `tests/test_kis_http_transport.py`

```python
import pytest

from app.broker.kis_http import (
    ALLOWED_PATHS_API_AUTH_001,
    KisApiMode,
    MockTransport,
    SafeKisHttpClient,
    UrllibTransport,
)
from app.broker.kis import KisAuthError, KisHttpError, KisConfigError
from app.broker.kis_token_cache import InMemoryTokenCache


def test_mock_transport_blocks_network():
    t = MockTransport()
    with pytest.raises(KisAuthError, match="mock_mode_no_network"):
        t.request("POST", "https://openapivts.koreainvestment.com:29443/oauth2/tokenP", {}, {"a": 1})


def test_urllib_transport_rejects_disallowed_host():
    t = UrllibTransport()
    with pytest.raises(KisAuthError, match="disallowed_host"):
        t.request("POST", "https://evil.example.com/oauth2/tokenP", {}, {})


def test_safe_client_rejects_unknown_path(settings):
    s = _paper_settings(settings)
    cache = InMemoryTokenCache()
    client = SafeKisHttpClient(settings=s, token_cache=cache, transport=MockTransport())
    with pytest.raises(KisHttpError, match="path_not_allowed_by_api_auth_001"):
        client.request("POST", "/uapi/some/other/path", {}, {})


def test_safe_client_blocks_live_mode(settings):
    s = _paper_settings(settings)
    s = _replace_live(s)
    with pytest.raises(KisConfigError, match="live_mode_not_supported_yet"):
        SafeKisHttpClient(settings=s, token_cache=InMemoryTokenCache())


def test_allowed_paths_are_just_two():
    assert ALLOWED_PATHS_API_AUTH_001 == frozenset({"/oauth2/tokenP", "/oauth2/revokeP"})


# helpers ------------------------------------------------------------
from dataclasses import replace


def _paper_settings(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
        kis_api_mode="paper",
    )


def _replace_live(s):
    return replace(s, kis_api_mode="live")
```

### F.4 `tests/test_kis_auth_client_http.py`

```python
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone

import pytest

from app.broker.kis import KisAuthClient, KisAuthError
from app.broker.kis_http import KisHttpTransport, SafeKisHttpClient
from app.broker.kis_token_cache import InMemoryTokenCache


def _paper_settings(settings):
    return replace(
        settings,
        kis_env="paper",
        kis_app_key="fake-key",
        kis_app_secret="fake-secret",
        kis_api_mode="paper",
    )


def _mock_settings(settings):
    return replace(_paper_settings(settings), kis_api_mode="mock")


@dataclass
class FakeTransport:
    response: dict
    calls: list = field(default_factory=list)
    raises: Exception | None = None

    def request(self, method, url, headers, payload):
        self.calls.append({"method": method, "url": url, "path": url.split(":29443", 1)[-1], "payload": dict(payload or {})})
        if self.raises:
            raise self.raises
        return dict(self.response)


def _make_client(settings_obj, transport):
    cache = InMemoryTokenCache()
    http = SafeKisHttpClient(settings=settings_obj, token_cache=cache, transport=transport)
    return KisAuthClient(settings=settings_obj, http=http, token_cache=cache), cache


def test_authenticate_mock_mode_fail_closed(settings):
    s = _mock_settings(settings)
    cache = InMemoryTokenCache()
    http = SafeKisHttpClient(settings=s, token_cache=cache)
    auth = KisAuthClient(settings=s, http=http, token_cache=cache)
    with pytest.raises(KisAuthError, match="mock_mode_no_network"):
        auth.authenticate()


def test_authenticate_paper_happy_path(settings):
    s = _paper_settings(settings)
    transport = FakeTransport(response={
        "access_token": "fake-token-abc",
        "token_type": "Bearer",
        "expires_in": 86400,
    })
    auth, cache = _make_client(s, transport)
    auth.authenticate()
    assert auth.is_authenticated()
    assert auth.get_access_token() == "fake-token-abc"
    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/oauth2/tokenP")
    assert call["payload"]["grant_type"] == "client_credentials"
    assert call["payload"]["appkey"] == "fake-key"


def test_authenticate_rejects_missing_access_token(settings):
    s = _paper_settings(settings)
    transport = FakeTransport(response={"token_type": "Bearer", "expires_in": 86400})
    auth, _ = _make_client(s, transport)
    with pytest.raises(KisAuthError, match="invalid_token_response"):
        auth.authenticate()


def test_authenticate_rejects_wrong_token_type(settings):
    s = _paper_settings(settings)
    transport = FakeTransport(response={"access_token": "x", "token_type": "basic", "expires_in": 86400})
    auth, _ = _make_client(s, transport)
    with pytest.raises(KisAuthError, match="invalid_token_type"):
        auth.authenticate()


def test_authenticate_rejects_bad_expires_in(settings):
    s = _paper_settings(settings)
    transport = FakeTransport(response={"access_token": "x", "token_type": "Bearer", "expires_in": "soon"})
    auth, _ = _make_client(s, transport)
    with pytest.raises(KisAuthError, match="invalid_expires_in"):
        auth.authenticate()


def test_authenticate_uses_cache_on_second_call(settings):
    s = _paper_settings(settings)
    transport = FakeTransport(response={"access_token": "x", "token_type": "Bearer", "expires_in": 86400})
    auth, cache = _make_client(s, transport)
    auth.authenticate()
    auth.clear_token()  # local state cleared but cache stays
    auth.authenticate()
    assert len(transport.calls) == 1  # second call served from cache


def test_revoke_clears_local_and_cache(settings):
    s = _paper_settings(settings)
    transport = FakeTransport(response={"access_token": "x", "token_type": "Bearer", "expires_in": 86400})
    auth, cache = _make_client(s, transport)
    auth.authenticate()
    transport.response = {"code": 200, "message": "ok"}
    auth.revoke()
    assert auth.is_authenticated() is False
    assert cache.get() is None
    revoke_calls = [c for c in transport.calls if c["url"].endswith("/oauth2/revokeP")]
    assert len(revoke_calls) == 1
```

### F.5 `tests/test_kis_config_api_mode.py`

```python
import pytest

from app.config import load_settings


def _write_env(tmp_path, content: str):
    env = tmp_path / ".env"
    env.write_text(content, encoding="utf-8")
    return env


def test_kis_api_mode_default_mock(tmp_path, monkeypatch):
    _write_env(tmp_path, "")
    monkeypatch.setattr("app.config._project_dir", lambda: tmp_path)
    monkeypatch.setattr("app.config.load_dotenv", lambda *a, **k: False)
    monkeypatch.delenv("KIS_API_MODE", raising=False)
    s = load_settings()
    assert s.kis_api_mode == "mock"


def test_kis_api_mode_paper_ok(tmp_path, monkeypatch):
    _write_env(tmp_path, "")
    monkeypatch.setattr("app.config._project_dir", lambda: tmp_path)
    monkeypatch.setattr("app.config.load_dotenv", lambda *a, **k: False)
    monkeypatch.setenv("KIS_API_MODE", "paper")
    s = load_settings()
    assert s.kis_api_mode == "paper"


def test_kis_api_mode_invalid_raises(tmp_path, monkeypatch):
    _write_env(tmp_path, "")
    monkeypatch.setattr("app.config._project_dir", lambda: tmp_path)
    monkeypatch.setattr("app.config.load_dotenv", lambda *a, **k: False)
    monkeypatch.setenv("KIS_API_MODE", "production")
    with pytest.raises(ValueError):
        load_settings()
```

### F.6 `tests/test_kis_http_boundaries.py` 확장

기존 파일에 다음 단정 추가(별 함수로):

```python
import pathlib


def test_kis_modules_do_not_import_third_party_http_libs():
    broker_dir = pathlib.Path(__file__).resolve().parents[1] / "app" / "broker"
    forbidden = ("import requests", "import httpx", "import aiohttp", "import urllib3", "from requests", "from httpx", "from aiohttp")
    for fp in broker_dir.glob("kis*.py"):
        text = fp.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in text, f"{fp.name}: {needle}"


def test_kis_http_has_no_live_transport_class():
    src = (pathlib.Path(__file__).resolve().parents[1] / "app" / "broker" / "kis_http.py").read_text(encoding="utf-8")
    assert "LiveTransport" not in src
    assert "class Live" not in src
```

### F.7 `tests/test_kis_auth_client.py` (기존 보존)

기존 5개 테스트 변경 금지. 새 케이스 1개 추가:

```python
def test_auth_client_default_uses_in_memory_cache(settings):
    auth = KisAuthClient(_settings(settings))
    # internal sanity — implementation detail but key invariant for api-auth-001
    from app.broker.kis_token_cache import InMemoryTokenCache
    assert isinstance(auth._cache, InMemoryTokenCache)  # type: ignore[attr-defined]
```

---

## §G. README 단락

`projects/paper-trading/README.md` 끝에 다음 단락만 추가. 기존 단락 변경 금지.

```markdown
## API 인증 (api-auth-001)

KIS Open API의 OAuth 토큰 발급/폐기와 안전 HTTP 래퍼를 제공합니다.

- 기본 모드 `KIS_API_MODE=mock`: 네트워크 호출 없음. `KisAuthClient.authenticate()`는 즉시 `KisAuthError`.
- `KIS_API_MODE=paper`로 설정하고 `KIS_APP_KEY`/`KIS_APP_SECRET`을 `.env`에 두면 `https://openapivts.koreainvestment.com:29443`의 `/oauth2/tokenP`만 호출 가능.
- `KIS_API_MODE=live`는 api-auth-001 범위에서 fail-closed (`KisConfigError`).
- 토큰은 메모리 캐시가 기본. `KIS_TOKEN_CACHE_PATH`를 설정하면 0600 권한 JSON 파일로 캐시 (paper 한정).
- 본 작업은 시세/주문 호출 본문을 추가하지 않습니다. 후속 job 참고.
```

---

## §H. 적용 절차

1. §A, §B의 신규 파일 작성.
2. §C에 따라 `app/broker/kis.py` 수정 (지정 메서드만).
3. §D에 따라 `app/config.py` 수정.
4. §E에 따라 `.env.example` 끝에 한 블록 추가.
5. §F의 신규 테스트 파일 작성 + 기존 테스트 확장.
6. §G에 따라 README 단락 추가.
7. 안전 grep:
   ```bash
   cd /root/ai-dev-center/projects/ai-team/projects/paper-trading
   git diff --stat
   git diff -- app/ tests/ .env.example README.md \
     | grep -E "PSNFD|PKID|AKIA|sk-|ghp_|Bearer eyJ|appkey=|appsecret=|\b\d{10,}\b|import requests|import httpx|import aiohttp|import urllib3|class Live|LiveTransport" \
     || echo "safety-grep: clean"
   ```
   `safety-grep: clean` 이 출력되어야 함.
8. 테스트:
   ```bash
   .venv/bin/python -m compileall app tests
   .venv/bin/python -m pytest -p no:cacheprovider
   ```
   - 기존 ≈ 214 + 신규 ≈ 20+ 모두 PASS.
   - 외부 네트워크 호출 0건(테스트가 fake transport와 stdlib 격리만 사용).
9. `docs/ai/jobs/api-auth-001/patch.md` 작성. 다음 8개 섹션:
   - Implementation Summary
   - 변경 파일 목록(plan §3과 일치)
   - 신규/수정 클래스/함수 요약
   - 안전 grep 결과 (위 패턴 × 0건 확인)
   - 테스트 결과 (전체 PASS 수치)
   - `compileall` 결과
   - 정책/안전 invariant 확인 (live fail-closed, mock 기본, path allowlist, 외부 lib 0건)
   - commit/push/merge 미실행 확인
10. `git commit` / `push` / `merge` / 배포 **미실행**.

---

## §I. Codex가 절대 하지 말아야 할 것 (반복)

- `KisBroker` / `KisAccountClient` / `KisMarketDataClient` 본문 변경.
- `OrderType.MARKET` 추가 또는 `ALLOW_MARKET_ORDERS` 기본값 변경.
- `KIS_ORDER_DRY_RUN` 기본값 변경.
- `LiveTransport` 또는 `class Live*` 작성.
- `requests`/`httpx`/`aiohttp`/`urllib3` import.
- `.env` 읽기/수정.
- `.env.example`에 실 키/placeholder/예시값 작성.
- 사용자 app key/secret/계좌번호/token을 어떤 코드/주석/문서/테스트에도 기록.
- 실제 KIS 호스트로 네트워크 호출하는 테스트.
- 자동 git commit/push/merge/deploy.
- 본 codex-task에 없는 추가 endpoint/path/TR_ID를 도입.
- `docs/kis/MISSING_*` 변경.
- `app/api/server.py`, `app/api/routes.py`, `app/main.py`, `app/static/*`, `app/oms/*`, `app/risk/*`, `app/strategy/*` 변경.

## §J. 완료 조건

- §A~§G의 파일이 본 codex-task 본문과 일치하게 작성됨.
- 안전 grep clean.
- 전체 pytest PASS, compileall 무오류.
- `patch.md`에 §H.9의 8개 섹션 기록.
- 사람이 직접 staging/commit하도록 변경만 남기고 종료.
