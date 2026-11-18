"""Login verification for the existing users table."""

import hashlib
import hmac
import os
import re
from contextlib import closing
from datetime import datetime, timedelta, timezone

from database import get_connection


_PBKDF2_PREFIX = "pbkdf2_sha256$"
_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
CACHE_STAMP_KEY = "mobile_user_cache_updated_at"
OFFLINE_CACHE_DAYS = 7
_PBKDF2_ROUNDS = 200_000


def _verify_password(password: str, stored_hash: str) -> bool:
    if stored_hash.startswith(_BCRYPT_PREFIXES):
        try:
            import bcrypt

            return bcrypt.checkpw(
                password.encode("utf-8"), stored_hash.encode("ascii")
            )
        except (ImportError, ValueError, TypeError, UnicodeEncodeError):
            return False

    if stored_hash.startswith(_PBKDF2_PREFIX):
        try:
            prefix, rounds_text, salt_hex, digest_hex = stored_hash.split("$", 3)
            if prefix != "pbkdf2_sha256":
                return False
            rounds = int(rounds_text)
            if not 1 <= rounds <= 2_000_000:
                return False
            expected = bytes.fromhex(digest_hex)
            actual = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), rounds
            )
            return hmac.compare_digest(actual, expected)
        except (ValueError, TypeError):
            return False

    if _SHA256_RE.fullmatch(stored_hash):
        actual = hashlib.sha256(password.encode("utf-8")).hexdigest()
        return hmac.compare_digest(actual, stored_hash.lower())
    return False


def authenticate_local(username: str, password: str):
    """Return ``(user, permissions, error)`` using the cached account.

    Local login is the offline fallback; it enforces the same account status,
    Android platform flag, and explicit permission rules as the desktop app.
    """
    import permissions as perm_module

    username = (username or "").strip()
    if not username or not password:
        return None, set(), "نام کاربری و رمز عبور را وارد کنید."

    with closing(get_connection()) as connection:
        if not _cache_is_fresh(connection):
            return None, set(), (
                "برای ورود آفلاین ابتدا یک‌بار با سرور دفتر وارد شوید."
            )
        user = connection.execute(
            "SELECT * FROM users WHERE username = ? LIMIT 1", (username,)
        ).fetchone()
        if user is None or not _verify_password(
            password, user["password_hash"] or ""
        ):
            return None, set(), "نام کاربری یا رمز عبور نادرست است."
        if not perm_module.account_active(user):
            return None, set(), "این حساب غیرفعال یا مسدود است."
        if not perm_module.platform_allowed(user, "android"):
            return None, set(), "ورود از نسخه اندروید برای این حساب مجاز نیست."
        effective = perm_module.effective_permissions(connection, user)
        if not perm_module.is_superadmin(user) and "app.login" not in effective:
            return None, set(), "مجوز ورود به برنامه برای این حساب وجود ندارد."
    return user, effective, ""


def _cache_is_fresh(connection) -> bool:
    row = connection.execute(
        "SELECT value FROM app_settings WHERE key = ?", (CACHE_STAMP_KEY,)
    ).fetchone()
    if row is None or not row[0]:
        return False
    try:
        updated = datetime.fromisoformat(str(row[0]))
    except ValueError:
        return False
    if updated.tzinfo is None:
        updated = updated.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - updated <= timedelta(
        days=OFFLINE_CACHE_DAYS
    )


def _hash_for_cache(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ROUNDS
    )
    return (
        f"{_PBKDF2_PREFIX}{_PBKDF2_ROUNDS}$"
        f"{salt.hex()}${digest.hex()}"
    )


def cache_online_session(user, password, permissions):
    """Cache the authenticated account and its effective grants locally.

    The real Windows database is never shipped; offline users are created
    here only after a successful server login.
    """
    username = str((user or {}).get("username") or "").strip()
    if not username:
        return
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    grants = sorted({str(key) for key in (permissions or []) if key})

    with closing(get_connection()) as connection:
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(users)")
        }
        values = {
            "username": username,
            "full_name": str(user.get("full_name") or ""),
            "role": str(user.get("role") or "engineer"),
            "phone": str(user.get("phone") or ""),
            "job_title": str(user.get("job_title") or ""),
            "notes": str(user.get("notes") or ""),
            "avatar_path": str(user.get("avatar_path") or ""),
            "active": 1,
            "permissions": "",
            "account_status": "active",
            "is_superadmin": 1 if user.get("is_superadmin") else 0,
            "platform_windows": 1 if user.get("platform_windows", 1) else 0,
            "platform_android": 1 if user.get("platform_android", 1) else 0,
            "permissions_version": int(user.get("permissions_version") or 1),
            "updated_at": now,
        }
        if password:
            values["password_hash"] = _hash_for_cache(password)
            values["created_at"] = now

        current = connection.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if current is None and not password:
            return
        usable = {key: value for key, value in values.items() if key in columns}
        if current:
            assignments = ", ".join(f"{key} = ?" for key in usable)
            connection.execute(
                f"UPDATE users SET {assignments} WHERE username = ?",
                (*usable.values(), username),
            )
        else:
            usable.setdefault("password_hash", _hash_for_cache(password or ""))
            usable.setdefault("created_at", now)
            fields = ", ".join(usable)
            marks = ", ".join("?" for _ in usable)
            connection.execute(
                f"INSERT INTO users ({fields}) VALUES ({marks})",
                tuple(usable.values()),
            )

        if connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' "
            "AND name = 'user_permissions'"
        ).fetchone():
            connection.execute(
                "DELETE FROM user_permissions WHERE username = ?", (username,)
            )
            connection.executemany(
                "INSERT INTO user_permissions "
                "(username, permission_key, allowed, granted_by, granted_at) "
                "VALUES (?, ?, 1, 'mobile-cache', ?)",
                [(username, key, now) for key in grants],
            )
        connection.execute(
            "INSERT INTO app_settings (key, value, updated_at) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value, "
            "updated_at = excluded.updated_at",
            (CACHE_STAMP_KEY, now, now),
        )
        connection.commit()


def cache_online_profile(user, permissions):
    """Refresh cached profile and grants without touching the local hash."""
    cache_online_session(user, None, permissions)


def verify_login(username: str, password: str):
    """Return the active user row on success; otherwise return None."""
    user, _permissions, _error = authenticate_local(username, password)
    return user