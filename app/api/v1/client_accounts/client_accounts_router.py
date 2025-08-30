from fastapi import APIRouter

from repos.v1.client_accounts import CreateClientAccount, UpdateClientAccount, ClientAccountInDb

from .client_accounts_controller import client_accounts_controller


client_accounts_router = APIRouter(tags=["client_accountsV1"])


@client_accounts_router.post("")
async def create_client_account(body: CreateClientAccount) -> ClientAccountInDb:
    return await client_accounts_controller.create_client_account(body)


@client_accounts_router.get("")
async def get_all_client_accounts() -> list[ClientAccountInDb]:
    return await client_accounts_controller.get_all_client_accounts()


@client_accounts_router.get("/{client_account_id}")
async def get_client_account_by_id(client_account_id: str) -> ClientAccountInDb:
    return await client_accounts_controller.get_client_account_by_id(client_account_id)


@client_accounts_router.patch("/{client_account_id}")
async def update_client_account_by_id(client_account_id: str, body: UpdateClientAccount) -> ClientAccountInDb: 
    return await client_accounts_controller.update_client_account_by_id(client_account_id, body)


@client_accounts_router.delete("/{client_account_id}")
async def delete_client_account_by_id(client_account_id: str) -> ClientAccountInDb:
    return await client_accounts_controller.delete_client_account_by_id(client_account_id)
