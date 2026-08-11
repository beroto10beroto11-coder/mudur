from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.schemas.class_ import ClassGroupResponse
from app.schemas.classroom import ClassroomResponse
from app.schemas.course import CourseResponse
from app.schemas.teacher import TeacherResponse


class CourseAssignmentCreate(BaseModel):
    academic_year_id: int
    course_id: int
    teacher_id: int
    class_id: int
    classroom_id: int | None = None
    weekly_hours: int
    priority: int = 5
    is_fixed: bool = False
    fixed_day: int | None = None
    fixed_period: int | None = None


class CourseAssignmentUpdate(BaseModel):
    teacher_id: int | None = None
    classroom_id: int | None = None
    weekly_hours: int | None = None
    priority: int | None = None
    is_fixed: bool | None = None
    fixed_day: int | None = None
    fixed_period: int | None = None
    is_active: bool | None = None


class CourseAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    academic_year_id: int
    course_id: int
    teacher_id: int
    class_id: int
    classroom_id: int | None = None
    weekly_hours: int
    priority: int
    is_fixed: bool
    fixed_day: int | None = None
    fixed_period: int | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    # Nested objects optional for detailed responses
    course: CourseResponse | None = None
    teacher: TeacherResponse | None = None
    class_group: ClassGroupResponse | None = None
    classroom: ClassroomResponse | None = None
