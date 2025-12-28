from pydantic import BaseModel


class TransferQueryParams(BaseModel):
    offset: int = 0
    limit: int = 50
    status: str | None = None
    origin: str | None = None
    destination: str | None = None
