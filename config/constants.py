# config/constants.py
"""Shared application constants."""

APP_NAME = "THE Eminence"
APP_VERSION = "0.1.0"
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"
DEFAULT_ADMIN_NAME = "Administrator"
DEFAULT_SESSION_TIMEOUT_MINUTES = 30

ROLES = ("admin", "manager", "user")
PERMISSIONS = {
    "admin": ("*",),
    "manager": ("dashboard", "customers", "projects", "reports"),
    "user": ("dashboard", "customers", "projects"),
}

ROUTES = (
    ("dashboard", "Dashboard"),
    ("customers", "Customers"),
    ("projects", "Projects"),
    ("reports", "Reports"),
    ("users", "Users"),
    ("settings", "Settings"),
)
