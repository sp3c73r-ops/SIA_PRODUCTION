from fastapi import HTTPException

from app.models.user import User
from app.models.bureau import Bureau
from app.models.user import USER_ROLE_ADMIN
from app.models.user import USER_ROLE_USER
from app.models.user import USER_ROLES
from app.repositories.user_repository import user_repository
from app.security.authorization import is_admin
from app.security.permissions import is_known_permission
from app.security.password import hash_password


class UserService:

    def __init__(self):
        self.repository = user_repository

    def _ensure_admin(self, current_user):
        if not is_admin(current_user):
            raise HTTPException(
                status_code=403,
                detail="Acces reserve a l'administrateur.",
            )

    def _normalize_permissions(self, permissions):
        if permissions is None:
            return []

        if not isinstance(permissions, list):
            raise HTTPException(
                status_code=400,
                detail="Les permissions doivent être fournies sous forme de liste.",
            )

        normalized_permissions = []
        seen_permissions = set()

        for permission in permissions:
            if not isinstance(permission, str):
                raise HTTPException(
                    status_code=400,
                    detail="Chaque permission doit être une chaîne de caractères.",
                )

            normalized_permission = permission.strip()

            if not normalized_permission:
                raise HTTPException(
                    status_code=400,
                    detail="Une permission vide n'est pas autorisée.",
                )

            if not is_known_permission(normalized_permission):
                raise HTTPException(
                    status_code=400,
                    detail=f"Permission inconnue: {normalized_permission}",
                )

            if normalized_permission in seen_permissions:
                continue

            seen_permissions.add(normalized_permission)
            normalized_permissions.append(normalized_permission)

        return normalized_permissions

    def _normalize_single_permission(self, permission: str):
        normalized_permissions = self._normalize_permissions([permission])
        return normalized_permissions[0]

    def _validate_role_and_bureau(
        self,
        db,
        role: str,
        bureau_id: int | None,
    ):
        if role not in USER_ROLES:
            raise HTTPException(
                status_code=400,
                detail="Le role doit être ADMIN ou USER.",
            )

        if role == USER_ROLE_USER and bureau_id is None:
            raise HTTPException(
                status_code=400,
                detail="Le bureau_id est obligatoire pour un utilisateur USER.",
            )

        if role == USER_ROLE_ADMIN and bureau_id is not None:
            raise HTTPException(
                status_code=400,
                detail="Un utilisateur ADMIN ne doit pas être rattaché à un bureau.",
            )

        if role == USER_ROLE_ADMIN:
            return

        if bureau_id is not None:
            bureau_exists = (
                db.query(Bureau)
                .filter(Bureau.id == bureau_id)
                .first()
            )

            if bureau_exists is None:
                raise HTTPException(
                    status_code=400,
                    detail="Le bureau_id fourni est introuvable.",
                )

    def get_all(self, db, current_user):
        self._ensure_admin(current_user)
        return self.repository.get_all(db)

    def get_by_id(self, db, user_id: int, current_user):
        self._ensure_admin(current_user)

        user = self.repository.get_by_id(db, user_id)

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Utilisateur introuvable.",
            )

        return user

    def create(self, db, data):
        raise HTTPException(
            status_code=403,
            detail="Acces reserve a l'administrateur.",
        )

    def create_by_admin(self, db, data, current_user):
        self._ensure_admin(current_user)

        if self.repository.get_by_username(db, data.username):
            raise HTTPException(
                status_code=400,
                detail="Nom d'utilisateur déjà utilisé.",
            )

        self._validate_role_and_bureau(
            db,
            data.role,
            data.bureau_id,
        )

        permissions = self._normalize_permissions(
            data.permissions,
        )

        user = User(
            nom=data.nom,
            prenom=data.prenom,
            username=data.username,
            password=hash_password(data.password),
            actif=data.actif,
            role=data.role,
            bureau_id=data.bureau_id,
            permissions=permissions,
        )

        return self.repository.create(db, user)

    def assign_permission(self, db, user_id: int, permission: str, current_user):
        self._ensure_admin(current_user)

        user = self.repository.get_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Utilisateur introuvable.",
            )

        normalized_permission = self._normalize_single_permission(permission)
        permissions = list(user.permissions or [])

        if normalized_permission not in permissions:
            permissions.append(normalized_permission)

        user.permissions = permissions
        return self.repository.update(db, user)

    def revoke_permission(self, db, user_id: int, permission: str, current_user):
        self._ensure_admin(current_user)

        user = self.repository.get_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Utilisateur introuvable.",
            )

        normalized_permission = self._normalize_single_permission(permission)
        user.permissions = [p for p in (user.permissions or []) if p != normalized_permission]
        return self.repository.update(db, user)

    def update_bureau(self, db, user_id: int, bureau_id: int | None, current_user):
        self._ensure_admin(current_user)

        user = self.repository.get_by_id(db, user_id)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Utilisateur introuvable.",
            )

        self._validate_role_and_bureau(db, user.role, bureau_id)
        user.bureau_id = bureau_id
        return self.repository.update(db, user)

    def update_role(
        self,
        db,
        user_id: int,
        role: str,
        bureau_id: int | None,
        current_user,
    ):
        self._ensure_admin(current_user)

        user = self.repository.get_by_id(db, user_id)

        if user is None:
            raise HTTPException(
                status_code=404,
                detail="Utilisateur introuvable.",
            )

        if role not in USER_ROLES:
            raise HTTPException(
                status_code=400,
                detail="Le role doit être ADMIN ou USER.",
            )

        self._validate_role_and_bureau(
            db,
            role,
            bureau_id,
        )

        user.role = role
        user.bureau_id = bureau_id

        return self.repository.update(db, user)


user_service = UserService()
