from fastapi import APIRouter

from repos.v1.client_groups import CreateClientGroup, UpdateClientGroup, ClientGroupInDb

from .client_groups_controller import client_groups_controller

from responses.v1 import ListResponse

c_groups_router = APIRouter(tags=["client_groupsV1"])


@c_groups_router.post("")
async def create_client_group(body: CreateClientGroup) -> ClientGroupInDb:
    return await client_groups_controller.create_client_group(body)


@c_groups_router.get("")
async def get_all_client_groups() -> ListResponse[ClientGroupInDb]:
    return await client_groups_controller.get_all_client_groups()


@c_groups_router.get("/{client_group_id}")
async def get_client_group_by_id(client_group_id: str) -> ClientGroupInDb:
    return await client_groups_controller.get_client_group_by_id(client_group_id)


@c_groups_router.patch("/{client_group_id}")
async def update_client_group_by_id(
    client_group_id: str, body: UpdateClientGroup
) -> ClientGroupInDb:
    return await client_groups_controller.update_client_group_by_id(
        client_group_id, body
    )


@c_groups_router.delete("/{client_group_id}")
async def delete_client_group_by_id(client_group_id: str) -> ClientGroupInDb:
    return await client_groups_controller.delete_client_group_by_id(client_group_id)
