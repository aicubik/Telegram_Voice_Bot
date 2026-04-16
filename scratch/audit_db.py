"""Audit script: check both DB files and verify paths."""
import sqlite3
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "Scripts")

# What memory_manager.py computes:
mm_db_path = os.path.join(os.path.dirname(os.path.abspath(os.path.join(SCRIPTS_DIR, "memory_manager.py"))), "..", "assistant_data.db")
mm_db_path = os.path.normpath(mm_db_path)

print(f"PROJECT_ROOT:        {PROJECT_ROOT}")
print(f"SCRIPTS_DIR:         {SCRIPTS_DIR}")
print(f"memory_manager path: {mm_db_path}")
print()

db_files = [
    ("ROOT DB", os.path.join(PROJECT_ROOT, "assistant_data.db")),
    ("SCRIPTS DB", os.path.join(SCRIPTS_DIR, "assistant_data.db")),
    ("MM computed", mm_db_path),
]

for label, path in db_files:
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    print(f"{label}: {path}")
    print(f"  exists={exists}, size={size} bytes")
    if exists and size > 0:
        try:
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            print(f"  tables: {tables}")
            for t in tables:
                cur.execute(f"SELECT COUNT(*) FROM [{t}]")
                cnt = cur.fetchone()[0]
                print(f"    {t}: {cnt} rows")
                if t == "reminders":
                    cur.execute(f"SELECT * FROM reminders LIMIT 5")
                    rows = cur.fetchall()
                    for row in rows:
                        print(f"      {row}")
            conn.close()
        except Exception as e:
            print(f"  ERROR reading: {e}")
    print()

# Check: are ROOT and MM computed the same file?
print("=" * 60)
root_norm = os.path.normpath(os.path.join(PROJECT_ROOT, "assistant_data.db"))
print(f"ROOT path (normalized):  {root_norm}")
print(f"MM path (normalized):    {mm_db_path}")
print(f"SAME FILE? {root_norm == mm_db_path}")
