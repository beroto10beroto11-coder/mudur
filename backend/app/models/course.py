"""
Course model.
"""
from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class Course(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Branch/subject area
    branch: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Teaching hours
    weekly_hours: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Lesson hour distribution pattern (e.g. "2+2+1+1" or "2+2+2, 3+3")
    hour_distribution: Mapped[str | None] = mapped_column(String(255), nullable=True, default="2+2+1+1")

    # If this course needs consecutive lessons (deprecated in UI, kept for compatibility)
    consecutive_hours: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    # Whether this course requires a specific classroom type
    requires_classroom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    required_room_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Elective flag
    is_elective: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Target classes (e.g., "ALL" for general course or "9/A,9/B" for specific classes)
    target_classes: Mapped[str | None] = mapped_column(String(255), nullable=True, default="ALL")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="courses")  # type: ignore[name-defined]
    course_assignments: Mapped[list["CourseAssignment"]] = relationship(  # type: ignore[name-defined]
        "CourseAssignment", back_populates="course"
    )

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_course_school_code"),
        Index("ix_courses_school_id", "school_id"),
        Index("ix_courses_branch", "branch"),
    )

    def __repr__(self) -> str:
        return f"<Course {self.name}>"


# Deferred imports
from app.models.school import School  # noqa: E402
from app.models.assignment import CourseAssignment  # noqa: E402
