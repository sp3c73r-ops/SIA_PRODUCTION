from datetime import date
from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
)

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database.session import get_db

from app.models.user import User

from app.schemas.document_schema import (
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse,
)

from app.security.dependencies import (
    get_current_user,
)
from app.security.authorization import require_permission
from app.security.permissions import PERMISSION_DOCUMENT_CREATE
from app.security.permissions import PERMISSION_DOCUMENT_DELETE
from app.security.permissions import PERMISSION_DOCUMENT_READ
from app.security.permissions import PERMISSION_DOCUMENT_UPDATE

from app.services.document_service import (
    document_service,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# ============================================================
# CREER UN DOCUMENT
# ============================================================

@router.post(
    "/",
    response_model=DocumentResponse,
)
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_DOCUMENT_CREATE)
    ),
):

    return document_service.create(
        db,
        document,
        current_user,
    )


@router.post(
    "/with-attachment",
    response_model=DocumentResponse,
)
def create_document_with_attachment(
    document_json: str = Form(...),
    file: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_DOCUMENT_CREATE)
    ),
):
    try:
        document = DocumentCreate.model_validate_json(
            document_json
        )
    except ValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=exc.errors(),
        )

    return document_service.create(
        db,
        document,
        current_user,
        initial_files=file,
    )


# ============================================================
# RECHERCHE AVANCEE
# IMPORTANT : AVANT /{document_id}
# ============================================================

@router.get(
    "/search",
    response_model=List[DocumentResponse],
)
def search_documents(
    reference_archive: Optional[str] = Query(
        default=None
    ),

    nom_document: Optional[str] = Query(
        default=None
    ),

    code_foncier: Optional[str] = Query(
        default=None
    ),

    numero_ordre: Optional[str] = Query(
        default=None
    ),

    type_document_id: Optional[int] = Query(
        default=None
    ),

    phase_id: Optional[int] = Query(
        default=None
    ),

    circonscription_id: Optional[int] = Query(
        default=None
    ),

    date_debut: Optional[date] = Query(
        default=None
    ),

    date_fin: Optional[date] = Query(
        default=None
    ),

    db: Session = Depends(get_db),

    current_user: User = Depends(
        require_permission(PERMISSION_DOCUMENT_READ)
    ),
):

    if (
        date_debut
        and date_fin
        and date_debut > date_fin
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "La date de début ne peut pas "
                "être supérieure à la date de fin."
            ),
        )

    return document_service.search(
        db=db,
        current_user=current_user,
        reference_archive=reference_archive,
        nom_document=nom_document,
        code_foncier=code_foncier,
        numero_ordre=numero_ordre,
        type_document_id=type_document_id,
        phase_id=phase_id,
        circonscription_id=circonscription_id,
        date_debut=date_debut,
        date_fin=date_fin,
    )


# ============================================================
# LISTE DES DOCUMENTS
# ============================================================

@router.get(
    "/",
    response_model=List[DocumentResponse],
)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_DOCUMENT_READ)
    ),
):

    return document_service.get_all(
        db,
        current_user,
    )


# ============================================================
# DOCUMENT PAR ID
# ============================================================

@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_DOCUMENT_READ)
    ),
):

    document = document_service.get_by_id(
        db,
        document_id,
        current_user,
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document introuvable",
        )

    return document


# ============================================================
# MODIFIER
# ============================================================

@router.put(
    "/{document_id}",
    response_model=DocumentResponse,
)
def update_document(
    document_id: int,
    data: DocumentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
):

    document = document_service.update(
        db,
        document_id,
        data,
        current_user,
    )

    if not document:

        raise HTTPException(
            status_code=404,
            detail="Document introuvable",
        )

    return document


# ============================================================
# SUPPRIMER
# ============================================================

@router.delete(
    "/{document_id}",
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_DOCUMENT_DELETE)
    ),
):

    success = document_service.delete(
        db,
        document_id,
        current_user,
    )

    if not success:

        raise HTTPException(
            status_code=404,
            detail="Document introuvable",
        )

    return {
        "message": "Document supprimé"
    }