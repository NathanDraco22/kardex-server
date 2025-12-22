from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import DailySummariesCollection


class DailySummariesDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_daily_summary(
        self, daily_summary: dict[str, Any]
    ) -> dict[str, Any]:
        collection = DailySummariesCollection()
        await collection.create_daily_summary(daily_summary)
        return daily_summary

    async def get_all_daily_summaries(self, **kwargs) -> list[dict[str, Any]]:
        collection = DailySummariesCollection()
        return await collection.fetch_all_daily_summaries(**kwargs)

    async def get_daily_summary_by_id(
        self, daily_summary_id: str
    ) -> dict[str, Any] | None:
        collection = DailySummariesCollection()
        return await collection.fetch_daily_summary_by_id(daily_summary_id)

    async def get_daily_summary_by_date_id(self, date_id: str) -> dict[str, Any] | None:
        collection = DailySummariesCollection()
        return await collection.fetch_daily_summary_by_date_id(date_id)

    async def update_daily_summary_by_id(
        self, daily_summary_id: str, daily_summary: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = DailySummariesCollection()
        return await collection.update_daily_summary_by_id(
            daily_summary_id, daily_summary
        )

    async def delete_daily_summary_by_id(
        self, daily_summary_id: str
    ) -> dict[str, Any] | None:
        collection = DailySummariesCollection()
        return await collection.delete_daily_summary_by_id(daily_summary_id)
