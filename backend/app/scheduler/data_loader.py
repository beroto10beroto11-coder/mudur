"""
data_loader.py — Veritabanından scheduler için gerekli tüm veriyi çeker.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Veri sınıfları
# ---------------------------------------------------------------------------

@dataclass
class TeacherData:
    id: int
    full_name: str
    branch: str | None
    max_daily_hours: int
    max_weekly_hours: int          # 0 = sınırsız
    allowed_courses: str           # "ALL" veya virgülle ayrılmış ders adları
    allowed_classes: str           # "ALL" veya virgülle ayrılmış sınıf adları
    unavailable_slots: set[tuple[int, int]] = field(default_factory=set)
    # (day 0-4, period 1-N) çiftleri: available=False olanlar


@dataclass
class CourseData:
    id: int
    name: str
    code: str | None
    branch: str | None
    weekly_hours: int
    hour_distribution: str         # örn. "2+2+1"  → [2, 2, 1]
    is_elective: bool
    target_classes: str            # "ALL" veya virgülle ayrılmış sınıf adları


@dataclass
class ClassData:
    id: int
    name: str
    grade: int
    section: str
    max_daily_hours: int           # sınıfa özel günlük üst sınır


@dataclass
class SchedulerInput:
    school_id: int
    academic_year_id: int
    daily_periods: list[int]       # [7, 7, 8, 7, 7]  → her gün kaç ders
    teachers: list[TeacherData]
    courses: list[CourseData]
    classes: list[ClassData]


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def _parse_distribution(dist: str | None, weekly_hours: int) -> list[int]:
    """'2+2+1' → [2, 2, 1].  None veya boş ise weekly_hours tek blok."""
    if not dist or not dist.strip():
        return [weekly_hours]
    try:
        parts = [int(x.strip()) for x in dist.strip().split("+") if x.strip()]
        return parts if parts else [weekly_hours]
    except ValueError:
        return [weekly_hours]


def _parse_daily_periods(structure: str | None) -> list[int]:
    """'7+7+8+7+7' → [7, 7, 8, 7, 7].  None → [8, 8, 8, 8, 8]."""
    if not structure or not structure.strip():
        return [8, 8, 8, 8, 8]
    try:
        parts = [int(x.strip()) for x in structure.strip().split("+") if x.strip()]
        if len(parts) != 5:
            return [8, 8, 8, 8, 8]
        return parts
    except ValueError:
        return [8, 8, 8, 8, 8]


# ---------------------------------------------------------------------------
# Ana yükleme fonksiyonu
# ---------------------------------------------------------------------------

async def load_scheduler_input(
    db: AsyncSession,
    school_id: int,
    academic_year_id: int,
) -> SchedulerInput:
    """
    Veritabanından tüm scheduler girdisini yükler ve SchedulerInput döner.
    """

    # 1. weekly_lesson_structure
    setting_row = await db.execute(
        text(
            "SELECT value FROM system_settings "
            "WHERE school_id = :sid AND key = 'weekly_lesson_structure' LIMIT 1"
        ),
        {"sid": school_id},
    )
    setting = setting_row.fetchone()
    daily_periods = _parse_daily_periods(setting[0] if setting else None)

    # 2. Öğretmenler
    teachers_rows = await db.execute(
        text(
            "SELECT id, first_name, last_name, branch, "
            "max_daily_hours, max_weekly_hours, allowed_courses, allowed_classes "
            "FROM teachers "
            "WHERE school_id = :sid AND is_active = 1 AND is_deleted = 0"
        ),
        {"sid": school_id},
    )
    teachers_raw = teachers_rows.fetchall()

    # 3. Müsaitlik: tüm unavailable slotlar
    avail_rows = await db.execute(
        text(
            "SELECT teacher_id, day, period FROM teacher_availability "
            "WHERE academic_year_id = :ayid AND available = 0"
        ),
        {"ayid": academic_year_id},
    )
    avail_raw = avail_rows.fetchall()

    unavail_map: dict[int, set[tuple[int, int]]] = {}
    for row in avail_raw:
        tid, day, period = row[0], row[1], row[2]
        unavail_map.setdefault(tid, set()).add((day, period))

    teachers: list[TeacherData] = []
    for r in teachers_raw:
        tid = r[0]
        teachers.append(
            TeacherData(
                id=tid,
                full_name=f"{r[1]} {r[2]}",
                branch=r[3],
                max_daily_hours=r[4] if r[4] else 8,
                max_weekly_hours=r[5] if r[5] else 0,
                allowed_courses=r[6] or "ALL",
                allowed_classes=r[7] or "ALL",
                unavailable_slots=unavail_map.get(tid, set()),
            )
        )

    # 4. Dersler
    courses_rows = await db.execute(
        text(
            "SELECT id, name, code, branch, weekly_hours, "
            "hour_distribution, is_elective, target_classes "
            "FROM courses "
            "WHERE school_id = :sid AND is_active = 1 AND is_deleted = 0"
        ),
        {"sid": school_id},
    )
    courses_raw = courses_rows.fetchall()

    courses: list[CourseData] = []
    for r in courses_raw:
        courses.append(
            CourseData(
                id=r[0],
                name=r[1],
                code=r[2],
                branch=r[3],
                weekly_hours=r[4] or 1,
                hour_distribution=r[5] or str(r[4] or 1),
                is_elective=bool(r[6]),
                target_classes=r[7] or "ALL",
            )
        )

    # 5. Sınıflar
    classes_rows = await db.execute(
        text(
            "SELECT id, name, grade, section, max_daily_hours "
            "FROM classes "
            "WHERE school_id = :sid AND is_active = 1 AND is_deleted = 0"
        ),
        {"sid": school_id},
    )
    classes_raw = classes_rows.fetchall()

    classes: list[ClassData] = []
    for r in classes_raw:
        classes.append(
            ClassData(
                id=r[0],
                name=r[1],
                grade=r[2],
                section=r[3],
                max_daily_hours=r[4] if r[4] else max(daily_periods),
            )
        )

    return SchedulerInput(
        school_id=school_id,
        academic_year_id=academic_year_id,
        daily_periods=daily_periods,
        teachers=teachers,
        courses=courses,
        classes=classes,
    )
