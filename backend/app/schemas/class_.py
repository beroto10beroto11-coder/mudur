from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ClassGroupCreate(BaseModel):
    name: str
    grade: int
    section: str
    student_count: int = 0
    max_daily_hours: int = 8
    notes: str | None = None
    is_active: bool = True


class ClassGroupUpdate(BaseModel):
    name: str | None = None
    grade: int | None = None
    section: str | None = None
    student_count: int | None = None
    max_daily_hours: int | None = None
    notes: str | None = None
    is_active: bool | None = None


class ClassGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    name: str
    grade: int
    section: str
    student_count: int
    max_daily_hours: int
    notes: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
