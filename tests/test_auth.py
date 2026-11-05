# tests/test_auth.py
"""Authentication, account creation, and permission tests."""

import pytest

from core.exceptions import AuthenticationError, ValidationError
from core.services.auth_service import AuthService
from auth.permissions import has_permission
from auth.session import Session


def test_default_admin_authenticates_and_logs(database):
    service = AuthService(database)
    user = service.authenticate("admin", "admin123")
    assert user.username == "admin"
    assert user.role == "admin"
    service.logout(user)
    actions = [
        row["action"] for row in database.fetch_all("SELECT action FROM activity_log ORDER BY id")
    ]
    assert actions == ["login", "logout"]


def test_invalid_password_is_rejected(database):
    with pytest.raises(AuthenticationError):
        AuthService(database).authenticate("admin", "wrong-password")


def test_user_creation_hashes_password_and_checks_permissions(database):
    service = AuthService(database)
    user_id = service.create_user("field.user", "correct-horse-battery", "Field User", "user")
    user = database.fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))
    assert user["password_hash"] != "correct-horse-battery"
    from core.models import User

    ordinary_user = User(user["id"], user["username"], user["full_name"], user["role"])
    assert has_permission(ordinary_user, "projects")
    assert not has_permission(ordinary_user, "users")


def test_duplicate_user_and_weak_password_are_rejected(database):
    service = AuthService(database)
    with pytest.raises(ValidationError):
        service.create_user("admin", "correct-horse-battery", "Duplicate")
    with pytest.raises(ValidationError):
        service.create_user("another", "short", "Another")


def test_admin_can_change_password(database):
    service = AuthService(database)
    user = service.authenticate("admin", "admin123")
    service.change_password(user.id, "admin123", "new-admin-password")
    assert service.authenticate("admin", "new-admin-password").id == user.id


def test_session_expires_without_losing_user_for_logout_audit(database):
    user = AuthService(database).authenticate("admin", "admin123")
    session = Session(timeout_minutes=0)
    session.start(user)
    assert not session.is_authenticated
    assert session.clear() == user
