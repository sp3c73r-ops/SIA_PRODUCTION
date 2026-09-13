from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.movement import Movement
from app.models.user import User

from app.repositories.bureau_repository import (
    bureau_repository,
)
from app.repositories.document_repository import (
    document_repository,
)
from app.repositories.movement_repository import (
    movement_repository,
)
from app.repositories.user_repository import (
    user_repository,
)

from app.schemas.movement_schema import (
    MovementCreate,
)

from app.security.authorization import has_effective_permission
from app.security.authorization import is_admin
from app.security.permissions import PERMISSION_MOVEMENT_CREATE
from app.security.permissions import PERMISSION_MOVEMENT_READ
from app.security.permissions import PERMISSION_MOVEMENT_UPDATE


class MovementService:

    # ============================================================
    # SCOPES RBAC
    # USER  -> bureau_id
    # ADMIN -> admin_circonscription_id
    # ============================================================

    def _get_scopes(self, current_user: User):
        if is_admin(current_user):
            circonscription_id = getattr(
                current_user,
                "admin_circonscription_id",
                None,
            )

            if circonscription_id is None:
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Acces refuse: circonscription "
                        "non assignee."
                    ),
                )

            return None, circonscription_id

        bureau_id = getattr(
            current_user,
            "bureau_id",
            None,
        )

        if bureau_id is None:
            raise HTTPException(
                status_code=403,
                detail="Acces refuse: bureau non assigne.",
            )

        return bureau_id, None

    def _ensure_permission(
        self,
        db: Session,
        current_user: User,
        permission: str,
        bureau_id=None,
    ):
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

    def _ensure_document_in_scope(
        self,
        db: Session,
        document_id: int,
        bureau_id,
        circonscription_id,
    ):
        document = document_repository.get_by_id(
            db,
            document_id,
        )

        if document is None:
            raise HTTPException(
                status_code=404,
                detail="Document introuvable",
            )

        if bureau_id is not None:
            if document.bureau_id != bureau_id:
                raise HTTPException(
                    status_code=403,
                    detail="Acces interdit a ce document.",
                )
            return document

        bureau = bureau_repository.get_by_id(
            db,
            document.bureau_id,
        )

        if (
            bureau is None
            or bureau.circonscription_id != circonscription_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Acces interdit a ce document.",
            )

        return document

    # ============================================================
    # CREER UN MOUVEMENT
    # ============================================================

    def create(
        self,
        db: Session,
        data: MovementCreate,
        current_user: User,
    ):

        bureau_id, circonscription_id = self._get_scopes(
            current_user,
        )

        self._ensure_permission(
            db,
            current_user,
            PERMISSION_MOVEMENT_CREATE,
            bureau_id=bureau_id,
        )

        document = self._ensure_document_in_scope(
            db,
            data.document_id,
            bureau_id,
            circonscription_id,
        )

        # L'origine est TOUJOURS le bureau proprietaire du document.
        # Jamais fournie par le frontend.
        bureau_origine_id = document.bureau_id

        bureau_destination_id = data.bureau_destination_id

        if bureau_destination_id == bureau_origine_id:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Le bureau destination doit etre different "
                    "du bureau d'origine."
                ),
            )

        destination = bureau_repository.get_by_id(
            db,
            bureau_destination_id,
        )

        if destination is None:
            raise HTTPException(
                status_code=404,
                detail="Bureau destination introuvable.",
            )

        if not destination.actif:
            raise HTTPException(
                status_code=400,
                detail="Le bureau destination est inactif.",
            )

        if (
            destination.circonscription_id
            != document.circonscription_id
        ):
            raise HTTPException(
                status_code=403,
                detail=(
                    "Le bureau destination n'appartient pas "
                    "a la circonscription du document."
                ),
            )

        # Regle metier : un seul mouvement EN_COURS par document.
        existing_active = (
            movement_repository.get_active_by_document(
                db,
                document.id,
            )
        )

        if existing_active is not None:
            raise HTTPException(
                status_code=409,
                detail="Le document est deja en traitement.",
            )

        movement = Movement(
            document_id=data.document_id,
            user_id=current_user.id,
            bureau_origine_id=bureau_origine_id,
            bureau_destination_id=bureau_destination_id,
            type_mouvement=data.type_mouvement,
            motif=data.motif,
            statut="EN_COURS",
            date_mouvement=datetime.now(),
        )

        try:
            return movement_repository.create(
                db,
                movement,
            )
        except IntegrityError:
            # Protection contre la race condition entre deux
            # creations simultanees : l'index unique partiel
            # PostgreSQL rejette le second EN_COURS.
            db.rollback()
            raise HTTPException(
                status_code=409,
                detail="Le document est deja en traitement.",
            )


    # ============================================================
    # RECUPERER TOUS LES MOUVEMENTS
    # ============================================================

    def get_all(
        self,
        db: Session,
        current_user: User,
    ):

        bureau_id, circonscription_id = self._get_scopes(
            current_user,
        )

        self._ensure_permission(
            db,
            current_user,
            PERMISSION_MOVEMENT_READ,
            bureau_id=bureau_id,
        )

        return movement_repository.get_all(
            db,
            bureau_id=bureau_id,
            circonscription_id=circonscription_id,
        )


    # ============================================================
    # RECUPERER UN MOUVEMENT
    # ============================================================

    def get_by_id(
        self,
        db: Session,
        movement_id: int,
        current_user: User,
    ):

        bureau_id, circonscription_id = self._get_scopes(
            current_user,
        )

        self._ensure_permission(
            db,
            current_user,
            PERMISSION_MOVEMENT_READ,
            bureau_id=bureau_id,
        )

        movement = movement_repository.get_by_id(
            db,
            movement_id,
            bureau_id=bureau_id,
            circonscription_id=circonscription_id,
        )

        if movement is not None:
            return movement

        existing_movement = movement_repository.get_by_id(
            db,
            movement_id,
        )

        if existing_movement is not None:
            raise HTTPException(
                status_code=403,
                detail="Acces interdit a ce mouvement.",
            )

        return None


    # ============================================================
    # MOUVEMENTS D'UN DOCUMENT
    # ============================================================

    def get_by_document_id(
        self,
        db: Session,
        document_id: int,
        current_user: User,
    ):

        bureau_id, circonscription_id = self._get_scopes(
            current_user,
        )

        self._ensure_permission(
            db,
            current_user,
            PERMISSION_MOVEMENT_READ,
            bureau_id=bureau_id,
        )

        self._ensure_document_in_scope(
            db,
            document_id,
            bureau_id,
            circonscription_id,
        )

        return movement_repository.get_by_document_id(
            db,
            document_id,
            bureau_id=bureau_id,
            circonscription_id=circonscription_id,
        )


    # ============================================================
    # MOUVEMENTS D'UN UTILISATEUR
    # ============================================================

    def get_by_user_id(
        self,
        db: Session,
        user_id: int,
        current_user: User,
    ):

        bureau_id, circonscription_id = self._get_scopes(
            current_user,
        )

        self._ensure_permission(
            db,
            current_user,
            PERMISSION_MOVEMENT_READ,
            bureau_id=bureau_id,
        )

        target_user = user_repository.get_by_id(
            db,
            user_id,
        )

        if target_user is None:
            raise HTTPException(
                status_code=404,
                detail="Utilisateur introuvable.",
            )

        if bureau_id is not None:
            if getattr(
                target_user,
                "bureau_id",
                None,
            ) != bureau_id:
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Acces interdit aux mouvements "
                        "de cet utilisateur."
                    ),
                )
        else:
            target_bureau_id = getattr(
                target_user,
                "bureau_id",
                None,
            )

            target_bureau = (
                bureau_repository.get_by_id(
                    db,
                    target_bureau_id,
                )
                if target_bureau_id is not None
                else None
            )

            if (
                target_bureau is None
                or target_bureau.circonscription_id
                != circonscription_id
            ):
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Acces interdit aux mouvements "
                        "de cet utilisateur."
                    ),
                )

        return movement_repository.get_by_user_id(
            db,
            user_id,
            bureau_id=bureau_id,
            circonscription_id=circonscription_id,
        )


    # ============================================================
    # MOUVEMENTS EN COURS
    # ============================================================

    def get_active(
        self,
        db: Session,
        current_user: User,
    ):

        bureau_id, circonscription_id = self._get_scopes(
            current_user,
        )

        self._ensure_permission(
            db,
            current_user,
            PERMISSION_MOVEMENT_READ,
            bureau_id=bureau_id,
        )

        return movement_repository.get_active(
            db,
            bureau_id=bureau_id,
            circonscription_id=circonscription_id,
        )


    # ============================================================
    # RETOUR D'UN DOCUMENT
    # ============================================================

    def return_document(
        self,
        db: Session,
        movement_id: int,
        current_user: User,
    ):

        bureau_id, circonscription_id = self._get_scopes(
            current_user,
        )

        self._ensure_permission(
            db,
            current_user,
            PERMISSION_MOVEMENT_UPDATE,
            bureau_id=bureau_id,
        )

        movement = movement_repository.get_by_id(
            db,
            movement_id,
            bureau_id=bureau_id,
            circonscription_id=circonscription_id,
        )

        if not movement:

            existing_movement = movement_repository.get_by_id(
                db,
                movement_id,
            )

            if existing_movement is not None:
                raise HTTPException(
                    status_code=403,
                    detail="Acces interdit a ce mouvement.",
                )

            return None

        # Seul le bureau D'ORIGINE peut cloturer le mouvement.
        # Le bureau destination ne peut PAS effectuer le retour.
        if bureau_id is not None:
            origine_id = getattr(
                movement,
                "bureau_origine_id",
                None,
            )

            if (
                origine_id is not None
                and origine_id != bureau_id
            ):
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Seul le bureau d'origine peut "
                        "effectuer le retour de ce document."
                    ),
                )

        if movement.statut == "RETOURNE":
            return movement

        movement.statut = "RETOURNE"

        movement.date_retour = datetime.now()

        return movement_repository.update(
            db,
            movement,
        )


movement_service = MovementService()