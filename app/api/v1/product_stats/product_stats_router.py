from fastapi import APIRouter, Depends

from repos.v1.product_stats import (
    ProductStatInDb,
    ProductStatInDbWithInfo,
    ProductStatInDbWithAccount,
)

from responses.v1 import ListResponse

from .product_stats_controller import product_stats_controller
from .query_params import ProductStatQueryParams, ReadProductStatQueryParams


product_stats_router = APIRouter(tags=["product_statsV1"])


@product_stats_router.get("")
async def get_all_product_stats(
    query=Depends(ReadProductStatQueryParams),
) -> ListResponse[ProductStatInDb]:
    return await product_stats_controller.get_all_product_stats(query)


@product_stats_router.get("/with-info")
async def get_all_product_stats_with_info(
    query=Depends(ReadProductStatQueryParams),
) -> ListResponse[ProductStatInDbWithInfo]:
    return await product_stats_controller.get_all_product_stats_with_info(query)


@product_stats_router.get("/with-account")
async def get_all_product_stats_with_account(
    query=Depends(ReadProductStatQueryParams),
) -> ListResponse[ProductStatInDbWithAccount]:
    return await product_stats_controller.get_all_product_stats_with_account(query)


@product_stats_router.post("/create-projection-xslx-file")
async def create_projection_xslx_file(projectionDays: int) -> None:
    await product_stats_controller.create_projection_xslx_file(projectionDays)


@product_stats_router.post("/estimate")
async def estimate_product_stats(
    query_params: ProductStatQueryParams,
) -> None:
    await product_stats_controller.estimate_product_stats(query_params)
