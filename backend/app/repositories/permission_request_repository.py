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

    def create(self, db: Session, request: PermissionRequest):
        db.add(request)
        db.commit()
        db.refresh(request)
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
    ):
        request.status = PERMISSION_REQUEST_STATUS_APPROVED
        request.reviewed_by = reviewed_by
        request.reviewed_at = reviewed_at
        request.expires_at = expires_at
        db.commit()
        db.refresh(request)
        return request

    def reject(
        self,
        db: Session,
        request: PermissionRequest,
        reviewed_by: int,
        reviewed_at: datetime,
    ):
        request.status = PERMISSION_REQUEST_STATUS_REJECTED
        request.reviewed_by = reviewed_by
        request.reviewed_at = reviewed_at
        request.expires_at = None
        db.commit()
        db.refresh(request)
        return request

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
