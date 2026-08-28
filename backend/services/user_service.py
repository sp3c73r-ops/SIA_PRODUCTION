from app.models.user import User
from app.repositories.user_repository import user_repository
from app.security.password import hash_password


class UserService:

    def __init__(self):
        self.repository = user_repository

    def create(self, db, data):

        if self.repository.get_by_username(db, data.username):
            raise Exception("Nom d'utilisateur déjà utilisé.")

        user = User(
            nom=data.nom,
            prenom=data.prenom,
            username=data.username,
            password=hash_password(data.password),
            actif=data.actif,
            bureau=data.bureau,
        )

        return self.repository.create(db, user)


user_service = UserService()
