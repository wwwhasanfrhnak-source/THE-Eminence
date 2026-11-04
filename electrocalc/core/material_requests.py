"""درخواست مصالح — مهندس می‌سازه، مدیر تأیید می‌کنه، برای مشتری می‌ره."""

from datetime import datetime
from electrocalc.data.database import get_connection


STATUS_FA = {
    "pending": "در انتظار بررسی",
    "approved": "تأیید شده",
    "sent": "ارسال شده به مشتری",
    "rejected": "رد شده",
}


def create_request(project_id, requester, title, description="",
                    items_text="", total_estimate=0, customer_name=""):
    if not title.strip():
        raise ValueError("عنوان درخواست الزامی است.")
    if not project_id:
        raise ValueError("پروژه الزامی است.")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO material_requests
            (project_id, requester, title, description, items_text,
             total_estimate, status, customer_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        """, (project_id, requester, title.strip(), description,
              items_text, total_estimate, customer_name,
              datetime.now().isoformat()))
        conn.commit()
        rid = cur.lastrowid
    finally:
        conn.close()

    # اعلان به مدیرها
    try:
        from electrocalc.core import notifications as notif
        notif.notify_admins(
            title="📋 درخواست مصالح جدید",
            message=f"{requester} برای پروژه درخواست «{title}» ثبت کرد",
            category="info",
        )
    except Exception:
        pass

    return rid


def list_requests(requester=None, status=None, project_id=None):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT r.*, p.name AS project_name
        FROM material_requests r
        LEFT JOIN projects p ON p.id = r.project_id
        WHERE 1=1
    """
    params = []
    if requester:
        query += " AND r.requester = ?"
        params.append(requester)
    if status:
        query += " AND r.status = ?"
        params.append(status)
    if project_id:
        query += " AND r.project_id = ?"
        params.append(project_id)
    query += " ORDER BY r.id DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def get_request(rid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.*, p.name AS project_name
        FROM material_requests r
        LEFT JOIN projects p ON p.id = r.project_id
        WHERE r.id = ?
    """, (rid,))
    row = cur.fetchone()
    conn.close()
    return row


def update_status(rid, new_status, admin_note="", approved_by=""):
    """تغییر وضعیت درخواست (فقط admin)."""
    if new_status not in STATUS_FA:
        raise ValueError("وضعیت نامعتبر")
    conn = get_connection()
    cur = conn.cursor()
    try:
        now = datetime.now().isoformat()
        cur.execute("""
            UPDATE material_requests
            SET status = ?, admin_note = ?, approved_by = ?, approved_at = ?
            WHERE id = ?
        """, (new_status, admin_note, approved_by, now, rid))
        conn.commit()

        # اطلاع به مهندس
        try:
            req = get_request(rid)
            if req:
                from electrocalc.core import notifications as notif
                title_map = {
                    "approved": "✅ درخواست شما تأیید شد",
                    "sent": "📤 درخواست شما به مشتری ارسال شد",
                    "rejected": "❌ درخواست شما رد شد",
                }
                notif.create_notification(
                    username=req["requester"],
                    title=title_map.get(new_status, "وضعیت درخواست تغییر کرد"),
                    message=f"درخواست «{req['title']}»",
                    category="approval" if new_status == "approved"
                             else "danger" if new_status == "rejected"
                             else "info",
                )
        except Exception:
            pass

        return cur.rowcount > 0
    finally:
        conn.close()


def delete_request(rid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM material_requests WHERE id = ?", (rid,))
    conn.commit()
    conn.close()


def count_pending():
    """تعداد درخواست‌های در انتظار تأیید."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) AS c FROM material_requests
        WHERE status = 'pending'
    """)
    row = cur.fetchone()
    conn.close()
    return row["c"] if row else 0


def get_customers_list():
    """لیست مشتریان برای dropdown."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT customer FROM projects WHERE customer IS NOT NULL AND customer != '' ORDER BY customer")
    rows = cur.fetchall()
    conn.close()
    return [r["customer"] for r in rows]