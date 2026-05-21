from .data.executive_summaries_datasource import ExecutiveSummariesDataSource
from .models.executive_summary_model import (
    CreateExecutiveSummary,
    ExecutiveSummaryInDb,
    SummaryType,
)

from kardex.tools import UuidTool, TimeTools

class ExecutiveSummariesRepository:
    _instance: "ExecutiveSummariesRepository | None" = None

    def __init__(self, executive_summaries_ds: ExecutiveSummariesDataSource):
        self.executive_summaries_ds = executive_summaries_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ExecutiveSummariesRepository(
                executive_summaries_ds=ExecutiveSummariesDataSource()
            )
        return cls._instance

    async def create_executive_summary(
        self, create_executive_summary: CreateExecutiveSummary
    ) -> ExecutiveSummaryInDb:
        new_executive_summary = ExecutiveSummaryInDb(
            **create_executive_summary.model_dump(),
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
        )

        await self.executive_summaries_ds.create_executive_summary(
            new_executive_summary.model_dump()
        )

        return new_executive_summary

    async def get_all_executive_summaries(self, **kwargs) -> list[ExecutiveSummaryInDb]:
        results = await self.executive_summaries_ds.get_all_executive_summaries(
            **kwargs
        )
        models = [ExecutiveSummaryInDb.model_validate(result) for result in results]
        return models

    async def get_executive_summary_by_id(
        self, executive_summary_id: str
    ) -> ExecutiveSummaryInDb | None:
        result = await self.executive_summaries_ds.get_executive_summary_by_id(
            executive_summary_id
        )

        if result is None:
            return None

        return ExecutiveSummaryInDb.model_validate(result)

    async def get_executive_summary_by_date_id_and_type(
        self, date_id: str, type: SummaryType
    ) -> ExecutiveSummaryInDb | None:
        result = (
            await self.executive_summaries_ds.get_executive_summary_by_date_id_and_type(
                date_id, type
            )
        )

        if result is None:
            return None

        return ExecutiveSummaryInDb.model_validate(result)
