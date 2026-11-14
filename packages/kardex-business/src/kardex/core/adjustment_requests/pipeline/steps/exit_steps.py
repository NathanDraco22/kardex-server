from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.core.inventory import (
    InventoryBatchTransformer,
    InventoryEngine,
    InventoryExitBatchItem,
)
from kardex.repos.v1.adjust_exits import AdjustExitInDb, CreateAdjustExit
from kardex.repos.v1.common.models import ExitItem
from kardex.services.mongo_collections.v1 import (
    AdjustExitsCollection,
    ProductAccountsCollection,
    ProductTransactionsCollection,
)
from kardex.tools import UuidTool

from ..base import PipelineStep
from ..context import AdjustmentRequestContext


class PrepareExitStep(PipelineStep[AdjustmentRequestContext]):
    """Prepara el documento y el lote de salida; reserva el número de documento."""

    def should_execute(self, context: AdjustmentRequestContext) -> bool:
        return bool(context.exit_items)

    async def execute(self, context: AdjustmentRequestContext) -> None:
        context.exit_doc_id = UuidTool.generate_uuid()
        context.exit_doc_number = await CounterManager().next_adjust_number(
            context.session
        )

        context.exit_doc_items = [
            ExitItem(
                productId=item.productId,
                productName=item.productName,
                code=item.code,
                brandName=item.brandName,
                unitName=item.unitName,
                cost=item.cost,
                quantity=-abs(item.difference),
                conversionFactor=item.conversionFactor,
                standardUnitName=item.standardUnitName,
                standardUnitFactor=item.standardUnitFactor,
            )
            for item in context.exit_items
        ]

        batch_items = [
            InventoryExitBatchItem(
                product_id=item.productId,
                quantity=abs(item.difference),
                product_name=item.productName,
            )
            for item in context.exit_items
        ]

        batch = InventoryBatchTransformer.prepare_exit(
            branch_id=context.request.branchId,
            items=batch_items,
            existing_accounts_dict=context.accounts,
            document_id=context.exit_doc_id,
            doc_number=context.exit_doc_number,
            tx_type="exit",
            tx_subtype="adjustment",
        )
        context.exit_batch = batch

        for index, exit_item in enumerate(context.exit_doc_items):
            exit_item.cost = batch.assigned_costs[index]

        adjust_exit = CreateAdjustExit(
            docNumber=context.exit_doc_number,
            branchId=context.request.branchId,
            description=f"Ajuste por solicitud {context.request.docNumber}",
            type="adjust",
            items=context.exit_doc_items,
            createdBy=context.request.createdBy,
        )

        exit_doc_data = adjust_exit.model_dump()
        exit_doc_data.update(
            {
                "id": context.exit_doc_id,
                "createdAt": context.now,
                "items": [
                    exit_item.model_dump() for exit_item in context.exit_doc_items
                ],
            }
        )
        context.exit_doc_data = exit_doc_data


class ExecuteExitStep(PipelineStep[AdjustmentRequestContext]):
    """Aplica la salida de inventario usando el lote preparado."""

    def __init__(
        self,
        product_accounts_col: ProductAccountsCollection,
        product_transactions_col: ProductTransactionsCollection,
    ):
        self.product_accounts_col = product_accounts_col
        self.product_transactions_col = product_transactions_col

    def should_execute(self, context: AdjustmentRequestContext) -> bool:
        return context.exit_batch is not None

    async def execute(self, context: AdjustmentRequestContext) -> None:
        batch = context.exit_batch
        if batch is None:
            return

        await InventoryEngine.execute_exit(
            branch_id=context.request.branchId,
            batch_result=batch,
            session=context.session,
            account_col=self.product_accounts_col,
            transaction_col=self.product_transactions_col,
        )


class PersistExitDocumentStep(PipelineStep[AdjustmentRequestContext]):
    """Persiste el documento de salida dentro de la transacción actual."""

    def __init__(self, adjust_exits_col: AdjustExitsCollection):
        self.adjust_exits_col = adjust_exits_col

    def should_execute(self, context: AdjustmentRequestContext) -> bool:
        return context.exit_doc_data is not None

    async def execute(self, context: AdjustmentRequestContext) -> None:
        data = context.exit_doc_data
        if data is None:
            return

        await self.adjust_exits_col.create_adjust_exit_with_session(
            data,
            session=context.session,
        )
        context.exit_doc = AdjustExitInDb.model_validate(data)
