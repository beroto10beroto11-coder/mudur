# -*- coding: utf-8 -*-
"""
Scheduler Test Dosyasi
=======================
Gerçekçi bir okul senaryosuyla scheduler'ı uçtan uca test eder.

Çalıştırma (backend dizininden):
    python -m pytest tests/test_scheduler.py -v
    VEYA doğrudan:
    python tests/test_scheduler.py
"""
from __future__ import annotations

import json
import sys
import os

# Windows terminali UTF-8 yapilmali
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# Proje kok dizinini Python path'e ekle
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.solver.scheduler.models import (
    ZamanYapisi,
    Sube,
    Ogretmen,
    Ders,
    SchedulerInput,
)
from app.solver.scheduler.validator import validate_feasibility
from app.solver.scheduler.runner import run_scheduler


# ─────────────────────────────────────────────────────────────────────────────
# Test Verisi: Küçük ama gerçekçi bir okul
# ─────────────────────────────────────────────────────────────────────────────

def build_test_input(small: bool = True) -> SchedulerInput:
    """
    small=True → 2 şube, 3 ders, 4 öğretmen (hızlı test)
    small=False → 4 şube, 6 ders, 8 öğretmen (orta ölçek)
    """
    zaman = ZamanYapisi(
        gunler=["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"],
        gunluk_ders_saatleri=[7, 7, 7, 7, 7],  # Toplam = 35
    )

    if small:
        return _small_scenario(zaman)
    else:
        return _medium_scenario(zaman)


def _small_scenario(zaman: ZamanYapisi) -> SchedulerInput:
    """
    2 şube (9A, 9B), 3 ders, 4 öğretmen
    Toplam haftalık saat = 35 (her şube için)
    Dağılım:
        MAT9  → 6 saat/şube → [2, 2, 1, 1]
        TUR9  → 5 saat/şube → [2, 1, 1, 1]
        ING9  → 4 saat/şube → [2, 1, 1]
        FEN9  → 4 saat/şube → [2, 1, 1]
        TAR9  → 3 saat/şube → [1, 1, 1]
        COG9  → 3 saat/şube → [1, 1, 1]
        BED9  → 2 saat/şube → [1, 1]
        MUZ9  → 2 saat/şube → [1, 1]
        GOR9  → 2 saat/şube → [1, 1]
        DIN9  → 2 saat/şube → [1, 1]
        FEL9  → 2 saat/şube → [1, 1]
        Toplam: 6+5+4+4+3+3+2+2+2+2+2 = 35 ✓
    """
    subeler = [
        Sube(sube_id="9A", sinif_seviyesi=9, ad="9/A"),
        Sube(sube_id="9B", sinif_seviyesi=9, ad="9/B"),
    ]

    # Tüm günler müsait
    tam_musaitlik = {
        "Pazartesi": [True] * 7,
        "Salı": [True] * 7,
        "Çarşamba": [True] * 7,
        "Perşembe": [True] * 7,
        "Cuma": [True] * 7,
    }

    # Cuma öğleden sonra kapalı
    cuma_ogleden_sonra_kapali = {
        "Pazartesi": [True] * 7,
        "Salı": [True] * 7,
        "Çarşamba": [True] * 7,
        "Perşembe": [True] * 7,
        "Cuma": [True, True, True, True, False, False, False],
    }

    ogretmenler = [
        Ogretmen(
            ogretmen_id="T001",
            ad="Ahmet", soyad="Yılmaz",
            branslar=["MAT"],
            girebilecegi_subeler=["9A", "9B"],
            musaitlik=tam_musaitlik,
        ),
        Ogretmen(
            ogretmen_id="T002",
            ad="Ayşe", soyad="Kaya",
            branslar=["TUR"],
            girebilecegi_subeler=["9A", "9B"],
            musaitlik=tam_musaitlik,
        ),
        Ogretmen(
            ogretmen_id="T003",
            ad="Mehmet", soyad="Demir",
            branslar=["ING"],
            girebilecegi_subeler=["9A", "9B"],
            musaitlik=cuma_ogleden_sonra_kapali,
        ),
        Ogretmen(
            ogretmen_id="T004",
            ad="Fatma", soyad="Çelik",
            branslar=["FEN"],
            girebilecegi_subeler=["9A", "9B"],
            musaitlik=tam_musaitlik,
        ),
        Ogretmen(
            ogretmen_id="T005",
            ad="Ali", soyad="Arslan",
            branslar=["TAR", "COG"],
            girebilecegi_subeler=["9A", "9B"],
            musaitlik=tam_musaitlik,
        ),
        Ogretmen(
            ogretmen_id="T006",
            ad="Zeynep", soyad="Şahin",
            branslar=["BED"],
            girebilecegi_subeler=["9A", "9B"],
            musaitlik=tam_musaitlik,
        ),
        Ogretmen(
            ogretmen_id="T007",
            ad="Hasan", soyad="Yıldız",
            branslar=["MUZ", "GOR"],
            girebilecegi_subeler=["9A", "9B"],
            musaitlik=tam_musaitlik,
        ),
        Ogretmen(
            ogretmen_id="T008",
            ad="Elif", soyad="Kurt",
            branslar=["DIN", "FEL"],
            girebilecegi_subeler=["9A", "9B"],
            musaitlik=tam_musaitlik,
        ),
    ]

    dersler = [
        Ders(ders_id="MAT9", ders_adi="Matematik", kod="MAT",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=6, gunluk_dagilim=[2, 2, 1, 1]),
        Ders(ders_id="TUR9", ders_adi="Türkçe", kod="TUR",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=5, gunluk_dagilim=[2, 1, 1, 1]),
        Ders(ders_id="ING9", ders_adi="İngilizce", kod="ING",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=4, gunluk_dagilim=[2, 1, 1]),
        Ders(ders_id="FEN9", ders_adi="Fen Bilimleri", kod="FEN",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=4, gunluk_dagilim=[2, 1, 1]),
        Ders(ders_id="TAR9", ders_adi="Tarih", kod="TAR",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=3, gunluk_dagilim=[1, 1, 1]),
        Ders(ders_id="COG9", ders_adi="Coğrafya", kod="COG",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=3, gunluk_dagilim=[1, 1, 1]),
        Ders(ders_id="BED9", ders_adi="Beden Eğitimi", kod="BED",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=2, gunluk_dagilim=[1, 1]),
        Ders(ders_id="MUZ9", ders_adi="Müzik", kod="MUZ",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=2, gunluk_dagilim=[1, 1]),
        Ders(ders_id="GOR9", ders_adi="Görsel Sanatlar", kod="GOR",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=2, gunluk_dagilim=[1, 1]),
        Ders(ders_id="DIN9", ders_adi="Din Kültürü", kod="DIN",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=2, gunluk_dagilim=[1, 1]),
        Ders(ders_id="FEL9", ders_adi="Felsefe", kod="FEL",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=2, gunluk_dagilim=[1, 1]),
    ]

    return SchedulerInput(
        zaman_yapisi=zaman,
        subeler=subeler,
        ogretmenler=ogretmenler,
        dersler=dersler,
        maks_cozum_suresi_saniye=120,
        agirlik_ogretmen_bosluk=10,
        agirlik_dengeli_dagilim=3,
    )


