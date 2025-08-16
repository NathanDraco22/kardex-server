from fastapi import APIRouter, Depends

from responses.v1.list_response import ListResponse
from repos.v1.exit_docs import CreateExitDoc, ExitDocInDb

from .query_params import ExitDocQueryParams
from .exit_docs_controller import exit_docs_controller


exit_docs_router = APIRouter(tags=["exit_docsV1"])


@exit_docs_router.post("")
async def create_exit_doc(body: CreateExitDoc) -> ExitDocInDb:
    return await exit_docs_controller.create_exit_doc(body)


@exit_docs_router.get("")
async def get_all_exit_docs() -> list[ExitDocInDb]:
    return await exit_docs_controller.get_all_exit_docs()


@exit_docs_router.get("/paginated")
async def get_paginated_exit_docs(
    query_params: ExitDocQueryParams = Depends(),
) -> ListResponse[ExitDocInDb]:
    return await exit_docs_controller.get_paginated_exit_docs(
        **query_params.model_dump()
    )


@exit_docs_router.get("/{exit_doc_id}")
async def get_exit_doc_by_id(exit_doc_id: str) -> ExitDocInDb:
    return await exit_docs_controller.get_exit_doc_by_id(exit_doc_id)
