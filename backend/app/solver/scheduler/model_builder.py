"""
CP-SAT Model Kurulum Modülü
============================
Karar değişkenlerini, sert ve yumuşak kısıtları tanımlar.

Değişken şeması:
    x[ders_id, sube_id, blok_idx, gun_idx, baslangic_saat_idx]
        = 1 → bu blok bu gün bu saatten başlıyor

    y[ders_id, sube_id, blok_idx, ogretmen_id]
        = 1 → bu bloğu bu öğretmen veriyor
"""
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from ortools.sat.python import cp_model

if TYPE_CHECKING:
    from app.solver.scheduler.models import SchedulerInput

# ─────────────────────────────────────────────────────────────────────────────
# Ağırlıklar (Soft Constraints)
# ─────────────────────────────────────────────────────────────────────────────
# Bu değerler SchedulerInput üzerinden dışarıdan ezilebilir.
WEIGHT_TEACHER_GAP: int = 10      # Öğretmen günlük boşluk ceza ağırlığı
WEIGHT_LOAD_BALANCE: int = 3      # Günlük yük dengesi ceza ağırlığı


# ─────────────────────────────────────────────────────────────────────────────
# Yardımcı: gün × saat → (gün_idx, saat_idx) arama yapısı
# ─────────────────────────────────────────────────────────────────────────────

def _build_slot_index(inp: "SchedulerInput") -> dict[tuple[int, int], bool]:
    """(gun_idx, saat_idx) → True sözlüğü; geçerli zaman dilimlerini listeler."""
    slots: dict[tuple[int, int], bool] = {}
    for g_idx, maks in enumerate(inp.zaman_yapisi.gunluk_ders_saatleri):
        for s_idx in range(maks):
            slots[(g_idx, s_idx)] = True
    return slots


# ─────────────────────────────────────────────────────────────────────────────
# Ana model kurulum fonksiyonu
# ─────────────────────────────────────────────────────────────────────────────

def build_model(
    inp: "SchedulerInput",
    model: cp_model.CpModel,
) -> tuple[dict, dict]:
    """
    CP-SAT modelini kurar.

    Döndürür:
        x_vars: {(ders_id, sube_id, blok_idx, gun_idx, saat_idx): BoolVar}
        y_vars: {(ders_id, sube_id, blok_idx, ogretmen_id): BoolVar}
    """
    gunler = inp.zaman_yapisi.gunler
    gun_saatleri = inp.zaman_yapisi.gunluk_ders_saatleri
    num_gunler = len(gunler)

    # ─── 1. Karar Değişkenlerini Oluştur ─────────────────────────────────────
    x_vars: dict[tuple, cp_model.BoolVar] = {}
    y_vars: dict[tuple, cp_model.BoolVar] = {}

    for ders in inp.dersler:
        for sube_id in ders.gecerli_sube_ids:
            # Şubenin gerçekten var olduğunu doğrula
            sube_var = next(
                (s for s in inp.subeler if s.sube_id == sube_id), None
            )
            if sube_var is None:
                continue

            # Bu (ders, sube) için hangi öğretmenler uygun?
            uygun_ogretmenler = [
                o for o in inp.ogretmenler
                if ders.kod in o.branslar
                and sube_id in o.girebilecegi_subeler
            ]

            for blok_idx, blok_uzunluk in enumerate(ders.gunluk_dagilim):
                # x değişkenleri: olası (gun, baslangic_saat) kombinasyonları
                for g_idx in range(num_gunler):
                    maks_saat = gun_saatleri[g_idx]
                    # blok_uzunluk saatlik blok; son olası başlangıç saati
                    son_baslangic = maks_saat - blok_uzunluk
                    for s_idx in range(son_baslangic + 1):
                        key = (ders.ders_id, sube_id, blok_idx, g_idx, s_idx)
                        x_vars[key] = model.new_bool_var(
                            f"x_d{ders.ders_id}_s{sube_id}_b{blok_idx}"
                            f"_g{g_idx}_t{s_idx}"
                        )

                # y değişkenleri: hangi öğretmen bu bloğu veriyor
                for o in uygun_ogretmenler:
                    key = (ders.ders_id, sube_id, blok_idx, o.ogretmen_id)
                    y_vars[key] = model.new_bool_var(
                        f"y_d{ders.ders_id}_s{sube_id}_b{blok_idx}"
                        f"_o{o.ogretmen_id}"
                    )

    # ─── 2. Sert Kısıtları Ekle ───────────────────────────────────────────────
    _add_hard_constraints(model, inp, x_vars, y_vars)

    # ─── 3. Yumuşak Kısıtları Ekle (Amaç Fonksiyonu) ─────────────────────────
    _add_soft_objectives(model, inp, x_vars, y_vars)

    return x_vars, y_vars


