import os
import sys
import pytest

# Добавляем корень проекта в PYTHONPATH для импортов вида `from src...`
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch):
    """Изоляция переменных окружения для тестов."""
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TEST_TOKEN")
    monkeypatch.setenv("OPENROUTER_API_KEY", "TEST_OPENROUTER_KEY")
    monkeypatch.setenv("LLM_MODEL", "gpt-4")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    yield
