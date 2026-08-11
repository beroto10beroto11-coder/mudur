# Progmatic Benzeri Okul Ders Programı Sistemi — Teknik Mimari

## 1. Amaç

Bu doküman, Progmatic'in temel işlevlerini modern, web tabanlı, ölçeklenebilir ve geliştirilebilir bir mimariyle yeniden oluşturmak için hazırlanmıştır.

Ana hedefler:

- Ders programı oluşturma
- Otomatik ders dağıtımı
- Öğretmen yönetimi
- Sınıf yönetimi
- Derslik yönetimi
- Öğretmen müsaitlikleri
- Seçmeli dersler
- Nöbet sistemi
- Manuel program düzenleme
- Excel/PDF aktarımı
- Yedekleme
- Program versiyonlama
- Çoklu okul desteği
- Kullanıcı/rol yönetimi
- Çakışma ve hata analizi

---

# 2. Teknoloji Stack

```text
Frontend
├── Next.js
├── TypeScript
├── TailwindCSS
├── shadcn/ui
├── React Query
└── Zustand

Backend
├── Python
├── FastAPI
├── SQLAlchemy
├── Pydantic
└── OR-Tools CP-SAT

Database
└── PostgreSQL

Queue / Cache
├── Redis
└── Celery

Dosya
├── Excel → openpyxl / pandas
├── PDF → WeasyPrint
└── CSV → pandas

Auth
├── JWT
└── Argon2

Deployment
├── Docker
├── Traefik / Nginx
└── Coolify

Desktop
└── Tauri
```

---

# 3. Proje Klasör Yapısı

```text
school-scheduler/
│
├── frontend/
│   ├── app/
│   │   ├── login/
│   │   ├── dashboard/
│   │   ├── courses/
│   │   ├── classes/
│   │   ├── teachers/
│   │   ├── classrooms/
│   │   ├── assignments/
│   │   ├── timetable/
│   │   ├── teacher-schedules/
│   │   ├── class-schedules/
│   │   ├── classroom-schedules/
│   │   ├── availability/
│   │   ├── duties/
│   │   ├── electives/
│   │   ├── announcements/
│   │   ├── reports/
│   │   ├── backup/
│   │   └── settings/
│   │
│   ├── components/
│   ├── hooks/
│   ├── lib/
│   ├── stores/
│   └── types/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── auth.py
│   │   │   ├── schools.py
│   │   │   ├── courses.py
│   │   │   ├── classes.py
│   │   │   ├── teachers.py
│   │   │   ├── classrooms.py
│   │   │   ├── assignments.py
│   │   │   ├── timetables.py
│   │   │   ├── duties.py
│   │   │   ├── electives.py
│   │   │   ├── reports.py
│   │   │   ├── imports.py
│   │   │   └── backups.py
│   │   │
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── solver/
│   │   ├── imports/
│   │   ├── exports/
│   │   ├── auth/
│   │   └── core/
│   │
│   ├── tests/
│   └── requirements.txt
│
├── docker/
├── scripts/
├── docker-compose.yml
└── README.md
```

---

# 4. Veritabanı Mimarisi

```text
School
 │
 ├── AcademicYear
 │
 ├── Grade
 │    └── Class
 │
 ├── Teacher
 │
 ├── Course
 │
 ├── Classroom
 │
 ├── CourseAssignment
 │
 ├── TeacherAvailability
 │
 ├── Timetable
 │    └── LessonSlot
 │
 ├── Duty
 │
 ├── ElectiveCourse
 │
 ├── Announcement
 │
 └── Backup
```

---

# 5. School / Academic Year

```python
from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

class School(Base):
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    city: Mapped[str | None] = mapped_column(String(100))
    district: Mapped[str | None] = mapped_column(String(100))

    academic_years = relationship(
        "AcademicYear",
        back_populates="school",
        cascade="all, delete-orphan"
    )


class AcademicYear(Base):
    __tablename__ = "academic_years"

    id: Mapped[int] = mapped_column(primary_key=True)

    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id")
    )

    name: Mapped[str] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    school = relationship(
        "School",
        back_populates="academic_years"
    )
```

---

# 6. Ders Modeli

