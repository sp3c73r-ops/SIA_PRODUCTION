from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class DocumentField(Base):
    __tablename__ = "document_fields"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    label = Column(
        String(150),
        nullable=False,
    )

    field_type = Column(
        String(30),
        nullable=False,
        default="string",
    )

    required = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    active = Column(
        Boolean,
        nullable=False,
        default=True,
    )

    order_index = Column(
        Integer,
        nullable=False,
        default=0,
    )

    description = Column(
        Text,
        nullable=True,
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

    values = relationship(
        "DocumentFieldValue",
        back_populates="document_field",
    )
