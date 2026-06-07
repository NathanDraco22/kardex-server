from fastapi import HTTPException
from kardex.repos.v1.exit_histories import (
    ExitHistoryInDb,
    ExitHistoriesRepository,
    ExitHistoriesDataSource,
)

from responses.v1 import ListResponse

from kardex.repos.v1.common.filter_params import ExitHistoryFilterParams


class ExitHistoriesController:
    def __init__(self, exit_histories_repo: ExitHistoriesRepository) -> None:
        self.exit_histories_repo = exit_histories_repo

    async def get_exit_history(
        self, params: ExitHistoryFilterParams
    ) -> ListResponse[ExitHistoryInDb]:
        exit_histories = await self.exit_histories_repo.get_exit_history(params)
        return ListResponse(count=len(exit_histories), data=exit_histories)

    async def get_exit_doc_history_by_id_with_client(
        self, exit_doc_id: str
    ) -> ExitHistoryInDb:
        res = await self.exit_histories_repo.get_exit_doc_history_by_id_with_client(
            exit_doc_id
        )

        if res is None:
            raise HTTPException(status_code=404, detail="Exit history not found")

        return ExitHistoryInDb.model_validate(res)

    async def get_exit_history_by_doc_number_and_branch_id(
        self, doc_number: str, branch_id: str
    ) -> ExitHistoryInDb:
        res = (
            await self.exit_histories_repo.get_exit_history_by_doc_number_and_branch_id(
                doc_number, branch_id
            )
        )

        if res is None:
            raise HTTPException(status_code=404, detail="Exit history not found")

        return ExitHistoryInDb.model_validate(res)


exit_histories_controller = ExitHistoriesController(
    exit_histories_repo=ExitHistoriesRepository(
        exit_histories_ds=ExitHistoriesDataSource(),
    ),
)
