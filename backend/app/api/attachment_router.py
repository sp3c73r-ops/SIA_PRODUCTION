from pathlib import Path
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    UploadFile,
    HTTPException,
)

from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.database.session import get_db

from app.schemas.attachment_schema import (
    AttachmentResponse,
)

from app.services.attachment_service import (
    attachment_service,
)

from app.security.dependencies import (
    get_current_user,
)

from app.models.user import User


router = APIRouter(
    prefix="/documents",
    tags=["Pièces jointes"],
)


# ============================================================
# LISTE GLOBALE DES PIECES JOINTES
# IMPORTANT :
# Cette route doit être AVANT /{document_id}/attachments
# ============================================================

@router.get(
    "/attachments/all",
    response_model=List[AttachmentResponse],
)
def list_all_attachments(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    return attachment_service.get_all(
        db
    )


# ============================================================
# TELECHARGER / OUVRIR UNE PIECE JOINTE
# IMPORTANT :
# Cette route doit être AVANT /{document_id}/attachments
# ============================================================

@router.get(
    "/attachments/{attachment_id}/download",
)
def download_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    attachment = (
        attachment_service.get_by_id(
            db,
            attachment_id,
        )
    )

    if not attachment:

        raise HTTPException(
            status_code=404,
            detail="Pièce jointe introuvable",
        )

    file_path = Path(
        attachment.chemin_fichier
    )

    if not file_path.exists():

        raise HTTPException(
            status_code=404,
            detail="Fichier physique introuvable",
        )

    return FileResponse(
        path=file_path,
        media_type=attachment.type_mime,
        filename=attachment.nom_original,
    )


# ============================================================
# SUPPRIMER UNE PIECE JOINTE
# ============================================================

@router.delete(
    "/attachments/{attachment_id}",
)
def delete_attachment(
    attachment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    success = attachment_service.delete(
        db,
        attachment_id,
    )

    if not success:

        raise HTTPException(
            status_code=404,
            detail="Pièce jointe introuvable",
        )

    return {
        "message": "Pièce jointe supprimée"
    }


# ============================================================
# AJOUTER UNE PIECE JOINTE A UN DOCUMENT
# ============================================================

@router.post(
    "/{document_id}/attachments",
    response_model=AttachmentResponse,
)
def upload_attachment(
    document_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    attachment = attachment_service.create(
        db,
        document_id,
        file,
    )

    return attachment


# ============================================================
# LISTE DES PIECES JOINTES D'UN DOCUMENT
# ============================================================

@router.get(
    "/{document_id}/attachments",
    response_model=List[AttachmentResponse],
)
def list_attachments(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    return attachment_service.get_by_document_id(
        db,
        document_id,
    )