from repos.v1.exit_histories import (
    ExitHistoryInDb,
    ExitHistoriesRepository,
    ExitHistoriesDataSource,
)

from responses.v1 import ListResponse


class ExitHistoriesController:
    def __init__(self, exit_histories_repo: ExitHistoriesRepository) -> None:
        self.exit_histories_repo = exit_histories_repo

    async def get_exit_history(
        self, branch_id: str, client_id: str | None, offset: int, limit: int
    ) -> ListResponse[ExitHistoryInDb]:
        exit_histories = await self.exit_histories_repo.get_exit_history(
            branch_id, client_id, offset, limit
        )
        return ListResponse(count=len(exit_histories), data=exit_histories)


exit_histories_controller = ExitHistoriesController(
    exit_histories_repo=ExitHistoriesRepository(
        exit_histories_ds=ExitHistoriesDataSource(),
    ),
)
