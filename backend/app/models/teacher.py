"""
Teacher and TeacherAvailability models.
"""
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class Teacher(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )

    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    branch: Mapped[str | None] = mapped_column(String(100), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Teaching limits
    max_daily_hours: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    max_weekly_hours: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Allowed/competent courses and classes for this teacher
    allowed_courses: Mapped[str | None] = mapped_column(String(500), nullable=True, default="ALL")
    allowed_classes: Mapped[str | None] = mapped_column(String(500), nullable=True, default="ALL")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="teachers")  # type: ignore[name-defined]
    availability: Mapped[list["TeacherAvailability"]] = relationship(
        "TeacherAvailability", back_populates="teacher", cascade="all, delete-orphan"
    )
    course_assignments: Mapped[list["CourseAssignment"]] = relationship(  # type: ignore[name-defined]
        "CourseAssignment", back_populates="teacher"
    )
    duties: Mapped[list["Duty"]] = relationship(  # type: ignore[name-defined]
        "Duty", back_populates="teacher"
    )

    __table_args__ = (
        Index("ix_teachers_school_id", "school_id"),
        Index("ix_teachers_branch", "branch"),
        Index("ix_teachers_active", "school_id", "is_active"),
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def __repr__(self) -> str:
        return f"<Teacher {self.full_name}>"


class TeacherAvailability(Base):
    """
    Defines when a teacher is available for teaching.
    By default, all slots are available.
    Only unavailable slots need to be stored.
    """
    __tablename__ = "teacher_availability"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )

    # 0=Monday, 1=Tuesday, 2=Wednesday, 3=Thursday, 4=Friday
    day: Mapped[int] = mapped_column(Integer, nullable=False)
    # 1-based period number
    period: Mapped[int] = mapped_column(Integer, nullable=False)

    # True = available, False = unavailable
    available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Preference score: -2 strongly disliked, -1 disliked, 0 neutral, 1 preferred, 2 strongly preferred
    preference: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Relationships
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="availability")

    __table_args__ = (
        UniqueConstraint(
            "teacher_id", "academic_year_id", "day", "period",
            name="uq_teacher_availability"
        ),
        Index("ix_teacher_avail_teacher", "teacher_id", "academic_year_id"),
    )

    def __repr__(self) -> str:
        day_names = ["Pzt", "Sal", "Çar", "Per", "Cum"]
        return (
            f"<TeacherAvailability teacher={self.teacher_id} "
            f"day={day_names[self.day]} period={self.period} "
            f"available={self.available}>"
        )


# Deferred imports
from app.models.school import School  # noqa: E402
from app.models.assignment import CourseAssignment  # noqa: E402
from app.models.duty import Duty  # noqa: E402
