from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.database.session import get_db

from app.models.user import User

from app.schemas.auth_schema import (
    LoginRequest,
    TokenResponse,
)

from app.schemas.user_schema import UserResponse

from app.security.dependencies import get_current_user

from app.services.auth_service import auth_service


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):

    token = auth_service.login(
        db,
        data.username,
        data.password,
    )

    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Nom d'utilisateur ou mot de passe incorrect",
        )

    return token


@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user
