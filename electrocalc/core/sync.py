"""منطق همگام‌سازی — ارسال داده به دفتر + دریافت از مهندسین."""

import json
import shutil
from datetime import datetime
from pathlib import Path

from electrocalc.data.database import get_connection


# ========================================================
# مسیر Share
# ========================================================
def get_share_path():
    """مسیر پوشه Share از تنظیمات."""
    try:
        from electrocalc.core import settings as st
        p = st.get_setting("sync_share_path", "")
        if p:
            return Path(p)
    except Exception:
        pass
    return None


def set_share_path(path):
    """ذخیره مسیر Share."""
    try:
        from electrocalc.core import settings as st
        st.set_setting("sync_share_path", str(path))
        return True
    except Exception as e:
        print(f"خطا در ذخیره مسیر: {e}")
        return False


def ensure_share_dirs():
    """ساخت پوشه‌های لازم تو Share."""
    share = get_share_path()
    if not share:
        return False, "مسیر Share تنظیم نشده"

    try:
        (share / "sync").mkdir(parents=True, exist_ok=True)
        (share / "updates").mkdir(parents=True, exist_ok=True)
        (share / "sync" / "archive").mkdir(parents=True, exist_ok=True)
        return True, "OK"
    except Exception as e:
        return False, f"خطا در ساخت پوشه: {e}"


def test_connection():
    """تست اتصال به پوشه Share."""
    share = get_share_path()
    if not share:
        return False, "مسیر Share تنظیم نشده"

    if not share.exists():
        return False, f"پوشه پیدا نشد: {share}"

    try:
        test_file = share / ".test_write"
        test_file.write_text("test", encoding="utf-8")
        test_file.unlink()
    except Exception as e:
        return False, f"دسترسی نوشتن نیست: {e}"

    return True, "اتصال موفق"


# ========================================================
# آخرین sync
# ========================================================
def get_last_sync(username):
    """آخرین تاریخ sync این کاربر."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT sync_date FROM sync_log
            WHERE username = ? AND sync_type = 'upload'
            ORDER BY id DESC LIMIT 1
        """, (username,))
        row = cur.fetchone()
        return row["sync_date"] if row else None
    finally:
        conn.close()


