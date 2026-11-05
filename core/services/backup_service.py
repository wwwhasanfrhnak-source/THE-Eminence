# core/services/backup_service.py
"""Consistent SQLite database backup and restore operations."""

import sqlite3
from datetime import datetime
from pathlib import Path

from config.settings import ROOT_DIR
from core.database import Database


class BackupService:
    def __init__(self, database: Database | None = None):
        self.db = database or Database()

    def create_backup(self, destination: str | Path | None = None) -> Path:
        target = (
            Path(destination)
            if destination
            else (
                ROOT_DIR
                / "data"
                / "backups"
                / f"eminence-{datetime.now().strftime('%Y%m%d-%H%M%S')}.sqlite"
            )
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        with self.db._lock:
            if self.db.connection is None:
                raise RuntimeError("Database connection is not initialized")
            with sqlite3.connect(target) as backup:
                self.db.connection.backup(backup)
        return target
