"""
CourseAssignment model — links Course + Teacher + ClassGroup + Classroom.
"""
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class CourseAssignment(TimestampMixin, Base):
    """
    The core entity: which teacher teaches which course in which class,
    in which classroom, for how many hours per week.
    """
    __tablename__ = "course_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    school_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    classroom_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("classrooms.id", ondelete="SET NULL"), nullable=True
    )

    # How many hours per week for this specific assignment
    weekly_hours: Mapped[int] = mapped_column(Integer, nullable=False)

    # Solver priority (higher = scheduled first)
    priority: Mapped[int] = mapped_column(Integer, default=5, nullable=False)

    # If True, this assignment's fixed_day/fixed_period must be honored
    is_fixed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    fixed_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fixed_period: Mapped[int | None] = mapped_column(Integer, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="course_assignments")  # type: ignore[name-defined]
    teacher: Mapped["Teacher"] = relationship("Teacher", back_populates="course_assignments")  # type: ignore[name-defined]
    class_group: Mapped["ClassGroup"] = relationship("ClassGroup", back_populates="course_assignments")  # type: ignore[name-defined]
    classroom: Mapped["Classroom | None"] = relationship("Classroom", back_populates="course_assignments")  # type: ignore[name-defined]
    academic_year: Mapped["AcademicYear"] = relationship("AcademicYear", back_populates="course_assignments")  # type: ignore[name-defined]
    timetable_lessons: Mapped[list["TimetableLesson"]] = relationship(  # type: ignore[name-defined]
        "TimetableLesson", back_populates="course_assignment"
    )

    __table_args__ = (
        UniqueConstraint(
            "academic_year_id", "course_id", "teacher_id", "class_id",
            name="uq_course_assignment"
        ),
        Index("ix_course_assignments_school", "school_id", "academic_year_id"),
        Index("ix_course_assignments_teacher", "teacher_id", "academic_year_id"),
        Index("ix_course_assignments_class", "class_id", "academic_year_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<CourseAssignment course={self.course_id} "
            f"teacher={self.teacher_id} class={self.class_id}>"
        )


# Deferred imports
from app.models.course import Course  # noqa: E402
from app.models.teacher import Teacher  # noqa: E402
from app.models.class_ import ClassGroup  # noqa: E402
from app.models.classroom import Classroom  # noqa: E402
from app.models.school import AcademicYear  # noqa: E402
from app.models.timetable import TimetableLesson  # noqa: E402
