from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class Notification(Base):
    """
    Modèle SQLAlchemy pour la persistance des notifications utilisateur.

    Correspond à la table 'notifications'.
    Utilise 'read_at' (DateTime nullable) pour déterminer le statut de lecture :
    - read_at IS NULL : Notification non lue
    - read_at IS NOT NULL : Notification lue à la date indiquée
    """

    __tablename__ = "notifications"

    id = Column(
        Integer,
        primary_key=True,
    )

    recipient_user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    action = Column(
        String(100),
        nullable=False,
    )

    title = Column(
        String(200),
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
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

    document_id = Column(
        Integer,
        ForeignKey(
            "documents.id",
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

    read_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relations ORM
    recipient = relationship(
        "User",
        foreign_keys=[recipient_user_id],
    )
    permission_request = relationship(
        "PermissionRequest",
        foreign_keys=[permission_request_id],
    )
    document = relationship(
        "Document",
        foreign_keys=[document_id],
    )
    bureau = relationship(
        "Bureau",
        foreign_keys=[bureau_id],
    )
    circonscription = relationship(
        "Circonscription",
        foreign_keys=[circonscription_id],
    )
