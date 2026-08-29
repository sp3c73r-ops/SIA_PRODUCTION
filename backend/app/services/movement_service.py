from datetime import datetime

from sqlalchemy.orm import Session

from app.models.movement import Movement
from app.models.user import User

from app.repositories.movement_repository import (
    movement_repository,
)

from app.schemas.movement_schema import (
    MovementCreate,
)


class MovementService:

    # ============================================================
    # CREER UN MOUVEMENT
    # ============================================================

    def create(
        self,
        db: Session,
        data: MovementCreate,
        current_user: User,
    ):

        movement = Movement(
            document_id=data.document_id,
            user_id=current_user.id,
            type_mouvement=data.type_mouvement,
            motif=data.motif,
            statut="EN_COURS",
            date_mouvement=datetime.now(),
        )

        return movement_repository.create(
            db,
            movement,
        )


    # ============================================================
    # RECUPERER TOUS LES MOUVEMENTS
    # ============================================================

    def get_all(
        self,
        db: Session,
    ):

        return movement_repository.get_all(
            db
        )


    # ============================================================
    # RECUPERER UN MOUVEMENT
    # ============================================================

    def get_by_id(
        self,
        db: Session,
        movement_id: int,
    ):

        return movement_repository.get_by_id(
            db,
            movement_id,
        )


    # ============================================================
    # MOUVEMENTS D'UN DOCUMENT
    # ============================================================

    def get_by_document_id(
        self,
        db: Session,
        document_id: int,
    ):

        return movement_repository.get_by_document_id(
            db,
            document_id,
        )


    # ============================================================
    # MOUVEMENTS D'UN UTILISATEUR
    # ============================================================

    def get_by_user_id(
        self,
        db: Session,
        user_id: int,
    ):

        return movement_repository.get_by_user_id(
            db,
            user_id,
        )


    # ============================================================
    # MOUVEMENTS EN COURS
    # ============================================================

    def get_active(
        self,
        db: Session,
    ):

        return movement_repository.get_active(
            db
        )


    # ============================================================
    # RETOUR D'UN DOCUMENT
    # ============================================================

    def return_document(
        self,
        db: Session,
        movement_id: int,
    ):

        movement = (
            movement_repository.get_by_id(
                db,
                movement_id,
            )
        )

        if not movement:
            return None

        if movement.statut == "RETOURNE":
            return movement

        movement.statut = "RETOURNE"

        movement.date_retour = datetime.now()

        return movement_repository.update(
            db,
            movement,
        )


movement_service = MovementService()