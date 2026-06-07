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

    await update_default_roles()


async def update_default_roles() -> None:
    roles = RoleManager().get_default_roles()
    collection = UserRolesCollection.get_instance()

    for role in roles:
        existing_role = await collection.fetch_user_role_by_id(role.name)
        if existing_role:
            current_access = existing_role.get("access", [])
            updated = False

            for permission in role.access:
                if permission not in current_access:
                    current_access.append(permission)
                    updated = True

            if updated:
                await collection.update_user_role_by_id(
                    role.name,
                    {"access": current_access}
                )
                print(f"[Role Migration] Rol '{role.name}' actualizado con nuevos permisos.")
