from sqlalchemy.orm import Session

from app.models.bureau import Bureau
from app.models.circonscription import Circonscription


class CirconscriptionRepository:

    def get_all(self, db: Session):
        return (
            db.query(Circonscription)
            .order_by(Circonscription.nom)
            .all()
        )

    def get_by_bureau_id(self, db: Session, bureau_id: int):
        return (
            db.query(Circonscription)
            .join(
                Bureau,
                Bureau.circonscription_id == Circonscription.id,
            )
            .filter(Bureau.id == bureau_id)
            .first()
        )

    def create(self, db: Session, circonscription: Circonscription):
        db.add(circonscription)
        db.commit()
        db.refresh(circonscription)
        return circonscription


circonscription_repository = CirconscriptionRepository()