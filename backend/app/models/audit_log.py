from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database.base import Base


class AuditLog(Base):
    """
    Modèle d'audit backend pour l'enregistrement immuable des événements.

    Correspond à la table 'audit_logs'.
    Note: la colonne 'metadata' est cartographiée sur l'attribut Python 'metadata_'
    afin d'éviter tout conflit avec la propriété 'Base.metadata' de SQLAlchemy Declarative,
    tout en conservant le nom 'metadata' en base de données.
    """

    __tablename__ = "audit_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    actor_user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    action = Column(
        String(100),
        nullable=False,
    )

    entity_type = Column(
        String(80),
        nullable=False,
    )

    entity_id = Column(
        Integer,
        nullable=True,
    )

    document_id = Column(
        Integer,
        ForeignKey(
            "documents.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    permission_request_id = Column(
        Integer,
        ForeignKey(
            "permission_requests.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    bureau_id = Column(
        Integer,
        ForeignKey(
            "bureaux.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    circonscription_id = Column(
        Integer,
        ForeignKey(
            "circonscriptions.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    old_state = Column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
    )

    new_state = Column(
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
    )

    metadata_ = Column(
        "metadata",
        JSON().with_variant(JSONB(), "postgresql"),
        nullable=True,
    )

    request_id = Column(
        String(100),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    actor = relationship("User", foreign_keys=[actor_user_id])
    document = relationship("Document", foreign_keys=[document_id])
    permission_request = relationship(
        "PermissionRequest", foreign_keys=[permission_request_id]
    )
    bureau = relationship("Bureau", foreign_keys=[bureau_id])
    circonscription = relationship(
        "Circonscription", foreign_keys=[circonscription_id]
    )

    def __init__(self, **kwargs):
        if "metadata" in kwargs:
            kwargs["metadata_"] = kwargs.pop("metadata")
        super().__init__(**kwargs)
