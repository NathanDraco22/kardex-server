from services import MongoService
from services.mongo_indexes import create_indexes


async def init_services() -> None:
    await MongoService().init_service()
    await create_indexes()
    pass
