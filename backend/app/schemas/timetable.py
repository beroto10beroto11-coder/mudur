from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.timetable import TimetableStatus


class TimetableGenerateRequest(BaseModel):
    academic_year_id: int
    name: str
    max_time_seconds: int = 60
    allow_soft_violations: bool = True


class TimetableLessonMoveRequest(BaseModel):
    new_day: int
    new_period: int


class TimetableLessonResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timetable_id: int
    course_assignment_id: int
    course_id: int
    teacher_id: int
    class_id: int
    classroom_id: int | None = None
    day: int
    period: int
    is_fixed: bool
    created_at: datetime

    # Display names for easy rendering
    course_name: str | None = None
    teacher_name: str | None = None
    class_name: str | None = None
    classroom_name: str | None = None


class TimetableResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    academic_year_id: int
    name: str
    description: str | None = None
    status: TimetableStatus
    solver_job_id: str | None = None
    solver_duration_seconds: float | None = None
    solver_objective_value: float | None = None
    solver_conflicts: dict | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    lessons_count: int = 0


class TimetableVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    timetable_id: int
    version_number: int
    description: str | None = None
    change_summary: str | None = None
    created_by_id: int | None = None
    created_at: datetime
