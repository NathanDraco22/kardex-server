from tools import UuidTool, TimeTools
from .data.suppliers_datasource import SuppliersDataSource
from .models.supplier_model import CreateSupplier, UpdateSupplier, SupplierInDb


class SuppliersRepository:
    def __init__(self, suppliers_ds: SuppliersDataSource):
        self.suppliers_ds = suppliers_ds

    async def create_supplier(self, create_supplier: CreateSupplier) -> SupplierInDb:
        new_supplier_in_db = SupplierInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_utc(),
            **create_supplier.model_dump(),
        )

        res = await self.suppliers_ds.create_supplier(new_supplier_in_db.model_dump())

        return SupplierInDb.model_validate(res)

    async def get_all_suppliers(self) -> list[SupplierInDb]:
        results = await self.suppliers_ds.get_all_suppliers()
        models = [SupplierInDb.model_validate(result) for result in results]
        return models

    async def get_supplier_by_id(self, supplier_id: str) -> SupplierInDb | None:
        result = await self.suppliers_ds.get_supplier_by_id(supplier_id)

        if result is None:
            return None

        return SupplierInDb.model_validate(result)

    async def search_supplier_by_text(self, text_query: str) -> list[SupplierInDb]:
        results = await self.suppliers_ds.search_supplier_by_text(text_query)
        models = [SupplierInDb.model_validate(result) for result in results]
        return models

    async def update_supplier_by_id(
        self, supplier_id: str, supplier: UpdateSupplier
    ) -> SupplierInDb | None:
        updated_supplier_data = supplier.model_dump()
        updated_supplier_data["updatedAt"] = TimeTools.get_now_utc()

        result = await self.suppliers_ds.update_supplier_by_id(
            supplier_id, updated_supplier_data
        )

        if result is None:
            return None

        return SupplierInDb.model_validate(result)

    async def delete_supplier_by_id(self, supplier_id: str) -> SupplierInDb | None:
        result = await self.suppliers_ds.update_supplier_by_id(
            supplier_id, {"isDeleted": True}
        )

        if result is None:
            return None

        return SupplierInDb.model_validate(result)
