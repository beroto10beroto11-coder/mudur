"""
Çözüm Sonrası Doğrulama Modülü (G1)
=====================================
Solver başarılı bir çözüm ürettikten sonra, veritabanına yazmadan önce
şartnamenin G1 maddesindeki tüm kontrolleri çalıştırır.

Kontroller:
    G1.1 — Her şubenin tüm saatleri dolu mu (A1)?
    G1.2 — Her dersin ataması tam saatinde mi (A2)?
    G1.3 — Hiçbir öğretmen müsait olmadığı saate atanmamış mı (C3)?
    G1.4 — Öğretmen çakışması yok mu (C5)?
    G1.5 — Şube çakışması yok mu (D1)?
    G1.6 — Şube bazlı ile öğretmen bazlı çıktılar tutarlı mı (I1)?
    G1.7 — Öğretmen haftalık max saat aşılmamış mı (C4)?
    G1.8 — Bloklar ardışık mı (B2) ve farklı günlerde mi (B3)?
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.solver.scheduler.models import (
        SchedulerInput,
        SubeProgram,
        OgretmenProgram,
    )


@dataclass
class PostValidationIhlali:
    kural: str        # "G1.1", "G1.2", ...
    tur: str          # "BOŞ_SAAT", "EKSIK_ATAMA", "CAKISMA", vb.
    mesaj: str
    detay: dict = field(default_factory=dict)


def validate_solution(
    inp: "SchedulerInput",
    sube_programlari: "list[SubeProgram]",
    ogretmen_programlari: "list[OgretmenProgram]",
) -> list[PostValidationIhlali]:
    """
    Solver çözümünü G1 kuralına göre doğrular.

    Döndürür: ihlal listesi. Boşsa çözüm geçerli.
    """
    ihlaller: list[PostValidationIhlali] = []

    # Hızlı erişim için indeksler
    gunler = inp.zaman_yapisi.gunler
    gun_saatleri = inp.zaman_yapisi.gunluk_ders_saatleri

    # Şube programlarını dict'e çevir: sube_id → {gun → {saat → (ders_id, ogretmen_id)}}
    sube_grid: dict[str, dict[str, dict[int, tuple[str, str]]]] = {}
    for sp in sube_programlari:
        sube_grid[sp.sube_id] = {}
        for gun, slotlar in sp.program.items():
            sube_grid[sp.sube_id][gun] = {s.saat: (s.ders_id, s.ogretmen_id) for s in slotlar}

    # Öğretmen programlarını dict'e çevir: ogretmen_id → {gun → {saat → (ders_id, sube_id)}}
    ogretmen_grid: dict[str, dict[str, dict[int, tuple[str | None, str | None]]]] = {}
    for op in ogretmen_programlari:
        ogretmen_grid[op.ogretmen_id] = {}
        for gun, slotlar in op.program.items():
            ogretmen_grid[op.ogretmen_id][gun] = {}
            for s in slotlar:
                if s.durum == "DOLU" and s.ders_id and s.sube_id:
                    ogretmen_grid[op.ogretmen_id][gun][s.saat] = (s.ders_id, s.sube_id)

    # ─── G1.1 — Her şubenin tüm saatleri dolu mu? (A1) ─────────────────────
    for g_idx, gun in enumerate(gunler):
        maks_saat = gun_saatleri[g_idx]
        for sube in inp.subeler:
            gun_program = sube_grid.get(sube.sube_id, {}).get(gun, {})
            for saat_1based in range(1, maks_saat + 1):
                if saat_1based not in gun_program:
                    ihlaller.append(PostValidationIhlali(
                        kural="G1.1",
                        tur="BOŞ_SAAT",
                        mesaj=(
                            f"A1 İHLALİ — Şube '{sube.ad}' ({sube.sube_id}): "
                            f"{gun} günü {saat_1based}. saat boş kaldı."
                        ),
                        detay={
                            "sube_id": sube.sube_id,
                            "sube_ad": sube.ad,
                            "gun": gun,
                            "saat": saat_1based,
                        },
                    ))

    # ─── G1.2 — Her dersin ataması tam saatinde mi? (A2) ────────────────────
    for ders in inp.dersler:
        for sube_id in ders.gecerli_sube_ids:
            sube_obj = next((s for s in inp.subeler if s.sube_id == sube_id), None)
            if sube_obj is None:
                continue
            # Şube programında bu derse ait toplam saat sayısını say
            atanan_saat = 0
            for gun_program in sube_grid.get(sube_id, {}).values():
                for saat, (d_id, _) in gun_program.items():
                    if d_id == ders.ders_id:
                        atanan_saat += 1

            if atanan_saat != ders.haftalik_saat:
                ihlaller.append(PostValidationIhlali(
                    kural="G1.2",
                    tur="EKSIK_ATAMA" if atanan_saat < ders.haftalik_saat else "FAZLA_ATAMA",
                    mesaj=(
                        f"A2 İHLALİ — Ders '{ders.ders_adi}', Şube '{sube_obj.ad}': "
                        f"Beklenen {ders.haftalik_saat} saat, atanan {atanan_saat} saat."
                    ),
                    detay={
                        "ders_id": ders.ders_id,
                        "ders_adi": ders.ders_adi,
                        "sube_id": sube_id,
                        "beklenen": ders.haftalik_saat,
                        "atanan": atanan_saat,
                    },
                ))

    # ─── G1.3 — Öğretmen müsait olmadığı saate atanmamış mı? (C3) ──────────
    for ogretmen in inp.ogretmenler:
        for g_idx, gun in enumerate(gunler):
            maks_saat = gun_saatleri[g_idx]
            ogr_gun = ogretmen_grid.get(ogretmen.ogretmen_id, {}).get(gun, {})
            for saat_1based, (ders_id, sube_id) in ogr_gun.items():
                saat_0based = saat_1based - 1
                if not ogretmen.musait_mi(gun, saat_0based):
                    ihlaller.append(PostValidationIhlali(
                        kural="G1.3",
                        tur="MUSAITLIK_IHLALI",
                        mesaj=(
                            f"C3 İHLALİ — Öğretmen '{ogretmen.tam_ad}': "
                            f"{gun} günü {saat_1based}. saatte müsait değil "
                            f"ama '{ders_id}' dersi atanmış (Şube: {sube_id})."
                        ),
                        detay={
                            "ogretmen_id": ogretmen.ogretmen_id,
                            "gun": gun,
                            "saat": saat_1based,
                            "ders_id": ders_id,
                            "sube_id": sube_id,
                        },
                    ))

    # ─── G1.4 — Öğretmen çakışması yok mu? (C5) ─────────────────────────────
    # Şube programlarından çapraz kontrol: aynı öğretmen, aynı (gün, saat)'te
    # birden fazla şubede ders veriyor mu?
    ogretmen_saat_kullanim: dict[str, dict[str, dict[int, list[tuple[str, str]]]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    for sp in sube_programlari:
        sube_id = sp.sube_id
        for gun, slotlar in sp.program.items():
            for slot in slotlar:
                ogretmen_saat_kullanim[slot.ogretmen_id][gun][slot.saat].append(
                    (sube_id, slot.ders_id)
                )

    for ogr_id, gun_map in ogretmen_saat_kullanim.items():
        ogretmen_obj = next((o for o in inp.ogretmenler if o.ogretmen_id == ogr_id), None)
        ogr_ad = ogretmen_obj.tam_ad if ogretmen_obj else ogr_id
        for gun, saat_map in gun_map.items():
            for saat, atamalar in saat_map.items():
                if len(atamalar) > 1:
                    sube_listesi = ", ".join(f"{s}({d})" for s, d in atamalar)
                    ihlaller.append(PostValidationIhlali(
                        kural="G1.4",
                        tur="OGRETMEN_CAKISMASI",
                        mesaj=(
                            f"C5 İHLALİ — Öğretmen '{ogr_ad}' ({ogr_id}): "
                            f"{gun} günü {saat}. saatte {len(atamalar)} şubede "
                            f"atanmış: [{sube_listesi}]"
                        ),
                        detay={
                            "ogretmen_id": ogr_id,
                            "gun": gun,
                            "saat": saat,
                            "atamalar": [{"sube_id": s, "ders_id": d} for s, d in atamalar],
                        },
                    ))

    # ─── G1.5 — Şube çakışması yok mu? (D1) ─────────────────────────────────
    # Şube programında aynı (gün, saat) için birden fazla ders atanmış mı?
    # sube_grid dict key unique olduğundan, ham slot listesinden kontrol:
    for sp in sube_programlari:
        for gun, slotlar in sp.program.items():
            saat_sayac: dict[int, list[str]] = defaultdict(list)
            for slot in slotlar:
                saat_sayac[slot.saat].append(slot.ders_id)
            for saat, ders_listesi in saat_sayac.items():
                if len(ders_listesi) > 1:
                    sube_obj = next((s for s in inp.subeler if s.sube_id == sp.sube_id), None)
                    sube_ad = sube_obj.ad if sube_obj else sp.sube_id
                    ihlaller.append(PostValidationIhlali(
                        kural="G1.5",
                        tur="SUBE_CAKISMASI",
                        mesaj=(
                            f"D1 İHLALİ — Şube '{sube_ad}' ({sp.sube_id}): "
                            f"{gun} günü {saat}. saatte {len(ders_listesi)} ders "
                            f"atanmış: {ders_listesi}"
                        ),
                        detay={
                            "sube_id": sp.sube_id,
                            "gun": gun,
                            "saat": saat,
                            "ders_listesi": ders_listesi,
                        },
                    ))

    # ─── G1.6 — Şube bazlı ile öğretmen bazlı tutarlılık (I1) ───────────────
    # Şube programında (ogretmen_id, gun, saat) → ders olan her kayıt,
    # öğretmen programında da (sube_id, gun, saat) → aynı ders olarak görünmeli.
    for sp in sube_programlari:
        sube_id = sp.sube_id
        for gun, slotlar in sp.program.items():
            for slot in slotlar:
                ogr_id = slot.ogretmen_id
                ogr_gun = ogretmen_grid.get(ogr_id, {}).get(gun, {})
                ogr_slot = ogr_gun.get(slot.saat)

                if ogr_slot is None:
                    ihlaller.append(PostValidationIhlali(
                        kural="G1.6",
                        tur="TUTARSIZLIK",
                        mesaj=(
                            f"I1 İHLALİ — Şube '{sube_id}' programında {gun} "
                            f"{slot.saat}. saatte öğretmen '{ogr_id}' için '{slot.ders_id}' "
                            f"görünüyor, ama öğretmen programında bu saat yok/BOŞ."
                        ),
                        detay={
                            "sube_id": sube_id,
                            "ogretmen_id": ogr_id,
                            "gun": gun,
                            "saat": slot.saat,
                            "ders_id": slot.ders_id,
                        },
                    ))
                elif ogr_slot[0] != slot.ders_id:
                    ihlaller.append(PostValidationIhlali(
                        kural="G1.6",
                        tur="TUTARSIZLIK",
                        mesaj=(
                            f"I1 İHLALİ — {gun} {slot.saat}. saatte Şube '{sube_id}' "
                            f"programı '{slot.ders_id}' diyor, "
                            f"öğretmen '{ogr_id}' programı '{ogr_slot[0]}' diyor."
                        ),
                        detay={
                            "sube_id": sube_id,
                            "ogretmen_id": ogr_id,
                            "gun": gun,
                            "saat": slot.saat,
                            "sube_dersid": slot.ders_id,
                            "ogretmen_dersid": ogr_slot[0],
                        },
                    ))

    # ─── G1.7 — Öğretmen haftalık max saat aşılmamış mı? (C4) ───────────────
    for ogretmen in inp.ogretmenler:
        if ogretmen.haftalik_max_ders_saati <= 0:
            continue  # Sınırsız
        toplam_saat = 0
        ogr_program = ogretmen_grid.get(ogretmen.ogretmen_id, {})
        for gun, saat_map in ogr_program.items():
            toplam_saat += len(saat_map)
        if toplam_saat > ogretmen.haftalik_max_ders_saati:
            ihlaller.append(PostValidationIhlali(
                kural="G1.7",
                tur="HAFTALIK_MAKS_ASIMI",
                mesaj=(
                    f"C4 İHLALİ — Öğretmen '{ogretmen.tam_ad}': "
                    f"Haftalık max {ogretmen.haftalik_max_ders_saati} saat, "
                    f"atanan {toplam_saat} saat."
                ),
                detay={
                    "ogretmen_id": ogretmen.ogretmen_id,
                    "max_saat": ogretmen.haftalik_max_ders_saati,
                    "atanan_saat": toplam_saat,
                },
            ))

    # ─── G1.8 — Blok ardışıklık (B2) ve farklı gün (B3) kontrolü ────────────
    for ders in inp.dersler:
        for sube_id in ders.gecerli_sube_ids:
            sube_program = sube_grid.get(sube_id, {})
            # Bu dersin hangi günlerde, hangi saatlerde olduğunu bul
            gun_saatler: dict[str, list[int]] = defaultdict(list)
            for gun, saat_map in sube_program.items():
                for saat, (d_id, _) in saat_map.items():
                    if d_id == ders.ders_id:
                        gun_saatler[gun].append(saat)

            # B3: Her gün en fazla 1 blok (farklı günlere dağılım)
            # Blok sayısına göre kontrol: kaç farklı günde olmalı = blok_sayisi
            bloklar_gun_listesi = [g for g, saatler in gun_saatler.items() if saatler]
            # Aynı gündeki saatleri sıralayıp ardışık blok kontrolü yap
            for gun, saatler in gun_saatler.items():
                if not saatler:
                    continue
                saatler_sorted = sorted(saatler)
                # B2: Blok içindeki saatler ardışık olmalı
                # Ardışık grupları bul
                gruplar: list[list[int]] = []
                current_group = [saatler_sorted[0]]
                for i in range(1, len(saatler_sorted)):
                    if saatler_sorted[i] == saatler_sorted[i - 1] + 1:
                        current_group.append(saatler_sorted[i])
                    else:
                        gruplar.append(current_group)
                        current_group = [saatler_sorted[i]]
                gruplar.append(current_group)

                # Bir gün içinde birden fazla ayrık grup varsa B3 ihlali
                if len(gruplar) > 1:
                    sube_obj = next((s for s in inp.subeler if s.sube_id == sube_id), None)
                    sube_ad = sube_obj.ad if sube_obj else sube_id
                    ihlaller.append(PostValidationIhlali(
                        kural="G1.8",
                        tur="BLOK_FARKLI_GUN_IHLALI",
                        mesaj=(
                            f"B3 İHLALİ — Ders '{ders.ders_adi}', Şube '{sube_ad}': "
                            f"{gun} gününde {len(gruplar)} ayrı blok var "
                            f"(saatler: {saatler_sorted}). Aynı günde tek blok olmalı."
                        ),
                        detay={
                            "ders_id": ders.ders_id,
                            "sube_id": sube_id,
                            "gun": gun,
                            "saatler": saatler_sorted,
                        },
                    ))

    return ihlaller

