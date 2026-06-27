from fastapi import APIRouter, Depends
from kardex.repos.v1.entry_histories import EntryHistoryInDb
from responses.v1 import ListResponse

from app_middleware import auth_middleware

from .entry_histories_controller import entry_histories_controller
from kardex.repos.v1.common.filter_params import EntryHistoryFilterParams

entry_histories_router = APIRouter(
    tags=["entry_historiesV1"], dependencies=[Depends(auth_middleware)]
)


@entry_histories_router.get("")
async def get_entry_histories(
    query_params: EntryHistoryFilterParams = Depends(),
) -> ListResponse[EntryHistoryInDb]:
    return await entry_histories_controller.get_entry_history(query_params)


@entry_histories_router.get("/by-product/{product_id}")
async def get_entry_docs_by_product_id(
    product_id: str,
) -> ListResponse[EntryHistoryInDb]:
    return await entry_histories_controller.get_entry_docs_by_product_id(product_id)


@entry_histories_router.get("/{entry_doc_id}")
async def get_history_by_id_with_supplier(entry_doc_id: str) -> EntryHistoryInDb:
    return await entry_histories_controller.get_history_by_id_with_supplier(
        entry_doc_id
    )


@entry_histories_router.get("/{doc_number}/{branch_id}")
async def get_entry_history_by_doc_number_and_branch_id(
    doc_number: str, branch_id: str
) -> EntryHistoryInDb:
    return (
        await entry_histories_controller.get_entry_history_by_doc_number_and_branch_id(
            doc_number, branch_id
        )
    )