```python
class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)

    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id")
    )

    name: Mapped[str] = mapped_column(String(150))

    weekly_hours: Mapped[int] = mapped_column(
        Integer,
        default=1
    )

    is_elective: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    requires_classroom: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    consecutive_hours: Mapped[int] = mapped_column(
        Integer,
        default=1
    )
```

---

# 7. Sınıf Modeli

```python
class ClassRoomGroup(Base):
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(primary_key=True)

    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id")
    )

    name: Mapped[str] = mapped_column(String(50))

    grade: Mapped[int] = mapped_column(Integer)

    section: Mapped[str] = mapped_column(String(10))

    student_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )
```

Örnek:

```text
9/A
9/B
9/C
10/A
10/B
11/A
12/A
```

---

# 8. Öğretmen Modeli

```python
class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(primary_key=True)

    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id")
    )

    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))

    branch: Mapped[str | None] = mapped_column(
        String(100)
    )

    max_daily_hours: Mapped[int] = mapped_column(
        Integer,
        default=8
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
```

---

# 9. Derslik Modeli

```python
class Classroom(Base):
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(primary_key=True)

    school_id: Mapped[int] = mapped_column(
        ForeignKey("schools.id")
    )

    name: Mapped[str] = mapped_column(String(100))

    capacity: Mapped[int] = mapped_column(
        Integer,
        default=30
    )

    room_type: Mapped[str | None] = mapped_column(
        String(50)
    )
```

Örnek:

```text
101
102
Bilişim Laboratuvarı
Fen Laboratuvarı
Spor Salonu
Müzik Odası
```

---

# 10. Ders Ataması

Sistemin temel ilişkisi:

```text
Matematik
   ↓
Ahmet Öğretmen
   ↓
9/A
   ↓
101
   ↓
haftada 5 saat
```

Model:

```python
class CourseAssignment(Base):
    __tablename__ = "course_assignments"

    id: Mapped[int] = mapped_column(primary_key=True)

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id")
    )

    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id")
    )

    class_id: Mapped[int] = mapped_column(
        ForeignKey("classes.id")
    )

    classroom_id: Mapped[int | None] = mapped_column(
        ForeignKey("classrooms.id"),
        nullable=True
    )

    weekly_hours: Mapped[int] = mapped_column(Integer)

    priority: Mapped[int] = mapped_column(
        Integer,
        default=1
    )
```

---

# 11. Öğretmen Müsaitlik Sistemi

```python
class TeacherAvailability(Base):
    __tablename__ = "teacher_availability"

    id: Mapped[int] = mapped_column(primary_key=True)

    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id")
    )

    day: Mapped[int] = mapped_column(Integer)

    period: Mapped[int] = mapped_column(Integer)

    available: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
```

Örnek:

```text
Ahmet
Pazartesi
1. ders → ❌

Ahmet
Pazartesi
2. ders → ❌

Ahmet
Salı
1. ders → ✅
```

---

# 12. Zaman Modeli

```python
class TimeSlot(Base):
    __tablename__ = "time_slots"

    id: Mapped[int] = mapped_column(primary_key=True)

    day: Mapped[int] = mapped_column(Integer)

    period: Mapped[int] = mapped_column(Integer)

    start_time: Mapped[str] = mapped_column(String(5))

    end_time: Mapped[str] = mapped_column(String(5))
```

Örnek:

```text
Pazartesi
1 → 08:30 - 09:10
2 → 09:20 - 10:00
3 → 10:10 - 10:50
```

---

# 13. Ders Programı Solver Mimarisi

En kritik bölüm **OR-Tools CP-SAT Constraint Solver** olacaktır.

```text
Assignments
      │
      ▼
Constraint Builder
      │
      ▼
CP-SAT Solver
      │
      ├── Teacher constraints
      ├── Class constraints
      ├── Classroom constraints
      ├── Availability
      ├── Daily limits
      ├── Consecutive lessons
      ├── Fixed lessons
      ├── Electives
      └── Optimization
      │
      ▼
Generated Timetable
```

---

# 14. Solver İskeleti

