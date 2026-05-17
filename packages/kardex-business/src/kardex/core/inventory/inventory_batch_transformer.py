from typing import Any
from pydantic import BaseModel

from kardex.tools import UuidTool, TimeTools
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.product_transactions import (
    ProductTransactionInDb,
    TransactionType,
    TransactionSubType,
)
from kardex.repos.v1.product_sale_profiles import CreateProductSaleProfile
from kardex.repos.v1.product_stats import CreateProductStat


class InventoryEntryBatchItem(BaseModel):
    product_id: str
    quantity: int
    unit_cost: int


class EntryBatchResult(BaseModel):
    accounts_update: list[dict[str, Any]]
    new_profiles: list[CreateProductSaleProfile]
    new_stats: list[CreateProductStat]
    transactions: list[ProductTransactionInDb]


class InventoryExitBatchItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int


class ExitBatchResult(BaseModel):
    stock_subtractions: list[tuple[str, int]]
    transactions: list[ProductTransactionInDb]
    assigned_costs: list[int]


class InsufficientBalanceError(Exception):
    pass


class InventoryBatchTransformer:
    @staticmethod
    def prepare_entry(
        branch_id: str,
        is_commerce_branch: bool,
        items: list[InventoryEntryBatchItem],
        existing_accounts_dict: dict[str, ProductAccountInDb],
        document_id: str,
        doc_number: str,
        tx_type: TransactionType,
        tx_subtype: TransactionSubType,
    ) -> EntryBatchResult:
        now = TimeTools.get_now_in_milliseconds()

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

        bulk_update_accounts: list[dict[str, Any]] = []
        new_sale_profiles: list[CreateProductSaleProfile] = []
        new_product_stats: list[CreateProductStat] = []
        new_transactions: list[ProductTransactionInDb] = []

        for p_id, data in consolidated.items():
            inc_qty = data["qty"]
            inc_total_value = data["total_value"]
            inc_last_cost = data["last_cost"]

            current_qty = 0
            current_avg_cost = 0
            current_max_cost = 0

            if p_id in existing_accounts_dict:
                acc = existing_accounts_dict[p_id]
                current_qty = acc.currentStock
                current_avg_cost = acc.averageCost
                current_max_cost = acc.maximumCost
            else:
                new_sale_profiles.append(
                    CreateProductSaleProfile(
                        branchId=branch_id, productId=p_id, salePrice=0
                    )
                )
                if is_commerce_branch:
                    new_product_stats.append(
                        CreateProductStat(
                            branchId=branch_id,
                            productId=p_id,
                            startDate=now,
                            endDate=now,
                            totalUnits=0,
                            totalTransactions=0,
                            daysAnalyzed=0,
                            lastEstimation=now,
                        )
                    )

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

            bulk_update_accounts.append(
                {
                    "product_id": p_id,
                    "qty": inc_qty,
                    "last_cost": inc_last_cost,
                    "avg_cost": new_avg_cost,
                    "max_cost": new_max_cost,
                }
            )

            transaction = ProductTransactionInDb(
                id=UuidTool.generate_uuid(),
                documentId=document_id,
                docNumber=doc_number,
                type=tx_type,
                subtype=tx_subtype,
                productId=p_id,
                branchId=branch_id,
                quantity=abs(inc_qty),
                averageCost=new_avg_cost,
                createdAt=now,
                resultStock=total_new_qty,
            )
            new_transactions.append(transaction)

        return EntryBatchResult(
            accounts_update=bulk_update_accounts,
            new_profiles=new_sale_profiles,
            new_stats=new_product_stats,
            transactions=new_transactions,
        )

    @staticmethod
    def prepare_exit(
        branch_id: str,
        items: list[InventoryExitBatchItem],
        existing_accounts_dict: dict[str, ProductAccountInDb],
        document_id: str,
        doc_number: str,
        tx_type: TransactionType,
        tx_subtype: TransactionSubType,
        is_order_fulfillment: bool = False,
    ) -> ExitBatchResult:
        now = TimeTools.get_now_in_milliseconds()

        consolidated_req: dict[str, int] = {}
        id_name_map: dict[str, str] = {}

        for item in items:
            consolidated_req[item.product_id] = (
                consolidated_req.get(item.product_id, 0) + item.quantity
            )
            if item.product_id not in id_name_map:
                id_name_map[item.product_id] = item.product_name

        pair_op: list[tuple[str, int]] = []

        for p_id, total_qty_needed in consolidated_req.items():
            p_name = id_name_map.get(p_id, "Producto Desconocido")

            if p_id not in existing_accounts_dict:
                raise InsufficientBalanceError(
                    f"El producto '{p_name}' no tiene cuenta en esta sucursal."
                )

            account = existing_accounts_dict[p_id]

            promise_stock = account.promiseStock if account.promiseStock else 0
            limit_stock = account.currentStock

            if not is_order_fulfillment:
                limit_stock = account.currentStock - promise_stock

            if total_qty_needed > limit_stock:
                stock_type_msg = "FÍSICO" if is_order_fulfillment else "DISPONIBLE"
                raise InsufficientBalanceError(
                    f"Stock {stock_type_msg} insuficiente para '{p_name}'. "
                    f"Requerido: {total_qty_needed}, "
                    f"Disponible: {limit_stock}"
                )

            pair_op.append((p_id, total_qty_needed))

        transactions: list[ProductTransactionInDb] = []
        assigned_costs: list[int] = []

        for item in items:
            current_account = existing_accounts_dict[item.product_id]
            cost_at_exit = current_account.averageCost
            assigned_costs.append(cost_at_exit)

            new_stock_level = current_account.currentStock - item.quantity

            new_tx = ProductTransactionInDb(
                id=UuidTool.generate_uuid(),
                documentId=document_id,
                docNumber=doc_number,
                type=tx_type,
                subtype=tx_subtype,
                productId=item.product_id,
                branchId=branch_id,
                quantity=-abs(item.quantity),
                averageCost=cost_at_exit,
                createdAt=now,
                resultStock=new_stock_level,
            )
            transactions.append(new_tx)
            current_account.currentStock = new_stock_level

        return ExitBatchResult(
            stock_subtractions=pair_op,
            transactions=transactions,
            assigned_costs=assigned_costs,
        )
