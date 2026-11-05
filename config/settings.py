# config/settings.py
"""Environment-backed application settings."""

import os
from pathlib import Path

from dotenv import load_dotenv

from config.constants import DEFAULT_SESSION_TIMEOUT_MINUTES

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")
DB_PATH = Path(os.getenv("EMINENCE_DB_PATH", str(ROOT_DIR / "data" / "db.sqlite")))
if not DB_PATH.is_absolute():
    DB_PATH = ROOT_DIR / DB_PATH
LOG_LEVEL = os.getenv("EMINENCE_LOG_LEVEL", "INFO").upper()
SESSION_TIMEOUT_MINUTES = int(
    os.getenv("EMINENCE_SESSION_TIMEOUT", str(DEFAULT_SESSION_TIMEOUT_MINUTES))
)
