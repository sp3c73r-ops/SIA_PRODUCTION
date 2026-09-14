from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.permission_request import PERMISSION_REQUEST_STATUS_APPROVED
from app.models.permission_request import PERMISSION_REQUEST_STATUS_CANCELLED
from app.models.permission_request import PERMISSION_REQUEST_STATUS_EXPIRED
from app.models.permission_request import PERMISSION_REQUEST_STATUS_PENDING
from app.models.permission_request import PERMISSION_REQUEST_STATUS_REJECTED
from app.models.permission_request import PermissionRequest


class PermissionRequestRepository:

    def create(
        self,
        db: Session,
        request: PermissionRequest,
        auto_commit: bool = True,
    ):
        db.add(request)
        if auto_commit:
            db.commit()
            db.refresh(request)
        else:
            db.flush()
        return request

    def get_by_id(self, db: Session, request_id: int):
        return (
            db.query(PermissionRequest)
            .filter(PermissionRequest.id == request_id)
            .first()
        )

    def get_by_user_id(self, db: Session, user_id: int):
        return (
            db.query(PermissionRequest)
            .filter(PermissionRequest.user_id == user_id)
            .order_by(PermissionRequest.requested_at.desc())
            .all()
        )

    def get_all(self, db: Session):
        return (
            db.query(PermissionRequest)
            .order_by(PermissionRequest.requested_at.desc())
            .all()
        )

    def get_pending(self, db: Session):
        return (
            db.query(PermissionRequest)
            .filter(PermissionRequest.status == PERMISSION_REQUEST_STATUS_PENDING)
            .order_by(PermissionRequest.requested_at.asc())
            .all()
        )

    def find_pending_duplicate(
        self,
        db: Session,
        user_id: int,
        permission: str,
        document_id: Optional[int],
    ):
        query = (
            db.query(PermissionRequest)
            .filter(PermissionRequest.user_id == user_id)
            .filter(PermissionRequest.permission == permission)
            .filter(PermissionRequest.status == PERMISSION_REQUEST_STATUS_PENDING)
        )

        if document_id is None:
            query = query.filter(PermissionRequest.document_id.is_(None))
        else:
            query = query.filter(PermissionRequest.document_id == document_id)

        return query.first()

    def approve(
        self,
        db: Session,
        request: PermissionRequest,
        reviewed_by: int,
        reviewed_at: datetime,
        expires_at: datetime,
        auto_commit: bool = True,
    ):
        updated_count = (
            db.query(PermissionRequest)
            .filter(PermissionRequest.id == request.id)
            .filter(PermissionRequest.status == PERMISSION_REQUEST_STATUS_PENDING)
            .update(
                {
                    PermissionRequest.status: PERMISSION_REQUEST_STATUS_APPROVED,
                    PermissionRequest.reviewed_by: reviewed_by,
                    PermissionRequest.reviewed_at: reviewed_at,
                    PermissionRequest.expires_at: expires_at,
                },
                synchronize_session=False,
            )
        )

        if updated_count != 1:
            db.rollback()
            return None

        if auto_commit:
            db.commit()
        else:
            db.flush()
        return self.get_by_id(db, request.id)

    def create_approved_companion(
        self,
        db: Session,
        source_request: PermissionRequest,
        permission: str,
        reviewed_by: int,
        reviewed_at: datetime,
        expires_at: datetime,
    ):
        companion = PermissionRequest(
            user_id=source_request.user_id,
            bureau_id=source_request.bureau_id,
            permission=permission,
            document_id=source_request.document_id,
            reason=getattr(source_request, "reason", None),
            status=PERMISSION_REQUEST_STATUS_APPROVED,
            reviewed_by=reviewed_by,
            reviewed_at=reviewed_at,
            expires_at=expires_at,
        )
        db.add(companion)
        db.flush()
        return companion

    def reject(
        self,
        db: Session,
        request: PermissionRequest,
        reviewed_by: int,
        reviewed_at: datetime,
        auto_commit: bool = True,
    ):
        updated_count = (
            db.query(PermissionRequest)
            .filter(PermissionRequest.id == request.id)
            .filter(PermissionRequest.status == PERMISSION_REQUEST_STATUS_PENDING)
            .update(
                {
                    PermissionRequest.status: PERMISSION_REQUEST_STATUS_REJECTED,
                    PermissionRequest.reviewed_by: reviewed_by,
                    PermissionRequest.reviewed_at: reviewed_at,
                    PermissionRequest.expires_at: None,
                },
                synchronize_session=False,
            )
        )

        if updated_count != 1:
            db.rollback()
            return None

        if auto_commit:
            db.commit()
        else:
            db.flush()
        return self.get_by_id(db, request.id)

    def cancel(
        self,
        db: Session,
        request: PermissionRequest,
    ):
        request.status = PERMISSION_REQUEST_STATUS_CANCELLED
        db.commit()
        db.refresh(request)
        return request

    def mark_expired(
        self,
        db: Session,
        request: PermissionRequest,
    ):
        request.status = PERMISSION_REQUEST_STATUS_EXPIRED
        db.commit()
        db.refresh(request)
        return request

    def find_approved(
        self,
        db: Session,
        user_id: int,
        bureau_id: int,
        permission: str,
        document_id: Optional[int],
    ):
        query = (
            db.query(PermissionRequest)
            .filter(PermissionRequest.user_id == user_id)
            .filter(PermissionRequest.bureau_id == bureau_id)
            .filter(PermissionRequest.permission == permission)
            .filter(PermissionRequest.status == PERMISSION_REQUEST_STATUS_APPROVED)
        )

        if document_id is None:
            query = query.filter(PermissionRequest.document_id.is_(None))
        else:
            query = query.filter(PermissionRequest.document_id == document_id)

        return (
            query
            .order_by(PermissionRequest.reviewed_at.desc())
            .first()
        )


permission_request_repository = PermissionRequestRepository()
