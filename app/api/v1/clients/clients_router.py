from fastapi import APIRouter, Depends

from repos.v1.clients import CreateClient, UpdateClient, ClientInDb
from responses.v1 import ListResponse

from app_middleware import auth_middleware

from .bodies import CreateInitialBalance
from .clients_controller import clients_controller
from .query_params import ClientQueryParams

clients_router = APIRouter(tags=["clientsV1"], dependencies=[Depends(auth_middleware)])


@clients_router.post("")
async def create_client(body: CreateClient) -> ClientInDb:
    return await clients_controller.create_client(body)


@clients_router.post("/initial-balance")
async def create_initial_balance(body: CreateInitialBalance) -> ClientInDb | None:
    client_id = body.clientId
    initial_balance = body.initialBalance
    branch_id = body.branchId
    product_name = body.productName

    return await clients_controller.create_initial_balance(
        client_id,
        initial_balance,
        branch_id,
        product_name,
    )


@clients_router.get("")
async def get_all_clients(
    params: ClientQueryParams = Depends(),
) -> ListResponse[ClientInDb]:
    return await clients_controller.get_all_clients(params)


@clients_router.get("/balance")
async def get_all_clients_with_balance(
    params: ClientQueryParams = Depends(),
) -> ListResponse[ClientInDb]:
    return await clients_controller.get_all_clients_with_balance(params)


@clients_router.get("/{client_id}")
async def get_client_by_id(client_id: str) -> ClientInDb:
    return await clients_controller.get_client_by_id(client_id)


@clients_router.get("/card/{card_id}")
async def get_client_by_card_id(card_id: str) -> ClientInDb:
    return await clients_controller.get_client_by_card_id(card_id)


@clients_router.get("/search/{text_query}")
async def search_client_by_text(text_query: str) -> ListResponse[ClientInDb]:
    return await clients_controller.search_client_by_text(text_query)


@clients_router.get("/search/balance/{text_query}")
async def search_clients_with_balance(text_query: str) -> ListResponse[ClientInDb]:
    return await clients_controller.search_clients_with_balance(text_query)


@clients_router.patch("/{client_id}")
async def update_client_by_id(client_id: str, body: UpdateClient) -> ClientInDb:
    return await clients_controller.update_client_by_id(client_id, body)


@clients_router.delete("/{client_id}")
async def delete_client_by_id(client_id: str) -> ClientInDb:
    return await clients_controller.delete_client_by_id(client_id)
