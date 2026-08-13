import sqlite3

conn = sqlite3.connect("school_scheduler.db")
cursor = conn.cursor()
indices = cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='courses'").fetchall()
for idx in indices:
    print(idx)
conn.close()
