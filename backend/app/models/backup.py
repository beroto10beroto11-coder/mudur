"""
Backup model.
"""
from enum import Enum as PyEnum

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class BackupStatus(str, PyEnum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class BackupType(str, PyEnum):
    MANUAL = "MANUAL"
    AUTOMATIC = "AUTOMATIC"


class Backup(TimestampMixin, Base):
    __tablename__ = "backups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    status: Mapped[BackupStatus] = mapped_column(
        Enum(BackupStatus, name="backup_status_enum"),
        default=BackupStatus.PENDING,
        nullable=False,
    )
    backup_type: Mapped[BackupType] = mapped_column(
        Enum(BackupType, name="backup_type_enum"),
        default=BackupType.MANUAL,
        nullable=False,
    )

    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    __table_args__ = (
        Index("ix_backups_status", "status"),
        Index("ix_backups_type", "backup_type"),
        Index("ix_backups_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Backup {self.name} [{self.status}]>"
