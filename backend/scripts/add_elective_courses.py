"""
Eksik secmeli dersleri ekle:
- SCM567: 5 haftalik saat, 5/A 5/B 6/A 6/B 7/A 7/B icin
- SCM8:   6 haftalik saat, 8/A 8/B icin
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect("school_scheduler.db")
cur = conn.cursor()

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

# Mevcut ders ID'lerini kontrol et
existing = cur.execute("SELECT id, name, code FROM courses WHERE school_id=1").fetchall()
print("Mevcut dersler:", existing)
print()

# Mevcut en buyuk ID
max_id = cur.execute("SELECT MAX(id) FROM courses").fetchone()[0] or 0
print(f"Max course ID: {max_id}")
print()

# SCM567 zaten var mi?
scm567_exists = cur.execute("SELECT id FROM courses WHERE code='SCM567' AND school_id=1").fetchone()
scm8_exists = cur.execute("SELECT id FROM courses WHERE code='SCM8' AND school_id=1").fetchone()

if not scm567_exists:
    # 5, 6, 7. siniflar: target_classes = '5/A,5/B,6/A,6/B,7/A,7/B'
    # weekly_hours=5, hour_distribution='1+1+1+1+1' (her gun 1 saat)
    cur.execute("""
        INSERT INTO courses 
        (name, code, branch, weekly_hours, hour_distribution, is_elective, target_classes, school_id, is_active, is_deleted, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Seçmeli Ders (5-6-7)", "SCM567", "SECMELI", 
        5, "1+1+1+1+1", 1, 
        "5/A,5/B,6/A,6/B,7/A,7/B",
        1, 1, 0, now, now
    ))
    scm567_id = cur.lastrowid
    print(f"SCM567 eklendi (id={scm567_id})")
else:
    scm567_id = scm567_exists[0]
    print(f"SCM567 zaten var (id={scm567_id})")

if not scm8_exists:
    # 8. siniflar: target_classes = '8/A,8/B'
    # weekly_hours=6, hour_distribution='1+1+1+1+1+1' (6 saat)
    # Ama 6 gun yok, 5 gun var. O yuzden birkac gun 2 saat olabilir: '2+1+1+1+1'
    cur.execute("""
        INSERT INTO courses 
        (name, code, branch, weekly_hours, hour_distribution, is_elective, target_classes, school_id, is_active, is_deleted, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Seçmeli Ders (8)", "SCM8", "SECMELI8",
        6, "2+1+1+1+1", 1,
        "8/A,8/B",
        1, 1, 0, now, now
    ))
    scm8_id = cur.lastrowid
    print(f"SCM8 eklendi (id={scm8_id})")
else:
    scm8_id = scm8_exists[0]
    print(f"SCM8 zaten var (id={scm8_id})")

conn.commit()
print()

# Sonucu dogrula
print("=== Sinif bazinda toplam ders saati (guncellendi) ===")
courses_raw = cur.execute("""
    SELECT id, name, weekly_hours, target_classes 
    FROM courses WHERE school_id=1 AND is_active=1 AND is_deleted=0
""").fetchall()

classes_raw = cur.execute("""
    SELECT id, name FROM classes WHERE school_id=1 AND is_active=1 AND is_deleted=0
""").fetchall()

for cls_id, cls_name in classes_raw:
    assigned = []
    for c_id, c_name, c_wh, c_target in courses_raw:
        targets = [] if (not c_target or c_target.strip().upper() == "ALL") else [x.strip() for x in c_target.split(",")]
        if not targets or cls_name in targets:
            assigned.append((c_name, c_wh))
    total = sum(h for _, h in assigned)
    status = "OK" if total == 35 else f"HATA! {total} != 35"
    print(f"  {cls_name}: {total} saat -> {status}")

conn.close()