```python
from ortools.sat.python import cp_model


class TimetableSolver:

    def __init__(
        self,
        assignments,
        teachers,
        classes,
        classrooms,
        timeslots
    ):
        self.model = cp_model.CpModel()

        self.assignments = assignments
        self.teachers = teachers
        self.classes = classes
        self.classrooms = classrooms
        self.timeslots = timeslots

        self.variables = {}

    def create_variables(self):

        for assignment in self.assignments:

            for slot in self.timeslots:

                key = (
                    assignment.id,
                    slot.id
                )

                self.variables[key] = (
                    self.model.NewBoolVar(
                        f"x_{assignment.id}_{slot.id}"
                    )
                )

    def add_assignment_constraints(self):

        for assignment in self.assignments:

            vars_ = [
                var
                for (assignment_id, slot_id), var
                in self.variables.items()
                if assignment_id == assignment.id
            ]

            self.model.Add(
                sum(vars_) == assignment.weekly_hours
            )

    def solve(self):

        self.create_variables()

        self.add_assignment_constraints()

        solver = cp_model.CpSolver()

        solver.parameters.max_time_in_seconds = 60

        status = solver.Solve(self.model)

        if status in (
            cp_model.OPTIMAL,
            cp_model.FEASIBLE
        ):
            return self.build_result(solver)

        return None
```

---

# 15. Öğretmen Çakışması

```python
def add_teacher_conflicts(self):

    for teacher in self.teachers:

        for slot in self.timeslots:

            vars_ = []

            for assignment in self.assignments:

                if assignment.teacher_id != teacher.id:
                    continue

                var = self.variables.get(
                    (assignment.id, slot.id)
                )

                if var:
                    vars_.append(var)

            if vars_:
                self.model.Add(
                    sum(vars_) <= 1
                )
```

Aynı öğretmen aynı anda iki derste olamaz.

---

# 16. Sınıf Çakışması

```python
def add_class_conflicts(self):

    for class_ in self.classes:

        for slot in self.timeslots:

            vars_ = []

            for assignment in self.assignments:

                if assignment.class_id != class_.id:
                    continue

                var = self.variables.get(
                    (assignment.id, slot.id)
                )

                if var:
                    vars_.append(var)

            if vars_:
                self.model.Add(
                    sum(vars_) <= 1
                )
```

---

# 17. Derslik Çakışması

```python
def add_classroom_conflicts(self):

    for room in self.classrooms:

        for slot in self.timeslots:

            vars_ = []

            for assignment in self.assignments:

                if assignment.classroom_id != room.id:
                    continue

                var = self.variables.get(
                    (assignment.id, slot.id)
                )

                if var:
                    vars_.append(var)

            if vars_:
                self.model.Add(
                    sum(vars_) <= 1
                )
```

---

# 18. Öğretmen Kapalı Saatleri

```python
def add_teacher_availability(
    self,
    availability
):

    for item in availability:

        if item.available:
            continue

        for assignment in self.assignments:

            if assignment.teacher_id != item.teacher_id:
                continue

            slot = self.find_slot(
                item.day,
                item.period
            )

            var = self.variables.get(
                (assignment.id, slot.id)
            )

            if var:
                self.model.Add(var == 0)
```

---

# 19. Günlük Maksimum Ders

```python
def add_daily_teacher_limit(self):

    for teacher in self.teachers:

        for day in range(5):

            vars_ = []

            for assignment in self.assignments:

                if assignment.teacher_id != teacher.id:
                    continue

                for slot in self.timeslots:

                    if slot.day != day:
                        continue

                    var = self.variables.get(
                        (assignment.id, slot.id)
                    )

                    if var:
                        vars_.append(var)

            self.model.Add(
                sum(vars_) <= teacher.max_daily_hours
            )
```

---

# 20. Sabit Dersler

```python
def fix_lesson(
    self,
    assignment_id,
    slot_id
):

    var = self.variables[
        (assignment_id, slot_id)
    ]

    self.model.Add(var == 1)
```

Örneğin:

```text
9/A
Matematik
Çarşamba
3. ders
```

sabitlenebilir.

---

# 21. Ders Programı API

