from fastapi import APIRouter, Depends
from kardex.repos.v1.exit_histories import ExitHistoryInDb
from responses.v1.list_response import ListResponse

from app_middleware import auth_middleware

from .exit_histories_controller import exit_histories_controller
from kardex.repos.v1.common.filter_params import ExitHistoryFilterParams

exit_histories_router = APIRouter(
    tags=["exit_historiesV1"], dependencies=[Depends(auth_middleware)]
)


@exit_histories_router.get("")
async def get_exit_history(
    query_params: ExitHistoryFilterParams = Depends(),
) -> ListResponse[ExitHistoryInDb]:
    return await exit_histories_controller.get_exit_history(query_params)


@exit_histories_router.get("/{exit_doc_id}")
async def get_exit_doc_history_by_id_with_client(exit_doc_id: str) -> ExitHistoryInDb:
    return await exit_histories_controller.get_exit_doc_history_by_id_with_client(
        exit_doc_id
    )


@exit_histories_router.get("/{doc_number}/{branch_id}")
async def get_exit_history_by_doc_number_and_branch_id(
    doc_number: str, branch_id: str
) -> ExitHistoryInDb:
    return await exit_histories_controller.get_exit_history_by_doc_number_and_branch_id(
        doc_number, branch_id
    )
