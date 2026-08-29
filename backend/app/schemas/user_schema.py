from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.models.user import (
    USER_ROLE_ADMIN,
    USER_ROLE_USER,
)


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

    @model_validator(mode="after")
    def validate_role_and_bureau(self):
        if self.role == USER_ROLE_USER and self.bureau_id is None:
            raise ValueError(
                "Le bureau_id est obligatoire pour un utilisateur USER."
            )

        if self.role == USER_ROLE_ADMIN and self.bureau_id is None:
            return self

        return self


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int


    class Config:
        from_attributes = True
