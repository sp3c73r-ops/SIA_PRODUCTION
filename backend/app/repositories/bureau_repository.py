from sqlalchemy.orm import Session

from app.models.bureau import Bureau


class BureauRepository:

    def get_all(self, db: Session):
        return db.query(Bureau).order_by(Bureau.id).all()

    def get_by_id(self, db: Session, bureau_id: int):
        return db.query(Bureau).filter(Bureau.id == bureau_id).first()

    def get_active_by_circonscription(self, db: Session, circonscription_id: int):
        return (
            db.query(Bureau)
            .filter(
                Bureau.circonscription_id == circonscription_id,
                Bureau.actif == True,
            )
            .order_by(Bureau.id)
            .all()
        )

    def get_by_code(self, db: Session, circonscription_id: int, code: str):
        return (
            db.query(Bureau)
            .filter(
                Bureau.circonscription_id == circonscription_id,
                Bureau.code == code,
            )
            .first()
        )

    def get_by_name(self, db: Session, circonscription_id: int, nom: str):
        return (
            db.query(Bureau)
            .filter(
                Bureau.circonscription_id == circonscription_id,
                Bureau.nom == nom,
            )
            .first()
        )

    def create(self, db: Session, bureau: Bureau):
        db.add(bureau)
        db.commit()
        db.refresh(bureau)
        return bureau

    def update(self, db: Session, bureau: Bureau):
        db.commit()
        db.refresh(bureau)
        return bureau


bureau_repository = BureauRepository()