from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.security.dependencies import get_current_user
from app.schemas.document_field_schema import (
    DocumentFieldCreate,
    DocumentFieldResponse,
    DocumentFieldUpdate,
)
from app.services.document_field_service import document_field_service

router = APIRouter(
    prefix="/document-fields",
    tags=["Document Fields"],
)


@router.get(
    "/",
    response_model=List[DocumentFieldResponse],
)
def get_document_fields(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return document_field_service.get_all(db)


@router.get(
    "/{field_id}",
    response_model=DocumentFieldResponse,
)
def get_document_field(
    field_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    field = document_field_service.get_by_id(db, field_id)
    if not field:
        raise HTTPException(
            status_code=404,
            detail="Champ introuvable.",
        )
    return field


@router.post(
    "/",
    response_model=DocumentFieldResponse,
)
def create_document_field(
    data: DocumentFieldCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return document_field_service.create(db, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.put(
    "/{field_id}",
    response_model=DocumentFieldResponse,
)
def update_document_field(
    field_id: int,
    data: DocumentFieldUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        item = document_field_service.update(db, field_id, data)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if not item:
        raise HTTPException(
            status_code=404,
            detail="Champ introuvable.",
        )

    return item


@router.patch(
    "/{field_id}/toggle-active",
    response_model=DocumentFieldResponse,
)
def toggle_document_field_active(
    field_id: int,
    active: bool,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    item = document_field_service.toggle_active(db, field_id, active)
    if not item:
        raise HTTPException(
            status_code=404,
            detail="Champ introuvable.",
        )
    return item


@router.delete(
    "/{field_id}",
)
def delete_document_field(
    field_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        success = document_field_service.delete(db, field_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Champ introuvable.",
        )
    return {"message": "Champ supprimé."}
