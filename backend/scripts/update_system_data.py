import sqlite3
import os
from datetime import datetime

db_paths = [
    os.path.abspath("school_scheduler.db"),
    os.path.abspath("backend/school_scheduler.db")
]

classes_data = [
    ("5/A", 5, "A", 30),
    ("5/B", 5, "B", 30),
    ("6/A", 6, "A", 30),
    ("6/B", 6, "B", 30),
    ("7/A", 7, "A", 30),
    ("7/B", 7, "B", 30),
    ("8/A", 8, "A", 30),
    ("8/B", 8, "B", 30),
]

courses_data = [
    # name, code, branch, weekly_hours, target_classes, hour_distribution
    ("Türkçe", "TR56", "Türkçe", 6, "5/A,5/B,6/A,6/B", "2+2+2"),
    ("Türkçe", "TR78", "Türkçe", 5, "7/A,7/B,8/A,8/B", "2+2+1"),
    ("Matematik", "MAT", "İlköğretim Matematik", 5, "5/A,5/B,6/A,6/B,7/A,7/B,8/A,8/B", "2+2+1"),
    ("Fen Bilimleri", "FEN", "Fen Bilimleri", 4, "5/A,5/B,6/A,6/B,7/A,7/B,8/A,8/B", "2+2"),
    ("Sosyal Bilgiler", "SOS", "Sosyal Bilgiler", 3, "5/A,5/B,6/A,6/B,7/A,7/B", "2+1"),
    ("T.C. İnkılap Tarihi ve Atatürkçülük", "INK", "Sosyal Bilgiler", 2, "8/A,8/B", "2"),
    ("Yabancı Dil", "YD56", "İngilizce", 3, "5/A,5/B,6/A,6/B", "2+1"),
    ("Yabancı Dil", "YD78", "İngilizce", 4, "7/A,7/B,8/A,8/B", "2+2"),
    ("Din Kültürü ve Ahlak Bilgisi", "DIN", "Din Kültürü ve Ahlâk Bilgisi", 2, "5/A,5/B,6/A,6/B,7/A,7/B,8/A,8/B", "2"),
    ("Görsel Sanatlar", "GOR", "Görsel Sanatlar", 1, "5/A,5/B,6/A,6/B,7/A,7/B,8/A,8/B", "1"),
    ("Müzik", "MUZ", "Müzik", 1, "5/A,5/B,6/A,6/B,7/A,7/B,8/A,8/B", "1"),
    ("Beden Eğitimi ve Spor", "BED", "Beden Eğitimi", 2, "5/A,5/B,6/A,6/B,7/A,7/B,8/A,8/B", "2"),
    ("Teknoloji ve Tasarım", "TEK", "Teknoloji ve Tasarım", 2, "7/A,7/B,8/A,8/B", "2"),
    ("Bilişim Teknolojileri ve Yazılım", "BIL", "Bilgisayar ve Öğretim Teknolojileri", 2, "5/A,5/B,6/A,6/B", "2"),
    ("Rehberlik ve Yönlendirme", "REH", "Rehberlik", 1, "5/A,5/B,6/A,6/B,7/A,7/B,8/A,8/B", "1"),
]

teachers_data = [
    ("ALİ", "KOBAK", "Din Kültürü ve Ahlâk Bilgisi", "Din Kültürü ve Ahlak Bilgisi"),
    ("BAHAR", "DAL", "İngilizce", "Yabancı Dil"),
    ("BESTE", "TANRIÖVER", "Fen Bilimleri", "Fen Bilimleri"),
    ("CANSU", "ÇETİNKAL", "İlköğretim Matematik", "Matematik"),
    ("EDA", "KAYNAK", "İlköğretim Matematik", "Matematik"),
    ("FİLİZ", "KULAKSIZ", "Türkçe", "Türkçe"),
    ("GÖZDE", "YILMAZ GÖKYAKA", "Rehberlik", "Rehberlik ve Yönlendirme"),
    ("HÜSNİYE ŞULE", "KILIÇALP", "Sosyal Bilgiler", "Sosyal Bilgiler,T.C. İnkılap Tarihi ve Atatürkçülük"),
    ("İLKAY", "MEYDAN", "Türkçe", "Türkçe"),
    ("KEMAL", "KILIÇALP", "Fen Bilimleri", "Fen Bilimleri"),
    ("MUSTAFA", "ZORLU", "Din Kültürü ve Ahlâk Bilgisi", "Din Kültürü ve Ahlak Bilgisi"),
    ("NİHAT", "DAĞISTANLI", "Beden Eğitimi", "Beden Eğitimi ve Spor"),
    ("NURİ", "GÜNAYDIN", "İngilizce", "Yabancı Dil"),
    ("OKTAY", "VARLIK", "İlköğretim Matematik", "Matematik"),
    ("PINAR", "KAYLAN", "Bilgisayar ve Öğretim Teknolojileri", "Bilişim Teknolojileri ve Yazılım"),
    ("RAMAZAN", "ŞAHİN", "Sosyal Bilgiler", "Sosyal Bilgiler,T.C. İnkılap Tarihi ve Atatürkçülük"),
    ("ŞÜKRAN", "DALBAYRAK", "Türkçe", "Türkçe"),
    ("TANER", "BİLALOĞLU", "Din Kültürü ve Ahlâk Bilgisi", "Din Kültürü ve Ahlak Bilgisi"),
]

