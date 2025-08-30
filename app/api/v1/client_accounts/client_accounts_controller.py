from fastapi import HTTPException, status

from repos.v1.client_accounts import (
    CreateClientAccount, 
    UpdateClientAccount, 
    ClientAccountInDb, 
    ClientAccountsRepository,
    ClientAccountsDataSource,
)


class ClientAccountsController:
    def __init__(self, client_accounts_repo: ClientAccountsRepository) -> None:
        self.client_accounts_repo = client_accounts_repo

    async def create_client_account(self, body: CreateClientAccount) -> ClientAccountInDb:
        return await self.client_accounts_repo.create_client_account(body)

    async def get_all_client_accounts(self) -> list[ClientAccountInDb]:
        client_accounts = await self.client_accounts_repo.get_all_client_accounts()
        return client_accounts

    async def get_client_account_by_id(self, client_account_id: str) -> ClientAccountInDb:
        client_account = await self.client_accounts_repo.get_client_account_by_id(client_account_id)
        if client_account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ClientAccount not found",
            )
        return client_account

    async def update_client_account_by_id(self, client_account_id: str, body: UpdateClientAccount) -> ClientAccountInDb:
        updated_client_account = await self.client_accounts_repo.update_client_account_by_id(client_account_id, body)
        if updated_client_account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ClientAccount not found",
            )
        return updated_client_account

    async def delete_client_account_by_id(self, client_account_id: str) -> ClientAccountInDb:
        deleted_client_account = await self.client_accounts_repo.delete_client_account_by_id(client_account_id)
        if deleted_client_account is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ClientAccount not found",
            )
        return deleted_client_account

client_accounts_controller = ClientAccountsController(
    client_accounts_repo=ClientAccountsRepository(
        client_accounts_ds=ClientAccountsDataSource(),
    ),
)
