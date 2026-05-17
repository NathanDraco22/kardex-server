from fastapi import HTTPException, status

from kardex.repos.v1.client_transactions import (
    ClientTransactionInDb,
    ClientTransactionsRepository,
    ClientTransactionsDataSource,
)

from responses.v1 import ListResponse

from .query_params import ClientTransactionQueryParams


class ClientTransactionsController:
    def __init__(self, client_transactions_repo: ClientTransactionsRepository) -> None:
        self.client_transactions_repo = client_transactions_repo

    async def get_all_client_transactions(
        self,
        params: ClientTransactionQueryParams,
    ) -> ListResponse[ClientTransactionInDb]:
        query = params.to_query()
        client_transactions = (
            await self.client_transactions_repo.get_all_client_transactions(**query)
        )
        return ListResponse(
            count=len(client_transactions),
            data=client_transactions,
        )

    async def get_client_transaction_by_id(
        self, client_transaction_id: str
    ) -> ClientTransactionInDb:
        client_transaction = (
            await self.client_transactions_repo.get_client_transaction_by_id(
                client_transaction_id
            )
        )
        if client_transaction is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ClientTransaction not found",
            )
        return client_transaction


client_transactions_controller = ClientTransactionsController(
    client_transactions_repo=ClientTransactionsRepository(
        client_transactions_ds=ClientTransactionsDataSource(),
    ),
)
