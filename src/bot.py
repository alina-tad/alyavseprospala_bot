import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from .config import Config

# Настройка логирования согласно @conventions.mdc
logging.basicConfig(
    level=Config.get_log_level(),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DreamsBot:
    """Telegram бот для осмысления снов"""
    
    def __init__(self):
        """Инициализация бота"""
        self.bot = Bot(token=Config.TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher()
        self.setup_handlers()
        logger.info("Бот инициализирован")
    
    def setup_handlers(self) -> None:
        """Настройка обработчиков команд и сообщений"""
        
        @self.dp.message(Command("start"))
        async def handle_start_command(message: types.Message) -> None:
            """Обработка команды /start"""
            welcome_text = (
                "Привет! Я здесь, чтобы помочь тебе разобраться в твоих снах. 🌟\n\n"
                "Опиши свой сон — вместе мы проанализируем сюжет, символы и эмоции, "
                "чтобы найти глубинные смыслы.\n\n"
                "Команды:\n"
                "/clear — начать диалог заново\n"
                "/stop  — завершить работу\n\n"
                "Готов(а) поделиться своим сном?"
            )
            await message.answer(welcome_text)
            logger.info(f"Пользователь {message.from_user.id} запустил бота")
        
        @self.dp.message(Command("stop"))
        async def handle_stop_command(message: types.Message) -> None:
            """Обработка команды /stop"""
            await message.answer("До свидания! Возвращайся, если захочешь поговорить о снах 👋")
            logger.info(f"Пользователь {message.from_user.id} остановил бота")
        
        @self.dp.message(Command("clear"))
        async def handle_clear_command(message: types.Message) -> None:
            """Обработка команды /clear"""
            await message.answer("История диалога очищена. ✨")
            logger.info(f"Пользователь {message.from_user.id} очистил историю")
        
        @self.dp.message(Command("export"))
        async def handle_export_command(message: types.Message) -> None:
            """Обработка команды /export"""
            user_id = message.from_user.id
            
            # Проверка на администратора
            if not Config.is_admin(user_id):
                await message.answer("⛔ У вас нет прав для выполнения этой команды.")
                logger.warning(f"Пользователь {user_id} попытался выполнить команду /export без прав администратора")
                return
            
            await message.answer("Экспорт истории диалогов (функция будет реализована в следующих итерациях). 📋")
            logger.info(f"Администратор {user_id} запросил экспорт")
        
        @self.dp.message()
        async def handle_echo_message(message: types.Message) -> None:
            """Обработка обычных сообщений (эхо-режим)"""
            user_message = message.text
            echo_response = f"Эхо: {user_message}"
            await message.answer(echo_response)
            
            # Логирование с ограничением длины сообщения
            log_message = user_message[:50] + "..." if len(user_message) > 50 else user_message
            logger.info(f"Пользователь {message.from_user.id} отправил: {log_message}")
    
    async def start(self) -> None:
        """Запуск бота"""
        logger.info("Запуск бота...")
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            raise 