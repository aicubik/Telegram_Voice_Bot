import sqlite3
import os
import time
from datetime import datetime

db_path = 'assistant_data.db'
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Get tables
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cur.fetchall()]
print(f"Tables: {tables}")

if 'reminders' in tables:
    cur.execute("SELECT * FROM reminders ORDER BY created_at DESC LIMIT 5")
    rows = cur.fetchall()
    print("\nRecent reminders:")
    for r in rows:
        print(r)
    
    # Check for anything that should have fired at 7:00 (approx)
    # 7:00 Minsk is 1713153600 (example)
    cur.execute("SELECT COUNT(*) FROM reminders WHERE status='pending'")
    print(f"Pending count: {cur.fetchone()[0]}")
else:
    print("Reminders table missing!")

conn.close()
