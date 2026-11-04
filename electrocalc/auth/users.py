"""مدیریت کاربران."""

import hashlib
from datetime import datetime

from electrocalc.data.database import get_connection


def hash_password(password: str) -> str:
    """رمزنگاری رمز عبور."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_user(username: str, password: str, full_name: str = "",
                role: str = "engineer", phone: str = "") -> int:
    """ساخت کاربر جدید."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO users (username, password_hash, full_name, role, phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, hash_password(password), full_name, role, phone,
              datetime.now().isoformat()))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def get_user(username: str):
    """گرفتن کاربر با نام کاربری."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cur.fetchone()
    conn.close()
    return row


def login(username: str, password: str):
    """ورود کاربر. اگر موفق بود کاربر رو برمی‌گردونه."""
    user = get_user(username)
    if not user:
        return None
    if not user["active"]:
        return None
    if user["password_hash"] != hash_password(password):
        return None
    return user


def change_password(username: str, new_password: str) -> bool:
    """تغییر رمز عبور یک کاربر."""
    if len(new_password) < 6:
        raise ValueError("رمز عبور باید حداقل ۶ کاراکتر باشد.")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (hash_password(new_password), username),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def set_avatar(username: str, avatar_path: str) -> bool:
    """ذخیره مسیر عکس پروفایل کاربر."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE users SET avatar_path = ? WHERE username = ?",
            (avatar_path, username),
        )
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def toggle_active(username: str) -> bool:
    """تغییر وضعیت فعال/غیرفعال کاربر. مقدار جدید رو برمی‌گردونه."""
    if username == "admin":
        raise ValueError("کاربر admin را نمی‌توان غیرفعال کرد.")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT active FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            return False
        new_val = 0 if row["active"] else 1
        cur.execute("UPDATE users SET active = ? WHERE username = ?",
                    (new_val, username))
        conn.commit()
        return bool(new_val)
    finally:
        conn.close()