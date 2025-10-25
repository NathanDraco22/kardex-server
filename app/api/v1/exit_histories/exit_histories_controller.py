from fastapi import HTTPException

from repos.v1.exit_histories import (
    ExitHistoryInDb,
    ExitHistoriesRepository,
    ExitHistoriesDataSource,
    GetExitHistoryParams,
)

from responses.v1 import ListResponse

from .query_params import ExitHistoryQueryParams


class ExitHistoriesController:
    def __init__(self, exit_histories_repo: ExitHistoriesRepository) -> None:
        self.exit_histories_repo = exit_histories_repo

    async def get_exit_history(
        self, params: ExitHistoryQueryParams
    ) -> ListResponse[ExitHistoryInDb]:
        domain_params = GetExitHistoryParams(
            branch_id=params.branchId,
            client_id=params.clientId,
            offset=params.offset,
            limit=params.limit,
            start_date=params.startDate,
            end_date=params.endDate,
        )

        exit_histories = await self.exit_histories_repo.get_exit_history(domain_params)
        return ListResponse(count=len(exit_histories), data=exit_histories)

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
