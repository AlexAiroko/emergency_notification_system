import json
import logging
import sys
from datetime import datetime, timezone

from app.core.config import settings, LogFormat


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(fmt="%(asctime)s %(levelname)s %(name)s: %(message)s")


def setup_logging() -> None:
    level = settings.LOG_LEVEL.value

    root = logging.getLogger()
    root.setLevel(getattr(logging, level))

    handler = logging.StreamHandler(sys.stdout)

    if settings.LOG_FORMAT == LogFormat.JSON:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    root.handlers.clear()
    root.addHandler(handler)


setup_logging()

logger = logging.getLogger("notification_system")
