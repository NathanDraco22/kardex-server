from pydantic import BaseModel


class PaginationParams(BaseModel):
    offset: int
    limit: int
