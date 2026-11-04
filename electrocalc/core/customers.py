"""منطق مدیریت مشتریان."""

from datetime import datetime
from electrocalc.data.database import get_connection


def create_customer(name, company="", phone="", mobile="", email="",
                     address="", city="", national_id="",
                     economic_code="", notes="", created_by=""):
    if not name.strip():
        raise ValueError("نام مشتری الزامی است.")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO customers
            (name, company, phone, mobile, email, address, city,
             national_id, economic_code, notes, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name.strip(), company, phone, mobile, email, address,
              city, national_id, economic_code, notes, created_by,
              datetime.now().isoformat()))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_customers(search=""):
    conn = get_connection()
    cur = conn.cursor()
    if search:
        cur.execute("""
            SELECT * FROM customers
            WHERE name LIKE ? OR company LIKE ? OR phone LIKE ?
               OR mobile LIKE ? OR city LIKE ?
            ORDER BY name
        """, (f"%{search}%",) * 5)
    else:
        cur.execute("SELECT * FROM customers ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def get_customer(cid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM customers WHERE id = ?", (cid,))
    row = cur.fetchone()
    conn.close()
    return row


def update_customer(cid, name, company="", phone="", mobile="", email="",
                     address="", city="", national_id="",
                     economic_code="", notes=""):
    if not name.strip():
        raise ValueError("نام مشتری الزامی است.")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE customers
            SET name = ?, company = ?, phone = ?, mobile = ?, email = ?,
                address = ?, city = ?, national_id = ?, economic_code = ?,
                notes = ?
            WHERE id = ?
        """, (name.strip(), company, phone, mobile, email, address,
              city, national_id, economic_code, notes, cid))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def delete_customer(cid):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM customers WHERE id = ?", (cid,))
    conn.commit()
    conn.close()


def get_customer_projects(customer_name):
    """پروژه‌های یه مشتری رو برمی‌گردونه."""
    if not customer_name:
        return []
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM projects
        WHERE customer = ?
        ORDER BY id DESC
    """, (customer_name,))
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def customer_stats(customer_name):
    """آمار یه مشتری."""
    if not customer_name:
        return {"projects": 0, "total_expenses": 0}
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT COUNT(*) AS c FROM projects WHERE customer = ?
    """, (customer_name,))
    projects_count = cur.fetchone()["c"]

    cur.execute("""
        SELECT COALESCE(SUM(amount),0) AS s FROM expenses
        WHERE project_id IN (SELECT id FROM projects WHERE customer = ?)
    """, (customer_name,))
    total_expenses = cur.fetchone()["s"]

    conn.close()
    return {
        "projects": projects_count,
        "total_expenses": total_expenses,
    }


def customers_for_combo():
    """لیست مشتری‌ها برای dropdown."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, company FROM customers ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return list(rows)