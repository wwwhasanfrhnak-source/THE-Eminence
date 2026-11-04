"""سیستم اعلان‌ها."""

from datetime import datetime
from electrocalc.data.database import get_connection


CATEGORIES = {
    "info": "ℹ️ اطلاع",
    "success": "✅ موفق",
    "warning": "⚠️ هشدار",
    "danger": "❌ خطا",
    "report": "📝 گزارش",
    "expense": "💰 هزینه",
    "approval": "✅ تأیید",
    "message": "💬 پیام",
    "project": "📁 پروژه",
    "stock": "📦 انبار",
}


def create_notification(username, title, message="",
                        category="info", link_to=""):
    """ثبت اعلان برای یه کاربر."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO notifications
            (username, title, message, category, link_to, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, title, message, category, link_to,
              datetime.now().isoformat()))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def notify_admins(title, message="", category="info", link_to=""):
    """ثبت اعلان برای همه مدیران."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE role='admin' AND active=1")
    admins = [r["username"] for r in cur.fetchall()]
    conn.close()

    for a in admins:
        create_notification(a, title, message, category, link_to)


def notify_all(title, message="", category="info", link_to=""):
    """ثبت اعلان برای همه کاربران فعال."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username FROM users WHERE active=1")
    users = [r["username"] for r in cur.fetchall()]
    conn.close()

    for u in users:
        create_notification(u, title, message, category, link_to)


def list_notifications(username, only_unread=False, limit=50):
    """لیست اعلان‌های یه کاربر."""
    conn = get_connection()
    cur = conn.cursor()
    if only_unread:
        cur.execute("""
            SELECT * FROM notifications
            WHERE username = ? AND is_read = 0
            ORDER BY id DESC LIMIT ?
        """, (username, limit))
    else:
        cur.execute("""
            SELECT * FROM notifications
            WHERE username = ?
            ORDER BY id DESC LIMIT ?
        """, (username, limit))
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def count_unread(username):
    """تعداد اعلان‌های خوانده‌نشده."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) AS c FROM notifications
        WHERE username = ? AND is_read = 0
    """, (username,))
    row = cur.fetchone()
    conn.close()
    return row["c"] if row else 0


def mark_read(notif_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE notifications SET is_read = 1 WHERE id = ?",
                (notif_id,))
    conn.commit()
    conn.close()


def mark_all_read(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE notifications SET is_read = 1 WHERE username = ?
    """, (username,))
    conn.commit()
    conn.close()


def delete_notification(notif_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM notifications WHERE id = ?", (notif_id,))
    conn.commit()
    conn.close()


def clear_all(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM notifications WHERE username = ?", (username,))
    conn.commit()
    conn.close()