from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_db
from app.schemas.classroom import ClassroomCreate, ClassroomResponse, ClassroomUpdate
from app.services.classroom_service import ClassroomService

router = APIRouter(prefix="/classrooms", tags=["Classrooms"])


@router.get("", response_model=list[ClassroomResponse])
async def list_classrooms(
    school_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    service = ClassroomService(db)
    return await service.get_all_classrooms(school_id, skip=skip, limit=limit)


@router.post("", response_model=ClassroomResponse, status_code=status.HTTP_201_CREATED)
async def create_classroom(
    school_id: int,
    data: ClassroomCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = ClassroomService(db)
    return await service.create_classroom(school_id, data)


@router.get("/{classroom_id}", response_model=ClassroomResponse)
async def get_classroom(
    classroom_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = ClassroomService(db)
    return await service.get_classroom(classroom_id)


@router.put("/{classroom_id}", response_model=ClassroomResponse)
async def update_classroom(
    classroom_id: int,
    data: ClassroomUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = ClassroomService(db)
    return await service.update_classroom(classroom_id, data)


@router.delete("/{classroom_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_classroom(
    classroom_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = ClassroomService(db)
    await service.delete_classroom(classroom_id)
