from services import MongoService
from services.mongo_indexes import create_indexes
from core.default_values.create_default_roles import create_default_roles
from core.default_values.defult_etags import set_default_etags
from core.default_values.create_default_integration import create_default_integration
from core.default_values.create_root_user import create_root_user
from tools import BranchesTool
from tools.users_tool import UsersTool


async def init_services() -> None:
    await MongoService().init_service()
    await create_indexes()
    await create_default_roles()
    await set_default_etags()
    await create_default_integration()
    await create_root_user()
    await BranchesTool().refresh_current_branches()
    await UsersTool().refresh_inactive_users()
