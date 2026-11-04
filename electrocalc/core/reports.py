"""منطق مدیریت گزارش‌ها — با اعلان خودکار."""

from datetime import datetime
from electrocalc.data.database import get_connection


STATUS_FA = {
    "pending": "در انتظار تأیید",
    "approved": "تأیید شده",
    "rejected": "رد شده",
}


def create_report(project_id, author, report_date, title,
                  description="", hours=0.0):
    if not title.strip():
        raise ValueError("عنوان گزارش الزامی است.")
    if not project_id:
        raise ValueError("پروژه را انتخاب کنید.")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO reports
            (project_id, author, report_date, title, description,
             hours, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (project_id, author, report_date, title.strip(),
              description, hours, datetime.now().isoformat()))
        conn.commit()
        rid = cur.lastrowid
    finally:
        conn.close()

    # ✅ اعلان خودکار به مدیرها
    try:
        from electrocalc.core import notifications as notif
        notif.notify_admins(
            title="📝 گزارش جدید ثبت شد",
            message=f"{author} گزارش «{title}» را ثبت کرد",
            category="report",
        )
    except Exception:
        pass

    return rid


def list_reports(search="", author=None, status=None):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT r.*, p.name AS project_name
        FROM reports r
        LEFT JOIN projects p ON p.id = r.project_id
        WHERE 1=1
    """
    params = []
    if search:
        query += " AND (r.title LIKE ? OR r.description LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    if author:
        query += " AND r.author = ?"
        params.append(author)
    if status:
        query += " AND r.status = ?"
        params.append(status)
    query += " ORDER BY r.id DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def get_report(rid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.*, p.name AS project_name
        FROM reports r
        LEFT JOIN projects p ON p.id = r.project_id
        WHERE r.id = ?
    """, (rid,))
    row = cur.fetchone()
    conn.close()
    return row


def update_report(rid, project_id, report_date, title,
                  description="", hours=0.0):
    if not title.strip():
        raise ValueError("عنوان گزارش الزامی است.")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE reports
            SET project_id = ?, report_date = ?, title = ?,
                description = ?, hours = ?
            WHERE id = ?
        """, (project_id, report_date, title.strip(),
              description, hours, rid))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def approve_report(rid, approved_by):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE reports
            SET status = 'approved', approved_by = ?, approved_at = ?
            WHERE id = ?
        """, (approved_by, datetime.now().isoformat(), rid))
        conn.commit()
    finally:
        conn.close()

    # ✅ اعلان به صاحب گزارش
    try:
        r = get_report(rid)
        if r:
            from electrocalc.core import notifications as notif
            notif.create_notification(
                username=r["author"],
                title="✅ گزارش شما تأیید شد",
                message=f"گزارش «{r['title']}» توسط {approved_by} تأیید شد",
                category="approval",
            )
    except Exception:
        pass


def reject_report(rid, approved_by):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE reports
            SET status = 'rejected', approved_by = ?, approved_at = ?
            WHERE id = ?
        """, (approved_by, datetime.now().isoformat(), rid))
        conn.commit()
    finally:
        conn.close()

    # ✅ اعلان به صاحب گزارش
    try:
        r = get_report(rid)
        if r:
            from electrocalc.core import notifications as notif
            notif.create_notification(
                username=r["author"],
                title="❌ گزارش شما رد شد",
                message=f"گزارش «{r['title']}» توسط {approved_by} رد شد",
                category="danger",
            )
    except Exception:
        pass


def delete_report(rid):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM reports WHERE id = ?", (rid,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()