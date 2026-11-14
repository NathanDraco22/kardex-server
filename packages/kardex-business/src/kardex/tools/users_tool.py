from kardex.kardex_config import kardexCtx
from kardex.repos.v1.users import UsersRepository, UsersDataSource, UserInDb
from kardex.tools.kardex_exceptions import TenantContextMissingError


class UsersTool:
    """Cache de usuarios inactivos por tenant.

    ``auth_middleware`` lo consulta en cada request con un getter sincrono; la
    carga se garantiza desde ``multi_tenant_middleware`` con
    ``ensure_loaded()``.
    """

    _instance: "UsersTool|None" = None
    __users_repo = UsersRepository(UsersDataSource())

    _inactive_users: dict[str, list[UserInDb]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UsersTool, cls).__new__(cls)
        return cls._instance

    @staticmethod
    def _key(nickname: str | None = None) -> str:
        target = nickname or kardexCtx.get().businessNickname
        if not target:
            raise TenantContextMissingError("No tenant in context")
        return target

    async def ensure_loaded(self, nickname: str | None = None) -> None:
        key = self._key(nickname)
        if key not in self._inactive_users:
            self._inactive_users[key] = (
                await self.__users_repo.get_all_inactive_users()
            )

    async def refresh_inactive_users(self, nickname: str | None = None) -> None:
        key = self._key(nickname)
        res = await self.__users_repo.get_all_inactive_users()
        self._inactive_users[key] = res

    def get_inactive_user_by_id(self, user_id: str) -> UserInDb | None:
        users = self._inactive_users.get(kardexCtx.get().businessNickname, [])
        for user in users:
            if user.id == user_id:
                return user
        return None
