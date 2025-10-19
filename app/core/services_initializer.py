from services import MongoService
from services.mongo_indexes import create_indexes
from core.default_values.create_default_roles import create_default_roles


async def init_services() -> None:
    await MongoService().init_service()
    await create_indexes()
    await create_default_roles()
