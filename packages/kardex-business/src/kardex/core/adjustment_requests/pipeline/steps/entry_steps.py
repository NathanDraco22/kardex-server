from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.core.inventory import (
    InventoryBatchTransformer,
    InventoryEngine,
    InventoryEntryBatchItem,
)
from kardex.repos.v1.adjust_entries import AdjustEntryInDb, CreateAdjustEntry
from kardex.repos.v1.common.models import EntryItem
from kardex.services.mongo_collections.v1 import (
    AdjustEntriesCollection,
    ProductAccountsCollection,
    ProductSaleProfilesCollection,
    ProductStatsCollection,
    ProductTransactionsCollection,
)
from kardex.tools import InvalidOperation, UuidTool

from ..base import PipelineStep
from ..context import AdjustmentRequestContext


class PrepareEntryStep(PipelineStep[AdjustmentRequestContext]):
    """Prepara el documento y el lote de entrada; reserva el número de documento."""

    def should_execute(self, context: AdjustmentRequestContext) -> bool:
        return bool(context.entry_items)

    async def execute(self, context: AdjustmentRequestContext) -> None:
        branch = context.branch
        if branch is None:
            raise InvalidOperation("BRANCH_NOT_LOADED")

        context.entry_doc_id = UuidTool.generate_uuid()
        context.entry_doc_number = await CounterManager().next_adjust_number(
            context.session
        )

        context.entry_doc_items = [
            EntryItem(
                productId=item.productId,
                productName=item.productName,
                code=item.code,
                brandName=item.brandName,
                unitName=item.unitName,
                cost=item.cost,
                quantity=item.difference,
                conversionFactor=item.conversionFactor,
                standardUnitName=item.standardUnitName,
                standardUnitFactor=item.standardUnitFactor,
            )
            for item in context.entry_items
        ]

        batch_items = [
            InventoryEntryBatchItem(
                product_id=item.productId,
                quantity=item.difference,
                unit_cost=item.cost,
            )
            for item in context.entry_items
        ]

        batch = InventoryBatchTransformer.prepare_entry(
            branch_id=context.request.branchId,
            is_commerce_branch=branch.isCommerce,
            items=batch_items,
            existing_accounts_dict=context.accounts,
            document_id=context.entry_doc_id,
            doc_number=context.entry_doc_number,
            tx_type="entry",
            tx_subtype="adjustment",
        )
        context.entry_batch = batch

        adjust_entry = CreateAdjustEntry(
            docNumber=context.entry_doc_number,
            branchId=context.request.branchId,
            description=f"Ajuste por solicitud {context.request.docNumber}",
            items=context.entry_doc_items,
            createdBy=context.request.createdBy,
        )

        entry_doc_data = adjust_entry.model_dump()
        entry_doc_data.update(
            {
                "id": context.entry_doc_id,
                "createdAt": context.now,
                "items": [
                    entry_item.model_dump()
                    for entry_item in context.entry_doc_items
                ],
            }
        )
        context.entry_doc_data = entry_doc_data


class ExecuteEntryStep(PipelineStep[AdjustmentRequestContext]):
    """Aplica la entrada de inventario usando el lote preparado."""

    def __init__(
        self,
        product_accounts_col: ProductAccountsCollection,
        product_sale_profiles_col: ProductSaleProfilesCollection,
        product_stats_col: ProductStatsCollection,
        product_transactions_col: ProductTransactionsCollection,
    ):
        self.product_accounts_col = product_accounts_col
        self.product_sale_profiles_col = product_sale_profiles_col
        self.product_stats_col = product_stats_col
        self.product_transactions_col = product_transactions_col

    def should_execute(self, context: AdjustmentRequestContext) -> bool:
        return context.entry_batch is not None

    async def execute(self, context: AdjustmentRequestContext) -> None:
        batch = context.entry_batch
        if batch is None:
            return

        await InventoryEngine.execute_entry(
            branch_id=context.request.branchId,
            batch_result=batch,
            session=context.session,
            account_col=self.product_accounts_col,
            profile_col=self.product_sale_profiles_col,
            stats_col=self.product_stats_col,
            transaction_col=self.product_transactions_col,
        )


class PersistEntryDocumentStep(PipelineStep[AdjustmentRequestContext]):
    """Persiste el documento de entrada dentro de la transacción actual."""

    def __init__(self, adjust_entries_col: AdjustEntriesCollection):
        self.adjust_entries_col = adjust_entries_col

    def should_execute(self, context: AdjustmentRequestContext) -> bool:
        return context.entry_doc_data is not None

    async def execute(self, context: AdjustmentRequestContext) -> None:
        data = context.entry_doc_data
        if data is None:
            return

        await self.adjust_entries_col.create_adjust_entry_with_session(
            data,
            session=context.session,
        )
        context.entry_doc = AdjustEntryInDb.model_validate(data)
