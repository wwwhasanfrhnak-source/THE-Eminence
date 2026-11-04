"""منطق مدیریت: ساعات کار، مصالح، هزینه‌ها، فایل‌ها، پیام‌ها، تأییدها.
همراه با اعلان خودکار.
"""

import shutil
from datetime import datetime
from pathlib import Path

from electrocalc.data.database import get_connection

# پوشه آپلود
UPLOADS_DIR = Path(__file__).resolve().parents[2] / "uploads"
UPLOADS_DIR.mkdir(exist_ok=True)


# ==================== ساعات کار ====================
def create_timesheet(username, project_id, work_date, start_time, end_time,
                     hours, description=""):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO timesheets
            (username, project_id, work_date, start_time, end_time,
             hours, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (username, project_id, work_date, start_time, end_time,
              hours, description, datetime.now().isoformat()))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_timesheets(username=None, status=None):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT t.*, p.name AS project_name
        FROM timesheets t
        LEFT JOIN projects p ON p.id = t.project_id
        WHERE 1=1
    """
    params = []
    if username:
        query += " AND t.username = ?"
        params.append(username)
    if status:
        query += " AND t.status = ?"
        params.append(status)
    query += " ORDER BY t.id DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def delete_timesheet(tid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM timesheets WHERE id = ?", (tid,))
    conn.commit()
    conn.close()


# ==================== مصالح ====================
def create_material(project_id, name, quantity, unit, unit_price,
                    description="", created_by="", material_date=""):
    total = quantity * unit_price
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO materials
            (project_id, name, quantity, unit, unit_price, total_price,
             description, created_by, material_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (project_id, name, quantity, unit, unit_price, total,
              description, created_by, material_date,
              datetime.now().isoformat()))
        conn.commit()
        mid = cur.lastrowid
    finally:
        conn.close()

    # ✅ اعلان به مدیرها
    try:
        from electrocalc.core import notifications as notif
        notif.notify_admins(
            title="🔧 مصالح جدید ثبت شد",
            message=f"{created_by} مصالح «{name}» را ثبت کرد",
            category="info",
        )
    except Exception:
        pass

    return mid


def list_materials(created_by=None, status=None):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT m.*, p.name AS project_name
        FROM materials m
        LEFT JOIN projects p ON p.id = m.project_id
        WHERE 1=1
    """
    params = []
    if created_by:
        query += " AND m.created_by = ?"
        params.append(created_by)
    if status:
        query += " AND m.status = ?"
        params.append(status)
    query += " ORDER BY m.id DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def delete_material(mid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM materials WHERE id = ?", (mid,))
    conn.commit()
    conn.close()


# ==================== هزینه‌ها ====================
def create_expense(project_id, title, amount, category="",
                   description="", created_by="", expense_date=""):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO expenses
            (project_id, title, amount, category, description,
             created_by, expense_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (project_id, title, amount, category, description,
              created_by, expense_date, datetime.now().isoformat()))
        conn.commit()
        eid = cur.lastrowid
    finally:
        conn.close()

    # ✅ اعلان به مدیرها
    try:
        from electrocalc.core import notifications as notif
        notif.notify_admins(
            title="💰 هزینه جدید ثبت شد",
            message=f"{created_by} هزینه «{title}» را ثبت کرد",
            category="expense",
        )
    except Exception:
        pass

    return eid


def list_expenses(created_by=None, status=None):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT e.*, p.name AS project_name
        FROM expenses e
        LEFT JOIN projects p ON p.id = e.project_id
        WHERE 1=1
    """
    params = []
    if created_by:
        query += " AND e.created_by = ?"
        params.append(created_by)
    if status:
        query += " AND e.status = ?"
        params.append(status)
    query += " ORDER BY e.id DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def delete_expense(eid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id = ?", (eid,))
    conn.commit()
    conn.close()


# ==================== فایل‌ها ====================
def create_file(project_id, title, source_path, uploaded_by="", description=""):
    source = Path(source_path)
    if not source.exists():
        raise ValueError("فایل پیدا نشد.")
    ext = source.suffix
    dest_name = f"f_{datetime.now().strftime('%Y%m%d%H%M%S')}_{source.name}"
    dest = UPLOADS_DIR / dest_name
    shutil.copy(source, dest)

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO files
            (project_id, title, filepath, uploaded_by, description, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, title, str(dest), uploaded_by, description,
              datetime.now().isoformat()))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_files(uploaded_by=None):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT f.*, p.name AS project_name
        FROM files f
        LEFT JOIN projects p ON p.id = f.project_id
        WHERE 1=1
    """
    params = []
    if uploaded_by:
        query += " AND f.uploaded_by = ?"
        params.append(uploaded_by)
    query += " ORDER BY f.id DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def delete_file(fid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT filepath FROM files WHERE id = ?", (fid,))
    row = cur.fetchone()
    if row:
        try:
            Path(row["filepath"]).unlink(missing_ok=True)
        except Exception:
            pass
    cur.execute("DELETE FROM files WHERE id = ?", (fid,))
    conn.commit()
    conn.close()


