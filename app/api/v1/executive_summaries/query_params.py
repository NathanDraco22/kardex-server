from pydantic import BaseModel


class ExecutiveSummaryQueryParams(BaseModel):
    offset: int = 0
    limit: int = 50
    startDate: int | None = None
    endDate: int | None = None