def log_sync(username, sync_type, count=0, notes=""):
    """ثبت sync تو دیتابیس."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO sync_log
                (username, sync_date, sync_type, records_count, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (username, datetime.now().isoformat(),
              sync_type, count, notes))
        conn.commit()
    finally:
        conn.close()


# ========================================================
# Export — مهندس داده‌هاش رو می‌فرسته
# ========================================================
def export_my_data(username):
    """خروجی گرفتن از داده‌های جدید کاربر → فایل JSON."""
    ok, msg = test_connection()
    if not ok:
        return False, msg, 0

    ok, msg = ensure_share_dirs()
    if not ok:
        return False, msg, 0

    last_sync = get_last_sync(username)
    if not last_sync:
        last_sync = "1970-01-01T00:00:00"

    conn = get_connection()
    cur = conn.cursor()

    try:
        data = {
            "sync_id": f"{username}-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "username": username,
            "date": datetime.now().isoformat(),
            "last_sync": last_sync,
            "reports": [],
            "timesheets": [],
            "expenses": [],
            "material_requests": [],
        }

        # گزارش‌ها
        cur.execute("""
            SELECT * FROM reports
            WHERE author = ? AND created_at > ?
        """, (username, last_sync))
        data["reports"] = [dict(r) for r in cur.fetchall()]

        # ساعات کار
        cur.execute("""
            SELECT * FROM timesheets
            WHERE username = ? AND created_at > ?
        """, (username, last_sync))
        data["timesheets"] = [dict(r) for r in cur.fetchall()]

        # هزینه‌ها
        cur.execute("""
            SELECT * FROM expenses
            WHERE created_by = ? AND created_at > ?
        """, (username, last_sync))
        data["expenses"] = [dict(r) for r in cur.fetchall()]

        # درخواست مصالح
        cur.execute("""
            SELECT * FROM material_requests
            WHERE requester = ? AND created_at > ?
        """, (username, last_sync))
        data["material_requests"] = [dict(r) for r in cur.fetchall()]

        total = (len(data["reports"]) + len(data["timesheets"])
                 + len(data["expenses"])
                 + len(data["material_requests"]))

        if total == 0:
            return True, "داده جدیدی برای ارسال نیست", 0

        share = get_share_path()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{username}_{timestamp}.json"
        filepath = share / "sync" / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        log_sync(username, "upload", total, f"file={filename}")

        return True, f"{total} رکورد ارسال شد", total

    except Exception as e:
        import traceback
        traceback.print_exc()
        return False, f"خطا: {e}", 0
    finally:
        conn.close()


# ========================================================
# Import — مدیر داده‌ها رو می‌گیره
# ========================================================
def import_all_from_engineers():
    """مدیر: همه فایل‌های sync رو می‌خونه و ادغام می‌کنه."""
    ok, msg = test_connection()
    if not ok:
        return False, msg, 0

    share = get_share_path()
    sync_dir = share / "sync"

    if not sync_dir.exists():
        return False, "پوشه sync وجود نداره", 0

    files = list(sync_dir.glob("*.json"))
    if not files:
        return True, "فایل جدیدی نیست", 0

    total_imported = 0
    total_files = 0
    errors = []

    for f in files:
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)

            count = _import_one(data)
            total_imported += count
            total_files += 1

            archive_dir = sync_dir / "archive"
            archive_dir.mkdir(exist_ok=True)
            dest = archive_dir / f.name
            shutil.move(str(f), str(dest))

        except Exception as e:
            errors.append(f"{f.name}: {e}")

    if errors:
        msg = f"{total_files} فایل، {total_imported} رکورد. خطا: {errors[:2]}"
        return False, msg, total_imported

    return True, f"{total_files} فایل، {total_imported} رکورد ادغام شد", total_imported


def _import_one(data):
    """ادغام داده‌های یه فایل تو دیتابیس مدیر."""
    conn = get_connection()
    cur = conn.cursor()
    count = 0

    try:
        # ---- reports ----
        for r in data.get("reports", []):
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO reports
                        (id, project_id, author, report_date, title,
                         description, hours, status, approved_by,
                         approved_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (r.get("id"), r.get("project_id"), r.get("author"),
                      r.get("report_date"), r.get("title"),
                      r.get("description"), r.get("hours", 0),
                      r.get("status", "pending"), r.get("approved_by"),
                      r.get("approved_at"), r.get("created_at")))
                count += 1
            except Exception as e:
                print(f"خطا report: {e}")

        # ---- timesheets ----
        for t in data.get("timesheets", []):
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO timesheets
                        (id, username, project_id, work_date,
                         start_time, end_time, hours, description,
                         status, approved_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (t.get("id"), t.get("username"), t.get("project_id"),
                      t.get("work_date"), t.get("start_time"),
                      t.get("end_time"), t.get("hours", 0),
                      t.get("description"), t.get("status", "pending"),
                      t.get("approved_by"), t.get("created_at")))
                count += 1
            except Exception as e:
                print(f"خطا timesheet: {e}")

        # ---- expenses ----
        for ex in data.get("expenses", []):
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO expenses
                        (id, project_id, title, amount, category,
                         description, created_by, expense_date,
                         status, approved_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (ex.get("id"), ex.get("project_id"), ex.get("title"),
                      ex.get("amount", 0), ex.get("category"),
                      ex.get("description"), ex.get("created_by"),
                      ex.get("expense_date"), ex.get("status", "pending"),
                      ex.get("approved_by"), ex.get("created_at")))
                count += 1
            except Exception as e:
                print(f"خطا expense: {e}")

        # ---- material_requests ----
        for m in data.get("material_requests", []):
            try:
                cur.execute("""
                    INSERT OR IGNORE INTO material_requests
                        (id, project_id, requester, title, description,
                         items_text, total_estimate, status,
                         customer_name, admin_note, approved_by,
                         approved_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (m.get("id"), m.get("project_id"), m.get("requester"),
                      m.get("title"), m.get("description"),
                      m.get("items_text"), m.get("total_estimate", 0),
                      m.get("status", "pending"), m.get("customer_name"),
                      m.get("admin_note"), m.get("approved_by"),
                      m.get("approved_at"), m.get("created_at")))
                count += 1
            except Exception as e:
                print(f"خطا material_request: {e}")

        conn.commit()

        if data.get("username"):
            log_sync(data["username"], "import", count,
                     f"sync_id={data.get('sync_id')}")

        return count

    finally:
        conn.close()


# ========================================================
# آمار
# ========================================================
def get_pending_syncs():
    """لیست فایل‌های sync موجود در پوشه Share."""
    share = get_share_path()
    if not share:
        return []

    sync_dir = share / "sync"
    if not sync_dir.exists():
        return []

    result = []
    for f in sync_dir.glob("*.json"):
        try:
            with open(f, encoding="utf-8") as fp:
                data = json.load(fp)

            total = (len(data.get("reports", []))
                     + len(data.get("timesheets", []))
                     + len(data.get("expenses", []))
                     + len(data.get("material_requests", [])))

            result.append({
                "file": f.name,
                "username": data.get("username", "?"),
                "date": data.get("date", "?"),
                "records": total,
            })
        except Exception:
            pass

    return result