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


auth_service = AuthService()