```python
@router.post("/timetables/generate")
async def generate_timetable(
    school_id: int,
    academic_year_id: int
):

    data = await timetable_service.load_data(
        school_id,
        academic_year_id
    )

    solver = TimetableSolver(
        assignments=data.assignments,
        teachers=data.teachers,
        classes=data.classes,
        classrooms=data.classrooms,
        timeslots=data.timeslots
    )

    result = solver.solve()

    if not result:
        raise HTTPException(
            422,
            "Geçerli bir ders programı oluşturulamadı."
        )

    await timetable_service.save(result)

    return {
        "success": True,
        "timetable_id": result.id
    }
```

---

# 22. Solver Hata Analizi

Program çözülemezse sadece hata vermek yerine sebebi açıklanmalı.

```json
{
  "success": false,
  "reason": "INFEASIBLE",
  "conflicts": [
    {
      "type": "TEACHER_AVAILABILITY",
      "teacher": "Ahmet Yılmaz",
      "message": "Ahmet Yılmaz'ın yalnızca 12 uygun saati var."
    },
    {
      "type": "CLASSROOM",
      "room": "Bilişim Laboratuvarı",
      "message": "Aynı saat için 3 ders bu dersliği istiyor."
    }
  ]
}
```

Frontend:

```text
❌ Program oluşturulamadı

2 problem bulundu:

1. Ahmet Yılmaz'ın müsaitliği yetersiz.
2. Bilişim Laboratuvarı aynı saatte 3 derse atanmış.

[Problemleri Göster]
```

---

# 23. Manuel Program Düzenleme

Modern bir Drag & Drop grid:

```text
             Pzt   Sal   Çar   Per   Cum
------------------------------------------------
1. Ders      MAT   FİZ   MAT   TAR   İNG
2. Ders      MAT   FİZ   BİL   TAR   İNG
3. Ders      TÜR   KİM   BİL   MAT   BED
4. Ders      TAR   KİM   İNG   MAT   BED
5. Ders      FİZ   MAT   TÜR   KİM   MÜZ
6. Ders      FİZ   MAT   TÜR   KİM   MÜZ
```

API:

```http
PATCH /api/timetables/{id}/lessons/{lesson_id}
```

```json
{
  "day": 2,
  "period": 3
}
```

Değişiklik sonrası:

```text
validate_timetable()
        ↓
Teacher conflict?
Class conflict?
Room conflict?
Availability?
Daily limit?
        ↓
OK / ERROR
```

---

# 24. Nöbet Sistemi

```python
class Duty(Base):
    __tablename__ = "duties"

    id: Mapped[int] = mapped_column(primary_key=True)

    teacher_id: Mapped[int] = mapped_column(
        ForeignKey("teachers.id")
    )

    day: Mapped[int] = mapped_column(Integer)

    location: Mapped[str] = mapped_column(
        String(150)
    )

    automatic: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )
```

Dağıtım:

```text
Öğretmenler
     ↓
Uygunluk
     ↓
Ders yükü
     ↓
Nöbet geçmişi
     ↓
Dengeli dağıtım
     ↓
Nöbet programı
```

---

# 25. Seçmeli Ders Sistemi

```text
electives/
├── courses
├── students
├── choices
├── groups
├── teachers
├── classrooms
└── scheduler
```

Örnek:

```text
360 öğrenci
      ↓
öğrenci tercihleri
      ↓
gruplandırma
      ↓
minimum grup sayısı
      ↓
öğretmen
      ↓
derslik
      ↓
zaman
      ↓
program
```

---

# 26. Excel Import

```text
Excel
 ↓
Schema validation
 ↓
Duplicate detection
 ↓
Data normalization
 ↓
Preview
 ↓
User approval
 ↓
Database
```

Örnek:

```python
import pandas as pd


def import_teachers(file):

    df = pd.read_excel(file)

    required = [
        "Ad",
        "Soyad",
        "Branş"
    ]

    missing = [
        x for x in required
        if x not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Eksik kolonlar: {missing}"
        )

    return df.to_dict("records")
```

---

# 27. Excel Export

```text
exports/
├── teacher_schedule.py
├── class_schedule.py
├── classroom_schedule.py
├── duty_schedule.py
└── full_school.py
```

Çıktılar:

```text
Öğretmen Programları.xlsx
Sınıf Programları.xlsx
Derslik Programları.xlsx
Nöbet Çizelgesi.xlsx
Okul Genel Programı.xlsx
```

---

