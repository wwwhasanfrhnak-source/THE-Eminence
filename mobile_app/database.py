"""SQLite access scoped to the Android application's private storage."""

import shutil
import sqlite3
from contextlib import closing
from pathlib import Path


DATABASE_NAME = "electrocalc.db"
REQUIRED_TABLES = {"users", "projects", "invoices"}


def get_database_path() -> Path:
    from kivy.app import App

    app = App.get_running_app()
    if app is None:
        raise RuntimeError("Database access requires a running Kivy application.")
    return Path(app.user_data_dir) / DATABASE_NAME


def initialize_database() -> Path:
    """Install the bundled database once, without changing its schema."""
    target = get_database_path()
    if not target.exists():
        source = Path(__file__).resolve().parent / "assets" / DATABASE_NAME
        if not source.is_file():
            raise FileNotFoundError(f"Bundled database not found: {source}")

        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".db.tmp")
        shutil.copyfile(source, temporary)
        temporary.replace(target)

    with closing(sqlite3.connect(str(target))) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        missing = REQUIRED_TABLES - tables
        if missing:
            raise sqlite3.DatabaseError(
                "The bundled database is missing required tables: "
                + ", ".join(sorted(missing))
            )
    return target


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(str(get_database_path()), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def dashboard_counts() -> dict[str, int]:
    """Return summary counts using tables already present in the desktop DB."""
    with closing(get_connection()) as connection:
        counts = {}
        for table in ("projects", "invoices", "tasks"):
            exists = connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                (table,),
            ).fetchone()
            counts[table] = (
                int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
                if exists
                else 0
            )
        return counts