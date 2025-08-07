import logging
import asyncio
import os
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from .config import Config

logger = logging.getLogger(__name__)

class LLMClient:
    """Клиент для работы с LLM через OpenRouter"""
    
    def __init__(self):
        """Инициализация клиента LLM"""
        self.client = OpenAI(
            base_url=Config.LLM_BASE_URL,
            api_key=Config.OPENROUTER_API_KEY
        )
        logger.info(f"LLM клиент инициализирован с моделью {Config.LLM_PRIMARY_MODEL}")
        try:
            fallbacks_for_log = Config.get_fallback_models() if Config.LLM_FALLBACK_ENABLED else []
        except Exception:
            fallbacks_for_log = []
        logger.info(f"LLM primary: {Config.LLM_PRIMARY_MODEL}; fallbacks: {fallbacks_for_log}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,))
    )
    async def get_response(self, messages: list) -> str:
        """Получение ответа от LLM с retry логикой"""
        try:
            logger.info(f"Отправка запроса к LLM, модель: {Config.LLM_PRIMARY_MODEL}")
            
            response = self.client.chat.completions.create(
                model=Config.LLM_PRIMARY_MODEL,
                messages=messages,
                max_tokens=Config.LLM_MAX_TOKENS,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            logger.info(f"Получен ответ от LLM: {len(response_text)} символов")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Ошибка при обращении к LLM: {e}")
            raise  # Пробрасываем исключение для retry

    async def get_response_with_model(self, model: str, messages: list) -> tuple[str, dict]:
        """Отправить запрос в указанную модель; вернуть (text, meta)"""
        logger.info(f"Отправка запроса к LLM, модель: {model}")
        response = self.client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=Config.LLM_MAX_TOKENS,
            temperature=0.7
        )
        response_text = response.choices[0].message.content
        finish_reason = getattr(response.choices[0], "finish_reason", None)
        usage = getattr(response, "usage", None)
        meta = {
            "model": model,
            "fallback": False,
            "finish_reason": finish_reason,
            "continued": False,
            "continuations": 0,
        }
        if usage:
            # OpenAI совместимое поле может отсутствовать у некоторых роутов
            meta["usage"] = {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            }
        logger.info(f"Получен ответ от LLM: {len(response_text)} символов")
        # Автопродолжение, если обрезано по длине
        if finish_reason == "length":
            try:
                augmented_messages = list(messages)
                augmented_messages.append({"role": "assistant", "content": response_text})
                augmented_messages.append({
                    "role": "user",
                    "content": "Продолжи предыдущий ответ кратко (1 абзац). Не повторяй уже сказанное."
                })
                for i in range(2):  # максимум 2 догенерации
                    cont = self.client.chat.completions.create(
                        model=model,
                        messages=augmented_messages,
                        max_tokens=max(200, int(0.3 * Config.LLM_MAX_TOKENS)),
                        temperature=0.7
                    )
                    cont_text = cont.choices[0].message.content
                    response_text += ("\n" + cont_text)
                    meta["continued"] = True
                    meta["continuations"] = meta.get("continuations", 0) + 1
                    fr = getattr(cont.choices[0], "finish_reason", None)
                    if fr != "length":
                        break
                    augmented_messages.append({"role": "assistant", "content": cont_text})
            except Exception as _:
                pass
        return response_text, meta

    def _looks_too_dry_or_off(self, text: str) -> bool:
        """Простая эвристика качества: слишком коротко, нет структуры, или повтор правил"""
        if not text or len(text.strip()) < 80:
            return True
        lowered = text.lower()
        banned = [
            "правила:",
            "не повторяй эти инструкции",
            "начинай сразу с анализа",
        ]
        if any(b in lowered for b in banned):
            return True
        has_structure = ("ключевые символы" in lowered) or ("практический вывод" in lowered)
        return not has_structure

    async def generate_with_fallback(self, messages: list) -> tuple[str, dict]:
        """Сначала primary, при ошибке/сухости — перебираем fallback-модели (если включены)"""
        try:
            primary_text, primary_meta = await self.get_response_with_model(Config.LLM_PRIMARY_MODEL, messages)
            if not self._looks_too_dry_or_off(primary_text):
                return primary_text, primary_meta
            logger.warning("Ответ primary выглядит сухим/без структуры — пробуем fallback(и)")
        except Exception as primary_error:
            logger.error(f"Primary ошибка: {primary_error}")

        fallbacks = []
        try:
            fallbacks = Config.get_fallback_models() if Config.LLM_FALLBACK_ENABLED else []
        except Exception:
            fallbacks = []

        for idx, fb_model in enumerate(fallbacks):
            try:
                fb_text, fb_meta = await self.get_response_with_model(fb_model, messages)
                fb_meta["fallback"] = True
                fb_meta["fallback_index"] = idx
                return fb_text, fb_meta
            except Exception as fb_error:
                logger.error(f"Fallback[{idx}] {fb_model} ошибка: {fb_error}")

        if 'primary_text' in locals() and primary_text:
            return primary_text, primary_meta
        raise RuntimeError("Не удалось получить ответ ни от primary, ни от fallback моделей")
    
    def create_system_prompt(self) -> str:
        """Создание системного промпта для бота"""
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompts', 'alyavseprospala_prompt.txt')
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as file:
                prompt_content = file.read().strip()
            logger.info(f"Системный промпт загружен из файла: {prompt_path}")
            return prompt_content
        except FileNotFoundError:
            logger.error(f"Файл промпта не найден: {prompt_path}")
            return "Ты бот для интерпретации снов. Помогай пользователям понимать их сны."
        except Exception as e:
            logger.error(f"Ошибка при чтении промпта: {e}")
            return "Ты бот для интерпретации снов. Помогай пользователям понимать их сны."