from .data.client_transactions_datasource import ClientTransactionsDataSource
from .models.client_transaction_model import ClientTransactionInDb


class ClientTransactionsRepository:
    def __init__(self, client_transactions_ds: ClientTransactionsDataSource):
        self.client_transactions_ds = client_transactions_ds

    async def get_all_client_transactions(self) -> list[ClientTransactionInDb]:
        results = await self.client_transactions_ds.get_all_client_transactions()
        models = [ClientTransactionInDb.model_validate(result) for result in results]
        return models

    async def get_client_transaction_by_id(
        self, client_transaction_id: str
    ) -> ClientTransactionInDb | None:
        result = await self.client_transactions_ds.get_client_transaction_by_id(
            client_transaction_id
        )

        if result is None:
            return None

        return ClientTransactionInDb.model_validate(result)
