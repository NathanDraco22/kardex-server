from tools import UuidTool, TimeTools

from .data.users_datasource import UsersDataSource
from .models.user_model import CreateUser, UpdateUser, UserInDb


class UsersRepository:
    def __init__(self, users_ds: UsersDataSource):
        self.users_ds = users_ds

    async def create_user(self, create_user: CreateUser) -> UserInDb:
        new_user = UserInDb(
            **create_user.model_dump(),
            id=UuidTool.generate_uuid(),
            created_at=TimeTools.get_now_in_milliseconds(),
        )

        await self.users_ds.create_user(new_user.model_dump())

        return new_user

    async def get_all_users(self) -> list[UserInDb]:
        results = await self.users_ds.get_all_users()
        models = [UserInDb.model_validate(result) for result in results]
        return models

    async def get_user_by_id(self, user_id: str) -> UserInDb | None:
        result = await self.users_ds.get_user_by_id(user_id)

        if result is None:
            return None

        return UserInDb.model_validate(result)

    async def update_user_by_id(
        self,
        user_id: str,
        user: UpdateUser,
    ) -> UserInDb | None:
        updated_data = user.model_dump(exclude_unset=True)

        updated_data["updatedAt"] = TimeTools.get_now_in_milliseconds()

        result = await self.users_ds.update_user_by_id(user_id, updated_data)

        if result is None:
            return None

        return UserInDb.model_validate(result)

    async def delete_user_by_id(self, user_id: str) -> UserInDb | None:
        result = await self.users_ds.delete_user_by_id(user_id)

        if result is None:
            return None

        return UserInDb.model_validate(result)
