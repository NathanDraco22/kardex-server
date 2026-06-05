from __future__ import annotations

from kardex.core.client.process_create_client import InitialBalanceClient
from kardex.tools import TimeTools
from kardex.tools.search_tools import generate_prefixes
from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.repos.v1.common.filter_params import ClientFilterParams

from kardex.core.client.process_create_client import (
    create_multiple_initial_balance,
)
from kardex.core.client.process_create_client import (
    create_initial_balance,
)

from .data.clients_datasource import ClientsDataSource
from .models.client_model import CreateClient, UpdateClient, ClientInDb

class ClientsRepository:
    _instance: "ClientsRepository | None" = None

    def __init__(self, clients_ds: ClientsDataSource):
        self.clients_ds = clients_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ClientsRepository(
                clients_ds=ClientsDataSource()
            )
        return cls._instance

    async def create_client(self, create_client: CreateClient) -> ClientInDb:
        client_number = await CounterManager().next_client_number()
        new_client_in_db = ClientInDb(
            id=client_number,
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_client.model_dump(),
        )

        new_client_in_db_data = new_client_in_db.model_dump()

        new_client_in_db_data["searchPrefixes"] = generate_prefixes(
            new_client_in_db.name
        )

        result = await self.clients_ds.create_client(new_client_in_db_data)

        return ClientInDb.model_validate(result)

    async def create_initial_balance(
        self,
        client: ClientInDb,
        initial_balance: int,
        branch_id: str,
        product_name: str,
    ) -> ClientInDb:
        return await create_initial_balance(
            client, initial_balance, branch_id, product_name
        )

    async def create_multiple_initial_balance(
        self,
        balances: list[InitialBalanceClient],
    ) -> list[ClientInDb]:
        return await create_multiple_initial_balance(balances)

    async def get_all_clients(self, params: ClientFilterParams) -> list[ClientInDb]:
        results = await self.clients_ds.get_all_clients(
            **params.model_dump(exclude_none=True)
        )
        models = [ClientInDb.model_validate(result) for result in results]
        return models

    async def get_all_clients_with_balance(
        self, params: ClientFilterParams
    ) -> list[ClientInDb]:
        results = await self.clients_ds.get_all_clients_with_balance(
            **params.model_dump(exclude_none=True)
        )
        models = [ClientInDb.model_validate(result) for result in results]
        return models

    async def get_client_by_id(self, client_id: str) -> ClientInDb | None:
        result = await self.clients_ds.get_client_by_id(client_id)

        if result is None:
            return None

        return ClientInDb.model_validate(result)

    async def get_client_by_card_id(self, card_id: str) -> ClientInDb | None:
        result = await self.clients_ds.get_client_by_card_id(card_id)

        if result is None:
            return None

        return ClientInDb.model_validate(result)

    async def search_client_by_text(self, text_query: str) -> list[ClientInDb]:
        results = await self.clients_ds.search_client_by_text(text_query)
        models = [ClientInDb.model_validate(result) for result in results]
        return models

    async def search_clients_with_balance(self, text_query: str) -> list[ClientInDb]:
        results = await self.clients_ds.search_clients_with_balance(text_query)
        models = [ClientInDb.model_validate(result) for result in results]
        return models

    async def update_client_by_id(
        self, client_id: str, client: UpdateClient
    ) -> ClientInDb | None:
        updated_client_data = client.model_dump(exclude_unset=True)

        updated_client_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.clients_ds.update_client_by_id(
            client_id, updated_client_data
        )

        if result is None:
            return None

        return ClientInDb.model_validate(result)

    async def update_group(self, old_group: str, new_group: str) -> None:
        return await self.clients_ds.update_group(old_group, new_group)

    async def delete_client_by_id(self, client_id: str) -> ClientInDb | None:
        result = await self.clients_ds.update_client_by_id(
            client_id, {"isDeleted": True}
        )

        if result is None:
            return None

        return ClientInDb.model_validate(result)
