import os
import stat
from datetime import datetime, timedelta, timezone

from app.broker.kis_token_cache import FileTokenCache, InMemoryTokenCache, TokenRecord


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
