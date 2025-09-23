from typing import Any
from typing_extensions import Self
from services.mongo_collections.v1 import UsersCollection


class UsersDataSource:
    def __new__(cls) -> Self:
        if not hasattr(cls, "instance"):
            cls.instance = super(cls, cls).__new__(cls)
        return cls.instance

    async def create_user(self, user: dict[str, Any]) -> dict[str, Any]:
        collection = UsersCollection()
        await collection.create_user(user)
        return user

    async def get_all_users(self) -> list[dict[str, Any]]:
        collection = UsersCollection()
        return await collection.fetch_all_users()

    async def get_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        collection = UsersCollection()
        return await collection.fetch_user_by_id(user_id)

    async def update_user_by_id(
        self, user_id: str, user: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = UsersCollection()
        return await collection.update_user_by_id(user_id, user)

    async def delete_user_by_id(self, user_id: str) -> dict[str, Any] | None:
        collection = UsersCollection()
        return await collection.delete_user_by_id(user_id)
