from fastapi import HTTPException, status

from repos.v1.client_groups import (
    CreateClientGroup,
    UpdateClientGroup,
    ClientGroupInDb,
    ClientGroupsRepository,
    ClientGroupsDataSource,
)
from repos.v1.clients import ClientsRepository, ClientsDataSource
from responses.v1 import ListResponse


class ClientGroupsController:
    def __init__(
        self,
        client_groups_repo: ClientGroupsRepository,
        clients_repo: ClientsRepository,
    ) -> None:
        self.client_groups_repo = client_groups_repo
        self.clients_repo = clients_repo

    async def create_client_group(self, body: CreateClientGroup) -> ClientGroupInDb:
        return await self.client_groups_repo.create_client_group(body)

    async def get_all_client_groups(self) -> ListResponse[ClientGroupInDb]:
        client_groups = await self.client_groups_repo.get_all_client_groups()
        return ListResponse(
            count=len(client_groups),
            data=client_groups,
        )

    async def get_client_group_by_id(self, client_group_id: str) -> ClientGroupInDb:
        client_group = await self.client_groups_repo.get_client_group_by_id(
            client_group_id
        )
        if client_group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ClientGroup not found",
            )
        return client_group

    async def update_client_group_by_id(
        self, client_group_id: str, body: UpdateClientGroup
    ) -> ClientGroupInDb:
        current_group = await self.client_groups_repo.get_client_group_by_id(
            client_group_id
        )
        if current_group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ClientGroup not found",
            )
        updated_client_group = await self.client_groups_repo.update_client_group_by_id(
            client_group_id, body
        )
        if updated_client_group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ClientGroup not found",
            )

        if body.name is not None:
            await self.clients_repo.update_group(current_group.name, body.name)

        return updated_client_group

    async def delete_client_group_by_id(self, client_group_id: str) -> ClientGroupInDb:
        deleted_client_group = await self.client_groups_repo.delete_client_group_by_id(
            client_group_id
        )
        if deleted_client_group is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ClientGroup not found",
            )
        return deleted_client_group


client_groups_controller = ClientGroupsController(
    client_groups_repo=ClientGroupsRepository(
        client_groups_ds=ClientGroupsDataSource(),
    ),
    clients_repo=ClientsRepository(
        clients_ds=ClientsDataSource(),
    ),
)
