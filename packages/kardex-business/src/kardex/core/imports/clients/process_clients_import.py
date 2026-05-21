from kardex.tools import TimeTools
from kardex.tools.search_tools import generate_prefixes
from kardex.core.counter_manager.counter_manager import CounterManager
from kardex.core.client.process_create_client import (
    create_multiple_initial_balance,
    InitialBalanceClient,
)

from kardex.repos.v1.clients import ClientInDb
from .model.client_import import ClientImport

from kardex.services import MongoService
from kardex.services.mongo_collections.v1 import ClientsCollection


async def process_clients_import(branch_id: str, clients: list[ClientImport]) -> None:
    client_col = ClientsCollection.get_instance()
    now_milliseconds = TimeTools.get_now_in_milliseconds()

    new_clients: list[ClientInDb] = []
    initial_balance_requests: list[InitialBalanceClient] = []

    mongo_client = MongoService().client

    async with await mongo_client.start_session() as session:
        async with session.start_transaction():
            client_id = await CounterManager().next_client_number(session=session)
            raw_int = int(client_id)

            for import_client in clients:
                client_id = str(raw_int).zfill(4)

                client_data = import_client.model_dump(
                    exclude={"initialBalance"}, exclude_none=True
                )

                client_in_db = ClientInDb(
                    id=client_id, createdAt=now_milliseconds, **client_data
                )

                new_clients.append(client_in_db)

                if import_client.initialBalance > 0 or import_client.initialBalance < 0:
                    initial_balance_requests.append(
                        InitialBalanceClient(
                            client=client_in_db,
                            initial_balance=import_client.initialBalance,
                            branch_id=branch_id,
                            product_name="SALDO INICIAL IMPORTACIÓN",
                        )
                    )

                raw_int += 1

            new_client_data = []
            for client in new_clients:
                data = client.model_dump()
                data["searchPrefixes"] = generate_prefixes(client.name)
                new_client_data.append(data)

            if new_client_data:
                await client_col.create_many_clients_with_session(
                    new_client_data, session=session
                )

            if initial_balance_requests:
                await create_multiple_initial_balance(
                    balance_requests=initial_balance_requests, external_session=session
                )

            await CounterManager().set_client_number(raw_int - 1, session=session)
