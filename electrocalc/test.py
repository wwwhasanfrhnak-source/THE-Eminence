import sys
sys.path.insert(0, '.')
from electrocalc.data.database import get_connection, init_db
init_db()
conn = get_connection()
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("TABLES:", tables)
conn.close()