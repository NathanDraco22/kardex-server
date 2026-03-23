from pydantic import BaseModel


class ClientQueryParams(BaseModel):
    offset: int = 0
    limit: int = 50
    group: str | None = None
    hasMovements: bool | None = None
