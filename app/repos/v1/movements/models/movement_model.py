from pydantic import BaseModel
from enum import StrEnum


class MovementType(StrEnum):
    IN = "in"
    OUT = "out"


class ReferenceDocumentType(StrEnum):
    ENTRY = "entry"
    PURCHASE = "purchase"
    EXIT = "exit"
    SALE = "sale"


class BaseMovement(BaseModel):
    type: MovementType
    product_id: str
    branch_id: str
    quantity: int
    cost_at_moment: float
    refence_document_id: str
    reference_document_type: ReferenceDocumentType


class CreateMovement(BaseMovement):
    pass


class MovementInDb(BaseMovement):
    id: str
    created_at: int
