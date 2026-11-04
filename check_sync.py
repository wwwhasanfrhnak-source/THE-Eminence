"""چک جدول sync_log."""
from electrocalc.data.database import get_connection

conn = get_connection()
cur = conn.cursor()

# چک جدول
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sync_log'")
exists = bool(cur.fetchone())
print(f"Table sync_log exists: {exists}")

if exists:
    cur.execute("PRAGMA table_info(sync_log)")
    print("\nستون‌ها:")
    for row in cur.fetchall():
        print(f"  - {row[1]} ({row[2]})")

    cur.execute("SELECT COUNT(*) FROM sync_log")
    print(f"\nتعداد رکورد: {cur.fetchone()[0]}")

conn.close()