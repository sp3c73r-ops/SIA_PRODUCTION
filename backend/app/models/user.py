from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import relationship

from app.database.base import Base


USER_ROLE_ADMIN = "ADMIN"
USER_ROLE_USER = "USER"

USER_ROLES = (
    USER_ROLE_ADMIN,
    USER_ROLE_USER,
)


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
    )

    nom = Column(
        String(150),
    )

    prenom = Column(
        String(150),
    )

    username = Column(
        String(100),
        unique=True,
    )

    password = Column(
        String(255),
    )

    actif = Column(
        Boolean,
        default=True,
    )

    role = Column(
        String(20),
        default=USER_ROLE_USER,
        nullable=False,
    )

    bureau_id = Column(
        Integer,
        ForeignKey(
            "bureaux.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    admin_circonscription_id = Column(
        Integer,
        ForeignKey(
            "circonscriptions.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
        index=True,
    )

    permissions = Column(
        MutableList.as_mutable(JSONB),
        default=list,
        nullable=True,
    )

    bureau = relationship(
        "Bureau",
        back_populates="users",
    )

    admin_circonscription = relationship(
        "Circonscription",
        back_populates="admins",
    )

    documents = relationship(
        "Document",
        back_populates="encodeur",
    )

    permission_requests = relationship(
        "PermissionRequest",
        foreign_keys="PermissionRequest.user_id",
        back_populates="user",
    )

    reviewed_permission_requests = relationship(
        "PermissionRequest",
        foreign_keys="PermissionRequest.reviewed_by",
        back_populates="reviewer",
    )