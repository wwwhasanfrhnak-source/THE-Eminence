# auth/permissions.py
"""Role-based permission checks."""

from core.exceptions import AuthorizationError
from core.models import User


def has_permission(user: User, permission: str) -> bool:
    if not user.is_active:
        return False
    return (
        user.role == "admin"
        or permission == "settings"
        or permission
        in {
            "manager": {"dashboard", "customers", "projects", "reports"},
            "user": {"dashboard", "customers", "projects"},
        }.get(user.role, set())
    )


def require_permission(user: User, permission: str) -> None:
    if not has_permission(user, permission):
        raise AuthorizationError(f"Permission denied: {permission}")
