from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_super_admin
from app.core.database import get_db
from app.schemas.school import (
    AcademicYearCreate,
    AcademicYearResponse,
    AcademicYearUpdate,
    SchoolCreate,
    SchoolResponse,
    SchoolUpdate,
)
from app.services.school_service import SchoolService

router = APIRouter(prefix="/schools", tags=["Schools & Academic Years"])


@router.get("", response_model=list[SchoolResponse])
async def list_schools(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
    skip: int = 0,
    limit: int = 100,
):
    service = SchoolService(db)
    return await service.get_all_schools(skip=skip, limit=limit)


@router.post("", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED)
async def create_school(
    data: SchoolCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[CurrentUser, Depends(require_super_admin)],
):
    service = SchoolService(db)
    return await service.create_school(data)


@router.get("/{school_id}", response_model=SchoolResponse)
async def get_school(
    school_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = SchoolService(db)
    return await service.get_school(school_id)


@router.put("/{school_id}", response_model=SchoolResponse)
async def update_school(
    school_id: int,
    data: SchoolUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[CurrentUser, Depends(require_super_admin)],
):
    service = SchoolService(db)
    return await service.update_school(school_id, data)


@router.get("/{school_id}/academic-years", response_model=list[AcademicYearResponse])
async def get_academic_years(
    school_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = SchoolService(db)
    return await service.get_academic_years(school_id)


@router.post("/{school_id}/academic-years", response_model=AcademicYearResponse, status_code=status.HTTP_201_CREATED)
async def create_academic_year(
    school_id: int,
    data: AcademicYearCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = SchoolService(db)
    return await service.create_academic_year(school_id, data)
