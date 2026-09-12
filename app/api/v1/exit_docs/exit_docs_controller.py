from fastapi import HTTPException, status
from responses.v1.list_response import ListResponse
from kardex.core.product_ledger.product_ledger_manager import ProductLedgerManager
from kardex.repos.v1.common.filter_params import ExitDocFilterParams
from kardex.repos.v1.exit_docs import (
    CreateExitDoc,
    ExitDocInDb,
    ExitDocsRepository,
    ExitDocsDataSource,
    ExitHistoryInDb,
)


class ExitDocsController:
    def __init__(
        self,
        exit_docs_repo: ExitDocsRepository,
        product_ledger_manager: ProductLedgerManager,
    ) -> None:
        self.exit_docs_repo = exit_docs_repo
        self.product_ledger_manager = product_ledger_manager

    async def create_exit_doc(self, body: CreateExitDoc) -> ExitDocInDb:
        exit_doc = await self.product_ledger_manager.regis_exit_doc(body)
        return exit_doc

    async def create_exit_doc_direct(self, body: CreateExitDoc) -> ExitDocInDb:
        exit_doc = await self.product_ledger_manager.regis_exit_doc_direct(body)
        return exit_doc

    async def get_all_exit_docs(self) -> list[ExitDocInDb]:
        exit_docs = await self.exit_docs_repo.get_all_exit_docs()
        return exit_docs

    async def get_paginated_exit_docs(
        self, params: ExitDocFilterParams
    ) -> ListResponse[ExitDocInDb]:
        exit_docs = await self.exit_docs_repo.get_paginated_exit_docs(params)
        return ListResponse(count=len(exit_docs), data=exit_docs)

    async def get_exit_doc_by_id(self, exit_doc_id: str) -> ExitDocInDb:
        exit_doc = await self.exit_docs_repo.get_exit_doc_by_id(exit_doc_id)
        if exit_doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ExitDoc not found",
            )
        return exit_doc

    async def get_exit_history(
        self, params: ExitDocFilterParams
    ) -> ListResponse[ExitHistoryInDb]:
        exit_histories = await self.exit_docs_repo.get_exit_history(params)
        return ListResponse(count=len(exit_histories), data=exit_histories)

    async def get_history_by_id_with_client(self, exit_doc_id: str) -> ExitHistoryInDb:
        exit_history = await self.exit_docs_repo.get_exit_history_by_id_with_client(
            exit_doc_id
        )
        if not exit_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exit history not found",
            )
        return exit_history

    async def get_exit_history_by_doc_number_and_branch_id(
        self, doc_number: str, branch_id: str
    ) -> ExitHistoryInDb:
        exit_history = (
            await self.exit_docs_repo.get_exit_history_by_doc_number_and_branch_id(
                doc_number, branch_id
            )
        )
        if not exit_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exit history not found",
            )
        return exit_history


exit_docs_controller = ExitDocsController(
    exit_docs_repo=ExitDocsRepository(
        exit_docs_ds=ExitDocsDataSource(),
    ),
    product_ledger_manager=ProductLedgerManager(),
)
