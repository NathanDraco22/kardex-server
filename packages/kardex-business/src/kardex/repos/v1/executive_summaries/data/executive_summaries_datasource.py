from typing import Any
from kardex.services.mongo_collections.v1 import ExecutiveSummariesCollection


class ExecutiveSummariesDataSource:
    async def create_executive_summary(
        self, executive_summary: dict[str, Any]
    ) -> dict[str, Any]:
        collection = ExecutiveSummariesCollection.get_instance()
        await collection.create_executive_summary(executive_summary)
        return executive_summary

    async def get_all_executive_summaries(self, **kwargs) -> list[dict[str, Any]]:
        collection = ExecutiveSummariesCollection.get_instance()
        return await collection.fetch_all_executive_summaries(**kwargs)

    async def get_executive_summary_by_id(
        self, executive_summary_id: str
    ) -> dict[str, Any] | None:
        collection = ExecutiveSummariesCollection.get_instance()
        return await collection.fetch_executive_summary_by_id(executive_summary_id)

    async def get_executive_summary_by_date_id_and_type(
        self, date_id: str, type: str
    ) -> dict[str, Any] | None:
        collection = ExecutiveSummariesCollection.get_instance()
        return await collection.fetch_executive_summary_by_date_id_and_type(
            date_id, type
        )

    async def update_executive_summary_by_id(
        self, executive_summary_id: str, executive_summary: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ExecutiveSummariesCollection.get_instance()
        return await collection.update_executive_summary_by_id(
            executive_summary_id, executive_summary
        )

    async def delete_executive_summary_by_id(
        self, executive_summary_id: str
    ) -> dict[str, Any] | None:
        collection = ExecutiveSummariesCollection.get_instance()
        return await collection.delete_executive_summary_by_id(executive_summary_id)
