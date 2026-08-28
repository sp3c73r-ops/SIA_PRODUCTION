from sqlalchemy.orm import Session

from app.models.document_type import DocumentType


class DocumentTypeRepository:

    def get_all(self, db: Session):
        return (
            db.query(DocumentType)
            .order_by(DocumentType.libelle)
            .all()
        )

    def get_by_id(self, db: Session, item_id: int):
        return (
            db.query(DocumentType)
            .filter(DocumentType.id == item_id)
            .first()
        )

    def create(self, db: Session, libelle: str):

        item = DocumentType(
            libelle=libelle
        )

        db.add(item)

        db.commit()

        db.refresh(item)

        return item

    def update(self, db: Session, item, libelle):

        item.libelle = libelle

        db.commit()

        db.refresh(item)

        return item

    def delete(self, db: Session, item):

        db.delete(item)

        db.commit()