# ─────────────────────────────────────────────────────────────────────────────
# SERT KISITLAR
# ─────────────────────────────────────────────────────────────────────────────

def _add_hard_constraints(
    model: cp_model.CpModel,
    inp: "SchedulerInput",
    x_vars: dict,
    y_vars: dict,
) -> None:
    gunler = inp.zaman_yapisi.gunler
    gun_saatleri = inp.zaman_yapisi.gunluk_ders_saatleri
    num_gunler = len(gunler)

    # C1: Her blok tam olarak bir (gun, saat) konumuna atanmalı
    _c1_blok_tam_atama(model, inp, x_vars, gunler, gun_saatleri, num_gunler)

    # C2: Her blok tam olarak bir öğretmene atanmalı
    _c2_ogretmen_secimi(model, inp, x_vars, y_vars, gunler, gun_saatleri, num_gunler)

    # C3: Öğretmen müsaitlik kısıtı
    _c3_ogretmen_musaitlik(model, inp, x_vars, y_vars, gunler, gun_saatleri)

    # C4: Şube çakışma yok
    _c4_sube_cakisma_yok(model, inp, x_vars, gunler, gun_saatleri, num_gunler)

    # C5: Öğretmen çakışma yok
    _c5_ogretmen_cakisma_yok(model, inp, x_vars, y_vars, gunler, gun_saatleri, num_gunler)

    # C6: Aynı dersin blokları farklı günlerde olmalı
    _c6_bloklar_farkli_gun(model, inp, x_vars, num_gunler)

    # C7: Öğretmen yalnızca branşı ve izinli şubeleri için y=1 olabilir
    # (y_vars oluşturulurken zaten filtrelendi; ancak x ile bağ kurulmalı)
    # Bu kısıt C2 içinde zaten sağlanıyor.


def _c1_blok_tam_atama(
    model, inp, x_vars, gunler, gun_saatleri, num_gunler
):
    """
    Her (ders, sube, blok) üçlüsü tam olarak 1 (gun, baslangic_saat) almalı.
    """
    for ders in inp.dersler:
        for sube_id in ders.gecerli_sube_ids:
            sube_obj = next(
                (s for s in inp.subeler if s.sube_id == sube_id), None
            )
            if sube_obj is None:
                continue
            for blok_idx, blok_uzunluk in enumerate(ders.gunluk_dagilim):
                blok_x = [
                    x_vars[(ders.ders_id, sube_id, blok_idx, g, s)]
                    for g in range(num_gunler)
                    for s in range(gun_saatleri[g] - blok_uzunluk + 1)
                    if (ders.ders_id, sube_id, blok_idx, g, s) in x_vars
                ]
                if blok_x:
                    model.add(sum(blok_x) == 1)


def _c2_ogretmen_secimi(
    model, inp, x_vars, y_vars, gunler, gun_saatleri, num_gunler
):
    """
    Her (ders, sube, blok) için:
    1. Tam olarak 1 öğretmen seçilmeli.
    2. x=1 olduğunda, seçilen öğretmen o saatlerde müsait olmalı (y ile bağlantı).
    """
    for ders in inp.dersler:
        for sube_id in ders.gecerli_sube_ids:
            sube_obj = next(
                (s for s in inp.subeler if s.sube_id == sube_id), None
            )
            if sube_obj is None:
                continue

            uygun_ogretmenler = [
                o for o in inp.ogretmenler
                if ders.kod in o.branslar
                and sube_id in o.girebilecegi_subeler
            ]

            for blok_idx in range(len(ders.gunluk_dagilim)):
                y_blok = [
                    y_vars[(ders.ders_id, sube_id, blok_idx, o.ogretmen_id)]
                    for o in uygun_ogretmenler
                    if (ders.ders_id, sube_id, blok_idx, o.ogretmen_id) in y_vars
                ]
                if y_blok:
                    model.add(sum(y_blok) == 1)
                else:
                    # Hiç uygun öğretmen yok → bu blok atanamazdı
                    # (validator bunu yakalamalıydı; yine de x=0 zorla)
                    blok_x = [
                        x_vars[k] for k in x_vars
                        if k[0] == ders.ders_id and k[1] == sube_id and k[2] == blok_idx
                    ]
                    for xv in blok_x:
                        model.add(xv == 0)


