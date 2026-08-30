from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database.base import Base


PERMISSION_REQUEST_STATUS_PENDING = "PENDING"
PERMISSION_REQUEST_STATUS_APPROVED = "APPROVED"
PERMISSION_REQUEST_STATUS_REJECTED = "REJECTED"
PERMISSION_REQUEST_STATUS_EXPIRED = "EXPIRED"
PERMISSION_REQUEST_STATUS_CANCELLED = "CANCELLED"

PERMISSION_REQUEST_STATUSES = (
    PERMISSION_REQUEST_STATUS_PENDING,
    PERMISSION_REQUEST_STATUS_APPROVED,
    PERMISSION_REQUEST_STATUS_REJECTED,
    PERMISSION_REQUEST_STATUS_EXPIRED,
    PERMISSION_REQUEST_STATUS_CANCELLED,
)


class PermissionRequest(Base):
    __tablename__ = "permission_requests"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    bureau_id = Column(
        Integer,
        ForeignKey(
            "bureaux.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    permission = Column(
        String(120),
        nullable=False,
    )

    document_id = Column(
        Integer,
        ForeignKey(
            "documents.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    reason = Column(
        Text,
        nullable=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default=PERMISSION_REQUEST_STATUS_PENDING,
        server_default=PERMISSION_REQUEST_STATUS_PENDING,
    )

    requested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    reviewed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    reviewed_by = Column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="permission_requests",
    )

    bureau = relationship(
        "Bureau",
        back_populates="permission_requests",
    )

    document = relationship(
        "Document",
        back_populates="permission_requests",
    )

    reviewer = relationship(
        "User",
        foreign_keys=[reviewed_by],
        back_populates="reviewed_permission_requests",
    )
