"""منطق مدیریت تسک‌ها (کارهای پروژه)."""

from datetime import datetime
from electrocalc.data.database import get_connection


PRIORITY_FA = {
    "low": "🟢 کم",
    "medium": "🟡 متوسط",
    "high": "🟠 زیاد",
    "urgent": "🔴 فوری",
}

STATUS_FA = {
    "pending": "در انتظار",
    "in_progress": "در حال انجام",
    "done": "انجام شده",
    "cancelled": "لغو شده",
}


def create_task(project_id, title, description="", assigned_to="",
                priority="medium", due_date="", created_by=""):
    if not title.strip():
        raise ValueError("عنوان تسک الزامی است.")
    if not project_id:
        raise ValueError("پروژه الزامی است.")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO tasks
            (project_id, title, description, assigned_to, priority,
             status, due_date, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, 'pending', ?, ?, ?)
        """, (project_id, title.strip(), description, assigned_to,
              priority, due_date, created_by, datetime.now().isoformat()))
        conn.commit()
        tid = cur.lastrowid
    finally:
        conn.close()

    if assigned_to:
        try:
            from electrocalc.core import notifications as notif
            notif.create_notification(
                username=assigned_to,
                title="✅ تسک جدید برای شما",
                message=f"تسک «{title}» به شما اختصاص داده شد",
                category="info",
            )
        except Exception:
            pass

    return tid


def list_tasks(project_id=None, assigned_to=None, status=None):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT t.*, p.name AS project_name
        FROM tasks t
        LEFT JOIN projects p ON p.id = t.project_id
        WHERE 1=1
    """
    params = []
    if project_id:
        query += " AND t.project_id = ?"
        params.append(project_id)
    if assigned_to:
        query += " AND t.assigned_to = ?"
        params.append(assigned_to)
    if status:
        query += " AND t.status = ?"
        params.append(status)
    query += """
        ORDER BY
            CASE t.priority
                WHEN 'urgent' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'low' THEN 4
                ELSE 5
            END,
            t.id DESC
    """
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def get_task(tid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT t.*, p.name AS project_name
        FROM tasks t
        LEFT JOIN projects p ON p.id = t.project_id
        WHERE t.id = ?
    """, (tid,))
    row = cur.fetchone()
    conn.close()
    return row


def update_task(tid, title, description="", assigned_to="",
                priority="medium", status="pending", due_date=""):
    if not title.strip():
        raise ValueError("عنوان تسک الزامی است.")
    conn = get_connection()
    cur = conn.cursor()
    try:
        completed = None
        if status == "done":
            completed = datetime.now().isoformat()
        cur.execute("""
            UPDATE tasks
            SET title = ?, description = ?, assigned_to = ?,
                priority = ?, status = ?, due_date = ?, completed_at = ?
            WHERE id = ?
        """, (title.strip(), description, assigned_to, priority,
              status, due_date, completed, tid))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def toggle_task(tid):
    t = get_task(tid)
    if not t:
        return False
    new_status = "pending" if t["status"] == "done" else "done"
    conn = get_connection()
    cur = conn.cursor()
    completed = datetime.now().isoformat() if new_status == "done" else None
    cur.execute("""
        UPDATE tasks SET status = ?, completed_at = ? WHERE id = ?
    """, (new_status, completed, tid))
    conn.commit()
    conn.close()
    return True


def delete_task(tid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (tid,))
    conn.commit()
    conn.close()


def project_progress(project_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM tasks WHERE project_id = ?",
                (project_id,))
    total = cur.fetchone()["c"]
    if total == 0:
        conn.close()
        return {"total": 0, "done": 0, "percent": 0}

    cur.execute("""
        SELECT COUNT(*) AS c FROM tasks
        WHERE project_id = ? AND status = 'done'
    """, (project_id,))
    done = cur.fetchone()["c"]
    conn.close()
    return {"total": total, "done": done,
            "percent": int((done / total) * 100)}


def get_active_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT username, full_name FROM users
        WHERE active = 1 ORDER BY username
    """)
    rows = cur.fetchall()
    conn.close()
    return list(rows)