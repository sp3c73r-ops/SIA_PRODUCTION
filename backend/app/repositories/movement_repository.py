from sqlalchemy.orm import Session

from app.models.movement import Movement


class MovementRepository:

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
    ):

        return (
            db.query(Movement)
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
    ):

        return (
            db.query(Movement)
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
    ):

        return (
            db.query(Movement)
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
    ):

        return (
            db.query(Movement)
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
    ):

        return (
            db.query(Movement)
            .filter(
                Movement.statut == "EN_COURS"
            )
            .order_by(
                Movement.date_mouvement.desc()
            )
            .all()
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