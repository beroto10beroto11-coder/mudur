from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_db
from app.models.announcement import Announcement
from app.schemas.announcement import AnnouncementCreate, AnnouncementResponse

router = APIRouter(prefix="/announcements", tags=["Announcements"])


@router.get("", response_model=list[AnnouncementResponse])
async def list_announcements(
    school_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    query = (
        select(Announcement)
        .where(Announcement.school_id == school_id, Announcement.is_active == True)
        .order_by(Announcement.is_pinned.desc(), Announcement.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    school_id: int,
    data: AnnouncementCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    announcement = Announcement(school_id=school_id, created_by_id=current_user.id, **data.model_dump())
    db.add(announcement)
    await db.commit()
    await db.refresh(announcement)
    return announcement
