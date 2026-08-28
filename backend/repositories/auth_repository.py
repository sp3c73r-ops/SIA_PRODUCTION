from sqlalchemy.orm import Session

from app.models.user import User


class AuthRepository:

    def get_by_username(
        self,
        db: Session,
        username: str,
    ):
        return (
            db.query(User)
            .filter(User.username == username)
            .first()
        )


auth_repository = AuthRepository()