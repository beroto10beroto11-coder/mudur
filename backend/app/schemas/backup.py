from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.backup import BackupStatus, BackupType


class BackupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    file_path: str
    file_size_bytes: int | None = None
    status: BackupStatus
    backup_type: BackupType
    duration_seconds: float | None = None
    error_message: str | None = None
    created_by_id: int | None = None
    created_at: datetime
