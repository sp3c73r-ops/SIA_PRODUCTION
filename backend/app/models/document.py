from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Date,
    DateTime,
    Boolean,
    ForeignKey,
    func,
)

from sqlalchemy.orm import relationship

from app.database.base import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)

    bureau_id = Column(
        Integer,
        ForeignKey(
            "bureaux.id",
            ondelete="RESTRICT",
        ),
        nullable=True,
    )

    reference_archive = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    nom_document = Column(
        String(255),
        nullable=False,
    )

    date_creation = Column(
        Date,
        nullable=False,
    )

    type_document_id = Column(
        Integer,
        ForeignKey("document_types.id"),
        nullable=False,
    )

    phase_id = Column(
        Integer,
        ForeignKey("phases.id"),
        nullable=True,
    )

    code_foncier = Column(
        String(100),
    )

    circonscription_id = Column(
        Integer,
        ForeignKey("circonscriptions.id"),
        nullable=True,
    )

    # NumCad / Réf / Indice
    # Peut contenir des chiffres, lettres, espaces et symboles
    numero_ordre = Column(
        String(100),
        nullable=True,
    )

    encodeur_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
    )

    remarque = Column(
        Text,
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

    is_deleted = Column(
        Boolean,
        default=False,
    )

    # ==========================
    # Relations
    # ==========================

    bureau = relationship(
        "Bureau",
        back_populates="documents",

    )
    type_document = relationship(
        "DocumentType",
        back_populates="documents",
    )

    phase = relationship(
        "Phase",
        back_populates="documents",
    )

    circonscription = relationship(
        "Circonscription",
        back_populates="documents",
    )

    encodeur = relationship(
        "User",
        back_populates="documents",
    )
    attachments = relationship(
        "DocumentAttachment",
        back_populates="document",
        cascade="all, delete-orphan",
    )
    custom_field_values = relationship(
        "DocumentFieldValue",
        back_populates="document",
        cascade="all, delete-orphan",
    )

    permission_requests = relationship(
        "PermissionRequest",
        back_populates="document",
    )

    @staticmethod
    def _extract_typed_value(item):
        if item.value_string is not None:
            return item.value_string
        if item.value_text is not None:
            return item.value_text
        if item.value_integer is not None:
            return item.value_integer
        if item.value_decimal is not None:
            return float(item.value_decimal)
        if item.value_date is not None:
            return item.value_date
        if item.value_datetime is not None:
            return item.value_datetime
        if item.value_boolean is not None:
            return item.value_boolean
        return None

    @property
    def custom_fields(self):
        values = {}
        for item in self.custom_field_values or []:
            if (
                item.document_field
                and item.document_field.name
            ):
                values[item.document_field.name] = (
                    self._extract_typed_value(item)
                )
        return values

