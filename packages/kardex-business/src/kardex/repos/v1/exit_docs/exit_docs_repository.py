from .data.exit_docs_datasource import ExitDocsDataSource
from .models.exit_doc_model import ExitDocInDb, ExitHistoryInDb
from kardex.repos.v1.common.filter_params import ExitDocFilterParams

class ExitDocsRepository:
    _instance: "ExitDocsRepository | None" = None

    def __init__(self, exit_docs_ds: ExitDocsDataSource):
        self.exit_docs_ds = exit_docs_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ExitDocsRepository(
                exit_docs_ds=ExitDocsDataSource()
            )
        return cls._instance

    async def get_all_exit_docs(self) -> list[ExitDocInDb]:
        results = await self.exit_docs_ds.get_all_exit_docs()
        models = [ExitDocInDb.model_validate(result) for result in results]
        return models

    async def get_paginated_exit_docs(
        self, params: ExitDocFilterParams
    ) -> list[ExitDocInDb]:
        results = await self.exit_docs_ds.get_paginated_exit_docs(
            params.offset, params.limit, params.branch_id
        )
        models = [ExitDocInDb.model_validate(result) for result in results]

        return models

    async def get_exit_doc_by_id(self, exit_doc_id: str) -> ExitDocInDb | None:
        result = await self.exit_docs_ds.get_exit_doc_by_id(exit_doc_id)

        if result is None:
            return None

        return ExitDocInDb.model_validate(result)

    async def get_exit_doc_by_doc_number(self, doc_number: str) -> ExitDocInDb | None:
        result = await self.exit_docs_ds.get_exit_doc_by_doc_number(doc_number)

        if result is None:
            return None

        return ExitDocInDb.model_validate(result)

    async def get_exit_doc_by_doc_number_and_client(
        self, client_id: str, doc_number: str
    ) -> ExitDocInDb | None:
        result = await self.exit_docs_ds.get_exit_doc_by_doc_number_and_client(
            client_id,
            doc_number,
        )

        if result is None:
            return None

        return ExitDocInDb.model_validate(result)

    async def get_exit_history(
        self, params: ExitDocFilterParams
    ) -> list[ExitHistoryInDb]:
        mapped_kwargs = {
            "branch_id": params.branch_id,
            "client_id": params.clientId,
            "offset": params.offset,
            "limit": params.limit,
            "start_date": params.startDate,
            "end_date": params.endDate,
        }
        results = await self.exit_docs_ds.get_exit_history(**mapped_kwargs)
        return [ExitHistoryInDb.model_validate(result) for result in results]

    async def get_exit_history_by_id_with_client(
        self, exit_doc_id: str
    ) -> ExitHistoryInDb | None:
        result = await self.exit_docs_ds.get_exit_history_by_id_with_client(
            exit_doc_id
        )
        if result is None:
            return None
        return ExitHistoryInDb.model_validate(result)

    async def get_exit_history_by_doc_number_and_branch_id(
        self, doc_number: str, branch_id: str
    ) -> ExitHistoryInDb | None:
        result = await self.exit_docs_ds.get_exit_history_by_doc_number_and_branch_id(
            doc_number, branch_id
        )
        if result is None:
            return None
        return ExitHistoryInDb.model_validate(result)
