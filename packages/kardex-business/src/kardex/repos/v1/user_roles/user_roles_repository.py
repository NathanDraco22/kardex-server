from kardex.tools import TimeTools, UuidTool


from .data.user_roles_datasource import UserRolesDataSource
from .models.user_role_model import CreateUserRole, UpdateUserRole, UserRoleInDb


class UserRolesRepository:
    def __init__(self, user_roles_ds: UserRolesDataSource):
        self.user_roles_ds = user_roles_ds

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
        models = [UserRoleInDb.model_validate(result) for result in results]
        return models

    async def get_user_role_by_id(self, user_role_id: str) -> UserRoleInDb | None:
        result = await self.user_roles_ds.get_user_role_by_id(user_role_id)

        if result is None:
            return None

        return UserRoleInDb.model_validate(result)

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

        return UserRoleInDb.model_validate(result)

    async def delete_user_role_by_id(self, user_role_id: str) -> UserRoleInDb | None:
        result = await self.user_roles_ds.delete_user_role_by_id(user_role_id)

        if result is None:
            return None

        return UserRoleInDb.model_validate(result)
