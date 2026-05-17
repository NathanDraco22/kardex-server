from .data.client_groups_datasource import ClientGroupsDataSource
from .models.client_group_model import (
    CreateClientGroup,
    UpdateClientGroup,
    ClientGroupInDb,
)

from kardex.tools import UuidTool, TimeTools

class ClientGroupsRepository:
    _instance: "ClientGroupsRepository | None" = None

    def __init__(self, client_groups_ds: ClientGroupsDataSource):
        self.client_groups_ds = client_groups_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = ClientGroupsRepository(
                client_groups_ds=ClientGroupsDataSource()
            )
        return cls._instance

    async def create_client_group(
        self, create_client_group: CreateClientGroup
    ) -> ClientGroupInDb:
        new_group = ClientGroupInDb(
            **create_client_group.model_dump(),
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
        )

        await self.client_groups_ds.create_client_group(new_group.model_dump())

        return new_group

    async def get_all_client_groups(self) -> list[ClientGroupInDb]:
        results = await self.client_groups_ds.get_all_client_groups()
        models = [ClientGroupInDb.model_validate(result) for result in results]
        return models

    async def get_client_group_by_id(
        self, client_group_id: str
    ) -> ClientGroupInDb | None:
        result = await self.client_groups_ds.get_client_group_by_id(client_group_id)

        if result is None:
            return None

        return ClientGroupInDb.model_validate(result)

    async def update_client_group_by_id(
        self, client_group_id: str, client_group: UpdateClientGroup
    ) -> ClientGroupInDb | None:
        updated_data = client_group.model_dump(exclude_unset=True)

        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.client_groups_ds.update_client_group_by_id(
            client_group_id, updated_data
        )

        if result is None:
            return None

        return ClientGroupInDb.model_validate(result)

    async def delete_client_group_by_id(
        self, client_group_id: str
    ) -> ClientGroupInDb | None:
        result = await self.client_groups_ds.delete_client_group_by_id(client_group_id)

        if result is None:
            return None

        return ClientGroupInDb.model_validate(result)
