from fastapi import APIRouter

from repos.v1.clients import CreateClient, UpdateClient, ClientInDb
from responses.v1 import ListResponse

from .clients_controller import clients_controller


clients_router = APIRouter(tags=["clientsV1"])


@clients_router.post("")
async def create_client(body: CreateClient) -> ClientInDb:
    return await clients_controller.create_client(body)


@clients_router.get("")
async def get_all_clients() -> ListResponse[ClientInDb]:
    return await clients_controller.get_all_clients()


@clients_router.get("/{client_id}")
async def get_client_by_id(client_id: str) -> ClientInDb:
    return await clients_controller.get_client_by_id(client_id)


@clients_router.patch("/{client_id}")
async def update_client_by_id(client_id: str, body: UpdateClient) -> ClientInDb:
    return await clients_controller.update_client_by_id(client_id, body)
