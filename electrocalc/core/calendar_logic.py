"""منطق تقویم کارگاه — تقویم شمسی + رویدادها."""

from datetime import datetime, timedelta

import jdatetime

from electrocalc.data.database import get_connection


# ========================================================
# اطلاعات ماه
# ========================================================
def get_today_jalali():
    """تاریخ امروز شمسی."""
    today = datetime.now().date()
    j = jdatetime.date.fromgregorian(date=today)
    return j


def get_month_days(jy, jm):
    """لیست روزهای ماه شمسی + روز هفته شروع."""
    # تعداد روزهای ماه
    if jm <= 6:
        days = 31
    elif jm <= 11:
        days = 30
    else:  # اسفند
        # تشخیص کبیسه
        if jdatetime.date(jy, 12, 1).isleap():
            days = 30
        else:
            days = 29

    # روز هفته اول ماه (0=شنبه, 6=جمعه)
    first = jdatetime.date(jy, jm, 1)
    # jdatetime: 0=شنبه, 6=جمعه
    first_weekday = first.weekday()

    return days, first_weekday


def get_month_name(jm):
    """اسم ماه شمسی."""
    names = [
        "فروردین", "اردیبهشت", "خرداد",
        "تیر", "مرداد", "شهریور",
        "مهر", "آبان", "آذر",
        "دی", "بهمن", "اسفند",
    ]
    return names[jm - 1]


def get_weekday_names():
    """اسم روزهای هفته."""
    return ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه",
            "چهارشنبه", "پنج‌شنبه", "جمعه"]


# ========================================================
# رویدادهای ماه
# ========================================================
def get_month_events(jy, jm):
    """دریافت رویدادهای ماه شمسی.
    خروجی: {تاریخ_میلادی: [(نوع, عنوان, رنگ), ...]}
    """
    days, _ = get_month_days(jy, jm)

    first_j = jdatetime.date(jy, jm, 1)
    last_j = jdatetime.date(jy, jm, days)

    first_g = first_j.togregorian()
    last_g = last_j.togregorian()

    start = first_g.strftime("%Y-%m-%d")
    end = last_g.strftime("%Y-%m-%d")

    events = {}

    conn = get_connection()
    cur = conn.cursor()

    try:
        # ۱) گزارش‌ها
        cur.execute("""
            SELECT report_date, title, status
            FROM reports
            WHERE report_date BETWEEN ? AND ?
        """, (start, end))
        for r in cur.fetchall():
            d = r["report_date"]
            events.setdefault(d, []).append(
                ("گزارش", r["title"] or "گزارش کار", "#7c3aed"))

        # ۲) تسک‌ها
        try:
            cur.execute("""
                SELECT due_date, title
                FROM tasks
                WHERE due_date BETWEEN ? AND ?
            """, (start, end))
            for r in cur.fetchall():
                d = r["due_date"]
                if d:
                    events.setdefault(d, []).append(
                        ("تسک", r["title"] or "تسک", "#f59e0b"))
        except Exception:
            pass

        # ۳) فاکتورها
        cur.execute("""
            SELECT issue_date, number, total
            FROM invoices
            WHERE issue_date BETWEEN ? AND ?
        """, (start, end))
        for r in cur.fetchall():
            d = r["issue_date"]
            events.setdefault(d, []).append(
                ("فاکتور", f"{r['number']} — {r['total']:,.0f}",
                 "#10b981"))

        # ۴) هزینه‌ها
        cur.execute("""
            SELECT expense_date, title, amount
            FROM expenses
            WHERE expense_date BETWEEN ? AND ?
        """, (start, end))
        for r in cur.fetchall():
            d = r["expense_date"]
            if d:
                events.setdefault(d, []).append(
                    ("هزینه", f"{r['title']} — {r['amount']:,.0f}",
                     "#ef4444"))

        # ۵) ساعات کار
        cur.execute("""
            SELECT work_date, username, hours
            FROM timesheets
            WHERE work_date BETWEEN ? AND ?
        """, (start, end))
        for r in cur.fetchall():
            d = r["work_date"]
            events.setdefault(d, []).append(
                ("ساعت کار", f"{r['username']} — {r['hours']:.1f}س",
                 "#06b6d4"))

        return events

    finally:
        conn.close()


# ========================================================
# رویدادهای یک روز خاص
# ========================================================
def get_day_events(greg_date_str):
    """رویدادهای یک روز میلادی مشخص."""
    conn = get_connection()
    cur = conn.cursor()
    events = []

    try:
        # گزارش‌ها
        cur.execute("""
            SELECT title, description, hours, status
            FROM reports WHERE report_date = ?
        """, (greg_date_str,))
        for r in cur.fetchall():
            events.append({
                "type": "گزارش",
                "color": "#7c3aed",
                "title": r["title"],
                "desc": r["description"] or "",
                "extra": f"{r['hours']:.1f} ساعت",
            })

        # تسک‌ها
        try:
            cur.execute("""
                SELECT title, description, priority, status
                FROM tasks WHERE due_date = ?
            """, (greg_date_str,))
            for r in cur.fetchall():
                events.append({
                    "type": "تسک",
                    "color": "#f59e0b",
                    "title": r["title"],
                    "desc": r["description"] or "",
                    "extra": f"اولویت: {r['priority']}",
                })
        except Exception:
            pass

        # فاکتورها
        cur.execute("""
            SELECT number, total, status
            FROM invoices WHERE issue_date = ?
        """, (greg_date_str,))
        for r in cur.fetchall():
            events.append({
                "type": "فاکتور",
                "color": "#10b981",
                "title": r["number"],
                "desc": f"وضعیت: {r['status']}",
                "extra": f"{r['total']:,.0f} تومان",
            })

        # هزینه‌ها
        cur.execute("""
            SELECT title, amount, category
            FROM expenses WHERE expense_date = ?
        """, (greg_date_str,))
        for r in cur.fetchall():
            events.append({
                "type": "هزینه",
                "color": "#ef4444",
                "title": r["title"],
                "desc": r["category"] or "",
                "extra": f"{r['amount']:,.0f} تومان",
            })

        # ساعات کار
        cur.execute("""
            SELECT username, hours, description
            FROM timesheets WHERE work_date = ?
        """, (greg_date_str,))
        for r in cur.fetchall():
            events.append({
                "type": "ساعت کار",
                "color": "#06b6d4",
                "title": r["username"],
                "desc": r["description"] or "",
                "extra": f"{r['hours']:.1f} ساعت",
            })

        return events

    finally:
        conn.close()