from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class Phase(Base):
    __tablename__ = "phases"

    id = Column(Integer, primary_key=True)

    libelle = Column(String(100), unique=True)

    documents = relationship(
        "Document",
        back_populates="phase",
    )