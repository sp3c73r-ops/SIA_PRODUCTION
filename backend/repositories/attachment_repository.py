from sqlalchemy.orm import Session

from app.models.attachment import DocumentAttachment


class AttachmentRepository:

    # ============================================================
    # CREER UNE PIECE JOINTE
    # ============================================================

    def create(
        self,
        db: Session,
        attachment: DocumentAttachment,
    ):

        db.add(attachment)

        db.commit()

        db.refresh(attachment)

        return attachment


    # ============================================================
    # RECUPERER UNE PIECE JOINTE PAR ID
    # ============================================================

    def get_by_id(
        self,
        db: Session,
        attachment_id: int,
    ):

        return (
            db.query(DocumentAttachment)
            .filter(
                DocumentAttachment.id == attachment_id
            )
            .first()
        )


    # ============================================================
    # RECUPERER TOUTES LES PIECES JOINTES
    # ============================================================

    def get_all(
        self,
        db: Session,
    ):

        return (
            db.query(DocumentAttachment)
            .order_by(
                DocumentAttachment.created_at.desc()
            )
            .all()
        )


    # ============================================================
    # PIECES JOINTES D'UN DOCUMENT
    # ============================================================

    def get_by_document_id(
        self,
        db: Session,
        document_id: int,
    ):

        return (
            db.query(DocumentAttachment)
            .filter(
                DocumentAttachment.document_id
                == document_id
            )
            .order_by(
                DocumentAttachment.id.asc()
            )
            .all()
        )


    # ============================================================
    # SUPPRIMER UNE PIECE JOINTE
    # ============================================================

    def delete(
        self,
        db: Session,
        attachment: DocumentAttachment,
    ):

        db.delete(attachment)

        db.commit()

        return True


attachment_repository = AttachmentRepository()