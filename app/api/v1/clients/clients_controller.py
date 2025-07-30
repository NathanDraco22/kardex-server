from fastapi import HTTPException, status

from responses.v1 import ListResponse

from repos.v1.clients import (
    CreateClient,
    UpdateClient,
    ClientInDb,
    ClientsRepository,
    ClientsDataSource,
)


class ClientsController:
    def __init__(self, clients_repo: ClientsRepository) -> None:
        self.clients_repo = clients_repo

    async def create_client(self, body: CreateClient) -> ClientInDb:
        return await self.clients_repo.create_client(body)

    async def get_all_clients(self) -> ListResponse[ClientInDb]:
        clients = await self.clients_repo.get_all_clients()
        return ListResponse(
            data=clients,
            count=len(clients),
        )

    async def get_client_by_id(self, client_id: str) -> ClientInDb:
        client = await self.clients_repo.get_client_by_id(client_id)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )
        return client

    async def search_client_by_text(self, text_query: str) -> ListResponse[ClientInDb]:
        clients = await self.clients_repo.search_client_by_text(text_query)
        return ListResponse(
            data=clients,
            count=len(clients),
        )

    async def update_client_by_id(
        self, client_id: str, body: UpdateClient
    ) -> ClientInDb:
        updated_client = await self.clients_repo.update_client_by_id(client_id, body)
        if updated_client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )
        return updated_client


clients_controller = ClientsController(
    clients_repo=ClientsRepository(
        clients_ds=ClientsDataSource(),
    ),
)
