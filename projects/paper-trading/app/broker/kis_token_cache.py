"""KIS access token cache abstractions."""

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
    """Opt-in on-disk cache. Permission 0o600."""

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
        fd = os.open(str(self._path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)
        try:
            os.chmod(self._path, 0o600)
        except OSError:
            pass

    def clear(self) -> None:
        try:
            self._path.unlink()
        except FileNotFoundError:
            pass
