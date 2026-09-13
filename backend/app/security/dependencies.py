from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from sqlalchemy.orm import Session

from app.database.session import get_db

from app.repositories.auth_repository import auth_repository

from app.security.jwt import decode_access_token


security = HTTPBearer(
    bearerFormat="JWT",
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):

    token = credentials.credentials

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=401,
            detail="Token invalide",
        )

    username = payload.get("sub")

    if username is None:
        raise HTTPException(
            status_code=401,
            detail="Token invalide",
        )

    user = auth_repository.get_by_username(
        db,
        username,
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Utilisateur introuvable",
        )

    if not user.actif:
        raise HTTPException(
            status_code=401,
            detail="Utilisateur inactif",
        )

    return user