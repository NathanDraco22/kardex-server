from .data.product_stats_datasource import ProductStatsDataSource
from .models.product_stat_model import (
    CreateProductStat,
    UpdateProductStat,
    ProductStatInDb,
    ProductStatInDbWithInfo,
    UpdateProductStatBatchItem,
)


class ProductStatsRepository:
    def __init__(self, product_stats_ds: ProductStatsDataSource):
        self.product_stats_ds = product_stats_ds

    async def get_all_product_stats(self, **kwargs) -> list[ProductStatInDb]:
        results = await self.product_stats_ds.get_all_product_stats(**kwargs)
        models = [ProductStatInDb.model_validate(result) for result in results]
        return models

    async def get_all_product_stats_with_info(
        self, **kwargs
    ) -> list[ProductStatInDbWithInfo]:
        results = await self.product_stats_ds.get_all_product_stats_with_info(**kwargs)
        models = [ProductStatInDbWithInfo.model_validate(result) for result in results]
        return models

    async def get_product_stats_with_transaction(self) -> list[ProductStatInDb]:
        results = await self.product_stats_ds.get_all_product_stats_with_transaction()
        models = [ProductStatInDb.model_validate(result) for result in results]
        return models

    async def get_product_stat_by_id(
        self, product_stat_id: str
    ) -> ProductStatInDb | None:
        result = await self.product_stats_ds.get_product_stat_by_id(product_stat_id)

        if result is None:
            return None

        return ProductStatInDb.model_validate(result)

    async def set_no_transtaction_product_stats(self, last_estimation: int) -> None:
        await self.product_stats_ds.set_no_transtaction_product_stats(last_estimation)

    async def update_product_batch(
        self, product_stats: list[UpdateProductStatBatchItem]
    ) -> None:
        data = [item.model_dump(exclude_unset=True) for item in product_stats]
        await self.product_stats_ds.update_product_batch(data)
