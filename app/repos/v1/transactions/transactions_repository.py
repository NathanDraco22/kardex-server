from tools import TimeTools, UuidTool
from .data.transactions_datasource import TransactionsDataSource
from .models.transaction_model import CreateTransaction, TransactionInDb


class TransactionsRepository:
    def __init__(self, transactions_ds: TransactionsDataSource):
        self.transactions_ds = transactions_ds

    async def create_transaction(
        self, create_transaction: CreateTransaction
    ) -> TransactionInDb:
        new_transaction = TransactionInDb(
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_transaction.model_dump(),
        )

        result = await self.transactions_ds.create_transaction(
            new_transaction.model_dump()
        )

        return TransactionInDb.model_validate(result)

    async def get_all_transactions(self) -> list[TransactionInDb]:
        results = await self.transactions_ds.get_all_transactions()
        models = [TransactionInDb.model_validate(result) for result in results]
        return models

    async def get_transaction_by_id(
        self, transaction_id: str
    ) -> TransactionInDb | None:
        result = await self.transactions_ds.get_transaction_by_id(transaction_id)

        if result is None:
            return None

        return TransactionInDb.model_validate(result)
