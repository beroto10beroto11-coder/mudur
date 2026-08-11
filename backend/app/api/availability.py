from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_db
from app.schemas.availability import TeacherAvailabilityBatchUpdate, TeacherAvailabilityResponse
from app.services.teacher_service import TeacherService

router = APIRouter(prefix="/availability", tags=["Teacher Availability"])


@router.get("/teacher/{teacher_id}", response_model=list[TeacherAvailabilityResponse])
async def get_teacher_availability(
    teacher_id: int,
    academic_year_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = TeacherService(db)
    return await service.get_availability(teacher_id, academic_year_id)


@router.post("/batch", status_code=status.HTTP_200_OK)
async def update_teacher_availability(
    data: TeacherAvailabilityBatchUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = TeacherService(db)
    await service.update_availability(data)
    return {"message": "Müsaitlik bilgileri güncellendi."}
