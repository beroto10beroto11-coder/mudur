"""
SystemSetting model — per-school key-value settings.
"""
from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class SystemSetting(TimestampMixin, Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True
    )  # None = global setting

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    value_type: Mapped[str] = mapped_column(
        String(20), default="string", nullable=False
    )  # string, integer, boolean, json

    # Relationships
    school: Mapped["School | None"] = relationship(  # type: ignore[name-defined]
        "School", back_populates="settings"
    )

    __table_args__ = (
        UniqueConstraint("school_id", "key", name="uq_system_setting_school_key"),
        Index("ix_system_settings_school", "school_id"),
        Index("ix_system_settings_key", "key"),
    )

    def __repr__(self) -> str:
        return f"<SystemSetting {self.key}={self.value}>"


# Deferred imports
from app.models.school import School  # noqa: E402
