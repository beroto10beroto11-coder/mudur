from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class StudentCreate(BaseModel):
    class_id: int
    academic_year_id: int
    student_number: str | None = None
    first_name: str
    last_name: str
    email: EmailStr | None = None


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    class_id: int
    academic_year_id: int
    student_number: str | None = None
    first_name: str
    last_name: str
    full_name: str
    email: str | None = None
    is_active: bool


class ElectiveCourseCreate(BaseModel):
    academic_year_id: int
    course_id: int
    name: str
    description: str | None = None
    min_students: int = 5
    max_students: int = 30
    eligible_grades: str | None = None


class ElectiveCourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    academic_year_id: int
    course_id: int
    name: str
    description: str | None = None
    min_students: int
    max_students: int
    eligible_grades: str | None = None
    is_active: bool


class StudentChoiceSubmit(BaseModel):
    student_id: int
    choices: list[dict]  # [{"elective_course_id": 1, "preference_rank": 1}, ...]


class ElectiveAutoGroupRequest(BaseModel):
    academic_year_id: int
    target_group_size: int = 20
