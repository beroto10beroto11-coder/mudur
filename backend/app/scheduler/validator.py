"""
validator.py — Algoritma başlamadan önce veri tutarlılığını doğrular.
"""
from __future__ import annotations

from dataclasses import dataclass

from app.scheduler.data_loader import (
    SchedulerInput,
    CourseData,
    ClassData,
    _parse_distribution,
)


@dataclass
class ValidationResult:
    valid: bool
    errors: list[str]
    warnings: list[str]


def validate(inp: SchedulerInput) -> ValidationResult:
    """
    Tüm kısıtların algoritmaya girilmeden önce karşılandığını kontrol eder.
    Hatalar: programı durduran kritik sorunlar.
    Uyarılar: devam edilebilir ama dikkat gerektiren durumlar.
    """
    errors: list[str] = []
    warnings: list[str] = []

    total_weekly = sum(inp.daily_periods)  # örn. 7+7+8+7+7 = 36

    # ------------------------------------------------------------------ #
    # 1. Ders bazlı kontroller
    # ------------------------------------------------------------------ #
    course_map: dict[str, CourseData] = {}
    for c in inp.courses:
        # hour_distribution vs weekly_hours uyumu
        dist = _parse_distribution(c.hour_distribution, c.weekly_hours)
        dist_total = sum(dist)
        if dist_total != c.weekly_hours:
            errors.append(
                f"[DERS HATASI] '{c.name}' ({c.code or '—'}): "
                f"hour_distribution toplamı ({dist_total}) weekly_hours ({c.weekly_hours}) ile uyuşmuyor. "
                f"Lütfen dersi düzeltin."
            )
        course_map[c.name] = c

        # Dağılımdaki her bloğun günlük max'ı aşıp aşmadığı
        max_block = max(dist) if dist else 1
        max_day = max(inp.daily_periods)
        if max_block > max_day:
            errors.append(
                f"[DERS HATASI] '{c.name}': Dağılımdaki en büyük blok ({max_block}) "
                f"günlük maksimum ders sayısını ({max_day}) aşıyor."
            )

    # ------------------------------------------------------------------ #
    # 2. Sınıf bazlı kontroller: toplam ders saati == weekly toplam mı?
    # ------------------------------------------------------------------ #
    for cls in inp.classes:
        assigned_courses = _get_courses_for_class(cls, inp.courses)
        total_assigned = sum(c.weekly_hours for c in assigned_courses)

        if not assigned_courses:
            warnings.append(
                f"[SINIF UYARISI] '{cls.name}': Bu sınıfa atanmış hiç ders yok."
            )
        elif total_assigned != total_weekly:
            errors.append(
                f"[SINIF HATASI] '{cls.name}': Atanmış derslerin toplam haftalık saati "
                f"({total_assigned}) okulun haftalık ders yapısıyla ({total_weekly}) uyuşmuyor. "
                f"Lütfen ders saatlerini gözden geçirin."
            )

    # ------------------------------------------------------------------ #
    # 3. Öğretmen bazlı kontroller
    # ------------------------------------------------------------------ #
    for t in inp.teachers:
        allowed_c = _parse_str_list(t.allowed_courses)
        allowed_cl = _parse_str_list(t.allowed_classes)

        if not allowed_c and t.allowed_courses.upper() != "ALL":
            warnings.append(
                f"[ÖĞRETMEN UYARISI] '{t.full_name}': Verebileceği ders tanımlı değil."
            )
        if not allowed_cl and t.allowed_classes.upper() != "ALL":
            warnings.append(
                f"[ÖĞRETMEN UYARISI] '{t.full_name}': Girebileceği sınıf tanımlı değil."
            )

    # ------------------------------------------------------------------ #
    # 4. Öğretmen-ders eşleşme kontrolü: her (ders, sınıf) için en az 1 öğretmen var mı?
    # ------------------------------------------------------------------ #
    for cls in inp.classes:
        assigned_courses = _get_courses_for_class(cls, inp.courses)
        for c in assigned_courses:
            eligible = _get_eligible_teachers(c, cls, inp.teachers)
            if not eligible:
                errors.append(
                    f"[EŞLEŞİM HATASI] '{cls.name}' sınıfı – '{c.name}' dersi: "
                    f"Bu (ders, sınıf) çiftine uygun hiçbir öğretmen bulunamadı. "
                    f"Öğretmen branş/sınıf izin listelerini kontrol edin."
                )

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
    )


# ---------------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ---------------------------------------------------------------------------

def _parse_str_list(value: str) -> list[str]:
    """'ALL' → []  (tümünü temsil eder).  'A,B,C' → ['A', 'B', 'C']."""
    if not value or value.strip().upper() == "ALL":
        return []
    return [x.strip() for x in value.split(",") if x.strip()]


def _get_courses_for_class(cls: ClassData, courses: list[CourseData]) -> list[CourseData]:
    """Bu sınıfa atanmış dersleri döner (target_classes kontrolü)."""
    result = []
    for c in courses:
        targets = _parse_str_list(c.target_classes)
        if not targets:  # ALL
            result.append(c)
        elif cls.name in targets:
            result.append(c)
    return result


def _get_eligible_teachers(
    course: CourseData,
    cls: ClassData,
    teachers: list,
) -> list:
    """Bu (ders, sınıf) çiftine uygun öğretmenleri döner."""
    result = []
    for t in teachers:
        # Ders yetkisi
        allowed_c = _parse_str_list(t.allowed_courses)
        if allowed_c:  # ALL değil
            if course.name not in allowed_c and (course.code or "") not in allowed_c:
                continue
        # Sınıf yetkisi
        allowed_cl = _parse_str_list(t.allowed_classes)
        if allowed_cl:  # ALL değil
            if cls.name not in allowed_cl:
                continue
        result.append(t)
    return result
