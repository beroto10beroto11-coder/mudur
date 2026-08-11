from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int | None = None
    user_email: str | None = None
    school_id: int | None = None
    action: str
    entity_type: str
    entity_id: int | None = None
    entity_name: str | None = None
    old_data: dict | None = None
    new_data: dict | None = None
    description: str | None = None
    ip_address: str | None = None
    created_at: datetime
