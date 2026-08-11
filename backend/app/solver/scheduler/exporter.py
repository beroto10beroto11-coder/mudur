"""
Çıktı Üretici Modül
====================
Solver çözümünden şube ve öğretmen bazlı program tablolarını üretir.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

if TYPE_CHECKING:
    from app.solver.scheduler.models import SchedulerInput

from app.solver.scheduler.models import (
    SubeSlot,
    SubeProgram,
    OgretmenSlot,
    OgretmenProgram,
)


def export_by_class(
    solver: cp_model.CpSolver,
    x_vars: dict,
    y_vars: dict,
    inp: "SchedulerInput",
) -> list[SubeProgram]:
    """
    Şube bazlı haftalık program tablosunu üretir.

    Her şube için gün × saat matrisi:
        gün → [{"saat": 1, "ders_id": ..., "ogretmen_id": ...}, ...]
    """
    gunler = inp.zaman_yapisi.gunler
    gun_saatleri = inp.zaman_yapisi.gunluk_ders_saatleri
    num_gunler = len(gunler)

    # Çözümden (ders, sube, blok, gun, saat, ogretmen) atamalarını çıkar
    assignments = _extract_assignments(solver, x_vars, y_vars, inp)

    result: list[SubeProgram] = []

    for sube in inp.subeler:
        sube_id = sube.sube_id
        program: dict[str, list[SubeSlot]] = {}

        for g_idx, gun_adi in enumerate(gunler):
            maks = gun_saatleri[g_idx]
            gun_slots: list[SubeSlot] = []

            # Bu gündeki tüm ders saatlerini doldur
            h_to_slot: dict[int, tuple[str, str]] = {}  # h_idx → (ders_id, ogretmen_id)

            for asn in assignments:
                if asn["sube_id"] != sube_id:
                    continue
                if asn["gun_idx"] != g_idx:
                    continue
                blok_uzunluk = inp.dersler[
                    next(i for i, d in enumerate(inp.dersler) if d.ders_id == asn["ders_id"])
                ].gunluk_dagilim[asn["blok_idx"]]
                for offset in range(blok_uzunluk):
                    h = asn["baslangic_saat"] + offset
                    h_to_slot[h] = (asn["ders_id"], asn["ogretmen_id"])

            for h in range(maks):
                if h in h_to_slot:
                    ders_id, ogretmen_id = h_to_slot[h]
                    gun_slots.append(SubeSlot(
                        saat=h + 1,  # 1-tabanlı
                        ders_id=ders_id,
                        ogretmen_id=ogretmen_id,
                    ))

            program[gun_adi] = gun_slots

        result.append(SubeProgram(sube_id=sube_id, program=program))

    return result


def export_by_teacher(
    solver: cp_model.CpSolver,
    x_vars: dict,
    y_vars: dict,
    inp: "SchedulerInput",
) -> list[OgretmenProgram]:
    """
    Öğretmen bazlı haftalık program tablosunu üretir.

    Her öğretmen için gün × saat matrisi;
    boş saatler 'durum: BOŞ' ile işaretlenir.
    """
    gunler = inp.zaman_yapisi.gunler
    gun_saatleri = inp.zaman_yapisi.gunluk_ders_saatleri
    num_gunler = len(gunler)

    assignments = _extract_assignments(solver, x_vars, y_vars, inp)

    result: list[OgretmenProgram] = []

    for o in inp.ogretmenler:
        ogretmen_id = o.ogretmen_id
        program: dict[str, list[OgretmenSlot]] = {}

        for g_idx, gun_adi in enumerate(gunler):
            maks = gun_saatleri[g_idx]
            h_to_slot: dict[int, tuple[str, str]] = {}  # h_idx → (ders_id, sube_id)

            for asn in assignments:
                if asn["ogretmen_id"] != ogretmen_id:
                    continue
                if asn["gun_idx"] != g_idx:
                    continue
                # Ders nesnesini bul
                ders_obj = next(
                    (d for d in inp.dersler if d.ders_id == asn["ders_id"]), None
                )
                if ders_obj is None:
                    continue
                blok_uzunluk = ders_obj.gunluk_dagilim[asn["blok_idx"]]
                for offset in range(blok_uzunluk):
                    h = asn["baslangic_saat"] + offset
                    h_to_slot[h] = (asn["ders_id"], asn["sube_id"])

            gun_slots: list[OgretmenSlot] = []
            for h in range(maks):
                if h in h_to_slot:
                    ders_id, sube_id = h_to_slot[h]
                    gun_slots.append(OgretmenSlot(
                        saat=h + 1,
                        ders_id=ders_id,
                        sube_id=sube_id,
                        durum="DOLU",
                    ))
                else:
                    gun_slots.append(OgretmenSlot(
                        saat=h + 1,
                        durum="BOŞ",
                    ))

            program[gun_adi] = gun_slots

        result.append(OgretmenProgram(ogretmen_id=ogretmen_id, program=program))

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Ortak yardımcı: solver çözümünden atamaları çıkar
# ─────────────────────────────────────────────────────────────────────────────

def _extract_assignments(
    solver: cp_model.CpSolver,
    x_vars: dict,
    y_vars: dict,
    inp: "SchedulerInput",
) -> list[dict]:
    """
    x=1 ve karşılık gelen y=1 olan (ders, sube, blok, gun, saat, ogretmen)
    atamalarını döndürür.
    """
    # Önce seçilen (ders, sube, blok) → ogretmen_id eşlemesini bul
    blok_ogretmen: dict[tuple, str] = {}
    for (ders_id, sube_id, blok_idx, ogretmen_id), y_var in y_vars.items():
        if solver.value(y_var) == 1:
            blok_ogretmen[(ders_id, sube_id, blok_idx)] = ogretmen_id

    assignments = []
    for (ders_id, sube_id, blok_idx, g_idx, s_idx), x_var in x_vars.items():
        if solver.value(x_var) == 1:
            ogretmen_id = blok_ogretmen.get((ders_id, sube_id, blok_idx), "BILINMIYOR")
            assignments.append({
                "ders_id": ders_id,
                "sube_id": sube_id,
                "blok_idx": blok_idx,
                "gun_idx": g_idx,
                "baslangic_saat": s_idx,
                "ogretmen_id": ogretmen_id,
            })

    return assignments
