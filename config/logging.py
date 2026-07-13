from pathlib import Path
import logging

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)


class RequestIDFallbackFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s request_id=%(request_id)s"
        },
    },
    "handlers": {
        "app_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": str(LOG_DIR / "app.log"),
            "maxBytes": 5 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "json",
            "filters": ["request_id_fallback"],
        },
    },
    "filters": {
        "request_id_fallback": {
            "()": "config.logging.RequestIDFallbackFilter",
        }
    },
    "loggers": {
        "": {"handlers": ["app_file"], "level": "INFO"},
        "django.request": {"handlers": ["app_file"], "level": "WARNING", "propagate": False},
        "security": {"handlers": ["app_file"], "level": "INFO", "propagate": False},
        "audit": {"handlers": ["app_file"], "level": "INFO", "propagate": False},
    },
}
