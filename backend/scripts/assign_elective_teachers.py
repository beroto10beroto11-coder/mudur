"""
Secmeli ders ogretmen kontrolu:
- SCM567 (SECMELI bransi) icin ogretmen bul/ata
- SCM8 (SECMELI8 bransi) icin ogretmen bul/ata

Solver'da ogretmen eslestirmesi su sekilde calisiyor (solver_task.py):
  _extract_branslar(teacher):
    if teacher.branch: branslar.append(teacher.branch)
    if allowed_courses != 'ALL': parcala ve ekle
    if branslar bos: branslar = ['GENEL']

  model_builder.py C1/C2/C3:
    uygun_ogretmenler = [o for o in ogretmenler if ders.kod in o.branslar ...]
    Ders kodu = _extract_ders_kodu(course) = course.branch if branch else code...

Yani SCM567 icin ders.kod = 'SECMELI' olmali.
Bir ogretmenin bu derse girmesi icin: 
  teacher.branch == 'SECMELI' VEYA teacher.allowed_courses LIKE '%SCM567%' veya '%Secmeli Ders%'
"""
import sqlite3

conn = sqlite3.connect("school_scheduler.db")
cur = conn.cursor()

# Yeni dersleri kontrol et
courses = cur.execute("""
    SELECT id, name, code, branch FROM courses WHERE code IN ('SCM567', 'SCM8')
""").fetchall()
print("Secmeli dersler:", courses)
print()

# solver_task.py _extract_ders_kodu:
#   if course.branch: return course.branch.strip()
#   elif course.code: return course.code.strip()
# => SCM567 bransi = 'SECMELI' => ders.kod = 'SECMELI'
# => SCM8 bransi = 'SECMELI8' => ders.kod = 'SECMELI8'

# _extract_branslar:
#   if teacher.branch: branslar.append(teacher.branch)
#   if allowed_courses != 'ALL': split by ',' ve ekle
# Hicbir ogretmenin branch = SECMELI degil.
# Uygun ogretmen = hicbiri

# Cozum: Tüm öğretmenler için allowed_courses'a 'Seçmeli Ders' eklemek yerine,
# ALTERNATIF: dersin branşını ALL yapmak yerine öğretmenlerin allowed_courses'ına ekle.
# En kolay cozum: Birkaç öğretmenin allowed_courses'una SCM567 ve SCM8 ekle.

# Mevcut ogretmenler
teachers = cur.execute("""
    SELECT id, first_name, last_name, branch, allowed_courses, allowed_classes 
    FROM teachers WHERE school_id=1 AND is_active=1 AND is_deleted=0
""").fetchall()
print("=== Ogretmenler ===")
for t in teachers:
    print(f"  id={t[0]}, {t[1]} {t[2]}, branch={t[3]!r}, allowed_courses={t[4]!r}")
print()

# Secmeli ders icin: en az 1 ogretmen gerekli her sube icin.
# SCM567 icin -> 5-6-7. siniflar (6 sube) -> 1 ogretmen yeterli ama yuk cok olur.
# En mantikli: Rehberlik ogretmeni ya da branssiz biri ata.
# Ya da: dersin branch'ini None yap, code=SCM567 olsun.
# Sonra _extract_ders_kodu => code.strip() = 'SCM567'
# Ogretmen allowed_courses = 'Seçmeli Ders (5-6-7)' ya da 'SCM567' icerirse kabul.

# Plan: courses tablosunda SCM567'nin branch'ini NULL yap (kod kalsin).
# Sonra allowed_courses'a 'SCM567' veya ders adi ekle.
# Ama daha temiz: allowed_courses field'ina ekleme yapalim.

# Rehberlik ogretmeni (Rehberlik ve Yonlendirme = REH bransi) veya herhangi biri
# SCM567 ve SCM8 derslerini verebilecek olarak isaretleyelim.

# En az direnc: allowed_courses'a ekleme yap
# SCM567 icin: 2-3 ogretmen secelim (yuk dagitimi icin)
# SCM8 icin: 1-2 ogretmen

print("=== Yapilanacak islem ===")
print("courses.branch'i ders kodu ile eslesmesi icin duzenliyoruz:")
print("  SCM567 => branch=NULL, code='SCM567' => ders.kod = 'SCM567'")  
print("  SCM8   => branch=NULL, code='SCM8'   => ders.kod = 'SCM8'")
print()
print("Ogretmenlerin allowed_courses'una eklenecek:")
print("  Ilk 3 ogretmene SCM567 yetkisi")
print("  Ilk 2 ogretmene SCM8 yetkisi")
print()

# Derslerin branch'ini NULL yap - boylece kod olarak kod kullanilir
cur.execute("UPDATE courses SET branch=NULL WHERE code='SCM567'")
cur.execute("UPDATE courses SET branch=NULL WHERE code='SCM8'")
print("Branch NULL yapildi.")

# Ogretmenlere yetki ekle
# id=1: ALI KOBAK (Din Kulturu) - SCM567 ve SCM8
# id=2: BAHAR DAL (Yabanci Dil) - SCM567
# id=3: BESTE TANRISEVER (Fen) - SCM567
# id=4: CANSU CETINKAL (Matematik) - SCM8

for tid in [1, 2, 3]:
    current_ac = cur.execute("SELECT allowed_courses FROM teachers WHERE id=?", (tid,)).fetchone()[0] or ""
    new_ac = current_ac + ",SCM567" if current_ac else "SCM567"
    # Sadece var olan ogretmenin adini alip goster
    tname = cur.execute("SELECT first_name, last_name FROM teachers WHERE id=?", (tid,)).fetchone()
    cur.execute("UPDATE teachers SET allowed_courses=? WHERE id=?", (new_ac, tid))
    print(f"  {tname[0]} {tname[1]} (id={tid}): allowed_courses -> {new_ac!r}")

for tid in [4, 5]:
    current_ac = cur.execute("SELECT allowed_courses FROM teachers WHERE id=?", (tid,)).fetchone()[0] or ""
    new_ac = current_ac + ",SCM8" if current_ac else "SCM8"
    tname = cur.execute("SELECT first_name, last_name FROM teachers WHERE id=?", (tid,)).fetchone()
    cur.execute("UPDATE teachers SET allowed_courses=? WHERE id=?", (new_ac, tid))
    print(f"  {tname[0]} {tname[1]} (id={tid}): allowed_courses -> {new_ac!r}")

conn.commit()
print()
print("Tamamlandi!")
print()

# Dogrulama: kod artik 'SCM567' olacak, ogretmen allowed_courses'unda 'SCM567' var
# solver_task.py _extract_branslar(teacher):
#   allowed = teacher.allowed_courses != 'ALL' => split by ',' => 'SCM567' liste icinde
#   => branslar = ['Din Kulturu...', 'SCM567']
# solver_task.py _extract_ders_kodu(course):
#   course.branch = None => course.code = 'SCM567'
# model_builder: uygun_ogretmen = o where 'SCM567' in o.branslar => ESLESME VAR!

print("=== Son kontrol: courses tablosu ===")
rows = cur.execute("SELECT id, name, code, branch FROM courses WHERE school_id=1 AND is_active=1 ORDER BY id").fetchall()
for r in rows:
    print(f"  id={r[0]}, name={r[1]!r}, code={r[2]!r}, branch={r[3]!r}")

conn.close()
