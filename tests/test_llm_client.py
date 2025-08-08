import types
import pytest

from src.llm import LLMClient
from src.config import Config


class DummyChoice:
    def __init__(self, content: str, finish_reason: str | None = None):
        self.message = types.SimpleNamespace(content=content)
        self.finish_reason = finish_reason


class DummyResponse:
    def __init__(self, content: str, finish_reason: str | None = None):
        self.choices = [DummyChoice(content, finish_reason)]
        self.usage = types.SimpleNamespace(prompt_tokens=10, completion_tokens=20, total_tokens=30)


class DummyCompletions:
    def create(self, *, model: str, messages: list, max_tokens: int, temperature: float):
        # имитируем: primary сначала вернет "сухой" ответ, потом при fallback нормальный
        if model == Config.LLM_PRIMARY_MODEL:
            return DummyResponse("коротко и сухо", finish_reason="stop")
        # fallback
        return DummyResponse("Ответ с нужной структурой и ключевые символы: ...")


class DummyClient:
    def __init__(self):
        self.chat = types.SimpleNamespace(completions=DummyCompletions())


@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "T")
    monkeypatch.setenv("OPENROUTER_API_KEY", "K")
    monkeypatch.setenv("LLM_PRIMARY_MODEL", "gpt-4")
    monkeypatch.setenv("LLM_FALLBACK_ENABLED", "true")
    monkeypatch.setenv("LLM_FALLBACK_MODELS", "gpt-4o-mini")


@pytest.mark.asyncio
async def test_llm_fallback(monkeypatch):
    # подменяем OpenAI клиента на заглушку
    from src import llm as llm_module
    monkeypatch.setattr(llm_module, "OpenAI", lambda base_url, api_key: DummyClient())

    client = LLMClient()
    messages = [{"role": "user", "content": "расскажи про сон..."}]
    text, meta = await client.generate_with_fallback(messages)

    assert "ключевые символы" in text.lower()
    assert meta.get("fallback") in (True, False)  # может быть выставлен
