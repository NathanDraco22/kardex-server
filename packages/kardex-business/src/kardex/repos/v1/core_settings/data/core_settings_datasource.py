from typing import Any
from kardex.services.mongo_collections.v1 import CoreSettingsCollection


class CoreSettingsDataSource:
    async def create_core_setting(self, core_setting: dict[str, Any]) -> dict[str, Any]:
        collection = CoreSettingsCollection()
        await collection.create_core_setting(core_setting)
        return core_setting

    async def get_all_core_settings(self) -> list[dict[str, Any]]:
        collection = CoreSettingsCollection()
        return await collection.fetch_all_core_settings()

    async def get_core_setting_by_id(
        self, core_setting_id: str
    ) -> dict[str, Any] | None:
        collection = CoreSettingsCollection()
        return await collection.fetch_core_setting_by_id(core_setting_id)

    async def update_core_setting_by_nickname(
        self, core_setting_id: str, core_setting: dict[str, Any]
    ) -> dict[str, Any] | None:
        collection = CoreSettingsCollection()
        return await collection.update_core_setting_by_nickname(
            core_setting_id, core_setting
        )

    async def delete_core_setting_by_id(
        self, core_setting_id: str
    ) -> dict[str, Any] | None:
        collection = CoreSettingsCollection()
        return await collection.delete_core_setting_by_id(core_setting_id)
