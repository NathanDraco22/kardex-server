from fastapi import APIRouter, Depends

from repos.v1.exit_histories import ExitHistoryInDb
from responses.v1.list_response import ListResponse

from .exit_histories_controller import exit_histories_controller
from .query_params import ExitHistoryQueryParams

exit_histories_router = APIRouter(tags=["exit_historiesV1"])


@exit_histories_router.get("")
async def get_exit_history(
    query_params: ExitHistoryQueryParams = Depends(),
) -> ListResponse[ExitHistoryInDb]:
    return await exit_histories_controller.get_exit_history(query_params)


@exit_histories_router.get("/{doc_number}/{branch_id}")
async def get_exit_history_by_doc_number_and_branch_id(
    doc_number: str, branch_id: str
) -> ExitHistoryInDb:
    return await exit_histories_controller.get_exit_history_by_doc_number_and_branch_id(
        doc_number, branch_id
    )
