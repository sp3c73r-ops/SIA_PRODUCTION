from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


VALID_FIELD_TYPES = {
    "string",
    "integer",
    "decimal",
    "date",
    "datetime",
    "boolean",
    "text",
}


class DocumentFieldBase(BaseModel):
    name: str
    label: str
    field_type: str
    required: bool = False
    active: bool = True
    order_index: int = 0
    description: Optional[str] = None

    model_config = ConfigDict(str_strip_whitespace=True)

    def model_post_init(self, __context):
        if self.field_type not in VALID_FIELD_TYPES:
            raise ValueError(
                "field_type doit être l'un des suivants : "
                "string, integer, decimal, date, datetime, boolean, text."
            )


class DocumentFieldCreate(DocumentFieldBase):
    pass


class DocumentFieldUpdate(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    field_type: Optional[str] = None
    required: Optional[bool] = None
    active: Optional[bool] = None
    order_index: Optional[int] = None
    description: Optional[str] = None

    model_config = ConfigDict(str_strip_whitespace=True)

    def model_post_init(self, __context):
        if self.field_type is not None and self.field_type not in VALID_FIELD_TYPES:
            raise ValueError(
                "field_type doit être l'un des suivants : "
                "string, integer, decimal, date, datetime, boolean, text."
            )


class DocumentFieldResponse(DocumentFieldBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
