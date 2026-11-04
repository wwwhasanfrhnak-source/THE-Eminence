"""ثبت فعالیت‌های کاربران (Audit Log)."""

from datetime import datetime

from electrocalc.data.database import get_connection


# اکشن‌های استاندارد
ACTIONS = {
    "login": "ورود به سیستم",
    "logout": "خروج از سیستم",
    "create": "ساخت",
    "update": "ویرایش",
    "delete": "حذف",
    "approve": "تأیید",
    "reject": "رد",
    "password_change": "تغییر رمز",
    "user_disable": "غیرفعال کردن کاربر",
    "user_enable": "فعال کردن کاربر",
    "backup": "پشتیبان‌گیری",
    "restore": "بازیابی",
    "permission_change": "تغییر مجوز",
}


def log_action(username, action, object_type="", object_id=None,
               description="", old_value="", new_value=""):
    """ثبت یه فعالیت."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO audit_log
            (username, action, object_type, object_id, description,
             old_value, new_value, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, action, object_type, object_id, description,
              str(old_value) if old_value else "",
              str(new_value) if new_value else "",
              datetime.now().isoformat()))
        conn.commit()
        conn.close()
    except Exception:
        pass  # اگه خطا داد، برنامه رو متوقف نکن


def list_logs(search="", username=None, action=None, limit=500):
    """لیست لاگ‌ها با فیلتر."""
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []

    if search:
        query += " AND (description LIKE ? OR object_type LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    if username:
        query += " AND username = ?"
        params.append(username)
    if action:
        query += " AND action = ?"
        params.append(action)

    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def get_users_list():
    """لیست کاربرانی که لاگ دارن."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT username FROM audit_log
        WHERE username IS NOT NULL AND username != ''
        ORDER BY username
    """)
    rows = cur.fetchall()
    conn.close()
    return [r["username"] for r in rows]


def clear_all():
    """پاک کردن همه لاگ‌ها (فقط admin)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM audit_log")
    conn.commit()
    conn.close()


def delete_older_than(days=30):
    """حذف لاگ‌های قدیمی‌تر از X روز."""
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM audit_log WHERE created_at < ?", (cutoff,))
    conn.commit()
    deleted = cur.rowcount
    conn.close()
    return deleted


def count_logs():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM audit_log")
    row = cur.fetchone()
    conn.close()
    return row["c"] if row else 0