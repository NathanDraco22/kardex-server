from typing import Any
from kardex.services.mongo_collections.v1 import UserRolesCollection, UsersCollection


class UserRolesDataSource:
    async def create_user_role(self, user_role: dict[str, Any]) -> dict[str, Any]:
        collection = UserRolesCollection.get_instance()
        await collection.create_user_role(user_role)
        return user_role

    async def create_user_role_if_absent(
        self,
        user_role_id: str,
        user_role: dict[str, Any],
    ) -> None:
        collection = UserRolesCollection.get_instance()
        await collection.create_role_if_absent(user_role_id, user_role)

    async def get_all_user_roles(self) -> list[dict[str, Any]]:
        collection = UserRolesCollection.get_instance()
        return await collection.fetch_all_user_roles()

    async def get_user_role_by_id(self, user_role_id: str) -> dict[str, Any] | None:
        collection = UserRolesCollection.get_instance()
        return await collection.fetch_user_role_by_id(user_role_id)

    async def update_user_role_by_id(
        self, user_role_id: str, user_role: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = UserRolesCollection.get_instance()
        return await collection.update_user_role_by_id(user_role_id, user_role)

    async def delete_user_role_by_id(self, user_role_id: str) -> dict[str, Any] | None:
        collection = UserRolesCollection.get_instance()
        return await collection.delete_user_role_by_id(user_role_id)

    async def get_user_role_by_name(
        self, name: str, exclude_id: str | None = None
    ) -> dict[str, Any] | None:
        collection = UserRolesCollection.get_instance()
        return await collection.fetch_user_role_by_name(name, exclude_id=exclude_id)

    async def count_users_with_role(self, user_role_id: str) -> int:
        collection = UsersCollection.get_instance()
        return await collection.count_users_by_role(user_role_id)