# 28. PDF Sistemi

```text
reports/
├── teacher_schedule.html
├── class_schedule.html
├── classroom_schedule.html
└── duty_schedule.html
```

```python
from weasyprint import HTML

HTML(
    string=html
).write_pdf(
    "teacher_schedule.pdf"
)
```

---

# 29. Frontend Sayfa Yapısı

```text
/dashboard
/courses
/classes
/teachers
/classrooms
/assignments
/timetable
/teacher-schedules
/class-schedules
/classroom-schedules
/availability
/duties
/electives
/reports
/backup
/settings
```

Dashboard:

```text
┌──────────────────────────────────────────────┐
│ Okul Yönetim Sistemi                         │
├──────────────┬───────────────────────────────┤
│ Dashboard    │ 2026-2027 Eğitim Öğretim     │
│              │                               │
│ Dersler      │ 👨‍🏫 54 Öğretmen               │
│ Sınıflar     │ 🏫 32 Sınıf                    │
│ Öğretmenler  │ 📚 48 Ders                    │
│ Derslikler   │ 🏠 24 Derslik                 │
│              │                               │
│ Ders Atama   │ ⚠ 3 Problem                   │
│ Program      │                               │
│ Nöbet        │                               │
│ Seçmeliler   │                               │
│ Raporlar     │                               │
│ Ayarlar      │                               │
└──────────────┴───────────────────────────────┘
```

---

# 30. Filtreleme

```text
Programı göster:

[ Öğretmen ▼ ]
    Ahmet Yılmaz

[ Sınıf ▼ ]
    9/A

[ Derslik ▼ ]
    101

[ Branş ▼ ]
    Matematik
```

Backend:

```http
GET /api/timetables/{id}
    ?teacher_id=12
    &class_id=4
    &classroom_id=8
```

---

# 31. Program Versiyonlama

```text
Program
│
├── Version 1
├── Version 2
├── Version 3
└── Current
```

Örnek:

```text
2026-08-09 13:20
Program oluşturuldu

2026-08-09 13:35
Ahmet Yılmaz değiştirildi

2026-08-09 13:42
9/A Matematik değiştirildi
```

Geri alma:

```http
POST /api/timetables/versions/12/restore
```

---

# 32. Otomatik Yedekleme

```text
PostgreSQL
     ↓
pg_dump
     ↓
/backups
     ↓
2026-08-09_13-00.sql
```

Arayüz:

```text
[ Manuel Yedek Al ]

[ Son Yedeği Geri Yükle ]

[ Otomatik Yedekleme ]
    Her gün 03:00
```

---

# 33. Audit Log

Her değişiklik kayıt altına alınmalı.

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int]

    action: Mapped[str]

    entity: Mapped[str]

    entity_id: Mapped[int]

    old_data: Mapped[dict | None]

    new_data: Mapped[dict | None]
```

Örnek:

```text
Berat
09.08.2026 13:42

9/A Matematik
Pazartesi 3 → Çarşamba 4
```

---

# 34. Multi-School

Sistem tek okul ile sınırlı olmamalı.

```text
Platform
│
├── School A
│   ├── 2025-2026
│   └── 2026-2027
│
├── School B
│   └── 2026-2027
│
└── School C
    └── 2026-2027
```

Temel tablolarda:

```text
school_id
```

bulunmalı.

---

# 35. Kullanıcı Rolleri

```text
SUPER_ADMIN
SCHOOL_ADMIN
VICE_PRINCIPAL
TEACHER
VIEWER
```

Yetkiler:

```text
SUPER_ADMIN
    ↓
her şey

SCHOOL_ADMIN
    ↓
okul yönetimi

VICE_PRINCIPAL
    ↓
ders programı
öğretmen
sınıf
nöbet

TEACHER
    ↓
kendi programı

VIEWER
    ↓
sadece görüntüleme
```

---

# 36. Docker

```yaml
services:

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"

  backend:
    build: ./backend
    ports:
      - "8000:8000"

  postgres:
    image: postgres:17
    environment:
      POSTGRES_DB: school
      POSTGRES_USER: school
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7

  worker:
    build: ./backend
    command: celery -A app.worker worker -l info

volumes:
  postgres_data:
