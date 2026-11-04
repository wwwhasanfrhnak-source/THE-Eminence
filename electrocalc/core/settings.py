"""تنظیمات برنامه — ذخیره در پایگاه داده."""

from datetime import datetime
from electrocalc.data.database import get_connection


DEFAULTS = {
    "app_language": "fa",
    "app_theme": "light",
    "decimal_places": "2",
    "default_cos_phi": "0.9",
    "default_voltage": "220",
    "default_voltage_3ph": "380",
    "default_efficiency": "0.9",
    "backup_on_start": "0",
    "show_timer_admin": "0",
    "auto_lock_minutes": "0",
    "notify_new_reports": "1",
    "notify_new_expenses": "1",
    "notify_low_stock": "1",
    "scroll_mode": "always",
    "scroll_speed": "0.5",
}


def get_setting(key, default=None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT value FROM app_settings WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row["value"]
    if default is not None:
        return default
    return DEFAULTS.get(key, "")


def set_setting(key, value):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO app_settings (key, value, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value,
                                        updated_at=excluded.updated_at
    """, (key, str(value), datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_all():
    result = dict(DEFAULTS)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM app_settings")
    for r in cur.fetchall():
        result[r["key"]] = r["value"]
    conn.close()
    return result


def reset_all():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM app_settings")
    conn.commit()
    conn.close()