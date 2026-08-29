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
        get_current_user
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
        get_current_user
    ),
):

    return movement_service.get_all(
        db
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
        get_current_user
    ),
):

    return movement_service.get_active(
        db
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
        get_current_user
    ),
):

    return movement_service.get_by_document_id(
        db,
        document_id,
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
        get_current_user
    ),
):

    return movement_service.get_by_user_id(
        db,
        user_id,
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
        get_current_user
    ),
):

    movement = movement_service.get_by_id(
        db,
        movement_id,
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
        get_current_user
    ),
):

    movement = movement_service.return_document(
        db,
        movement_id,
    )

    if not movement:

        raise HTTPException(
            status_code=404,
            detail="Mouvement introuvable",
        )

    return movement