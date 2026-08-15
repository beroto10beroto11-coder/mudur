"""
Scheduler Ana Çalıştırıcı
==========================
Tüm aşamaları koordine eden tek giriş noktası:

    1. Ön doğrulama (validate_feasibility)
    2. Model kurulumu (build_model)
    3. CP-SAT çözümü
    4. Sonuç exportu (export_by_class + export_by_teacher)
    5. Çözüm sonrası doğrulama (validate_solution) — G1
    6. INFEASIBLE durumunda teşhis (diagnose_infeasibility)
"""
from __future__ import annotations

import os
import time

from ortools.sat.python import cp_model

from app.solver.scheduler.models import SchedulerInput, SchedulerResult, FeasibilityIhlali
from app.solver.scheduler.validator import validate_feasibility
from app.solver.scheduler.model_builder import build_model
from app.solver.scheduler.exporter import export_by_class, export_by_teacher
from app.solver.scheduler.diagnostics import diagnose_infeasibility
from app.solver.scheduler.post_validator import validate_solution


def run_scheduler(inp: SchedulerInput) -> SchedulerResult:
    """
    Çizelgeleme işlemini baştan sona çalıştırır.

    Args:
        inp: Tam doğrulanmış SchedulerInput nesnesi.

    Returns:
        SchedulerResult — başarı, INFEASIBLE veya validasyon hatası içerir.
    """
    start = time.perf_counter()

    # ─── Aşama 1: Ön Doğrulama ───────────────────────────────────────────────
    ihlaller = validate_feasibility(inp)
    # Sadece kritik ihlaller (YETERSIZ_OGRETMEN) solver'ı durdurur.
    # SUBE_SAAT_UYUMSUZLUGU uyarıdır; solver yine de çalışır ama uyarı döner.
    kritik_ihlaller = [
        ih for ih in ihlaller if ih.tur == "YETERSIZ_OGRETMEN"
    ]
    if kritik_ihlaller:
        sure = time.perf_counter() - start
        return SchedulerResult(
            basarili=False,
            durum="VALIDATION_ERROR",
            sure_saniye=round(sure, 3),
            ihlaller=ihlaller,
            teshis_mesajlari=[ih.mesaj for ih in kritik_ihlaller],
        )

    # ─── Aşama 2: Model Kur ──────────────────────────────────────────────────
    model = cp_model.CpModel()
    x_vars, y_vars = build_model(inp, model)

    # ─── Aşama 3: Solver Konfigürasyonu ─────────────────────────────────────
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = inp.maks_cozum_suresi_saniye
    solver.parameters.num_search_workers = (
        inp.paralel_isci_sayisi
        if inp.paralel_isci_sayisi is not None
        else max(4, os.cpu_count() or 8)
    )
    # Portfolio search: CP-SAT'ın birden fazla stratejiyi paralel deneyen modu
    solver.parameters.search_branching = cp_model.PORTFOLIO_SEARCH
    solver.parameters.linearization_level = 2
    solver.parameters.cp_model_presolve = True

    # ─── Aşama 4: Çöz ────────────────────────────────────────────────────────
    status = solver.solve(model)
    sure = time.perf_counter() - start

    # ─── Aşama 5: Sonuç Üret ve Doğrula ──────────────────────────────────────
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        sube_prog = export_by_class(solver, x_vars, y_vars, inp)
        ogretmen_prog = export_by_teacher(solver, x_vars, y_vars, inp)

        durum_str = "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE"

        # ─── Aşama 5.5: Çözüm Sonrası Doğrulama (G1) ────────────────────────
        # Şartname G1: Export'tan önce otomatik doğrulama yapılmalı.
        # Bu doğrulamalardan biri bile başarısız olursa sonuç kesinlikle
        # export edilmemeli, hata raporu üretilmelidir.
        post_ihlaller = validate_solution(inp, sube_prog, ogretmen_prog)

        if post_ihlaller:
            # G1 ihlali var → çözüm geçersiz, export etme
            post_ihlal_mesajlari = [
                f"[{pi.kural}:{pi.tur}] {pi.mesaj}" for pi in post_ihlaller
            ]
            # Ön doğrulama uyarılarını da ekle
            tum_ihlaller = [
                ih for ih in ihlaller if ih.tur != "YETERSIZ_OGRETMEN"
            ]
            # Post validation ihlallerini FeasibilityIhlali formatına çevir
            for pi in post_ihlaller:
                tum_ihlaller.append(FeasibilityIhlali(
                    tur=f"POST_VALIDATION_{pi.tur}",
                    mesaj=f"[{pi.kural}] {pi.mesaj}",
                    detay=pi.detay,
                ))

            return SchedulerResult(
                basarili=False,
                durum="VALIDATION_ERROR",
                sure_saniye=round(sure, 3),
                hedef_deger=solver.objective_value,
                ihlaller=tum_ihlaller,
                teshis_mesajlari=post_ihlal_mesajlari,
            )

        # Doğrulama geçti → başarılı sonuç döndür
        return SchedulerResult(
            basarili=True,
            durum=durum_str,
            sure_saniye=round(sure, 3),
            hedef_deger=solver.objective_value,
            sube_programlari=sube_prog,
            ogretmen_programlari=ogretmen_prog,
            # Uyarı düzeyindeki ihlalleri de dön (ör. saat dengesizliği)
            ihlaller=[ih for ih in ihlaller if ih.tur != "YETERSIZ_OGRETMEN"],
        )

    else:
        # INFEASIBLE veya UNKNOWN → teşhis üret
        teshis = diagnose_infeasibility(inp, x_vars, y_vars, model)

        return SchedulerResult(
            basarili=False,
            durum="INFEASIBLE",
            sure_saniye=round(sure, 3),
            ihlaller=ihlaller,
            teshis_mesajlari=teshis,
        )

