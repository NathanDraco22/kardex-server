from kardex.services_initializer import init_business_services
from kardex.core.default_values.create_default_roles import create_default_roles
from kardex.core.default_values.create_default_expense_categories import (
    create_default_expense_categories,
)
from kardex.core.default_values.defult_etags import set_default_etags
from kardex.core.default_values.create_default_integration import (
    create_default_integration,
)
from kardex.core.default_values.create_default_app_settings import (
    create_default_app_settings,
)
from kardex.core.default_values.create_root_user import create_root_user
from kardex.tools import BranchesTool
from kardex.tools.app_settings_tool import AppSettingsTool
from kardex.tools.users_tool import UsersTool


async def init_services() -> None:
    await init_business_services()
    await create_default_roles()
    await create_default_expense_categories()
    await set_default_etags()
    await create_default_integration()
    await create_default_app_settings()
    await create_root_user()
    await BranchesTool().refresh_current_branches()
    await UsersTool().refresh_inactive_users()
    await AppSettingsTool().refresh_current_app_settings()
