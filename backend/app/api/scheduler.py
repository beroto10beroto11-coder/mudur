"""
scheduler.py — FastAPI router: /api/scheduler/...
"""
from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.scheduler.data_loader import load_scheduler_input
from app.scheduler.validator import validate
from app.scheduler.solver import solve
from app.scheduler.output_generator import generate_output

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scheduler", tags=["Scheduler"])


# ---------------------------------------------------------------------------
# Request / Response şemaları
# ---------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    academic_year_id: int
    format: Literal["excel", "pdf", "word"] = "excel"
    time_limit_seconds: int = 120


class ValidationResponse(BaseModel):
    valid: bool
    errors: list[str]
    warnings: list[str]


class WarningItem(BaseModel):
    class_name: str
    course_name: str
    reason: str


class GenerateResponse(BaseModel):
    solver_status: str
    lesson_count: int
    warning_count: int
    warnings: list[WarningItem]


# ---------------------------------------------------------------------------
# GET /api/scheduler/validate — veri tutarlılığı kontrolü
# ---------------------------------------------------------------------------

@router.get("/validate", response_model=ValidationResponse)
async def validate_data(
    school_id: int = Query(...),
    academic_year_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Algoritma başlamadan önce veri tutarlılığını doğrular.
    Hata varsa 'valid=false' döner; kullanıcı hataları düzeltmelidir.
    """
    try:
        inp = await load_scheduler_input(db, school_id, academic_year_id)
        result = validate(inp)
        return ValidationResponse(
            valid=result.valid,
            errors=result.errors,
            warnings=result.warnings,
        )
    except Exception as e:
        logger.exception("Validation error")
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# POST /api/scheduler/generate — dosya üret ve indir
# ---------------------------------------------------------------------------

@router.post("/generate")
async def generate_schedule(
    req: GenerateRequest,
    school_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    OR-Tools CP-SAT ile ders programını çözer ve dosya döner.
    Hata varsa bile mevcut çözümle dosyayı üretir; eksikler uyarılar bölümünde listelenir.
    """
    try:
        logger.info(f"Scheduler generate: school={school_id} year={req.academic_year_id} fmt={req.format}")

        # 1. Veri yükle
        inp = await load_scheduler_input(db, school_id, req.academic_year_id)

        if not inp.classes:
            raise HTTPException(status_code=422, detail="Sisteme kayıtlı aktif sınıf bulunamadı.")
        if not inp.courses:
            raise HTTPException(status_code=422, detail="Sisteme kayıtlı aktif ders bulunamadı.")
        if not inp.teachers:
            raise HTTPException(status_code=422, detail="Sisteme kayıtlı aktif öğretmen bulunamadı.")

        # 2. Validasyon (hataları uyarıya çevir, durdurmadan devam et)
        val_result = validate(inp)
        extra_warnings = []
        for err in val_result.errors:
            extra_warnings.append(err)

        # 3. Çöz
        solver_result = solve(inp, time_limit_seconds=req.time_limit_seconds)

        # Validasyon hatalarını uyarı listesine ekle
        from app.scheduler.solver import InfeasibilityWarning
        for err_msg in extra_warnings:
            solver_result.warnings.append(
                InfeasibilityWarning(class_name="—", course_name="—", reason=err_msg)
            )

        # 4. Çıktı üret
        file_bytes, media_type, filename = generate_output(inp, solver_result, req.format)

        logger.info(
            f"Schedule generated: {len(solver_result.lessons)} lessons, "
            f"{len(solver_result.warnings)} warnings, status={solver_result.solver_status}"
        )

        return Response(
            content=file_bytes,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "X-Solver-Status": solver_result.solver_status,
                "X-Lesson-Count": str(len(solver_result.lessons)),
                "X-Warning-Count": str(len(solver_result.warnings)),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Scheduler generate error")
        raise HTTPException(status_code=500, detail=f"Program üretilirken hata: {str(e)}")
