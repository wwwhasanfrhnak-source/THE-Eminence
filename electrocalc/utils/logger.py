"""لاگ‌گیری ساده برای ElectroCalc — ذخیره در logs/electrocalc.log."""

import logging
import sys
from pathlib import Path

# پوشه لاگ در ریشه پروژه
LOG_DIR = Path(__file__).resolve().parents[2] / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "electrocalc.log"


def setup_logger() -> logging.Logger:
    """راه‌اندازی لاگر سراسری."""
    logger = logging.getLogger("electrocalc")
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # فایل
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # کنسول
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger


log = setup_logger()