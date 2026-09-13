from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    """
    Repository pour la persistance et la consultation des journaux d'audit.

    Ce repository est strictement immuable (création et lecture uniquement).
    Aucune méthode de mise à jour (update) ou de suppression (delete) n'existe.
    """

    def create(
        self,
        db: Session,
        audit_log: AuditLog,
        auto_commit: bool = False,
    ) -> AuditLog:
        """
        Ajoute l'entrée d'audit dans la session SQLAlchemy et effectue un flush().

        Par défaut auto_commit=False pour s'intégrer dans la transaction
        du workflow métier.
        """
        db.add(audit_log)
        db.flush()
        if auto_commit:
            db.commit()
            db.refresh(audit_log)
        return audit_log

    def get_by_id(self, db: Session, audit_log_id: int) -> Optional[AuditLog]:
        return (
            db.query(AuditLog)
            .filter(AuditLog.id == audit_log_id)
            .first()
        )

    def get_by_entity(
        self,
        db: Session,
        entity_type: str,
        entity_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        return (
            db.query(AuditLog)
            .filter(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id,
            )
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_document_id(
        self,
        db: Session,
        document_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        return (
            db.query(AuditLog)
            .filter(AuditLog.document_id == document_id)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_permission_request_id(
        self,
        db: Session,
        permission_request_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditLog]:
        return (
            db.query(AuditLog)
            .filter(AuditLog.permission_request_id == permission_request_id)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def list(
        self,
        db: Session,
        limit: int = 100,
        offset: int = 0,
        actor_user_id: Optional[int] = None,
        circonscription_id: Optional[int] = None,
        bureau_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
    ) -> List[AuditLog]:
        query = db.query(AuditLog)

        if actor_user_id is not None:
            query = query.filter(AuditLog.actor_user_id == actor_user_id)
        if circonscription_id is not None:
            query = query.filter(AuditLog.circonscription_id == circonscription_id)
        if bureau_id is not None:
            query = query.filter(AuditLog.bureau_id == bureau_id)
        if entity_type is not None:
            query = query.filter(AuditLog.entity_type == entity_type)
        if action is not None:
            query = query.filter(AuditLog.action == action)

        return (
            query.order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )


audit_log_repository = AuditLogRepository()
