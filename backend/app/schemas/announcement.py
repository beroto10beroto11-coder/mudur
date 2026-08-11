from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AnnouncementCreate(BaseModel):
    title: str
    content: str
    is_pinned: bool = False
    expires_at: str | None = None


class AnnouncementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    created_by_id: int | None = None
    title: str
    content: str
    is_pinned: bool
    is_active: bool
    expires_at: str | None = None
    created_at: datetime
