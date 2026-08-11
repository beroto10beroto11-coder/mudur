from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_db
from app.schemas.timeslot import TimeSlotBatchCreate, TimeSlotResponse
from app.services.timeslot_service import TimeSlotService

router = APIRouter(prefix="/timeslots", tags=["TimeSlots"])


@router.get("", response_model=list[TimeSlotResponse])
async def list_timeslots(
    academic_year_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = TimeSlotService(db)
    return await service.get_by_academic_year(academic_year_id)


@router.post("/generate", response_model=list[TimeSlotResponse], status_code=status.HTTP_201_CREATED)
async def generate_timeslots(
    school_id: int,
    data: TimeSlotBatchCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = TimeSlotService(db)
    return await service.generate_default_slots(school_id, data)
