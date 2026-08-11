"""
Models package — import all models to ensure they are registered with SQLAlchemy.
"""
# Order matters to resolve forward references properly
from app.models.base import Base, TimestampMixin, SoftDeleteMixin  # noqa: F401
from app.models.school import School, AcademicYear  # noqa: F401
from app.models.user import User, RefreshToken, UserRole, user_school_association  # noqa: F401
from app.models.teacher import Teacher, TeacherAvailability  # noqa: F401
from app.models.course import Course  # noqa: F401
from app.models.class_ import ClassGroup  # noqa: F401
from app.models.classroom import Classroom  # noqa: F401
from app.models.assignment import CourseAssignment  # noqa: F401
from app.models.timeslot import TimeSlot  # noqa: F401
from app.models.timetable import Timetable, TimetableLesson, TimetableVersion, TimetableStatus  # noqa: F401
from app.models.duty import Duty  # noqa: F401
from app.models.elective import Student, ElectiveCourse, ElectiveGroup, StudentChoice  # noqa: F401
from app.models.audit import AuditLog  # noqa: F401
from app.models.backup import Backup, BackupStatus, BackupType  # noqa: F401
from app.models.announcement import Announcement  # noqa: F401
from app.models.settings import SystemSetting  # noqa: F401

__all__ = [
    "Base",
    "TimestampMixin",
    "SoftDeleteMixin",
    "School",
    "AcademicYear",
    "User",
    "RefreshToken",
    "UserRole",
    "user_school_association",
    "Teacher",
    "TeacherAvailability",
    "Course",
    "ClassGroup",
    "Classroom",
    "CourseAssignment",
    "TimeSlot",
    "Timetable",
    "TimetableLesson",
    "TimetableVersion",
    "TimetableStatus",
    "Duty",
    "Student",
    "ElectiveCourse",
    "ElectiveGroup",
    "StudentChoice",
    "AuditLog",
    "Backup",
    "BackupStatus",
    "BackupType",
    "Announcement",
    "SystemSetting",
]
