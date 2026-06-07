from kardex.services import MongoService
from kardex.services.mongo_indexes import create_indexes


async def init_business_services() -> None:
    mongo_service = MongoService()
    await mongo_service.init_service()
    await create_indexes()
    await set_new_values()


async def set_new_values() -> None:
    pass
