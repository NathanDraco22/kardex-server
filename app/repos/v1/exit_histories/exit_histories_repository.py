from .data.exit_histories_datasource import ExitHistoriesDataSource
from .models.exit_history_model import ExitHistoryInDb
from .params.get_exit_history_params import GetExitHistoryParams


class ExitHistoriesRepository:
    def __init__(self, exit_histories_ds: ExitHistoriesDataSource):
        self.exit_histories_ds = exit_histories_ds

    async def get_exit_history(
        self, params: GetExitHistoryParams
    ) -> list[ExitHistoryInDb]:
        res = await self.exit_histories_ds.get_exit_history(**params.to_dict())

        exit_histories = [
            ExitHistoryInDb.model_validate(exit_history) for exit_history in res
        ]

        return exit_histories
