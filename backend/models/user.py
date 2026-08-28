from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)

    nom = Column(String(150))

    prenom = Column(String(150))

    username = Column(String(100), unique=True)

    password = Column(String(255))

    actif = Column(Boolean, default=True)

    bureau = Column(
        String(50),
        nullable=True,
    )

    documents = relationship(
        "Document",
        back_populates="encodeur",
    )
