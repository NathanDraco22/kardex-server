from kardex.tools import TimeTools, UuidTool

from .data.user_roles_datasource import UserRolesDataSource
from .models.user_role_model import CreateUserRole, UpdateUserRole, UserRoleInDb


def _to_role_model(data: dict) -> UserRoleInDb:
    from kardex.core.role_manager.role_manager import RoleManager

    model = UserRoleInDb.model_validate(data)
    model.isDefault = RoleManager.is_default_role(model.id)
    return model

class UserRolesRepository:
    _instance: "UserRolesRepository | None" = None

    def __init__(self, user_roles_ds: UserRolesDataSource):
        self.user_roles_ds = user_roles_ds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = UserRolesRepository(
                user_roles_ds=UserRolesDataSource()
            )
        return cls._instance

    async def create_user_role(self, create_user_role: CreateUserRole) -> UserRoleInDb:
        new_user_role = UserRoleInDb(
            **create_user_role.model_dump(),
            id=UuidTool.generate_uuid(),
            createdAt=TimeTools.get_now_in_milliseconds(),
        )

        await self.user_roles_ds.create_user_role(new_user_role.model_dump())

        return new_user_role

    async def get_all_user_roles(self) -> list[UserRoleInDb]:
        results = await self.user_roles_ds.get_all_user_roles()
        return [_to_role_model(result) for result in results]

    async def get_user_role_by_id(self, user_role_id: str) -> UserRoleInDb | None:
        result = await self.user_roles_ds.get_user_role_by_id(user_role_id)

        if result is None:
            return None

        return _to_role_model(result)

    async def get_user_role_by_name(
        self, name: str, exclude_id: str | None = None
    ) -> UserRoleInDb | None:
        result = await self.user_roles_ds.get_user_role_by_name(
            name, exclude_id=exclude_id
        )
        if result is None:
            return None
        return _to_role_model(result)

    async def count_users_with_role(self, user_role_id: str) -> int:
        return await self.user_roles_ds.count_users_with_role(user_role_id)

    async def update_user_role_by_id(
        self,
        user_role_id: str,
        user_role: UpdateUserRole,
    ) -> UserRoleInDb | None:
        updated_data = user_role.model_dump(exclude_unset=True)

        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.user_roles_ds.update_user_role_by_id(
            user_role_id, updated_data
        )

        if result is None:
            return None

        return _to_role_model(result)

    async def delete_user_role_by_id(self, user_role_id: str) -> UserRoleInDb | None:
        result = await self.user_roles_ds.delete_user_role_by_id(user_role_id)

        if result is None:
            return None

        return _to_role_model(result)
