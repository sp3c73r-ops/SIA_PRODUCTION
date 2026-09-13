from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database.base import Base


class Circonscription(Base):
    __tablename__ = "circonscriptions"

    id = Column(Integer, primary_key=True)

    nom = Column(String(150), unique=True)

    bureaux = relationship(
        "Bureau",
        back_populates="circonscription",
    )

    admins = relationship(
        "User",
        back_populates="admin_circonscription",
    )

    documents = relationship(
        "Document",
        back_populates="circonscription",
    )