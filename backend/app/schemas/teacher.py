from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr


class TeacherCreate(BaseModel):
    first_name: str
    last_name: str
    branch: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None
    max_daily_hours: int = 8
    max_weekly_hours: int = 0
    allowed_courses: str | None = "ALL"
    allowed_classes: str | None = "ALL"
    is_active: bool = True


class TeacherUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    branch: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None
    max_daily_hours: int | None = None
    max_weekly_hours: int | None = None
    allowed_courses: str | None = None
    allowed_classes: str | None = None
    is_active: bool | None = None


class TeacherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    first_name: str
    last_name: str
    full_name: str
    branch: str | None = None
    email: str | None = None
    phone: str | None = None
    notes: str | None = None
    max_daily_hours: int
    max_weekly_hours: int
    allowed_courses: str | None = "ALL"
    allowed_classes: str | None = "ALL"
    is_active: bool
    created_at: datetime
    updated_at: datetime
