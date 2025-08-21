from .data.exit_histories_datasource import ExitHistoriesDataSource
from .models.exit_history_model import ExitHistoryInDb


class ExitHistoriesRepository:
    def __init__(self, exit_histories_ds: ExitHistoriesDataSource):
        self.exit_histories_ds = exit_histories_ds

    async def get_exit_history(
        self, branch_id: str, client_id: str | None, offset: int, limit: int
    ) -> list[ExitHistoryInDb]:
        res = await self.exit_histories_ds.get_exit_history(
            branch_id, client_id, offset, limit
        )

        exit_histories = [
            ExitHistoryInDb.model_validate(exit_history) for exit_history in res
        ]

        return exit_histories