```

---

# 37. Uzun Süren Solver İşlemi

Solver HTTP request içinde çalıştırılmamalı.

```text
Frontend
   │
   │ POST /generate
   ▼
FastAPI
   │
   ▼
Redis Queue
   │
   ▼
Celery Worker
   │
   ▼
OR-Tools
   │
   ▼
PostgreSQL
   │
   ▼
WebSocket
   │
   ▼
Frontend
```

Frontend:

```text
Program oluşturuluyor...

██████████████░░░░ 72%

1428 constraint
284 assignment
32 class
54 teacher

[İptal]
```

---

# 38. Solver Optimizasyonu

Amaç sadece geçerli program üretmek değil, kaliteli program üretmek.

```text
MINIMIZE

teacher_gaps
+ class_gaps
+ classroom_gaps
+ unwanted_periods
+ uneven_daily_load
+ consecutive_penalties
+ late_lessons
```

Örnek:

```python
self.model.Minimize(
    sum(
        teacher_gap_penalties
        + class_gap_penalties
        + unwanted_slot_penalties
    )
)
```

Böylece daha dengeli program seçilir.

---

# 39. Constraint Öncelikleri

```python
class ConstraintPriority:

    HARD = 1000000

    IMPORTANT = 10000

    NORMAL = 100

    SOFT = 1
```

## HARD

```text
Öğretmen aynı anda iki ders
Sınıf aynı anda iki ders
Derslik aynı anda iki ders
Kapalı saat
```

## SOFT

```text
Öğretmenin boşlukları
İlk ders istememe
Son ders istememe
Günlük yük dengesi
```

---

# 40. Modül Karşılıkları

| Progmatic | Yeni Sistem |
|---|---|
| Dersler | `CourseService` |
| Sınıflar | `ClassService` |
| Derslikler | `ClassroomService` |
| Öğretmenler | `TeacherService` |
| Günlük ders sayıları | `ScheduleConfig` |
| Sınıflarda okutulan dersler | `CourseAssignment` |
| Öğretmen ders ataması | `CourseAssignment` |
| Öğretmen programları | `TimetableQueryService` |
| Yazdırma | `ReportService` |
| Nöbetler | `DutyService` |
| Bilgi panosu | `AnnouncementService` |
| Yedekleme | `BackupService` |
| Programlar | `TimetableService` |
| Dosya bakımı | `MaintenanceService` |
| Ayarlar | `SettingsService` |
| Lisans | `LicenseService` |
| Destek | `SupportService` |

---

# 41. API Mimarisi

```text
/api
│
├── /auth
│   ├── login
│   ├── refresh
│   └── logout
│
├── /schools
├── /academic-years
├── /teachers
├── /classes
├── /courses
├── /classrooms
├── /assignments
├── /availability
│
├── /timetables
│   ├── generate
│   ├── validate
│   ├── publish
│   ├── versions
│   └── lessons
│
├── /duties
├── /electives
├── /imports
├── /exports
├── /reports
└── /backups
```

---

# 42. Service Mimarisi

```text
API
 │
 ▼
Service Layer
 │
 ├── SchoolService
 ├── TeacherService
 ├── CourseService
 ├── ClassService
 ├── ClassroomService
 ├── AssignmentService
 │
 ├── TimetableService
 │       │
 │       └── SolverService
 │
 ├── DutyService
 ├── ElectiveService
 ├── ImportService
 ├── ExportService
 └── BackupService
```

---

# 43. Repository Katmanı

```python
class TeacherRepository:

    async def get_all(
        self,
        school_id: int
    ):
        ...

    async def get_by_id(
        self,
        teacher_id: int
    ):
        ...

    async def create(
        self,
        teacher
    ):
        ...

    async def update(
        self,
        teacher_id,
        data
    ):
        ...

    async def delete(
        self,
        teacher_id
    ):
        ...
```

Service:

```python
class TeacherService:

    def __init__(
        self,
        repository
    ):
        self.repository = repository

    async def create_teacher(
        self,
        data
    ):

        self.validate(data)

        return await self.repository.create(
            data
        )
