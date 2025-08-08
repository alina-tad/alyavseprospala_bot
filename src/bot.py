import asyncio
import logging
import os
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from .config import Config
from .llm import LLMClient
from .data_manager import DataManager
from .metrics import MetricsManager
from .logging_utils import JSONEventLogger, setup_structured_file_logging

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
        self.data_manager = DataManager()
        self.metrics = MetricsManager()
        self.events = JSONEventLogger()
        self.system_prompt = self.llm_client.create_system_prompt()
        self.setup_handlers()
        # структурированный файл-лог
        setup_structured_file_logging()
        logger.info("Бот инициализирован с LLM и DataManager")
    
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
                "/stop  — завершить работу\n\n"
                "Готов(а) поделиться своим сном?"
            )
            await message.answer(welcome_text)
            logger.info(f"Пользователь {message.from_user.id} запустил бота")
            self.events.log_event("start", {"user_id": message.from_user.id})
        
        @self.dp.message(Command("stop"))
        async def handle_stop_command(message: types.Message) -> None:
            """Обработка команды /stop"""
            await message.answer("До свидания! Возвращайся, если захочешь поговорить о снах 👋")
            logger.info(f"Пользователь {message.from_user.id} остановил бота")
            self.events.log_event("stop", {"user_id": message.from_user.id})
        
        @self.dp.message(Command("clear"))
        async def handle_clear_command(message: types.Message) -> None:
            """Обработка команды /clear (только для администратора)"""
            user_id = message.from_user.id
            
            # Проверка на администратора
            if not Config.is_admin(user_id):
                # Тихо игнорируем для не-администраторов (без ответа пользователю)
                logger.warning(f"Пользователь {user_id} попытался выполнить команду /clear без прав администратора")
                self.events.log_event("clear_denied", {"user_id": user_id})
                return
            
            # Очистка истории для администратора
            user_id_str = str(user_id)
            self.data_manager.clear_user_history(user_id_str)
            await message.answer("История диалога очищена. ✨")
            logger.info(f"Администратор {user_id} очистил историю")
            self.events.log_event("clear_ok", {"user_id": user_id})
        
        @self.dp.message(Command("export"))
        async def handle_export_command(message: types.Message) -> None:
            """Обработка команды /export"""
            user_id = message.from_user.id
            
            # Проверка на администратора
            if not Config.is_admin(user_id):
                # Тихо игнорируем для не-администраторов (без ответа пользователю)
                logger.warning(f"Пользователь {user_id} попытался выполнить команду /export без прав администратора")
                self.events.log_event("export_denied", {"user_id": user_id})
                return
            
            try:
                # Получаем статистику
                stats = self.data_manager.get_statistics()
                stats_text = (
                    f"📊 Статистика бота:\n"
                    f"👥 Пользователей: {stats['total_users']}\n"
                    f"💬 Сессий: {stats['total_sessions']}\n"
                    f"📝 Сообщений: {stats['total_messages']}"
                )
                
                # Экспортируем данные
                export_data = self.data_manager.export_all_history()
                
                # Создаем файл для отправки
                filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(export_data)
                
                # Отправляем файл
                with open(filename, 'rb') as f:
                    await message.answer_document(
                        types.BufferedInputFile(f.read(), filename=filename),
                        caption=stats_text
                    )
                
                # Удаляем временный файл
                os.remove(filename)
                logger.info(f"Администратор {user_id} экспортировал данные")
                self.events.log_event("export_ok", {"user_id": user_id, "filename": filename})
                
            except Exception as e:
                await message.answer("❌ Ошибка при экспорте данных.")
                logger.error(f"Ошибка экспорта для администратора {user_id}: {e}")
        
        @self.dp.message()
        async def handle_message(message: types.Message) -> None:
            """Обработка обычных сообщений с LLM"""
            user_message = message.text
            user_id = str(message.from_user.id)
            username = message.from_user.username or message.from_user.first_name or "Unknown"
            # Игнорируем команды, чтобы их обработали соответствующие хендлеры
            if user_message.strip().startswith('/'):
                return
            
            # Логирование входящего сообщения
            log_message = user_message[:50] + "..." if len(user_message) > 50 else user_message
            logger.info(f"Пользователь {user_id} отправил: {log_message}")
            # jsonl событие
            self.events.log_event("message_in", {"user_id": user_id, "text": log_message})
            
            # Проверяем, содержит ли сообщение описание сна
            if len(user_message.strip()) < 15:
                await message.answer(
                    "Пожалуйста, опиши свой сон подробнее. Расскажи, что ты видел, какие чувства испытывал, "
                    "какие образы запомнились. Чем больше деталей, тем глубже будет анализ. 🌙"
                )
                return
            
            # Сохраняем сообщение пользователя
            self.data_manager.add_message(user_id, username, "user", user_message)
            
            # Подготовка сообщений для LLM
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Проанализируй этот сон: {user_message}"}
            ]
            
            # Получение ответа от LLM (с поддержкой fallback)
            try:
                start_ts = datetime.now()
                response_text, response_meta = await self.llm_client.generate_with_fallback(messages)
                await message.answer(response_text)
                
                # Сохраняем ответ бота
                self.data_manager.add_message(user_id, username, "assistant", response_text, metadata=response_meta)
                
                model_used = response_meta.get("model")
                is_fallback = response_meta.get("fallback")
                logger.info(f"Отправлен ответ пользователю {user_id}. Модель: {model_used}, fallback: {is_fallback}")
                self.events.log_event("message_out", {"user_id": user_id, "model": model_used, "fallback": bool(is_fallback)})
                # метрики
                duration_ms = int((datetime.now() - start_ts).total_seconds() * 1000)
                self.metrics.record_request(
                    model=model_used,
                    used_fallback=bool(is_fallback),
                    success=True,
                    response_time_ms=duration_ms,
                    primary_attempt=not bool(is_fallback),
                )
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
                self.events.log_event("error", {"user_id": user_id, "error": str(e)})

        @self.dp.message(Command("stats"))
        async def handle_stats_command(message: types.Message) -> None:
            """Краткая статистика (только для администратора)"""
            user_id = message.from_user.id
            if not Config.is_admin(user_id):
                # Тихо игнорируем
                self.events.log_event("stats_denied", {"user_id": user_id})
                return
            stats = self.data_manager.get_statistics()
            # Сжато: ключевые показатели + последние LLM-метрики из файла
            from .metrics import MetricsManager
            mm = MetricsManager()
            m = mm.metrics
            avg_ms = 0
            if m["timings"]["response_ms_count"]:
                avg_ms = int(m["timings"]["response_ms_sum"] / m["timings"]["response_ms_count"])  # noqa: E501
            text = (
                "📊 Статистика\n"
                f"👥 Пользователи: {stats['total_users']}\n"
                f"💬 Сессии: {stats['total_sessions']}\n"
                f"📝 Сообщения: {stats['total_messages']}\n"
                f"⚙️ Запросы LLM: {m['totals']['requests']}, ошибки: {m['totals']['errors']}\n"
                f"🧠 Primary success: {m['llm']['primary_success']}, Fallback success: {m['llm']['fallback_success']}\n"  # noqa: E501
                f"⏱️ Ср. время ответа: {avg_ms} мс\n"
            )
            await message.answer(text)
            self.events.log_event("stats_ok", {"user_id": user_id})
    
    async def start(self) -> None:
        """Запуск бота"""
        logger.info("Запуск бота...")
        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
            raise 