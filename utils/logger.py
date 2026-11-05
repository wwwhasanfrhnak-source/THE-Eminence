# utils/logger.py
"""Configure rotating application logs."""

import logging
from logging.handlers import RotatingFileHandler

from config.settings import LOG_LEVEL, ROOT_DIR


def get_logger(name: str = "eminence") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        log_dir = ROOT_DIR / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = RotatingFileHandler(
            log_dir / "eminence.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    return logger
