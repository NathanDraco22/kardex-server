from .data.client_accounts_datasource import ClientAccountsDataSource
from .models.client_account_model import CreateClientAccount, UpdateClientAccount, ClientAccountInDb


class ClientAccountsRepository:
    def __init__(self, client_accounts_ds: ClientAccountsDataSource):
        self.client_accounts_ds = client_accounts_ds

    async def create_client_account(self, create_client_account: CreateClientAccount) -> ClientAccountInDb:
        # TODO: implement create
        raise NotImplementedError()

    async def get_all_client_accounts(self) -> list[ClientAccountInDb]:
        results = await self.client_accounts_ds.get_all_client_accounts()
        models = [ClientAccountInDb.model_validate(result) for result in results]
        return models

    async def get_client_account_by_id(self, client_account_id: str) -> ClientAccountInDb | None :
        result = await self.client_accounts_ds.get_client_account_by_id(client_account_id)
        
        if result is None:
            return None
        
        return ClientAccountInDb.model_validate(result)

    async def update_client_account_by_id(self, client_account_id: str, client_account: UpdateClientAccount) -> ClientAccountInDb | None:
        # TODO: implement update
        raise NotImplementedError()

    async def delete_client_account_by_id(self, client_account_id: str) -> ClientAccountInDb | None:
        result = await self.client_accounts_ds.delete_client_account_by_id(client_account_id)
        
        if result is None:
            return None
        
        return ClientAccountInDb.model_validate(result)
