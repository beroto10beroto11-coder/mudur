"""
ClassGroup model (Sınıf — e.g. 9/A, 10/B).
"""
from sqlalchemy import (
    Boolean,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin


class ClassGroup(TimestampMixin, SoftDeleteMixin, Base):
    """
    Represents a class group (e.g., 9/A, 10/B).
    In Turkish schools: grade (9, 10, 11, 12) + section (A, B, C...).
    """
    __tablename__ = "classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "9/A"
    grade: Mapped[int] = mapped_column(Integer, nullable=False)    # 9, 10, 11, 12
    section: Mapped[str] = mapped_column(String(10), nullable=False)  # A, B, C

    student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Daily lesson limit for this class
    max_daily_hours: Mapped[int] = mapped_column(Integer, default=8, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="classes")  # type: ignore[name-defined]
    course_assignments: Mapped[list["CourseAssignment"]] = relationship(  # type: ignore[name-defined]
        "CourseAssignment", back_populates="class_group"
    )
    students: Mapped[list["Student"]] = relationship(  # type: ignore[name-defined]
        "Student", back_populates="class_group"
    )

    __table_args__ = (
        UniqueConstraint("school_id", "grade", "section", name="uq_class_school_grade_section"),
        Index("ix_classes_school_id", "school_id"),
        Index("ix_classes_grade", "school_id", "grade"),
    )

    def __repr__(self) -> str:
        return f"<ClassGroup {self.name}>"


# Deferred imports
from app.models.school import School  # noqa: E402
from app.models.assignment import CourseAssignment  # noqa: E402
from app.models.elective import Student  # noqa: E402
