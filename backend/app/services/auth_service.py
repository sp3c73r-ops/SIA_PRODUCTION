from fastapi import HTTPException
from sqlalchemy.orm import joinedload

from app.models.bureau import Bureau
from app.models.user import USER_ROLE_ADMIN, User
from app.repositories.auth_repository import auth_repository

from app.security.password import verify_password
from app.security.jwt import create_access_token


class AuthService:

    def __init__(self):
        self.repository = auth_repository

    def login(
        self,
        db,
        username: str,
        password: str,
    ):

        user = self.repository.get_by_username(
            db,
            username,
        )

        if not user:
            return None

        if not verify_password(
            password,
            user.password,
        ):
            return None

        token = create_access_token(
            {
                "sub": user.username,
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    def get_current_user_profile(self, db, current_user: User):
        user = (
            db.query(User)
            .options(
                joinedload(User.bureau).joinedload(
                    Bureau.circonscription
                ),
                joinedload(User.admin_circonscription),
            )
            .filter(User.id == current_user.id)
            .first()
        )

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Utilisateur introuvable",
            )

        bureau = user.bureau
        circonscription = (
            user.admin_circonscription
            if user.role == USER_ROLE_ADMIN
            else getattr(bureau, "circonscription", None)
        )

        return {
            "id": user.id,
            "nom": user.nom,
            "prenom": user.prenom,
            "username": user.username,
            "actif": user.actif,
            "role": user.role,
            "bureau": (
                {
                    "id": bureau.id,
                    "nom": bureau.nom,
                }
                if bureau is not None
                else None
            ),
            "circonscription": (
                {
                    "id": circonscription.id,
                    "nom": circonscription.nom,
                }
                if circonscription is not None
                else None
            ),
            "permissions": user.permissions or [],
        }


auth_service = AuthService()