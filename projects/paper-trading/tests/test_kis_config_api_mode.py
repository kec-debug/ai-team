import pytest

from app.config import load_settings


def _write_env(tmp_path, content: str):
    env = tmp_path / ".env"
    env.write_text(content, encoding="utf-8")
    return env


def test_kis_api_mode_default_mock(tmp_path, monkeypatch):
    _write_env(tmp_path, "")
    monkeypatch.setattr("app.config._project_dir", lambda: tmp_path)
    monkeypatch.setattr("app.config.load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.delenv("KIS_API_MODE", raising=False)
    settings = load_settings()
    assert settings.kis_api_mode == "mock"


def test_kis_api_mode_paper_ok(tmp_path, monkeypatch):
    _write_env(tmp_path, "")
    monkeypatch.setattr("app.config._project_dir", lambda: tmp_path)
    monkeypatch.setattr("app.config.load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.setenv("KIS_API_MODE", "paper")
    settings = load_settings()
    assert settings.kis_api_mode == "paper"


def test_kis_api_mode_invalid_raises(tmp_path, monkeypatch):
    _write_env(tmp_path, "")
    monkeypatch.setattr("app.config._project_dir", lambda: tmp_path)
    monkeypatch.setattr("app.config.load_dotenv", lambda *args, **kwargs: False)
    monkeypatch.setenv("KIS_API_MODE", "production")
    with pytest.raises(ValueError):
        load_settings()
