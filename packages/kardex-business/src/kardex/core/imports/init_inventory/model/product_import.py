import json

from pydantic import BaseModel, field_validator


class ProductImport(BaseModel):
    id: str | None = None
    name: str
    description: str | None = None
    code: str | None = None
    brandName: str
    unitName: str
    categoryName: str | None = None
    tags: list[str] = []
    hasIva: bool = False
    isActive: bool = True
    quantity: int
    cost: int
    price: int
    price2: int = 0
    price3: int = 0
    price4: int = 0

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, value: object) -> object:
        if value is None:
            return []

        if not isinstance(value, str):
            return value

        text = value.strip()
        if not text:
            return []

        if text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                parsed = None

            if isinstance(parsed, list):
                return [str(tag).strip() for tag in parsed if str(tag).strip()]

        return [tag.strip() for tag in text.split(";") if tag.strip()]
