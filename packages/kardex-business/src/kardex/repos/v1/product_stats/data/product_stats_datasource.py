from typing import Any
from kardex.services.mongo_collections.v1 import ProductStatsCollection


class ProductStatsDataSource:
    async def get_all_product_stats(self, **kwargs) -> list[dict[str, Any]]:
        collection = ProductStatsCollection()
        return await collection.fetch_all_product_stats(**kwargs)

    async def get_all_product_stats_with_info(self, **kwargs) -> list[dict[str, Any]]:
        collection = ProductStatsCollection()
        return await collection.fetch_all_product_stats_with_info(**kwargs)

    async def get_all_product_stats_with_account(
        self, **kwargs
    ) -> list[dict[str, Any]]:
        collection = ProductStatsCollection()
        return await collection.fetch_all_product_stats_with_account(**kwargs)

    async def get_all_product_stats_with_transaction(self) -> list[dict[str, Any]]:
        collection = ProductStatsCollection()
        return await collection.fetch_all_product_stats_with_transaction()

    async def get_product_stat_by_id(
        self, product_stat_id: str
    ) -> dict[str, Any] | None:
        collection = ProductStatsCollection()
        return await collection.fetch_product_stat_by_id(product_stat_id)

    async def set_no_transtaction_product_stats(self, last_estimation: int) -> None:
        collection = ProductStatsCollection()
        await collection.set_no_transtaction_product_stats(last_estimation)

    async def update_product_batch(self, product_stats: list[dict[str, Any]]):
        collection = ProductStatsCollection()
        await collection.update_product_batch(product_stats)
