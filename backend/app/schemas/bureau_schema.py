from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BureauBase(BaseModel):
    code: str
    nom: str
    description: Optional[str] = None


class BureauCreate(BureauBase):
    circonscription_id: int


class BureauUpdate(BaseModel):
    code: Optional[str] = None
    nom: Optional[str] = None
    description: Optional[str] = None


class BureauResponse(BureauBase):
    id: int
    circonscription_id: int
    actif: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)