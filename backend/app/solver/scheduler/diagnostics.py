"""
INFEASIBLE Teşhis Modülü
=========================
Solver çözüm bulamazsa hangi kısıtların tıkandığına dair
insan-okunur teşhis raporu üretir.

Strateji:
1. Validator'ın kapasite raporunu tekrar çalıştır.
2. Ek heuristik analizler yap (öğretmen yük taşması, blok yerleştirme
   imkânsızlığı vb.)
3. OR-Tools assumption-based infeasibility analizi (CpSolver.SolveWithAssumptions)
   ile minimum çakışan kısıt setini bulmaya çalış.
"""
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

if TYPE_CHECKING:
    from app.solver.scheduler.models import SchedulerInput

from app.solver.scheduler.models import FeasibilityIhlali
from app.solver.scheduler.validator import validate_feasibility


def diagnose_infeasibility(
    inp: "SchedulerInput",
    x_vars: dict,
    y_vars: dict,
    model: cp_model.CpModel,
) -> list[str]:
    """
    Olası tıkanma noktalarını analiz ederek insan-okunur mesaj listesi döndürür.
    """
    mesajlar: list[str] = []

    # ─── 1. Kapasite Raporunu Tekrar Çalıştır ─────────────────────────────────
    ihlaller = validate_feasibility(inp)
    for ih in ihlaller:
        mesajlar.append(f"[{ih.tur}] {ih.mesaj}")

    # ─── 2. Blok Yerleştirme Analizi ──────────────────────────────────────────
    gunler = inp.zaman_yapisi.gunler
    gun_saatleri = inp.zaman_yapisi.gunluk_ders_saatleri
    num_gunler = len(gunler)

    for ders in inp.dersler:
        for blok_idx, blok_uzunluk in enumerate(ders.gunluk_dagilim):
            # Bu bloğun yerleştirilebileceği gün sayısı
            uygun_gun_sayisi = sum(
                1 for g in range(num_gunler)
                if gun_saatleri[g] >= blok_uzunluk
            )
            if uygun_gun_sayisi < len(ders.gunluk_dagilim):
                mesajlar.append(
                    f"[BLOK_YERLESTIRME] Ders '{ders.ders_adi}' ({ders.ders_id}): "
                    f"Blok #{blok_idx + 1} ({blok_uzunluk} saat) için yeterli "
                    f"gün yok. Gereken gün sayısı: {len(ders.gunluk_dagilim)}, "
                    f"yeterli saatli gün: {uygun_gun_sayisi}."
                )

    # ─── 3. Öğretmen Günlük Yük Analizi ──────────────────────────────────────
    for o in inp.ogretmenler:
        # Bu öğretmenin verebileceği tüm dersler
        ogr_dersler = [
            d for d in inp.dersler
            if d.kod in o.branslar
            and any(s in o.girebilecegi_subeler for s in d.gecerli_sube_ids)
        ]
        toplam_atanabilir_sube = sum(
            len([s for s in d.gecerli_sube_ids if s in o.girebilecegi_subeler])
            * d.haftalik_saat
            for d in ogr_dersler
        )

        # Öğretmenin toplam müsait saati
        toplam_musait = sum(
            1
            for g_idx, gun_adi in enumerate(gunler)
            for s_idx in range(gun_saatleri[g_idx])
            if o.musait_mi(gun_adi, s_idx)
        )

        if toplam_atanabilir_sube > 0 and toplam_musait == 0:
            mesajlar.append(
                f"[MUSAITLIK_SIFIR] Öğretmen '{o.tam_ad}' ({o.ogretmen_id}): "
                f"Hiç müsait saati yok fakat {toplam_atanabilir_sube} saatlik "
                f"ders yükü var."
            )

    # ─── 4. Şube × Gün Çakışma Analizi ───────────────────────────────────────
    for sube in inp.subeler:
        sube_id = sube.sube_id
        sube_dersler = [d for d in inp.dersler if sube_id in d.gecerli_sube_ids]
        toplam_blok = sum(d.blok_sayisi for d in sube_dersler)
        if toplam_blok > num_gunler * max(gun_saatleri):
            mesajlar.append(
                f"[SUBE_BLOK_ASIMI] Şube '{sube.ad}' ({sube_id}): "
                f"Toplam blok sayısı ({toplam_blok}), mevcut gün×saat "
                f"kapasitesini aşıyor ({num_gunler * max(gun_saatleri)})."
            )

    # ─── 5. OR-Tools Assumption tabanlı MUS analizi ───────────────────────────
    mus_mesaj = _try_mus_analysis(model, x_vars, y_vars)
    if mus_mesaj:
        mesajlar.append(mus_mesaj)

    if not mesajlar:
        mesajlar.append(
            "[GENEL_INFEASIBILITY] Belirtilen kısıtlar altında geçerli bir "
            "ders programı bulunamadı. Öğretmen müsaitliklerini, ders atamalarını "
            "veya blok dağılımlarını gözden geçirin."
        )

    return mesajlar


def _try_mus_analysis(
    model: cp_model.CpModel,
    x_vars: dict,
    y_vars: dict,
) -> str | None:
    """
    OR-Tools'un SolveWithAssumptions API'si ile minimum uyumsuz alt küme (MUS)
    bulmaya çalışır. Zaman aşımı nedeniyle kısmen bilgi döndürebilir.
    """
    try:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 10

        # Tüm x değişkenlerini assumption olarak ver
        assumptions = list(x_vars.values())[:200]  # çok büyük olmasın
        if not assumptions:
            return None

        status = solver.solve_with_assumptions(model, assumptions)

        if status == cp_model.INFEASIBLE:
            sufficient_assumptions = solver.sufficient_assumptions_for_infeasibility()
            if sufficient_assumptions:
                return (
                    f"[MUS_ANALİZ] CP-SAT {len(sufficient_assumptions)} değişkeni "
                    f"içeren çakışan bir kısıt kümesi tespit etti. "
                    f"Bu blok atamaları gevşetilerek çözüm aranabilir."
                )
    except Exception:
        pass

    return None
