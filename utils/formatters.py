# utils/formatters.py
"""Display formatting helpers."""


def format_currency(value: float, currency: str = "USD") -> str:
    return f"{currency} {value:,.2f}"


def format_phone(value: str | None) -> str:
    return value or "—"
