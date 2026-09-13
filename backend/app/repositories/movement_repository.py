from sqlalchemy.orm import Session

from app.models.bureau import Bureau
from app.models.document import Document
from app.models.movement import Movement


class MovementRepository:

    # ============================================================
    # SCOPE RBAC
    # USER  -> Document.bureau_id == bureau_id
    # ADMIN -> Bureau.circonscription_id == circonscription_id
    # ============================================================

    def _apply_scope(
        self,
        query,
        bureau_id=None,
        circonscription_id=None,
    ):

        if bureau_id is None and circonscription_id is None:
            return query

        query = query.join(
            Document,
            Movement.document_id == Document.id,
        )

        if bureau_id is not None:
            query = query.filter(
                Document.bureau_id == bureau_id
            )

        if circonscription_id is not None:
            query = query.join(
                Bureau,
                Document.bureau_id == Bureau.id,
            ).filter(
                Bureau.circonscription_id
                == circonscription_id
            )

        return query

    # ============================================================
    # CREER UN MOUVEMENT
    # ============================================================

    def create(
        self,
        db: Session,
        movement: Movement,
    ):

        db.add(movement)

        db.commit()

        db.refresh(movement)

        return movement


    # ============================================================
    # RECUPERER UN MOUVEMENT PAR ID
    # ============================================================

    def get_by_id(
        self,
        db: Session,
        movement_id: int,
        bureau_id=None,
        circonscription_id=None,
    ):

        query = db.query(Movement)

        query = self._apply_scope(
            query,
            bureau_id=bureau_id,
            circonscription_id=circonscription_id,
        )

        return (
            query
            .filter(
                Movement.id == movement_id
            )
            .first()
        )


    # ============================================================
    # RECUPERER TOUS LES MOUVEMENTS
    # ============================================================

    def get_all(
        self,
        db: Session,
        bureau_id=None,
        circonscription_id=None,
    ):

        query = db.query(Movement)

        query = self._apply_scope(
            query,
            bureau_id=bureau_id,
            circonscription_id=circonscription_id,
        )

        return (
            query
            .order_by(
                Movement.date_mouvement.desc()
            )
            .all()
        )


    # ============================================================
    # RECUPERER LES MOUVEMENTS D'UN DOCUMENT
    # ============================================================

    def get_by_document_id(
        self,
        db: Session,
        document_id: int,
        bureau_id=None,
        circonscription_id=None,
    ):

        query = db.query(Movement)

        query = self._apply_scope(
            query,
            bureau_id=bureau_id,
            circonscription_id=circonscription_id,
        )

        return (
            query
            .filter(
                Movement.document_id == document_id
            )
            .order_by(
                Movement.date_mouvement.desc()
            )
            .all()
        )


    # ============================================================
    # RECUPERER LES MOUVEMENTS D'UN UTILISATEUR
    # ============================================================

    def get_by_user_id(
        self,
        db: Session,
        user_id: int,
        bureau_id=None,
        circonscription_id=None,
    ):

        query = db.query(Movement)

        query = self._apply_scope(
            query,
            bureau_id=bureau_id,
            circonscription_id=circonscription_id,
        )

        return (
            query
            .filter(
                Movement.user_id == user_id
            )
            .order_by(
                Movement.date_mouvement.desc()
            )
            .all()
        )


    # ============================================================
    # RECUPERER LES MOUVEMENTS EN COURS
    # ============================================================

    def get_active(
        self,
        db: Session,
        bureau_id=None,
        circonscription_id=None,
    ):

        query = db.query(Movement)

        query = self._apply_scope(
            query,
            bureau_id=bureau_id,
            circonscription_id=circonscription_id,
        )

        return (
            query
            .filter(
                Movement.statut == "EN_COURS"
            )
            .order_by(
                Movement.date_mouvement.desc()
            )
            .all()
        )


    # ============================================================
    # MOUVEMENT ACTIF (EN_COURS) D'UN DOCUMENT
    # ============================================================

    def get_active_by_document(
        self,
        db: Session,
        document_id: int,
    ):

        return (
            db.query(Movement)
            .filter(
                Movement.document_id == document_id,
                Movement.statut == "EN_COURS",
            )
            .first()
        )


    # ============================================================
    # MODIFIER UN MOUVEMENT
    # ============================================================

    def update(
        self,
        db: Session,
        movement: Movement,
    ):

        db.commit()

        db.refresh(movement)

        return movement


movement_repository = MovementRepository()