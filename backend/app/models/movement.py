from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.database.base import Base


class Movement(Base):

    __tablename__ = "movements"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    document_id = Column(
        Integer,
        ForeignKey(
            "documents.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    type_mouvement = Column(
        String(50),
        nullable=False,
    )

    motif = Column(
        Text,
        nullable=True,
    )

    statut = Column(
        String(30),
        nullable=False,
        default="EN_COURS",
    )

    date_mouvement = Column(
        DateTime,
        nullable=False,
        default=datetime.now,
    )

    date_retour = Column(
        DateTime,
        nullable=True,
    )

    document = relationship(
        "Document",
        backref="movements",
    )

    user = relationship(
        "User",
        backref="movements",
    )