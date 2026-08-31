from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.schemas.user_schema import (
    UserBureauUpdate,
    UserCreate,
    UserPermissionCreate,
    UserResponse,
    UserRoleUpdate,
)
from app.security.authorization import require_permission
from app.security.permissions import PERMISSION_USER_ASSIGN_PERMISSION
from app.security.permissions import PERMISSION_USER_ASSIGN_ROLE
from app.security.permissions import PERMISSION_USER_CREATE
from app.security.permissions import PERMISSION_USER_READ
from app.security.permissions import PERMISSION_USER_REVOKE_PERMISSION
from app.security.permissions import PERMISSION_USER_UPDATE
from app.services.user_service import user_service


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/",
    response_model=List[UserResponse],
)
def get_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_USER_READ)
    ),
):
    return user_service.get_all(db, current_user)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_USER_READ)
    ),
):
    return user_service.get_by_id(db, user_id, current_user)


@router.post(
    "/",
    response_model=UserResponse,
)
def create_user(
    data: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_USER_CREATE)
    ),
):
    return user_service.create_by_admin(db, data, current_user)


@router.post(
    "/{user_id}/permissions",
    response_model=UserResponse,
)
def assign_permission_to_user(
    user_id: int,
    payload: UserPermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_USER_ASSIGN_PERMISSION)
    ),
):
    return user_service.assign_permission(
        db,
        user_id,
        payload.permission,
        current_user,
    )


@router.delete(
    "/{user_id}/permissions/{permission}",
    response_model=UserResponse,
)
def revoke_permission_from_user(
    user_id: int,
    permission: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_USER_REVOKE_PERMISSION)
    ),
):
    return user_service.revoke_permission(
        db,
        user_id,
        permission,
        current_user,
    )


@router.patch(
    "/{user_id}/bureau",
    response_model=UserResponse,
)
def update_user_bureau(
    user_id: int,
    payload: UserBureauUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_USER_UPDATE)
    ),
):
    return user_service.update_bureau(
        db,
        user_id,
        payload.bureau_id,
        current_user,
    )


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
)
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission(PERMISSION_USER_ASSIGN_ROLE)
    ),
):
    return user_service.update_role(
        db,
        user_id,
        payload.role,
        payload.bureau_id,
        current_user,
    )