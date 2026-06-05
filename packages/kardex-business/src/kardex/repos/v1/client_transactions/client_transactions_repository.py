from .data.client_transactions_datasource import ClientTransactionsDataSource
from .models.client_transaction_model import ClientTransactionInDb
from kardex.repos.v1.common.filter_params import ClientTransactionFilterParams

class ClientTransactionsRepository:
    _instance: "ClientTransactionsRepository | None" = None

    def __init__(self, client_transactions_ds: ClientTransactionsDataSource):
        self.client_transactions_ds = client_transactions_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ClientTransactionsRepository(
                client_transactions_ds=ClientTransactionsDataSource()
            )
        return cls._instance

    async def get_all_client_transactions(
        self, params: ClientTransactionFilterParams
    ) -> list[ClientTransactionInDb]:
        query = params.to_query()
        results = await self.client_transactions_ds.get_all_client_transactions(
            **query
        )
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
