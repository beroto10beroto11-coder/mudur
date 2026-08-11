import sqlite3
import os

db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "school_scheduler.db")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE teachers SET allowed_courses = branch WHERE branch IS NOT NULL AND branch != ''")
    conn.commit()
    conn.close()
    print(f"[OK] Successfully updated teacher allowed_courses to match their branch in {db_path}")
else:
    print(f"[!] Database file not found at {db_path}")
