# utils/date_helper.py
"""Gregorian and optional Jalali date formatting."""

from datetime import date, datetime


def today_iso() -> str:
    return date.today().isoformat()


def format_date(value: str | date | datetime, jalali: bool = False) -> str:
    parsed = value if isinstance(value, (date, datetime)) else date.fromisoformat(value)
    if jalali:
        try:
            import jdatetime
        except ImportError as exc:
            raise RuntimeError("Install jdatetime to format Jalali dates") from exc
        gregorian_date = parsed.date() if isinstance(parsed, datetime) else parsed
        return jdatetime.date.fromgregorian(date=gregorian_date).strftime("%Y/%m/%d")
    return parsed.strftime("%Y-%m-%d")
