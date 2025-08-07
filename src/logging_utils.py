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

