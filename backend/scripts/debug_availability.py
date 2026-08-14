"""
Asil root cause analizi: time_slots ve course_assignments tablolari
"""
import sqlite3

conn = sqlite3.connect("school_scheduler.db")
cur = conn.cursor()

# 1. time_slots tablosu
print("=== time_slots ===")
cnt = cur.execute("SELECT COUNT(*) FROM time_slots").fetchone()[0]
print(f"Total rows: {cnt}")
if cnt > 0:
    rows = cur.execute("SELECT * FROM time_slots LIMIT 10").fetchall()
    cols = [d[0] for d in cur.description]
    print("Columns:", cols)
    for r in rows:
        print(r)
print()

# 2. course_assignments tablosu
print("=== course_assignments ===")
cnt2 = cur.execute("SELECT COUNT(*) FROM course_assignments").fetchone()[0]
print(f"Total rows: {cnt2}")
if cnt2 > 0:
    rows2 = cur.execute("SELECT * FROM course_assignments LIMIT 5").fetchall()
    cols2 = [d[0] for d in cur.description]
    print("Columns:", cols2)
    for r in rows2:
        print(r)
print()

# 3. timetables
print("=== timetables ===")
cnt3 = cur.execute("SELECT COUNT(*) FROM timetables").fetchone()[0]
print(f"Total rows: {cnt3}")
if cnt3 > 0:
    rows3 = cur.execute("SELECT * FROM timetables ORDER BY id DESC LIMIT 5").fetchall()
    cols3 = [d[0] for d in cur.description]
    print("Columns:", cols3)
    for r in rows3:
        print(r)
print()

# 4. Kritik analiz: time_slots bos ise ne olur?
print("=== KRITIK ANALIZ ===")
if cnt == 0:
    print("SORUN BULUNDU: time_slots tablosu BOŞ!")
    print("  solver_task.py satir 141-151:")
    print("  'day_periods = defaultdict(set)'")
    print("  'for slot in timeslots: day_periods[slot.day].add(slot.period)'")
    print("  'max_day = max(day_periods.keys(), default=4)'")
    print()
    print("  time_slots BOŞ ise => day_periods bos => max_day = 4 (default)")
    print("  => gunluk_ders_saatleri = [0, 0, 0, 0, 0] cunku periods bos set!")
    print()
    print("  avail_map[t.id] = {gun: [True] * 0 for ...} => TUM LISTELER BOSH!")
    print()
    print("  Ogretmen.musait_mi(gun, saat_idx): if saat_idx >= len(gunluk) => False!")
    print("  => HER SAAT icin musait_mi() = False!")
    print()
    print("  Bu yuzden C3 kisiti: her (x, y) kombinasyonu icin x + y <= 1")
    print("  => y_vars hicbiri 1 olamaz => INFEASIBLE!")
    print()
    print("  SONUC: time_slots doldurmak gerekiyor ya da kod time_slots olmadan")
    print("  fallback kullanmali (weekly_lesson_structure'dan gunluk saati alarak)")
else:
    print(f"time_slots dolu ({cnt} kayit). Baska sorun aranmali.")
    day_dist = cur.execute("SELECT day, COUNT(*) FROM time_slots WHERE is_active=1 GROUP BY day").fetchall()
    print("Day distribution:", day_dist)
    period_dist = cur.execute("SELECT day, MAX(period) FROM time_slots WHERE is_active=1 GROUP BY day").fetchall()
    print("Max period per day:", period_dist)

print()

# 5. Teacher availability ayrintisi
print("=== DAY_NAMES karsilastirmasi ===")
print("solver_task.py DAY_NAMES = ['Pazartesi', 'Sali', 'Carsamba', 'Persembe', 'Cuma']")
avail_rows = cur.execute("SELECT DISTINCT day FROM teacher_availability ORDER BY day").fetchall()
print("teacher_availability'daki gun indexleri:", [r[0] for r in avail_rows])
print("Bu indexler 0-4 arasi olmali (0=Pazartesi)")

conn.close()
