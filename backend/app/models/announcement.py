"""
Announcement model.
"""
from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Announcement(TimestampMixin, Base):
    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )
    created_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    expires_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="announcements")  # type: ignore[name-defined]

    __table_args__ = (
        Index("ix_announcements_school", "school_id"),
        Index("ix_announcements_pinned", "school_id", "is_pinned"),
    )

    def __repr__(self) -> str:
        return f"<Announcement {self.title}>"


# Deferred imports
from app.models.school import School  # noqa: E402
