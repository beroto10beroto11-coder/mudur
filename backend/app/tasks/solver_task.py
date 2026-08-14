"""
Celery task for async OR-Tools Timetable solving with Redis progress reporting.

Bu modül DB'den veri çekip yeni scheduler (CP-SAT tabanlý) ile çizelge üretir
ve sonucu TimetableLesson kayýtlari olarak veritabanina yazar.
"""
import asyncio
import json
import re
from collections import defaultdict
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.core.redis import publish_progress
from app.models.course import Course
from app.models.assignment import CourseAssignment
from app.models.class_ import ClassGroup
from app.models.classroom import Classroom
from app.models.teacher import Teacher, TeacherAvailability
from app.models.timeslot import TimeSlot
from app.models.timetable import Timetable, TimetableLesson, TimetableStatus, TimetableVersion
from app.worker import celery_app

# Yeni scheduler modulu
from app.solver.scheduler import (
    ZamanYapisi,
    Sube,
    Ogretmen,
    Ders,
    SchedulerInput,
    run_scheduler,
)


# ---------------------------------------------------------------------------
# Yardimci: Course.hour_distribution string -> List[int]
# ---------------------------------------------------------------------------

def _parse_hour_distribution(
    hour_distribution: Optional[str],
    weekly_hours: int,
) -> list:
    """
    "2+2+2" -> [2, 2, 2]
    "2+2+1" -> [2, 2, 1]
    Parse edilemezse veya toplamı weekly_hours ile uyuşmazsa akıllı varsayılan bloklar döndürür.
    """
    if hour_distribution:
        options = [opt.strip() for opt in hour_distribution.split(",") if opt.strip()]
        for opt in options:
            parts = re.split(r"[+\s]+", opt)
            try:
                dist = [int(p) for p in parts if p]
                if dist and sum(dist) == weekly_hours and all(p > 0 for p in dist):
                    return dist
            except (ValueError, TypeError):
                pass

    if weekly_hours <= 0:
        return [1]
    twos = weekly_hours // 2
    ones = weekly_hours % 2
    res = [2] * twos
    if ones > 0:
        res.append(1)
    return res



# ---------------------------------------------------------------------------
# Yardimci: sinif adinden seviye
# ---------------------------------------------------------------------------

def _extract_sinif_seviyesi(class_name: str) -> int:
    m = re.match(r"(\d+)", class_name.strip())
    return int(m.group(1)) if m else 0


# ---------------------------------------------------------------------------
# Yardimci: ogretmen branslarini cikar
# ---------------------------------------------------------------------------

def _extract_branslar(teacher: Teacher) -> list:
    branslar = []
    if teacher.branch:
        branslar.append(teacher.branch.strip())
    allowed = teacher.allowed_courses or "ALL"
    if allowed != "ALL":
        for part in allowed.split(","):
            part = part.strip()
            if part and part not in branslar:
                branslar.append(part)
    if not branslar:
        branslar = ["GENEL"]
    return branslar


# ---------------------------------------------------------------------------
# Yardimci: ogretmenin girebilecegi subeler
# ---------------------------------------------------------------------------

def _extract_girebilecegi_subeler(teacher: Teacher, classes: list) -> list:
    allowed = teacher.allowed_classes or "ALL"
    if allowed == "ALL":
        return [str(cls.id) for cls in classes]
    allowed_names = {n.strip() for n in allowed.split(",")}
    return [str(cls.id) for cls in classes if cls.name in allowed_names]


# ---------------------------------------------------------------------------
# Yardimci: ders branski kodu
# ---------------------------------------------------------------------------

def _extract_ders_kodu(course: Course) -> str:
    if course.branch:
        return course.branch.strip()
    if course.code:
        return course.code.strip()
    return course.name[:4].upper() if course.name else "GENEL"


# ---------------------------------------------------------------------------
# DB modellerini SchedulerInput'a donustur
# ---------------------------------------------------------------------------

