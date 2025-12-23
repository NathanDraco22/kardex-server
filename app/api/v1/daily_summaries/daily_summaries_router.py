from fastapi import APIRouter, Depends

from repos.v1.daily_summaries import CreateDailySummary, DailySummaryInDb
from responses.v1 import ListResponse

from .daily_summaries_controller import daily_summaries_controller
from .query_params import DailySummaryQueryParams


daily_summaries_router = APIRouter(tags=["daily_summariesV1"])


@daily_summaries_router.post("")
async def create_daily_summary(body: CreateDailySummary) -> DailySummaryInDb:
    return await daily_summaries_controller.create_daily_summary(body)


@daily_summaries_router.get("")
async def get_all_daily_summaries(
    query: DailySummaryQueryParams = Depends(),
) -> ListResponse[DailySummaryInDb]:
    return await daily_summaries_controller.get_all_daily_summaries(query)


@daily_summaries_router.get("/{daily_summary_id}")
async def get_daily_summary_by_id(daily_summary_id: str) -> DailySummaryInDb:
    return await daily_summaries_controller.get_daily_summary_by_id(daily_summary_id)
