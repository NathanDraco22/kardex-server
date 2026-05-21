from typing import Any
from kardex.services.mongo_collections.v1 import DailySummariesCollection


class DailySummariesDataSource:
    async def create_daily_summary(
        self, daily_summary: dict[str, Any]
    ) -> dict[str, Any]:
        collection = DailySummariesCollection.get_instance()
        await collection.create_daily_summary(daily_summary)
        return daily_summary

    async def get_all_daily_summaries(self, **kwargs) -> list[dict[str, Any]]:
        collection = DailySummariesCollection.get_instance()
        return await collection.fetch_all_daily_summaries(**kwargs)

    async def get_daily_summary_by_start_date_range(
        self, **kwargs
    ) -> list[dict[str, Any]]:
        collection = DailySummariesCollection.get_instance()
        return await collection.fetch_daily_summary_by_start_date_range(**kwargs)

    async def get_daily_summary_by_id(
        self, daily_summary_id: str
    ) -> dict[str, Any] | None:
        collection = DailySummariesCollection.get_instance()
        return await collection.fetch_daily_summary_by_id(daily_summary_id)

    async def get_daily_summary_by_date_id(self, date_id: str) -> dict[str, Any] | None:
        collection = DailySummariesCollection.get_instance()
        return await collection.fetch_daily_summary_by_date_id(date_id)

    async def update_daily_summary_by_id(
        self, daily_summary_id: str, daily_summary: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = DailySummariesCollection.get_instance()
        return await collection.update_daily_summary_by_id(
            daily_summary_id, daily_summary
        )

    async def delete_daily_summary_by_id(
        self, daily_summary_id: str
    ) -> dict[str, Any] | None:
        collection = DailySummariesCollection.get_instance()
        return await collection.delete_daily_summary_by_id(daily_summary_id)