def _c3_ogretmen_musaitlik(
    model, inp, x_vars, y_vars, gunler, gun_saatleri
):
    """
    Öğretmen y[...,o]=1 olduğunda, blok yerleştiği tüm saatlerde müsait
    olmak zorunda.

    Lineer formülasyon:
        Σ_s  x[d,sub,b,g,s] * (s_saatleri kapsar saat h ama o müsait değil) == 0
        ↔
        Öğretmen müsait olmadığı saatlere atandığı x değişkenlerinin
        y ile çarpımı 0.

    Yaklaşım: her (blok, gun, baslangic_saat) için, öğretmen bu blokta
    o günde müsait değilse  x ∧ y → 0  booleans ile zorluyoruz.
    """
    num_gunler = len(gunler)

    for ders in inp.dersler:
        for sube_id in ders.gecerli_sube_ids:
            sube_obj = next(
                (s for s in inp.subeler if s.sube_id == sube_id), None
            )
            if sube_obj is None:
                continue

            uygun_ogretmenler = [
                o for o in inp.ogretmenler
                if ders.kod in o.branslar
                and sube_id in o.girebilecegi_subeler
            ]

            for blok_idx, blok_uzunluk in enumerate(ders.gunluk_dagilim):
                for o in uygun_ogretmenler:
                    y_key = (ders.ders_id, sube_id, blok_idx, o.ogretmen_id)
                    if y_key not in y_vars:
                        continue
                    y_var = y_vars[y_key]

                    for g in range(num_gunler):
                        gun_adi = gunler[g]
                        maks = gun_saatleri[g]
                        for s in range(maks - blok_uzunluk + 1):
                            x_key = (ders.ders_id, sube_id, blok_idx, g, s)
                            if x_key not in x_vars:
                                continue
                            x_var = x_vars[x_key]

                            # Tüm saat dilimlerinde müsaitlik kontrol
                            for offset in range(blok_uzunluk):
                                saat_idx = s + offset
                                if not o.musait_mi(gun_adi, saat_idx):
                                    # x_var=1 ∧ y_var=1 imkânsız
                                    model.add(x_var + y_var <= 1)
                                    break


def _c4_sube_cakisma_yok(
    model, inp, x_vars, gunler, gun_saatleri, num_gunler
):
    """
    Aynı şube, aynı (gun, saat) diliminde en fazla 1 derste olabilir.
    Blok boyutu 2 ise, başlangıç saati ve başlangıç+1 saati kaplanır.
    """
    for sube_id in [s.sube_id for s in inp.subeler]:
        for g in range(num_gunler):
            for h in range(gun_saatleri[g]):  # h = saat index (0-tabanlı)
                kaplayan_x = []

                for ders in inp.dersler:
                    if sube_id not in ders.gecerli_sube_ids:
                        continue
                    for blok_idx, blok_uzunluk in enumerate(ders.gunluk_dagilim):
                        # Bu bloğun h saatini kaplaması için:
                        # baslangic_saat <= h < baslangic_saat + blok_uzunluk
                        for s in range(max(0, h - blok_uzunluk + 1), h + 1):
                            if s + blok_uzunluk - 1 >= gun_saatleri[g]:
                                continue
                            key = (ders.ders_id, sube_id, blok_idx, g, s)
                            if key in x_vars:
                                kaplayan_x.append(x_vars[key])

                if len(kaplayan_x) > 1:
                    model.add(sum(kaplayan_x) <= 1)


