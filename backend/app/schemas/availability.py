from pydantic import BaseModel, ConfigDict


class TeacherAvailabilityCreate(BaseModel):
    teacher_id: int
    academic_year_id: int
    day: int
    period: int
    available: bool = True
    preference: int = 0
    reason: str | None = None


class TeacherAvailabilityBatchUpdate(BaseModel):
    teacher_id: int
    academic_year_id: int
    unavailabilities: list[dict]  # [{"day": 0, "period": 1, "available": False, "preference": -2, "reason": ""}]


class TeacherAvailabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    teacher_id: int
    academic_year_id: int
    day: int
    period: int
    available: bool
    preference: int
    reason: str | None = None
