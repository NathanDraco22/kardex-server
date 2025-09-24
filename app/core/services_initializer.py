from services import MongoService
from services.mongo_indexes import create_indexes
from .default_values import create_default_roles


async def init_services() -> None:
    await MongoService().init_service()
    await create_indexes()
    await create_default_roles()
    pass
