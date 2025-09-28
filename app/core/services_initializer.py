from services import MongoService
from services.mongo_indexes import create_indexes
from .default_values import (
    create_default_roles,
    create_default_client,
    create_default_branch,
)


async def init_services() -> None:
    await MongoService().init_service()
    await create_indexes()
    await create_default_branch()
    await create_default_roles()
    await create_default_client()
