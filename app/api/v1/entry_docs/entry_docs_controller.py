from fastapi import HTTPException, status

from responses.v1.list_response import ListResponse
from core.product_ledger.product_ledger_manager import ProductLedgerManager

from repos.v1.entry_docs import (
    CreateEntryDoc,
    EntryDocInDb,
    EntryDocsRepository,
    EntryDocsDataSource,
)


class EntryDocsController:
    def __init__(
        self,
        entry_docs_repo: EntryDocsRepository,
        product_ledger_manager: ProductLedgerManager,
    ) -> None:
        self.entry_docs_repo = entry_docs_repo
        self.product_ledger_manager = product_ledger_manager

    async def create_entry_doc(self, body: CreateEntryDoc) -> EntryDocInDb:
        entry_doc, _ = await self.product_ledger_manager.regis_entry_doc(body)
        return entry_doc

    async def get_all_entry_docs(self) -> list[EntryDocInDb]:
        entry_docs = await self.entry_docs_repo.get_all_entry_docs()
        return entry_docs

    async def get_paginated_entry_docs(
        self, offset: int, limit: int, branch_id: str
    ) -> ListResponse[EntryDocInDb]:
        entry_docs = await self.entry_docs_repo.get_paginated_entry_docs(
            offset, limit, branch_id
        )
        return ListResponse(
            count=len(entry_docs),
            data=entry_docs,
        )

    async def get_entry_doc_by_id(self, entry_doc_id: str) -> EntryDocInDb:
        entry_doc = await self.entry_docs_repo.get_entry_doc_by_id(entry_doc_id)
        if entry_doc is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="EntryDoc not found",
            )
        return entry_doc


entry_docs_controller = EntryDocsController(
    entry_docs_repo=EntryDocsRepository(
        entry_docs_ds=EntryDocsDataSource(),
    ),
    product_ledger_manager=ProductLedgerManager(),
)
