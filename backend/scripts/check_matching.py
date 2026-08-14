import sqlite3
conn = sqlite3.connect("school_scheduler.db")
cur = conn.cursor()

# Sorunlu dersler
print("=== Sorunlu Dersler ===")
rows = cur.execute("SELECT id, name, code, branch FROM courses WHERE school_id=1 AND is_active=1 AND is_deleted=0 ORDER BY id").fetchall()
for r in rows:
    print(f"  id={r[0]}: name={r[1]!r}, code={r[2]!r}, branch={r[3]!r}")

print()
print("=== Tum Ogretmenler ===")
rows2 = cur.execute("SELECT id, first_name, last_name, branch, allowed_courses FROM teachers WHERE school_id=1 AND is_active=1 AND is_deleted=0 ORDER BY id").fetchall()
for r in rows2:
    print(f"  id={r[0]}: {r[1]} {r[2]} | branch={r[3]!r} | allowed_courses={r[4]!r}")

print()
print("=== ESLESTIRME ANALIZI ===")
print("Solver eslestirme mantigi:")
print("  ders.kod = course.branch or course.code")
print("  ogretmen.branslar = [teacher.branch] + allowed_courses.split(',')")
print("  Eslesme: ders.kod IN ogretmen.branslar")
print()

# Her ders icin eslesen ogretmen sayisi
for c_id, c_name, c_code, c_branch in rows:
    ders_kod = c_branch if c_branch else c_code
    matching = []
    for t_id, t_fn, t_ln, t_branch, t_ac in rows2:
        branslar = []
        if t_branch:
            branslar.append(t_branch.strip())
        if t_ac and t_ac != "ALL":
            for part in t_ac.split(","):
                part = part.strip()
                if part and part not in branslar:
                    branslar.append(part)
        if not branslar:
            branslar = ["GENEL"]

        if ders_kod in branslar:
            matching.append(f"{t_fn} {t_ln}")

    if not matching:
        print(f"  HATA: {c_name} (kod={ders_kod!r}) -> HICBIR OGRETMEN ESLESMEDI!")
    else:
        print(f"  OK: {c_name} (kod={ders_kod!r}) -> {len(matching)} ogretmen")

conn.close()
