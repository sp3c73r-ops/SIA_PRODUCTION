from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


# ============================================================
# CREATION D'UN MOUVEMENT
# ============================================================

class MovementCreate(BaseModel):

    document_id: int

    type_mouvement: str

    motif: Optional[str] = None


# ============================================================
# REPONSE
# ============================================================

class MovementResponse(BaseModel):

    id: int

    document_id: int

    user_id: int

    type_mouvement: str

    motif: Optional[str] = None

    statut: str

    date_mouvement: datetime

    date_retour: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True
    )