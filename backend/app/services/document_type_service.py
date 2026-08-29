from app.repositories.document_type_repository import (
    DocumentTypeRepository,
)


class DocumentTypeService:

    def __init__(self):

        self.repository = DocumentTypeRepository()