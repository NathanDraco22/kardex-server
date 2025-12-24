from fastapi import HTTPException, status

from tools import TimeTools

from core.ml import ProductClassifier, ProductDataStat


from responses.v1 import ListResponse

from repos.v1.product_transactions import (
    ProductTransactionsRepository,
    ProductTransactionsDataSource,
)

from repos.v1.product_stats import (
    UpdateProductStatBatchItem,
    ProductStatInDb,
    ProductStatInDbWithInfo,
    ProductStatsRepository,
    ProductStatsDataSource,
)

from .query_params import ProductStatQueryParams, ReadProductStatQueryParams


class ProductStatsController:
    def __init__(
        self,
        product_stats_repo: ProductStatsRepository,
        product_transactions_repo: ProductTransactionsRepository,
    ) -> None:
        self.product_stats_repo = product_stats_repo
        self.product_transactions_repo = product_transactions_repo

    async def get_all_product_stats(
        self, query_params: ReadProductStatQueryParams
    ) -> ListResponse[ProductStatInDb]:
        raw_params = query_params.model_dump(exclude_none=True)
        product_stats = await self.product_stats_repo.get_all_product_stats(
            **raw_params
        )
        return ListResponse(
            count=len(product_stats),
            data=product_stats,
        )

    async def get_all_product_stats_with_info(
        self, query_params: ReadProductStatQueryParams
    ) -> ListResponse[ProductStatInDbWithInfo]:
        raw_params = query_params.model_dump(exclude_none=True)
        product_stats = await self.product_stats_repo.get_all_product_stats_with_info(
            **raw_params
        )
        return ListResponse(
            count=len(product_stats),
            data=product_stats,
        )

    async def get_product_stat_by_id(self, product_stat_id: str) -> ProductStatInDb:
        product_stat = await self.product_stats_repo.get_product_stat_by_id(
            product_stat_id
        )
        if product_stat is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ProductStat not found",
            )
        return product_stat

    async def estimate_product_stats(self, query_params: ProductStatQueryParams):
        raw_query_params = query_params.model_dump()
        batch_time = TimeTools.get_now_in_milliseconds()
        raw_query_params["batchTime"] = batch_time

        await self.product_transactions_repo.estimate_product_stats(**raw_query_params)

        await self.product_stats_repo.set_no_transtaction_product_stats(batch_time)

        all_product_stats = (
            await self.product_stats_repo.get_product_stats_with_transaction()
        )

        if len(all_product_stats) == 0:
            print("Get in")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Empty product stats",
            )

        product_stat_data: list[ProductDataStat] = []

        for stat in all_product_stats:
            product_average = stat.totalUnits / stat.daysAnalyzed
            transaction_frecuency = stat.totalTransactions / stat.daysAnalyzed
            product_stat_data.append(
                ProductDataStat(
                    productId=stat.productId,
                    branchId=stat.branchId,
                    productAverage=product_average,
                    transactionFrequency=transaction_frecuency,
                ),
            )

        estimation_result = ProductClassifier().estimate_classification(
            product_stat_data
        )

        update_items = [
            UpdateProductStatBatchItem(
                productId=result.productId,
                branchId=result.branchId,
                estimationLevel=result.classification,
            )
            for result in estimation_result
        ]

        await self.product_stats_repo.update_product_batch(update_items)


product_stats_controller = ProductStatsController(
    product_stats_repo=ProductStatsRepository(
        product_stats_ds=ProductStatsDataSource(),
    ),
    product_transactions_repo=ProductTransactionsRepository(
        product_transactions_ds=ProductTransactionsDataSource(),
    ),
)