def _c5_ogretmen_cakisma_yok(
    model, inp, x_vars, y_vars, gunler, gun_saatleri, num_gunler
):
    """
    Aynı öğretmen, aynı (gun, saat) diliminde en fazla 1 şubede/derste olabilir.
    x ∧ y birlikte "öğretmen o günde o saatte bu dersi veriyor" anlamına gelir.
    Yardımcı bool değişken: z[ders,sube,blok,ogretmen,gun,saat] = x ∧ y
    """
    for o in inp.ogretmenler:
        for g in range(num_gunler):
            for h in range(gun_saatleri[g]):
                # Bu saatte bu öğretmeni kullanan tüm z değişkenleri
                z_list = []

                for ders in inp.dersler:
                    y_key_base = (ders.ders_id,)
                    uygun = (
                        ders.kod in o.branslar
                    )
                    if not uygun:
                        continue

                    for sube_id in ders.gecerli_sube_ids:
                        if sube_id not in o.girebilecegi_subeler:
                            continue

                        for blok_idx, blok_uzunluk in enumerate(ders.gunluk_dagilim):
                            y_key = (ders.ders_id, sube_id, blok_idx, o.ogretmen_id)
                            if y_key not in y_vars:
                                continue
                            y_var = y_vars[y_key]

                            # h saatini kaplayan başlangıç saatleri
                            for s in range(max(0, h - blok_uzunluk + 1), h + 1):
                                if s + blok_uzunluk - 1 >= gun_saatleri[g]:
                                    continue
                                x_key = (ders.ders_id, sube_id, blok_idx, g, s)
                                if x_key not in x_vars:
                                    continue
                                x_var = x_vars[x_key]

                                z_name = (
                                    f"z_o{o.ogretmen_id}_d{ders.ders_id}"
                                    f"_s{sube_id}_b{blok_idx}_g{g}_t{h}_st{s}"
                                )
                                z = model.new_bool_var(z_name)
                                # z = x_var AND y_var
                                model.add_bool_and([x_var, y_var]).only_enforce_if(z)
                                model.add_bool_or([x_var.negated(), y_var.negated()]).only_enforce_if(z.negated())
                                z_list.append(z)

                if len(z_list) > 1:
                    model.add(sum(z_list) <= 1)


def _c6_bloklar_farkli_gun(model, inp, x_vars, num_gunler):
    """
    Aynı (ders, sube) çiftinin farklı blokları aynı güne düşemez.
    Her gün için, o günde atanan blok sayısı ≤ 1.
    """
    for ders in inp.dersler:
        for sube_id in ders.gecerli_sube_ids:
            sube_obj = next(
                (s for s in inp.subeler if s.sube_id == sube_id), None
            )
            if sube_obj is None:
                continue

            for g in range(num_gunler):
                # Bu gündeki tüm blokların x değişkenleri
                gun_blok_x = []
                for blok_idx in range(len(ders.gunluk_dagilim)):
                    blok_x = [
                        x_vars[k]
                        for k in x_vars
                        if (
                            k[0] == ders.ders_id
                            and k[1] == sube_id
                            and k[2] == blok_idx
                            and k[3] == g
                        )
                    ]
                    gun_blok_x.extend(blok_x)

                if len(gun_blok_x) > 1:
                    model.add(sum(gun_blok_x) <= 1)


# ─────────────────────────────────────────────────────────────────────────────
# YUMUŞAK KISITLAR (Amaç Fonksiyonu)
# ─────────────────────────────────────────────────────────────────────────────

