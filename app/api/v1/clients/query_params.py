from pydantic import BaseModel


class ClientQueryParams(BaseModel):
    offset: int = 0
    limit: int = 50
