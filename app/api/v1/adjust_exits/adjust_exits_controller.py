from fastapi import HTTPException, status
from api.common.query_params import AdjustQueryParams
from core.adjust_ledger.adjust_ledger import AdjustLedgerManager

from responses.v1 import ListResponse

from repos.v1.adjust_exits import (
    CreateAdjustExit,
    UpdateAdjustExit,
    AdjustExitInDb,
    AdjustExitsRepository,
    AdjustExitsDataSource,
)


class AdjustExitsController:
    def __init__(self, adjust_exits_repo: AdjustExitsRepository) -> None:
        self.adjust_exits_repo = adjust_exits_repo
        self.adjust_ledger_manager = AdjustLedgerManager()

    async def create_adjust_exit(self, body: CreateAdjustExit) -> AdjustExitInDb:
        res, _ = await self.adjust_ledger_manager.regis_adjust_exit(body)
        return res

    async def get_all_adjust_exits(
        self, params: AdjustQueryParams
    ) -> ListResponse[AdjustExitInDb]:
        raw_params = params.model_dump(exclude_none=True)
        adjust_exits = await self.adjust_exits_repo.get_all_adjust_exits(**raw_params)
        return ListResponse(
            count=len(adjust_exits),
            data=adjust_exits,
        )

    async def get_adjust_exit_by_id(self, adjust_exit_id: str) -> AdjustExitInDb:
        adjust_exit = await self.adjust_exits_repo.get_adjust_exit_by_id(adjust_exit_id)
        if adjust_exit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AdjustExit not found",
            )
        return adjust_exit

    async def get_adjust_exit_by_doc_number(
        self, doc_number: str, branch_id: str
    ) -> AdjustExitInDb:
        adjust_exit = await self.adjust_exits_repo.get_adjust_exit_by_doc_number(
            doc_number, branch_id
        )
        if adjust_exit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AdjustExit not found",
            )
        return adjust_exit

    async def update_adjust_exit_by_id(
        self, adjust_exit_id: str, body: UpdateAdjustExit
    ) -> AdjustExitInDb:
        updated_adjust_exit = await self.adjust_exits_repo.update_adjust_exit_by_id(
            adjust_exit_id, body
        )
        if updated_adjust_exit is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AdjustExit not found",
            )
        return updated_adjust_exit


adjust_exits_controller = AdjustExitsController(
    adjust_exits_repo=AdjustExitsRepository(
        adjust_exits_ds=AdjustExitsDataSource(),
    ),
)