def _build_scheduler_input(
    teachers: list,
    classes: list,
    assignments: list,
    timeslots: list,
    availabilities: list,
    school_id: int,
) -> SchedulerInput:
    DAY_NAMES = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma"]

    # Zaman yapisi
    day_periods = defaultdict(set)
    for slot in timeslots:
        day_periods[slot.day].add(slot.period)

    max_day = max(day_periods.keys(), default=4)
    gunler = []
    gunluk_ders_saatleri = []
    for day_idx in range(max_day + 1):
        periods = day_periods.get(day_idx, set())
        gun_adi = DAY_NAMES[day_idx] if day_idx < len(DAY_NAMES) else f"Gun{day_idx + 1}"
        gunler.append(gun_adi)
        gunluk_ders_saatleri.append(max(periods) if periods else 0)

    if not gunler:
        gunler = DAY_NAMES
        gunluk_ders_saatleri = [7, 7, 7, 7, 7]

    zaman_yapisi = ZamanYapisi(
        gunler=gunler,
        gunluk_ders_saatleri=gunluk_ders_saatleri,
    )

    # Subeler
    subeler_list = []
    for cls in classes:
        seviye = _extract_sinif_seviyesi(cls.name)
        subeler_list.append(Sube(
            sube_id=str(cls.id),
            sinif_seviyesi=seviye,
            ad=cls.name,
        ))

    # Musaitlik haritasi
    avail_map = {}
    for t in teachers:
        avail_map[t.id] = {
            gun: [True] * maks
            for gun, maks in zip(gunler, gunluk_ders_saatleri)
        }

    for av in availabilities:
        if av.teacher_id not in avail_map:
            continue
        if not (0 <= av.day <= max_day):
            continue
        gun_adi = DAY_NAMES[av.day]
        if gun_adi not in avail_map[av.teacher_id]:
            continue
        period_idx = av.period - 1
        day_list = avail_map[av.teacher_id][gun_adi]
        if 0 <= period_idx < len(day_list):
            day_list[period_idx] = av.available

    course_to_subeler = defaultdict(set)
    for asgn in assignments:
        course_to_subeler[asgn.course_id].add(str(asgn.class_id))

    dersler_list = []
    seen_course_ids = set()
    # course_id -> ders.kod eslesmesi (ogretmen brans zenginlestirme icin)
    course_id_to_kod: dict[int, str] = {}

    for asgn in assignments:
        cid = asgn.course_id
        if cid in seen_course_ids:
            continue
        seen_course_ids.add(cid)

        course = asgn.course
        if course is None:
            continue

        gecerli_subeler = sorted(course_to_subeler[cid])
        weekly_hours = asgn.weekly_hours or (course.weekly_hours or 1)
        gunluk_dagilim = _parse_hour_distribution(course.hour_distribution, weekly_hours)
        kod = _extract_ders_kodu(course)
        course_id_to_kod[cid] = kod

        try:
            ders = Ders(
                ders_id=str(cid),
                ders_adi=course.name,
                kod=kod,
                gecerli_sube_ids=gecerli_subeler,
                haftalik_saat=weekly_hours,
                gunluk_dagilim=gunluk_dagilim,
            )
            dersler_list.append(ders)
        except Exception:
            try:
                ders = Ders(
                    ders_id=str(cid),
                    ders_adi=course.name,
                    kod=kod,
                    gecerli_sube_ids=gecerli_subeler,
                    haftalik_saat=weekly_hours,
                    gunluk_dagilim=[1] * weekly_hours,
                )
                dersler_list.append(ders)
            except Exception:
                pass

    # Ogretmen -> atanmis ders kodlari eslesmesi (assignments uzerinden)
    # Bu, _synthesize_assignments veya gercek CourseAssignment'lardan gelen
    # atama bilgisini solver'a tasir.
    teacher_assigned_kodlar: dict[int, set] = defaultdict(set)
    for asgn in assignments:
        if asgn.teacher_id and asgn.course_id in course_id_to_kod:
            teacher_assigned_kodlar[asgn.teacher_id].add(
                course_id_to_kod[asgn.course_id]
            )

    # Ogretmenler
    ogretmenler_list = []
    for t in teachers:
        branslar = _extract_branslar(t)
        # Atama bilgisinden gelen ders kodlarini da brans listesine ekle
        for kod in teacher_assigned_kodlar.get(t.id, set()):
            if kod not in branslar:
                branslar.append(kod)
        girebilecegi = _extract_girebilecegi_subeler(t, classes)
        ogretmenler_list.append(Ogretmen(
            ogretmen_id=str(t.id),
            ad=t.first_name,
            soyad=t.last_name,
            branslar=branslar,
            girebilecegi_subeler=girebilecegi,
            musaitlik=avail_map[t.id],
        ))

    return SchedulerInput(
        zaman_yapisi=zaman_yapisi,
        subeler=subeler_list,
        ogretmenler=ogretmenler_list,
        dersler=dersler_list,
        maks_cozum_suresi_saniye=120,
        paralel_isci_sayisi=None,
    )


