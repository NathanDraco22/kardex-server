from services import MongoService, ProductClassifierService
from services.mongo_indexes import create_indexes
from core.default_values.create_default_roles import create_default_roles
from core.default_values.defult_etags import set_default_etags
from tools import BranchesTool
from tools.users_tool import UsersTool


async def init_services() -> None:
    await MongoService().init_service()
    await create_indexes()
    await create_default_roles()
    await set_default_etags()
    await BranchesTool().refresh_current_branches()
    await UsersTool().refresh_inactive_users()
    ProductClassifierService()
