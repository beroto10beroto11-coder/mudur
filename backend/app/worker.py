"""
Celery application configuration.
Redis/Celery is optional — the app falls back to thread-based execution when Redis is unavailable.
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
    # ─── Redis yokken bloke olmayı önle ────────────────────────────────────
    # Startup'ta bağlantı denemesi yapma
    broker_connection_retry_on_startup=False,
    # Bağlantı kaybında sadece 1 retry, 1 saniye bekle, sonra exception fırlat
    broker_connection_max_retries=1,
    broker_connection_retry=False,
    # Socket timeout'ları
    broker_transport_options={
        "max_retries": 1,
        "interval_start": 0,
        "interval_step": 0,
        "interval_max": 1,
        "socket_timeout": 2,
        "socket_connect_timeout": 2,
    },
    result_backend_transport_options={
        "socket_timeout": 2,
        "socket_connect_timeout": 2,
    },
    # ───────────────────────────────────────────────────────────────────────
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
