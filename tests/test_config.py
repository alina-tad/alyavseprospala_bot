import pytest

from src.config import Config


def test_config_validation_ok(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "T")
    monkeypatch.setenv("OPENROUTER_API_KEY", "K")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    # не бросает исключение
    Config.validate()


def test_config_invalid_log_level(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "T")
    monkeypatch.setenv("OPENROUTER_API_KEY", "K")
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    with pytest.raises(ValueError):
        Config.validate()


def test_config_admin_check(monkeypatch):
    monkeypatch.setenv("ADMIN_USER_ID", "123")
    assert Config.is_admin(123) is True
    assert Config.is_admin(456) is False
