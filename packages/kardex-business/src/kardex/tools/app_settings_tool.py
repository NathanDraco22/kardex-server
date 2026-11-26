from kardex.repos.v1.app_settings import (
    AppSettingsRepository,
    AppSettingsDataSource,
    AppSettingInDb,
)
from kardex.kardex_config import kardexCtx
from kardex.tools.kardex_exceptions import TenantContextMissingError
from kardex.tools.tenant_cache import BoundedTenantCache
from kardex.tools.tenant_context import normalize_nickname, run_with_tenant_context


class AppSettingsTool:
    _instance: "AppSettingsTool | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    __current_app_settings: BoundedTenantCache[AppSettingInDb] = BoundedTenantCache()

    def __init__(self) -> None:
        pass

    @staticmethod
    def _key(nickname: str | None = None) -> str:
        target = normalize_nickname(nickname or kardexCtx.get().businessNickname)
        if not target:
            raise TenantContextMissingError("No tenant in context")
        return target

    async def _load(self, nickname: str | None = None) -> AppSettingInDb | None:
        key = self._key(nickname)
        app_settings_repo = AppSettingsRepository(
            app_settings_ds=AppSettingsDataSource()
        )
        if key == normalize_nickname(kardexCtx.get().businessNickname):
            settings = await app_settings_repo.get_current_app_settings()
        else:
            settings = await run_with_tenant_context(
                key, app_settings_repo.get_current_app_settings
            )

        if settings is None:
            self.__current_app_settings.pop(key, None)
            return None

        self.__current_app_settings[key] = settings
        return settings

    async def get_current_app_settings(self) -> AppSettingInDb | None:
        key = self._key()
        cached = self.__current_app_settings.get(key)
        if cached is None:
            return await self._load(key)
        return cached

    async def refresh_current_app_settings(
        self, nickname: str | None = None
    ) -> None:
        await self._load(nickname)
