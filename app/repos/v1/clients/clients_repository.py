from tools import TimeTools
from core.counter_manager.counter_manager import CounterManager

from .data.clients_datasource import ClientsDataSource
from .models.client_model import CreateClient, UpdateClient, ClientInDb


class ClientsRepository:
    def __init__(self, clients_ds: ClientsDataSource):
        self.clients_ds = clients_ds

    async def create_client(self, create_client: CreateClient) -> ClientInDb:
        client_number = await CounterManager().next_client_number()
        new_client_in_db = ClientInDb(
            id=client_number,
            createdAt=TimeTools.get_now_in_milliseconds(),
            **create_client.model_dump(),
        )

        result = await self.clients_ds.create_client(new_client_in_db.model_dump())

        return ClientInDb.model_validate(result)

    async def get_all_clients(self) -> list[ClientInDb]:
        results = await self.clients_ds.get_all_clients()
        models = [ClientInDb.model_validate(result) for result in results]
        return models

    async def get_all_clients_with_balance(self, **kwargs) -> list[ClientInDb]:
        results = await self.clients_ds.get_all_clients_with_balance(**kwargs)
        models = [ClientInDb.model_validate(result) for result in results]
        return models

    async def get_client_by_id(self, client_id: str) -> ClientInDb | None:
        result = await self.clients_ds.get_client_by_id(client_id)

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
