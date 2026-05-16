from fastapi import APIRouter, Depends

from responses.v1.list_response import ListResponse
from kardex.repos.v1.suppliers import CreateSupplier, UpdateSupplier, SupplierInDb

from app_middleware import auth_middleware

from .suppliers_controller import suppliers_controller


suppliers_router = APIRouter(
    tags=["suppliersV1"], dependencies=[Depends(auth_middleware)]
)


@suppliers_router.post("")
async def create_supplier(body: CreateSupplier) -> SupplierInDb:
    return await suppliers_controller.create_supplier(body)


@suppliers_router.get("")
async def get_all_suppliers() -> ListResponse[SupplierInDb]:
    return await suppliers_controller.get_all_suppliers()


@suppliers_router.get("/{supplier_id}")
async def get_supplier_by_id(supplier_id: str) -> SupplierInDb:
    return await suppliers_controller.get_supplier_by_id(supplier_id)


@suppliers_router.get("/search/{text_query}")
async def search_supplier_by_text(text_query: str) -> ListResponse[SupplierInDb]:
    return await suppliers_controller.search_supplier_by_text(text_query)


@suppliers_router.patch("/{supplier_id}")
async def update_supplier_by_id(supplier_id: str, body: UpdateSupplier) -> SupplierInDb:
    return await suppliers_controller.update_supplier_by_id(supplier_id, body)


@suppliers_router.delete("/{supplier_id}")
async def delete_supplier_by_id(supplier_id: str) -> SupplierInDb:
    return await suppliers_controller.delete_supplier_by_id(supplier_id)
