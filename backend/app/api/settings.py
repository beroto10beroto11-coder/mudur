from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.core.database import get_db
from app.models.settings import SystemSetting
from app.schemas.settings import SystemSettingResponse, SystemSettingUpdate

router = APIRouter(prefix="/settings", tags=["System Settings"])


@router.get("", response_model=list[SystemSettingResponse])
async def get_settings(
    school_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    query = select(SystemSetting).where(
        (SystemSetting.school_id == school_id) | (SystemSetting.school_id == None)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


@router.put("/{key}", response_model=SystemSettingResponse)
async def update_setting(
    key: str,
    data: SystemSettingUpdate,
    school_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: CurrentUser,
):
    query = select(SystemSetting).where(
        SystemSetting.school_id == school_id,
        SystemSetting.key == key,
    )
    result = await db.execute(query)
    setting = result.scalar_one_or_none()

    if not setting:
        setting = SystemSetting(
            school_id=school_id,
            key=key,
            value=data.value,
            description=data.description,
        )
        db.add(setting)
    else:
        setting.value = data.value
        if data.description:
            setting.description = data.description

    await db.commit()
    await db.refresh(setting)
    return setting
