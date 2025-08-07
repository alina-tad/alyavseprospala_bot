import os
import logging
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Конфигурация приложения из переменных окружения"""
    
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")  # ID администратора бота
    
    # Настройки LLM
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    # Базовая совместимость: используем LLM_MODEL как прежний способ указания модели
    LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
    # Primary / fallback модели (можно переопределять в .env)
    LLM_PRIMARY_MODEL = os.getenv("LLM_PRIMARY_MODEL", LLM_MODEL)
    LLM_FALLBACK_MODEL = os.getenv("LLM_FALLBACK_MODEL", "")  # по умолчанию нет
    LLM_FALLBACK_ENABLED = os.getenv("LLM_FALLBACK_ENABLED", "true").lower() == "true"
    # Список fallback-моделей (через запятую). Сохраняем обратную совместимость с LLM_FALLBACK_MODEL
    LLM_FALLBACK_MODELS = [m.strip() for m in os.getenv("LLM_FALLBACK_MODELS", "").split(",") if m.strip()]
    # Лимит генерируемых токенов
    try:
        LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1200"))
    except ValueError:
        LLM_MAX_TOKENS = 1200
    LLM_BASE_URL = "https://openrouter.ai/api/v1"

    @classmethod
    def get_fallback_models(cls) -> list[str]:
        """Вернуть финальный список fallback-моделей с учётом обратной совместимости"""
        models = list(cls.LLM_FALLBACK_MODELS)
        if not models and cls.LLM_FALLBACK_MODEL:
            models.append(cls.LLM_FALLBACK_MODEL)
        return models
    
    @classmethod
    def validate(cls) -> None:
        """Проверка обязательных настроек"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен в .env файле")
        
        # Проверка корректности уровня логирования
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR"]
        if cls.LOG_LEVEL not in valid_levels:
            raise ValueError(f"LOG_LEVEL должен быть одним из: {valid_levels}")
        
        # Проверка ID администратора (опционально)
        if cls.ADMIN_USER_ID:
            try:
                int(cls.ADMIN_USER_ID)
            except ValueError:
                raise ValueError("ADMIN_USER_ID должен быть числом")
        
        # Проверка настроек LLM
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY не установлен в .env файле")
    
    @classmethod
    def get_log_level(cls) -> int:
        """Получить уровень логирования как константу"""
        return getattr(logging, cls.LOG_LEVEL)
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        if not cls.ADMIN_USER_ID:
            return False
        return str(user_id) == cls.ADMIN_USER_ID 