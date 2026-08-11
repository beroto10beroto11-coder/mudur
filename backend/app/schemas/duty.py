from datetime import datetime
from pydantic import BaseModel, ConfigDict


class DutyCreate(BaseModel):
    academic_year_id: int
    teacher_id: int
    day: int
    shift: int = 0
    location: str
    notes: str | None = None
    automatic: bool = True
    week_number: int | None = None
    duty_date: str | None = None


class DutyAutoAssignRequest(BaseModel):
    academic_year_id: int
    locations: list[str]
    days: list[int] = [0, 1, 2, 3, 4]


class DutyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    academic_year_id: int
    teacher_id: int
    teacher_name: str | None = None
    day: int
    shift: int
    location: str
    notes: str | None = None
    automatic: bool
    week_number: int | None = None
    duty_date: str | None = None
    created_at: datetime
