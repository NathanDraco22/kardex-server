from kardex.kardex_config import kardexCtx
from kardex.repos.v1.branches import BranchInDb, BranchesRepository, BranchesDataSource
from kardex.tools.kardex_exceptions import TenantContextMissingError
from kardex.tools.tenant_cache import BoundedTenantCache
from kardex.tools.tenant_context import normalize_nickname, run_with_tenant_context


class BranchesTool:
    """Cache de sucursales por tenant (acotado con LRU).

    Los getters siguen siendo sincronos (36 llamadas en el dominio): la carga
    se garantiza con ``ensure_loaded()`` desde ``multi_tenant_middleware``.
    """

    _instance: "BranchesTool|None" = None

    __branches_repo = BranchesRepository(BranchesDataSource())

    _branches: BoundedTenantCache[list[BranchInDb]] = BoundedTenantCache()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BranchesTool, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def _key(nickname: str | None = None) -> str:
        target = normalize_nickname(nickname or kardexCtx.get().businessNickname)
        if not target:
            raise TenantContextMissingError("No tenant in context")
        return target

    async def _fetch_branches(self, key: str) -> list[BranchInDb]:
        if key == normalize_nickname(kardexCtx.get().businessNickname):
            return await self.__branches_repo.get_all_branches()
        return await run_with_tenant_context(key, self.__branches_repo.get_all_branches)

    async def ensure_loaded(self, nickname: str | None = None) -> None:
        key = self._key(nickname)
        if key not in self._branches:
            self._branches[key] = await self._fetch_branches(key)

    async def refresh_current_branches(self, nickname: str | None = None) -> None:
        key = self._key(nickname)
        self._branches[key] = await self._fetch_branches(key)

    def get_branch_by_id(self, branch_id: str) -> BranchInDb | None:
        branches = self._branches.get(
            normalize_nickname(kardexCtx.get().businessNickname), []
        )
        for branch in branches:
            if branch.id == branch_id:
                return branch
        return None
