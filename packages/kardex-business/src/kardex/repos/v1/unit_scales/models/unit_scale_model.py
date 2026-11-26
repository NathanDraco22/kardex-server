from typing import Literal

from pydantic import BaseModel, Field
from kardex.repos.v1.products.models.product_model import ExtraUnit


ScaleType = Literal[
    "weight",
    "volume",
    "length",
    "pack",
    "fractionPack",
    "custom",
]


class BaseUnitScale(BaseModel):
    name: str
    scaleType: ScaleType = "custom"
    baseUnit: str
    units: list[ExtraUnit] = []
    defaultUnitIndex: int = 0
    wholesaleUnitIndex: int = 0
    priceUnitFactor: int = Field(default=1, ge=1)
    showBasicUnit: bool = True


class CreateUnitScale(BaseUnitScale):
    pass


class UpdateUnitScale(BaseModel):
    name: str | None = None
    scaleType: ScaleType | None = None
    baseUnit: str | None = None
    units: list[ExtraUnit] | None = None
    defaultUnitIndex: int | None = None
    wholesaleUnitIndex: int | None = None
    priceUnitFactor: int | None = Field(default=None, ge=1)
    showBasicUnit: bool | None = None


class UnitScaleInDb(BaseUnitScale):
    id: str
    createdAt: int
    updatedAt: int | None = None
