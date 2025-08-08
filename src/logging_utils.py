import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional


class JSONEventLogger:
    """Простой JSONL-логгер событий в файл data/events.jsonl"""

    def __init__(self, path: str = "data/events.jsonl") -> None:
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self._logger = logging.getLogger(__name__)

    def log_event(self, event: str, payload: Optional[Dict[str, Any]] = None) -> None:
        record = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "payload": payload or {},
        }
        try:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as e:
            self._logger.warning(f"Не удалось записать событие в {self.path}: {e}")


class JSONLogFormatter(logging.Formatter):
    """Форматер логов в JSONL (минимальные поля)"""

    def format(self, record: logging.LogRecord) -> str:  # type: ignore[override]
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_structured_file_logging(path: str = "data/app.jsonl", level: int = logging.INFO) -> None:
    """Добавить file handler с JSONL форматом, не меняя консольный вывод"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setLevel(level)
    handler.setFormatter(JSONLogFormatter())
    root = logging.getLogger()
    # предотвращаем дублирование при повторном вызове
    for h in root.handlers:
        if isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', '') == os.path.abspath(path):
            return
    root.addHandler(handler)