# ---------------------------------------------------------------------------
# SchedulerResult -> TimetableLesson kayitlari
# ---------------------------------------------------------------------------

def _build_timetable_lessons(
    scheduler_result,
    timetable_id: int,
    classes: list,
    teachers: list,
    assignments: list,
    timeslots: list,
) -> list:
    DAY_NAMES = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma"]
    DAY_NAME_TO_IDX = {name: idx for idx, name in enumerate(DAY_NAMES)}

    teacher_id_map = {str(t.id): t.id for t in teachers}
    class_id_map = {str(cls.id): cls.id for cls in classes}

    asgn_lookup = {}
    for asgn in assignments:
        asgn_lookup[(asgn.course_id, asgn.class_id)] = asgn.id

    lessons = []

    for sube_program in scheduler_result.sube_programlari:
        sube_id_str = sube_program.sube_id
        class_db_id = class_id_map.get(sube_id_str)
        if class_db_id is None:
            continue

        for gun_adi, slots in sube_program.program.items():
            day_idx = DAY_NAME_TO_IDX.get(gun_adi)
            if day_idx is None:
                continue

            for slot in slots:
                course_db_id = int(slot.ders_id) if slot.ders_id else None
                teacher_db_id = teacher_id_map.get(slot.ogretmen_id)

                if course_db_id is None or teacher_db_id is None:
                    continue

                asgn_id = asgn_lookup.get((course_db_id, class_db_id))
                if asgn_id is None:
                    continue

                lessons.append({
                    "timetable_id": timetable_id,
                    "course_assignment_id": asgn_id,
                    "course_id": course_db_id,
                    "teacher_id": teacher_db_id,
                    "class_id": class_db_id,
                    "classroom_id": None,
                    "day": day_idx,
                    "period": slot.saat,
                    "is_fixed": False,
                })

    return lessons


# ---------------------------------------------------------------------------
# Dinamik assignment sentezi (CourseAssignment yoksa)
# ---------------------------------------------------------------------------

def _synthesize_assignments(
    courses: list,
    classes: list,
    teachers: list,
    school_id: int,
    academic_year_id: int,
) -> list:
    synthesized = []
    counter = 1000

    for cls in classes:
        for crs in courses:
            c_target = crs.target_classes or "ALL"
            if c_target != "ALL" and cls.name not in [x.strip() for x in c_target.split(",")]:
                continue

            candidates = []
            for t in teachers:
                t_c = t.allowed_courses or "ALL"
                t_cl = t.allowed_classes or "ALL"
                can_course = (
                    t_c == "ALL"
                    or crs.name in [x.strip() for x in t_c.split(",")]
                    or (t.branch and crs.branch and t.branch.lower() == crs.branch.lower())
                )
                can_class = t_cl == "ALL" or cls.name in [x.strip() for x in t_cl.split(",")]
                if can_course and can_class:
                    candidates.append(t)

            if not candidates:
                candidates = teachers

            chosen = candidates[0]
            mock = CourseAssignment(
                id=counter,
                school_id=school_id,
                academic_year_id=academic_year_id,
                course_id=crs.id,
                teacher_id=chosen.id,
                class_id=cls.id,
                weekly_hours=crs.weekly_hours,
                is_fixed=False,
            )
            mock.course = crs
            synthesized.append(mock)
            counter += 1

    return synthesized


# ---------------------------------------------------------------------------
# Ana solver yurutme fonksiyonu
# ---------------------------------------------------------------------------