# ==================== پیام‌ها ====================
def create_message(sender, receiver, subject, body):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO messages
            (sender, receiver, subject, body, sent_at)
            VALUES (?, ?, ?, ?, ?)
        """, (sender, receiver, subject, body,
              datetime.now().isoformat()))
        conn.commit()
        mid = cur.lastrowid
    finally:
        conn.close()

    # ✅ اعلان به گیرنده
    try:
        from electrocalc.core import notifications as notif
        notif.create_notification(
            username=receiver,
            title="💬 پیام جدید",
            message=f"از {sender}: {subject or '(بدون موضوع)'}",
            category="message",
        )
    except Exception:
        pass

    return mid


def list_messages(username, box="inbox"):
    conn = get_connection()
    cur = conn.cursor()
    if box == "inbox":
        cur.execute("""
            SELECT * FROM messages
            WHERE receiver = ?
            ORDER BY id DESC
        """, (username,))
    else:
        cur.execute("""
            SELECT * FROM messages
            WHERE sender = ?
            ORDER BY id DESC
        """, (username,))
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def mark_message_read(mid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE messages SET is_read = 1 WHERE id = ?", (mid,))
    conn.commit()
    conn.close()


def count_unread(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COUNT(*) AS c FROM messages
        WHERE receiver = ? AND is_read = 0
    """, (username,))
    row = cur.fetchone()
    conn.close()
    return row["c"] if row else 0


# ==================== تأییدها ====================
def list_pending_for_approval():
    conn = get_connection()
    cur = conn.cursor()
    items = []

    cur.execute("""
        SELECT r.id, r.title, r.report_date AS date, r.author AS who,
               p.name AS project
        FROM reports r
        LEFT JOIN projects p ON p.id = r.project_id
        WHERE r.status = 'pending'
        ORDER BY r.id DESC
    """)
    for row in cur.fetchall():
        items.append({
            "table": "reports", "id": row["id"],
            "type": "گزارش", "title": row["title"],
            "who": row["who"], "date": row["date"],
            "project": row["project"] or "-",
        })

    cur.execute("""
        SELECT e.id, e.title, e.expense_date AS date, e.created_by AS who,
               p.name AS project
        FROM expenses e
        LEFT JOIN projects p ON p.id = e.project_id
        WHERE e.status = 'pending'
        ORDER BY e.id DESC
    """)
    for row in cur.fetchall():
        items.append({
            "table": "expenses", "id": row["id"],
            "type": "هزینه", "title": row["title"],
            "who": row["who"], "date": row["date"],
            "project": row["project"] or "-",
        })

    cur.execute("""
        SELECT m.id, m.name AS title, m.material_date AS date,
               m.created_by AS who, p.name AS project
        FROM materials m
        LEFT JOIN projects p ON p.id = m.project_id
        WHERE m.status = 'pending'
        ORDER BY m.id DESC
    """)
    for row in cur.fetchall():
        items.append({
            "table": "materials", "id": row["id"],
            "type": "مصالح", "title": row["title"],
            "who": row["who"], "date": row["date"],
            "project": row["project"] or "-",
        })

    cur.execute("""
        SELECT t.id, t.work_date AS date, t.username AS who,
               p.name AS project, t.hours
        FROM timesheets t
        LEFT JOIN projects p ON p.id = t.project_id
        WHERE t.status = 'pending'
        ORDER BY t.id DESC
    """)
    for row in cur.fetchall():
        items.append({
            "table": "timesheets", "id": row["id"],
            "type": "ساعت کار",
            "title": f"{row['hours']:.1f} ساعت",
            "who": row["who"], "date": row["date"],
            "project": row["project"] or "-",
        })

    conn.close()
    return items


def approve_item(table, item_id, approved_by):
    if table not in ("reports", "expenses", "materials", "timesheets"):
        raise ValueError("نوع نامعتبر")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE {table} SET status = 'approved', approved_by = ? WHERE id = ?",
        (approved_by, item_id))
    conn.commit()
    conn.close()

    # ✅ اعلان به صاحب رکورد
    try:
        _notify_owner(table, item_id, approved_by, approved=True)
    except Exception:
        pass


def reject_item(table, item_id, approved_by):
    if table not in ("reports", "expenses", "materials", "timesheets"):
        raise ValueError("نوع نامعتبر")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        f"UPDATE {table} SET status = 'rejected', approved_by = ? WHERE id = ?",
        (approved_by, item_id))
    conn.commit()
    conn.close()

    # ✅ اعلان به صاحب رکورد
    try:
        _notify_owner(table, item_id, approved_by, approved=False)
    except Exception:
        pass


# ==================== کمکی ====================
def _notify_owner(table, item_id, approved_by, approved):
    """اعلان به صاحب رکورد بعد از تأیید/رد."""
    from electrocalc.core import notifications as notif

    conn = get_connection()
    cur = conn.cursor()
    info = None

    if table == "reports":
        cur.execute("SELECT title AS name, author AS who FROM reports WHERE id = ?",
                    (item_id,))
        row = cur.fetchone()
        if row:
            info = ("گزارش", row["name"], row["who"])

    elif table == "expenses":
        cur.execute("SELECT title AS name, created_by AS who FROM expenses WHERE id = ?",
                    (item_id,))
        row = cur.fetchone()
        if row:
            info = ("هزینه", row["name"], row["who"])

    elif table == "materials":
        cur.execute("SELECT name, created_by AS who FROM materials WHERE id = ?",
                    (item_id,))
        row = cur.fetchone()
        if row:
            info = ("مصالح", row["name"], row["who"])

    elif table == "timesheets":
        cur.execute("SELECT username AS who, hours FROM timesheets WHERE id = ?",
                    (item_id,))
        row = cur.fetchone()
        if row:
            info = ("ساعت کار", f"{row['hours']:.1f} ساعت", row["who"])

    conn.close()

    if not info:
        return

    kind, name, who = info
    if not who:
        return

    if approved:
        title = f"✅ {kind} شما تأیید شد"
        msg = f"{kind} «{name}» توسط {approved_by} تأیید شد"
        cat = "approval"
    else:
        title = f"❌ {kind} شما رد شد"
        msg = f"{kind} «{name}» توسط {approved_by} رد شد"
        cat = "danger"

    notif.create_notification(
        username=who,
        title=title,
        message=msg,
        category=cat,
    )