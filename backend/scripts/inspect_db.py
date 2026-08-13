import sqlite3
import os

db_paths = [
    "school_scheduler.db",
    "backend/school_scheduler.db"
]

for p in db_paths:
    if os.path.exists(p):
        print(f"=== DB: {p} ===")
        conn = sqlite3.connect(p)
        cursor = conn.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        print("Tables:", [t[0] for t in tables])
        
        # Count classes, courses, teachers
        for t in ["classes", "courses", "teachers", "course_assignments", "schools"]:
            if (t,) in tables:
                cnt = cursor.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                print(f"  {t}: {cnt} rows")
        conn.close()
