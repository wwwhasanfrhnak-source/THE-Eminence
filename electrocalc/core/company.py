"""اطلاعات شرکت."""

import shutil
from datetime import datetime
from pathlib import Path

from electrocalc.data.database import get_connection

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets"
ASSETS_DIR.mkdir(exist_ok=True)


def get_company():
    """اطلاعات شرکت رو برمی‌گردونه. اگه نبود، یه رکورد خالی می‌سازه."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM company WHERE id = 1")
    row = cur.fetchone()
    if not row:
        cur.execute("""
            INSERT INTO company (id, name, updated_at)
            VALUES (1, 'شرکت من', ?)
        """, (datetime.now().isoformat(),))
        conn.commit()
        cur.execute("SELECT * FROM company WHERE id = 1")
        row = cur.fetchone()
    conn.close()
    return row


def save_company(name="", address="", phone="", email="",
                 website="", registration="", tax_id="",
                 economic_code=""):
    """ذخیره اطلاعات شرکت."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE company
            SET name = ?, address = ?, phone = ?, email = ?,
                website = ?, registration = ?, tax_id = ?,
                economic_code = ?, updated_at = ?
            WHERE id = 1
        """, (name, address, phone, email, website, registration,
              tax_id, economic_code, datetime.now().isoformat()))
        conn.commit()
        return cur.rowcount > 0
    finally:
        conn.close()


def set_logo(source_path):
    """کپی لوگو به پوشه assets و ذخیره مسیرش."""
    src = Path(source_path)
    if not src.exists():
        raise ValueError("فایل لوگو پیدا نشد.")
    ext = src.suffix.lower()
    dest = ASSETS_DIR / f"company_logo{ext}"
    shutil.copy(source_path, dest)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE company SET logo_path = ?, updated_at = ? WHERE id = 1",
                (str(dest), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return str(dest)


def remove_logo():
    """حذف لوگو."""
    c = get_company()
    if c and c["logo_path"]:
        try:
            Path(c["logo_path"]).unlink(missing_ok=True)
        except Exception:
            pass
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE company SET logo_path = '' WHERE id = 1")
    conn.commit()
    conn.close()