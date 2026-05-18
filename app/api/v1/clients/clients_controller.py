from fastapi import HTTPException, status

from responses.v1 import ListResponse
from kardex.repos.v1.clients import (
    CreateClient,
    UpdateClient,
    ClientInDb,
    ClientsRepository,
    ClientsDataSource,
)
from kardex.core.client.process_create_client import InitialBalanceClient

from .query_params import ClientQueryParams
from .bodies import CreateMultipleInitialBalance


class ClientsController:
    def __init__(self, clients_repo: ClientsRepository) -> None:
        self.clients_repo = clients_repo

    async def create_client(self, body: CreateClient) -> ClientInDb:
        if body.cardId is not None and body.cardId != "":
            res = await self.clients_repo.get_client_by_card_id(body.cardId)
            if res is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Esta cedula fue registrada: {res.name}",
                )

        return await self.clients_repo.create_client(body)

    async def create_initial_balance(
        self,
        client_id: str,
        initial_balance: int,
        branch_id: str,
        product_name: str,
    ) -> ClientInDb | None:
        client = await self.clients_repo.get_client_by_id(client_id)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

        if client.hasMovements:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client already has movements",
            )
        return await self.clients_repo.create_initial_balance(
            client,
            initial_balance,
            branch_id,
            product_name,
        )

    async def create_multiple_initial_balance(
        self, body: CreateMultipleInitialBalance
    ) -> ListResponse[ClientInDb]:
        client = await self.clients_repo.get_client_by_id(body.clientId)
        if client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )

        if client.hasMovements:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Client already has movements",
            )

        balances = body.initialBalances

        new_balances = []
        for balance in balances:
            new_balance = InitialBalanceClient(
                client=client,
                branch_id=body.branchId,
                product_name=balance.productName,
                initial_balance=balance.initialBalance,
            )

            new_balances.append(new_balance)

        res = await self.clients_repo.create_multiple_initial_balance(new_balances)
        return ListResponse(count=len(res), data=res)

    async def get_all_clients(
        self, params: ClientQueryParams
    ) -> ListResponse[ClientInDb]:
        clients = await self.clients_repo.get_all_clients(
            **params.model_dump(exclude_none=True)
        )
        return ListResponse(
            data=clients,
            count=len(clients),
        )

    async def get_all_clients_with_balance(
        self, params: ClientQueryParams
    ) -> ListResponse[ClientInDb]:
        clients = await self.clients_repo.get_all_clients_with_balance(
            **params.model_dump(exclude_none=True)
        )
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

    async def get_client_by_card_id(self, card_id: str) -> ClientInDb:
        client = await self.clients_repo.get_client_by_card_id(card_id)
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

    async def search_clients_with_balance(
        self, text_query: str
    ) -> ListResponse[ClientInDb]:
        clients = await self.clients_repo.search_clients_with_balance(text_query)
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

    async def delete_client_by_id(self, client_id: str) -> ClientInDb:
        deleted_client = await self.clients_repo.delete_client_by_id(client_id)
        if deleted_client is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Client not found",
            )
        return deleted_client


clients_controller = ClientsController(
    clients_repo=ClientsRepository(
        clients_ds=ClientsDataSource(),
    ),
)
