from fastapi import HTTPException, status
from kardex.repos.v1.daily_summaries import (
    CreateDailySummary,
    DailySummaryInDb,
    DailySummariesRepository,
    DailySummariesDataSource,
)

from responses.v1 import ListResponse

from kardex.repos.v1.common.filter_params import DailySummaryFilterParams


class DailySummariesController:
    def __init__(self, daily_summaries_repo: DailySummariesRepository) -> None:
        self.daily_summaries_repo = daily_summaries_repo

    async def create_daily_summary(self, body: CreateDailySummary) -> DailySummaryInDb:
        return await self.daily_summaries_repo.create_daily_summary(body)

    async def get_all_daily_summaries(
        self, query: DailySummaryFilterParams
    ) -> ListResponse[DailySummaryInDb]:
        daily_summaries = await self.daily_summaries_repo.get_all_daily_summaries(
            query
        )
        return ListResponse(
            count=len(daily_summaries),
            data=daily_summaries,
        )

    async def get_daily_summary_by_id(self, daily_summary_id: str) -> DailySummaryInDb:
        daily_summary = await self.daily_summaries_repo.get_daily_summary_by_id(
            daily_summary_id
        )
        if daily_summary is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DailySummary not found",
            )
        return daily_summary


daily_summaries_controller = DailySummariesController(
    daily_summaries_repo=DailySummariesRepository(
        daily_summaries_ds=DailySummariesDataSource(),
    ),
)
