from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    id: int
    recipient_user_id: int
    action: str
    title: str
    message: str
    permission_request_id: Optional[int] = None
    document_id: Optional[int] = None
    bureau_id: Optional[int] = None
    circonscription_id: Optional[int] = None
    read_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationUnreadCountResponse(BaseModel):
    unread_count: int


class NotificationMarkAllReadResponse(BaseModel):
    updated_count: int
