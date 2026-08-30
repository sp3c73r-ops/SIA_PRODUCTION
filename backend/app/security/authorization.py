from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from datetime import timezone

from fastapi import Depends
from fastapi import HTTPException

from app.models.permission_request import PERMISSION_REQUEST_STATUS_APPROVED
from app.models.user import USER_ROLE_ADMIN
from app.models.user import USER_ROLE_USER
from app.repositories.permission_request_repository import permission_request_repository
from app.security.dependencies import get_current_user
from app.security.permissions import is_known_permission


def is_admin(user) -> bool:
    """Retourne True si l'utilisateur a le role ADMIN."""

    return getattr(user, "role", None) == USER_ROLE_ADMIN


def has_permission(user, permission: str) -> bool:
    """Vérifie une permission RBAC officielle pour un utilisateur."""

    if not isinstance(permission, str):
        return False

    normalized_permission = permission.strip()

    if not normalized_permission:
        return False

    if not is_known_permission(normalized_permission):
        return False

    if is_admin(user):
        return True

    if getattr(user, "role", None) != USER_ROLE_USER:
        return False

    permissions = getattr(user, "permissions", None) or []

    if not isinstance(permissions, (list, tuple, set, frozenset)):
        return False

    normalized_user_permissions = {
        p.strip()
        for p in permissions
        if isinstance(p, str) and p.strip()
    }

    return normalized_permission in normalized_user_permissions


def has_bureau_access(user, bureau_id: int | None) -> bool:
    """Vérifie le périmètre bureau de façon indépendante des permissions."""

    if bureau_id is None:
        return False

    if is_admin(user):
        return True

    if getattr(user, "role", None) != USER_ROLE_USER:
        return False

    user_bureau_id = getattr(user, "bureau_id", None)

    if user_bureau_id is None:
        return False

    return user_bureau_id == bureau_id


def has_temporary_permission(
    db,
    user,
    permission: str,
    document_id: int | None = None,
    bureau_id: int | None = None,
) -> bool:
    """Vérifie une autorisation temporaire approuvée et non expirée."""

    if not isinstance(permission, str):
        return False

    normalized_permission = permission.strip()

    if not normalized_permission:
        return False

    if not is_known_permission(normalized_permission):
        return False

    if is_admin(user):
        return True

    if getattr(user, "role", None) != USER_ROLE_USER:
        return False

    user_bureau_id = getattr(user, "bureau_id", None)
    if user_bureau_id is None:
        return False

    target_bureau_id = bureau_id if bureau_id is not None else user_bureau_id

    if user_bureau_id != target_bureau_id:
        return False

    request = permission_request_repository.find_approved(
        db,
        user_id=user.id,
        bureau_id=target_bureau_id,
        permission=normalized_permission,
        document_id=document_id,
    )

    if request is None:
        return False

    if request.status != PERMISSION_REQUEST_STATUS_APPROVED:
        return False

    if request.bureau_id != target_bureau_id:
        return False

    if document_id is not None and request.document_id != document_id:
        return False

    if request.expires_at is None:
        return False

    now = datetime.now(timezone.utc)
    expires_at = request.expires_at

    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if expires_at <= now:
        permission_request_repository.mark_expired(db, request)
        return False

    return True


def has_effective_permission(
    db,
    user,
    permission: str,
    document_id: int | None = None,
    bureau_id: int | None = None,
) -> bool:
    """Vérifie permission permanente puis autorisation temporaire."""

    if has_permission(user, permission):
        return True

    return has_temporary_permission(
        db,
        user,
        permission,
        document_id=document_id,
        bureau_id=bureau_id,
    )


def require_permission(permission: str) -> Callable:
    """Dépendance FastAPI qui impose une permission RBAC officielle."""

    async def _dependency(current_user=Depends(get_current_user)):
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=403,
                detail="Acces refuse: permission insuffisante.",
            )

        return current_user

    return _dependency
