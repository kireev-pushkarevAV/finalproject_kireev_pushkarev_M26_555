import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from valutatrade_hub.infra.settings import SettingsLoader


def setup_logging() -> logging.Logger:
    settings = SettingsLoader()
    logs_dir: Path = settings.get("LOGS_DIR")
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file: Path = settings.get("LOG_FILE")
    log_level = getattr(logging, settings.get("LOG_LEVEL", "INFO"))

    logger = logging.getLogger("valutatrade")
    logger.setLevel(log_level)

    if not logger.handlers:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=1_000_000,
            backupCount=3,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "%(levelname)s %(asctime)s %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
