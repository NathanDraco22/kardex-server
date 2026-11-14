from kardex.kardex_config import kardexCtx
from kardex.repos.v1.branches import BranchInDb, BranchesRepository, BranchesDataSource
from kardex.tools.kardex_exceptions import TenantContextMissingError


class BranchesTool:
    """Cache de sucursales por tenant.

    Los getters siguen siendo sincronos (36 llamadas en el dominio): la carga
    se garantiza con ``ensure_loaded()`` desde ``multi_tenant_middleware``.
    """

    _instance: "BranchesTool|None" = None

    __branches_repo = BranchesRepository(BranchesDataSource())

    _branches: dict[str, list[BranchInDb]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BranchesTool, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def _key(nickname: str | None = None) -> str:
        target = nickname or kardexCtx.get().businessNickname
        if not target:
            raise TenantContextMissingError("No tenant in context")
        return target

    async def ensure_loaded(self, nickname: str | None = None) -> None:
        key = self._key(nickname)
        if key not in self._branches:
            self._branches[key] = await self.__branches_repo.get_all_branches()

    async def refresh_current_branches(self, nickname: str | None = None) -> None:
        key = self._key(nickname)
        branches = await self.__branches_repo.get_all_branches()
        self._branches[key] = branches

    def get_branch_by_id(self, branch_id: str) -> BranchInDb | None:
        branches = self._branches.get(kardexCtx.get().businessNickname, [])
        for branch in branches:
            if branch.id == branch_id:
                return branch
        return None
