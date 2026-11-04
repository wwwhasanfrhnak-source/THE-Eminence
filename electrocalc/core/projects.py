"""منطق مدیریت پروژه‌ها + اعضای پروژه."""

from datetime import datetime
from electrocalc.data.database import get_connection


STATUS_FA = {
    "planning": "در برنامه‌ریزی",
    "in_progress": "در حال انجام",
    "paused": "متوقف",
    "done": "تمام شده",
    "cancelled": "لغو شده",
}


# ==================== پروژه‌ها ====================
def create_project(name, customer="", address="", description="",
                   status="in_progress", start_date="", end_date="",
                   created_by=""):
    if not name.strip():
        raise ValueError("نام پروژه الزامی است.")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO projects
            (name, customer, address, description, status,
             start_date, end_date, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name.strip(), customer, address, description, status,
              start_date, end_date, created_by, datetime.now().isoformat()))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_projects(search=""):
    """همه پروژه‌ها (برای admin)."""
    conn = get_connection()
    cur = conn.cursor()
    if search:
        cur.execute("""
            SELECT * FROM projects
            WHERE name LIKE ? OR customer LIKE ?
            ORDER BY id DESC
        """, (f"%{search}%", f"%{search}%"))
    else:
        cur.execute("SELECT * FROM projects ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def list_projects_for_user(username, search=""):
    """پروژه‌هایی که کاربر ساخته یا عضوشه."""
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT DISTINCT p.* FROM projects p
        LEFT JOIN project_members m ON m.project_id = p.id
        WHERE (p.created_by = ? OR m.username = ?)
    """
    params = [username, username]
    if search:
        query += " AND (p.name LIKE ? OR p.customer LIKE ?)"
        params += [f"%{search}%", f"%{search}%"]
    query += " ORDER BY p.id DESC"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def get_project(pid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM projects WHERE id = ?", (pid,))
    row = cur.fetchone()
    conn.close()
    return row


def update_project(pid, name, customer="", address="", description="",
                   status="in_progress", start_date="", end_date=""):
    if not name.strip():
        raise ValueError("نام پروژه الزامی است.")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE projects
            SET name = ?, customer = ?, address = ?, description = ?,
                status = ?, start_date = ?, end_date = ?
            WHERE id = ?
        """, (name.strip(), customer, address, description, status,
              start_date, end_date, pid))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_project(pid):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM project_members WHERE project_id = ?", (pid,))
        cur.execute("DELETE FROM projects WHERE id = ?", (pid,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ==================== اعضای پروژه ====================
def get_members(project_id):
    """لیست usernames اعضای یه پروژه."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT username FROM project_members
        WHERE project_id = ?
        ORDER BY username
    """, (project_id,))
    rows = cur.fetchall()
    conn.close()
    return [r["username"] for r in rows]


def set_members(project_id, usernames):
    """جایگزین کل اعضا."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM project_members WHERE project_id = ?",
                    (project_id,))
        for u in usernames:
            cur.execute("""
                INSERT INTO project_members (project_id, username, added_at)
                VALUES (?, ?, ?)
            """, (project_id, u, datetime.now().isoformat()))
        conn.commit()
    finally:
        conn.close()


def add_member(project_id, username):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT OR IGNORE INTO project_members
            (project_id, username, added_at) VALUES (?, ?, ?)
        """, (project_id, username, datetime.now().isoformat()))
        conn.commit()
    finally:
        conn.close()


def remove_member(project_id, username):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM project_members
            WHERE project_id = ? AND username = ?
        """, (project_id, username))
        conn.commit()
    finally:
        conn.close()


def count_members(project_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS c FROM project_members WHERE project_id = ?",
                (project_id,))
    row = cur.fetchone()
    conn.close()
    return row["c"] if row else 0


def get_active_users():
    """لیست کاربران فعال برای انتخاب اعضا."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT username, full_name, role FROM users
        WHERE active = 1
        ORDER BY username
    """)
    rows = cur.fetchall()
    conn.close()
    return list(rows)