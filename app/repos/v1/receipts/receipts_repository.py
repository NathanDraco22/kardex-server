from repos.v1.common.models.history_params import HistoryClientParams
from .data.receipts_datasource import ReceiptsDataSource
from .models.receipt_model import CreateReceipt, UpdateReceipt, ReceiptInDb
from .models.receipt_total import ReceiptTotal
from .models.branch_receipt_amount_total import BranchAppliedReceiptsAmountsSummary


class ReceiptsRepository:
    def __init__(self, receipts_ds: ReceiptsDataSource):
        self.receipts_ds = receipts_ds

    async def create_receipt(self, create_receipt: CreateReceipt) -> ReceiptInDb:
        # TODO: implement create
        raise NotImplementedError()

    async def get_all_receipts(self, **kwargs) -> list[ReceiptInDb]:
        results = await self.receipts_ds.get_all_receipts(**kwargs)
        models = [ReceiptInDb.model_validate(result) for result in results]
        return models

    async def get_receipts_by_invoice_id(self, invoice_id: str) -> list[ReceiptInDb]:
        results = await self.receipts_ds.get_receipts_by_invoice_id(invoice_id)
        models = [ReceiptInDb.model_validate(result) for result in results]
        return models

    async def get_totals_from_receipts(self, **kwargs) -> ReceiptTotal:
        res = await self.receipts_ds.get_totals_from_receipts(**kwargs)
        return ReceiptTotal.model_validate(res)

    async def get_totals_from_receipts_by_payment_method(
        self, **kwargs
    ) -> list[ReceiptTotal]:
        res = await self.receipts_ds.get_totals_from_receipts_by_payment_method(
            **kwargs
        )
        models = [ReceiptTotal.model_validate(result) for result in res]
        return models

    async def get_receipt_by_id(self, receipt_id: str) -> ReceiptInDb | None:
        result = await self.receipts_ds.get_receipt_by_id(receipt_id)

        if result is None:
            return None

        return ReceiptInDb.model_validate(result)

    async def get_receipt_by_doc_number(self, doc_number: str) -> ReceiptInDb | None:
        result = await self.receipts_ds.get_receipt_by_doc_number(doc_number)

        if result is None:
            return None

        return ReceiptInDb.model_validate(result)

    async def update_receipt_by_id(
        self, receipt_id: str, receipt: UpdateReceipt
    ) -> ReceiptInDb | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_receipt_by_id(self, receipt_id: str) -> ReceiptInDb | None:
        result = await self.receipts_ds.delete_receipt_by_id(receipt_id)

        if result is None:
            return None

        return ReceiptInDb.model_validate(result)

    async def get_receipt_history(
        self, params: HistoryClientParams
    ) -> list[ReceiptInDb]:
        params_data = params.to_query_params()
        results = await self.receipts_ds.fetch_receipt_history(**params_data)
        models = [ReceiptInDb.model_validate(result) for result in results]
        return models

    async def get_branch_receipt_amounts_summary(
        self, **kwargs
    ) -> list[BranchAppliedReceiptsAmountsSummary]:
        results = await self.receipts_ds.get_applied_amounts_by_branch(**kwargs)
        models = [
            BranchAppliedReceiptsAmountsSummary.model_validate(result)
            for result in results
        ]
        return models
