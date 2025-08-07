import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from .config import Config
from .llm import LLMClient

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
        self.llm_client = LLMClient()
        self.system_prompt = self.llm_client.create_system_prompt()
        self.setup_handlers()
        logger.info("Бот инициализирован с LLM")
    
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
        async def handle_message(message: types.Message) -> None:
            """Обработка обычных сообщений с LLM"""
            user_message = message.text
            user_id = message.from_user.id
            
            # Логирование входящего сообщения
            log_message = user_message[:50] + "..." if len(user_message) > 50 else user_message
            logger.info(f"Пользователь {user_id} отправил: {log_message}")
            
            # Проверяем, содержит ли сообщение описание сна
            if len(user_message.strip()) < 15:
                await message.answer(
                    "Пожалуйста, опиши свой сон подробнее. Расскажи, что ты видел, какие чувства испытывал, "
                    "какие образы запомнились. Чем больше деталей, тем глубже будет анализ. 🌙"
                )
                return
            
            # Подготовка сообщений для LLM
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Проанализируй этот сон: {user_message}"}
            ]
            
            # Получение ответа от LLM
            try:
                response = await self.llm_client.get_response(messages)
                await message.answer(response)
                logger.info(f"Отправлен ответ пользователю {user_id}")
            except Exception as e:
                # Специфичные сообщения об ошибках
                if "rate limit" in str(e).lower():
                    error_message = "Слишком много запросов. Подождите немного и попробуйте снова."
                elif "api" in str(e).lower():
                    error_message = "Проблема с сервисом. Попробуйте позже."
                else:
                    error_message = "Извините, произошла ошибка при обработке вашего сообщения. Попробуйте позже."
                
                await message.answer(error_message)
                logger.error(f"Ошибка при обработке сообщения пользователя {user_id}: {e}")
    
    async def start(self) -> None:
        """Запуск бота"""
        logger.info("Запуск бота...")
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            raise 