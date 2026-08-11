"""
TimeSlot model — defines the schedule grid (day + period → start/end times).
"""
from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TimeSlot(Base):
    """
    One cell in the timetable grid.
    day: 0=Monday ... 4=Friday
    period: 1-based (1=first lesson)
    """
    __tablename__ = "time_slots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )

    # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday
    day: Mapped[int] = mapped_column(Integer, nullable=False)
    # 1-based period within the day
    period: Mapped[int] = mapped_column(Integer, nullable=False)

    # HH:MM format
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)

    # Whether this slot is usable (can mark break periods as inactive)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    academic_year: Mapped["AcademicYear"] = relationship(  # type: ignore[name-defined]
        "AcademicYear", back_populates="time_slots"
    )

    __table_args__ = (
        UniqueConstraint(
            "academic_year_id", "day", "period",
            name="uq_timeslot_academic_year_day_period"
        ),
        Index("ix_time_slots_academic_year", "academic_year_id"),
        Index("ix_time_slots_day_period", "academic_year_id", "day", "period"),
    )

    @property
    def day_name(self) -> str:
        names = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma"]
        return names[self.day] if 0 <= self.day <= 4 else "Bilinmiyor"

    def __repr__(self) -> str:
        return f"<TimeSlot day={self.day} period={self.period} {self.start_time}-{self.end_time}>"


# Deferred imports
from app.models.school import AcademicYear  # noqa: E402
