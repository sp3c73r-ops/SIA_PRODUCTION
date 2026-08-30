from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.permission_request import PermissionRequest
from app.models.permission_request import PERMISSION_REQUEST_STATUS_PENDING
from app.models.user import USER_ROLE_USER
from app.models.user import User
from app.repositories.document_repository import document_repository
from app.repositories.permission_request_repository import permission_request_repository
from app.security.authorization import is_admin
from app.security.permissions import is_known_permission


class PermissionRequestService:

    def _ensure_user(self, current_user: User):
        if getattr(current_user, "role", None) != USER_ROLE_USER:
            raise HTTPException(
                status_code=403,
                detail="Acces reserve aux utilisateurs USER.",
            )

    def _ensure_admin(self, current_user: User):
        if not is_admin(current_user):
            raise HTTPException(
                status_code=403,
                detail="Acces reserve a l'administrateur.",
            )

    def _validate_known_permission(self, permission: str) -> str:
        normalized_permission = permission.strip() if isinstance(permission, str) else ""

        if not normalized_permission:
            raise HTTPException(
                status_code=400,
                detail="Permission invalide.",
            )

        if not is_known_permission(normalized_permission):
            raise HTTPException(
                status_code=400,
                detail="Permission inconnue.",
            )

        return normalized_permission

    def create(self, db: Session, current_user: User, data):
        self._ensure_user(current_user)

        bureau_id = getattr(current_user, "bureau_id", None)
        if bureau_id is None:
            raise HTTPException(
                status_code=403,
                detail="Acces refuse: bureau non assigne.",
            )

        permission = self._validate_known_permission(data.permission)
        document_id = data.document_id

        if document_id is not None:
            scoped_document = document_repository.get_by_id(
                db,
                document_id,
                bureau_id=bureau_id,
            )

            if scoped_document is None:
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

        duplicate_pending = permission_request_repository.find_pending_duplicate(
            db,
            user_id=current_user.id,
            permission=permission,
            document_id=document_id,
        )

        if duplicate_pending is not None:
            raise HTTPException(
                status_code=409,
                detail="Une demande identique est deja en attente.",
            )

        request = permission_request_repository.create(
            db,
            request=PermissionRequest(
                user_id=current_user.id,
                bureau_id=bureau_id,
                permission=permission,
                document_id=document_id,
                reason=data.reason,
                status=PERMISSION_REQUEST_STATUS_PENDING,
            ),
        )

        return request

    def get_me(self, db: Session, current_user: User):
        self._ensure_user(current_user)

        return permission_request_repository.get_by_user_id(
            db,
            current_user.id,
        )

    def cancel(self, db: Session, request_id: int, current_user: User):
        self._ensure_user(current_user)

        request = permission_request_repository.get_by_id(
            db,
            request_id,
        )

        if request is None:
            raise HTTPException(
                status_code=404,
                detail="Demande introuvable",
            )

        if request.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Acces interdit a cette demande.",
            )

        if request.status != PERMISSION_REQUEST_STATUS_PENDING:
            raise HTTPException(
                status_code=403,
                detail="Cette demande ne peut plus etre annulee.",
            )

        return permission_request_repository.cancel(db, request)

    def get_all(self, db: Session, current_user: User):
        self._ensure_admin(current_user)
        return permission_request_repository.get_all(db)

    def get_pending(self, db: Session, current_user: User):
        self._ensure_admin(current_user)
        return permission_request_repository.get_pending(db)

    def approve(self, db: Session, request_id: int, duration_minutes: int, current_user: User):
        self._ensure_admin(current_user)

        request = permission_request_repository.get_by_id(db, request_id)
        if request is None:
            raise HTTPException(
                status_code=404,
                detail="Demande introuvable",
            )

        if request.status != PERMISSION_REQUEST_STATUS_PENDING:
            raise HTTPException(
                status_code=400,
                detail="Cette demande a deja ete traitee.",
            )

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=duration_minutes)

        return permission_request_repository.approve(
            db,
            request,
            reviewed_by=current_user.id,
            reviewed_at=now,
            expires_at=expires_at,
        )

    def reject(self, db: Session, request_id: int, current_user: User):
        self._ensure_admin(current_user)

        request = permission_request_repository.get_by_id(db, request_id)
        if request is None:
            raise HTTPException(
                status_code=404,
                detail="Demande introuvable",
            )

        if request.status != PERMISSION_REQUEST_STATUS_PENDING:
            raise HTTPException(
                status_code=400,
                detail="Cette demande a deja ete traitee.",
            )

        now = datetime.now(timezone.utc)

        return permission_request_repository.reject(
            db,
            request,
            reviewed_by=current_user.id,
            reviewed_at=now,
        )


permission_request_service = PermissionRequestService()
