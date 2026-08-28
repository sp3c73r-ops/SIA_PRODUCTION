from pydantic import BaseModel, ConfigDict


class PhaseBase(BaseModel):
    libelle: str

    model_config = ConfigDict(str_strip_whitespace=True)


class PhaseCreate(PhaseBase):
    pass


class PhaseUpdate(PhaseBase):
    pass


class PhaseResponse(PhaseBase):
    id: int

    class Config:
        from_attributes = True