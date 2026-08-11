from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    global_role: UserRole = UserRole.VIEWER
    teacher_id: int | None = None
    school_ids: list[int] = []


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
    password: str | None = None
    global_role: UserRole | None = None
    is_active: bool | None = None
    teacher_id: int | None = None


class UserDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    full_name: str
    global_role: UserRole
    is_active: bool
    is_verified: bool
    teacher_id: int | None = None
    created_at: datetime
    updated_at: datetime