async def _execute_solver(timetable_id: int, school_id: int, academic_year_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Timetable).where(Timetable.id == timetable_id))
        timetable = result.scalar_one_or_none()
        if not timetable:
            return

        timetable.status = TimetableStatus.GENERATING
        await session.commit()

        channel_name = f"solver_progress_{timetable_id}"

        async def _publish(data: dict):
            try:
                await publish_progress(channel_name, json.dumps(data))
            except Exception:
                pass

        await _publish({"percent": 5, "message": "Veriler yukleniyor..."})

        # Verileri yukle
        teachers_res = await session.execute(
            select(Teacher).where(Teacher.school_id == school_id, Teacher.is_active == True)
        )
        teachers = list(teachers_res.scalars().all())

        classes_res = await session.execute(
            select(ClassGroup).where(ClassGroup.school_id == school_id, ClassGroup.is_active == True)
        )
        classes = list(classes_res.scalars().all())

        asgns_res = await session.execute(
            select(CourseAssignment)
            .options(selectinload(CourseAssignment.course))
            .where(
                CourseAssignment.school_id == school_id,
                CourseAssignment.academic_year_id == academic_year_id,
                CourseAssignment.is_active == True,
            )
        )
        assignments = list(asgns_res.scalars().all())

        if not assignments:
            courses_res = await session.execute(
                select(Course).where(Course.school_id == school_id, Course.is_active == True)
            )
            courses = list(courses_res.scalars().all())
            assignments = _synthesize_assignments(courses, classes, teachers, school_id, academic_year_id)

        slots_res = await session.execute(
            select(TimeSlot).where(
                TimeSlot.academic_year_id == academic_year_id,
                TimeSlot.is_active == True,
            )
        )
        timeslots = list(slots_res.scalars().all())

        avail_res = await session.execute(
            select(TeacherAvailability).where(TeacherAvailability.academic_year_id == academic_year_id)
        )
        availabilities = list(avail_res.scalars().all())

        await _publish({"percent": 15, "message": "CP-SAT modeli olusturuluyor..."})

        try:
            scheduler_input = _build_scheduler_input(
                teachers=teachers,
                classes=classes,
                assignments=assignments,
                timeslots=timeslots,
                availabilities=availabilities,
                school_id=school_id,
            )
        except Exception as e:
            timetable.status = TimetableStatus.FAILED
            timetable.solver_conflicts = {"error": f"Girdi olusturulamadi: {str(e)}"}
            await session.commit()
            await _publish({"percent": 100, "status": "FAILED", "success": False})
            return

        await _publish({"percent": 25, "message": "Solver calistiriliyor..."})

        loop = asyncio.get_running_loop()
        solver_result = await loop.run_in_executor(None, run_scheduler, scheduler_input)

        await _publish({"percent": 85, "message": "Sonuclar isleniyor..."})

        if solver_result.basarili:
            from sqlalchemy import delete as sa_delete
            await session.execute(
                sa_delete(TimetableLesson).where(TimetableLesson.timetable_id == timetable_id)
            )

            lessons_data = _build_timetable_lessons(
                scheduler_result=solver_result,
                timetable_id=timetable_id,
                classes=classes,
                teachers=teachers,
                assignments=assignments,
                timeslots=timeslots,
            )

            new_lessons = [TimetableLesson(**item) for item in lessons_data]
            session.add_all(new_lessons)

            timetable.status = TimetableStatus.GENERATED
            timetable.solver_duration_seconds = solver_result.sure_saniye
            timetable.solver_objective_value = solver_result.hedef_deger
            timetable.solver_conflicts = None

            version_snapshot = TimetableVersion(
                timetable_id=timetable_id,
                version_number=1,
                description=f"CP-SAT solver -- {solver_result.durum}",
                change_summary=(
                    f"{len(new_lessons)} ders basariyla yerlestirildi. "
                    f"Sure: {solver_result.sure_saniye:.1f}s"
                ),
                lessons_snapshot=lessons_data,
            )
            session.add(version_snapshot)

            if solver_result.ihlaller:
                timetable.solver_conflicts = {
                    "warnings": [
                        {"tur": ih.tur, "mesaj": ih.mesaj}
                        for ih in solver_result.ihlaller
                    ]
                }
        else:
            timetable.status = TimetableStatus.FAILED
            timetable.solver_duration_seconds = solver_result.sure_saniye
            timetable.solver_conflicts = {
                "ihlaller": [
                    {"tur": ih.tur, "mesaj": ih.mesaj, "detay": ih.detay}
                    for ih in solver_result.ihlaller
                ],
                "teshis": solver_result.teshis_mesajlari,
            }

        await session.commit()
        await _publish({
            "percent": 100,
            "status": timetable.status.value,
            "success": solver_result.basarili,
            "durum": solver_result.durum,
            "sure_saniye": solver_result.sure_saniye,
        })


# ---------------------------------------------------------------------------
# Celery task
# ---------------------------------------------------------------------------

@celery_app.task(name="app.tasks.solver_task.run_solver")
def run_solver(timetable_id: int, school_id: int, academic_year_id: int):
    asyncio.run(_execute_solver(timetable_id, school_id, academic_year_id))
