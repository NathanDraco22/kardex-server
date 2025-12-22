from fastapi import HTTPException, status

from repos.v1.executive_summaries import (
    CreateExecutiveSummary,
    ExecutiveSummaryInDb,
    ExecutiveSummariesRepository,
    ExecutiveSummariesDataSource,
)

from .query_params import ExecutiveSummaryQueryParams


class ExecutiveSummariesController:
    def __init__(self, executive_summaries_repo: ExecutiveSummariesRepository) -> None:
        self.executive_summaries_repo = executive_summaries_repo

    async def create_executive_summary(
        self, body: CreateExecutiveSummary
    ) -> ExecutiveSummaryInDb:
        return await self.executive_summaries_repo.create_executive_summary(body)

    async def get_all_executive_summaries(
        self, query: ExecutiveSummaryQueryParams
    ) -> list[ExecutiveSummaryInDb]:
        raw_query = query.model_dump(exclude_unset=True)
        executive_summaries = (
            await self.executive_summaries_repo.get_all_executive_summaries(**raw_query)
        )
        return executive_summaries

    async def get_executive_summary_by_id(
        self, executive_summary_id: str
    ) -> ExecutiveSummaryInDb:
        executive_summary = (
            await self.executive_summaries_repo.get_executive_summary_by_id(
                executive_summary_id
            )
        )
        if executive_summary is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ExecutiveSummary not found",
            )
        return executive_summary


executive_summaries_controller = ExecutiveSummariesController(
    executive_summaries_repo=ExecutiveSummariesRepository(
        executive_summaries_ds=ExecutiveSummariesDataSource(),
    ),
)