```

---

# 44. Ana Sistem Mimarisi

```text
                    SCHOOL SCHEDULER
                           │
          ┌────────────────┴────────────────┐
          │                                 │
      WEB CLIENT                       DESKTOP CLIENT
      Next.js                           Tauri
          │                                 │
          └──────────────┬──────────────────┘
                         │
                       API
                         │
                    FastAPI
                         │
       ┌─────────────────┼──────────────────┐
       │                 │                  │
   PostgreSQL          Redis             Storage
       │                 │
       │              Celery
       │                 │
       │             OR-Tools
       │                 │
       └──────── Timetable Engine ─────────┘
                         │
                 Validation Engine
                         │
                  Reporting Engine
                         │
             ┌───────────┼───────────┐
             │           │           │
           Excel        PDF        Print
```

---

# 45. Geliştirme Fazları

## Phase 1 — Temel Sistem

```text
PostgreSQL
FastAPI
Auth
School
Teacher
Class
Course
Classroom
```

## Phase 2 — Program Altyapısı

```text
CourseAssignment
Availability
TimeSlot
Manual Timetable
```

## Phase 3 — Solver

```text
OR-Tools
Hard Constraints
Soft Constraints
Optimization
Conflict Detection
```

## Phase 4 — Arayüz

```text
Drag & Drop
Teacher Schedule
Class Schedule
Classroom Schedule
Printable Views
```

## Phase 5 — Dosya İşlemleri

```text
Excel Import
Excel Export
PDF
Backup
```

## Phase 6 — İleri Modüller

```text
Duty System
Elective System
Student Management
Automatic Grouping
```

## Phase 7 — Enterprise

```text
Versioning
Audit Logs
Notifications
WebSocket
Advanced Solver
```

## Phase 8 — SaaS

```text
Multi-school
License
Subscription
Admin Panel
```

---

# 46. Önerilen Nihai Mimari

```text
                    SCHOOL SCHEDULER
                           │
                    ┌──────▼──────┐
                    │   Next.js   │
                    │  Frontend   │
                    └──────┬──────┘
                           │
                     REST / WebSocket
                           │
                    ┌──────▼──────┐
                    │   FastAPI   │
                    │ API Layer   │
                    └──────┬──────┘
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
     PostgreSQL          Redis            Storage
          │                │
          │             Celery
          │                │
          │           ┌────▼────┐
          │           │OR-Tools │
          │           │ Solver  │
          │           └────┬────┘
          │                │
          └────────┬───────┘
                   ▼
           Timetable Engine
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   Validation   Reports    Export
        │          │          │
        ▼          ▼          ▼
      Excel       PDF       Print
```

---

# 47. Kritik Tasarım Kararları

1. Ders programı algoritması klasik if/else yapısında değil, Constraint Programming ile kurulmalı.
2. Hard constraint ve soft constraint ayrımı yapılmalı.
3. Solver ayrı bir servis/worker olarak çalışmalı.
4. Manuel değişiklik sonrası program yeniden validate edilmeli.
5. Program versiyonları saklanmalı.
6. Her önemli kullanıcı işlemi AuditLog'a yazılmalı.
7. Excel import işleminden önce validation + preview yapılmalı.
8. Çoklu okul desteği baştan veri modeline eklenmeli.
9. Solver'ın sadece "çözülemedi" demesi yerine conflict explanation üretmesi sağlanmalı.
10. Frontend ve backend birbirinden bağımsız geliştirilmeli.
11. PostgreSQL ana veri kaynağı olmalı.
12. Redis + Celery uzun süren işlemler için kullanılmalı.
13. Docker ile tüm servisler containerize edilmeli.
14. Tauri opsiyonel desktop client olarak kullanılabilir.

---

# 48. Sonuç

Bu mimariyle Progmatic'in temel işlevleri tek bir modern sistem içerisinde yeniden oluşturulabilir.

En önemli üç katman:

```text
1. DATA LAYER
   PostgreSQL

2. BUSINESS LAYER
   FastAPI + Services

3. SCHEDULING ENGINE
   OR-Tools CP-SAT
```

Bunların üzerine:

```text
Next.js
Excel
PDF
Backup
Reports
Authentication
Roles
Audit
Versioning
WebSocket
```

eklenerek tam kapsamlı bir okul ders programı SaaS/desktop sistemi oluşturulabilir.
