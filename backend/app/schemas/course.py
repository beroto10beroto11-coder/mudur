from datetime import datetime
from pydantic import BaseModel, ConfigDict


class CourseCreate(BaseModel):
    name: str
    code: str | None = None
    description: str | None = None
    branch: str | None = None
    weekly_hours: int = 1
    hour_distribution: str | None = "2+2+1+1"
    consecutive_hours: int = 1
    requires_classroom: bool = False
    required_room_type: str | None = None
    is_elective: bool = False
    target_classes: str | None = "ALL"
    color: str | None = None
    is_active: bool = True


class CourseUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    description: str | None = None
    branch: str | None = None
    weekly_hours: int | None = None
    hour_distribution: str | None = None
    consecutive_hours: int | None = None
    requires_classroom: bool | None = None
    required_room_type: str | None = None
    is_elective: bool | None = None
    target_classes: str | None = None
    color: str | None = None
    is_active: bool | None = None


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    name: str
    code: str | None = None
    description: str | None = None
    branch: str | None = None
    weekly_hours: int
    hour_distribution: str | None = "2+2+1+1"
    consecutive_hours: int
    requires_classroom: bool
    required_room_type: str | None = None
    is_elective: bool
    target_classes: str | None = "ALL"
    color: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
