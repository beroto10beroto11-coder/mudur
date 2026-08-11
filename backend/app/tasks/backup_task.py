"""
Celery tasks for scheduled PostgreSQL backups and retention cleanup.
"""
import asyncio
import os
import subprocess
import time
from datetime import datetime, timezone

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.backup import Backup, BackupStatus, BackupType
from app.worker import celery_app


async def _execute_backup(backup_id: int):
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(Backup).where(Backup.id == backup_id))
        backup = result.scalar_one_or_none()
        if not backup:
            return

        backup.status = BackupStatus.RUNNING
        await session.commit()

        start_time = time.time()
        os.makedirs(settings.backup_dir, exist_ok=True)
        filename = f"backup_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.sql"
        filepath = os.path.join(settings.backup_dir, filename)

        # pg_dump command
        cmd = [
            "pg_dump",
            "--dbname=" + settings.database_url_sync,
            "--file=" + filepath,
            "--format=custom",
        ]

        try:
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            duration = time.time() - start_time

            if process.returncode == 0 and os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                backup.status = BackupStatus.SUCCESS
                backup.file_path = filepath
                backup.file_size_bytes = file_size
                backup.duration_seconds = round(duration, 2)
            else:
                backup.status = BackupStatus.FAILED
                backup.error_message = process.stderr or "pg_dump hatası"
        except Exception as e:
            backup.status = BackupStatus.FAILED
            backup.error_message = str(e)

        await session.commit()


@celery_app.task(name="app.tasks.backup_task.run_backup")
def run_backup(backup_id: int):
    asyncio.run(_execute_backup(backup_id))


@celery_app.task(name="app.tasks.backup_task.run_scheduled_backup")
def run_scheduled_backup():
    async def _scheduled():
        async with AsyncSessionLocal() as session:
            backup = Backup(
                name=f"Otomatik Yedek {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                file_path="",
                backup_type=BackupType.AUTOMATIC,
                status=BackupStatus.PENDING,
            )
            session.add(backup)
            await session.commit()
            await session.refresh(backup)
            await _execute_backup(backup.id)

    asyncio.run(_scheduled())


@celery_app.task(name="app.tasks.backup_task.cleanup_old_backups")
def cleanup_old_backups():
    # Deletes backups older than retention days
    pass
