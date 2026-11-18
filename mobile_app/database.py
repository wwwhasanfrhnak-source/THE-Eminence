"""SQLite access, first-run database installation, and mobile data helpers."""

import shutil
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


DATABASE_NAME = "electrocalc.db"
REQUIRED_TABLES = {"users", "projects", "invoices"}
CACHE_STAMP_KEY = "mobile_user_cache_updated_at"

PROJECT_STATUSES = {
    "planned": "برنامه‌ریزی‌شده",
    "in_progress": "در حال انجام",
    "done": "پایان‌یافته",
    "cancelled": "لغوشده",
}

ACCESS_MAP = {
    "projects": "projects.view",
    "invoices": "invoices.view",
    "tasks": "tasks.view",
    "reports": "reports.view",
    "timesheets": "timesheets.view",
    "materials": "materials.view",
    "customers": "customers.view",
}


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_database_path() -> Path:
    from kivy.app import App

    app = App.get_running_app()
    if app is None:
        raise RuntimeError("Database access requires a running Kivy application.")
    return Path(app.user_data_dir) / DATABASE_NAME


def initialize_database() -> Path:
    """Install the bundled database template once, without changing its schema."""
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
        connection.row_factory = sqlite3.Row
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
        _stamp_bundled_accounts(connection, tables)
    return target


def _stamp_bundled_accounts(connection, tables):
    """Treat a pre-seeded database as a fresh offline cache for seven days."""
    if "app_settings" not in tables or "users" not in tables:
        return
    count = connection.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if not count:
        return
    existing = connection.execute(
        "SELECT 1 FROM app_settings WHERE key = ?", (CACHE_STAMP_KEY,)
    ).fetchone()
    if existing is None:
        connection.execute(
            "INSERT INTO app_settings (key, value, updated_at) VALUES (?, ?, ?)",
            (CACHE_STAMP_KEY, _now(), _now()),
        )
        connection.commit()


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(str(get_database_path()), timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("PRAGMA busy_timeout = 10000")
    return connection


def _permitted(permissions, permission):
    if permissions is None:
        return True
    if permission in permissions:
        return True
    section = permission.split(".", 1)[0]
    return f"{section}.manage" in permissions


def dashboard_counts(permissions=None) -> dict[str, int]:
    """Return summary counts for the sections the user may see."""
    with closing(get_connection()) as connection:
        counts = {}
        for table, permission in ACCESS_MAP.items():
            if not _permitted(permissions, permission):
                continue
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


def list_projects(search="", limit=200):
    term = f"%{str(search or '').strip()}%"
    with closing(get_connection()) as connection:
        return connection.execute(
            "SELECT * FROM projects "
            "WHERE name LIKE ? OR COALESCE(customer, '') LIKE ? "
            "ORDER BY COALESCE(updated_at, created_at) DESC, id DESC LIMIT ?",
            (term, term, int(limit)),
        ).fetchall()


def project_count():
    with closing(get_connection()) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0])


def create_project(name, customer="", description="", status="planned",
                   created_by=""):
    name = str(name or "").strip()
    if not name:
        raise ValueError("نام پروژه الزامی است.")
    if status not in PROJECT_STATUSES:
        raise ValueError("وضعیت پروژه معتبر نیست.")
    now = _now()
    with closing(get_connection()) as connection:
        cursor = connection.execute(
            "INSERT INTO projects "
            "(name, customer, description, status, created_by, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, str(customer or "").strip(), str(description or "").strip(),
             status, str(created_by or ""), now, now),
        )
        connection.commit()
        return int(cursor.lastrowid)


def merge_projects(rows):
    """Upsert project rows received from the LAN delta endpoint."""
    if not isinstance(rows, list):
        return 0
    merged = 0
    with closing(get_connection()) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(projects)")
        }
        for row in rows:
            if not isinstance(row, dict) or "id" not in row:
                continue
            safe = {key: value for key, value in row.items() if key in columns}
            if not safe:
                continue
            fields = ", ".join(safe)
            marks = ", ".join("?" for _ in safe)
            updates = ", ".join(
                f"{key} = excluded.{key}" for key in safe if key != "id"
            )
            sql = f"INSERT INTO projects ({fields}) VALUES ({marks})"
            if updates:
                sql += f" ON CONFLICT(id) DO UPDATE SET {updates}"
            connection.execute(sql, tuple(safe.values()))
            merged += 1
        connection.commit()
    return merged


def list_users(search="", limit=200):
    term = f"%{str(search or '').strip()}%"
    with closing(get_connection()) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(users)")
        }
        wanted = [
            "username", "full_name", "role", "active", "account_status",
            "platform_windows", "platform_android", "is_superadmin",
            "created_at", "last_login", "last_login_platform",
        ]
        selected = ", ".join(key for key in wanted if key in columns)
        order = "is_superadmin DESC, username" if "is_superadmin" in columns else "username"
        return connection.execute(
            f"SELECT {selected} FROM users "
            "WHERE username LIKE ? OR COALESCE(full_name, '') LIKE ? "
            f"ORDER BY {order} LIMIT ?",
            (term, term, int(limit)),
        ).fetchall()


def user_count():
    with closing(get_connection()) as connection:
        return int(connection.execute("SELECT COUNT(*) FROM users").fetchone()[0])
