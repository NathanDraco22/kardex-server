import base64

from fastapi import HTTPException, status
from fastapi.responses import FileResponse

from tools import TimeTools, EtagTool

from core.ml import ProductClassifier, ProductDataStat

from services import ProjectionExcelService, ProjectionSheet, ProjectionRow

from responses.v1 import ListResponse

from repos.v1.product_transactions import (
    ProductTransactionsRepository,
    ProductTransactionsDataSource,
)

from repos.v1.branches import BranchesRepository, BranchesDataSource

from repos.v1.product_stats import (
    UpdateProductStatBatchItem,
    ProductStatInDb,
    ProductStatInDbWithInfo,
    ProductStatInDbWithAccount,
    ProductStatsRepository,
    ProductStatsDataSource,
)

from .query_params import ProductStatQueryParams, ReadProductStatQueryParams


class ProductStatsController:
    def __init__(
        self,
        product_stats_repo: ProductStatsRepository,
        product_transactions_repo: ProductTransactionsRepository,
        branches_repo: BranchesRepository = BranchesRepository(
            branches_ds=BranchesDataSource()
        ),
    ) -> None:
        self.product_stats_repo = product_stats_repo
        self.product_transactions_repo = product_transactions_repo
        self.branches_repo = branches_repo

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

    async def get_all_product_stats_with_account(
        self, query_params: ReadProductStatQueryParams
    ) -> ListResponse[ProductStatInDbWithAccount]:
        raw_params = query_params.model_dump(exclude_none=True)
        product_stats = (
            await self.product_stats_repo.get_all_product_stats_with_account(
                **raw_params
            )
        )
        return ListResponse(
            count=len(product_stats),
            data=product_stats,
        )

    async def get_projection_file(self) -> FileResponse:
        path = ProjectionExcelService().get_projection_xslx()
        if not path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="EL archivo No Existe o no Ha sido creado",
            )

        current_etag = EtagTool().get_projection_file_etag()
        headers = {}
        if current_etag is not None:
            headers["ETag"] = current_etag.value

        return FileResponse(
            path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers,
        )

    async def create_projection_xslx_file(self, projection_days: int) -> None:
        commercial_branches = await self.branches_repo.get_all_commerce_branches()
        product_stats = (
            await self.product_stats_repo.get_all_product_stats_with_account()
        )

        sheets = []
        consolidated_map = {}

        for branch in commercial_branches:
            branch_stats = [
                stat for stat in product_stats if stat.branchId == branch.id
            ]

            rows = []

            for stat in branch_stats:
                average_day = (
                    stat.totalUnits / stat.daysAnalyzed if stat.daysAnalyzed > 0 else 0
                )

                average_day = round(average_day, 1)

                # Consolidation Logic
                if stat.productId not in consolidated_map:
                    consolidated_map[stat.productId] = {
                        "stat": stat,
                        "totalStock": 0,
                        "totalAverageDay": 0,
                        "sumAverageCost": 0,
                        "sumClassification": 0,
                        "countAdded": 0,
                    }

                consolidated_map[stat.productId]["totalStock"] += (
                    stat.account.currentStock
                )
                consolidated_map[stat.productId]["totalAverageDay"] += average_day

                # Sumanos el costo directo para luego promediarlo por el número de sucursales
                consolidated_map[stat.productId]["sumAverageCost"] += (
                    stat.account.averageCost
                )
                consolidated_map[stat.productId]["sumClassification"] += (
                    stat.estimationLevel
                )
                consolidated_map[stat.productId]["countAdded"] += 1

                rows.append(
                    ProjectionRow(
                        code=stat.product.code,
                        productName=stat.product.name,
                        brandName=stat.product.brandName,
                        unitName=stat.product.unitName,
                        currentStock=stat.account.currentStock,
                        averageDay=average_day,
                        projectionDays=projection_days,
                        averageCost=stat.account.averageCost / 100,
                        classification=self._get_classification_label(
                            stat.estimationLevel
                        ),
                    )
                )

            projection_sheet = ProjectionSheet(
                name=branch.name,
                title=branch.name,
                subtitle=f"Projection for {projection_days} days",
                rows=rows,
            )
            sheets.append(projection_sheet)

        # Generate Consolidated Sheet
        consolidated_rows = []
        for product_id, data in consolidated_map.items():
            stat = data["stat"]
            total_stock = data["totalStock"]
            count_added = data["countAdded"]
            sum_average_cost = data["sumAverageCost"]
            sum_classification = data["sumClassification"]

            # Request: Promedio de los promedios (dividir entre sucursales que sumaron)
            final_average_cost = (
                sum_average_cost / count_added if count_added > 0 else 0
            )
            final_average_cost = round(final_average_cost / 100, 2)

            average_classification = (
                round(sum_classification / count_added) if count_added > 0 else 1
            )

            consolidated_rows.append(
                ProjectionRow(
                    code=stat.product.code,
                    productName=stat.product.name,
                    brandName=stat.product.brandName,
                    unitName=stat.product.unitName,
                    currentStock=total_stock,
                    averageDay=data["totalAverageDay"],
                    projectionDays=projection_days,
                    averageCost=final_average_cost,
                    classification=self._get_classification_label(
                        int(average_classification)
                    ),  # Classification might vary per branch, taking last one seen
                )
            )

        consolidated_sheet = ProjectionSheet(
            name="Consolidado",
            title="Consolidado General",
            subtitle=f"Projection for {projection_days} days (All Branches)",
            rows=consolidated_rows,
        )

        sheets.insert(0, consolidated_sheet)

        ProjectionExcelService().create_projection_xslx(sheets)

        EtagTool().set_projection_file_etag(str(TimeTools.get_now_in_milliseconds()))

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
        key = base64.b64encode(str(raw_query_params).encode()).decode()
        EtagTool().estimation_etag(key)

    def _get_classification_label(self, level: int) -> str:
        mapping = {
            5: "ALTO (5)",
            4: "BUENO (4)",
            3: "REGULAR (3)",
            2: "BAJO (2)",
            1: "MIN (1)",
        }
        return mapping.get(level, str(level))


product_stats_controller = ProductStatsController(
    product_stats_repo=ProductStatsRepository(
        product_stats_ds=ProductStatsDataSource(),
    ),
    product_transactions_repo=ProductTransactionsRepository(
        product_transactions_ds=ProductTransactionsDataSource(),
    ),
)
