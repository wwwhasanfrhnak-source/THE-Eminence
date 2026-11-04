"""اتصال به پایگاه داده SQLite — سازگار با EXE + sync."""

import sys
import sqlite3
from pathlib import Path


# ========================================================
# تشخیص مسیر دیتابیس
# ========================================================
if getattr(sys, "frozen", False):
    BASE = Path(sys.executable).parent
else:
    BASE = Path(__file__).resolve().parents[2]

DB_FILE = BASE / "electrocalc.db"


# ========================================================
# اتصال
# ========================================================
def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row

    try:
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode = WAL")
        cur.execute("PRAGMA synchronous = NORMAL")
        cur.execute("PRAGMA busy_timeout = 5000")
        cur.execute("PRAGMA foreign_keys = ON")
        cur.close()
    except Exception:
        pass

    return conn


# ========================================================
# Init — ساخت جداول
# ========================================================
def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()

    # users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            role TEXT NOT NULL DEFAULT 'engineer',
            phone TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            avatar_path TEXT,
            permissions TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # projects
    cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            customer TEXT,
            address TEXT,
            description TEXT,
            status TEXT NOT NULL DEFAULT 'in_progress',
            start_date TEXT,
            end_date TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # project_members
    cur.execute("""
        CREATE TABLE IF NOT EXISTS project_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            added_at TEXT NOT NULL,
            UNIQUE(project_id, username)
        )
    """)

    # reports
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            author TEXT NOT NULL,
            report_date TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            hours REAL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'pending',
            approved_by TEXT,
            approved_at TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # timesheets
    cur.execute("""
        CREATE TABLE IF NOT EXISTS timesheets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            project_id INTEGER,
            work_date TEXT NOT NULL,
            start_time TEXT,
            end_time TEXT,
            hours REAL DEFAULT 0,
            description TEXT,
            status TEXT DEFAULT 'pending',
            approved_by TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # materials
    cur.execute("""
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            name TEXT NOT NULL,
            quantity REAL DEFAULT 0,
            unit TEXT,
            unit_price REAL DEFAULT 0,
            total_price REAL DEFAULT 0,
            description TEXT,
            created_by TEXT,
            material_date TEXT,
            status TEXT DEFAULT 'pending',
            approved_by TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # warehouse
    cur.execute("""
        CREATE TABLE IF NOT EXISTS warehouse (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE,
            name TEXT NOT NULL,
            category TEXT,
            unit TEXT DEFAULT 'عدد',
            quantity REAL DEFAULT 0,
            min_quantity REAL DEFAULT 0,
            purchase_price REAL DEFAULT 0,
            sale_price REAL DEFAULT 0,
            supplier TEXT,
            location TEXT,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
    """)

    # warehouse_transactions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS warehouse_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            warehouse_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL DEFAULT 0,
            total_price REAL DEFAULT 0,
            project_id INTEGER,
            supplier TEXT,
            note TEXT,
            created_by TEXT,
            trans_date TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # expenses
    cur.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            amount REAL DEFAULT 0,
            category TEXT,
            description TEXT,
            created_by TEXT,
            expense_date TEXT,
            status TEXT DEFAULT 'pending',
            approved_by TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # files
    cur.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            filepath TEXT NOT NULL,
            uploaded_by TEXT,
            description TEXT,
            uploaded_at TEXT NOT NULL
        )
    """)

    # messages
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            subject TEXT,
            body TEXT,
            is_read INTEGER DEFAULT 0,
            sent_at TEXT NOT NULL
        )
    """)

    # company
    cur.execute("""
        CREATE TABLE IF NOT EXISTS company (
            id INTEGER PRIMARY KEY,
            name TEXT,
            logo_path TEXT,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            registration TEXT,
            tax_id TEXT,
            economic_code TEXT,
            updated_at TEXT
        )
    """)

    # active_sessions
    cur.execute("""
        CREATE TABLE IF NOT EXISTS active_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            project_id INTEGER,
            login_at TEXT NOT NULL,
            last_ping TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        )
    """)

    # audit_log
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            action TEXT NOT NULL,
            object_type TEXT,
            object_id INTEGER,
            description TEXT,
            old_value TEXT,
            new_value TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # app_settings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
    """)

    # notifications
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT,
            category TEXT DEFAULT 'info',
            link_to TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    # tasks
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            assigned_to TEXT,
            priority TEXT DEFAULT 'medium',
            status TEXT DEFAULT 'pending',
            due_date TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT
        )
    """)

    # customers
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            company TEXT,
            phone TEXT,
            mobile TEXT,
            email TEXT,
            address TEXT,
            city TEXT,
            national_id TEXT,
            economic_code TEXT,
            notes TEXT,
            created_by TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # material_requests
    cur.execute("""
        CREATE TABLE IF NOT EXISTS material_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            requester TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            items_text TEXT,
            total_estimate REAL DEFAULT 0,
            status TEXT DEFAULT 'pending',
            customer_name TEXT,
            admin_note TEXT,
            approved_by TEXT,
            approved_at TEXT,
            created_at TEXT NOT NULL
        )
    """)

    # invoices
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT UNIQUE NOT NULL,
            customer_id INTEGER,
            project_id INTEGER,
            issue_date TEXT NOT NULL,
            due_date TEXT,
            subtotal REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            tax REAL DEFAULT 0,
            total REAL DEFAULT 0,
            paid REAL DEFAULT 0,
            status TEXT DEFAULT 'پیش‌نویس',
            notes TEXT,
            created_by TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
    """)

    # invoice_items
    cur.execute("""
        CREATE TABLE IF NOT EXISTS invoice_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            description TEXT NOT NULL,
            quantity REAL DEFAULT 1,
            unit_price REAL DEFAULT 0,
            total REAL DEFAULT 0,
            item_type TEXT DEFAULT 'کالا',
            FOREIGN KEY (invoice_id) REFERENCES invoices(id)
                ON DELETE CASCADE
        )
    """)

    # ========================================================
    # sync_log — لاگ همگام‌سازی
    # ========================================================
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            sync_date TEXT NOT NULL,
            sync_type TEXT NOT NULL,
            records_count INTEGER DEFAULT 0,
            notes TEXT
        )
    """)

    conn.commit()

    # ========================================================
    # مهاجرت‌ها
    # ========================================================
    cur.execute("PRAGMA table_info(users)")
    cols = [r[1] for r in cur.fetchall()]
    if "avatar_path" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN avatar_path TEXT")
    if "permissions" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN permissions TEXT")

    cur.execute("PRAGMA table_info(active_sessions)")
    cols = [r[1] for r in cur.fetchall()]
    if "project_id" not in cols:
        cur.execute("ALTER TABLE active_sessions ADD COLUMN project_id INTEGER")

    # ========================================================
    # Indexها
    # ========================================================
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_timesheets_user ON timesheets(username)",
        "CREATE INDEX IF NOT EXISTS idx_timesheets_date ON timesheets(work_date)",
        "CREATE INDEX IF NOT EXISTS idx_reports_author ON reports(author)",
        "CREATE INDEX IF NOT EXISTS idx_reports_date ON reports(report_date)",
        "CREATE INDEX IF NOT EXISTS idx_expenses_project ON expenses(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_expenses_user ON expenses(created_by)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_project ON invoices(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status)",
        "CREATE INDEX IF NOT EXISTS idx_warehouse_trans_project ON warehouse_transactions(project_id)",
        "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(username)",
        "CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(username)",
        "CREATE INDEX IF NOT EXISTS idx_sync_log_user ON sync_log(username)",
        "CREATE INDEX IF NOT EXISTS idx_sync_log_date ON sync_log(sync_date)",
    ]
    for sql in indexes:
        try:
            cur.execute(sql)
        except Exception:
            pass

    conn.commit()
    conn.close()