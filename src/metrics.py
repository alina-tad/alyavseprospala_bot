import json
import os
import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class MetricsManager:
    """Простая метрика в JSON-файле без внешних зависимостей"""

    def __init__(self, path: str = "data/metrics.json") -> None:
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.metrics: Dict[str, object] = self._load()

    def _load(self) -> Dict[str, object]:
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Не удалось прочитать {self.path}: {e}")
        # дефолтная структура
        return {
            "created_at": datetime.now().isoformat(),
            "totals": {
                "requests": 0,
                "success": 0,
                "errors": 0,
            },
            "llm": {
                "primary_attempts": 0,
                "primary_success": 0,
                "fallback_attempts": 0,
                "fallback_success": 0,
                "per_model": {},  # model -> count
            },
            "timings": {
                "response_ms_sum": 0,
                "response_ms_count": 0,
            },
            "updated_at": None,
        }

    def _save(self) -> None:
        try:
            self.metrics["updated_at"] = datetime.now().isoformat()
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.metrics, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Не удалось сохранить {self.path}: {e}")

    def record_request(
        self,
        *,
        model: Optional[str],
        used_fallback: bool,
        success: bool,
        response_time_ms: Optional[int] = None,
        primary_attempt: bool = True,
    ) -> None:
        # totals
        self.metrics["totals"]["requests"] += 1
        if success:
            self.metrics["totals"]["success"] += 1
        else:
            self.metrics["totals"]["errors"] += 1

        # llm
        if primary_attempt:
            self.metrics["llm"]["primary_attempts"] += 1
            if success and not used_fallback:
                self.metrics["llm"]["primary_success"] += 1
        if used_fallback:
            self.metrics["llm"]["fallback_attempts"] += 1
            if success:
                self.metrics["llm"]["fallback_success"] += 1

        if model:
            per_model = self.metrics["llm"].setdefault("per_model", {})
            per_model[model] = int(per_model.get(model, 0)) + 1

        # timings
        if response_time_ms is not None:
            self.metrics["timings"]["response_ms_sum"] += int(response_time_ms)
            self.metrics["timings"]["response_ms_count"] += 1

        self._save()

