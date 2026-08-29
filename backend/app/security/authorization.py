from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends
from fastapi import HTTPException

from app.models.user import USER_ROLE_ADMIN
from app.models.user import USER_ROLE_USER
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
