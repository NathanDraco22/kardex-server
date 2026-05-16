from kardex.tools import TimeTools
from kardex.core.counter_manager.counter_manager import CounterManager

from kardex.repos.v1.suppliers import SupplierInDb
from .model.supplier_import import SupplierImport

from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import SuppliersCollection


async def process_suppliers_import(suppliers: list[SupplierImport]) -> None:
    supplier_col = SuppliersCollection()
    now_milliseconds = TimeTools.get_now_in_milliseconds()

    new_suppliers: list[SupplierInDb] = []

    mongo_client = MongoService().client

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            supplier_id = await CounterManager().next_supplier_number(session=session)
            raw_int = int(supplier_id)

            for import_supplier in suppliers:
                supplier_id = str(raw_int).zfill(4)

                supplier_data = import_supplier.model_dump(exclude_none=True)

                supplier_in_db = SupplierInDb(
                    id=supplier_id, createdAt=now_milliseconds, **supplier_data
                )

                new_suppliers.append(supplier_in_db)

                raw_int += 1

            new_supplier_data = [supplier.model_dump() for supplier in new_suppliers]

            if new_supplier_data:
                await supplier_col.create_many_suppliers_with_session(
                    new_supplier_data, session=session
                )

            await CounterManager().set_supplier_number(raw_int - 1, session=session)
