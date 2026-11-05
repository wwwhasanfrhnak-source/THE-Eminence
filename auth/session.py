# auth/session.py
"""In-memory current user session with automatic expiration."""

from datetime import datetime, timedelta

from config.constants import PERMISSIONS
from config.settings import SESSION_TIMEOUT_MINUTES
from core.models import User


class Session:
    def __init__(self, timeout_minutes: int = SESSION_TIMEOUT_MINUTES, theme: str = "dark"):
        self.timeout = timedelta(minutes=timeout_minutes)
        self.user: User | None = None
        self.permissions: tuple[str, ...] = ()
        self.theme = theme
        self.last_activity: datetime | None = None

    @property
    def current_user(self) -> User | None:
        return self.user

    @property
    def is_authenticated(self) -> bool:
        return (
            self.user is not None
            and self.last_activity is not None
            and datetime.now() - self.last_activity < self.timeout
        )

    def start(self, user: User) -> None:
        self.user = user
        self.permissions = tuple(PERMISSIONS.get(user.role, ()))
        self.touch()

    def touch(self) -> None:
        if self.user is not None:
            self.last_activity = datetime.now()

    def clear(self) -> User | None:
        user = self.user
        self.user = None
        self.permissions = ()
        self.last_activity = None
        return user
