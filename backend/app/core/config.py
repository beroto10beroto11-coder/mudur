"""
Core application configuration using Pydantic Settings.
All values are read from environment variables.
"""
from functools import lru_cache
from typing import List

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ──────────────────────────────
    # Application
    # ──────────────────────────────
    app_name: str = "School Scheduler API"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False
    log_level: str = "INFO"
    log_format: str = "json"

    # ──────────────────────────────
    # Database
    # ──────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./school_scheduler.db"
    database_url_sync: str = "sqlite:///./school_scheduler.db"
    db_pool_size: int = 20
    db_max_overflow: int = 40
    db_pool_timeout: int = 30
    db_echo: bool = False

    # ──────────────────────────────
    # Redis / Celery
    # ──────────────────────────────
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    # ──────────────────────────────
    # JWT Auth
    # ──────────────────────────────
    jwt_secret_key: str = "changeme_very_long_random_secret_key_at_least_64_chars_long_here"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # ──────────────────────────────
    # CORS
    # ──────────────────────────────
    allowed_origins: str = "http://localhost:3000"

    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    # ──────────────────────────────
    # Solver
    # ──────────────────────────────
    solver_max_time_seconds: int = 300
    solver_num_workers: int = 8

    # ──────────────────────────────
    # Backup
    # ──────────────────────────────
    backup_dir: str = "/app/backups"
    backup_retention_days: int = 30
    backup_schedule: str = "0 3 * * *"

    # ──────────────────────────────
    # First Superadmin (initial setup)
    # ──────────────────────────────
    first_superadmin_email: str = "admin@school.k12.tr"
    first_superadmin_password: str = ""
    first_superadmin_full_name: str = "System Administrator"

    # ──────────────────────────────
    # File Storage
    # ──────────────────────────────
    upload_dir: str = "/app/uploads"
    max_upload_size_mb: int = 50

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @model_validator(mode="after")
    def set_debug_from_environment(self) -> "Settings":
        if self.environment == "development":
            object.__setattr__(self, "debug", True)
            object.__setattr__(self, "db_echo", False)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()
