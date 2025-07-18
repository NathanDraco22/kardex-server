from services import MongoService


async def init_services() -> None:
    await MongoService().init_service()
    pass
