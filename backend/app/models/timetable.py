"""
Timetable, TimetableLesson, TimetableVersion models.
"""
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class TimetableStatus(str, PyEnum):
    DRAFT = "DRAFT"
    GENERATING = "GENERATING"
    GENERATED = "GENERATED"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"
    FAILED = "FAILED"


class Timetable(TimestampMixin, Base):
    """
    Main timetable entity for a school year.
    Contains meta info; lessons are in TimetableLesson.
    """
    __tablename__ = "timetables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[TimetableStatus] = mapped_column(
        Enum(TimetableStatus, name="timetable_status_enum"),
        default=TimetableStatus.DRAFT,
        nullable=False,
    )

    # Solver job tracking
    solver_job_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    solver_duration_seconds: Mapped[float | None] = mapped_column(nullable=True)
    solver_objective_value: Mapped[float | None] = mapped_column(nullable=True)
    solver_conflicts: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    academic_year: Mapped["AcademicYear"] = relationship(  # type: ignore[name-defined]
        "AcademicYear", back_populates="timetables"
    )
    lessons: Mapped[list["TimetableLesson"]] = relationship(
        "TimetableLesson",
        back_populates="timetable",
        cascade="all, delete-orphan",
        lazy="select",
    )
    versions: Mapped[list["TimetableVersion"]] = relationship(
        "TimetableVersion",
        back_populates="timetable",
        cascade="all, delete-orphan",
        order_by="TimetableVersion.version_number.desc()",
    )

    __table_args__ = (
        Index("ix_timetables_school", "school_id", "academic_year_id"),
        Index("ix_timetables_status", "status"),
    )

    def __repr__(self) -> str:
        return f"<Timetable {self.name} [{self.status}]>"


class TimetableLesson(TimestampMixin, Base):
    """
    A single lesson slot in the timetable.
    One row = one scheduled lesson (course + teacher + class + classroom + time).
    """
    __tablename__ = "timetable_lessons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timetable_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("timetables.id", ondelete="CASCADE"), nullable=False
    )
    course_assignment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("course_assignments.id", ondelete="CASCADE"), nullable=False
    )

    # Denormalized for performance (no JOIN needed for grid display)
    course_id: Mapped[int] = mapped_column(Integer, nullable=False)
    teacher_id: Mapped[int] = mapped_column(Integer, nullable=False)
    class_id: Mapped[int] = mapped_column(Integer, nullable=False)
    classroom_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Time placement
    day: Mapped[int] = mapped_column(Integer, nullable=False)      # 0=Mon..4=Fri
    period: Mapped[int] = mapped_column(Integer, nullable=False)   # 1-based

    # Whether this lesson is pinned (cannot be moved)
    is_fixed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    timetable: Mapped["Timetable"] = relationship("Timetable", back_populates="lessons")
    course_assignment: Mapped["CourseAssignment"] = relationship(  # type: ignore[name-defined]
        "CourseAssignment", back_populates="timetable_lessons"
    )

    __table_args__ = (
        # No two lessons can occupy the same teacher/class/classroom at same time
        UniqueConstraint(
            "timetable_id", "teacher_id", "day", "period",
            name="uq_lesson_teacher_slot"
        ),
        UniqueConstraint(
            "timetable_id", "class_id", "day", "period",
            name="uq_lesson_class_slot"
        ),
        Index("ix_timetable_lessons_timetable", "timetable_id"),
        Index("ix_timetable_lessons_teacher", "timetable_id", "teacher_id"),
        Index("ix_timetable_lessons_class", "timetable_id", "class_id"),
        Index("ix_timetable_lessons_day_period", "timetable_id", "day", "period"),
    )

    def __repr__(self) -> str:
        day_names = ["Pzt", "Sal", "Çar", "Per", "Cum"]
        return (
            f"<TimetableLesson day={day_names[self.day]} "
            f"period={self.period} course={self.course_id}>"
        )


class TimetableVersion(TimestampMixin, Base):
    """
    Snapshot of a timetable at a point in time.
    Supports restore to any previous version.
    """
    __tablename__ = "timetable_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timetable_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("timetables.id", ondelete="CASCADE"), nullable=False
    )

    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Serialized snapshot of all lessons at this version
    lessons_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)

    created_by_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    # Relationships
    timetable: Mapped["Timetable"] = relationship("Timetable", back_populates="versions")

    __table_args__ = (
        UniqueConstraint(
            "timetable_id", "version_number",
            name="uq_timetable_version"
        ),
        Index("ix_timetable_versions_timetable", "timetable_id"),
    )

    def __repr__(self) -> str:
        return f"<TimetableVersion v{self.version_number} of timetable={self.timetable_id}>"


# Deferred imports
from app.models.assignment import CourseAssignment  # noqa: E402
from app.models.school import AcademicYear  # noqa: E402
