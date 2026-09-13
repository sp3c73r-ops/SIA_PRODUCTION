from datetime import date, datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentEncoderResponse(BaseModel):
    id: int
    nom: Optional[str] = None
    prenom: Optional[str] = None
    username: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentBase(BaseModel):
    reference_archive: str
    nom_document: str
    date_creation: date

    type_document_id: Optional[int] = None
    phase_id: Optional[int] = None
    circonscription_id: Optional[int] = None
    encodeur_id: Optional[int] = None

    code_foncier: Optional[str] = None
    numero_ordre: Optional[str] = None
    remarque: Optional[str] = None
    custom_fields: dict[str, Any] = Field(default_factory=dict)


class DocumentCreate(DocumentBase):
    pass


class DocumentUpdate(BaseModel):
    reference_archive: Optional[str] = None
    nom_document: Optional[str] = None
    date_creation: Optional[date] = None

    type_document_id: Optional[int] = None
    phase_id: Optional[int] = None
    circonscription_id: Optional[int] = None

    code_foncier: Optional[str] = None
    numero_ordre: Optional[str] = None
    remarque: Optional[str] = None
    custom_fields: Optional[dict[str, Any]] = None


class DocumentResponse(DocumentBase):
    id: int

    encodeur: Optional[DocumentEncoderResponse] = None

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)