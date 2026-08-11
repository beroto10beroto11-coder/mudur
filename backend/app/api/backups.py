from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser, require_super_admin
from app.core.database import get_db
from app.models.backup import Backup, BackupStatus, BackupType
from app.schemas.backup import BackupResponse
from app.tasks.backup_task import run_backup

router = APIRouter(prefix="/backups", tags=["Backups"])


@router.get("", response_model=list[BackupResponse])
async def list_backups(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[CurrentUser, Depends(require_super_admin)],
):
    query = select(Backup).order_by(Backup.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


@router.post("/trigger", response_model=BackupResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_manual_backup(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[CurrentUser, Depends(require_super_admin)],
):
    backup = Backup(
        name="Manuel Yedek",
        file_path="",
        backup_type=BackupType.MANUAL,
        status=BackupStatus.PENDING,
        created_by_id=admin.id,
    )
    db.add(backup)
    await db.commit()
    await db.refresh(backup)

    run_backup.delay(backup.id)
    return backup
