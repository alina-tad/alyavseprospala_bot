import os
import logging
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Конфигурация приложения из переменных окружения"""
    
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")  # ID администратора бота
    
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