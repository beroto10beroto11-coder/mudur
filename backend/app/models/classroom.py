"""
Classroom model.
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


class Classroom(TimestampMixin, SoftDeleteMixin, Base):
    """
    Physical classroom / lab / room in a school.
    """
    __tablename__ = "classrooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # Room type for matching with course requirements
    # e.g., "normal", "lab_science", "lab_computer", "gym", "music", "workshop"
    room_type: Mapped[str] = mapped_column(String(50), default="normal", nullable=False)

    floor: Mapped[int | None] = mapped_column(Integer, nullable=True)
    building: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="classrooms")  # type: ignore[name-defined]
    course_assignments: Mapped[list["CourseAssignment"]] = relationship(  # type: ignore[name-defined]
        "CourseAssignment", back_populates="classroom"
    )

    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_classroom_school_name"),
        Index("ix_classrooms_school_id", "school_id"),
        Index("ix_classrooms_room_type", "school_id", "room_type"),
    )

    def __repr__(self) -> str:
        return f"<Classroom {self.name} (cap={self.capacity})>"


# Deferred imports
from app.models.school import School  # noqa: E402
from app.models.assignment import CourseAssignment  # noqa: E402
