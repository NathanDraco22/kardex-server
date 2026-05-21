from kardex.repos.v1.clients import ClientInDb
from kardex.services.mongo_collections.v1 import ClientsCollection
from kardex.tools import TimeTools

SALE_CLIENT_ID = "SALE_CLIENT"
sale_client_name = "Cliente Contado"


async def create_default_client() -> ClientInDb:
    new_client = ClientInDb(
        id=SALE_CLIENT_ID,
        name=sale_client_name,
        isInternal=True,
        createdAt=TimeTools.get_now_in_milliseconds(),
    )

    await ClientsCollection.get_instance().create_client_if_absent(
        SALE_CLIENT_ID, new_client.model_dump()
    )

    return new_client
