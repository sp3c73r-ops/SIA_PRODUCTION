from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class Circonscription(Base):
    __tablename__ = "circonscriptions"

    id = Column(Integer, primary_key=True)

    nom = Column(String(150), unique=True)

    documents = relationship(
        "Document",
        back_populates="circonscription",
    )