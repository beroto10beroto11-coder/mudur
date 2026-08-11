"""
Ön Doğrulama Modülü
===================
Solver çalıştırılmadan önce veri tutarlılığını ve
fiziksel gerçekleşebilirliği kontrol eder.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.solver.scheduler.models import SchedulerInput

from app.solver.scheduler.models import FeasibilityIhlali


def validate_feasibility(inp: "SchedulerInput") -> list[FeasibilityIhlali]:
    """
    İki temel kontrol gerçekleştirir:

    1. Branş/ders bazında öğretmen kapasite kontrolü.
    2. Her şube için toplam haftalık ders saati = toplam okul saati kontrolü.

    Döndürülen liste boşsa ön doğrulama geçmiştir.
    """
    ihlaller: list[FeasibilityIhlali] = []
    ihlaller.extend(_kontrol_ogretmen_kapasite(inp))
    ihlaller.extend(_kontrol_sube_saat_dengesi(inp))
    return ihlaller


# ─────────────────────────────────────────────────────────────────────────────
# 1. Branş/ders bazında kapasite kontrolü
# ─────────────────────────────────────────────────────────────────────────────

def _kontrol_ogretmen_kapasite(inp: "SchedulerInput") -> list[FeasibilityIhlali]:
    """
    Her ders_id için gereken toplam saat = haftalik_saat × ilgili şube sayısı.
    Bu dersi verebilecek (branş + şube izni + müsaitlik) öğretmenlerin
    teorik kapasitesiyle karşılaştırır.

    Not: "teorik kapasite" olarak o öğretmenin o şube için müsait olduğu
    toplam saat sayısını kullanıyoruz (güçlü bir üst sınır; gerçek atama
    sırasında çakışmalar kapasiteyi daha da düşürebilir).
    """
    ihlaller: list[FeasibilityIhlali] = []
    gunler = inp.zaman_yapisi.gunler
    gunluk_saatler = inp.zaman_yapisi.gunluk_ders_saatleri

    for ders in inp.dersler:
        gecerli_subeler = [
            s for s in inp.subeler if s.sube_id in ders.gecerli_sube_ids
        ]
        if not gecerli_subeler:
            continue

        # Her şube için ayrı ayrı kontrol et
        for sube in gecerli_subeler:
            gereken_saat = ders.haftalik_saat

            # Bu ders için bu şubeye girebilecek ve branşı uygun öğretmenler
            uygun_ogretmenler = [
                o for o in inp.ogretmenler
                if ders.kod in o.branslar
                and sube.sube_id in o.girebilecegi_subeler
            ]

            if not uygun_ogretmenler:
                ihlaller.append(FeasibilityIhlali(
                    tur="YETERSIZ_OGRETMEN",
                    mesaj=(
                        f"Ders '{ders.ders_adi}' ({ders.ders_id}), "
                        f"Şube '{sube.ad}' için uygun öğretmen YOK. "
                        f"Branş '{ders.kod}' ve şube izni olan öğretmen bulunamadı."
                    ),
                    detay={
                        "ders_id": ders.ders_id,
                        "sube_id": sube.sube_id,
                        "gereken_saat": gereken_saat,
                        "uygun_ogretmen_sayisi": 0,
                    },
                ))
                continue

            # Teorik toplam kapasite: her uygun öğretmenin bu şube için
            # müsait olduğu saat toplamı
            toplam_kapasite = 0
            ogretmen_kapasiteleri: dict[str, int] = {}
            for o in uygun_ogretmenler:
                kapasite = 0
                for gun_idx, gun in enumerate(gunler):
                    maks_saat = gunluk_saatler[gun_idx]
                    for saat_idx in range(maks_saat):
                        if o.musait_mi(gun, saat_idx):
                            kapasite += 1
                ogretmen_kapasiteleri[o.ogretmen_id] = kapasite
                toplam_kapasite += kapasite

            if toplam_kapasite < gereken_saat:
                ihlaller.append(FeasibilityIhlali(
                    tur="YETERSIZ_OGRETMEN",
                    mesaj=(
                        f"Ders '{ders.ders_adi}' ({ders.ders_id}), "
                        f"Şube '{sube.ad}': "
                        f"Gereken {gereken_saat} saat karşılanamıyor. "
                        f"Toplam öğretmen kapasitesi: {toplam_kapasite} saat "
                        f"({len(uygun_ogretmenler)} öğretmen)."
                    ),
                    detay={
                        "ders_id": ders.ders_id,
                        "sube_id": sube.sube_id,
                        "gereken_saat": gereken_saat,
                        "toplam_kapasite": toplam_kapasite,
                        "ogretmen_kapasiteleri": ogretmen_kapasiteleri,
                    },
                ))

    return ihlaller


# ─────────────────────────────────────────────────────────────────────────────
# 2. Şube–saat dengesi kontrolü
# ─────────────────────────────────────────────────────────────────────────────

def _kontrol_sube_saat_dengesi(inp: "SchedulerInput") -> list[FeasibilityIhlali]:
    """
    Her şube için:
        toplam_ders_saati  =  Σ(ders.haftalik_saat for ders in o şubeye ait dersler)
        okul_toplam_saat   =  Σ(gunluk_ders_saatleri)

    Eşit değilse uyarı üretir (boş saat kalacak veya taşacak).
    """
    ihlaller: list[FeasibilityIhlali] = []
    okul_toplam = inp.zaman_yapisi.toplam_haftalik_saat

    for sube in inp.subeler:
        sube_dersler = [
            d for d in inp.dersler if sube.sube_id in d.gecerli_sube_ids
        ]
        toplam_ders_saati = sum(d.haftalik_saat for d in sube_dersler)

        if toplam_ders_saati != okul_toplam:
            fark = toplam_ders_saati - okul_toplam
            yon = "fazla" if fark > 0 else "eksik"
            ihlaller.append(FeasibilityIhlali(
                tur="SUBE_SAAT_UYUMSUZLUGU",
                mesaj=(
                    f"Şube '{sube.ad}' ({sube.sube_id}): "
                    f"Ders toplamı {toplam_ders_saati} saat, "
                    f"okul haftası {okul_toplam} saat. "
                    f"Fark: {abs(fark)} saat {yon}."
                ),
                detay={
                    "sube_id": sube.sube_id,
                    "toplam_ders_saati": toplam_ders_saati,
                    "okul_toplam_saat": okul_toplam,
                    "fark": fark,
                    "ders_listesi": [
                        {"ders_id": d.ders_id, "haftalik_saat": d.haftalik_saat}
                        for d in sube_dersler
                    ],
                },
            ))

    return ihlaller
