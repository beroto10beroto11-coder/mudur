"""
Duty (Nöbet) model.
"""
from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Duty(TimestampMixin, Base):
    """
    A supervision duty (nöbet) assigned to a teacher on a specific day/location.
    """
    __tablename__ = "duties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )

    # 0=Monday..4=Friday
    day: Mapped[int] = mapped_column(Integer, nullable=False)
    # Which shift/period (e.g. 0=before class, 1=break1, 2=break2, etc.)
    shift: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    location: Mapped[str] = mapped_column(String(150), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # True = auto-assigned, False = manually assigned
    automatic: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Week number within academic year (None = every week)
    week_number: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Date (if specific date, not recurring)
    duty_date: Mapped[str | None] = mapped_column(String(10), nullable=True)

    # Relationships
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="duties")  # type: ignore[name-defined]
    academic_year: Mapped["AcademicYear"] = relationship(  # type: ignore[name-defined]
        "AcademicYear", back_populates="duties"
    )

    __table_args__ = (
        Index("ix_duties_school", "school_id", "academic_year_id"),
        Index("ix_duties_teacher", "teacher_id"),
        Index("ix_duties_day", "academic_year_id", "day"),
    )

    def __repr__(self) -> str:
        day_names = ["Pzt", "Sal", "Çar", "Per", "Cum"]
        return f"<Duty teacher={self.teacher_id} day={day_names[self.day]} loc={self.location}>"


# Deferred imports
from app.models.teacher import Teacher  # noqa: E402
from app.models.school import AcademicYear  # noqa: E402
