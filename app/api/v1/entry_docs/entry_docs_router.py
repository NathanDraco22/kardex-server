from fastapi import APIRouter, Depends, BackgroundTasks


from responses.v1.list_response import ListResponse
from repos.v1.entry_docs import CreateEntryDoc, EntryDocInDb

from app_middleware import auth_middleware

from .entry_docs_controller import entry_docs_controller
from .query_params import EntryDocQueryParams


entry_docs_router = APIRouter(
    tags=["entry_docsV1"], dependencies=[Depends(auth_middleware)]
)


@entry_docs_router.post("")
async def create_entry_doc(
    body: CreateEntryDoc, bg_tasks: BackgroundTasks
) -> EntryDocInDb:
    return await entry_docs_controller.create_entry_doc(body, bg_tasks)


@entry_docs_router.get("")
async def get_all_entry_docs() -> list[EntryDocInDb]:
    return await entry_docs_controller.get_all_entry_docs()


@entry_docs_router.get("/paginated")
async def get_paginated_entry_docs(
    query_params: EntryDocQueryParams = Depends(),
) -> ListResponse[EntryDocInDb]:
    return await entry_docs_controller.get_paginated_entry_docs(
        **query_params.model_dump()
    )


@entry_docs_router.get("/{entry_doc_id}")
async def get_entry_doc_by_id(entry_doc_id: str) -> EntryDocInDb:
    return await entry_docs_controller.get_entry_doc_by_id(entry_doc_id)
