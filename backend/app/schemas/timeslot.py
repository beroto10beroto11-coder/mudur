from pydantic import BaseModel, ConfigDict


class TimeSlotCreate(BaseModel):
    academic_year_id: int
    day: int
    period: int
    start_time: str
    end_time: str
    is_active: bool = True


class TimeSlotBatchCreate(BaseModel):
    academic_year_id: int
    days: int = 5
    periods_per_day: int = 8
    daily_periods: list[int] | None = None
    start_time_str: str = "08:30"
    lesson_duration_minutes: int = 40
    break_duration_minutes: int = 10


class TimeSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    academic_year_id: int
    day: int
    period: int
    start_time: str
    end_time: str
    is_active: bool
    day_name: str
