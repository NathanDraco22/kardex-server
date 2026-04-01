from typing import Any
from pydantic import BaseModel

from tools import TimeTools
from repos.v1.product_accounts import ProductAccountInDb
from repos.v1.product_sale_profiles import CreateProductSaleProfile

from services.mongo_collections.v1 import (
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
)


class InventoryEntryBatchItem(BaseModel):
    product_id: str
    quantity: int  # Siempre positivo aquí
    unit_cost: int  # Costo unitario en centavos


class EntryBatchResult(BaseModel):
    accounts_update: list[dict[str, Any]]
    new_profiles: list[CreateProductSaleProfile]
    simulated_accounts: list[ProductAccountInDb]


def prepare_inventory_entry_batch(
    branch_id: str,
    is_commerce_branch: bool,
    items: list[InventoryEntryBatchItem],
    existing_accounts_dict: dict[str, ProductAccountInDb],
    # Metadata para el Kardex
    document_id: str,
    doc_number: str,
) -> EntryBatchResult:
    now = TimeTools.get_now_in_milliseconds()

    # 1. Consolidar Items (Evitar duplicados)
    consolidated: dict[str, dict] = {}
    for item in items:
        if item.product_id not in consolidated:
            consolidated[item.product_id] = {
                "qty": 0,
                "total_value": 0,
                "last_cost": item.unit_cost,
            }
        entry = consolidated[item.product_id]
        entry["qty"] += item.quantity
        entry["total_value"] += item.quantity * item.unit_cost
        entry["last_cost"] = item.unit_cost

    # Listas de resultados
    bulk_update_accounts: list[dict[str, Any]] = []
    new_sale_profiles: list[CreateProductSaleProfile] = []
    simulated_accounts: list[ProductAccountInDb] = []

    # 2. Loop de Cálculo
    for p_id, data in consolidated.items():
        inc_qty = data["qty"]
        inc_total_value = data["total_value"]
        inc_last_cost = data["last_cost"]

        # Estado actual
        current_qty = 0
        current_avg_cost = 0
        current_max_cost = 0

        if p_id in existing_accounts_dict:
            acc = existing_accounts_dict[p_id]
            current_qty = acc.currentStock
            current_avg_cost = acc.averageCost
            current_max_cost = acc.maximumCost
        else:
            # Es producto nuevo en la sucursal
            new_sale_profiles.append(
                CreateProductSaleProfile(
                    branchId=branch_id, productId=p_id, salePrice=0
                )
            )

        # Cálculo de Promedio Ponderado
        current_asset_value = current_qty * current_avg_cost
        total_new_qty = current_qty + inc_qty

        new_avg_cost = 0
        if total_new_qty > 0:
            new_avg_cost = int(
                round((current_asset_value + inc_total_value) / total_new_qty)
            )
        else:
            new_avg_cost = inc_last_cost

        new_max_cost = max(inc_last_cost, current_max_cost)

        # Preparar Data para Bulk Update
        bulk_update_accounts.append(
            {
                "product_id": p_id,
                "qty": inc_qty,
                "last_cost": inc_last_cost,
                "avg_cost": new_avg_cost,
                "max_cost": new_max_cost,
            }
        )

        # Simular cuenta (para retorno API)
        simulated_accounts.append(
            ProductAccountInDb(
                productId=p_id,
                branchId=branch_id,
                currentStock=total_new_qty,
                averageCost=new_avg_cost,
                lastCost=inc_last_cost,
                createdAt=now,
                updatedAt=now,
                promiseStock=0,
            )
        )

    return EntryBatchResult(
        accounts_update=bulk_update_accounts,
        new_profiles=new_sale_profiles,
        simulated_accounts=simulated_accounts,
    )


async def execute_inventory_entry_db_operations(
    branch_id: str,
    batch_result: EntryBatchResult,  # <--- Ahora usamos tu modelo fuerte
    session: Any,
    # Inyección de dependencias
    account_col: ProductAccountsCollection,
    profile_col: ProductSaleProfilesCollection,
):
    """
    Ejecuta las operaciones de escritura masiva preparadas por la lógica de negocio.
    """

    # 1. Update Cuentas
    if batch_result.accounts_update:
        await account_col.bulk_update_product_account_balance_with_average_cost(
            branch_id=branch_id,
            bulk_data=batch_result.accounts_update,
            session=session,
        )

    # 2. Crear Perfiles (Si hay)
    if batch_result.new_profiles:
        # Convertimos los modelos Pydantic a dicts para Mongo
        raw_profiles = [p.model_dump() for p in batch_result.new_profiles]
        await profile_col.bulk_create_product_sale_profiles(
            raw_profiles, session=session
        )

