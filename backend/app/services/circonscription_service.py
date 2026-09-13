from fastapi import HTTPException

from app.models.user import User
from app.models.circonscription import Circonscription
from app.repositories.circonscription_repository import (
    circonscription_repository,
)
from app.security.authorization import has_effective_permission
from app.security.authorization import is_admin
from app.security.permissions import PERMISSION_DOCUMENT_READ


class CirconscriptionService:

    def __init__(self):
        self.repository = circonscription_repository

    def _get_scope_bureau_id(self, current_user: User) -> int | None:
        if is_admin(current_user):
            return None

        bureau_id = getattr(current_user, "bureau_id", None)
        if bureau_id is None:
            raise HTTPException(
                status_code=403,
                detail="Acces refuse: bureau non assigne.",
            )

        return bureau_id

    def _ensure_read_permission(
        self,
        db,
        current_user: User,
        bureau_id: int | None,
    ):
        if not has_effective_permission(
            db,
            current_user,
            PERMISSION_DOCUMENT_READ,
            bureau_id=bureau_id,
        ):
            raise HTTPException(
                status_code=403,
                detail="Acces refuse: permission insuffisante.",
            )

    def get_all(self, db, current_user: User):
        bureau_id = self._get_scope_bureau_id(current_user)
        self._ensure_read_permission(db, current_user, bureau_id)

        if bureau_id is None:
            return self.repository.get_all(db)

        circonscription = self.repository.get_by_bureau_id(db, bureau_id)
        if circonscription is None:
            raise HTTPException(
                status_code=403,
                detail="Acces refuse: circonscription introuvable.",
            )

        return [circonscription]

    def create(self, db, data, current_user: User):
        if not is_admin(current_user):
            raise HTTPException(
                status_code=403,
                detail="Acces reserve a l'administrateur.",
            )

        item = Circonscription(**data.model_dump())
        return self.repository.create(db, item)


circonscription_service = CirconscriptionService()