from fastapi import APIRouter

from repos.v1.client_transactions import ClientTransactionInDb

from .client_transactions_controller import client_transactions_controller


client_transactions_router = APIRouter(tags=["client_transactionsV1"])


@client_transactions_router.get("")
async def get_all_client_transactions() -> list[ClientTransactionInDb]:
    return await client_transactions_controller.get_all_client_transactions()


@client_transactions_router.get("/{client_transaction_id}")
async def get_client_transaction_by_id(
    client_transaction_id: str,
) -> ClientTransactionInDb:
    return await client_transactions_controller.get_client_transaction_by_id(
        client_transaction_id
    )
