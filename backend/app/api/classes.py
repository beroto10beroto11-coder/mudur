from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_db
from app.schemas.class_ import ClassGroupCreate, ClassGroupResponse, ClassGroupUpdate
from app.services.class_service import ClassGroupService

router = APIRouter(prefix="/classes", tags=["Classes"])


@router.get("", response_model=list[ClassGroupResponse])
async def list_classes(
    school_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    service = ClassGroupService(db)
    return await service.get_all_classes(school_id, skip=skip, limit=limit)


@router.post("", response_model=ClassGroupResponse, status_code=status.HTTP_201_CREATED)
async def create_class(
    school_id: int,
    data: ClassGroupCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = ClassGroupService(db)
    return await service.create_class(school_id, data)


@router.get("/{class_id}", response_model=ClassGroupResponse)
async def get_class(
    class_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = ClassGroupService(db)
    return await service.get_class(class_id)


@router.put("/{class_id}", response_model=ClassGroupResponse)
async def update_class(
    class_id: int,
    data: ClassGroupUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = ClassGroupService(db)
    return await service.update_class(class_id, data)


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(
    class_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = ClassGroupService(db)
    await service.delete_class(class_id)
