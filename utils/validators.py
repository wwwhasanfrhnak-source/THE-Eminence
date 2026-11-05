# utils/validators.py
"""Validation helpers for forms and account creation."""

import re
from datetime import date

from core.exceptions import ValidationError

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")


def validate_username(username: str) -> str:
    value = username.strip()
    if not USERNAME_PATTERN.fullmatch(value):
        raise ValidationError("Username must be 3–32 letters, digits, dots, dashes, or underscores")
    return value


def validate_password(password: str) -> None:
    if len(password) < 8:
        raise ValidationError("Password must contain at least 8 characters")


def validate_email(email: str) -> str:
    value = email.strip()
    if not EMAIL_PATTERN.fullmatch(value):
        raise ValidationError("Enter a valid email address")
    return value


def validate_customer(values: dict) -> dict:
    data = {
        key: value
        for key, value in values.items()
        if key in ("name", "type", "phone", "email", "address", "national_id", "notes")
    }
    if "name" in data and (not data["name"] or not str(data["name"]).strip()):
        raise ValidationError("Customer name is required")
    if data.get("email"):
        data["email"] = validate_email(data["email"])
    return data


def validate_project(values: dict) -> dict:
    data = {
        key: value
        for key, value in values.items()
        if key
        in ("customer_id", "title", "description", "status", "budget", "start_date", "end_date")
    }
    if "title" in data and (not data["title"] or not str(data["title"]).strip()):
        raise ValidationError("Project title is required")
    if "status" in data and not data["status"]:
        data["status"] = "pending"
    if "budget" in data and data["budget"] is None:
        data["budget"] = 0
    if "budget" in data:
        try:
            data["budget"] = float(data["budget"] or 0)
        except (ValueError, TypeError) as exc:
            raise ValidationError("Budget must be a number") from exc
        if data["budget"] < 0:
            raise ValidationError("Budget cannot be negative")
    if "status" in data and data["status"] not in (
        "pending",
        "in_progress",
        "completed",
        "cancelled",
    ):
        raise ValidationError("Invalid project status")
    for field in ("start_date", "end_date"):
        if data.get(field):
            try:
                date.fromisoformat(data[field])
            except (TypeError, ValueError) as exc:
                raise ValidationError(
                    f"{field.replace('_', ' ').title()} must be YYYY-MM-DD"
                ) from exc
    return data
