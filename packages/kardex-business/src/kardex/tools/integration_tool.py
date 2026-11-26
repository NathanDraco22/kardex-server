from kardex.repos.v1.integrations import (
    IntegrationsRepository,
    IntegrationsDataSource,
    IntegrationInDb,
)
from kardex.kardex_config import kardexCtx
from kardex.tools.kardex_exceptions import TenantContextMissingError
from kardex.tools.tenant_cache import BoundedTenantCache
from kardex.tools.tenant_context import normalize_nickname, run_with_tenant_context


class IntegrationTool:
    _instance: "IntegrationTool|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    __current_integration: BoundedTenantCache[IntegrationInDb] = BoundedTenantCache()

    def __init__(self) -> None:
        pass

    @staticmethod
    def _key(nickname: str | None = None) -> str:
        target = normalize_nickname(nickname or kardexCtx.get().businessNickname)
        if not target:
            raise TenantContextMissingError("No tenant in context")
        return target

    async def _load(self, nickname: str | None = None) -> IntegrationInDb:
        key = self._key(nickname)
        integration_repo = IntegrationsRepository(
            integrations_ds=IntegrationsDataSource()
        )
        if key == normalize_nickname(kardexCtx.get().businessNickname):
            all_integrations = await integration_repo.get_all_integrations()
        else:
            all_integrations = await run_with_tenant_context(
                key, integration_repo.get_all_integrations
            )
        self.__current_integration[key] = all_integrations[0]
        return self.__current_integration[key]

    async def get_current_integration(self) -> IntegrationInDb:
        key = self._key()
        cached = self.__current_integration.get(key)
        if cached is None:
            return await self._load(key)
        return cached

    async def refresh_current_integration(
        self, nickname: str | None = None
    ) -> None:
        await self._load(nickname)
