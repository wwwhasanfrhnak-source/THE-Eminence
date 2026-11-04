"""تایمر خودکار ورود/خروج + تغییر پروژه."""

from datetime import datetime

from electrocalc.data.database import get_connection


def _save_session_as_timesheet(cur, session_row, end_dt):
    """ثبت جلسه در timesheets. اگر معتبر نبود، None برمی‌گردونه."""
    try:
        login = datetime.fromisoformat(session_row["login_at"])
    except Exception:
        return None

    delta_seconds = (end_dt - login).total_seconds()
    if delta_seconds < 60:
        return None

    hours = delta_seconds / 3600.0
    cur.execute("""
        INSERT INTO timesheets
        (username, project_id, work_date, start_time, end_time,
         hours, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        session_row["username"],
        session_row["project_id"],
        login.strftime("%Y-%m-%d"),
        login.strftime("%H:%M"),
        end_dt.strftime("%H:%M"),
        round(hours, 2),
        "ورود و خروج خودکار",
        end_dt.isoformat(),
    ))
    return cur.lastrowid


def start_session(username, project_id=None):
    """شروع جلسه جدید. جلسات معلق قبلی رو خودکار می‌بنده."""
    conn = get_connection()
    cur = conn.cursor()

    # بازیابی جلسات معلق (کرش قبلی)
    cur.execute("""
        SELECT * FROM active_sessions
        WHERE username = ? AND is_active = 1
        ORDER BY id DESC
    """, (username,))
    old_rows = cur.fetchall()
    for r in old_rows:
        _save_session_as_timesheet(cur, r, datetime.now())

    # بستن همه
    cur.execute("""
        UPDATE active_sessions SET is_active = 0
        WHERE username = ? AND is_active = 1
    """, (username,))

    now = datetime.now().isoformat()
    cur.execute("""
        INSERT INTO active_sessions
        (username, project_id, login_at, last_ping, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (username, project_id, now, now))
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return sid


def ping(session_id):
    """آپدیت زمان آخرین فعالیت."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE active_sessions SET last_ping = ? WHERE id = ?",
        (datetime.now().isoformat(), session_id))
    conn.commit()
    conn.close()


def end_session(session_id):
    """بستن جلسه و ذخیره در timesheets."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM active_sessions WHERE id = ?", (session_id,))
    row = cur.fetchone()
    if not row or not row["is_active"]:
        conn.close()
        return None

    ts_id = _save_session_as_timesheet(cur, row, datetime.now())
    cur.execute(
        "UPDATE active_sessions SET is_active = 0 WHERE id = ?",
        (session_id,))
    conn.commit()
    conn.close()
    return ts_id


def change_project(session_id, new_project_id):
    """پایان جلسه فعلی + شروع جلسه جدید با پروژه جدید."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM active_sessions WHERE id = ?", (session_id,))
    row = cur.fetchone()
    if not row or not row["is_active"]:
        conn.close()
        return None

    now = datetime.now()
    _save_session_as_timesheet(cur, row, now)
    cur.execute(
        "UPDATE active_sessions SET is_active = 0 WHERE id = ?",
        (session_id,))

    # جلسه جدید
    cur.execute("""
        INSERT INTO active_sessions
        (username, project_id, login_at, last_ping, is_active)
        VALUES (?, ?, ?, ?, 1)
    """, (row["username"], new_project_id, now.isoformat(), now.isoformat()))
    new_sid = cur.lastrowid
    conn.commit()
    conn.close()
    return new_sid


def get_active_session(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM active_sessions
        WHERE username = ? AND is_active = 1
        ORDER BY id DESC LIMIT 1
    """, (username,))
    row = cur.fetchone()
    conn.close()
    return row


def get_project_name(project_id):
    """اسم پروژه رو از ID بگیر."""
    if not project_id:
        return None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM projects WHERE id = ?", (project_id,))
    row = cur.fetchone()
    conn.close()
    return row["name"] if row else None