# core/database.py
"""Thread-safe SQLite singleton and schema initialization."""

import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from config.constants import (
    DEFAULT_ADMIN_NAME,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    PERMISSIONS,
)
from config.settings import DB_PATH


class Database:
    """Process-wide, serialized SQLite connection."""

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, path: str | Path | None = None):
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
                cls._instance._init_lock = threading.Lock()
        return cls._instance

    def __init__(self, path: str | Path | None = None):
        with self._init_lock:
            if self._initialized:
                return
            self._lock = threading.RLock()
            self.path = Path(path) if path is not None else DB_PATH
            self.connection: sqlite3.Connection | None = None
            self.initialize()
            self._initialized = True

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            if self.connection is not None:
                self.connection.close()
            self.connection = sqlite3.connect(self.path, check_same_thread=False, timeout=30)
            self.connection.row_factory = sqlite3.Row
            self.connection.execute("PRAGMA journal_mode = WAL")
            self.connection.execute("PRAGMA foreign_keys = ON")
            schema_path = Path(__file__).with_name("schema.sql")
            self.connection.executescript(schema_path.read_text(encoding="utf-8"))
            self._seed_defaults()
            self.connection.commit()

    def _seed_defaults(self) -> None:
        import bcrypt

        assert self.connection is not None
        user = self.connection.execute(
            "SELECT id FROM users WHERE username = ?", (DEFAULT_ADMIN_USERNAME,)
        ).fetchone()
        if user is None:
            password_hash = bcrypt.hashpw(
                DEFAULT_ADMIN_PASSWORD.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            self.connection.execute(
                "INSERT INTO users (username, password_hash, full_name, role) "
                "VALUES (?, ?, ?, ?)",
                (DEFAULT_ADMIN_USERNAME, password_hash, DEFAULT_ADMIN_NAME, "admin"),
            )
        for role, permissions in PERMISSIONS.items():
            for permission in permissions:
                self.connection.execute(
                    "INSERT OR IGNORE INTO permissions (role, permission) VALUES (?, ?)",
                    (role, permission),
                )

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Hold the connection lock for a complete atomic operation."""
        with self._lock:
            if self.connection is None:
                raise RuntimeError("Database connection is not initialized")
            try:
                yield self.connection
                self.connection.commit()
            except Exception:
                self.connection.rollback()
                raise

    def fetch_all(self, query: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            if self.connection is None:
                raise RuntimeError("Database connection is not initialized")
            return self.connection.execute(query, params).fetchall()

    def fetch_one(self, query: str, params: tuple = ()) -> sqlite3.Row | None:
        with self._lock:
            if self.connection is None:
                raise RuntimeError("Database connection is not initialized")
            return self.connection.execute(query, params).fetchone()

    def close(self) -> None:
        with self._lock:
            if self.connection is not None:
                self.connection.close()
                self.connection = None

    @classmethod
    def reset_for_tests(cls) -> None:
        """Close and clear the singleton to allow isolated temporary databases."""
        with cls._instance_lock:
            if cls._instance is not None:
                cls._instance.close()
            cls._instance = None
