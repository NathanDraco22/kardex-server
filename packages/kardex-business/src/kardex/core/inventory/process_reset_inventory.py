from kardex.tools import UuidTool, TimeTools, BranchesTool, BranchNotFound, InvalidOperation
from kardex.core.inventory import (
    InventoryBatchTransformer,
    InventoryExitBatchItem,
    InventoryEngine,
)
from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.repos.v1.common.models import ExitItem
from kardex.repos.v1.product_accounts import ProductAccountInDb
from kardex.repos.v1.inventories.models.reset_inventory_model import (
    ResetBranchInventoryRequest,
    ResetBranchInventoryResponse,
)
from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import (
    AdjustExitsCollection,
    ProductTransactionsCollection,
    ProductAccountsCollection,
)


async def process_reset_inventory(
    req: ResetBranchInventoryRequest,
) -> ResetBranchInventoryResponse:
    # 1. Validar existencia de sucursal
    branch = BranchesTool().get_branch_by_id(req.branchId)
    if branch is None:
        raise BranchNotFound("BRANCH_NOT_FOUND", branch_id=req.branchId)

    # 2. Validar que el nombre de confirmación coincida exactamente
    if branch.name.strip().lower() != req.branchNameConfirm.strip().lower():
        raise InvalidOperation(
            f"El nombre de confirmación '{req.branchNameConfirm}' no coincide con el nombre de la sucursal '{branch.name}'."
        )

    mongo_client = MongoService().client
    adjust_col = AdjustExitsCollection.get_instance()
    prd_transaction_col = ProductTransactionsCollection.get_instance()
    product_account_col = ProductAccountsCollection.get_instance()

    async with mongo_client.start_session() as session:
        async with await session.start_transaction():
            now_in_milliseconds = TimeTools.get_now_in_milliseconds()

            # 3. Obtener cuentas con stock > 0
            cursor = await product_account_col._collection.aggregate(
                [
                    {
                        "$match": {
                            "branchId": req.branchId,
                            "currentStock": {"$gt": 0},
                        }
                    },
                    {
                        "$lookup": {
                            "from": "Products",
                            "localField": "productId",
                            "foreignField": "id",
                            "pipeline": [
                                {
                                    "$match": {
                                        "isDeleted": False,
                                    }
                                }
                            ],
                            "as": "product",
                        }
                    },
                    {"$unwind": "$product"},
                    {"$sort": {"product.name": 1}},
                ],
                session=session,
            )
            accounts_data = await cursor.to_list(length=None)
            await cursor.close()

            if not accounts_data:
                return ResetBranchInventoryResponse(
                    message="El inventario de la sucursal ya se encuentra en 0 existencias.",
                    branchId=req.branchId,
                    docNumber="",
                    adjustExitId="",
                    adjustedProductsCount=0,
                    totalQuantityRemoved=0,
                )

            new_adjust_id = UuidTool.generate_uuid()
            doc_number = await CounterManager().next_adjust_number(session)

            accounts_dict = {
                acc["productId"]: ProductAccountInDb.model_validate(acc)
                for acc in accounts_data
            }

            batch_items = [
                InventoryExitBatchItem(
                    product_id=acc["productId"],
                    quantity=acc["currentStock"],
                    product_name=acc["product"].get("name", "Producto"),
                )
                for acc in accounts_data
            ]

            total_qty_removed = sum(acc["currentStock"] for acc in accounts_data)

            # 4. Transformar lote de salida
            batch_result = InventoryBatchTransformer.prepare_exit(
                branch_id=req.branchId,
                items=batch_items,
                existing_accounts_dict=accounts_dict,
                document_id=new_adjust_id,
                doc_number=doc_number,
                tx_type="exit",
                tx_subtype="adjustment",
                is_order_fulfillment=True,
            )

            # 5. Generar items del ajuste
            exit_items: list[ExitItem] = []
            for i, acc in enumerate(accounts_data):
                cost = batch_result.assigned_costs[i]
                exit_items.append(
                    ExitItem(
                        productId=acc["productId"],
                        productName=acc["product"].get("name", ""),
                        code=acc["product"].get("code"),
                        brandName=acc["product"].get("brandName"),
                        unitName=acc["product"].get("unitName"),
                        cost=cost,
                        quantity=-acc["currentStock"],
                        conversionFactor=1,
                    )
                )

            # 6. Ejecutar salida en motor de inventario
            await InventoryEngine.execute_exit(
                branch_id=req.branchId,
                batch_result=batch_result,
                session=session,
                account_col=product_account_col,
                transaction_col=prd_transaction_col,
                allow_negative=True,
            )

            # 7. Reiniciar promiseStock a 0 en cuentas de la sucursal para evitar inconsistencias
            await product_account_col._collection.update_many(
                {
                    "branchId": req.branchId,
                    "promiseStock": {"$gt": 0},
                },
                {
                    "$set": {
                        "promiseStock": 0,
                        "updatedAt": now_in_milliseconds,
                    }
                },
                session=session,
            )

            # 8. Persistir documento de Ajuste de Salida
            adjust_doc = {
                "id": new_adjust_id,
                "docNumber": doc_number,
                "branchId": req.branchId,
                "description": req.description
                or "Reinicio de inventario a 0 (Zona de Peligro)",
                "type": "adjust",
                "items": [item.model_dump() for item in exit_items],
                "createdBy": req.createdBy.model_dump(),
                "createdAt": now_in_milliseconds,
                "updatedAt": None,
            }
            await adjust_col.create_adjust_exit_with_session(
                adjust_doc,
                session=session,
            )

            return ResetBranchInventoryResponse(
                message=f"Inventario reiniciado exitosamente. Se generó el ajuste de salida {doc_number}.",
                branchId=req.branchId,
                docNumber=doc_number,
                adjustExitId=new_adjust_id,
                adjustedProductsCount=len(exit_items),
                totalQuantityRemoved=total_qty_removed,
            )
