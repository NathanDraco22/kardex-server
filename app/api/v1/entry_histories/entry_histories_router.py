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
    return await entry_histories_controller.get_entry_history(
        **query_params.model_dump()
    )
