from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class Bureau(Base):
    __tablename__ = "bureaux"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    code = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    nom = Column(
        String(150),
        unique=True,
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