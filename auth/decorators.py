# auth/decorators.py
"""Decorators for session and permission-protected actions."""

from functools import wraps

from auth.permissions import require_permission
from core.exceptions import AuthenticationError


def login_required(function):
    @wraps(function)
    def wrapper(self, *args, **kwargs):
        if not self.session.is_authenticated:
            raise AuthenticationError("Please sign in again")
        self.session.touch()
        return function(self, *args, **kwargs)

    return wrapper


def permission_required(permission: str):
    def decorate(function):
        @wraps(function)
        def wrapper(self, *args, **kwargs):
            if not self.session.is_authenticated:
                raise AuthenticationError("Please sign in again")
            require_permission(self.session.user, permission)
            self.session.touch()
            return function(self, *args, **kwargs)

        return wrapper

    return decorate
