from .data.daily_summaries_datasource import DailySummariesDataSource
from .models.daily_summary_model import CreateDailySummary, DailySummaryInDb

from tools import UuidTool, TimeTools


class DailySummariesRepository:
    def __init__(self, daily_summaries_ds: DailySummariesDataSource):
        self.daily_summaries_ds = daily_summaries_ds

    async def create_daily_summary(
        self, create_daily_summary: CreateDailySummary
    ) -> DailySummaryInDb:
        new_daily_summary = DailySummaryInDb(
            **create_daily_summary.model_dump(),
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
        )

        await self.daily_summaries_ds.create_daily_summary(
            new_daily_summary.model_dump()
        )

        return new_daily_summary

    async def get_all_daily_summaries(self, **kwargs) -> list[DailySummaryInDb]:
        results = await self.daily_summaries_ds.get_all_daily_summaries(**kwargs)
        models = [DailySummaryInDb.model_validate(result) for result in results]
        return models

    async def get_daily_summary_by_start_date_range(
        self, **kwargs
    ) -> list[DailySummaryInDb]:
        results = await self.daily_summaries_ds.get_daily_summary_by_start_date_range(
            **kwargs
        )
        models = [DailySummaryInDb.model_validate(result) for result in results]
        return models

    async def get_daily_summary_by_id(
        self, daily_summary_id: str
    ) -> DailySummaryInDb | None:
        result = await self.daily_summaries_ds.get_daily_summary_by_id(daily_summary_id)

        if result is None:
            return None

        return DailySummaryInDb.model_validate(result)

    async def get_daily_summary_by_date_id(
        self, date_id: str
    ) -> DailySummaryInDb | None:
        result = await self.daily_summaries_ds.get_daily_summary_by_date_id(date_id)

        if result is None:
            return None

        return DailySummaryInDb.model_validate(result)
