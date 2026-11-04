"""Read-only invoice income aggregates used by dashboard charts."""

from datetime import date

from electrocalc.data.database import get_connection


_WEEKDAY_LABELS = ("د", "س", "چ", "پ", "ج", "ش", "ی")
_MONTH_LABELS = (
    "ژان", "فور", "مار", "آور", "مه", "ژوئن",
    "ژوئیه", "اوت", "سپ", "اکت", "نو", "دس",
)
_ELIGIBLE_STATUSES = ("ارسال‌شده", "پرداخت‌شده")


def _shift_month(year, month, offset):
    """Return the first day of a month shifted by offset calendar months."""
    month_index = year * 12 + month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def get_income_trends(today=None):
    """Return daily income for the last seven days and monthly income for six months.

    This mirrors the existing finance calculation: ``invoices.total`` is counted
    only when status is sent or paid. Draft/cancelled invoices are excluded.
    Uses the application's existing database connection and performs read-only
    SELECTs; it never initializes, alters, or writes to the database.
    """
    today = today or date.today()
    week_start = date.fromordinal(today.toordinal() - 6)
    month_start = _shift_month(today.year, today.month, -5)
    next_month = _shift_month(today.year, today.month, 1)
    query_start = min(week_start, month_start)

    weekly_totals = {
        date.fromordinal(week_start.toordinal() + i): 0.0
        for i in range(7)
    }
    monthly_totals = {}
    cursor_month = month_start
    while cursor_month < next_month:
        monthly_totals[(cursor_month.year, cursor_month.month)] = 0.0
        cursor_month = _shift_month(cursor_month.year, cursor_month.month, 1)

    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """SELECT issue_date, COALESCE(SUM(total), 0) AS income
               FROM invoices
               WHERE status IN (?, ?)
                 AND issue_date >= ? AND issue_date < ?
               GROUP BY issue_date""",
            (
                *_ELIGIBLE_STATUSES,
                query_start.isoformat(),
                next_month.isoformat(),
            ),
        )
        for row in cursor.fetchall():
            try:
                invoice_day = date.fromisoformat(str(row["issue_date"])[:10])
                amount = float(row["income"] or 0)
            except (TypeError, ValueError):
                # Skip malformed legacy dates/amounts without breaking dashboard refresh.
                continue

            if invoice_day in weekly_totals:
                weekly_totals[invoice_day] += amount
            month_key = (invoice_day.year, invoice_day.month)
            if month_key in monthly_totals:
                monthly_totals[month_key] += amount
    finally:
        connection.close()

    weekly_dates = sorted(weekly_totals)
    month_keys = list(monthly_totals)
    return {
        "weekly": {
            # Python weekday: Monday=0; dashboard labels follow this same order.
            "labels": [_WEEKDAY_LABELS[day.weekday()] for day in weekly_dates],
            "values": [weekly_totals[day] for day in weekly_dates],
        },
        "monthly": {
            "labels": [_MONTH_LABELS[month - 1] for _, month in month_keys],
            "values": [monthly_totals[key] for key in month_keys],
        },
    }
