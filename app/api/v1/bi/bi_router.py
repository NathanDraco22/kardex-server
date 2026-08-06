from fastapi import APIRouter, Depends, Query

from app.app_middleware.depends.api_key_middleware import api_key_middleware
from kardex.repos.v1.bi import (
    BIDetalleVentaItem,
    BIClienteItem,
    BIFlujoCajaItem,
    BIInventarioItem,
    BIVentaItem,
)

from .bi_controller import BIController

bi_router = APIRouter(
    prefix="/bi",
    tags=["Power BI Analytics"],
    dependencies=[Depends(api_key_middleware)],
)


@bi_router.get("/invoices", response_model=list[BIVentaItem])
async def get_bi_invoices(
    startDate: int | None = Query(None, description="Unix timestamp de inicio"),
    endDate: int | None = Query(None, description="Unix timestamp de fin"),
    branchId: str | None = Query(None, description="ID de sucursal"),
):
    controller = BIController()
    return await controller.get_invoices(startDate, endDate, branchId)


@bi_router.get("/invoice-items", response_model=list[BIDetalleVentaItem])
async def get_bi_invoice_items(
    startDate: int | None = Query(None, description="Unix timestamp de inicio"),
    endDate: int | None = Query(None, description="Unix timestamp de fin"),
    branchId: str | None = Query(None, description="ID de sucursal"),
):
    controller = BIController()
    return await controller.get_invoice_items(startDate, endDate, branchId)


@bi_router.get("/cash-flow", response_model=list[BIFlujoCajaItem])
async def get_bi_cash_flow(
    startDate: int | None = Query(None, description="Unix timestamp de inicio"),
    endDate: int | None = Query(None, description="Unix timestamp de fin"),
    branchId: str | None = Query(None, description="ID de sucursal"),
):
    controller = BIController()
    return await controller.get_cash_flow(startDate, endDate, branchId)


@bi_router.get("/inventory", response_model=list[BIInventarioItem])
async def get_bi_inventory(
    branchId: str | None = Query(None, description="ID de sucursal"),
):
    controller = BIController()
    return await controller.get_inventory(branchId)


@bi_router.get("/customers", response_model=list[BIClienteItem])
async def get_bi_customers():
    controller = BIController()
    return await controller.get_customers()
