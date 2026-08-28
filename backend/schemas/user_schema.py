from pydantic import BaseModel


class UserBase(BaseModel):
    nom: str
    prenom: str
    username: str
    actif: bool = True
    bureau: str | None = None


class UserCreate(UserBase):
    password: str


class UserResponse(UserBase):
    id: int

    class Config:
        from_attributes = True