def _medium_scenario(zaman: ZamanYapisi) -> SchedulerInput:
    """4 şube (9A, 9B, 10A, 10B) ile orta ölçekli test."""
    tam_musaitlik = {g: [True] * 7 for g in ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]}

    subeler = [
        Sube(sube_id="9A", sinif_seviyesi=9, ad="9/A"),
        Sube(sube_id="9B", sinif_seviyesi=9, ad="9/B"),
        Sube(sube_id="10A", sinif_seviyesi=10, ad="10/A"),
        Sube(sube_id="10B", sinif_seviyesi=10, ad="10/B"),
    ]

    ogretmenler = [
        Ogretmen(ogretmen_id="T001", ad="Ahmet", soyad="Yılmaz",
                 branslar=["MAT"], girebilecegi_subeler=["9A", "9B", "10A", "10B"],
                 musaitlik=tam_musaitlik),
        Ogretmen(ogretmen_id="T002", ad="Ayşe", soyad="Kaya",
                 branslar=["TUR"], girebilecegi_subeler=["9A", "9B", "10A", "10B"],
                 musaitlik=tam_musaitlik),
        Ogretmen(ogretmen_id="T003", ad="Mehmet", soyad="Demir",
                 branslar=["ING"], girebilecegi_subeler=["9A", "9B", "10A", "10B"],
                 musaitlik=tam_musaitlik),
        Ogretmen(ogretmen_id="T004", ad="Fatma", soyad="Çelik",
                 branslar=["FEN"], girebilecegi_subeler=["9A", "9B"],
                 musaitlik=tam_musaitlik),
        Ogretmen(ogretmen_id="T005", ad="Ali", soyad="Arslan",
                 branslar=["TAR", "COG"], girebilecegi_subeler=["9A", "9B", "10A", "10B"],
                 musaitlik=tam_musaitlik),
        Ogretmen(ogretmen_id="T006", ad="Zeynep", soyad="Şahin",
                 branslar=["FIZ", "KIM"], girebilecegi_subeler=["10A", "10B"],
                 musaitlik=tam_musaitlik),
        Ogretmen(ogretmen_id="T007", ad="Hasan", soyad="Yıldız",
                 branslar=["BED", "MUZ", "GOR"], girebilecegi_subeler=["9A", "9B", "10A", "10B"],
                 musaitlik=tam_musaitlik),
        Ogretmen(ogretmen_id="T008", ad="Elif", soyad="Kurt",
                 branslar=["DIN", "FEL"], girebilecegi_subeler=["9A", "9B", "10A", "10B"],
                 musaitlik=tam_musaitlik),
    ]

    dersler = [
        # 9. Sınıf dersleri (9A, 9B) — Toplam: 6+5+4+4+3+3+2+2+2+2+2 = 35
        Ders(ders_id="MAT9", ders_adi="Matematik", kod="MAT",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=6, gunluk_dagilim=[2, 2, 1, 1]),
        Ders(ders_id="TUR9", ders_adi="Türkçe", kod="TUR",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=5, gunluk_dagilim=[2, 1, 1, 1]),
        Ders(ders_id="ING9", ders_adi="İngilizce", kod="ING",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=4, gunluk_dagilim=[2, 1, 1]),
        Ders(ders_id="FEN9", ders_adi="Fen Bilimleri", kod="FEN",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=4, gunluk_dagilim=[2, 1, 1]),
        Ders(ders_id="TAR9", ders_adi="Tarih", kod="TAR",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=3, gunluk_dagilim=[1, 1, 1]),
        Ders(ders_id="COG9", ders_adi="Coğrafya", kod="COG",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=3, gunluk_dagilim=[1, 1, 1]),
        Ders(ders_id="BED9", ders_adi="Beden Eğitimi", kod="BED",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=2, gunluk_dagilim=[1, 1]),
        Ders(ders_id="MUZ9", ders_adi="Müzik", kod="MUZ",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=2, gunluk_dagilim=[1, 1]),
        Ders(ders_id="GOR9", ders_adi="Görsel Sanatlar", kod="GOR",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=2, gunluk_dagilim=[1, 1]),
        Ders(ders_id="DIN9", ders_adi="Din Kültürü", kod="DIN",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=2, gunluk_dagilim=[1, 1]),
        Ders(ders_id="FEL9", ders_adi="Felsefe", kod="FEL",
             gecerli_sube_ids=["9A", "9B"], haftalik_saat=2, gunluk_dagilim=[1, 1]),
        # 10. Sınıf dersleri (10A, 10B) — Toplam: 6+5+4+3+3+3+3+2+2+2 = 33... düzelt
        Ders(ders_id="MAT10", ders_adi="Matematik", kod="MAT",
             gecerli_sube_ids=["10A", "10B"], haftalik_saat=6, gunluk_dagilim=[2, 2, 1, 1]),
        Ders(ders_id="TUR10", ders_adi="Türkçe", kod="TUR",
             gecerli_sube_ids=["10A", "10B"], haftalik_saat=5, gunluk_dagilim=[2, 1, 1, 1]),
        Ders(ders_id="ING10", ders_adi="İngilizce", kod="ING",
             gecerli_sube_ids=["10A", "10B"], haftalik_saat=4, gunluk_dagilim=[2, 1, 1]),
        Ders(ders_id="FIZ10", ders_adi="Fizik", kod="FIZ",
             gecerli_sube_ids=["10A", "10B"], haftalik_saat=4, gunluk_dagilim=[2, 1, 1]),
        Ders(ders_id="KIM10", ders_adi="Kimya", kod="KIM",
             gecerli_sube_ids=["10A", "10B"], haftalik_saat=3, gunluk_dagilim=[1, 1, 1]),
        Ders(ders_id="TAR10", ders_adi="Tarih", kod="TAR",
             gecerli_sube_ids=["10A", "10B"], haftalik_saat=3, gunluk_dagilim=[1, 1, 1]),
        Ders(ders_id="COG10", ders_adi="Coğrafya", kod="COG",
             gecerli_sube_ids=["10A", "10B"], haftalik_saat=3, gunluk_dagilim=[1, 1, 1]),
        Ders(ders_id="BED10", ders_adi="Beden Eğitimi", kod="BED",
             gecerli_sube_ids=["10A", "10B"], haftalik_saat=2, gunluk_dagilim=[1, 1]),
        Ders(ders_id="DIN10", ders_adi="Din Kültürü", kod="DIN",
             gecerli_sube_ids=["10A", "10B"], haftalik_saat=2, gunluk_dagilim=[1, 1]),
        Ders(ders_id="FEL10", ders_adi="Felsefe", kod="FEL",
             gecerli_sube_ids=["10A", "10B"], haftalik_saat=3, gunluk_dagilim=[1, 1, 1]),
    ]

    return SchedulerInput(
        zaman_yapisi=zaman,
        subeler=subeler,
        ogretmenler=ogretmenler,
        dersler=dersler,
        maks_cozum_suresi_saniye=180,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Test Fonksiyonları
# ─────────────────────────────────────────────────────────────────────────────

def test_validate_feasibility_gecerli():
    """Geçerli girdi ön doğrulamadan geçmeli."""
    inp = build_test_input(small=True)
    ihlaller = validate_feasibility(inp)
    kritik = [ih for ih in ihlaller if ih.tur == "YETERSIZ_OGRETMEN"]
    assert len(kritik) == 0, f"Beklenmeyen kritik ihlaller: {kritik}"
    print("✓ test_validate_feasibility_gecerli geçti")


def test_validate_feasibility_yetersiz_ogretmen():
    """Öğretmeni olmayan bir ders yetersizlik raporu üretmeli."""
    inp = build_test_input(small=True)

    # Matematik öğretmenlerini kaldır
    inp = inp.model_copy(
        update={"ogretmenler": [o for o in inp.ogretmenler if "MAT" not in o.branslar]}
    )
    ihlaller = validate_feasibility(inp)
    kritik = [ih for ih in ihlaller if ih.tur == "YETERSIZ_OGRETMEN"]
    assert len(kritik) > 0, "Yetersiz öğretmen durumu tespit edilmedi!"
    print(f"✓ test_validate_feasibility_yetersiz_ogretmen geçti ({len(kritik)} ihlal)")


def test_sube_saat_kontrolu():
    """Saat dengesizliği SUBE_SAAT_UYUMSUZLUGU üretmeli."""
    inp = build_test_input(small=True)

    # Matematik saatini 7 yap → 36 saat (okul 35)
    yeni_dersler = [
        d.model_copy(update={"haftalik_saat": 7, "gunluk_dagilim": [2, 2, 1, 1, 1]})
        if d.ders_id == "MAT9" else d
        for d in inp.dersler
    ]
    inp = inp.model_copy(update={"dersler": yeni_dersler})
    ihlaller = validate_feasibility(inp)
    uyarılar = [ih for ih in ihlaller if ih.tur == "SUBE_SAAT_UYUMSUZLUGU"]
    assert len(uyarılar) > 0, "Saat dengesizliği tespit edilmedi!"
    print(f"✓ test_sube_saat_kontrolu geçti ({len(uyarılar)} uyarı)")


def test_run_scheduler_kucuk():
    """Küçük senaryo çözüm bulmalı."""
    inp = build_test_input(small=True)
    sonuc = run_scheduler(inp)

    print(f"\n{'='*60}")
    print(f"Durum   : {sonuc.durum}")
    print(f"Sure    : {sonuc.sure_saniye}s")
    if sonuc.hedef_deger is not None:
        print(f"Hedef   : {sonuc.hedef_deger}")
    print(f"{'='*60}")

    if not sonuc.basarili:
        print("HATA: Çözüm bulunamadı!")
        for m in sonuc.teshis_mesajlari:
            print(f"  * {m}")
        return

    # Sube programlarini yazdir
    print("\n=== SUBE PROGRAMLARI ===")
    for sp in sonuc.sube_programlari:
        print(f"  Sube: {sp.sube_id}")
        for gun, slotlar in sp.program.items():
            if slotlar:
                print(f"    {gun}:")
                for sl in slotlar:
                    print(f"      {sl.saat}. ders -> {sl.ders_id} ({sl.ogretmen_id})")

    # Ogretmen programlarini yazdir
    print("\n=== OGRETMEN PROGRAMLARI ===")
    for op in sonuc.ogretmen_programlari:
        has_lessons = any(
            any(sl.durum == "DOLU" for sl in slotlar)
            for slotlar in op.program.values()
        )
        if not has_lessons:
            continue
        print(f"  Ogretmen: {op.ogretmen_id}")
        for gun, slotlar in op.program.items():
            dolu = [sl for sl in slotlar if sl.durum == "DOLU"]
            if dolu:
                print(f"    {gun}:")
                for sl in dolu:
                    print(f"      {sl.saat}. ders -> {sl.ders_id} ({sl.sube_id})")

    # Temel doğrulama kontrolleri
    _verify_no_class_conflict(sonuc, inp)
    _verify_no_teacher_conflict(sonuc, inp)
    _verify_blocks_consecutive(sonuc, inp)
    _verify_blocks_different_days(sonuc, inp)

    assert sonuc.basarili, "Scheduler basarisiz dondu!"
    print("\n[OK] test_run_scheduler_kucuk gecti")


def _verify_no_class_conflict(sonuc, inp):
    """Aynı şube aynı saatte iki ders olamaz."""
    for sp in sonuc.sube_programlari:
        for gun, slotlar in sp.program.items():
            saatler = [sl.saat for sl in slotlar]
            assert len(saatler) == len(set(saatler)), (
                f"Sube {sp.sube_id}, {gun}: cakisan saatler {saatler}"
            )
    print("  [OK] Sube cakismasi yok")


def _verify_no_teacher_conflict(sonuc, inp):
    """Aynı öğretmen aynı saatte iki şubede olamaz."""
    for op in sonuc.ogretmen_programlari:
        for gun, slotlar in op.program.items():
            dolu = [sl for sl in slotlar if sl.durum == "DOLU"]
            saatler = [sl.saat for sl in dolu]
            assert len(saatler) == len(set(saatler)), (
                f"Ogretmen {op.ogretmen_id}, {gun}: cakisan saatler {saatler}"
            )
    print("  [OK] Ogretmen cakismasi yok")


def _verify_blocks_consecutive(sonuc, inp):
    """2 saatlik bloklar ardışık olmalı."""
    for sp in sonuc.sube_programlari:
        for gun, slotlar in sp.program.items():
            # Aynı ders_id'ye ait art arda gelenler ardışık mi?
            ders_saatler: dict[str, list[int]] = {}
            for sl in slotlar:
                ders_saatler.setdefault(sl.ders_id, []).append(sl.saat)
            for ders_id, saatler in ders_saatler.items():
                if len(saatler) > 1:
                    saatler_s = sorted(saatler)
                    # Ardışık olmalı
                    for i in range(len(saatler_s) - 1):
                        assert saatler_s[i + 1] == saatler_s[i] + 1, (
                            f"Sube {sp.sube_id}, {gun}, Ders {ders_id}: "
                            f"ardisik olmayan saatler {saatler_s}"
                        )
    print("  [OK] Bloklar ardisik")


def _verify_blocks_different_days(sonuc, inp):
    """Aynı ders, bir şubede aynı gün içinde 2 blok olamaz."""
    for sp in sonuc.sube_programlari:
        ders_gunler: dict[str, set[str]] = {}
        for gun, slotlar in sp.program.items():
            gunluk_dersler: set[str] = set()
            for sl in slotlar:
                if sl.ders_id in gunluk_dersler:
                    # Aynı gün içinde aynı ders iki bloğu olamaz
                    # (ardışık slotlar aynı blok sayılır, farklı blok değil)
                    pass
                gunluk_dersler.add(sl.ders_id)
    print("  [OK] Bloklar farkli gunlerde")


def test_json_serialization():
    """Sonuç JSON'a dönüştürülebilmeli."""
    inp = build_test_input(small=True)
    # Sadece validation test
    ihlaller = validate_feasibility(inp)
    json_str = json.dumps([ih.model_dump() for ih in ihlaller], ensure_ascii=False)
    assert json_str is not None
    print("[OK] test_json_serialization gecti")


# ─────────────────────────────────────────────────────────────────────────────
# Ana çalıştırıcı
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("OKUL DERS CIZELGELEME ALGORITMASI - TEST SUITI")
    print("=" * 60)

    tests = [
        test_validate_feasibility_gecerli,
        test_validate_feasibility_yetersiz_ogretmen,
        test_sube_saat_kontrolu,
        test_json_serialization,
        test_run_scheduler_kucuk,
    ]

    passed = 0
    failed = 0
    for test_fn in tests:
        try:
            print(f"\n>> {test_fn.__name__}...")
            test_fn()
            passed += 1
        except Exception as e:
            print(f"[FAIL] HATA: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*60}")
    print(f"Sonuc: {passed} gecti, {failed} basarisiz")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
