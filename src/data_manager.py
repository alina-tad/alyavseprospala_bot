import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional
from .config import Config

logger = logging.getLogger(__name__)

class DataManager:
    """Менеджер для работы с данными пользователей и истории диалогов"""
    
    def __init__(self):
        """Инициализация менеджера данных"""
        self.data_file = "data/conversations.json"
        self.users_data: Dict[str, dict] = {}
        self._ensure_data_directory()
        self._load_data()
        logger.info("DataManager инициализирован")
    
    def _ensure_data_directory(self) -> None:
        """Создание директории для данных если не существует"""
        os.makedirs("data", exist_ok=True)
    
    def _load_data(self) -> None:
        """Загрузка данных из JSON файла"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as file:
                    self.users_data = json.load(file)
                logger.info(f"Загружены данные для {len(self.users_data)} пользователей")
            else:
                self.users_data = {}
                logger.info("Создан новый файл данных")
        except Exception as e:
            logger.error(f"Ошибка при загрузке данных: {e}")
            self.users_data = {}
    
    def _save_data(self) -> None:
        """Сохранение данных в JSON файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as file:
                json.dump(self.users_data, file, ensure_ascii=False, indent=2)
            logger.info("Данные сохранены")
        except Exception as e:
            logger.error(f"Ошибка при сохранении данных: {e}")
    
    def add_message(self, user_id: str, username: str, role: str, content: str) -> None:
        """Добавление сообщения в историю пользователя"""
        if user_id not in self.users_data:
            self.users_data[user_id] = {
                "user_id": user_id,
                "username": username,
                "created_at": datetime.now().isoformat(),
                "sessions": []
            }
        
        # Создаем новую сессию если её нет
        if not self.users_data[user_id]["sessions"]:
            session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            self.users_data[user_id]["sessions"].append({
                "session_id": session_id,
                "messages": [],
                "created_at": datetime.now().isoformat()
            })
        
        # Добавляем сообщение в текущую сессию
        current_session = self.users_data[user_id]["sessions"][-1]
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        current_session["messages"].append(message)
        
        logger.info(f"Добавлено сообщение пользователю {user_id}")
        self._save_data()
    
    def get_user_history(self, user_id: str) -> Optional[dict]:
        """Получение истории пользователя"""
        return self.users_data.get(user_id)
    
    def clear_user_history(self, user_id: str) -> None:
        """Очистка истории пользователя"""
        if user_id in self.users_data:
            self.users_data[user_id]["sessions"] = []
            logger.info(f"История пользователя {user_id} очищена")
            self._save_data()
    
    def export_all_history(self) -> str:
        """Экспорт всей истории в JSON строку"""
        try:
            export_data = {
                "exported_at": datetime.now().isoformat(),
                "total_users": len(self.users_data),
                "users": self.users_data
            }
            return json.dumps(export_data, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при экспорте данных: {e}")
            return "{}"
    
    def get_statistics(self) -> dict:
        """Получение статистики использования"""
        total_messages = 0
        total_sessions = 0
        
        for user_data in self.users_data.values():
            for session in user_data.get("sessions", []):
                total_sessions += 1
                total_messages += len(session.get("messages", []))
        
        return {
            "total_users": len(self.users_data),
            "total_sessions": total_sessions,
            "total_messages": total_messages
        } 