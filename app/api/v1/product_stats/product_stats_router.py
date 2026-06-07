from typing import Any
from fastapi import APIRouter, Depends, Response
from fastapi.responses import FileResponse
from kardex.repos.v1.product_stats import (
    ProductStatInDb,
    ProductStatInDbWithInfo,
    ProductStatInDbWithAccount,
)

from responses.v1 import ListResponse
from .product_stats_controller import product_stats_controller
from kardex.repos.v1.common.filter_params import ProductStatFilterParams, ReadProductStatFilterParams
from .bodies import CreateXlsxFileBody


product_stats_router = APIRouter(tags=["product_statsV1"])


@product_stats_router.get("")
async def get_all_product_stats(
    query=Depends(ReadProductStatFilterParams),
) -> ListResponse[ProductStatInDb]:
    return await product_stats_controller.get_all_product_stats(query)


@product_stats_router.get("/projection/file")
async def get_current_projection_file() -> FileResponse:
    return await product_stats_controller.get_projection_file()


@product_stats_router.get("/with-info")
async def get_all_product_stats_with_info(
    query=Depends(ReadProductStatFilterParams),
) -> ListResponse[ProductStatInDbWithInfo]:
    return await product_stats_controller.get_all_product_stats_with_info(query)


@product_stats_router.get("/with-account")
async def get_all_product_stats_with_account(
    query=Depends(ReadProductStatFilterParams),
) -> ListResponse[ProductStatInDbWithAccount]:
    return await product_stats_controller.get_all_product_stats_with_account(query)


@product_stats_router.post("/create-projection-xslx-file")
async def create_projection_xslx_file(body: CreateXlsxFileBody, res: Response) -> dict:
    await product_stats_controller.create_projection_xslx_file(body.projectionDays)
    return {"message": "Archivo Creado"}


@product_stats_router.post("/estimate")
async def estimate_product_stats(
    query_params: ProductStatFilterParams,
) -> dict[str, Any]:
    await product_stats_controller.estimate_product_stats(query_params)
    return {"message": "Product stats estimated"}
