from fastapi import APIRouter, Depends
from kardex.repos.v1.executive_summaries import (
    CreateExecutiveSummary,
    ExecutiveSummaryInDb,
)

from responses.v1 import ListResponse

from app_middleware import cache_header_response_midnight
from app_middleware import auth_middleware

from .query_params import ExecutiveSummaryQueryParams
from .executive_summaries_controller import executive_summaries_controller


executive_summaries_router = APIRouter(
    tags=["executive_summariesV1"], dependencies=[Depends(auth_middleware)]
)


@executive_summaries_router.post(
    "", dependencies=[Depends(cache_header_response_midnight)]
)
async def create_executive_summary(
    body: CreateExecutiveSummary,
) -> ExecutiveSummaryInDb:
    return await executive_summaries_controller.create_executive_summary(body)


@executive_summaries_router.get("")
async def get_all_executive_summaries(
    query: ExecutiveSummaryQueryParams = Depends(),
) -> ListResponse[ExecutiveSummaryInDb]:
    return await executive_summaries_controller.get_all_executive_summaries(query)


@executive_summaries_router.get("/{executive_summary_id}")
async def get_executive_summary_by_id(
    executive_summary_id: str,
) -> ExecutiveSummaryInDb:
    return await executive_summaries_controller.get_executive_summary_by_id(
        executive_summary_id
    )
