from pydantic import BaseModel


class DailySummaryQueryParams(BaseModel):
    offset: int = 0
    limit: int = 50
    dateId: str | None = None
    startDate: int | None = None
    endDate: int | None = None
