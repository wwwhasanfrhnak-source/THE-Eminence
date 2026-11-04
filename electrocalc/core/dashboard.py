"""آمار داشبورد."""

from electrocalc.data.database import get_connection


def get_summary():
    """آمار کلی."""
    conn = get_connection()
    cur = conn.cursor()
    result = {}

    cur.execute("SELECT COUNT(*) AS c FROM projects")
    result["projects"] = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM users WHERE active=1")
    result["users"] = cur.fetchone()["c"]

    cur.execute("SELECT COALESCE(SUM(hours),0) AS s FROM timesheets")
    result["total_hours"] = cur.fetchone()["s"]

    cur.execute("SELECT COALESCE(SUM(amount),0) AS s FROM expenses")
    result["total_expenses"] = cur.fetchone()["s"]

    cur.execute("SELECT COALESCE(SUM(total_price),0) AS s FROM materials")
    result["total_materials"] = cur.fetchone()["s"]

    cur.execute("SELECT COUNT(*) AS c FROM reports WHERE status='pending'")
    result["pending_reports"] = cur.fetchone()["c"]

    cur.execute("SELECT COUNT(*) AS c FROM expenses WHERE status='pending'")
    result["pending_expenses"] = cur.fetchone()["c"]

    conn.close()
    return result


def hours_per_engineer():
    """مجموع ساعات کار هر مهندس."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT username, COALESCE(SUM(hours),0) AS total
        FROM timesheets
        GROUP BY username
        ORDER BY total DESC
        LIMIT 8
    """)
    rows = [(r["username"], r["total"]) for r in cur.fetchall()]
    conn.close()
    return rows


def project_status_counts():
    """تعداد پروژه‌ها به تفکیک وضعیت."""
    from electrocalc.core.projects import STATUS_FA
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT status, COUNT(*) AS c FROM projects GROUP BY status")
    rows = []
    for r in cur.fetchall():
        rows.append((STATUS_FA.get(r["status"], r["status"]), r["c"]))
    conn.close()
    return rows


def expenses_per_project():
    """هزینه هر پروژه (هزینه‌ها + مصالح)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.name,
               COALESCE((SELECT SUM(amount) FROM expenses WHERE project_id=p.id), 0) +
               COALESCE((SELECT SUM(total_price) FROM materials WHERE project_id=p.id), 0)
               AS total
        FROM projects p
        ORDER BY total DESC
        LIMIT 8
    """)
    rows = [(r["name"], r["total"]) for r in cur.fetchall()]
    conn.close()
    return rows