import os
import uuid

from pathlib import Path

from fastapi import UploadFile

from sqlalchemy.orm import Session

from app.models.attachment import DocumentAttachment

from app.repositories.attachment_repository import (
    attachment_repository,
)


UPLOAD_DIR = Path(
    "app/uploads/documents"
)


class AttachmentService:

    # ============================================================
    # CREER UNE PIECE JOINTE
    # ============================================================

    def create(
        self,
        db: Session,
        document_id: int,
        file: UploadFile,
    ):

        document_dir = (
            UPLOAD_DIR
            / str(document_id)
        )

        document_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        original_name = (
            file.filename
            or "fichier"
        )

        extension = Path(
            original_name
        ).suffix

        stored_name = (
            f"{uuid.uuid4().hex}"
            f"{extension}"
        )

        file_path = (
            document_dir
            / stored_name
        )

        content = file.file.read()

        with open(
            file_path,
            "wb",
        ) as buffer:

            buffer.write(content)

        attachment = DocumentAttachment(
            document_id=document_id,
            nom_original=original_name,
            nom_stockage=stored_name,
            chemin_fichier=str(
                file_path
            ),
            type_mime=file.content_type,
            taille=len(content),
        )

        return attachment_repository.create(
            db,
            attachment,
        )


    # ============================================================
    # TOUTES LES PIECES JOINTES
    # ============================================================

    def get_all(
        self,
        db: Session,
    ):

        return attachment_repository.get_all(
            db
        )


    # ============================================================
    # PIECES JOINTES D'UN DOCUMENT
    # ============================================================

    def get_by_document_id(
        self,
        db: Session,
        document_id: int,
    ):

        return attachment_repository.get_by_document_id(
            db,
            document_id,
        )


    # ============================================================
    # PIECE JOINTE PAR ID
    # ============================================================

    def get_by_id(
        self,
        db: Session,
        attachment_id: int,
    ):

        return attachment_repository.get_by_id(
            db,
            attachment_id,
        )


    # ============================================================
    # SUPPRIMER UNE PIECE JOINTE
    # ============================================================

    def delete(
        self,
        db: Session,
        attachment_id: int,
    ):

        attachment = (
            attachment_repository.get_by_id(
                db,
                attachment_id,
            )
        )

        if not attachment:
            return False

        file_path = Path(
            attachment.chemin_fichier
        )

        if file_path.exists():

            os.remove(
                file_path
            )

        return attachment_repository.delete(
            db,
            attachment,
        )


attachment_service = AttachmentService()