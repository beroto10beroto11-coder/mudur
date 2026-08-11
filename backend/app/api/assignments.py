from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_db
from app.schemas.assignment import CourseAssignmentCreate, CourseAssignmentResponse, CourseAssignmentUpdate
from app.services.assignment_service import CourseAssignmentService

router = APIRouter(prefix="/assignments", tags=["Course Assignments"])


@router.get("", response_model=list[CourseAssignmentResponse])
async def list_assignments(
    school_id: int,
    academic_year_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = CourseAssignmentService(db)
    return await service.get_assignments(school_id, academic_year_id)


@router.post("", response_model=CourseAssignmentResponse, status_code=status.HTTP_201_CREATED)
async def create_assignment(
    school_id: int,
    data: CourseAssignmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = CourseAssignmentService(db)
    return await service.create_assignment(school_id, data)


@router.get("/{assignment_id}", response_model=CourseAssignmentResponse)
async def get_assignment(
    assignment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = CourseAssignmentService(db)
    return await service.get_assignment(assignment_id)


@router.put("/{assignment_id}", response_model=CourseAssignmentResponse)
async def update_assignment(
    assignment_id: int,
    data: CourseAssignmentUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = CourseAssignmentService(db)
    return await service.update_assignment(assignment_id, data)


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assignment(
    assignment_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    service = CourseAssignmentService(db)
    await service.delete_assignment(assignment_id)
