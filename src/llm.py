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
        logger.info(f"LLM клиент инициализирован с моделью {Config.LLM_MODEL}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((Exception,))
    )
    async def get_response(self, messages: list) -> str:
        """Получение ответа от LLM с retry логикой"""
        try:
            logger.info(f"Отправка запроса к LLM, модель: {Config.LLM_MODEL}")
            
            response = self.client.chat.completions.create(
                model=Config.LLM_MODEL,
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            logger.info(f"Получен ответ от LLM: {len(response_text)} символов")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Ошибка при обращении к LLM: {e}")
            raise  # Пробрасываем исключение для retry
    
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