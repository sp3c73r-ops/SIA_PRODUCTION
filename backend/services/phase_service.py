from app.models.phase import Phase
from app.repositories.phase_repository import phase_repository


class PhaseService:

    def __init__(self):
        self.repository = phase_repository

    def create(self, db, data):
        libelle = data.libelle.strip()

        if not libelle:
            raise ValueError(
                "Le libellé de la nature est obligatoire."
            )

        existing = self.repository.get_by_libelle(
            db,
            libelle,
        )
        if existing:
            raise ValueError(
                "Cette nature existe déjà."
            )

        phase = Phase(libelle=libelle)
        return self.repository.create(db, phase)

    def update(self, db, phase_id: int, data):
        phase = self.repository.get_by_id(db, phase_id)

        if not phase:
            return None

        libelle = data.libelle.strip()

        if not libelle:
            raise ValueError(
                "Le libellé de la nature est obligatoire."
            )

        existing = self.repository.get_by_libelle(
            db,
            libelle,
        )
        if existing and existing.id != phase.id:
            raise ValueError(
                "Cette nature existe déjà."
            )

        phase.libelle = libelle

        return self.repository.update(db, phase)

    def delete(self, db, phase_id: int):
        phase = self.repository.get_by_id(db, phase_id)

        if not phase:
            return False

        usage_count = self.repository.count_documents_using_phase(
            db,
            phase_id,
        )

        if usage_count > 0:
            raise ValueError(
                "Cette nature est déjà utilisée par des documents et ne peut pas être supprimée."
            )

        return self.repository.delete(db, phase)


phase_service = PhaseService()