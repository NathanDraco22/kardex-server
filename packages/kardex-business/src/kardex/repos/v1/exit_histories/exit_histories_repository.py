from .data.exit_histories_datasource import ExitHistoriesDataSource
from .models.exit_history_model import ExitHistoryInDb
from kardex.repos.v1.common.filter_params import ExitHistoryFilterParams

class ExitHistoriesRepository:
    _instance: "ExitHistoriesRepository | None" = None

    def __init__(self, exit_histories_ds: ExitHistoriesDataSource):
        self.exit_histories_ds = exit_histories_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ExitHistoriesRepository(
                exit_histories_ds=ExitHistoriesDataSource()
            )
        return cls._instance

    async def get_exit_history(
        self, params: ExitHistoryFilterParams
    ) -> list[ExitHistoryInDb]:
        res = await self.exit_histories_ds.get_exit_history(
            **params.to_query_params()
        )

        exit_histories = [
            ExitHistoryInDb.model_validate(exit_history) for exit_history in res
        ]

        return exit_histories

    async def get_exit_doc_history_by_id_with_client(
        self, exit_doc_id: str
    ) -> ExitHistoryInDb | None:
        res = await self.exit_histories_ds.get_exit_doc_history_by_id_with_client(
            exit_doc_id
        )
        if res is None:
            return None
        return ExitHistoryInDb.model_validate(res)

    async def get_exit_history_by_doc_number_and_branch_id(
        self, doc_number: str, branch_id: str
    ) -> ExitHistoryInDb | None:
        res = await self.exit_histories_ds.get_exit_history_by_doc_number_and_branch_id(
            doc_number, branch_id
        )
        if res is None:
            return None
        return ExitHistoryInDb.model_validate(res)
