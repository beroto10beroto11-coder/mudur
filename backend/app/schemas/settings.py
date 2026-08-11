from pydantic import BaseModel, ConfigDict


class SystemSettingUpdate(BaseModel):
    value: str
    description: str | None = None


class SystemSettingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int | None = None
    key: str
    value: str | None = None
    description: str | None = None
    value_type: str
