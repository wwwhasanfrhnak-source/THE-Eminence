"""آمار عملکرد مهندسین."""

from datetime import datetime, timedelta
from electrocalc.data.database import get_connection


def get_summary_period(period="all"):
    """
    آمار کلی در بازه مشخص.

    period: week | month | all
    """
    conn = get_connection()
    cur = conn.cursor()

    # تاریخ شروع
    if period == "week":
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    elif period == "month":
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        start = "1900-01-01"

    # ---- ساعات هر مهندس ----
    cur.execute("""
        SELECT username, COALESCE(SUM(hours),0) AS total
        FROM timesheets
        WHERE work_date >= ?
        GROUP BY username
        ORDER BY total DESC
    """, (start,))
    hours = [(r["username"], r["total"]) for r in cur.fetchall()]

    # ---- تعداد گزارش‌ها هر مهندس ----
    cur.execute("""
        SELECT author,
               COUNT(*) AS total,
               SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) AS approved,
               SUM(CASE WHEN status='rejected' THEN 1 ELSE 0 END) AS rejected,
               SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) AS pending
        FROM reports
        WHERE report_date >= ?
        GROUP BY author
    """, (start,))
    reports = {}
    for r in cur.fetchall():
        reports[r["author"]] = {
            "total": r["total"],
            "approved": r["approved"],
            "rejected": r["rejected"],
            "pending": r["pending"],
        }

    # ---- هزینه هر مهندس ----
    cur.execute("""
        SELECT created_by, COALESCE(SUM(amount),0) AS total
        FROM expenses
        WHERE expense_date >= ?
        GROUP BY created_by
        ORDER BY total DESC
    """, (start,))
    expenses = [(r["created_by"], r["total"]) for r in cur.fetchall()
                if r["created_by"]]

    # ---- تعداد پروژه‌های هر مهندس ----
    cur.execute("""
        SELECT username, COUNT(*) AS total
        FROM project_members
        GROUP BY username
        ORDER BY total DESC
    """)
    projects = [(r["username"], r["total"]) for r in cur.fetchall()]

    conn.close()

    return {
        "hours": hours,
        "reports": reports,
        "expenses": expenses,
        "projects": projects,
    }


def get_engineer_details(username):
    """جزئیات یه مهندس خاص."""
    conn = get_connection()
    cur = conn.cursor()

    result = {"username": username, "full_name": "", "role": ""}

    # اطلاعات کاربر
    cur.execute("SELECT full_name, role FROM users WHERE username = ?",
                (username,))
    row = cur.fetchone()
    if row:
        result["full_name"] = row["full_name"] or username
        result["role"] = row["role"]

    # ساعات کار (کل)
    cur.execute("""
        SELECT COALESCE(SUM(hours),0) AS s FROM timesheets
        WHERE username = ?
    """, (username,))
    result["total_hours"] = cur.fetchone()["s"]

    # ساعات این ماه
    start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    cur.execute("""
        SELECT COALESCE(SUM(hours),0) AS s FROM timesheets
        WHERE username = ? AND work_date >= ?
    """, (username, start))
    result["month_hours"] = cur.fetchone()["s"]

    # ساعات این هفته
    start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    cur.execute("""
        SELECT COALESCE(SUM(hours),0) AS s FROM timesheets
        WHERE username = ? AND work_date >= ?
    """, (username, start))
    result["week_hours"] = cur.fetchone()["s"]

    # گزارش‌ها
    cur.execute("""
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN status='approved' THEN 1 ELSE 0 END) AS approved,
            SUM(CASE WHEN status='rejected' THEN 1 ELSE 0 END) AS rejected,
            SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) AS pending
        FROM reports
        WHERE author = ?
    """, (username,))
    r = cur.fetchone()
    result["reports"] = {
        "total": r["total"] or 0,
        "approved": r["approved"] or 0,
        "rejected": r["rejected"] or 0,
        "pending": r["pending"] or 0,
    }

    # پروژه‌ها
    cur.execute("""
        SELECT COUNT(*) AS c FROM project_members WHERE username = ?
    """, (username,))
    result["projects"] = cur.fetchone()["c"]

    # هزینه‌ها
    cur.execute("""
        SELECT COALESCE(SUM(amount),0) AS s FROM expenses
        WHERE created_by = ?
    """, (username,))
    result["total_expenses"] = cur.fetchone()["s"]

    # گزارش‌های هفتگی (برای نمودار خطی)
    weekly = []
    for i in range(6, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        cur.execute("""
            SELECT COUNT(*) AS c FROM reports
            WHERE author = ? AND report_date = ?
        """, (username, d))
        weekly.append(cur.fetchone()["c"])
    result["weekly_reports"] = weekly

    conn.close()
    return result


def get_weekly_report_activity(period="all"):
    """
    فعالیت گزارش‌دهی در ۷ روز اخیر (برای نمودار خطی).
    """
    conn = get_connection()
    cur = conn.cursor()
    result = []

    for i in range(6, -1, -1):
        d = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        cur.execute("""
            SELECT COUNT(*) AS c FROM reports WHERE report_date = ?
        """, (d,))
        count = cur.fetchone()["c"]
        result.append((d, count))

    conn.close()
    return result