"""KIS HTTP safe wrapper for api-auth-001."""

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


class KisConfigError(Exception):
    """Configuration missing or invalid."""


class KisAuthError(Exception):
    """Authentication / token error."""


class KisHttpError(Exception):
    """Safe wrapper for KIS HTTP failures."""


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


class KisHttpTransport(Protocol):
    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any] | None,
    ) -> dict[str, Any]: ...


@dataclass
class MockTransport:
    """Mock-mode transport: any request raises immediately."""

    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        raise KisAuthError("mock_mode_no_network")


@dataclass
class UrllibTransport:
    """Paper-only transport using stdlib urllib."""

    timeout_seconds: float = 5.0
    max_retries: int = 1
    backoff_seconds: float = 2.0

    def request(
        self,
        method: str,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
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
                    response = json.loads(body.decode("utf-8"))
                except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                    raise KisHttpError("invalid_response_body") from exc
                if isinstance(response, dict) and response.get("rt_cd") not in (None, "0"):
                    raise KisHttpError(str(response.get("msg_cd") or response.get("msg1") or "kis_error"))
                if not isinstance(response, dict):
                    raise KisHttpError("invalid_response_body")
                return response
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
    return rest.split("/", 1)[0]


class SafeKisHttpClient:
    """Mode-aware safe wrapper constructed per Settings."""

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

    def request(
        self,
        method: str,
        path: str,
        headers: dict[str, str],
        payload: dict[str, Any] | None,
    ) -> dict[str, Any]:
        if path not in ALLOWED_PATHS_API_AUTH_001:
            raise KisHttpError("path_not_allowed_by_api_auth_001")
        url = self._base_url() + path
        return self._transport.request(method=method, url=url, headers=dict(headers), payload=payload)

    def _base_url(self) -> str:
        return self._settings.kis_base_url_paper.rstrip("/")
