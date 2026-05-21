from kardex.repos.v1.user_roles import UserRoleInDb
from kardex.services.mongo_collections.v1 import UserRolesCollection
from kardex.core.role_manager.role_manager import RoleManager

from kardex.tools import TimeTools


async def create_default_roles() -> None:
    roles = RoleManager().get_default_roles()

    for role in roles:
        new_role_db = UserRoleInDb(
            id=role.name,
            name=role.name,
            access=role.access,
            createdAt=TimeTools.get_now_in_milliseconds(),
        )

        await UserRolesCollection.get_instance().create_role_if_absent(
            role.name,
            new_role_db.model_dump(),
        )
