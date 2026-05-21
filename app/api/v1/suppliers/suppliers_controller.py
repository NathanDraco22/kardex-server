from fastapi import HTTPException, status

from responses.v1 import ListResponse
from kardex.repos.v1.suppliers import (
    CreateSupplier,
    UpdateSupplier,
    SupplierInDb,
    SuppliersRepository,
    SuppliersDataSource,
)


class SuppliersController:
    def __init__(self, suppliers_repo: SuppliersRepository) -> None:
        self.suppliers_repo = suppliers_repo

    async def create_supplier(self, body: CreateSupplier) -> SupplierInDb:
        return await self.suppliers_repo.create_supplier(body)

    async def get_all_suppliers(self) -> ListResponse[SupplierInDb]:
        suppliers = await self.suppliers_repo.get_all_suppliers()
        return ListResponse(
            data=suppliers,
            count=len(suppliers),
        )

    async def get_supplier_by_id(self, supplier_id: str) -> SupplierInDb:
        supplier = await self.suppliers_repo.get_supplier_by_id(supplier_id)
        if supplier is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found",
            )
        return supplier

    async def search_supplier_by_text(
        self, text_query: str
    ) -> ListResponse[SupplierInDb]:
        suppliers = await self.suppliers_repo.search_supplier_by_text(text_query)
        return ListResponse(
            data=suppliers,
            count=len(suppliers),
        )

    async def update_supplier_by_id(
        self, supplier_id: str, body: UpdateSupplier
    ) -> SupplierInDb:
        updated_supplier = await self.suppliers_repo.update_supplier_by_id(
            supplier_id, body
        )
        if updated_supplier is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found",
            )
        return updated_supplier

    async def delete_supplier_by_id(self, supplier_id: str) -> SupplierInDb:
        deleted_supplier = await self.suppliers_repo.delete_supplier_by_id(supplier_id)
        if deleted_supplier is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Supplier not found",
            )
        return deleted_supplier


suppliers_controller = SuppliersController(
    suppliers_repo=SuppliersRepository(
        suppliers_ds=SuppliersDataSource(),
    ),
)
