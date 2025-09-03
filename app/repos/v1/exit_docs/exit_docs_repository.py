from .data.exit_docs_datasource import ExitDocsDataSource
from .models.exit_doc_model import ExitDocInDb


class ExitDocsRepository:
    def __init__(self, exit_docs_ds: ExitDocsDataSource):
        self.exit_docs_ds = exit_docs_ds

    async def get_all_exit_docs(self) -> list[ExitDocInDb]:
        results = await self.exit_docs_ds.get_all_exit_docs()
        models = [ExitDocInDb.model_validate(result) for result in results]
        return models

    async def get_paginated_exit_docs(
        self, offset: int, page_size: int, branch_id: str
    ) -> list[ExitDocInDb]:
        results = await self.exit_docs_ds.get_paginated_exit_docs(
            offset, page_size, branch_id
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
