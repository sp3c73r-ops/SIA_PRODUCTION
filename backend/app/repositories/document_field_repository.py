from sqlalchemy.orm import Session

from app.models.document_field import DocumentField


class DocumentFieldRepository:

    def get_all(self, db: Session):
        return (
            db.query(DocumentField)
            .order_by(
                DocumentField.order_index.asc(),
                DocumentField.id.asc(),
            )
            .all()
        )

    def get_by_id(self, db: Session, item_id: int):
        return (
            db.query(DocumentField)
            .filter(DocumentField.id == item_id)
            .first()
        )

    def get_by_name(self, db: Session, name: str):
        return (
            db.query(DocumentField)
            .filter(DocumentField.name == name)
            .first()
        )

    def get_active(self, db: Session):
        return (
            db.query(DocumentField)
            .filter(DocumentField.active == True)
            .order_by(
                DocumentField.order_index.asc(),
                DocumentField.id.asc(),
            )
            .all()
        )

    def get_by_ids(self, db: Session, ids: list[int]):
        if not ids:
            return []

        return (
            db.query(DocumentField)
            .filter(DocumentField.id.in_(ids))
            .all()
        )

    def create(self, db: Session, item: DocumentField):
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def update(self, db: Session, item: DocumentField):
        db.commit()
        db.refresh(item)
        return item

    def delete(self, db: Session, item: DocumentField):
        db.delete(item)
        db.commit()
        return True


document_field_repository = DocumentFieldRepository()
