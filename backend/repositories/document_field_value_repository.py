from sqlalchemy.orm import Session

from app.models.document_field_value import DocumentFieldValue


class DocumentFieldValueRepository:

    def get_by_document_id(
        self,
        db: Session,
        document_id: int,
    ):
        return (
            db.query(DocumentFieldValue)
            .filter(
                DocumentFieldValue.document_id
                == document_id
            )
            .all()
        )

    def get_by_document_and_field(
        self,
        db: Session,
        document_id: int,
        field_id: int,
    ):
        return (
            db.query(DocumentFieldValue)
            .filter(
                DocumentFieldValue.document_id
                == document_id,
                DocumentFieldValue.document_field_id
                == field_id,
            )
            .first()
        )

    def count_by_field_id(
        self,
        db: Session,
        field_id: int,
    ) -> int:
        return (
            db.query(DocumentFieldValue)
            .filter(
                DocumentFieldValue.document_field_id
                == field_id
            )
            .count()
        )


document_field_value_repository = (
    DocumentFieldValueRepository()
)
