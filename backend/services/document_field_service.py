from typing import Optional

from sqlalchemy.orm import Session

from app.models.document_field import DocumentField
from app.repositories.document_field_repository import (
    document_field_repository,
)
from app.repositories.document_field_value_repository import (
    document_field_value_repository,
)
from app.schemas.document_field_schema import (
    DocumentFieldCreate,
    DocumentFieldUpdate,
)


class DocumentFieldService:

    def __init__(self):
        self.repository = document_field_repository
        self.value_repository = (
            document_field_value_repository
        )

    def get_all(self, db: Session):
        return self.repository.get_all(db)

    def get_by_id(self, db: Session, item_id: int):
        return self.repository.get_by_id(db, item_id)

    def create(self, db: Session, data: DocumentFieldCreate):
        existing = self.repository.get_by_name(db, data.name)
        if existing:
            raise ValueError("Ce nom technique existe déjà.")

        item = DocumentField(**data.model_dump())
        return self.repository.create(db, item)

    def update(self, db: Session, item_id: int, data: DocumentFieldUpdate):
        item = self.repository.get_by_id(db, item_id)
        if not item:
            return None

        if data.name is not None and data.name != item.name:
            existing = self.repository.get_by_name(db, data.name)
            if existing and existing.id != item.id:
                raise ValueError("Ce nom technique existe déjà.")

        if (
            data.field_type is not None
            and data.field_type != item.field_type
        ):
            value_count = self.value_repository.count_by_field_id(
                db,
                item.id,
            )
            if value_count > 0:
                raise ValueError(
                    "Le type ne peut pas être modifié car ce champ possède déjà des valeurs."
                )

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(item, key, value)

        return self.repository.update(db, item)

    def delete(self, db: Session, item_id: int):
        item = self.repository.get_by_id(db, item_id)
        if not item:
            return False

        value_count = self.value_repository.count_by_field_id(
            db,
            item.id,
        )

        if value_count > 0:
            raise ValueError(
                "Ce champ ne peut pas être supprimé car il est déjà utilisé par des documents."
            )

        return self.repository.delete(db, item)

    def toggle_active(self, db: Session, item_id: int, active: bool):
        item = self.repository.get_by_id(db, item_id)
        if not item:
            return None

        item.active = active
        return self.repository.update(db, item)


document_field_service = DocumentFieldService()
