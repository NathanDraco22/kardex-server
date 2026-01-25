from fastapi import HTTPException, status, BackgroundTasks
from api.common.query_params import AdjustQueryParams
from responses.v1.list_response import ListResponse
from core.adjust_ledger.adjust_ledger import AdjustLedgerManager
from core.app_notifier.app_notifier import AppNotifier
from tools import BranchesTool

from repos.v1.adjust_entries import (
    CreateAdjustEntry,
    UpdateAdjustEntry,
    AdjustEntryInDb,
    AdjustEntriesRepository,
    AdjustEntriesDataSource,
)


class AdjustEntriesController:
    def __init__(self, adjust_entries_repo: AdjustEntriesRepository) -> None:
        self.adjust_entries_repo = adjust_entries_repo
        self.adjust_ledger_manager = AdjustLedgerManager()

    async def create_adjust_entry(
        self, body: CreateAdjustEntry, bg_tasks: BackgroundTasks
    ) -> AdjustEntryInDb:
        res, _ = await self.adjust_ledger_manager.regis_adjust_entry(body)

        doc_branch = BranchesTool().get_branch_by_id(res.branchId)

        if doc_branch is not None:
            bg_tasks.add_task(
                AppNotifier().notify_adjustments,
                doc_branch.name,
                res.docNumber,
                "in",
                res.createdBy.name,
            )

        return res

    async def get_all_adjust_entries(
        self, query: AdjustQueryParams
    ) -> ListResponse[AdjustEntryInDb]:
        raw_query = query.model_dump(exclude_none=True)
        adjust_entries = await self.adjust_entries_repo.get_all_adjust_entries(
            **raw_query
        )
        return ListResponse(count=len(adjust_entries), data=adjust_entries)

    async def get_adjust_entry_by_id(self, adjust_entry_id: str) -> AdjustEntryInDb:
        adjust_entry = await self.adjust_entries_repo.get_adjust_entry_by_id(
            adjust_entry_id
        )
        if adjust_entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AdjustEntry not found",
            )
        return adjust_entry

    async def update_adjust_entry_by_id(
        self, adjust_entry_id: str, body: UpdateAdjustEntry
    ) -> AdjustEntryInDb:
        updated_adjust_entry = await self.adjust_entries_repo.update_adjust_entry_by_id(
            adjust_entry_id, body
        )
        if updated_adjust_entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AdjustEntry not found",
            )
        return updated_adjust_entry

    async def get_adjust_entry_by_doc_number(
        self, doc_number: str, branch_id: str
    ) -> AdjustEntryInDb:
        adjust_entry = await self.adjust_entries_repo.get_adjust_entry_by_doc_number(
            doc_number, branch_id
        )
        if adjust_entry is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AdjustEntry not found",
            )
        return adjust_entry


adjust_entries_controller = AdjustEntriesController(
    adjust_entries_repo=AdjustEntriesRepository(
        adjust_entries_ds=AdjustEntriesDataSource(),
    ),
)
