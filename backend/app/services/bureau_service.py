from fastapi import HTTPException

from app.models.bureau import Bureau
from app.models.circonscription import Circonscription
from app.models.user import User
from app.repositories.bureau_repository import bureau_repository
from app.security.authorization import has_effective_permission
from app.security.authorization import is_admin
from app.security.permissions import PERMISSION_BUREAU_CREATE
from app.security.permissions import PERMISSION_BUREAU_DISABLE
from app.security.permissions import PERMISSION_BUREAU_READ
from app.security.permissions import PERMISSION_BUREAU_UPDATE


STANDARD_BUREAUX = (
    ("CONTENTIEUX", "Contentieux"),
    ("ENREGISTREMENT", "Enregistrement"),
    ("DOMAINE_NOTARIAT", "Domaine et notariat"),
    ("DOCUMENTATION_ARCHIVES", "Documentation et archives"),
)


class BureauService:

    def __init__(self):
        self.repository = bureau_repository

    def _ensure_permission(self, db, current_user: User, permission: str, bureau_id=None):
        if not has_effective_permission(
            db,
            current_user,
            permission,
            bureau_id=bureau_id,
        ):
            raise HTTPException(
                status_code=403,
                detail="Acces refuse: permission insuffisante.",
            )

    def _ensure_admin_permission(self, db, current_user: User, permission: str):
        self._ensure_permission(db, current_user, permission)
        if not is_admin(current_user):
            raise HTTPException(
                status_code=403,
                detail="Acces reserve a l'administrateur.",
            )

    def _get_user_bureau_id(self, current_user: User) -> int:
        bureau_id = getattr(current_user, "bureau_id", None)
        if bureau_id is None:
            raise HTTPException(
                status_code=403,
                detail="Acces refuse: bureau non assigne.",
            )
        return bureau_id

    def get_all(self, db, current_user: User):
        # USER : bureaux actifs de SA circonscription
        # (derives de son bureau).
        if not is_admin(current_user):
            bureau_id = self._get_user_bureau_id(current_user)
            self._ensure_permission(
                db,
                current_user,
                PERMISSION_BUREAU_READ,
                bureau_id=bureau_id,
            )
            bureau = self.repository.get_by_id(db, bureau_id)
            if bureau is None:
                raise HTTPException(status_code=403, detail="Acces refuse: bureau introuvable.")
            return self.repository.get_active_by_circonscription(
                db,
                bureau.circonscription_id,
            )

        # ADMIN : bureaux actifs de SA circonscription.
        self._ensure_permission(db, current_user, PERMISSION_BUREAU_READ)
        admin_circonscription_id = getattr(
            current_user,
            "admin_circonscription_id",
            None,
        )
        if admin_circonscription_id is not None:
            return self.repository.get_active_by_circonscription(
                db,
                admin_circonscription_id,
            )
        return self.repository.get_all(db)

    def get_by_id(self, db, bureau_id: int, current_user: User):
        if is_admin(current_user):
            self._ensure_permission(db, current_user, PERMISSION_BUREAU_READ)
        else:
            user_bureau_id = self._get_user_bureau_id(current_user)
            self._ensure_permission(
                db,
                current_user,
                PERMISSION_BUREAU_READ,
                bureau_id=user_bureau_id,
            )
            if bureau_id != user_bureau_id:
                raise HTTPException(status_code=403, detail="Acces interdit a ce bureau.")

        bureau = self.repository.get_by_id(db, bureau_id)
        if bureau is None:
            raise HTTPException(status_code=404, detail="Bureau introuvable.")
        return bureau

    def create(self, db, data, current_user: User):
        self._ensure_admin_permission(db, current_user, PERMISSION_BUREAU_CREATE)
        if db.query(Circonscription).filter(Circonscription.id == data.circonscription_id).first() is None:
            raise HTTPException(status_code=404, detail="Circonscription introuvable.")
        if self.repository.get_by_code(db, data.circonscription_id, data.code):
            raise HTTPException(status_code=400, detail="Ce code existe deja dans cette circonscription.")
        if self.repository.get_by_name(db, data.circonscription_id, data.nom):
            raise HTTPException(status_code=400, detail="Ce nom existe deja dans cette circonscription.")
        return self.repository.create(db, Bureau(**data.model_dump()))

    def update(self, db, bureau_id: int, data, current_user: User):
        self._ensure_admin_permission(db, current_user, PERMISSION_BUREAU_UPDATE)
        bureau = self.get_by_id(db, bureau_id, current_user)
        if data.code is not None and data.code != bureau.code:
            existing = self.repository.get_by_code(db, bureau.circonscription_id, data.code)
            if existing and existing.id != bureau.id:
                raise HTTPException(status_code=400, detail="Ce code existe deja dans cette circonscription.")
        if data.nom is not None and data.nom != bureau.nom:
            existing = self.repository.get_by_name(db, bureau.circonscription_id, data.nom)
            if existing and existing.id != bureau.id:
                raise HTTPException(status_code=400, detail="Ce nom existe deja dans cette circonscription.")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(bureau, key, value)
        return self.repository.update(db, bureau)

    def disable(self, db, bureau_id: int, current_user: User):
        self._ensure_admin_permission(db, current_user, PERMISSION_BUREAU_DISABLE)
        bureau = self.get_by_id(db, bureau_id, current_user)
        bureau.actif = False
        return self.repository.update(db, bureau)


bureau_service = BureauService()