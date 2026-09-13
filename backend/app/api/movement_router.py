from typing import List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from app.database.session import get_db

from app.models.user import User

from app.schemas.movement_schema import (
    MovementCreate,
    MovementResponse,
)

from app.services.movement_service import (
    movement_service,
)

from app.security.dependencies import (
    get_current_user,
)

from app.security.authorization import require_permission

from app.security.permissions import PERMISSION_MOVEMENT_CREATE
from app.security.permissions import PERMISSION_MOVEMENT_READ
from app.security.permissions import PERMISSION_MOVEMENT_UPDATE


router = APIRouter(
    prefix="/movements",
    tags=["Mouvements des archives"],
)


# ============================================================
# CREER UN MOUVEMENT
# ============================================================

@router.post(
    "/",
    response_model=MovementResponse,
)
def create_movement(
    data: MovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_MOVEMENT_CREATE)
    ),
):

    movement = movement_service.create(
        db,
        data,
        current_user,
    )

    return movement


# ============================================================
# LISTE DES MOUVEMENTS
# ============================================================

@router.get(
    "/",
    response_model=List[MovementResponse],
)
def list_movements(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_MOVEMENT_READ)
    ),
):

    return movement_service.get_all(
        db,
        current_user,
    )


# ============================================================
# MOUVEMENTS EN COURS
# ============================================================

@router.get(
    "/active",
    response_model=List[MovementResponse],
)
def list_active_movements(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_MOVEMENT_READ)
    ),
):

    return movement_service.get_active(
        db,
        current_user,
    )


# ============================================================
# MOUVEMENTS D'UN DOCUMENT
# ============================================================

@router.get(
    "/document/{document_id}",
    response_model=List[MovementResponse],
)
def list_document_movements(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_MOVEMENT_READ)
    ),
):

    return movement_service.get_by_document_id(
        db,
        document_id,
        current_user,
    )


# ============================================================
# MOUVEMENTS D'UN UTILISATEUR
# ============================================================

@router.get(
    "/user/{user_id}",
    response_model=List[MovementResponse],
)
def list_user_movements(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_MOVEMENT_READ)
    ),
):

    return movement_service.get_by_user_id(
        db,
        user_id,
        current_user,
    )


# ============================================================
# RECUPERER UN MOUVEMENT
# ============================================================

@router.get(
    "/{movement_id}",
    response_model=MovementResponse,
)
def get_movement(
    movement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_MOVEMENT_READ)
    ),
):

    movement = movement_service.get_by_id(
        db,
        movement_id,
        current_user,
    )

    if not movement:

        raise HTTPException(
            status_code=404,
            detail="Mouvement introuvable",
        )

    return movement


# ============================================================
# ENREGISTRER LE RETOUR D'UN DOCUMENT
# ============================================================

@router.put(
    "/{movement_id}/return",
    response_model=MovementResponse,
)
def return_movement(
    movement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_MOVEMENT_UPDATE)
    ),
):

    movement = movement_service.return_document(
        db,
        movement_id,
        current_user,
    )

    if not movement:

        raise HTTPException(
            status_code=404,
            detail="Mouvement introuvable",
        )

    return movement