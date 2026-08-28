from app.models.circonscription import Circonscription
from app.repositories.circonscription_repository import (
    circonscription_repository,
)


class CirconscriptionService:

    def __init__(self):
        self.repository = circonscription_repository

    def create(self, db, data):
        item = Circonscription(**data.model_dump())
        return self.repository.create(db, item)


circonscription_service = CirconscriptionService()