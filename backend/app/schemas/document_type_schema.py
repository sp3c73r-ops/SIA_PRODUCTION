from pydantic import BaseModel


class DocumentTypeBase(BaseModel):
    libelle: str


class DocumentTypeCreate(DocumentTypeBase):
    pass


class DocumentTypeUpdate(DocumentTypeBase):
    pass


class DocumentTypeResponse(DocumentTypeBase):
    id: int

    class Config:
        from_attributes = True