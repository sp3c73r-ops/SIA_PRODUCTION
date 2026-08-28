from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class DocumentType(Base):
    __tablename__ = "document_types"

    id = Column(Integer, primary_key=True, index=True)

    libelle = Column(String(100), unique=True, nullable=False)

    documents = relationship(
        "Document",
        back_populates="type_document",
    )