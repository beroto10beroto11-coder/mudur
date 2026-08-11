"""
School and AcademicYear models.
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
from app.models.base import TimestampMixin


class School(TimestampMixin, Base):
    __tablename__ = "schools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    academic_years: Mapped[list["AcademicYear"]] = relationship(
        "AcademicYear", back_populates="school", cascade="all, delete-orphan"
    )
    teachers: Mapped[list["Teacher"]] = relationship(  # type: ignore[name-defined]
        "Teacher", back_populates="school", cascade="all, delete-orphan"
    )
    courses: Mapped[list["Course"]] = relationship(  # type: ignore[name-defined]
        "Course", back_populates="school", cascade="all, delete-orphan"
    )
    classes: Mapped[list["ClassGroup"]] = relationship(  # type: ignore[name-defined]
        "ClassGroup", back_populates="school", cascade="all, delete-orphan"
    )
    classrooms: Mapped[list["Classroom"]] = relationship(  # type: ignore[name-defined]
        "Classroom", back_populates="school", cascade="all, delete-orphan"
    )
    users: Mapped[list["User"]] = relationship(  # type: ignore[name-defined]
        "User",
        secondary="user_schools",
        back_populates="schools",
        lazy="select",
    )
    announcements: Mapped[list["Announcement"]] = relationship(  # type: ignore[name-defined]
        "Announcement", back_populates="school", cascade="all, delete-orphan"
    )
    settings: Mapped[list["SystemSetting"]] = relationship(  # type: ignore[name-defined]
        "SystemSetting", back_populates="school", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_schools_name", "name"),)

    def __repr__(self) -> str:
        return f"<School {self.name}>"


class AcademicYear(TimestampMixin, Base):
    __tablename__ = "academic_years"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    school_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(20), nullable=False)  # e.g., "2026-2027"
    start_date: Mapped[str | None] = mapped_column(String(10), nullable=True)  # ISO date
    end_date: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # School day config
    days_per_week: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    periods_per_day: Mapped[int] = mapped_column(Integer, default=8, nullable=False)

    # Relationships
    school: Mapped["School"] = relationship("School", back_populates="academic_years")
    time_slots: Mapped[list["TimeSlot"]] = relationship(  # type: ignore[name-defined]
        "TimeSlot", back_populates="academic_year", cascade="all, delete-orphan"
    )
    timetables: Mapped[list["Timetable"]] = relationship(  # type: ignore[name-defined]
        "Timetable", back_populates="academic_year", cascade="all, delete-orphan"
    )
    course_assignments: Mapped[list["CourseAssignment"]] = relationship(  # type: ignore[name-defined]
        "CourseAssignment", back_populates="academic_year", cascade="all, delete-orphan"
    )
    duties: Mapped[list["Duty"]] = relationship(  # type: ignore[name-defined]
        "Duty", back_populates="academic_year", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("school_id", "name", name="uq_academic_year_school_name"),
        Index("ix_academic_years_school_id", "school_id"),
        Index("ix_academic_years_active", "school_id", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<AcademicYear {self.name} (school={self.school_id})>"


# Deferred imports to avoid circular references
from app.models.teacher import Teacher  # noqa: E402
from app.models.course import Course  # noqa: E402
from app.models.class_ import ClassGroup  # noqa: E402
from app.models.classroom import Classroom  # noqa: E402
from app.models.timeslot import TimeSlot  # noqa: E402
from app.models.timetable import Timetable  # noqa: E402
from app.models.assignment import CourseAssignment  # noqa: E402
from app.models.duty import Duty  # noqa: E402
from app.models.announcement import Announcement  # noqa: E402
from app.models.settings import SystemSetting  # noqa: E402
from app.models.user import User  # noqa: E402
