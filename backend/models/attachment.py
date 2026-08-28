from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    func,
)

from sqlalchemy.orm import relationship

from app.database.base import Base


class DocumentAttachment(Base):

    __tablename__ = "document_attachments"

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
    )

    nom_original = Column(
        String(255),
        nullable=False,
    )

    nom_stockage = Column(
        String(255),
        nullable=False,
    )

    chemin_fichier = Column(
        String(500),
        nullable=False,
    )

    type_mime = Column(
        String(100),
        nullable=True,
    )

    taille = Column(
        Integer,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # ==========================
    # Relation avec le document
    # ==========================

    document = relationship(
        "Document",
        back_populates="attachments",
    )