from datetime import datetime
from pydantic import BaseModel, ConfigDict


class SchoolCreate(BaseModel):
    name: str
    short_name: str | None = None
    city: str | None = None
    district: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool = True


class SchoolUpdate(BaseModel):
    name: str | None = None
    short_name: str | None = None
    city: str | None = None
    district: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool | None = None


class SchoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    short_name: str | None = None
    city: str | None = None
    district: str | None = None
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AcademicYearCreate(BaseModel):
    name: str
    start_date: str | None = None
    end_date: str | None = None
    days_per_week: int = 5
    periods_per_day: int = 8
    is_active: bool = False


class AcademicYearUpdate(BaseModel):
    name: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    days_per_week: int | None = None
    periods_per_day: int | None = None
    is_active: bool | None = None


class AcademicYearResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    name: str
    start_date: str | None = None
    end_date: str | None = None
    days_per_week: int
    periods_per_day: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
