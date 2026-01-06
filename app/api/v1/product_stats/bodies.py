from pydantic import BaseModel


class CreateXlsxFileBody(BaseModel):
    projectionDays: int
