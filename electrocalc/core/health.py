"""بررسی سلامت پایگاه داده."""

import os
from pathlib import Path

from electrocalc.data.database import get_connection, DB_FILE


TABLES = [
    "users", "projects", "project_members", "reports",
    "timesheets", "materials", "expenses", "files",
    "messages", "company", "active_sessions", "audit_log",
]


def check_all():
    """همه چک‌ها. خروجی: دیکشنری نتیجه‌ها."""
    result = {
        "db_exists": False,
        "db_size": 0,
        "db_size_str": "-",
        "integrity_ok": False,
        "integrity_msg": "",
        "tables": [],
        "missing_tables": [],
        "row_counts": {},
        "orphan_count": 0,
        "warnings": [],
        "total_records": 0,
    }

    # 1) وجود فایل
    if not DB_FILE.exists():
        result["warnings"].append("⚠️ فایل پایگاه داده پیدا نشد!")
        return result

    result["db_exists"] = True
    size = DB_FILE.stat().st_size
    result["db_size"] = size
    result["db_size_str"] = _format_size(size)

    # 2) اتصال
    try:
        conn = get_connection()
        cur = conn.cursor()

        # 3) بررسی یکپارچگی
        cur.execute("PRAGMA integrity_check")
        row = cur.fetchone()
        integrity = row[0] if row else "unknown"
        if integrity == "ok":
            result["integrity_ok"] = True
            result["integrity_msg"] = "✅ پایگاه داده سالم است"
        else:
            result["integrity_msg"] = f"❌ مشکل: {integrity}"
            result["warnings"].append(f"مشکل یکپارچگی: {integrity}")

        # 4) جدول‌ها
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing = {r[0] for r in cur.fetchall()}
        result["tables"] = sorted(existing)
        result["missing_tables"] = [t for t in TABLES if t not in existing]

        if result["missing_tables"]:
            result["warnings"].append(
                f"⚠️ جدول‌های غایب: {', '.join(result['missing_tables'])}")

        # 5) تعداد رکوردها
        total = 0
        for t in TABLES:
            if t not in existing:
                continue
            try:
                cur.execute(f"SELECT COUNT(*) FROM {t}")
                n = cur.fetchone()[0]
                result["row_counts"][t] = n
                total += n
            except Exception:
                result["row_counts"][t] = -1

        result["total_records"] = total

        # 6) رکوردهای یتیم (orphans)
        orphans = 0
        try:
            cur.execute("""
                SELECT COUNT(*) FROM reports
                WHERE project_id NOT IN (SELECT id FROM projects)
            """)
            orphans += cur.fetchone()[0]
        except Exception:
            pass

        try:
            cur.execute("""
                SELECT COUNT(*) FROM expenses
                WHERE project_id IS NOT NULL
                  AND project_id NOT IN (SELECT id FROM projects)
            """)
            orphans += cur.fetchone()[0]
        except Exception:
            pass

        result["orphan_count"] = orphans
        if orphans > 0:
            result["warnings"].append(
                f"⚠️ {orphans} رکورد یتیم (به پروژه ناموجود وصل)")

        # 7) هشدارهای اضافی
        try:
            cur.execute("SELECT COUNT(*) FROM users")
            u = cur.fetchone()[0]
            if u == 0:
                result["warnings"].append("⚠️ هیچ کاربری وجود ندارد!")
        except Exception:
            pass

        try:
            cur.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND active=1")
            a = cur.fetchone()[0]
            if a == 0:
                result["warnings"].append("⚠️ هیچ مدیر فعالی وجود ندارد!")
        except Exception:
            pass

        conn.close()

    except Exception as e:
        result["warnings"].append(f"❌ خطا در اتصال: {e}")

    return result


def vacuum_db():
    """فشرده‌سازی پایگاه داده."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("VACUUM")
    conn.commit()
    conn.close()


def _format_size(size):
    if size < 1024:
        return f"{size} B"
    if size < 1024 * 1024:
        return f"{size/1024:.1f} KB"
    if size < 1024 * 1024 * 1024:
        return f"{size/(1024*1024):.2f} MB"
    return f"{size/(1024*1024*1024):.2f} GB"