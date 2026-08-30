from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.permission_request_schema import PermissionRequestApprove
from app.schemas.permission_request_schema import PermissionRequestCreate
from app.schemas.permission_request_schema import PermissionRequestReject
from app.schemas.permission_request_schema import PermissionRequestResponse
from app.security.authorization import require_permission
from app.security.dependencies import get_current_user
from app.security.permissions import PERMISSION_AUTHORIZATION_APPROVE
from app.security.permissions import PERMISSION_AUTHORIZATION_READ
from app.security.permissions import PERMISSION_AUTHORIZATION_REJECT
from app.services.permission_request_service import permission_request_service


router = APIRouter(
    prefix="/permission-requests",
    tags=["Permission Requests"],
)


@router.post(
    "",
    response_model=PermissionRequestResponse,
)
def create_permission_request(
    payload: PermissionRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return permission_request_service.create(
        db,
        current_user,
        payload,
    )


@router.get(
    "/me",
    response_model=List[PermissionRequestResponse],
)
def list_my_permission_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return permission_request_service.get_me(
        db,
        current_user,
    )


@router.delete(
    "/{request_id}",
    response_model=PermissionRequestResponse,
)
def cancel_permission_request(
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return permission_request_service.cancel(
        db,
        request_id,
        current_user,
    )


@router.get(
    "",
    response_model=List[PermissionRequestResponse],
)
def list_all_permission_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PERMISSION_AUTHORIZATION_READ)),
):
    return permission_request_service.get_all(
        db,
        current_user,
    )


@router.get(
    "/pending",
    response_model=List[PermissionRequestResponse],
)
def list_pending_permission_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PERMISSION_AUTHORIZATION_READ)),
):
    return permission_request_service.get_pending(
        db,
        current_user,
    )


@router.post(
    "/{request_id}/approve",
    response_model=PermissionRequestResponse,
)
def approve_permission_request(
    request_id: int,
    payload: PermissionRequestApprove,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PERMISSION_AUTHORIZATION_APPROVE)),
):
    return permission_request_service.approve(
        db,
        request_id,
        payload.duration_minutes,
        current_user,
    )


@router.post(
    "/{request_id}/reject",
    response_model=PermissionRequestResponse,
)
def reject_permission_request(
    request_id: int,
    payload: PermissionRequestReject,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PERMISSION_AUTHORIZATION_REJECT)),
):
    _ = payload
    return permission_request_service.reject(
        db,
        request_id,
        current_user,
    )
