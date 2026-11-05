import sqlite3
from pathlib import Path
db_path = Path(__file__).with_name("electrocalc.db")
print("Database path:", db_path.resolve())
print("Database exists:", db_path.exists())
if not db_path.exists():
    raise SystemExit("Database file not found!")
uri = db_path.resolve().as_uri() + "?mode=ro"
with sqlite3.connect(uri, uri=True) as conn:
    print("\nTables:")
    for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ):
        print("-", row[0])
    print("\nInvoices columns:")
    for row in conn.execute("PRAGMA table_info(invoices)"):
        print(row)
    print("\nInvoice count:")
    print(conn.execute("SELECT COUNT(*) FROM invoices").fetchone()[0])
