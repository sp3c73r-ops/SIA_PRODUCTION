from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.security.dependencies import get_current_user
from app.schemas.circonscription_schema import (
    CirconscriptionCreate,
    CirconscriptionResponse,
)
from app.services.circonscription_service import (
    circonscription_service,
)

router = APIRouter(
    prefix="/circonscriptions",
    tags=["Circonscriptions"],
)


@router.get(
    "/",
    response_model=List[CirconscriptionResponse],
)
def get_circonscriptions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return circonscription_service.get_all(db, current_user)


@router.post(
    "/",
    response_model=CirconscriptionResponse,
)
def create_circonscription(
    data: CirconscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return circonscription_service.create(db, data, current_user)