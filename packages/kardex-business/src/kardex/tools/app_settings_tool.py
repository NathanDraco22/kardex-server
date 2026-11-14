from kardex.repos.v1.app_settings import (
    AppSettingsRepository,
    AppSettingsDataSource,
    AppSettingInDb,
)
from kardex.kardex_config import kardexCtx
from kardex.tools.kardex_exceptions import TenantContextMissingError


class AppSettingsTool:
    _instance: "AppSettingsTool | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    __current_app_settings: dict[str, AppSettingInDb] = {}

    def __init__(self) -> None:
        pass

    @staticmethod
    def _key(nickname: str | None = None) -> str:
        target = nickname or kardexCtx.get().businessNickname
        if not target:
            raise TenantContextMissingError("No tenant in context")
        return target

    async def _load(self, nickname: str | None = None) -> AppSettingInDb:
        key = self._key(nickname)
        app_settings_repo = AppSettingsRepository(
            app_settings_ds=AppSettingsDataSource()
        )
        self.__current_app_settings[key] = (
            await app_settings_repo.get_current_app_settings()
        )
        return self.__current_app_settings[key]

    async def get_current_app_settings(self) -> AppSettingInDb:
        key = self._key()
        if key not in self.__current_app_settings:
            return await self._load(key)
        return self.__current_app_settings[key]

    async def refresh_current_app_settings(
        self, nickname: str | None = None
    ) -> None:
        await self._load(nickname)
