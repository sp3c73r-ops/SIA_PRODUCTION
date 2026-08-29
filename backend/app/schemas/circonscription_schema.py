from pydantic import BaseModel


class CirconscriptionBase(BaseModel):
    nom: str


class CirconscriptionCreate(CirconscriptionBase):
    pass


class CirconscriptionResponse(CirconscriptionBase):
    id: int

    class Config:
        from_attributes = True