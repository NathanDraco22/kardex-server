from fastapi import APIRouter, Depends, BackgroundTasks

from api.common.query_params import AdjustQueryParams
from kardex.repos.v1.adjust_entries import (
    CreateAdjustEntry,
    AdjustEntryInDb,
)
from app_middleware import auth_middleware
from responses.v1 import ListResponse

from .adjust_entries_controller import adjust_entries_controller


adjust_entries_router = APIRouter(
    tags=["adjust_entriesV1"], dependencies=[Depends(auth_middleware)]
)


@adjust_entries_router.post("")
async def create_adjust_entry(
    body: CreateAdjustEntry, bg_tasks: BackgroundTasks
) -> AdjustEntryInDb:
    return await adjust_entries_controller.create_adjust_entry(body, bg_tasks)


@adjust_entries_router.get("")
async def get_all_adjust_entries(
    query: AdjustQueryParams = Depends(),
) -> ListResponse[AdjustEntryInDb]:
    return await adjust_entries_controller.get_all_adjust_entries(query)


@adjust_entries_router.get("/{adjust_entry_id}")
async def get_adjust_entry_by_id(adjust_entry_id: str) -> AdjustEntryInDb:
    return await adjust_entries_controller.get_adjust_entry_by_id(adjust_entry_id)


@adjust_entries_router.get("/{branch_id}/{doc_number}")
async def get_adjust_entry_by_doc_number(
    doc_number: str, branch_id: str
) -> AdjustEntryInDb:
    return await adjust_entries_controller.get_adjust_entry_by_doc_number(
        doc_number, branch_id
    )
