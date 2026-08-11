"""
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "school_scheduler",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.solver_task",
        "app.tasks.backup_task",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Istanbul",
    enable_utc=True,
    result_expires=86400,  # 24 hours
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.tasks.solver_task.run_solver": {"queue": "solver"},
        "app.tasks.backup_task.run_backup": {"queue": "backup"},
        "app.tasks.backup_task.cleanup_old_backups": {"queue": "backup"},
    },
    # Celery Beat schedule (periodic tasks)
    beat_schedule={
        "daily-backup": {
            "task": "app.tasks.backup_task.run_scheduled_backup",
            "schedule": crontab(hour=3, minute=0),
            "options": {"queue": "backup"},
        },
        "cleanup-old-backups": {
            "task": "app.tasks.backup_task.cleanup_old_backups",
            "schedule": crontab(hour=3, minute=30),
            "options": {"queue": "backup"},
        },
    },
)
