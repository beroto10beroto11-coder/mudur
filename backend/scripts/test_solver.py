"""
Solver'i dogrudan calistirip sonucu analiz et.
Tum sinif/sube icin eksik slotlari bul.
"""
import asyncio
import sys
import os

# Backend path'ini ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.models.course import Course
from app.models.assignment import CourseAssignment
from app.models.class_ import ClassGroup
from app.models.teacher import Teacher, TeacherAvailability
from app.models.timeslot import TimeSlot
from app.tasks.solver_task import (
    _build_scheduler_input,
    _synthesize_assignments,
    _parse_hour_distribution,
    _extract_ders_kodu,
    _extract_branslar,
)
from app.solver.scheduler import run_scheduler


async def main():
    school_id = 1
    academic_year_id = 1

    async with AsyncSessionLocal() as session:
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
            courses_list = list(courses_res.scalars().all())
            assignments = _synthesize_assignments(courses_list, classes, teachers, school_id, academic_year_id)
            print(f"Synthesized {len(assignments)} assignments (no real assignments found)")
        else:
            print(f"Found {len(assignments)} real assignments")

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

    print(f"\nTeachers: {len(teachers)}")
    print(f"Classes: {len(classes)}")
    print(f"TimeSlots: {len(timeslots)}")
    print(f"Availabilities: {len(availabilities)}")

    # SchedulerInput olustur
    scheduler_input = _build_scheduler_input(
        teachers=teachers,
        classes=classes,
        assignments=assignments,
        timeslots=timeslots,
        availabilities=availabilities,
        school_id=school_id,
    )

    print(f"\n=== SchedulerInput ===")
    print(f"Gunler: {scheduler_input.zaman_yapisi.gunler}")
    print(f"Gunluk ders saatleri: {scheduler_input.zaman_yapisi.gunluk_ders_saatleri}")
    print(f"Toplam haftalik: {scheduler_input.zaman_yapisi.toplam_haftalik_saat}")
    print(f"Subeler: {len(scheduler_input.subeler)}")
    print(f"Ogretmenler: {len(scheduler_input.ogretmenler)}")
    print(f"Dersler: {len(scheduler_input.dersler)}")

    # Her ders icin bilgi
    print(f"\n=== Dersler ===")
    for d in scheduler_input.dersler:
        print(f"  {d.ders_id}: {d.ders_adi} (kod={d.kod}, haftalik={d.haftalik_saat}, dagilim={d.gunluk_dagilim}, subeler={d.gecerli_sube_ids})")

    # Her ogretmen icin brans
    print(f"\n=== Ogretmenler ===")
    for o in scheduler_input.ogretmenler:
        print(f"  {o.ogretmen_id}: {o.ad} {o.soyad} branslar={o.branslar}, subeler={o.girebilecegi_subeler}")

    # Her (ders, sube) icin uygun ogretmen kontrolu
    print(f"\n=== Ders-Sube Ogretmen Eslesmesi ===")
    problem_pairs = []
    for d in scheduler_input.dersler:
        for sube_id in d.gecerli_sube_ids:
            uygun = [
                o for o in scheduler_input.ogretmenler
                if d.kod in o.branslar and sube_id in o.girebilecegi_subeler
            ]
            if not uygun:
                problem_pairs.append((d.ders_adi, d.kod, sube_id))
                print(f"  HATA: {d.ders_adi} (kod={d.kod}) -> sube {sube_id}: UYGUN OGRETMEN YOK!")
            else:
                print(f"  OK: {d.ders_adi} (kod={d.kod}) -> sube {sube_id}: {len(uygun)} ogretmen ({[o.tam_ad for o in uygun]})")

    if problem_pairs:
        print(f"\n!!! {len(problem_pairs)} (ders, sube) cifti icin ogretmen bulunamadi!")
        print("Solver INFEASIBLE donecek veya eksik program uretecek.")
        return

    # Sube bazinda toplam saat kontrolu
    print(f"\n=== Sube Bazinda Toplam Ders Saati ===")
    okul_toplam = scheduler_input.zaman_yapisi.toplam_haftalik_saat
    for sube in scheduler_input.subeler:
        sube_dersler = [d for d in scheduler_input.dersler if sube.sube_id in d.gecerli_sube_ids]
        toplam = sum(d.haftalik_saat for d in sube_dersler)
        status = "OK" if toplam == okul_toplam else f"HATA ({toplam} != {okul_toplam})"
        print(f"  {sube.ad} (id={sube.sube_id}): {toplam} saat [{status}]")

    # Solver calistir
    print(f"\n=== Solver Calistiriliyor... ===")
    result = run_scheduler(scheduler_input)

    print(f"\nSonuc: basarili={result.basarili}, durum={result.durum}, sure={result.sure_saniye:.1f}s")
    print(f"Hedef deger: {result.hedef_deger}")
    print(f"Ihlaller: {len(result.ihlaller)}")
    for ih in result.ihlaller:
        print(f"  [{ih.tur}] {ih.mesaj}")
    print(f"Teshis: {len(result.teshis_mesajlari)}")
    for t in result.teshis_mesajlari:
        print(f"  {t}")

    if not result.basarili:
        print("\nSolver basarisiz! Yukaridaki ihlaller ve teshis mesajlarini inceleyin.")
        return

    # Sonuclari analiz et
    print(f"\n=== Sube Programlari Analizi ===")
    DAY_NAMES = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma"]
    gun_saatleri = scheduler_input.zaman_yapisi.gunluk_ders_saatleri

    for sp in result.sube_programlari:
        sube_obj = next((s for s in scheduler_input.subeler if s.sube_id == sp.sube_id), None)
        sube_ad = sube_obj.ad if sube_obj else sp.sube_id
        print(f"\n  --- {sube_ad} (id={sp.sube_id}) ---")

        toplam_ders = 0
        toplam_bos = 0

        for gun_idx, gun_adi in enumerate(DAY_NAMES):
            maks = gun_saatleri[gun_idx]
            slots = sp.program.get(gun_adi, [])
            dolu_saatler = {s.saat for s in slots}

            bos_saatler = []
            for saat in range(1, maks + 1):
                if saat not in dolu_saatler:
                    bos_saatler.append(saat)

            toplam_ders += len(slots)
            toplam_bos += len(bos_saatler)

            if bos_saatler:
                print(f"    {gun_adi}: {len(slots)}/{maks} dolu, BOS saatler: {bos_saatler}")
            else:
                print(f"    {gun_adi}: {len(slots)}/{maks} dolu (TAM)")

        print(f"    TOPLAM: {toplam_ders} ders, {toplam_bos} bos saat")
        if toplam_bos > 0:
            print(f"    *** EKSIK PROGRAM: {toplam_bos} saat bos! ***")

    # Ogretmen programlari analizi
    print(f"\n=== Ogretmen Cakisma Kontrolu ===")
    cakisma_var = False
    for op in result.ogretmen_programlari:
        for gun_adi, slots in op.program.items():
            saatler = [s.saat for s in slots if s.durum == "DOLU"]
            if len(saatler) != len(set(saatler)):
                from collections import Counter
                c = Counter(saatler)
                for saat, cnt in c.items():
                    if cnt > 1:
                        print(f"  CAKISMA: Ogretmen {op.ogretmen_id}, {gun_adi} saat {saat}: {cnt} ders!")
                        cakisma_var = True

    if not cakisma_var:
        print("  Ogretmen cakismasi yok (OK)")


if __name__ == "__main__":
    asyncio.run(main())
