import sqlite3

conn = sqlite3.connect("school_scheduler.db")
cursor = conn.cursor()
for table in ["classes", "courses", "teachers", "course_assignments"]:
    print(f"--- Table: {table} ---")
    cols = cursor.execute(f"PRAGMA table_info({table})").fetchall()
    for col in cols:
        print(f"  {col[1]} ({col[2]})")
conn.close()
