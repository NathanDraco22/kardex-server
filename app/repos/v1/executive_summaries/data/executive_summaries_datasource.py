from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import ExecutiveSummariesCollection


class ExecutiveSummariesDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_executive_summary(
        self, executive_summary: dict[str, Any]
    ) -> dict[str, Any]:
        collection = ExecutiveSummariesCollection()
        await collection.create_executive_summary(executive_summary)
        return executive_summary

    async def get_all_executive_summaries(self, **kwargs) -> list[dict[str, Any]]:
        collection = ExecutiveSummariesCollection()
        return await collection.fetch_all_executive_summaries(**kwargs)

    async def get_executive_summary_by_id(
        self, executive_summary_id: str
    ) -> dict[str, Any] | None:
        collection = ExecutiveSummariesCollection()
        return await collection.fetch_executive_summary_by_id(executive_summary_id)

    async def update_executive_summary_by_id(
        self, executive_summary_id: str, executive_summary: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = ExecutiveSummariesCollection()
        return await collection.update_executive_summary_by_id(
            executive_summary_id, executive_summary
        )

    async def delete_executive_summary_by_id(
        self, executive_summary_id: str
    ) -> dict[str, Any] | None:
        collection = ExecutiveSummariesCollection()
        return await collection.delete_executive_summary_by_id(executive_summary_id)
