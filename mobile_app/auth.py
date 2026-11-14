"""Login verification for the existing users table."""

import hashlib
import hmac
import re
from contextlib import closing

from database import get_connection


_PBKDF2_PREFIX = "pbkdf2_sha256$"
_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


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


def verify_login(username: str, password: str):
    """Return the active user row on success; otherwise return None."""
    username = username.strip()
    if not username or not password:
        return None

    with closing(get_connection()) as connection:
        user = connection.execute(
            "SELECT * FROM users WHERE username = ? LIMIT 1", (username,)
        ).fetchone()

    if user is None or not user["active"]:
        return None
    if not _verify_password(password, user["password_hash"] or ""):
        return None
    return user