from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:

    def get_all(self, db: Session):
        return (
            db.query(User)
            .order_by(User.nom)
            .all()
        )

    def get_by_username(self, db: Session, username: str):
        return (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

    def get_by_id(self, db: Session, user_id: int):
        return (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    def create(self, db: Session, user: User):
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def update(self, db: Session, user: User):
        db.commit()
        db.refresh(user)
        return user


user_repository = UserRepository()