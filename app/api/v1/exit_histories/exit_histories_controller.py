from datetime import datetime, time

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
        start_date: datetime | None = None
        end_date: datetime | None = None

        if params.start_date and params.end_date:
            start_date = datetime.combine(params.start_date, time.min)
            end_date = datetime.combine(params.end_date, time.max)

        domain_params = GetExitHistoryParams(
            branch_id=params.branch_id,
            client_id=params.client_id,
            offset=params.offset,
            limit=params.limit,
            start_date=start_date,
            end_date=end_date,
        )

        exit_histories = await self.exit_histories_repo.get_exit_history(domain_params)
        return ListResponse(count=len(exit_histories), data=exit_histories)


exit_histories_controller = ExitHistoriesController(
    exit_histories_repo=ExitHistoriesRepository(
        exit_histories_ds=ExitHistoriesDataSource(),
    ),
)
