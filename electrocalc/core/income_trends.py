"""Read-only financial summaries and time series for the Tk dashboard."""

from datetime import date, timedelta

from electrocalc.data.database import get_connection

# These are the invoice states already used by electrocalc.core.finance.
ELIGIBLE_INVOICE_STATUSES = ("ارسال‌شده", "پرداخت‌شده")
_MONTH_NAMES = (
    "ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن",
    "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر",
)
_WEEKDAY_NAMES = ("دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه")


def _shift_month(year, month, offset):
    month_index = year * 12 + month - 1 + offset
    return date(month_index // 12, month_index % 12 + 1, 1)


def _period_bounds(today):
    week_start = today - timedelta(days=today.weekday())
    month_start = date(today.year, today.month, 1)
    next_month = _shift_month(today.year, today.month, 1)
    return {
        "today": (today, today + timedelta(days=1)),
        "week": (week_start, week_start + timedelta(days=7)),
        "month": (month_start, next_month),
    }


def get_financial_dashboard(today=None):
    """Fetch KPI totals and four billed/received series with SELECT-only SQL.

    Billed revenue is invoices.total; received revenue is invoices.paid. Both
    follow the same eligible statuses as the existing finance module. Invoice
    items are intentionally not joined: invoice totals are already calculated
    from items by the existing invoice create/update workflow, and joining would
    multiply invoice totals for invoices with multiple items.
    """
    today = today or date.today()
    bounds = _period_bounds(today)
    daily_start = today - timedelta(days=29)
    weekly_start = today - timedelta(days=today.weekday()) - timedelta(weeks=11)
    monthly_start = _shift_month(today.year, today.month, -11)
    year_start = date(min(today.year, monthly_start.year), 1, 1)
    tomorrow = today + timedelta(days=1)
    statuses = ELIGIBLE_INVOICE_STATUSES

    summaries = {"all": {"invoiced": 0.0, "received": 0.0}}
    for key in bounds:
        summaries[key] = {"invoiced": 0.0, "received": 0.0}

    daily = {daily_start + timedelta(days=i): [0.0, 0.0] for i in range(30)}
    weekly = {}
    for i in range(12):
        start = weekly_start + timedelta(weeks=i)
        weekly[start] = [0.0, 0.0]
    monthly = {}
    cursor = monthly_start
    while cursor < _shift_month(today.year, today.month, 1):
        monthly[(cursor.year, cursor.month)] = [0.0, 0.0]
        cursor = _shift_month(cursor.year, cursor.month, 1)

    connection = get_connection()
    try:
        cursor = connection.cursor()
        # One bounded scan supplies the recent charts and period KPI values.
        cursor.execute(
            """SELECT issue_date, COALESCE(total, 0) AS total,
                      COALESCE(paid, 0) AS paid
               FROM invoices
               WHERE status IN (?, ?)
                 AND issue_date >= ? AND issue_date < ?""",
            (*statuses, year_start.isoformat(), tomorrow.isoformat()),
        )
        for row in cursor.fetchall():
            try:
                invoice_day = date.fromisoformat(str(row["issue_date"])[:10])
                billed = float(row["total"] or 0)
                received = float(row["paid"] or 0)
            except (TypeError, ValueError):
                continue

            for key, (start, end) in bounds.items():
                if start <= invoice_day < end:
                    summaries[key]["invoiced"] += billed
                    summaries[key]["received"] += received
            if invoice_day in daily:
                daily[invoice_day][0] += billed
                daily[invoice_day][1] += received
            week_key = invoice_day - timedelta(days=invoice_day.weekday())
            if week_key in weekly:
                weekly[week_key][0] += billed
                weekly[week_key][1] += received
            month_key = (invoice_day.year, invoice_day.month)
            if month_key in monthly:
                monthly[month_key][0] += billed
                monthly[month_key][1] += received

        # All-time KPI and yearly comparison are grouped by SQLite, avoiding a
        # Python-side full-table scan on large invoice databases.
        cursor.execute(
            """SELECT COALESCE(SUM(total), 0) AS invoiced,
                      COALESCE(SUM(paid), 0) AS received
               FROM invoices WHERE status IN (?, ?)""",
            statuses,
        )
        row = cursor.fetchone()
        summaries["all"] = {
            "invoiced": float(row["invoiced"] or 0),
            "received": float(row["received"] or 0),
        }
        cursor.execute(
            """SELECT substr(issue_date, 1, 4) AS year,
                      COALESCE(SUM(total), 0) AS invoiced,
                      COALESCE(SUM(paid), 0) AS received
               FROM invoices
               WHERE status IN (?, ?) AND issue_date < ?
               GROUP BY substr(issue_date, 1, 4)
               ORDER BY year""",
            (*statuses, tomorrow.isoformat()),
        )
        yearly_data = {}
        for row in cursor.fetchall():
            try:
                year = int(row["year"])
            except (TypeError, ValueError):
                continue
            yearly_data[year] = [float(row["invoiced"] or 0),
                                 float(row["received"] or 0)]
    finally:
        connection.close()

    def series(labels, values):
        return {
            "labels": labels,
            "invoiced": [v[0] for v in values],
            "received": [v[1] for v in values],
        }

    daily_dates = list(daily)
    weekly_dates = list(weekly)
    month_keys = list(monthly)
    years = list(range(min(yearly_data, default=today.year), today.year + 1))
    yearly_values = [yearly_data.get(year, [0.0, 0.0]) for year in years]
    return {
        "summary": summaries,
        "daily": series([d.strftime("%m/%d") for d in daily_dates],
                         [daily[d] for d in daily_dates]),
        "weekly": series([f"{d.month:02d}/{d.day:02d}" for d in weekly_dates],
                          [weekly[d] for d in weekly_dates]),
        "monthly": series([_MONTH_NAMES[m - 1][:3] for _, m in month_keys],
                           [monthly[k] for k in month_keys]),
        "yearly": series([str(y) for y in years], yearly_values),
    }
