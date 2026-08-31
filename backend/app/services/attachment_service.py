import os
import uuid

from pathlib import Path

from fastapi import HTTPException
from fastapi import UploadFile

from sqlalchemy.orm import Session

from app.models.attachment import DocumentAttachment
from app.models.user import User
from app.repositories.document_repository import (
    document_repository,
)

from app.repositories.attachment_repository import (
    attachment_repository,
)
from app.security.authorization import has_effective_permission
from app.security.authorization import is_admin
from app.security.permissions import PERMISSION_ATTACHMENT_CREATE
from app.security.permissions import PERMISSION_ATTACHMENT_DELETE
from app.security.permissions import PERMISSION_ATTACHMENT_DOWNLOAD
from app.security.permissions import PERMISSION_ATTACHMENT_READ
from app.security.permissions import is_known_permission


UPLOAD_DIR = Path(
    "app/uploads/documents"
)


class AttachmentService:

    def _ensure_permission(
        self,
        db: Session,
        current_user: User,
        permission: str,
        bureau_id: int | None = None,
        document_id: int | None = None,
    ):
        if not is_known_permission(permission):
            raise HTTPException(
                status_code=403,
                detail="Acces refuse: permission insuffisante.",
            )

        if not has_effective_permission(
            db,
            current_user,
            permission,
            document_id=document_id,
            bureau_id=bureau_id,
        ):
            raise HTTPException(
                status_code=403,
                detail="Acces refuse: permission insuffisante.",
            )

    def _get_scope_bureau_id(
        self,
        current_user: User,
    ) -> int | None:
        if is_admin(current_user):
            return None

        user_bureau_id = getattr(
            current_user,
            "bureau_id",
            None,
        )

        if user_bureau_id is None:
            raise HTTPException(
                status_code=403,
                detail="Acces refuse: bureau non assigne.",
            )

        return user_bureau_id

    def _get_document_in_scope(
        self,
        db: Session,
        document_id: int,
        scope_bureau_id: int | None,
    ):
        document = document_repository.get_by_id(
            db,
            document_id,
            bureau_id=scope_bureau_id,
        )

        if document is not None:
            return document

        existing_document = document_repository.get_by_id(
            db,
            document_id,
        )

        if existing_document is None:
            raise HTTPException(
                status_code=404,
                detail="Document introuvable",
            )

        raise HTTPException(
            status_code=403,
            detail="Acces interdit a ce document.",
        )

    # ============================================================
    # CREER UNE PIECE JOINTE
    # ============================================================

    def create(
        self,
        db: Session,
        document_id: int,
        file: UploadFile,
        current_user: User,
    ):

        scope_bureau_id = self._get_scope_bureau_id(
            current_user,
        )

        self._ensure_permission(
            db,
            current_user,
            PERMISSION_ATTACHMENT_CREATE,
            bureau_id=scope_bureau_id,
            document_id=document_id,
        )

        self._get_document_in_scope(
            db,
            document_id,
            scope_bureau_id,
        )

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
        current_user: User,
    ):

        scope_bureau_id = self._get_scope_bureau_id(
            current_user,
        )

        self._ensure_permission(
            db,
            current_user,
            PERMISSION_ATTACHMENT_READ,
            bureau_id=scope_bureau_id,
        )

        if scope_bureau_id is None:
            return attachment_repository.get_all(
                db
            )

        return attachment_repository.get_all_by_bureau(
            db,
            bureau_id=scope_bureau_id,
        )


    # ============================================================
    # PIECES JOINTES D'UN DOCUMENT
    # ============================================================

    def get_by_document_id(
        self,
        db: Session,
        document_id: int,
        current_user: User,
    ):

        scope_bureau_id = self._get_scope_bureau_id(
            current_user,
        )

        self._ensure_permission(
            db,
            current_user,
            PERMISSION_ATTACHMENT_READ,
            bureau_id=scope_bureau_id,
            document_id=document_id,
        )

        self._get_document_in_scope(
            db,
            document_id,
            scope_bureau_id,
        )

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
        current_user: User,
    ):

        attachment = attachment_repository.get_by_id(
            db,
            attachment_id,
        )

        if attachment is None:
            return None

        document = document_repository.get_by_id(
            db,
            attachment.document_id,
        )

        if document is None:
            return None

        scope_bureau_id = self._get_scope_bureau_id(
            current_user,
        )

        if (
            scope_bureau_id is not None
            and document.bureau_id != scope_bureau_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Acces interdit a cette piece jointe.",
            )

        self._ensure_permission(
            db,
            current_user,
            PERMISSION_ATTACHMENT_DOWNLOAD,
            bureau_id=document.bureau_id,
            document_id=document.id,
        )

        return attachment


    # ============================================================
    # SUPPRIMER UNE PIECE JOINTE
    # ============================================================

    def delete(
        self,
        db: Session,
        attachment_id: int,
        current_user: User,
    ):

        attachment = (
            attachment_repository.get_by_id(
                db,
                attachment_id,
            )
        )

        if not attachment:
            return False

        document = document_repository.get_by_id(
            db,
            attachment.document_id,
        )

        if document is None:
            return False

        scope_bureau_id = self._get_scope_bureau_id(
            current_user,
        )

        if (
            scope_bureau_id is not None
            and document.bureau_id != scope_bureau_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Acces interdit a cette piece jointe.",
            )

        self._ensure_permission(
            db,
            current_user,
            PERMISSION_ATTACHMENT_DELETE,
            bureau_id=document.bureau_id,
            document_id=document.id,
        )

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