"""
Elective course models: ElectiveCourse, ElectiveGroup, Student, StudentChoice.
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
from app.models.base import TimestampMixin


class Student(TimestampMixin, Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )
    class_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False
    )
    academic_year_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("academic_years.id", ondelete="CASCADE"), nullable=False
    )

    student_number: Mapped[str | None] = mapped_column(String(30), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    class_group: Mapped["ClassGroup"] = relationship(  # type: ignore[name-defined]
        "ClassGroup", back_populates="students"
    )
    choices: Mapped[list["StudentChoice"]] = relationship(
        "StudentChoice", back_populates="student", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_students_school", "school_id", "academic_year_id"),
        Index("ix_students_class", "class_id"),
    )

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class ElectiveCourse(TimestampMixin, Base):
    """
    An elective course offering (e.g., Robotics, Chess, Drama).
    """
    __tablename__ = "elective_courses"

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

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    min_students: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_students: Mapped[int] = mapped_column(Integer, default=30, nullable=False)

    # Which grades can participate (comma-separated, e.g., "9,10")
    eligible_grades: Mapped[str | None] = mapped_column(String(50), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationships
    groups: Mapped[list["ElectiveGroup"]] = relationship(
        "ElectiveGroup", back_populates="elective_course", cascade="all, delete-orphan"
    )
    student_choices: Mapped[list["StudentChoice"]] = relationship(
        "StudentChoice", back_populates="elective_course"
    )

    __table_args__ = (
        Index("ix_elective_courses_school", "school_id", "academic_year_id"),
    )


class ElectiveGroup(TimestampMixin, Base):
    """
    A formed group for an elective course after student grouping.
    """
    __tablename__ = "elective_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    elective_course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("elective_courses.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True
    )
    classroom_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("classrooms.id", ondelete="SET NULL"), nullable=True
    )

    name: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g., "Robotik-A"
    day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    period: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    elective_course: Mapped["ElectiveCourse"] = relationship(
        "ElectiveCourse", back_populates="groups"
    )
    student_choices: Mapped[list["StudentChoice"]] = relationship(
        "StudentChoice", back_populates="elective_group"
    )

    __table_args__ = (
        Index("ix_elective_groups_course", "elective_course_id"),
    )


class StudentChoice(TimestampMixin, Base):
    """
    A student's preference for an elective course.
    """
    __tablename__ = "student_choices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False
    )
    elective_course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("elective_courses.id", ondelete="CASCADE"), nullable=False
    )
    elective_group_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("elective_groups.id", ondelete="SET NULL"), nullable=True
    )

    # 1 = first choice, 2 = second, etc.
    preference_rank: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_assigned: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="choices")
    elective_course: Mapped["ElectiveCourse"] = relationship(
        "ElectiveCourse", back_populates="student_choices"
    )
    elective_group: Mapped["ElectiveGroup | None"] = relationship(
        "ElectiveGroup", back_populates="student_choices"
    )

    __table_args__ = (
        UniqueConstraint(
            "student_id", "elective_course_id",
            name="uq_student_choice"
        ),
        Index("ix_student_choices_student", "student_id"),
    )


# Deferred imports
from app.models.class_ import ClassGroup  # noqa: E402
