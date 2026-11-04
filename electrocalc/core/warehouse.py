"""منطق مدیریت انبار."""

from datetime import datetime
from electrocalc.data.database import get_connection


CATEGORIES = [
    "کابل و سیم",
    "کلید و پریز",
    "فیوز و کلید مینیاتوری",
    "تابلو برق",
    "موتور و تجهیزات",
    "روشنایی",
    "ابزار",
    "اتصالات",
    "سایر",
]


# ========================================================
# کالاها
# ========================================================
def create_item(name, category="", unit="عدد", quantity=0,
                min_quantity=0, purchase_price=0, sale_price=0,
                supplier="", location="", description=""):
    if not name.strip():
        raise ValueError("نام کالا الزامی است.")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO warehouse
            (name, category, unit, quantity, min_quantity,
             purchase_price, sale_price, supplier, location,
             description, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (name.strip(), category, unit, quantity, min_quantity,
              purchase_price, sale_price, supplier, location,
              description, datetime.now().isoformat()))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def update_item(item_id, name, category="", unit="عدد", quantity=0,
                min_quantity=0, purchase_price=0, sale_price=0,
                supplier="", location="", description=""):
    if not name.strip():
        raise ValueError("نام کالا الزامی است.")

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE warehouse
            SET name = ?, category = ?, unit = ?, quantity = ?,
                min_quantity = ?, purchase_price = ?, sale_price = ?,
                supplier = ?, location = ?, description = ?,
                updated_at = ?
            WHERE id = ?
        """, (name.strip(), category, unit, quantity, min_quantity,
              purchase_price, sale_price, supplier, location,
              description, datetime.now().isoformat(), item_id))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def list_items(search="", category=None, low_stock_only=False):
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT * FROM warehouse WHERE 1=1"
    params = []

    if search:
        query += " AND (name LIKE ? OR code LIKE ? OR supplier LIKE ?)"
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]

    if category:
        query += " AND category = ?"
        params.append(category)

    if low_stock_only:
        query += " AND quantity <= min_quantity AND min_quantity > 0"

    query += " ORDER BY name"
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def get_item(item_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM warehouse WHERE id = ?", (item_id,))
    row = cur.fetchone()
    conn.close()
    return row


def delete_item(item_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM warehouse_transactions WHERE warehouse_id = ?",
                    (item_id,))
        cur.execute("DELETE FROM warehouse WHERE id = ?", (item_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


# ========================================================
# ورود/خروج کالا
# ========================================================
def add_transaction(item_id, trans_type, quantity, unit_price=0,
                    project_id=None, supplier="", note="", created_by=""):
    """
    trans_type: in (ورود) | out (خروج)
    """
    if trans_type not in ("in", "out"):
        raise ValueError("نوع تراکنش باید in یا out باشد.")
    if quantity <= 0:
        raise ValueError("تعداد باید بزرگ‌تر از صفر باشد.")

    conn = get_connection()
    cur = conn.cursor()
    try:
        # ذخیره تراکنش
        cur.execute("""
            INSERT INTO warehouse_transactions
            (warehouse_id, type, quantity, unit_price, total_price,
             project_id, supplier, note, created_by,
             trans_date, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (item_id, trans_type, quantity, unit_price,
              quantity * unit_price, project_id, supplier, note,
              created_by,
              datetime.now().strftime("%Y-%m-%d"),
              datetime.now().isoformat()))

        # به‌روزرسانی موجودی
        if trans_type == "in":
            cur.execute("""
                UPDATE warehouse
                SET quantity = quantity + ?, updated_at = ?
                WHERE id = ?
            """, (quantity, datetime.now().isoformat(), item_id))
        else:
            cur.execute("""
                UPDATE warehouse
                SET quantity = quantity - ?, updated_at = ?
                WHERE id = ?
            """, (quantity, datetime.now().isoformat(), item_id))

        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def list_transactions(item_id=None, trans_type=None, limit=500):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT t.*, w.name AS item_name, w.unit AS item_unit,
               p.name AS project_name
        FROM warehouse_transactions t
        LEFT JOIN warehouse w ON w.id = t.warehouse_id
        LEFT JOIN projects p ON p.id = t.project_id
        WHERE 1=1
    """
    params = []
    if item_id:
        query += " AND t.warehouse_id = ?"
        params.append(item_id)
    if trans_type:
        query += " AND t.type = ?"
        params.append(trans_type)
    query += " ORDER BY t.id DESC LIMIT ?"
    params.append(limit)

    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return list(rows)


def delete_transaction(trans_id):
    """حذف تراکنش + برگشت موجودی."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM warehouse_transactions WHERE id = ?",
                    (trans_id,))
        row = cur.fetchone()
        if not row:
            return False

        # برگشت موجودی
        if row["type"] == "in":
            cur.execute("""
                UPDATE warehouse SET quantity = quantity - ?
                WHERE id = ?
            """, (row["quantity"], row["warehouse_id"]))
        else:
            cur.execute("""
                UPDATE warehouse SET quantity = quantity + ?
                WHERE id = ?
            """, (row["quantity"], row["warehouse_id"]))

        cur.execute("DELETE FROM warehouse_transactions WHERE id = ?",
                    (trans_id,))
        conn.commit()
        return True
    finally:
        conn.close()


# ========================================================
# آمار
# ========================================================
def get_stats():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS c FROM warehouse")
    total_items = cur.fetchone()["c"]

    cur.execute("""
        SELECT COALESCE(SUM(quantity * purchase_price), 0) AS s
        FROM warehouse
    """)
    total_value = cur.fetchone()["s"]

    cur.execute("""
        SELECT COUNT(*) AS c FROM warehouse
        WHERE quantity <= min_quantity AND min_quantity > 0
    """)
    low_stock = cur.fetchone()["c"]

    cur.execute("""
        SELECT COUNT(*) AS c FROM warehouse WHERE quantity <= 0
    """)
    out_of_stock = cur.fetchone()["c"]

    conn.close()
    return {
        "total_items": total_items,
        "total_value": total_value,
        "low_stock": low_stock,
        "out_of_stock": out_of_stock,
    }


def notify_low_stock():
    """اعلان به مدیرها برای کالاهای کم."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT name, quantity, min_quantity, unit
            FROM warehouse
            WHERE quantity <= min_quantity AND min_quantity > 0
        """)
        rows = cur.fetchall()
        conn.close()

        if not rows:
            return

        from electrocalc.core import notifications as notif
        for r in rows:
            notif.notify_admins(
                title=f"⚠️ کمبود در انبار: {r['name']}",
                message=f"موجودی: {r['quantity']} {r['unit']} — "
                        f"حداقل: {r['min_quantity']} {r['unit']}",
                category="warning",
            )
    except Exception:
        pass