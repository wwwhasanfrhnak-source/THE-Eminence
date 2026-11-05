# core/services/auth_service.py
"""Credential verification and user account management."""

import bcrypt

from core.database import Database
from core.exceptions import AuthenticationError, ValidationError
from core.models import User
from core.repository import Repository
from utils.validators import validate_email, validate_password, validate_username


class AuthService:
    def __init__(self, database: Database | None = None):
        self.db = database or Database()
        self.repository = Repository(self.db)

    @staticmethod
    def _as_user(row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            full_name=row["full_name"],
            role=row["role"],
            email=row["email"],
            phone=row["phone"],
            is_active=bool(row["is_active"]),
        )

    def authenticate(self, username: str, password: str) -> User:
        username = username.strip()
        row = self.db.fetch_one("SELECT * FROM users WHERE username = ?", (username,))
        if row is None or not row["is_active"]:
            self._log_failed_login(username, row["id"] if row is not None else None)
            raise AuthenticationError("Invalid username or password")
        if not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
            self._log_failed_login(username, row["id"])
            raise AuthenticationError("Invalid username or password")
        with self.db.transaction() as connection:
            connection.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (row["id"],)
            )
            connection.execute(
                "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
                (row["id"], "login", "Successful login"),
            )
        return self._as_user(row)

    def _log_failed_login(self, username: str, user_id: int | None) -> None:
        with self.db.transaction() as connection:
            connection.execute(
                "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
                (user_id, "login_failed", f"username={username}"),
            )

    def logout(self, user: User) -> None:
        self.repository.log_activity("logout", "User logged out", user.id)

    def change_password(self, user_id: int, current_password: str, new_password: str) -> None:
        validate_password(new_password)
        row = self.db.fetch_one("SELECT password_hash FROM users WHERE id = ?", (user_id,))
        if row is None or not bcrypt.checkpw(
            current_password.encode("utf-8"), row["password_hash"].encode("utf-8")
        ):
            raise AuthenticationError("Current password is incorrect")
        password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        with self.db.transaction() as connection:
            connection.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?", (password_hash, user_id)
            )
            connection.execute(
                "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
                (user_id, "change_password", "Password changed"),
            )

    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        role: str = "user",
        email: str | None = None,
        phone: str | None = None,
        actor_id: int | None = None,
    ) -> int:
        username = validate_username(username)
        validate_password(password)
        if not full_name or not full_name.strip():
            raise ValidationError("Full name is required")
        if role not in ("admin", "manager", "user"):
            raise ValidationError("Role must be admin, manager, or user")
        if email:
            email = validate_email(email)
        password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        with self.db.transaction() as connection:
            try:
                cursor = connection.execute(
                    "INSERT INTO users (username, password_hash, full_name, role, email, phone) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (username, password_hash, full_name.strip(), role, email, phone),
                )
            except Exception as exc:
                if "UNIQUE constraint failed" in str(exc):
                    raise ValidationError("That username is already in use") from exc
                raise
            connection.execute(
                "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
                (actor_id, "create_user", f"username={username}"),
            )
            return int(cursor.lastrowid)
