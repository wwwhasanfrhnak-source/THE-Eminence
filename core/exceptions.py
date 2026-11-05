# core/exceptions.py
"""Domain-specific exceptions."""


class EminenceError(Exception):
    """Base application exception."""


class AuthenticationError(EminenceError):
    """Raised when authentication fails."""


class AuthorizationError(EminenceError):
    """Raised when a user lacks permission."""


class ValidationError(EminenceError):
    """Raised when user-provided data is invalid."""


class NotFoundError(EminenceError):
    """Raised when a requested record does not exist."""
