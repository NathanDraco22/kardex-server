from typing import Any
from kardex.services.mongo_collections.v1 import UsersCollection


class UsersDataSource:
    async def create_user(self, user: dict[str, Any]) -> dict[str, Any]:
        collection = UsersCollection()
        await collection.create_user(user)
        return user

    async def get_all_users(self) -> list[dict[str, Any]]:
        collection = UsersCollection()
        return await collection.fetch_all_users()

    async def get_all_active_users_by_branch(
        self, branch_id: str | None
    ) -> list[dict[str, Any]]:
        collection = UsersCollection()
        return await collection.fetch_all_active_users_by_branch(branch_id)

    async def get_inactive_users(self) -> list[dict[str, Any]]:
        collection = UsersCollection()
        return await collection.get_inactive_users()

    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        collection = UsersCollection()
        return await collection.fetch_user_by_id(user_id)

    async def update_user_by_id(
        self, user_id: str, user: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = UsersCollection()
        return await collection.update_user_by_id(user_id, user)

    async def change_password(
        self, user_id: str, password: str
    ) -> dict[str, Any] | None:
        collection = UsersCollection()
        return await collection.change_password(user_id, password)

    async def delete_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        collection = UsersCollection()
        return await collection.delete_user_by_id(user_id)
