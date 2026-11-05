# auth/session.py
"""In-memory current user session with automatic expiration."""

from datetime import datetime, timedelta

from config.settings import SESSION_TIMEOUT_MINUTES
from core.models import User


class Session:
    def __init__(self, timeout_minutes: int = SESSION_TIMEOUT_MINUTES):
        self.timeout = timedelta(minutes=timeout_minutes)
        self.user: User | None = None
        self.last_activity: datetime | None = None

    @property
    def is_authenticated(self) -> bool:
        if self.user is None or self.last_activity is None:
            return False
        if datetime.now() - self.last_activity >= self.timeout:
            return False
        return True

    def start(self, user: User) -> None:
        self.user = user
        self.touch()

    def touch(self) -> None:
        if self.user is not None:
            self.last_activity = datetime.now()

    def clear(self) -> User | None:
        user = self.user
        self.user = None
        self.last_activity = None
        return user
