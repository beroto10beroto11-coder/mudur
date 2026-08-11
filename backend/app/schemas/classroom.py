from datetime import datetime
from pydantic import BaseModel, ConfigDict


class ClassroomCreate(BaseModel):
    name: str
    capacity: int = 30
    room_type: str = "normal"
    floor: int | None = None
    building: str | None = None
    notes: str | None = None
    is_active: bool = True


class ClassroomUpdate(BaseModel):
    name: str | None = None
    capacity: int | None = None
    room_type: str | None = None
    floor: int | None = None
    building: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class ClassroomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    name: str
    capacity: int
    room_type: str
    floor: int | None = None
    building: str | None = None
    notes: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
