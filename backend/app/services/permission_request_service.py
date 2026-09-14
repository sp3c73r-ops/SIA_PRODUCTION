from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.bureau import Bureau
from app.models.permission_request import (
    PERMISSION_REQUEST_STATUS_APPROVED,
    PERMISSION_REQUEST_STATUS_PENDING,
    PERMISSION_REQUEST_STATUS_REJECTED,
    PermissionRequest,
)
from app.models.user import USER_ROLE_USER
from app.models.user import User
from app.repositories.bureau_repository import bureau_repository
from app.repositories.document_repository import document_repository
from app.repositories.permission_request_repository import permission_request_repository
from app.security.authorization import is_admin
from app.security.permissions import PERMISSION_ATTACHMENT_CREATE
from app.security.permissions import is_known_permission
from app.services.audit_log_service import audit_log_service
from app.services.notification_service import notification_service


class PermissionRequestService:

    @staticmethod
    def _is_pending_scope_conflict(exc: IntegrityError) -> bool:
        orig = getattr(exc, "orig", None)
        diag = getattr(orig, "diag", None)

        return (
            getattr(orig, "sqlstate", None) == "23505"
            and getattr(diag, "constraint_name", None)
            == "uq_permission_requests_pending_scope"
        )

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

    def _get_admin_circonscription_id(self, current_user: User) -> int:
        admin_circonscription_id = getattr(
            current_user,
            "admin_circonscription_id",
            None,
        )

        if admin_circonscription_id is None:
            raise HTTPException(
                status_code=403,
                detail=(
                    "Acces refuse: l'administrateur n'est rattache "
                    "a aucune circonscription."
                ),
            )

        return admin_circonscription_id

    def _scoped_query(self, db: Session, current_user: User):
        admin_circonscription_id = self._get_admin_circonscription_id(
            current_user,
        )

        return (
            db.query(PermissionRequest)
            .join(
                Bureau,
                Bureau.id == PermissionRequest.bureau_id,
            )
            .filter(
                Bureau.circonscription_id == admin_circonscription_id
            )
        )

    def _get_scoped_request(self, db: Session, request_id: int, current_user: User):
        return (
            self._scoped_query(db, current_user)
            .filter(PermissionRequest.id == request_id)
            .first()
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

        if permission == "document.update" and document_id is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "La permission document.update doit cibler "
                    "un document precis."
                ),
            )

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

        try:
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
                auto_commit=False,
            )

            circonscription_id = None
            user_bureau = getattr(current_user, "bureau", None)
            if user_bureau is not None and getattr(user_bureau, "circonscription_id", None) is not None:
                circonscription_id = user_bureau.circonscription_id
            elif hasattr(db, "query"):
                bureau_obj = bureau_repository.get_by_id(db, bureau_id)
                if bureau_obj is not None:
                    circonscription_id = bureau_obj.circonscription_id

            audit_log_service.log_event(
                db,
                action="permission_request.created",
                entity_type="PermissionRequest",
                entity_id=request.id,
                permission_request_id=request.id,
                actor_user_id=current_user.id,
                document_id=document_id,
                bureau_id=bureau_id,
                circonscription_id=circonscription_id,
                old_state=None,
                new_state={
                    "permission": permission,
                    "document_id": document_id,
                    "reason": data.reason,
                    "status": PERMISSION_REQUEST_STATUS_PENDING,
                },
                auto_commit=False,
            )

            if circonscription_id:
                user_name = (
                    f"{getattr(current_user, 'prenom', '')} {getattr(current_user, 'nom', '')}".strip()
                    or getattr(current_user, "username", None)
                    or f"Utilisateur {getattr(current_user, 'id', '')}"
                )
                notification_service.notify_admins_of_circonscription(
                    db,
                    circonscription_id=circonscription_id,
                    action="permission_request.created",
                    title="Nouvelle demande d'autorisation de modification",
                    message=f"L'utilisateur {user_name} demande l'autorisation de modifier un document.",
                    permission_request_id=request.id,
                    document_id=document_id,
                    bureau_id=bureau_id,
                    auto_commit=False,
                )

            db.commit()
            db.refresh(request)
        except IntegrityError as exc:
            db.rollback()

            if self._is_pending_scope_conflict(exc):
                raise HTTPException(
                    status_code=409,
                    detail="Une demande identique est deja en attente.",
                ) from exc

            raise
        except Exception:
            db.rollback()
            raise

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
        return (
            self._scoped_query(db, current_user)
            .order_by(PermissionRequest.requested_at.desc())
            .all()
        )

    def get_pending(self, db: Session, current_user: User):
        self._ensure_admin(current_user)
        return (
            self._scoped_query(db, current_user)
            .filter(
                PermissionRequest.status == PERMISSION_REQUEST_STATUS_PENDING
            )
            .order_by(PermissionRequest.requested_at.asc())
            .all()
        )

    def approve(self, db: Session, request_id: int, duration_minutes: int, current_user: User):
        self._ensure_admin(current_user)

        request = self._get_scoped_request(db, request_id, current_user)
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

        try:
            result = permission_request_repository.approve(
                db,
                request,
                reviewed_by=current_user.id,
                reviewed_at=now,
                expires_at=expires_at,
                auto_commit=False,
            )

            if result is None:
                raise HTTPException(
                    status_code=409,
                    detail="Cette demande a deja ete traitee.",
                )

            if result.permission == "document.update" and result.document_id is not None:
                permission_request_repository.create_approved_companion(
                    db,
                    source_request=result,
                    permission=PERMISSION_ATTACHMENT_CREATE,
                    reviewed_by=current_user.id,
                    reviewed_at=now,
                    expires_at=expires_at,
                )

            admin_circonscription_id = self._get_admin_circonscription_id(current_user)

            audit_log_service.log_event(
                db,
                action="permission_request.approved",
                entity_type="PermissionRequest",
                entity_id=result.id,
                permission_request_id=result.id,
                actor_user_id=current_user.id,
                document_id=result.document_id,
                bureau_id=result.bureau_id,
                circonscription_id=admin_circonscription_id,
                old_state={"status": PERMISSION_REQUEST_STATUS_PENDING},
                new_state={
                    "status": PERMISSION_REQUEST_STATUS_APPROVED,
                    "reviewed_by": current_user.id,
                    "reviewed_at": now.isoformat(),
                    "expires_at": expires_at.isoformat(),
                    "duration_minutes": duration_minutes,
                },
                auto_commit=False,
            )

            notification_service.notify_user(
                db,
                recipient_user_id=result.user_id,
                action="permission_request.approved",
                title="Demande d'autorisation approuvée",
                message=f"Votre demande d'autorisation de modification a été approuvée pour une durée de {duration_minutes} minute(s).",
                permission_request_id=result.id,
                document_id=result.document_id,
                bureau_id=result.bureau_id,
                circonscription_id=admin_circonscription_id,
                auto_commit=False,
            )

            db.commit()
            db.refresh(result)
            return result
        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise

    def reject(self, db: Session, request_id: int, current_user: User):
        self._ensure_admin(current_user)

        request = self._get_scoped_request(db, request_id, current_user)
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

        try:
            result = permission_request_repository.reject(
                db,
                request,
                reviewed_by=current_user.id,
                reviewed_at=now,
                auto_commit=False,
            )

            if result is None:
                raise HTTPException(
                    status_code=409,
                    detail="Cette demande a deja ete traitee.",
                )

            admin_circonscription_id = self._get_admin_circonscription_id(current_user)

            audit_log_service.log_event(
                db,
                action="permission_request.rejected",
                entity_type="PermissionRequest",
                entity_id=result.id,
                permission_request_id=result.id,
                actor_user_id=current_user.id,
                document_id=result.document_id,
                bureau_id=result.bureau_id,
                circonscription_id=admin_circonscription_id,
                old_state={"status": PERMISSION_REQUEST_STATUS_PENDING},
                new_state={
                    "status": PERMISSION_REQUEST_STATUS_REJECTED,
                    "reviewed_by": current_user.id,
                    "reviewed_at": now.isoformat(),
                },
                auto_commit=False,
            )

            notification_service.notify_user(
                db,
                recipient_user_id=result.user_id,
                action="permission_request.rejected",
                title="Demande d'autorisation rejetée",
                message="Votre demande d'autorisation de modification a été rejetée.",
                permission_request_id=result.id,
                document_id=result.document_id,
                bureau_id=result.bureau_id,
                circonscription_id=admin_circonscription_id,
                auto_commit=False,
            )

            db.commit()
            db.refresh(result)
            return result
        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise


permission_request_service = PermissionRequestService()
