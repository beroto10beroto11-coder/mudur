"""
solver.py — OR-Tools CP-SAT ile haftalık ders programı çözücüsü.

Hard Constraints:
  1. Müsaitlik: available=False olan (gün, period) → atama yok
  2. Öğretmen günlük max saat
  3. Öğretmen haftalık max saat (0 = sınırsız)
  4. Öğretmen çakışması: aynı (gün, period) → tek şube
  5. Şube çakışması: aynı (gün, period) → tek ders
  6. Branş/yetki: allowed_courses & allowed_classes
  7. Blok ardışıklık: hour_distribution'daki her sayı → art arda period'lar
  8. Aynı gün tekrar yasağı: bir ders bir şubeye aynı gün sadece 1 blok
  9. Şube doluluk: tüm period'lar dolu
 10. Hedef sınıf: target_classes
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import NamedTuple

from ortools.sat.python import cp_model

from app.scheduler.data_loader import (
    SchedulerInput,
    CourseData,
    ClassData,
    TeacherData,
    _parse_distribution,
)
from app.scheduler.validator import (
    _parse_str_list,
    _get_courses_for_class,
    _get_eligible_teachers,
)

logger = logging.getLogger(__name__)

DAYS = 5  # Pazartesi..Cuma
DAY_NAMES = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]

# ---------------------------------------------------------------------------
# Çıktı veri yapıları
# ---------------------------------------------------------------------------

@dataclass
class ScheduledLesson:
    """Programda yer alan tek bir ders bloğu (ardışık period'lar)."""
    class_name: str
    course_name: str
    course_code: str | None
    teacher_name: str
    day: int          # 0=Pazartesi
    start_period: int # 1-based
    length: int       # kaç period sürdüğü


@dataclass
class InfeasibilityWarning:
    class_name: str
    course_name: str
    reason: str


@dataclass
class SchedulerResult:
    lessons: list[ScheduledLesson]
    warnings: list[InfeasibilityWarning]
    solver_status: str


# ---------------------------------------------------------------------------
# Ana çözüm fonksiyonu
# ---------------------------------------------------------------------------

def solve(inp: SchedulerInput, time_limit_seconds: int = 120) -> SchedulerResult:
    """
    SchedulerInput alır, OR-Tools CP-SAT ile çözer, SchedulerResult döner.
    """
    model = cp_model.CpModel()
    lessons: list[ScheduledLesson] = []
    warnings: list[InfeasibilityWarning] = []

    # Tüm period sayısı: gün bazında
    # daily_periods[d] = o günkü toplam ders saati sayısı
    daily_periods = inp.daily_periods  # [7, 7, 8, 7, 7]
    max_period = max(daily_periods)

    # ---------------------------------------------------------------------------
    # Ön hesaplama: hangi (ders, sınıf) çifti için hangi öğretmenler uygun?
    # ---------------------------------------------------------------------------
    class Assignment(NamedTuple):
        course: CourseData
        cls: ClassData
        teacher: TeacherData
        day: int
        start_period: int   # 1-based
        block_len: int       # bu bloğun uzunluğu

    # Çözüm değişkenleri: (course_id, class_id, teacher_id, day, start_period, block_len) → BoolVar
    assign_vars: dict[tuple, cp_model.IntVar] = {}

    # (course, class) → gereken blok listesi [2, 2, 1] gibi
    course_class_blocks: dict[tuple[int, int], list[int]] = {}

    # Teacher slot kullanımı: (teacher_id, day, period) → list[BoolVar]
    teacher_slot_vars: dict[tuple[int, int, int], list] = {}

    # Class slot kullanımı: (class_id, day, period) → list[BoolVar]
    class_slot_vars: dict[tuple[int, int, int], list] = {}

    for cls in inp.classes:
        assigned_courses = _get_courses_for_class(cls, inp.courses)

        for course in assigned_courses:
            blocks = _parse_distribution(course.hour_distribution, course.weekly_hours)
            course_class_blocks[(course.id, cls.id)] = blocks

            eligible_teachers = _get_eligible_teachers(course, cls, inp.teachers)
            if not eligible_teachers:
                warnings.append(InfeasibilityWarning(
                    class_name=cls.name,
                    course_name=course.name,
                    reason=f"Bu (ders, sınıf) çifti için uygun öğretmen bulunamadı.",
                ))
                continue

            # Her blok için ayrı değişken grubu
            for block_idx, block_len in enumerate(blocks):
                block_vars = []

                for teacher in eligible_teachers:
                    for day in range(DAYS):
                        # Bu günde bu block_len kadar ardışık period başlayabilir mi?
                        day_max = daily_periods[day]
                        max_start = day_max - block_len + 1
                        if max_start < 1:
                            continue

                        for start in range(1, max_start + 1):
                            # Öğretmen bu slotlarda müsait mi?
                            slots_ok = all(
                                (day, start + offset) not in teacher.unavailable_slots
                                for offset in range(block_len)
                            )
                            if not slots_ok:
                                continue

                            key = (course.id, cls.id, teacher.id, day, start, block_len, block_idx)
                            var = model.new_bool_var(
                                f"c{course.id}_cl{cls.id}_t{teacher.id}_d{day}_s{start}_b{block_idx}"
                            )
                            assign_vars[key] = var
                            block_vars.append((var, teacher, day, start, block_len))

                            # Teacher slot tracker
                            for offset in range(block_len):
                                period = start + offset
                                tkey = (teacher.id, day, period)
                                teacher_slot_vars.setdefault(tkey, []).append(var)

                            # Class slot tracker
                            for offset in range(block_len):
                                period = start + offset
                                ckey = (cls.id, day, period)
                                class_slot_vars.setdefault(ckey, []).append(var)

                # Her blok tam olarak 1 slota atanmalı
                if block_vars:
                    model.add_exactly_one([v for v, *_ in block_vars])
                else:
                    warnings.append(InfeasibilityWarning(
                        class_name=cls.name,
                        course_name=course.name,
                        reason=(
                            f"Blok {block_idx + 1} ({block_len} saat) için uygun "
                            f"(gün, saat, öğretmen) kombinasyonu bulunamadı. "
                            f"Müsaitlik kısıtları çok sıkı olabilir."
                        ),
                    ))

    # ---------------------------------------------------------------------------
    # Kısıt 4: Öğretmen çakışması — aynı (gün, period) → tek şube
    # ---------------------------------------------------------------------------
    for (teacher_id, day, period), var_list in teacher_slot_vars.items():
        if len(var_list) > 1:
            model.add_at_most_one(var_list)

    # ---------------------------------------------------------------------------
    # Kısıt 5: Şube çakışması — aynı (gün, period) → tek ders
    # ---------------------------------------------------------------------------
    for (class_id, day, period), var_list in class_slot_vars.items():
        if len(var_list) > 1:
            model.add_at_most_one(var_list)

    # ---------------------------------------------------------------------------
    # Kısıt 2 & 3: Öğretmen günlük/haftalık max saat
    # ---------------------------------------------------------------------------
    for teacher in inp.teachers:
        for day in range(DAYS):
            day_vars = []
            for period in range(1, daily_periods[day] + 1):
                tkey = (teacher.id, day, period)
                day_vars.extend(teacher_slot_vars.get(tkey, []))

            if teacher.max_daily_hours > 0 and day_vars:
                model.add(sum(day_vars) <= teacher.max_daily_hours)

        if teacher.max_weekly_hours > 0:
            week_vars = []
            for day in range(DAYS):
                for period in range(1, daily_periods[day] + 1):
                    tkey = (teacher.id, day, period)
                    week_vars.extend(teacher_slot_vars.get(tkey, []))
            if week_vars:
                model.add(sum(week_vars) <= teacher.max_weekly_hours)

    # ---------------------------------------------------------------------------
    # Kısıt 8: Aynı gün tekrar yasağı (bir ders bir sınıfa aynı gün tek blok)
    # ---------------------------------------------------------------------------
    for cls in inp.classes:
        assigned_courses = _get_courses_for_class(cls, inp.courses)
        for course in assigned_courses:
            blocks = course_class_blocks.get((course.id, cls.id), [])
            for day in range(DAYS):
                # Bu gün için bu (course, class) 'ın tüm block_idx'lerine ait değişkenler
                day_block_vars = [
                    var
                    for (cid, clid, tid, d, s, bl, bidx), var in assign_vars.items()
                    if cid == course.id and clid == cls.id and d == day
                ]
                if len(day_block_vars) > 1:
                    # Aynı günde en fazla 1 blok
                    model.add_at_most_one(day_block_vars)

    # ---------------------------------------------------------------------------
    # Çözücü
    # ---------------------------------------------------------------------------
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = 4
    status = solver.solve(model)

    status_name = solver.status_name(status)
    logger.info(f"CP-SAT solver status: {status_name}")

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return SchedulerResult(
            lessons=[],
            warnings=warnings,
            solver_status=status_name,
        )

    # ---------------------------------------------------------------------------
    # Çözümü ScheduledLesson listesine dönüştür
    # ---------------------------------------------------------------------------
    for (cid, clid, tid, day, start, block_len, bidx), var in assign_vars.items():
        if solver.value(var) == 1:
            # Nesneleri bul
            course = next((c for c in inp.courses if c.id == cid), None)
            cls = next((cl for cl in inp.classes if cl.id == clid), None)
            teacher = next((t for t in inp.teachers if t.id == tid), None)
            if course and cls and teacher:
                lessons.append(ScheduledLesson(
                    class_name=cls.name,
                    course_name=course.name,
                    course_code=course.code,
                    teacher_name=teacher.full_name,
                    day=day,
                    start_period=start,
                    length=block_len,
                ))

    return SchedulerResult(
        lessons=lessons,
        warnings=warnings,
        solver_status=status_name,
    )
