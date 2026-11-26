from dataclasses import dataclass

from kardex.kardex_config import kardexCtx
from kardex.tools.kardex_exceptions import TenantContextMissingError
from kardex.tools.tenant_cache import BoundedTenantCache
from kardex.tools.tenant_context import normalize_nickname, run_with_tenant_context


@dataclass
class Etag:
    key: str
    value: str


class EtagTool:
    """ETags en memoria, aislados por tenant y acotados (LRU).

    ``_tags[nickname][key]``. Los getters siguen siendo sincronos; la primera
    carga del tenant la garantiza ``ensure_loaded()`` desde el middleware.
    """

    _instance: "EtagTool|None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
        return cls._instance

    _tags: BoundedTenantCache[dict[str, Etag]] = BoundedTenantCache()

    @staticmethod
    def _key(nickname: str | None = None) -> str:
        target = normalize_nickname(nickname or kardexCtx.get().businessNickname)
        if not target:
            raise TenantContextMissingError("No tenant in context")
        return target

    def _tenant_tags(self, nickname: str | None = None) -> dict[str, Etag]:
        return self._tags.setdefault(self._key(nickname), {})

    async def ensure_loaded(self, nickname: str | None = None) -> None:
        key = self._key(nickname)
        if key not in self._tags:
            await self.update_branches_etags(key)

    def set_last_update_branch_etag(
        self, value: str, nickname: str | None = None
    ) -> None:
        self._tenant_tags(nickname)["last_update_branch"] = Etag(
            "last_update_branch", value
        )

    def set_tag(self, key: str, value: str, nickname: str | None = None) -> None:
        self._tenant_tags(nickname)[key] = Etag(key, value)

    def get_etag(self, key: str, nickname: str | None = None) -> Etag | None:
        target = normalize_nickname(nickname or kardexCtx.get().businessNickname)
        if not target:
            return None
        return self._tags.get(target, {}).get(key)

    async def update_branches_etags(self, nickname: str | None = None) -> None:
        from kardex.services.mongo_collections.v1 import BranchesCollection

        key = self._key(nickname)

        async def _count() -> int:
            collection = BranchesCollection.get_instance()
            return await collection._collection.estimated_document_count()

        if key == normalize_nickname(kardexCtx.get().businessNickname):
            count = await _count()
        else:
            count = await run_with_tenant_context(key, _count)

        self.set_tag("branches_count", str(count), nickname=key)

    def get_branches_etag(self, nickname: str | None = None) -> Etag | None:
        target = normalize_nickname(nickname or kardexCtx.get().businessNickname)
        tags = self._tags.get(target, {})

        branches_count = tags.get("branches_count")
        last_update_branch = tags.get("last_update_branch")
        branches_count_value = (
            branches_count.value if branches_count is not None else "-"
        )
        last_update_branch_value = (
            last_update_branch.value if last_update_branch is not None else "-"
        )
        return Etag(
            "branches_count",
            str(branches_count_value) + "_" + str(last_update_branch_value),
        )

    def set_projection_file_etag(self, value: str, nickname: str | None = None) -> None:
        self._tenant_tags(nickname)["projection"] = Etag("projection", value)

    def get_projection_file_etag(self, nickname: str | None = None) -> Etag | None:
        target = normalize_nickname(nickname or kardexCtx.get().businessNickname)
        if not target:
            return None
        return self._tags.get(target, {}).get("projection")

    def estimation_etag(self, value: str, nickname: str | None = None) -> None:
        self._tenant_tags(nickname)["estimation"] = Etag("estimation", value)

    def get_estimation_etag(self, nickname: str | None = None) -> Etag | None:
        target = normalize_nickname(nickname or kardexCtx.get().businessNickname)
        if not target:
            return None
        return self._tags.get(target, {}).get("estimation")
