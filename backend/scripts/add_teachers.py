import sqlite3
from datetime import datetime

conn = sqlite3.connect("school_scheduler.db")
cur = conn.cursor()

now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Eklenecek ogretmenler
new_teachers = [
    {
        "first_name": "TEKNOLOJI",
        "last_name": "OGRETMENI",
        "branch": "Teknoloji ve Tasarım",
        "allowed_courses": "Teknoloji ve Tasarım",
    },
    {
        "first_name": "MUZIK",
        "last_name": "OGRETMENI",
        "branch": "Müzik",
        "allowed_courses": "Müzik",
    },
    {
        "first_name": "GORSEL",
        "last_name": "SANATLAR OGRETMENI",
        "branch": "Görsel Sanatlar",
        "allowed_courses": "Görsel Sanatlar",
    },
]

for t in new_teachers:
    cur.execute("""
        INSERT INTO teachers 
        (first_name, last_name, branch, allowed_courses, allowed_classes,
         max_daily_hours, max_weekly_hours, school_id, is_active, is_deleted, created_at, updated_at)
        VALUES (?, ?, ?, ?, 'ALL', 8, 30, 1, 1, 0, ?, ?)
    """, (t["first_name"], t["last_name"], t["branch"], t["allowed_courses"], now, now))
    tid = cur.lastrowid
    print(f"Eklendi: id={tid} | {t['first_name']} {t['last_name']} | brans={t['branch']}")

conn.commit()
conn.close()
print("\nTamamlandi! 3 ogretmen eklendi.")