def _add_soft_objectives(
    model: cp_model.CpModel,
    inp: "SchedulerInput",
    x_vars: dict,
    y_vars: dict,
) -> None:
    """
    Minimize edilecek ceza toplamı:
    1. Öğretmen günlük boşluk (pencere) cezası.
    2. Günlük yük dengesi cezası.

    Genişletilebilirlik: ileride öğretmen tercih saatleri buraya eklenebilir.
    """
    gunler = inp.zaman_yapisi.gunler
    gun_saatleri = inp.zaman_yapisi.gunluk_ders_saatleri
    num_gunler = len(gunler)
    W_GAP = inp.agirlik_ogretmen_bosluk
    W_BAL = inp.agirlik_dengeli_dagilim

    penalties = []

    # ─── Öğretmen günlük boşluk minimizasyonu ────────────────────────────────
    # Bir öğretmenin o günkü ilk ve son dersi arasındaki boş saatler.
    # Yaklaşım: Bitişik olmayan saat çiftlerinde (s1 dolu, s2 boş, s3 dolu)
    # "gap" değişkeni tanımla.
    for o in inp.ogretmenler:
        for g in range(num_gunler):
            gun_adi = gunler[g]
            maks = gun_saatleri[g]

            # Bu öğretmenin bu gündeki aktivite değişkenleri
            # active[h] = bu öğretmen bu gün h saatinde ders veriyor mu?
            active: dict[int, list[cp_model.BoolVar]] = {
                h: [] for h in range(maks)
            }

            for ders in inp.dersler:
                if ders.kod not in o.branslar:
                    continue
                for sube_id in ders.gecerli_sube_ids:
                    if sube_id not in o.girebilecegi_subeler:
                        continue
                    for blok_idx, blok_uzunluk in enumerate(ders.gunluk_dagilim):
                        y_key = (ders.ders_id, sube_id, blok_idx, o.ogretmen_id)
                        if y_key not in y_vars:
                            continue
                        y_var = y_vars[y_key]

                        for s in range(maks - blok_uzunluk + 1):
                            x_key = (ders.ders_id, sube_id, blok_idx, g, s)
                            if x_key not in x_vars:
                                continue
                            x_var = x_vars[x_key]

                            # Bu blok h saatini kaplıyorsa
                            for offset in range(blok_uzunluk):
                                h = s + offset
                                if h < maks:
                                    # z = x AND y (öğretmen bu saatte aktif)
                                    z_name = (
                                        f"soft_z_o{o.ogretmen_id}_d{ders.ders_id}"
                                        f"_s{sube_id}_b{blok_idx}_g{g}_st{s}_h{h}"
                                    )
                                    z = model.new_bool_var(z_name)
                                    model.add_bool_and([x_var, y_var]).only_enforce_if(z)
                                    model.add_bool_or(
                                        [x_var.negated(), y_var.negated()]
                                    ).only_enforce_if(z.negated())
                                    active[h].append(z)

            # active_any[h] = OR(active[h])
            active_any: dict[int, cp_model.BoolVar] = {}
            for h in range(maks):
                if active[h]:
                    a = model.new_bool_var(f"active_o{o.ogretmen_id}_g{g}_h{h}")
                    model.add_bool_or(active[h]).only_enforce_if(a)
                    model.add(sum(active[h]) == 0).only_enforce_if(a.negated())
                    active_any[h] = a

            # gap_h = active[h-1] AND NOT active[h] AND active[h+1]
            # → boş "pencere" saati
            for h in range(1, maks - 1):
                if h - 1 in active_any and h in active_any and h + 1 in active_any:
                    gap = model.new_bool_var(
                        f"gap_o{o.ogretmen_id}_g{g}_h{h}"
                    )
                    prev_a = active_any[h - 1]
                    curr_a = active_any[h]
                    next_a = active_any[h + 1]
                    # gap == 1 ↔ prev=1 ∧ curr=0 ∧ next=1
                    model.add_bool_and(
                        [prev_a, curr_a.negated(), next_a]
                    ).only_enforce_if(gap)
                    model.add_bool_or(
                        [prev_a.negated(), curr_a, next_a.negated()]
                    ).only_enforce_if(gap.negated())
                    penalties.append(gap * W_GAP)

    # ─── Günlük yük dengesi ───────────────────────────────────────────────────
    # Her şube için, günlük ders saatleri mümkün olduğunca eşit dağılsın.
    # Ceza: max_gunluk - min_gunluk > 0 ise ceza uygula.
    # Basit yaklaşım: her gün için şubenin toplam ders saatini hesapla,
    # ardışık günler arasındaki farkı cezalandır.
    for sube in inp.subeler:
        sube_id = sube.sube_id
        gun_toplamlar: list[cp_model.IntVar] = []

        for g in range(num_gunler):
            toplam = model.new_int_var(0, gun_saatleri[g], f"sube_load_{sube_id}_g{g}")
            kaplayan = []

            for ders in inp.dersler:
                if sube_id not in ders.gecerli_sube_ids:
                    continue
                for blok_idx, blok_uzunluk in enumerate(ders.gunluk_dagilim):
                    for s in range(gun_saatleri[g] - blok_uzunluk + 1):
                        x_key = (ders.ders_id, sube_id, blok_idx, g, s)
                        if x_key in x_vars:
                            kaplayan.append(x_vars[x_key] * blok_uzunluk)

            model.add(toplam == sum(kaplayan))
            gun_toplamlar.append(toplam)

        # Ardışık günler arasındaki farkı cezalandır
        for i in range(len(gun_toplamlar) - 1):
            diff = model.new_int_var(
                -gun_saatleri[0], gun_saatleri[0],
                f"load_diff_{sube_id}_g{i}"
            )
            abs_diff = model.new_int_var(
                0, gun_saatleri[0],
                f"load_abs_diff_{sube_id}_g{i}"
            )
            model.add(diff == gun_toplamlar[i + 1] - gun_toplamlar[i])
            model.add_abs_equality(abs_diff, diff)
            penalties.append(abs_diff * W_BAL)

    # Amaç: toplam cezayı minimize et
    if penalties:
        model.minimize(sum(penalties))
