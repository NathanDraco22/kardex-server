from fastapi import HTTPException, status, BackgroundTasks

from responses.v1.list_response import ListResponse
from core.product_ledger.product_ledger_manager import ProductLedgerManager

from repos.v1.expiration_logs import (
    ExpirationLogsRepository,
    ExpirationLogsDataSource,
    CreateExpirationLog,
    ProductInfo,
)
from repos.v1.entry_docs import (
    CreateEntryDoc,
    EntryDocInDb,
    EntryDocsRepository,
    EntryDocsDataSource,
    EntryHistoryInDb,
)


class EntryDocsController:
    def __init__(
        self,
        entry_docs_repo: EntryDocsRepository,
        product_ledger_manager: ProductLedgerManager,
        expiration_logs_repo: ExpirationLogsRepository,
    ) -> None:
        self.entry_docs_repo = entry_docs_repo
        self.product_ledger_manager = product_ledger_manager
        self.expiration_logs_repo = expiration_logs_repo

    async def _create_expiration_logs(self, entry_doc: EntryDocInDb) -> None:
        try:
            entry_items = entry_doc.items
            creation_logs: list[CreateExpirationLog] = []
            for entry_item in entry_items:
                expiration_date = entry_item.expirationDate
                if expiration_date is None:
                    continue
                product_info = ProductInfo(
                    id=entry_item.productId,
                    name=entry_item.productName,
                    brandName=entry_item.brandName,
                    unitName=entry_item.unitName,
                )
                new_expiration_log = CreateExpirationLog(
                    product=product_info,
                    branchId=entry_doc.branchId,
                    expirationDate=expiration_date,
                )
                creation_logs.append(new_expiration_log)

            await self.expiration_logs_repo.create_many_expiration_logs(creation_logs)

        except Exception as e:
            print(e)

    async def create_entry_doc(
        self, body: CreateEntryDoc, bg_tasks: BackgroundTasks
    ) -> EntryDocInDb:
        entry_doc, _ = await self.product_ledger_manager.regis_entry_doc(body)
        bg_tasks.add_task(self._create_expiration_logs, entry_doc)
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

    async def get_entry_history(
        self, **kwargs
    ) -> ListResponse[EntryHistoryInDb]:
        mapped_kwargs = {
            "branch_id": kwargs.get("branch_id"),
            "supplier_id": kwargs.get("supplierId"),
            "offset": kwargs.get("offset"),
            "limit": kwargs.get("limit"),
            "start_date": kwargs.get("startDate"),
            "end_date": kwargs.get("endDate"),
        }
        entry_histories = await self.entry_docs_repo.get_entry_history(**mapped_kwargs)
        return ListResponse(count=len(entry_histories), data=entry_histories)

    async def get_history_by_id_with_supplier(
        self, entry_doc_id: str
    ) -> EntryHistoryInDb:
        entry_history = await self.entry_docs_repo.get_entry_history_by_id_with_supplier(
            entry_doc_id
        )
        if not entry_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entry history not found",
            )
        return entry_history

    async def get_entry_history_by_doc_number_and_branch_id(
        self, doc_number: str, branch_id: str
    ) -> EntryHistoryInDb:
        entry_history = await self.entry_docs_repo.get_entry_history_by_doc_number_and_branch_id(
            doc_number, branch_id
        )
        if not entry_history:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Entry history not found",
            )
        return entry_history


entry_docs_controller = EntryDocsController(
    entry_docs_repo=EntryDocsRepository(
        entry_docs_ds=EntryDocsDataSource(),
    ),
    product_ledger_manager=ProductLedgerManager(),
    expiration_logs_repo=ExpirationLogsRepository(
        expiration_logs_ds=ExpirationLogsDataSource(),
    ),
)
