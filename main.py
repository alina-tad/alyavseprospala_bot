#!/usr/bin/env python3
"""
Точка входа для Dreams Bot
"""

import asyncio
import logging
import sys
from src.bot import DreamsBot
from src.config import Config

def main() -> None:
    """Основная функция запуска бота"""
    try:
        # Валидация конфигурации
        Config.validate()
        
        # Создание и запуск бота
        bot = DreamsBot()
        asyncio.run(bot.start())
        
    except ValueError as e:
        logging.error(f"Ошибка конфигурации: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logging.info("Бот остановлен пользователем")
    except Exception as e:
        logging.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 