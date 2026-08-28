from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.database.base import Base


class DocumentFieldValue(Base):
    __tablename__ = "document_field_values"

    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "document_field_id",
            name="uq_document_field_values_document_field",
        ),
    )

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

    document_field_id = Column(
        Integer,
        ForeignKey(
            "document_fields.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    value_string = Column(
        String(255),
        nullable=True,
    )

    value_text = Column(
        Text,
        nullable=True,
    )

    value_integer = Column(
        Integer,
        nullable=True,
    )

    value_decimal = Column(
        Numeric(18, 4),
        nullable=True,
    )

    value_date = Column(
        Date,
        nullable=True,
    )

    value_datetime = Column(
        DateTime(timezone=False),
        nullable=True,
    )

    value_boolean = Column(
        Boolean,
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

    document = relationship(
        "Document",
        back_populates="custom_field_values",
    )

    document_field = relationship(
        "DocumentField",
        back_populates="values",
    )
