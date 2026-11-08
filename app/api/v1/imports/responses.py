from pydantic import BaseModel


class ImportResponse(BaseModel):
    status: str
    message: str
    importedCount: int
