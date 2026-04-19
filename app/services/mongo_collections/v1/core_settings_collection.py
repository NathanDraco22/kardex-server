from typing import Any

from pymongo import ReturnDocument
from services import MongoService


class CoreSettingsCollection:
    collection_name = "CoreSettings"
    _instance: "CoreSettingsCollection|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        mongo_service = MongoService()
        self.__collection = mongo_service.get_collection(self.collection_name)

    async def create_core_setting(self, core_setting: dict) -> None:
        collection = self.__collection
        await collection.insert_one(core_setting)

    async def fetch_all_core_settings(self) -> list[dict[str, Any]]:
        collection = self.__collection
        cursor = collection.find()

        result = await cursor.to_list(length=None)
        await cursor.close()

        return result

    async def fetch_core_setting_by_id(
        self, core_setting_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one({"id": core_setting_id})
        return result

    async def update_core_setting_by_nickname(
        self,
        core_setting_id: str,
        core_setting: dict,
    ) -> dict[str, Any] | None:
        collection = self.__collection

        result = await collection.find_one_and_update(
            {"nickname": core_setting_id},
            {"$set": core_setting},
            return_document=ReturnDocument.AFTER,
        )

        return result

    async def delete_core_setting_by_id(
        self, core_setting_id: str
    ) -> dict[str, Any] | None:
        collection = self.__collection
        result = await collection.find_one_and_delete({"id": core_setting_id})
        return result
