from app.models.user import User
from app.models.bureau import Bureau
from app.models.user import USER_ROLE_ADMIN
from app.models.user import USER_ROLE_USER
from app.models.user import USER_ROLES
from app.repositories.user_repository import user_repository
from app.security.permissions import is_known_permission
from app.security.password import hash_password


class UserService:

    def __init__(self):
        self.repository = user_repository

    def _normalize_permissions(self, permissions):
        if permissions is None:
            return []

        if not isinstance(permissions, list):
            raise Exception("Les permissions doivent être fournies sous forme de liste.")

        normalized_permissions = []
        seen_permissions = set()

        for permission in permissions:
            if not isinstance(permission, str):
                raise Exception("Chaque permission doit être une chaîne de caractères.")

            normalized_permission = permission.strip()

            if not normalized_permission:
                raise Exception("Une permission vide n'est pas autorisée.")

            if not is_known_permission(normalized_permission):
                raise Exception(
                    f"Permission inconnue: {normalized_permission}"
                )

            if normalized_permission in seen_permissions:
                continue

            seen_permissions.add(normalized_permission)
            normalized_permissions.append(normalized_permission)

        return normalized_permissions

    def _validate_role_and_bureau(
        self,
        db,
        role: str,
        bureau_id: int | None,
    ):
        if role not in USER_ROLES:
            raise Exception("Le role doit être ADMIN ou USER.")

        if role == USER_ROLE_USER and bureau_id is None:
            raise Exception(
                "Le bureau_id est obligatoire pour un utilisateur USER."
            )

        if bureau_id is not None:
            bureau_exists = (
                db.query(Bureau)
                .filter(Bureau.id == bureau_id)
                .first()
            )

            if bureau_exists is None:
                raise Exception("Le bureau_id fourni est introuvable.")

        if role == USER_ROLE_ADMIN:
            return

    def create(self, db, data):

        if self.repository.get_by_username(db, data.username):
            raise Exception("Nom d'utilisateur déjà utilisé.")

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


user_service = UserService()
