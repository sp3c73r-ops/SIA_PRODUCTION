from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class Bureau(Base):
    __tablename__ = "bureaux"
    __table_args__ = (
        UniqueConstraint(
            "circonscription_id",
            "code",
            name="uq_bureaux_circonscription_code",
        ),
        UniqueConstraint(
            "circonscription_id",
            "nom",
            name="uq_bureaux_circonscription_nom",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    circonscription_id = Column(
        Integer,
        ForeignKey(
            "circonscriptions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    code = Column(
        String(50),
        nullable=False,
        index=True,
    )

    nom = Column(
        String(150),
        nullable=False,
    )

    description = Column(
        Text,
        nullable=True,
    )

    actif = Column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    circonscription = relationship(
        "Circonscription",
        back_populates="bureaux",
    )

    users = relationship(
        "User",
        back_populates="bureau",
    )

    documents = relationship(
        "Document",
        back_populates="bureau",
    )

    permission_requests = relationship(
        "PermissionRequest",
        back_populates="bureau",
    )