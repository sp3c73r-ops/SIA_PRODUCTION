from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AttachmentResponse(BaseModel):
    id: int
    document_id: int
    nom_original: str
    nom_stockage: str
    chemin_fichier: str
    type_mime: Optional[str] = None
    taille: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True
    )