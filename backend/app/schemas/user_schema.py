from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.models.user import (
    USER_ROLE_ADMIN,
    USER_ROLE_USER,
)
from app.security.permissions import is_known_permission


UserRole = Literal[
    "ADMIN",
    "USER",
]


class UserBase(BaseModel):
    nom: str
    prenom: str
    username: str
    actif: bool = True
    role: UserRole = USER_ROLE_USER
    bureau_id: int | None = None
    permissions: list[str] = Field(default_factory=list)

    @field_validator("permissions")
    @classmethod
    def validate_permissions(cls, permissions):
        if permissions is None:
            return []

        if not isinstance(permissions, list):
            raise ValueError(
                "Les permissions doivent être fournies sous forme de liste."
            )

        normalized_permissions = []
        seen_permissions = set()

        for permission in permissions:
            if not isinstance(permission, str):
                raise ValueError(
                    "Chaque permission doit être une chaîne de caractères."
                )

            normalized_permission = permission.strip()

            if not normalized_permission:
                raise ValueError("Une permission vide n'est pas autorisée.")

            if not is_known_permission(normalized_permission):
                raise ValueError(
                    f"Permission inconnue: {normalized_permission}"
                )

            if normalized_permission in seen_permissions:
                continue

            seen_permissions.add(normalized_permission)
            normalized_permissions.append(normalized_permission)

        return normalized_permissions

    @model_validator(mode="after")
    def validate_role_and_bureau(self):
        if self.role == USER_ROLE_USER and self.bureau_id is None:
            raise ValueError(
                "Le bureau_id est obligatoire pour un utilisateur USER."
            )

        if self.role == USER_ROLE_ADMIN and self.bureau_id is not None:
            raise ValueError(
                "Un utilisateur ADMIN ne doit pas être rattaché à un bureau."
            )

        return self


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int


    class Config:
        from_attributes = True


class UserPermissionCreate(BaseModel):
    permission: str

    @field_validator("permission")
    @classmethod
    def validate_permission(cls, permission):
        if not isinstance(permission, str):
            raise ValueError("La permission doit être une chaîne de caractères.")

        normalized_permission = permission.strip()

        if not normalized_permission:
            raise ValueError("Une permission vide n'est pas autorisée.")

        if not is_known_permission(normalized_permission):
            raise ValueError(f"Permission inconnue: {normalized_permission}")

        return normalized_permission


class UserRoleUpdate(BaseModel):
    role: UserRole
    bureau_id: int | None = None


class UserBureauUpdate(BaseModel):
    bureau_id: int | None = None
