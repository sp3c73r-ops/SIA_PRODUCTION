from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.phase import Phase
from app.models.document import Document


class PhaseRepository:

    def get_all(self, db: Session):
        return (
            db.query(Phase)
            .order_by(Phase.libelle)
            .all()
        )

    def create(self, db: Session, phase: Phase):
        db.add(phase)
        db.commit()
        db.refresh(phase)
        return phase

    def get_by_id(self, db: Session, phase_id: int):
        return (
            db.query(Phase)
            .filter(Phase.id == phase_id)
            .first()
        )

    def get_by_libelle(self, db: Session, libelle: str):
        normalized = libelle.strip().lower()
        return (
            db.query(Phase)
            .filter(
                func.lower(Phase.libelle)
                == normalized
            )
            .first()
        )

    def update(self, db: Session, phase: Phase):
        db.commit()
        db.refresh(phase)
        return phase

    def count_documents_using_phase(self, db: Session, phase_id: int) -> int:
        return (
            db.query(Document)
            .filter(Document.phase_id == phase_id)
            .count()
        )

    def delete(self, db: Session, phase: Phase):
        db.delete(phase)
        db.commit()
        return True


phase_repository = PhaseRepository()