create_courses_sql = """
CREATE TABLE courses (
    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, 
    school_id INTEGER NOT NULL, 
    name VARCHAR(150) NOT NULL, 
    code VARCHAR(20), 
    description TEXT, 
    branch VARCHAR(100), 
    weekly_hours INTEGER NOT NULL DEFAULT 1, 
    hour_distribution VARCHAR(255) DEFAULT '2+2+1+1', 
    consecutive_hours INTEGER NOT NULL DEFAULT 1, 
    requires_classroom BOOLEAN NOT NULL DEFAULT 0, 
    required_room_type VARCHAR(50), 
    is_elective BOOLEAN NOT NULL DEFAULT 0, 
    target_classes VARCHAR(255) DEFAULT 'ALL', 
    is_active BOOLEAN NOT NULL DEFAULT 1, 
    created_at DATETIME, 
    updated_at DATETIME, 
    is_deleted BOOLEAN NOT NULL DEFAULT 0, 
    deleted_at DATETIME, 
    FOREIGN KEY(school_id) REFERENCES schools (id) ON DELETE CASCADE, 
    CONSTRAINT uq_course_school_code UNIQUE (school_id, code)
);
"""

for db_path in db_paths:
    if not os.path.exists(db_path):
        print(f"Skipping non-existent DB: {db_path}")
        continue
    
    print(f"\n==========================================")
    print(f"Updating Database: {db_path}")
    print(f"==========================================")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get school_id (default 1 if exists)
    cursor.execute("SELECT id FROM schools LIMIT 1")
    row = cursor.fetchone()
    if row:
        school_id = row[0]
    else:
        cursor.execute(
            "INSERT INTO schools (name, short_name, city, district, is_active, created_at, updated_at, is_deleted) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("Atatürk Ortaokulu", "AO", "İstanbul", "Kadıköy", 1, datetime.now().isoformat(), datetime.now().isoformat(), 0)
        )
        school_id = cursor.lastrowid

    # 1. Clear old data from assignments, classes, teachers
    cursor.execute("DELETE FROM course_assignments WHERE school_id = ?", (school_id,))
    cursor.execute("DELETE FROM classes WHERE school_id = ?", (school_id,))
    cursor.execute("DELETE FROM teachers WHERE school_id = ?", (school_id,))

    # Recreate courses table to support uq_course_school_code
    cursor.execute("DROP TABLE IF EXISTS courses")
    cursor.execute(create_courses_sql)
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_courses_school_id ON courses (school_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_courses_branch ON courses (branch)")
    print("[OK] Recreated courses table with code-based unique constraint")

    # 2. Insert Classes
    class_id_map = {}
    for name, grade, sec, cnt in classes_data:
        now = datetime.now().isoformat()
        cursor.execute(
            """INSERT INTO classes (school_id, name, grade, section, student_count, max_daily_hours, is_active, created_at, updated_at, is_deleted)
               VALUES (?, ?, ?, ?, ?, 6, 1, ?, ?, 0)""",
            (school_id, name, grade, sec, cnt, now, now)
        )
        class_id_map[name] = cursor.lastrowid
    print(f"[OK] Inserted {len(classes_data)} Classes: {list(class_id_map.keys())}")

    # 3. Insert Courses
    course_id_map = {}
    for cname, code, br, wh, target_cls, dist in courses_data:
        now = datetime.now().isoformat()
        cursor.execute(
            """INSERT INTO courses (school_id, name, code, branch, weekly_hours, target_classes, hour_distribution, consecutive_hours, requires_classroom, is_elective, is_active, created_at, updated_at, is_deleted)
               VALUES (?, ?, ?, ?, ?, ?, ?, 2, 0, 0, 1, ?, ?, 0)""",
            (school_id, cname, code, br, wh, target_cls, dist, now, now)
        )
        course_id_map[code] = cursor.lastrowid
    print(f"[OK] Inserted {len(courses_data)} Courses with Middle School Curriculum")

    # 4. Insert Teachers
    teacher_id_list = []
    for fn, ln, br, allowed_c in teachers_data:
        now = datetime.now().isoformat()
        cursor.execute(
            """INSERT INTO teachers (school_id, first_name, last_name, branch, allowed_courses, allowed_classes, max_daily_hours, max_weekly_hours, is_active, created_at, updated_at, is_deleted)
               VALUES (?, ?, ?, ?, ?, 'ALL', 8, 30, 1, ?, ?, 0)""",
            (school_id, fn, ln, br, allowed_c, now, now)
        )
        teacher_id_list.append(cursor.lastrowid)
    print(f"[OK] Inserted {len(teachers_data)} Teachers")

    conn.commit()
    conn.close()
    print("Database sync completed successfully!")
