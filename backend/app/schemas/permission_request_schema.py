from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PermissionRequestCreate(BaseModel):
    permission: str
    document_id: Optional[int] = None
    reason: Optional[str] = None


class PermissionRequestApprove(BaseModel):
    duration_minutes: int = Field(ge=1, le=1440)


class PermissionRequestReject(BaseModel):
    reason: Optional[str] = None


class PermissionRequestResponse(BaseModel):
    id: int
    user_id: int
    bureau_id: int
    permission: str
    document_id: Optional[int] = None
    reason: Optional[str] = None
    status: str
    requested_at: datetime
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[int] = None
    expires_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
