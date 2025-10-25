from fastapi import APIRouter, Depends

from repos.v1.entry_histories import EntryHistoryInDb
from responses.v1 import ListResponse

from .entry_histories_controller import entry_histories_controller
from .query_params import EntryHistoryQueryParams

entry_histories_router = APIRouter(tags=["entry_historiesV1"])


@entry_histories_router.get("")
async def get_entry_histories(
    query_params: EntryHistoryQueryParams = Depends(),
) -> ListResponse[EntryHistoryInDb]:
    return await entry_histories_controller.get_entry_history(query_params)


@entry_histories_router.get("/{doc_number}/{branch_id}")
async def get_entry_history_by_doc_number_and_branch_id(
    doc_number: str, branch_id: str
) -> EntryHistoryInDb:
    return (
        await entry_histories_controller.get_entry_history_by_doc_number_and_branch_id(
            doc_number, branch_id
        )
    )
