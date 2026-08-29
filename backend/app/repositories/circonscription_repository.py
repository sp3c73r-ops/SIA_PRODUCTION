from sqlalchemy.orm import Session

from app.models.circonscription import Circonscription


class CirconscriptionRepository:

    def get_all(self, db: Session):
        return (
            db.query(Circonscription)
            .order_by(Circonscription.nom)
            .all()
        )

    def create(self, db: Session, circonscription: Circonscription):
        db.add(circonscription)
        db.commit()
        db.refresh(circonscription)
        return circonscription


circonscription_repository = CirconscriptionRepository()